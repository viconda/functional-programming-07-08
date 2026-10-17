"""Неизменяемые контейнеры с явным отсутствием и ошибкой."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Some:
    """Присутствующее значение; Some(None) отличается от Nothing."""

    value: Any

    def map(self, f: Callable) -> "Some":
        """Преобразовать значение, сохранив форму контейнера."""
        return Some(f(self.value))

    def bind(self, f: Callable) -> "Maybe":
        """Вызвать функцию, уже возвращающую Maybe."""
        return f(self.value)

    def get_or(self, default: Any) -> Any:
        """Извлечь присутствующее значение."""
        return self.value

    def is_some(self) -> bool:
        """Сообщить о наличии значения."""
        return True


@dataclass(frozen=True)
class Nothing:
    """Отсутствие значения, пропускающее следующие шаги."""

    def map(self, f: Callable) -> "Nothing":
        """Сохранить отсутствие без вызова f."""
        return self

    def bind(self, f: Callable) -> "Nothing":
        """Пропустить вычисление."""
        return self

    def get_or(self, default: Any) -> Any:
        """Вернуть запасное значение."""
        return default

    def is_some(self) -> bool:
        """Сообщить об отсутствии значения."""
        return False


@dataclass(frozen=True)
class Ok:
    """Успешный результат."""

    value: Any

    def map(self, f: Callable) -> "Ok":
        """Преобразовать успешное значение."""
        return Ok(f(self.value))

    def bind(self, f: Callable) -> "Result":
        """Продолжить вычисление функцией, возвращающей Result."""
        return f(self.value)

    def get_or(self, default: Any) -> Any:
        """Извлечь успешное значение."""
        return self.value

    def is_ok(self) -> bool:
        """Сообщить об успехе."""
        return True


@dataclass(frozen=True)
class Err:
    """Явная ошибка конвейера."""

    error: Any

    def map(self, f: Callable) -> "Err":
        """Сохранить ошибку без вызова f."""
        return self

    def bind(self, f: Callable) -> "Err":
        """Пропустить следующий шаг."""
        return self

    def get_or(self, default: Any) -> Any:
        """Вернуть запасное значение."""
        return default

    def is_ok(self) -> bool:
        """Сообщить об ошибке."""
        return False


Maybe = Some | Nothing
Result = Ok | Err


def maybe_of(value: Any) -> Maybe:
    """Преобразовать только None в Nothing, сохранив 0 и пустую строку."""
    return Nothing() if value is None else Some(value)


def try_(func: Callable, *args: Any) -> Result:
    """Адаптировать исключения внешней функции к Result."""
    try:
        return Ok(func(*args))
    except Exception as error:
        return Err(f"{type(error).__name__}: {error}")


def sequence(results: Iterable[Result]) -> Result:
    """Собрать значения или остановиться на первой ошибке."""
    values = []
    for result in results:
        if isinstance(result, Err):
            return result
        values.append(result.value)
    return Ok(values)


def partition_results(results: Iterable[Result]) -> tuple[list, list]:
    """Разделить все значения и все ошибки, сохранив порядок."""
    values, errors = [], []
    for result in results:
        if isinstance(result, Ok):
            values.append(result.value)
        else:
            errors.append(result.error)
    return values, errors


def config_host(config: dict) -> str:
    """Безопасно извлечь config['db']['replicas'][0]['host']."""
    return (
        maybe_of(config)
        .bind(lambda c: maybe_of(c.get("db") if isinstance(c, dict) else None))
        .bind(lambda d: maybe_of(d.get("replicas") if isinstance(d, dict) else None))
        .bind(lambda r: maybe_of(r[0] if isinstance(r, list) and r else None))
        .bind(lambda r: maybe_of(r.get("host") if isinstance(r, dict) else None))
        .get_or("localhost")
    )
