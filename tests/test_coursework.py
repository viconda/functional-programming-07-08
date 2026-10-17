"""Независимые эталоны, граничные случаи и алгебраические законы."""

import inspect
import itertools
import json
import random
from dataclasses import FrozenInstanceError
from functools import cache, lru_cache
from types import MappingProxyType

import pytest

from lab07 import deep, dp
from lab07.edit_distance import Edit, apply_script, edit_script, lev_table
from lab07.memo import fib_iter, fib_state, make_fib, make_grid, memoize
from lab08.compose import compose, identity, pipe, pipe_value, slugify
from lab08.containers import (
    Err,
    Nothing,
    Ok,
    Some,
    config_host,
    maybe_of,
    partition_results,
    sequence,
    try_,
)
from lab08.curry import between, convert, curry, replace_all
from lab08.decorators import log_call, retry, timed, ttl_cache, typecheck
from lab08.orders import make_pipeline, summarize
from lab08.patterns import (
    History,
    Shipment,
    State,
    by_distance,
    by_weight,
    chain,
    combine,
    delete,
    fixed,
    free_over,
    insert,
    move,
    shipping,
    template,
)
from lab08.protocol import decode_response, process_request
from lab08.structures import Cons, Queue, from_iter, pop, push, to_tuple


def subsequence(a: tuple | str, b: tuple | str) -> bool:
    """Независимо проверить сохранение порядка элементов."""
    iterator = iter(b)
    return all(any(x == y for y in iterator) for x in a)


def test_edit_200_pairs() -> None:
    """200 воспроизводимых пар, обе политики ничьих и применение операций."""
    rng = random.Random(703)
    for _ in range(200):
        a, b = ("".join(rng.choices("абвг", k=rng.randrange(9))) for _ in range(2))
        for order in (("delete", "insert", "replace"), ("replace", "insert", "delete")):
            distance, operations, _ = edit_script(a, b, order)
            assert distance == len(operations) == lev_table(a, b)[-1][-1]
            assert apply_script(a, operations) == b
    left = edit_script("ab", "ba")
    right = edit_script("ab", "ba", ("replace", "insert", "delete"))
    assert left[0] == right[0] == 2 and left[1] != right[1]


def test_edit_invalid() -> None:
    """Ошибочный сценарий нельзя незаметно применить."""
    with pytest.raises(ValueError):
        apply_script("a", (Edit("delete", 0, "b"),))
    with pytest.raises(ValueError):
        edit_script("a", "b", ("insert",))


@pytest.mark.parametrize("size", [None, 0, 1, 3, 128])
def test_lru(size: int | None) -> None:
    """Совпадение с lru_cache, очистка и метаданные."""

    def square(x: int) -> int:
        """Квадрат аргумента."""
        return x * x

    mine, standard = memoize(size)(square), lru_cache(size)(square)
    for x in (1, 2, 3, 1, 4, 1, 2):
        assert mine(x) == standard(x)
    assert mine.cache_info() == standard.cache_info()
    assert mine.__name__ == "square" and mine.__doc__ == square.__doc__
    mine.cache_clear()
    assert mine.cache_info() == (0, 0, size, 0)


def test_memo_keys() -> None:
    """Порядок kwargs не влияет на собственный ключ; списки недопустимы."""

    @memoize()
    def add(a: int, b: int = 0) -> int:
        return a + b

    assert add(a=1, b=2) == add(b=2, a=1) == 3
    assert add.cache_info().hits == 1
    with pytest.raises(TypeError):
        add([])
    with pytest.raises(ValueError):
        memoize(-1)
    for deco in (memoize(), cache):
        assert make_fib(deco)(30) == 832040
        assert make_grid(deco)(18, 18) == 2333606220


