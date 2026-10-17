"""Каррирование с учётом обязательных и именованных параметров."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any


def curry(func: Callable) -> Callable:
    """Накапливать аргументы до связывания всех обязательных параметров."""
    signature = inspect.signature(func)
    if any(
        p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        for p in signature.parameters.values()
    ):
        raise TypeError("curry требует конечную сигнатуру без *args и **kwargs")
    required = {
        name
        for name, p in signature.parameters.items()
        if p.default is inspect.Parameter.empty
    }

    def collect(args: tuple, kwargs: dict) -> Callable:
        @wraps(func)
        def step(*more: Any, **named: Any) -> Any:
            duplicate = kwargs.keys() & named.keys()
            if duplicate:
                raise TypeError(f"Аргумент уже передан: {sorted(duplicate)}")
            combined = {**kwargs, **named}
            values = args + more
            bound = signature.bind_partial(*values, **combined)
            if required <= bound.arguments.keys():
                return func(*values, **combined)
            return collect(values, combined)

        return step

    return collect((), {})


@curry
def convert(rate: float, fee: float, amount: float) -> float:
    """Умножить сумму на учебный курс и вычесть фиксированную комиссию."""
    return round(amount * rate - fee, 2)


@curry
def between(lo: float, hi: float, x: float) -> bool:
    """Проверить включительный диапазон."""
    return lo <= x <= hi


@curry
def replace_all(old: str, new: str, text: str) -> str:
    """Заменить все вхождения подстроки."""
    return text.replace(old, new)
