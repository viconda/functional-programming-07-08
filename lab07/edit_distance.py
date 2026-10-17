"""Расстояние Левенштейна и однозначно применимый сценарий."""

from dataclasses import dataclass
from functools import cache


@dataclass(frozen=True)
class Edit:
    """Позиция относится к строке после всех предыдущих операций."""
    kind: str
    index: int
    old: str = ""
    new: str = ""


def edit_script(
    s: str, t: str, order: tuple[str, ...] = ("delete", "insert", "replace")
) -> tuple[int, tuple[Edit, ...], tuple]:
    """Найти минимальный сценарий; порядок определяет разрешение ничьих."""
    if sorted(order) != ["delete", "insert", "replace"]:
        raise ValueError("Нужна перестановка трёх операций")

    @cache
    def go(i: int, j: int) -> tuple[int, tuple[Edit, ...]]:
        if i == len(s):
            return len(t) - j, tuple(Edit("insert", k, new=t[k])
                                     for k in range(j, len(t)))
        if j == len(t):
            return len(s) - i, tuple(Edit("delete", j, old=c) for c in s[i:])
        if s[i] == t[j]:
            return go(i + 1, j + 1)
        choices = {
            "delete": (go(i + 1, j), Edit("delete", j, old=s[i])),
            "insert": (go(i, j + 1), Edit("insert", j, new=t[j])),
            "replace": (go(i + 1, j + 1), Edit("replace", j, s[i], t[j])),
        }
        (cost, ops), op = min((choices[k] for k in order), key=lambda x: x[0][0])
        return cost + 1, (op,) + ops

    distance, operations = go(0, 0)
    return distance, operations, go.cache_info()


def apply_script(s: str, ops: tuple[Edit, ...]) -> str:
    """Применить сценарий с проверкой позиции и заменяемого символа."""
    for op in ops:
        i = op.index
        if not 0 <= i <= len(s):
            raise ValueError("Неверная позиция")
        if op.kind == "insert":
            s = s[:i] + op.new + s[i:]
        elif op.kind in ("delete", "replace"):
            if i == len(s) or s[i] != op.old:
                raise ValueError("Сценарий не соответствует строке")
            s = s[:i] + (op.new if op.kind == "replace" else "") + s[i + 1:]
        else:
            raise ValueError("Неизвестная операция")
    return s


def lev_table(s: str, t: str) -> list[list[int]]:
    """Построить независимую таблицу расстояний между префиксами."""
    d = [[0] * (len(t) + 1) for _ in range(len(s) + 1)]
    for i in range(len(s) + 1):
        d[i][0] = i
    for j in range(len(t) + 1):
        d[0][j] = j
    for i in range(1, len(s) + 1):
        for j in range(1, len(t) + 1):
            d[i][j] = min(d[i - 1][j] + 1, d[i][j - 1] + 1,
                          d[i - 1][j - 1] + (s[i - 1] != t[j - 1]))
    return d


def lev_plain(s: str, t: str) -> int:
    """Наивный эталон для коротких строк."""
    if not s or not t:
        return len(s) + len(t)
    if s[0] == t[0]:
        return lev_plain(s[1:], t[1:])
    return 1 + min(lev_plain(s[1:], t), lev_plain(s, t[1:]),
                   lev_plain(s[1:], t[1:]))