def test_dp_200_cases() -> None:
    """По 200 входов для всех пяти пар алгоритмов и варианта 3."""
    rng = random.Random(708)
    for _ in range(200):
        n = rng.randrange(20)
        steps = tuple(rng.sample(range(1, 7), rng.randrange(1, 5)))
        assert dp.stairs(n, steps) == dp.stairs(n, steps, False)
        assert dp.coin_ways(n, steps) == dp.coin_ways(n, steps, False)
        xs = tuple(rng.randrange(-5, 10) for _ in range(rng.randrange(9)))
        length, seq = dp.lis(xs)
        assert (length, seq) == dp.lis(xs, False)
        assert subsequence(seq, xs) and all(a < b for a, b in zip(seq, seq[1:]))
        brute_lis = max(
            (
                len(choice)
                for size in range(len(xs) + 1)
                for choice in itertools.combinations(xs, size)
                if all(a < b for a, b in zip(choice, choice[1:]))
            ),
            default=0,
        )
        assert length == brute_lis
        a, b = ("".join(rng.choices("abc", k=rng.randrange(8))) for _ in range(2))
        common = dp.lcs(a, b)
        assert common == dp.lcs(a, b, False)
        assert subsequence(common, a) and subsequence(common, b)
        brute_lcs = max(
            (
                size
                for size in range(len(a) + 1)
                for choice in itertools.combinations(a, size)
                if subsequence(choice, b)
            ),
            default=0,
        )
        assert len(common) == brute_lcs
        items = tuple(
            (str(i), rng.randrange(1, 6), rng.randrange(-2, 20))
            for i in range(rng.randrange(7))
        )
        cap = rng.randrange(15)
        best, chosen = dp.knapsack(items, cap)
        assert (best, chosen) == dp.knapsack(items, cap, False)
        options = (
            group
            for k in range(len(items) + 1)
            for group in itertools.combinations(items, k)
        )
        brute = max(
            sum(v for _, _, v in g) for g in options if sum(w for _, w, _ in g) <= cap
        )
        assert best == brute
        assert len(chosen) == len(set(chosen))
        assert sum(w for name, w, _ in items if name in chosen) <= cap
        assert sum(v for name, _, v in items if name in chosen) == best
        rows, cols = rng.randrange(1, 6), rng.randrange(1, 6)
        matrix = tuple(
            tuple(rng.randrange(-5, 15) for _ in range(cols)) for _ in range(rows)
        )
        value, path, _ = dp.matrix_path(matrix)
        assert (value, path) == dp.matrix_path(matrix, False)[:2]
        assert sum(matrix[i][j] for i, j in path) == value
        assert path[0] == (0, 0) and path[-1] == (rows - 1, cols - 1)
        assert all(
            (c - a, d - b) in ((1, 0), (0, 1)) for (a, b), (c, d) in zip(path, path[1:])
        )

        def paths(i: int, j: int) -> tuple[int, ...]:
            if i == rows - 1 and j == cols - 1:
                return (matrix[i][j],)
            tails = () if i + 1 == rows else paths(i + 1, j)
            tails += () if j + 1 == cols else paths(i, j + 1)
            return tuple(matrix[i][j] + tail for tail in tails)

        assert value == min(paths(0, 0))


def test_dp_boundaries() -> None:
    """Пустые входы, недостижимая сумма и недопустимые размеры."""
    assert dp.stairs(0, ()) == dp.coin_ways(0, ()) == 1
    assert dp.stairs(1, ()) == dp.coin_ways(1, ()) == 0
    assert dp.lis(()) == (0, ()) and dp.lcs("", "abc") == ""
    for top in (True, False):
        assert dp.min_coins((4, 7), 5, top) == -1
        assert dp.min_coins((1, 5, 10, 20, 50), 93, top) == 6
        with pytest.raises(ValueError):
            dp.stairs(3, (0,), top)
        with pytest.raises(ValueError):
            dp.matrix_path(((1,), (2, 3)), top)


