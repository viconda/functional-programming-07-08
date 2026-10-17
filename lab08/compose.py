"""Композиция, конвейеры и транслитерация."""

import re
from collections.abc import Callable
from functools import partial, reduce
from typing import Any


def identity(x: Any) -> Any:
    """Вернуть значение без изменения."""
    return x


def pipe(*fs: Callable) -> Callable:
    """Применять функции слева направо; пустой конвейер тождественен."""
    if not fs:
        return identity
    return lambda x: reduce(lambda value, f: f(value), fs, x)


def compose(*fs: Callable) -> Callable:
    """Применять функции справа налево."""
    return pipe(*reversed(fs))


def pipe_value(x: Any, *fs: Callable) -> Any:
    """Немедленно пропустить значение через конвейер."""
    return pipe(*fs)(x)


def transliterate(text: str) -> str:
    """Транслитерировать русские буквы; мягкий и твёрдый знаки убрать."""
    letters = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    replacements = (
        "a b v g d e yo zh z i y k l m n o p r s t u f kh ts ch sh shch _ y _ e yu ya"
    ).split()
    mapping = dict(zip(letters, ("" if x == "_" else x for x in replacements)))
    return "".join(mapping.get(c, c) for c in text)


def slugify(title: str) -> str:
    """Построить slug через pipe и частично применённые замены."""
    return pipe(
        str.strip,
        str.lower,
        transliterate,
        partial(re.sub, r"[^a-z0-9]+", "-"),
        partial(re.sub, r"-+", "-"),
        lambda s: s.strip("-"),
    )(title)
