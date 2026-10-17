"""Кэши с локальным состоянием и чистая передача состояния."""

from collections import OrderedDict, namedtuple
from collections.abc import Callable, Mapping
from functools import wraps
from types import MappingProxyType
from typing import Any

CacheInfo = namedtuple("CacheInfo", "hits misses maxsize currsize")


def memoize(maxsize: int | None = None) -> Callable:
    """Кэшировать хешируемые аргументы; нулевой размер отключает хранение."""
    if maxsize is not None and maxsize < 0:
        raise ValueError("maxsize должен быть неотрицательным")

    def decorate(func: Callable) -> Callable:
        cache: OrderedDict = OrderedDict()
        hits = misses = 0

        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            nonlocal hits, misses
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache:
                hits += 1
                cache.move_to_end(key)
                return cache[key]
            misses += 1
            value = func(*args, **kwargs)
            if maxsize != 0:
                cache[key] = value
                cache.move_to_end(key)
                if maxsize is not None and len(cache) > maxsize:
                    cache.popitem(last=False)
            return value

        def cache_info() -> tuple:
            return CacheInfo(hits, misses, maxsize, len(cache))

        def cache_clear() -> None:
            nonlocal hits, misses
            cache.clear()
            hits = misses = 0

        wrapped.cache_info = cache_info
        wrapped.cache_clear = cache_clear
        return wrapped

    return decorate


def make_fib(decorator: Callable) -> Callable:
    """Создать независимую функцию Фибоначчи с выбранным кэшем."""

    @decorator
    def fib(n: int) -> int:
        if n < 0:
            raise ValueError("n < 0")
        return n if n < 2 else fib(n - 1) + fib(n - 2)

    return fib


def make_grid(decorator: Callable) -> Callable:
    """Создать функцию числа путей по прямоугольнику ячеек."""

    @decorator
    def grid(m: int, n: int) -> int:
        if m < 1 or n < 1:
            raise ValueError("Размеры должны быть положительными")
        return 1 if m == 1 or n == 1 else grid(m - 1, n) + grid(m, n - 1)

    return grid


def fib_plain(n: int) -> int:
    """Наивный рекурсивный эталон для n >= 0."""
    if n < 0:
        raise ValueError("n < 0")
    return n if n < 2 else fib_plain(n - 1) + fib_plain(n - 2)


def fib_iter(n: int) -> int:
    """Вычислить F(n) циклом без рекурсивного стека."""
    if n < 0:
        raise ValueError("n < 0")
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_state(n: int, memo: Mapping[int, int]) -> tuple[int, Mapping[int, int]]:
    """Вернуть F(n) и новый неизменяемый словарь, не меняя входной."""
    if n < 0:
        raise ValueError("n < 0")
    if n in memo:
        return memo[n], memo
    if n < 2:
        value = n
    else:
        a, memo = fib_state(n - 1, memo)
        b, memo = fib_state(n - 2, memo)
        value = a + b
    return value, MappingProxyType({**memo, n: value})