def test_deep_and_stacks() -> None:
    """Сохранение порядка обхода, легальность Ханоя и сравнение Аккермана."""

    def fn():
        return 42

    assert deep.trampoline(lambda: fn) is fn
    assert deep.trampoline(deep.sum_tail, tuple(range(100000))) == 4999950000
    assert deep.trampoline(deep.is_even, 1000000) is True
    assert deep.trampoline(deep.is_odd, 1000000) is False
    assert deep.collatz_range(2000) == deep.collatz_range(2000, False)
    for n in (1, 2, 3, 27, 1000000):
        result = deep.trampoline(deep.collatz_tail, n)
        current, length = n, 0
        while current != 1:
            current = current // 2 if current % 2 == 0 else 3 * current + 1
            length += 1
        assert result == length
    tree = deep.Node(8, deep.Node(3, deep.Node(1), deep.Node(6)), deep.Node(10))
    assert deep.dfs_stack(tree) == deep.dfs_recursive(tree) == (8, 3, 1, 6, 10)
    for n in range(9):
        moves = deep.hanoi_stack(n)
        assert moves == deep.hanoi_recursive(n) and len(moves) == 2**n - 1
        pegs = {"A": list(range(n, 0, -1)), "B": [], "C": []}
        for src, dst in moves:
            disk = pegs[src].pop()
            assert not pegs[dst] or pegs[dst][-1] > disk
            pegs[dst].append(disk)
        assert pegs["C"] == list(range(n, 0, -1))
    for n in range(101):
        assert deep.ack_stack(2, n) == deep.ack_recursive(2, n) == 2 * n + 3
    for n in range(101, 1001):
        assert deep.ack_stack(2, n) == 2 * n + 3


def test_state_memo() -> None:
    """Входной словарь и ранее выданные версии остаются неизменными."""
    old = MappingProxyType({})
    value, new = fib_state(50, old)
    assert value == fib_iter(50) and len(old) == 0 and len(new) == 51
    with pytest.raises(TypeError):
        new[0] = 3


def test_composition_laws() -> None:
    """Законы на совместимых типах для всех пяти заданных функций."""
    triples = [
        (str.lower, str.strip, str.strip, "  PYTHON  "),
        (str.split, str.lower, str.strip, "  A B  "),
        (len, str.split, str.strip, " A B "),
        (lambda x: x * 2, len, str.split, "A B C"),
    ]
    for f, g, h, value in triples:
        assert compose(f, compose(g, h))(value) == compose(compose(f, g), h)(value)
    for f, values in (
        (str.strip, (" a ", "", "  ", " X", "y ")),
        (str.lower, ("A", "Б", "", "MiX", "123")),
        (str.split, ("a b", "", " x ", "1 2 3", "z")),
        (len, ("", "abc", (), (1,), [1, 2])),
        (lambda x: x * 2, (-2, 0, 1, 2, 5)),
    ):
        for x in values:
            assert compose(f, identity)(x) == compose(identity, f)(x) == f(x)
    assert pipe() is compose() is identity
    assert pipe_value(" A B ", str.strip, str.lower, str.split, len) == 2
    assert slugify("  Привет,   Мир! Ёж и Щука  ") == "privet-mir-yozh-i-shchuka"


def test_curry() -> None:
    """Группировка аргументов, defaults, keyword-only и ошибки связывания."""
    assert convert(2)(1)(10) == convert(2, 1, 10) == 19
    assert list(filter(between(2)(5), range(8))) == [2, 3, 4, 5]
    assert replace_all("a")("x")("banana") == "bxnxnx"

    @curry
    def f(a: int, b: int, *, scale: int = 2) -> int:
        return (a + b) * scale

    assert f(scale=3)(1)(2) == f(1)(scale=3)(2) == f(1)(2, scale=3) == 9
    assert f(1)(2) == 6
    with pytest.raises(TypeError):
        f(a=1)(a=2)
    with pytest.raises(TypeError):
        f(1, 2, 3)
    with pytest.raises(TypeError):
        f(unknown=1)

    @curry
    def g(a: int, /, b: int, *, c: int) -> int:
        return a + b + c

    assert g(1)(b=2)(c=3) == 6


