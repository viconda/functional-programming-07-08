"""Наблюдение и управление вызовами отделены от предметных функций."""

import inspect
import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import Any, get_type_hints


def timed(func: Callable) -> Callable:
    """Сохранить время каждого вызова, включая завершившийся исключением."""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            wrapper.history.append(time.perf_counter() - start)
    wrapper.history = []
    return wrapper


def log_call(level: str = "INFO") -> Callable:
    """Создать декоратор стандартного logging с выбранным уровнем."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Неизвестный уровень logging")

    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(func.__module__)
            logger.log(numeric_level, "%s args=%r kwargs=%r", func.__name__, args, kwargs)
            result = func(*args, **kwargs)
            logger.log(numeric_level, "%s -> %r", func.__name__, result)
            return result
        return wrapper
    return decorate


def retry(times: int = 3, exceptions: tuple[type[Exception], ...] = (Exception,),
          delay: float = 0.0) -> Callable:
    """times обозначает общее число попыток; последнюю ошибку пробросить."""
    if times < 1 or delay < 0:
        raise ValueError("times >= 1, delay >= 0")

    def decorate(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(times):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times - 1:
                        raise
                    if delay:
                        time.sleep(delay)
            raise AssertionError("Недостижимая ветвь")
        return wrapper
    return decorate


def typecheck(func: Callable) -> Callable:
    """Проверить int, float, str и list; bool не считается int."""
    signature, hints = inspect.signature(func), get_type_hints(func)
    supported = (int, float, str, list)
    if any(hint not in supported for name, hint in hints.items() if name != "return"):
        raise TypeError("Поддерживаются только простые int, float, str, list")

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        bound = signature.bind(*args, **kwargs)
        bound.apply_defaults()
        for name, value in bound.arguments.items():
            if name in hints and type(value) is not hints[name]:
                raise TypeError(f"{name}: ожидается {hints[name].__name__}")
        return func(*args, **kwargs)
    return wrapper


def ttl_cache(seconds: float, clock: Callable[[], float] = time.monotonic) -> Callable:
    """Кэшировать до истечения TTL; время жизни начинается после вычисления."""
    if seconds < 0:
        raise ValueError("seconds < 0")

    def decorate(func: Callable) -> Callable:
        cache: dict = {}

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = clock()
            for old in tuple(cache):
                if cache[old][0] <= now:
                    del cache[old]
            key = (args, tuple(sorted(kwargs.items())))
            if key in cache:
                return cache[key][1]
            result = func(*args, **kwargs)
            if seconds:
                cache[key] = (clock() + seconds, result)
            return result
        wrapper.cache_clear = cache.clear
        return wrapper
    return decorate
