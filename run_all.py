"""Воспроизводимый запуск всех практических работ и запись фактических результатов."""

import argparse
import contextlib
import hashlib
import inspect
import io
import json
import logging
import platform
import runpy
import statistics
import time
from dataclasses import asdict
from datetime import datetime
from functools import cache, lru_cache, partial
from pathlib import Path
from types import MappingProxyType

from lab07 import deep, dp, plots
from lab07.edit_distance import apply_script, edit_script, lev_plain, lev_table
from lab07.memo import fib_iter, fib_plain, fib_state, make_fib, make_grid, memoize
from lab08 import containers as c
from lab08 import patterns as p
from lab08.compose import compose, pipe, pipe_value, slugify
from lab08.curry import between, convert, curry, replace_all
from lab08.decorators import log_call, retry, timed, ttl_cache, typecheck
from lab08.network import roundtrip_demo
from lab08.orders import make_pipeline, summarize
from lab08.structures import Cons, Queue, from_iter, pop, push, to_tuple


def measure(fn: object, repeat: int = 3) -> float:
    """Нечистая оболочка измерений: медиана независимых запусков."""
    values = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        values.append(time.perf_counter() - start)
    return statistics.median(values)


def fib_count(n: int) -> tuple[int, int]:
    """Вернуть число и фактический счётчик вызовов наивной рекурсии."""
    calls = 0

    def go(k: int) -> int:
        nonlocal calls
        calls += 1
        return k if k < 2 else go(k - 1) + go(k - 2)

    return go(n), calls


def benchmark() -> list[dict]:
    """Измерить n=5..30 с новым кэшем в каждом повторе."""
    records = []
    for n in range(5, 31):
        fn = make_fib(cache)
        expected = fn(n)
        _, calls = fib_count(n)
        assert expected == fib_iter(n)
        records.append(
            {
                "n": n,
                "value": expected,
                "plain": measure(lambda: fib_plain(n)),
                "cached": measure(lambda: make_fib(cache)(n)),
                "iterative": measure(lambda: fib_iter(n)),
                "plain_calls": calls,
                "hits": fn.cache_info().hits,
                "misses": fn.cache_info().misses,
            }
        )
    return records


