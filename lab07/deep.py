"""Трамплин, взаимная рекурсия и явные стеки."""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from typing import Any


class Thunk:
    """Помеченный отложенный шаг, отличимый от функции-результата."""

    __slots__ = ("fn", "args")

    def __init__(self, fn: Callable, *args: Any) -> None:
        self.fn, self.args = fn, args


def trampoline(fn: Callable, *args: Any) -> Any:
    """Выполнять только Thunk; обычную функцию вернуть как значение."""
    result = fn(*args)
    while isinstance(result, Thunk):
        result = result.fn(*result.args)
    return result


def sum_tail(xs: Sequence[int], i: int = 0, acc: int = 0) -> int | Thunk:
    """Суммировать по индексу без копирования срезов."""
    return acc if i == len(xs) else Thunk(sum_tail, xs, i + 1, acc + xs[i])


def factorial_tail(n: int, acc: int = 1) -> int | Thunk:
    """Отложенный хвостовой факториал неотрицательного числа."""
    if n < 0:
        raise ValueError("n < 0")
    return acc if n == 0 else Thunk(factorial_tail, n - 1, acc * n)


def is_even(n: int) -> bool | Thunk:
    """Взаимно рекурсивная проверка чётности."""
    return True if n == 0 else Thunk(is_odd, abs(n) - 1)


def is_odd(n: int) -> bool | Thunk:
    """Взаимно рекурсивная проверка нечётности."""
    return False if n == 0 else Thunk(is_even, abs(n) - 1)


def collatz_tail(n: int, steps: int = 0) -> int | Thunk:
    """Число переходов до 1; длина с начальным элементом на 1 больше."""
    if n < 1:
        raise ValueError("n должен быть положительным")
    return (
        steps
        if n == 1
        else Thunk(collatz_tail, n // 2 if n % 2 == 0 else 3 * n + 1, steps + 1)
    )


def collatz_range(limit: int, use_trampoline: bool = True) -> tuple[int, ...]:
    """Проверить все 1..limit с общим локальным кэшем длин цепочек."""
    if limit < 1:
        return ()
    known = {1: 0}

    def step(n: int, path: list[int]) -> int | Thunk:
        if n in known:
            return known[n]
        path.append(n)
        return Thunk(step, n // 2 if n % 2 == 0 else 3 * n + 1, path)

    result = []
    for start in range(1, limit + 1):
        path: list[int] = []
        if use_trampoline:
            length = trampoline(step, start, path)
        else:
            n = start
            while n not in known:
                path.append(n)
                n = n // 2 if n % 2 == 0 else 3 * n + 1
            length = known[n]
        for n in reversed(path):
            length += 1
            known[n] = length
        result.append(known[start])
    return tuple(result)


@dataclass(frozen=True)
class Node:
    """Структура узла BST из работы 6 с неизменяемыми ссылками."""

    key: int
    left: "Node | None" = None
    right: "Node | None" = None


def dfs_recursive(tree: Node | None) -> tuple[int, ...]:
    """Эталонный прямой обход BST из работы 6."""
    return (
        ()
        if tree is None
        else (tree.key,) + dfs_recursive(tree.left) + dfs_recursive(tree.right)
    )


def dfs_stack(tree: Node | None) -> tuple[int, ...]:
    """Прямой обход с явным стеком и порядком слева направо."""
    stack = [tree] if tree else []
    out = []
    while stack:
        node = stack.pop()
        out.append(node.key)
        if node.right:
            stack.append(node.right)
        if node.left:
            stack.append(node.left)
    return tuple(out)


def walk(tree: Node | None, depth: int = 0) -> Iterator[tuple[int, int]]:
    """Рекурсивный ленивый обход с yield from."""
    if tree is not None:
        yield depth, tree.key
        yield from walk(tree.left, depth + 1)
        yield from walk(tree.right, depth + 1)


def hanoi_recursive(
    n: int, src: str = "A", dst: str = "C", via: str = "B"
) -> tuple[tuple[str, str], ...]:
    """Эталон Ханойских башен для небольшого числа дисков."""
    if n < 0:
        raise ValueError("n < 0")
    if n == 0:
        return ()
    return (
        hanoi_recursive(n - 1, src, via, dst)
        + ((src, dst),)
        + hanoi_recursive(n - 1, via, dst, src)
    )


def hanoi_stack(n: int) -> tuple[tuple[str, str], ...]:
    """Смоделировать кадры (n, src, dst, via, stage) явно."""
    if n < 0:
        raise ValueError("n < 0")
    stack = [(n, "A", "C", "B", 0)]
    moves = []
    while stack:
        n, src, dst, via, stage = stack.pop()
        if n == 0:
            continue
        if stage == 0:
            stack.extend([(n, src, dst, via, 1), (n - 1, src, via, dst, 0)])
        else:
            moves.append((src, dst))
            stack.append((n - 1, via, dst, src, 0))
    return tuple(moves)


def ack_recursive(m: int, n: int) -> int:
    """Прямое определение Аккермана для малых аргументов."""
    if m == 0:
        return n + 1
    if n == 0:
        return ack_recursive(m - 1, 1)
    return ack_recursive(m - 1, ack_recursive(m, n - 1))


def ack_stack(m: int, n: int) -> int:
    """Аккерман без рекурсии; стек хранит отложенные значения m."""
    if m < 0 or n < 0:
        raise ValueError("Аргументы должны быть неотрицательными")
    pending = [m]
    while pending:
        m = pending.pop()
        if m == 0:
            n += 1
        elif m == 1:
            # A(1, n) = n + 2, поэтому эту линейную ветвь можно свернуть.
            n += 2
        elif n == 0:
            n = 1
            pending.append(m - 1)
        else:
            n -= 1
            pending.extend((m - 1, m))
    return n
