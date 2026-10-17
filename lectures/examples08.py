"""Практические примеры из лекции, выполняемые последовательно."""


def main() -> None:
    """Выполнить исходные учебные примеры в локальной области."""
    print("\nПример из таблицы 1")
    from functools import reduce

    def compose(*funcs):
        """compose(f, g, h)(x) == f(g(h(x))) — справа налево."""
        return reduce(lambda f, g: lambda x: f(g(x)), funcs, lambda x: x)

    def pipe(*funcs):
        """pipe(f, g, h)(x) == h(g(f(x))) — слева направо, в порядке выполнения."""
        return reduce(lambda f, g: lambda x: g(f(x)), funcs, lambda x: x)

    strip = str.strip
    lower = str.lower
    words = str.split
    count = len

    count_words = pipe(strip, lower, words, count)
    normalize = compose(lower, strip)
    print(count_words("   Функциональное программирование на Python  "))
    print(repr(normalize("  ЛЯМБДА ")))
    print("\nПример из таблицы 3")
    from functools import partial

    def pipe(*funcs):
        def run(x):
            for f in funcs:
                x = f(x)
            return x

        return run

    clean_scores = pipe(
        partial(map, str.strip),  # убрать пробелы
        partial(filter, str.isdigit),  # оставить корректные числа
        partial(map, int),  # преобразовать в int
        partial(filter, lambda s: 0 <= s <= 100),  # оставить допустимый диапазон
        sorted,
    )
    print(clean_scores([" 85", "abc", "100 ", "120", "64", " 7"]))
    print("\nПример из таблицы 5")
    import inspect
    from functools import partial

    def curry(func):
        """Автоматическое каррирование по числу обязательных параметров."""
        arity = len(
            [
                p
                for p in inspect.signature(func).parameters.values()
                if p.default is inspect.Parameter.empty
            ]
        )

        def curried(*args):
            if len(args) >= arity:
                return func(*args)
            return lambda *more: curried(*args, *more)

        return curried

    @curry
    def price_with_discount(discount, tax, price):
        return round(price * (1 - discount) * (1 + tax), 2)

    student_price = price_with_discount(0.2)(0.12)  # скидка 20 %, НДС 12 %
    print(student_price(10_000), price_with_discount(0.1, 0.12, 10_000))
    print(list(map(student_price, [1000, 2500])))
    print("\nПример из таблицы 7")
    import time
    from functools import wraps

    def timed(func):
        @wraps(func)  # копирует __name__, __doc__ и др.
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print(f"{func.__name__} выполнена за {elapsed:.4f} с")
            return result

        return wrapper

    @timed
    def slow_sum(n):
        """Сумма квадратов."""
        return sum(i * i for i in range(n))

    slow_sum(1_000_000)
    print(slow_sum.__name__, slow_sum.__doc__)
    print("\nПример из таблицы 9")

    def retry(times=3, exceptions=(Exception,)):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(1, times + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        print(f"попытка {attempt} не удалась: {e}")
                raise RuntimeError(f"{func.__name__}: исчерпано {times} попыток")

            return wrapper

        return decorator

    attempts = iter([ConnectionError("таймаут"), ConnectionError("сброс"), "данные"])

    @retry(times=3, exceptions=(ConnectionError,))
    def fetch():
        value = next(attempts)
        if isinstance(value, Exception):
            raise value
        return value

    print(fetch())
    print("\nПример из таблицы 11")

    def validate(**checks):
        """Проверка именованных аргументов предикатами."""

        def decorator(func):
            @wraps(func)
            def wrapper(**kwargs):
                for name, pred in checks.items():
                    if not pred(kwargs[name]):
                        raise ValueError(
                            f"недопустимое значение {name}={kwargs[name]!r}"
                        )
                return func(**kwargs)

            return wrapper

        return decorator

    def log_call(func):
        @wraps(func)
        def wrapper(**kwargs):
            print(f"вызов {func.__name__}({kwargs})")
            return func(**kwargs)

        return wrapper

    @log_call
    @validate(age=lambda a: 16 <= a <= 99, gpa=lambda g: 0 <= g <= 4)
    def enroll(*, name, age, gpa):
        return f"{name} зачислен(а)"

    print(enroll(name="Аружан", age=18, gpa=3.6))
    try:
        enroll(name="Ерлан", age=12, gpa=3.0)
    except ValueError as e:
        print("Ошибка:", e)
    print("\nПример из таблицы 13")

    def no_discount(total):
        return total

    def student_discount(total):
        return total * 0.8

    def bulk_discount(total):
        return total * 0.9 if total > 50_000 else total

    def checkout(items, pricing=no_discount):
        return round(pricing(sum(price * qty for price, qty in items)), 2)

    cart = [(12_000, 2), (30_000, 1)]
    for strategy in (no_discount, student_discount, bulk_discount):
        print(strategy.__name__, checkout(cart, strategy))
    print("\nПример из таблицы 15")
    from functools import partial

    def move(state, dx, dy):
        x, y = state
        return (x + dx, y + dy)

    commands = [
        partial(move, dx=1, dy=0),
        partial(move, dx=0, dy=2),
        partial(move, dx=-3, dy=1),
    ]

    history = reduce(lambda states, cmd: states + [cmd(states[-1])], commands, [(0, 0)])
    print(history)  # полная история состояний — «отмена» тривиальна
    print("\nПример из таблицы 17")
    from dataclasses import dataclass
    from typing import Any, Callable

    @dataclass(frozen=True)
    class Maybe:
        value: Any = None
        present: bool = False

        @staticmethod
        def of(value):
            return Maybe(value, value is not None)

        def map(self, f: Callable) -> "Maybe":
            return Maybe.of(f(self.value)) if self.present else self

        def get_or(self, default):
            return self.value if self.present else default

    users = {"m.b": {"profile": {"city": "Алматы"}}, "a.k": {"profile": None}}

    def city_of(login):
        return (
            Maybe.of(users.get(login))
            .map(lambda u: u.get("profile"))
            .map(lambda p: p.get("city"))
            .map(str.upper)
            .get_or("город не указан")
        )

    print(city_of("m.b"), "|", city_of("a.k"), "|", city_of("unknown"))
    print("\nПример из таблицы 19")
    from dataclasses import dataclass
    from typing import Any, Callable

    @dataclass(frozen=True)
    class Ok:
        value: Any

        def bind(self, f: Callable) -> "Ok | Err":
            return f(self.value)

    @dataclass(frozen=True)
    class Err:
        error: str

        def bind(self, f: Callable) -> "Ok | Err":
            return self  # ошибка «проходит» мимо остальных шагов

    def parse_int(s):
        return Ok(int(s)) if s.strip().lstrip("-").isdigit() else Err(f"'{s}' не число")

    def check_range(n):
        return Ok(n) if 0 <= n <= 100 else Err(f"{n} вне диапазона 0..100")

    def to_letter(n):
        return Ok("A" if n >= 90 else "B" if n >= 75 else "C" if n >= 60 else "F")

    def grade(raw):
        return parse_int(raw).bind(check_range).bind(to_letter)

    for raw in ["95", "70", "abc", "150"]:
        match grade(raw):
            case Ok(value):
                print(raw, "->", value)
            case Err(error):
                print(raw, "-> ошибка:", error)
    print("\nПример из таблицы 21")
    from typing import Any, NamedTuple, Optional

    class Cons(NamedTuple):
        head: Any
        tail: Optional["Cons"]

    EMPTY = None

    def cons(x, lst):
        return Cons(x, lst)

    def from_iter(xs):
        result = EMPTY
        for x in reversed(list(xs)):
            result = cons(x, result)
        return result

    def to_list(lst):
        out = []
        while lst is not None:
            out.append(lst.head)
            lst = lst.tail
        return out

    base = from_iter([2, 3, 4])
    a = cons(1, base)  # [1, 2, 3, 4]
    b = cons(10, base)  # [10, 2, 3, 4]
    print(to_list(a), to_list(b), a.tail is b.tail)
    print("\nПример из таблицы 23")
    from typing import NamedTuple

    class Queue(NamedTuple):
        front: tuple = ()
        back: tuple = ()

    def enqueue(q, x):
        return Queue(q.front, (x,) + q.back)

    def dequeue(q):
        """Вернуть (элемент, новая очередь)."""
        if not q.front:
            if not q.back:
                raise IndexError("очередь пуста")
            q = Queue(tuple(reversed(q.back)), ())
        return q.front[0], Queue(q.front[1:], q.back)

    q0 = Queue()
    q1 = enqueue(enqueue(enqueue(q0, "A"), "B"), "C")
    x, q2 = dequeue(q1)
    y, q3 = dequeue(enqueue(q2, "D"))
    print(x, y, q3, q1)  # q1 не изменилась


if __name__ == "__main__":
    main()