def run_practice() -> dict:
    """Реально выполнить задания лабораторных и вернуть результаты."""
    out = {}
    distance, ops, info = edit_script("лямбда", "лампа")
    assert distance == len(ops) and apply_script("лямбда", ops) == "лампа"
    surname = edit_script("Швачкина", "Виктория")
    alternatives = [
        edit_script("ab", "ba", order)
        for order in (("delete", "insert", "replace"), ("replace", "insert", "delete"))
    ]
    out["lab07_0"] = {
        "input": ["лямбда", "лампа"],
        "distance": distance,
        "operations": [asdict(x) for x in ops],
        "applied": apply_script("лямбда", ops),
        "cache": info._asdict(),
        "name_input": ["Швачкина", "Виктория"],
        "name_distance": surname[0],
        "name_cache": surname[2]._asdict(),
        "ties": [[d, [asdict(x) for x in o]] for d, o, _ in alternatives],
    }
    comparisons = []
    for label, deco in (("memoize", memoize()), ("lru_cache", lru_cache(None))):
        for name, factory, args in (
            ("fib", make_fib, (30,)),
            ("grid", make_grid, (18, 18)),
        ):
            fn = factory(deco)
            result = fn(*args)
            cold_info = fn.cache_info()._asdict()
            comparisons.append(
                {
                    "decorator": label,
                    "function": name,
                    "result": result,
                    "cache": cold_info,
                    "cold_seconds": measure(lambda: factory(deco)(*args)),
                    "warm_seconds": measure(lambda: fn(*args), 101),
                }
            )
    lru = memoize(3)(lambda x: x * x)
    for n in (1, 2, 3, 1, 4, 1, 2):
        lru(n)
    out["lab07_1"] = {
        "comparison": comparisons,
        "lru_sequence": [1, 2, 3, 1, 4, 1, 2],
        "lru_cache": lru.cache_info()._asdict(),
    }
    items = (
        ("ноутбук", 3, 2000),
        ("камера", 1, 1500),
        ("книга", 1, 300),
        ("гитара", 4, 3000),
        ("наушники", 1, 500),
    )
    out["lab07_2"] = {
        "stairs_n10_steps135": [dp.stairs(10, (1, 3, 5), top) for top in (True, False)],
        "coin_ways_10_125": [dp.coin_ways(10, (1, 2, 5), top) for top in (True, False)],
        "lis_input": [3, 1, 2, 5, 4, 6],
        "lis": [dp.lis((3, 1, 2, 5, 4, 6), top) for top in (True, False)],
        "lcs_input": ["ФУНКЦИОНАЛЬНЫЙ", "ФУНДАМЕНТАЛЬНЫЙ"],
        "lcs": [
            dp.lcs("ФУНКЦИОНАЛЬНЫЙ", "ФУНДАМЕНТАЛЬНЫЙ", top) for top in (True, False)
        ],
        "knapsack_capacity5": [dp.knapsack(items, 5, top) for top in (True, False)],
    }
    xs = tuple(range(100000))
    sum_result = deep.trampoline(deep.sum_tail, xs)
    collatz_start = time.perf_counter()
    lengths = deep.collatz_range(1000000)
    collatz_seconds = time.perf_counter() - collatz_start
    loop_start = time.perf_counter()
    loop_lengths = deep.collatz_range(1000000, False)
    loop_seconds = time.perf_counter() - loop_start
    assert lengths == loop_lengths
    maximum = max(lengths)

    def sum_loop() -> int:
        acc = 0
        for x in xs:
            acc += x
        return acc

    def result_function() -> int:
        return 42

    out["lab07_3"] = {
        "sum_100000": sum_result,
        "sum_trampoline_seconds": measure(lambda: deep.trampoline(deep.sum_tail, xs)),
        "sum_loop_seconds": measure(sum_loop),
        "collatz_checked": len(lengths),
        "collatz_equal": lengths == loop_lengths,
        "collatz_max_start": lengths.index(maximum) + 1,
        "collatz_max_transitions": maximum,
        "collatz_length_including_start": maximum + 1,
        "collatz_1000000": lengths[-1],
        "collatz_trampoline_seconds": collatz_seconds,
        "collatz_loop_seconds": loop_seconds,
        "is_even_1000000": deep.trampoline(deep.is_even, 1000000),
        "is_odd_1000000": deep.trampoline(deep.is_odd, 1000000),
        "function_result_preserved": deep.trampoline(lambda: result_function)
        is result_function,
    }
    tree = deep.Node(
        50,
        deep.Node(30, deep.Node(20), deep.Node(40, deep.Node(35))),
        deep.Node(70, deep.Node(60), deep.Node(80)),
    )
    ack = tuple(deep.ack_stack(2, n) for n in range(1001))
    assert all(value == 2 * n + 3 for n, value in enumerate(ack))
    out["lab07_4"] = {
        "tree_keys_from_lab06": [50, 30, 70, 20, 40, 60, 80, 35],
        "dfs_recursive": deep.dfs_recursive(tree),
        "dfs_stack": deep.dfs_stack(tree),
        "hanoi_n3": deep.hanoi_stack(3),
        "hanoi_equal_0_to8": all(
            deep.hanoi_stack(n) == deep.hanoi_recursive(n) for n in range(9)
        ),
        "ack_values_checked": len(ack),
        "ack_2_1000": ack[-1],
        "ack_recursive_equal_0_to100": all(
            deep.ack_stack(2, n) == deep.ack_recursive(2, n) for n in range(101)
        ),
    }
    records = benchmark()
    out["lab07_5"] = {
        "records": records,
        "repeats": 3,
        "aggregate": "median",
        "cache_policy": "fresh cache per repeat",
        "table": dp.lcs_table("ABCBDAB", "BDCABA"),
    }
    matrix = ((1, 3, 1, 2), (1, 5, 1, 1), (4, 2, 1, 3))
    value, path, info = dp.matrix_path(matrix)
    matrix_times = []
    for size in (5, 10, 20, 40, 80, 120):
        data = tuple(
            tuple(1 + (i * 7 + j * 3) % 9 for j in range(size)) for i in range(size)
        )
        assert dp.matrix_path(data)[:2] == dp.matrix_path(data, False)[:2]
        matrix_times.append(
            {
                "n": size,
                "cached": measure(lambda: dp.matrix_path(data)),
                "iterative": measure(lambda: dp.matrix_path(data, False)),
            }
        )
    out["lab07_6"] = {
        "matrix": matrix,
        "cost": value,
        "path": path,
        "cell_values": [matrix[i][j] for i, j in path],
        "cache": info._asdict(),
        "bottom_up": dp.matrix_path(matrix, False)[:2],
        "timings": matrix_times,
    }
    before = MappingProxyType({})
    value, after = fib_state(100, before)
    out["lab07_extra"] = {
        "fib100": value,
        "old_size": len(before),
        "new_size": len(after),
        "immutable_state_seconds": measure(
            lambda: fib_state(100, MappingProxyType({}))
        ),
        "cache_seconds": measure(lambda: make_fib(cache)(100)),
    }
    out["lab08_1"] = {
        "words": pipe(str.strip, str.lower, str.split, len)("  A B C  "),
        "compose": compose(str.lower, str.strip)("  ЛЯМБДА "),
        "pipe_value": pipe_value(" a b ", str.split, len, lambda x: x * 2),
        "slugify_input": "  Привет,   Мир! Ёж и Щука  ",
        "slugify": slugify("  Привет,   Мир! Ёж и Щука  "),
    }

    @curry
    def defaults(a: int, b: int, *, scale: int = 2) -> int:
        return (a + b) * scale

    out["lab08_2"] = {
        "convert_map": list(map(convert(2)(1), (10, 20, 30))),
        "between_filter": list(filter(between(2)(5), range(8))),
        "replace_map": list(map(replace_all(" ")("_"), ("a b", "c d"))),
        "defaults_early_middle_late": [
            defaults(scale=3)(1)(2),
            defaults(1)(scale=3)(2),
            defaults(1)(2, scale=3),
        ],
        "partial": list(map(partial(convert.__wrapped__, 2, 1), (10, 20, 30))),
        "lambda": list(map(lambda x: x * 2 - 1, (10, 20, 30))),
    }
    fake_time, calls = [0.0], []

    @ttl_cache(5, clock=lambda: fake_time[0])
    def square(n: int) -> int:
        calls.append(n)
        return n * n

    ttl_history = []
    for instant in (0, 4.999, 5, 5):
        fake_time[0] = instant
        ttl_history.append((instant, square(3), len(calls)))
    attempts = []

    @timed
    @log_call("INFO")
    @retry(3, (ConnectionError,))
    def fetch() -> str:
        """Демонстрация восстановления после двух ошибок соединения."""
        attempts.append(1)
        if len(attempts) < 3:
            raise ConnectionError("учебный сбой")
        return "данные"

    @typecheck
    def add(a: int, b: int) -> int:
        return a + b

    type_errors = []
    for value in ("2", True):
        try:
            add(value, 1)
        except TypeError as error:
            type_errors.append(str(error))
    out["lab08_3"] = {
        "fetch": fetch(),
        "attempts": len(attempts),
        "history": fetch.history,
        "name": fetch.__name__,
        "doc": fetch.__doc__,
        "signature": str(inspect.signature(fetch)),
        "ttl": ttl_history,
        "typecheck_valid": add(2, 3),
        "type_errors": type_errors,
    }
    out["lab08_4"] = {
        "present_host": c.config_host({"db": {"replicas": [{"host": "db.example"}]}}),
        "missing_host": c.config_host({"db": {"replicas": []}}),
        "map": repr(c.Some(3).map(lambda x: x + 1)),
        "bind": repr(c.Some(3).bind(lambda x: c.Some(x + 1))),
        "sequence_success": repr(c.sequence([c.Ok(1), c.Ok(2)])),
        "sequence_error": repr(c.sequence([c.Ok(1), c.Err("first"), c.Err("second")])),
        "partition": c.partition_results([c.Ok(1), c.Err("bad"), c.Ok(2)]),
        "try_int": repr(c.try_(int, "abc")),
    }
    order = p.Shipment(2, 10, 25000)
    strategies = (
        p.by_weight(100),
        p.by_distance(30),
        p.fixed(250),
        p.free_over(20000, p.fixed(500)),
    )
    h = p.History().execute(p.insert("abc")).execute(p.move(-2)).execute(p.delete(1))
    out["lab08_5"] = {
        "shipping": [p.shipping(order, s) for s in strategies],
        "min": p.shipping(order, p.combine(min, *strategies)),
        "max": p.shipping(order, p.combine(max, *strategies)),
        "history": [asdict(s) for s in h.states],
        "undo": asdict(h.undo().current),
        "redo": asdict(h.undo().redo().current),
        "branch": asdict(h.undo().execute(p.insert("X")).current),
        "chain_zero": p.chain(1, lambda x: None, lambda x: 0, lambda x: "later"),
    }
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
    process = make_pipeline((("BOOK", 5000), ("PEN", 500)))
    out["lab08_6"] = {"input": lines, **summarize(map(process, lines))}
    out["tcp"] = roundtrip_demo()
    base = from_iter((2, 3, 4))
    a, b = Cons(1, base), Cons(10, base)
    queue = Queue().enqueue("A").enqueue("B").enqueue("C")
    x, q2 = queue.dequeue()
    y, q3 = q2.enqueue("D").dequeue()
    out["lecture08_structures"] = {
        "a": to_tuple(a),
        "b": to_tuple(b),
        "shared_tail": a.tail is b.tail,
        "stack_pop": [pop(push(base, 1))[0], to_tuple(pop(push(base, 1))[1])],
        "queue_first_two": [x, y],
        "queue_remaining": repr(q3),
        "old_queue_preserved": repr(queue),
        "template_method": p.template(" 2 ", str.strip, int, lambda x: x * 3),
    }
    out["lecture07_extra"] = {
        "factorial5000_bits": deep.trampoline(deep.factorial_tail, 5000).bit_length(),
        "walk": list(deep.walk(tree)),
        "min_coins93": dp.min_coins((1, 5, 10, 20, 50), 93),
    }
    return out


