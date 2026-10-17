"""Персистентные связные список, стек и очередь."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Cons:
    """Ячейка с общим неизменяемым хвостом."""
    head: Any
    tail: "Cons | None" = None


def from_iter(xs: tuple) -> Cons | None:
    """Создать связный список в исходном порядке."""
    result = None
    for x in reversed(xs):
        result = Cons(x, result)
    return result


def to_tuple(xs: Cons | None) -> tuple:
    """Преобразовать список в кортеж без рекурсии."""
    out = []
    while xs is not None:
        out.append(xs.head)
        xs = xs.tail
    return tuple(out)


def push(stack: Cons | None, value: Any) -> Cons:
    """Добавить ячейку в стек за O(1)."""
    return Cons(value, stack)


def pop(stack: Cons | None) -> tuple[Any, Cons | None]:
    """Вернуть вершину и оставшийся стек за O(1)."""
    if stack is None:
        raise IndexError("Пустой стек")
    return stack.head, stack.tail


@dataclass(frozen=True)
class Queue:
    """Очередь на двух связных списках с сохранением старых версий."""
    front: Cons | None = None
    back: Cons | None = None

    def enqueue(self, x: Any) -> "Queue":
        """Добавить элемент за O(1)."""
        return Queue(self.front, Cons(x, self.back))

    def dequeue(self) -> tuple[Any, "Queue"]:
        """Извлечь первый элемент; разворот требуется при пустом front."""
        front, back = self.front, self.back
        if front is None:
            while back is not None:
                front, back = Cons(back.head, front), back.tail
        if front is None:
            raise IndexError("Пустая очередь")
        return front.head, Queue(front.tail, back)
