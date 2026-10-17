"""Стратегии, неизменяемый редактор и цепочка обработчиков."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Shipment:
    """Учебный заказ с массой, расстоянием и суммой."""

    weight: float
    distance: float
    total: float


def by_weight(rate: float) -> Callable:
    """Фабрика тарифа по массе."""
    return lambda order: order.weight * rate


def by_distance(rate: float) -> Callable:
    """Фабрика тарифа по расстоянию."""
    return lambda order: order.distance * rate


def fixed(value: float) -> Callable:
    """Фиксированный тариф."""
    return lambda order: value


def free_over(threshold: float, fallback: Callable) -> Callable:
    """Бесплатная доставка при достижении порога суммы."""
    return lambda order: 0.0 if order.total >= threshold else fallback(order)


def combine(selector: Callable, *strategies: Callable) -> Callable:
    """Выбрать min/max стоимости нескольких стратегий."""
    if not strategies:
        raise ValueError("Нужна хотя бы одна стратегия")
    return lambda order: selector(strategy(order) for strategy in strategies)


def shipping(order: Shipment, strategy: Callable) -> float:
    """Рассчитать доставку выбранной стратегией."""
    return round(strategy(order), 2)


@dataclass(frozen=True)
class State:
    """Текст и курсор между символами."""

    text: str = ""
    cursor: int = 0

    def __post_init__(self) -> None:
        if not 0 <= self.cursor <= len(self.text):
            raise ValueError("Курсор вне текста")


def insert(text: str) -> Callable[[State], State]:
    """Вставить строку перед курсором и сдвинуть курсор вправо."""
    return lambda s: State(
        s.text[: s.cursor] + text + s.text[s.cursor :], s.cursor + len(text)
    )


def delete(n: int) -> Callable[[State], State]:
    """Удалить до n символов справа от курсора."""
    if n < 0:
        raise ValueError("n < 0")
    return lambda s: State(s.text[: s.cursor] + s.text[s.cursor + n :], s.cursor)


def move(k: int) -> Callable[[State], State]:
    """Сдвинуть курсор на k с ограничением границами текста."""
    return lambda s: State(s.text, max(0, min(len(s.text), s.cursor + k)))


@dataclass(frozen=True)
class History:
    """История состояний; ветка redo отсекается новой командой."""

    states: tuple[State, ...] = (State(),)
    index: int = 0

    @property
    def current(self) -> State:
        """Текущее неизменяемое состояние."""
        return self.states[self.index]

    def execute(self, command: Callable[[State], State]) -> "History":
        """Применить команду, сохранив предыдущие версии."""
        return History(
            self.states[: self.index + 1] + (command(self.current),), self.index + 1
        )

    def undo(self) -> "History":
        """Отменить один шаг, если он существует."""
        return History(self.states, max(0, self.index - 1))

    def redo(self) -> "History":
        """Повторить отменённый шаг, если он существует."""
        return History(self.states, min(len(self.states) - 1, self.index + 1))


def chain(request: Any, *handlers: Callable) -> Any:
    """Вернуть первый ответ, отличный от None; 0 и '' тоже ответы."""
    for handler in handlers:
        answer = handler(request)
        if answer is not None:
            return answer
    return None


def template(data: Any, prepare: Callable, process: Callable, finish: Callable) -> Any:
    """Шаблонный метод задаёт каркас и принимает заменяемые этапы."""
    return finish(process(prepare(data)))
