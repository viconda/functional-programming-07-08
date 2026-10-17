"""Вариант 3: чистый конвейер обработки учебных заказов."""

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass, replace
from functools import partial, reduce, wraps

from .containers import Err, Ok, Result, partition_results
from .curry import between


@dataclass(frozen=True)
class Order:
    """Заказ; товары задаются парами артикул/количество."""
    code: str
    items: tuple[tuple[str, int], ...]
    address: str
    payment: str
    total: int = 0
    delivery: int = 0


def named_step(name: str) -> Callable:
    """Добавить имя этапа к ошибке без журнала и других побочных эффектов."""
    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(value: object) -> Result:
            result = func(value)
            return Err(f"{name}: {result.error}") if isinstance(result, Err) else result
        return wrapper
    return decorate


@named_step("разбор")
def parse_order(line: str) -> Result:
    """Формат: код; артикул:количество,...; адрес; способ оплаты."""
    parts = tuple(part.strip() for part in line.split(";"))
    if len(parts) != 4:
        return Err("нужно 4 поля")
    code, raw, address, payment = parts
    items = []
    for token in raw.split(","):
        pair = token.strip().split(":")
        if len(pair) != 2 or not pair[1].isascii() or not pair[1].isdecimal():
            return Err("товар должен иметь вид артикул:целое количество")
        if len(pair[1]) > 4:
            return Err("слишком длинное количество")
        items.append((pair[0].strip().upper(), int(pair[1])))
    return Ok(Order(code, tuple(items), address, payment.lower()))


def check(predicate: Callable, reason: str, order: Order) -> Result:
    """Вернуть заказ либо явную причину отклонения."""
    return Ok(order) if predicate(order) else Err(reason)


def enrich(prices: tuple[tuple[str, int], ...], order: Order) -> Result:
    """Вычислить сумму и учебную стоимость доставки в тенге."""
    catalog = dict(prices)
    total = sum(catalog[sku] * qty for sku, qty in order.items)
    return Ok(replace(order, total=total, delivery=0 if total >= 20000 else 1500))


def make_pipeline(prices: tuple[tuple[str, int], ...]) -> Callable[[str], Result]:
    """Собрать разбор, пять проверок, обогащение и итоговую запись."""
    catalog = frozenset(sku for sku, _ in prices)
    quantity_ok = between(1)(99)
    steps = (
        parse_order,
        partial(check, lambda o: bool(o.code), "пустой код заказа"),
        partial(check, lambda o: all(sku in catalog for sku, _ in o.items),
                "неизвестный товар"),
        partial(check, lambda o: all(quantity_ok(qty) for _, qty in o.items),
                "количество вне 1..99"),
        partial(check, lambda o: len(o.address) >= 10 and "," in o.address,
                "неполный адрес"),
        partial(check, lambda o: o.payment in {"card", "cash", "transfer"},
                "неизвестный способ оплаты"),
        partial(enrich, prices),
        lambda o: Ok({"code": o.code, "items": o.items, "address": o.address,
                      "payment": o.payment, "total": o.total,
                      "delivery": o.delivery, "payable": o.total + o.delivery}),
    )
    return lambda line: reduce(lambda result, step: result.bind(step), steps, Ok(line))


def summarize(results: Iterable[Result]) -> dict:
    """Подсчитать успехи и распределение первой ошибки каждой записи."""
    values, errors = partition_results(results)
    return {"success": len(values), "rejected": len(errors),
            "errors": dict(sorted(Counter(errors).items())), "orders": values}
