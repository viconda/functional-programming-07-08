"""Чистое ядро TCP-протокола без eval и исключений управления потоком."""

import json
import math
import operator
import re
from functools import partial

from .compose import pipe
from .containers import Err, Ok, Result


def parse(line: str) -> Result:
    """Разделить имя команды и полезную нагрузку."""
    if len(line) > 10000:
        return Err("слишком длинный запрос")
    parts = line.strip().split(maxsplit=1)
    if not parts:
        return Err("пустой запрос")
    return Ok((parts[0].upper(), parts[1] if len(parts) == 2 else ""))


def number(raw: str) -> Result:
    """Проверить ограниченное десятичное число до преобразования."""
    if (
        len(raw) > 100
        or re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)", raw) is None
    ):
        return Err("некорректное число")
    value = float(raw)
    return (
        Ok(value)
        if math.isfinite(value) and abs(value) <= 1e100
        else Err("число слишком велико")
    )


def validate(request: tuple[str, str]) -> Result:
    """Проверить команду, число параметров и значения."""
    command, payload = request
    if command == "UPPER":
        return Ok((command, payload)) if payload else Err("UPPER требует текст")
    tokens = payload.split()
    if command == "CALC":
        if len(tokens) != 3 or tokens[1] not in {"+", "-", "*", "/"}:
            return Err("формат CALC: число оператор число")
        left, right = number(tokens[0]), number(tokens[2])
        if isinstance(left, Err) or isinstance(right, Err):
            return Err("CALC: некорректное число")
        if tokens[1] == "/" and right.value == 0:
            return Err("деление на ноль")
        return Ok((command, (left.value, tokens[1], right.value)))
    if command not in {"STATS", "CONVERT"}:
        return Err("неизвестная команда")
    if not tokens or (command == "CONVERT" and len(tokens) != 3):
        return Err("неверное число аргументов")
    parsed = tuple(map(number, tokens))
    if any(isinstance(x, Err) for x in parsed):
        return Err("некорректное число")
    values = tuple(x.value for x in parsed)
    if command == "CONVERT" and (values[0] <= 0 or values[1] < 0 or values[2] < 0):
        return Err("CONVERT: rate > 0, fee >= 0, amount >= 0")
    return Ok((command, values))


def calculate(args: tuple[float, str, float]) -> float:
    """Посчитать одно проверенное арифметическое действие."""
    a, op, b = args
    return {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
    }[op](a, b)


def stats(values: tuple[float, ...]) -> dict:
    """Статистика проверенной непустой последовательности."""
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "mean": sum(values) / len(values),
    }


def dispatch(request: tuple) -> Result:
    """Выбрать чистый обработчик из локального словаря."""
    command, args = request
    handlers = {
        "CALC": calculate,
        "UPPER": str.upper,
        "STATS": stats,
        "CONVERT": lambda xs: round(xs[0] * xs[2] - xs[1], 2),
    }
    return Ok(handlers[command](args))


def format_response(result: Result) -> str:
    """Вернуть однострочный JSON, безопасный для текстового протокола."""
    record = (
        {"ok": True, "value": result.value}
        if isinstance(result, Ok)
        else {"ok": False, "error": result.error}
    )
    return json.dumps(record, ensure_ascii=False, allow_nan=False)


def process_request(line: str) -> str:
    """Конвейер parse -> validate -> dispatch -> format_response."""
    return pipe(
        parse, lambda r: r.bind(validate), lambda r: r.bind(dispatch), format_response
    )(line)


def request(command: str, *args: object) -> str:
    """Собрать строку запроса для клиента."""
    return " ".join((command, *(str(x) for x in args)))


def client_commands() -> tuple[str, ...]:
    """Использовать partial для специализации команд клиента."""
    calc, upper = partial(request, "CALC"), partial(request, "UPPER")
    return (
        calc(2, "+", 3),
        upper("привет, мир"),
        request("STATS", 1, 5, 7),
        request("CONVERT", 2, 1, 10),
        calc(1, "/", 0),
        request("UNKNOWN"),
    )


def decode_response(text: str) -> Result:
    """Чисто преобразовать внешний JSON в Result на границе клиента."""
    try:
        record = json.loads(text)
    except (ValueError, TypeError):
        return Err("повреждённый ответ сервера")
    if not isinstance(record, dict) or type(record.get("ok")) is not bool:
        return Err("неверная схема ответа")
    if record["ok"] and "value" in record:
        return Ok(record["value"])
    if not record["ok"] and isinstance(record.get("error"), str):
        return Err(record["error"])
    return Err("неверная схема ответа")