def save_outputs(out: dict, root: Path) -> None:
    """Сохранить журналы, входы, графики и страницы просмотра результатов."""
    evidence, data, images = root / "evidence", root / "data", root / "figures"
    for directory in (evidence, data, images, root / "screenshots"):
        directory.mkdir(exist_ok=True)
    payload = json.dumps(out, ensure_ascii=False, indent=2)
    (data / "results.json").write_text(payload, encoding="utf-8")
    for key, value in out.items():
        log = json.dumps(value, ensure_ascii=False, indent=2)
        (evidence / f"{key}.txt").write_text(log, encoding="utf-8")
    plots.plot_times(
        plots.timing_series(out["lab07_5"]["records"]), images / "fib_times.png"
    )
    selected = [
        x for x in out["lab07_5"]["records"] if x["n"] in (5, 10, 15, 20, 25, 30)
    ]
    plots.plot_calls(plots.call_series(selected), images / "fib_calls.png")
    plots.plot_heatmap(
        dp.lcs_table("ABCBDAB", "BDCABA"), "ABCBDAB", "BDCABA", images / "lcs.png", True
    )
    plots.plot_heatmap(
        lev_table("лямбда", "лампа"), "лямбда", "лампа", images / "levenshtein.png"
    )
    series = out["lab07_6"]["timings"]
    plots.plot_times(
        {k: [r[k] for r in series] for k in ("n", "cached", "iterative")},
        images / "matrix_times.png",
        "Размер стороны квадратной матрицы",
    )
    lev_records = [
        {
            "n": n,
            "cached": measure(lambda: edit_script("a" * n, "b" * n)),
            "plain": measure(lambda: lev_plain("a" * n, "b" * n)),
        }
        for n in range(1, 8)
    ]
    (data / "levenshtein_timings.json").write_text(
        json.dumps(lev_records, indent=2), encoding="utf-8"
    )
    plots.plot_times(
        {k: [r[k] for r in lev_records] for k in ("n", "cached", "plain")},
        images / "levenshtein_times.png",
        "Длина слов",
    )
    checksum = hashlib.sha256(payload.encode()).hexdigest()
    (evidence / "results.sha256").write_text(checksum, encoding="utf-8")


def main() -> None:
    """Запустить программу из корневой папки проекта."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--only-examples", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    (root / "evidence").mkdir(exist_ok=True)
    logging.basicConfig(
        filename=root / "evidence" / "calls.log", filemode="w", level=logging.INFO
    )
    out = {
        "environment": {
            "timestamp": datetime.now().astimezone().isoformat(),
            "python": platform.python_version(),
            "platform": platform.platform(),
            "command": "python run_all.py",
            "cwd": str(root),
        }
    }
    if not args.only_examples:
        out.update(run_practice())
    for number in (7, 8):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            runpy.run_path(
                str(root / "lectures" / f"examples{number:02d}.py"), run_name="__main__"
            )
        out[f"lecture{number:02d}_examples"] = {"stdout": buffer.getvalue()}
    for number in (7, 8):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            runpy.run_path(
                str(root / "lectures" / f"lab_example{number:02d}.py"),
                run_name="__main__",
            )
        out[f"lab{number:02d}_example"] = {"stdout": buffer.getvalue()}
    if not args.only_examples:
        save_outputs(out, root)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