def test_decorators() -> None:
    """TTL на точной границе, retries, wraps, история и проверка типов."""
    clock = [0.0]
    calls = []

    @ttl_cache(5, clock=lambda: clock[0])
    def square(n: int) -> int:
        calls.append(n)
        return n * n

    assert square(3) == square(3) == 9 and len(calls) == 1
    clock[0] = 4.999
    square(3)
    assert len(calls) == 1
    clock[0] = 5
    square(3)
    assert len(calls) == 2
    attempts = []

    @timed
    @log_call("INFO")
    @retry(3, (ConnectionError,))
    def flaky() -> str:
        """Тестируемая функция."""
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("test")
        return "ok"

    assert flaky() == "ok" and len(attempts) == 3 and len(flaky.history) == 1
    assert flaky.__name__ == "flaky" and flaky.__doc__ == "Тестируемая функция."
    assert str(inspect.signature(flaky)) == "() -> str"
    errors = []

    @retry(2, (ValueError,))
    def fail() -> None:
        errors.append(1)
        raise ValueError("last")

    with pytest.raises(ValueError, match="last"):
        fail()
    assert len(errors) == 2

    @retry(3, (ConnectionError,))
    def excluded() -> None:
        raise TypeError("not retryable")

    with pytest.raises(TypeError):
        excluded()

    @typecheck
    def add(a: int, b: int = 1) -> int:
        return a + b

    assert add(2) == 3
    with pytest.raises(TypeError):
        add("2")
    with pytest.raises(TypeError):
        add(True)
    with pytest.raises(ValueError):
        retry(0)
    with pytest.raises(ValueError):
        ttl_cache(-1)


@pytest.mark.parametrize("unit,empty", [(Some, Nothing()), (Ok, Err("error"))])
def test_container_laws(unit: type, empty: object) -> None:
    """Все законы для пяти функций и пяти значений, включая пустую ветвь."""
    functions = (
        lambda x: x + 1,
        lambda x: x * 2,
        lambda x: x * x,
        lambda x: x - 3,
        lambda x: -x,
    )
    for value in (-2, 0, 1, 4, 7):
        for f, g in itertools.product(functions, repeat=2):
            for m in (unit(value), empty):
                assert m.map(identity) == m
                assert m.map(f).map(g) == m.map(lambda x: g(f(x)))
                mf, mg = lambda x: unit(f(x)), lambda x: unit(g(x))
                assert unit(value).bind(mf) == mf(value)
                assert m.bind(unit) == m
                assert m.bind(mf).bind(mg) == m.bind(lambda x: mf(x).bind(mg))

    def fail(x):
        return empty if x < 0 else unit(x)

    assert unit(-1).bind(fail).bind(lambda x: unit(x + 1)) == empty


def test_container_helpers() -> None:
    """None, falsy values, short-circuit, первая ошибка и вложенная конфигурация."""
    assert maybe_of(None) == Nothing() and maybe_of(0) == Some(0)
    assert Some(1).map(lambda x: None) == Some(None)
    for m in (Nothing(), Err("stop")):
        assert m.map(lambda x: 1 / 0) is m
        assert m.bind(lambda x: 1 / 0) is m
    assert sequence([]) == Ok([])
    assert sequence([Ok(1), Ok(2)]) == Ok([1, 2])
    assert sequence([Ok(1), Err("first"), Err("second")]) == Err("first")
    assert partition_results([Ok(1), Err("bad"), Ok(2)]) == ([1, 2], ["bad"])
    assert try_(int, "5") == Ok(5) and isinstance(try_(int, "x"), Err)
    assert config_host({"db": {"replicas": [{"host": "db.example"}]}}) == "db.example"
    for config in (
        {},
        {"db": None},
        {"db": {"replicas": []}},
        {"db": {"replicas": [None]}},
    ):
        assert config_host(config) == "localhost"
    with pytest.raises(FrozenInstanceError):
        Some(1).value = 2


def test_patterns_and_structures() -> None:
    """Стоимость, история с ветвлением, общие хвосты и FIFO."""
    order = Shipment(2, 10, 25000)
    choices = (
        by_weight(100),
        by_distance(30),
        fixed(250),
        free_over(20000, fixed(500)),
    )
    assert [shipping(order, s) for s in choices] == [200, 300, 250, 0]
    assert shipping(order, combine(min, *choices)) == 0
    assert shipping(order, combine(max, *choices)) == 300
    h0 = History()
    h1 = h0.execute(insert("abc")).execute(move(-2)).execute(delete(1))
    assert h1.current == State("ac", 1) and h0.current == State()
    assert h1.undo().redo() == h1
    branch = h1.undo().execute(insert("X"))
    assert branch.current.text == "aXbc" and branch.redo() == branch
    assert chain(1, lambda x: None, lambda x: 0, lambda x: "later") == 0
    assert template(" 2 ", str.strip, int, lambda x: x * 3) == 6
    base = from_iter((2, 3, 4))
    a, b = Cons(1, base), Cons(10, base)
    assert a.tail is b.tail and to_tuple(a) == (1, 2, 3, 4)
    assert pop(push(base, 1)) == (1, base)
    q0 = Queue()
    q1 = q0.enqueue("A").enqueue("B").enqueue("C")
    x, q2 = q1.dequeue()
    y, q3 = q2.enqueue("D").dequeue()
    assert (x, y) == ("A", "B") and q0 == Queue()
    assert q3.dequeue()[0] == "C" and q1.dequeue()[0] == "A"


def test_orders() -> None:
    """Пять отдельных проверок, обогащение и распределение причин."""
    process = make_pipeline((("BOOK", 5000), ("PEN", 500)))
    lines = (
        "1;BOOK:4;Алматы, дом 1;card",
        "2;PEN:2;Алматы, дом 2;cash",
        ";PEN:1;Алматы, дом 2;cash",
        "4;UNKNOWN:1;Алматы, дом 2;cash",
        "5;PEN:0;Алматы, дом 2;cash",
        "6;PEN:1;x;cash",
        "7;PEN:1;Алматы, дом 2;crypto",
        "broken",
    )
    result = summarize(map(process, lines))
    assert result["success"] == 2 and result["rejected"] == 6
    assert len(result["errors"]) == 6 and result["orders"][0]["payable"] == 20000
    assert result["orders"][1]["payable"] == 2500
    assert process(lines[0]) == process(lines[0])


@pytest.mark.parametrize(
    "line,value",
    [
        ("CALC 2 + 3", 5),
        ("CALC 7 / 2", 3.5),
        ("UPPER привет", "ПРИВЕТ"),
        ("CONVERT 2 1 10", 19),
    ],
)
def test_protocol_success(line: str, value: object) -> None:
    """Корректные запросы проходят весь чистый конвейер."""
    assert decode_response(process_request(line)) == Ok(value)


@pytest.mark.parametrize(
    "line",
    [
        "",
        "UNKNOWN",
        "CALC 1 / 0",
        "CALC x + 1",
        "CALC 1 ** 2",
        "STATS",
        "STATS nan",
        "UPPER",
        "CONVERT -1 0 2",
        "CONVERT 1 2",
        "x" * 10001,
    ],
)
def test_protocol_errors(line: str) -> None:
    """Ошибки представлены Err и не требуют eval."""
    assert isinstance(decode_response(process_request(line)), Err)


def test_protocol_stats() -> None:
    """Статистика и повреждённый ответ клиента."""
    response = json.loads(process_request("STATS 1 5 7"))
    assert response["value"] == {"count": 3, "min": 1, "max": 7, "mean": 13 / 3}
    assert isinstance(decode_response("bad json"), Err)
