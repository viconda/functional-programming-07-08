"""Практические примеры из лекции, выполняемые последовательно."""


def main() -> None:
    """Выполнить исходные учебные примеры в локальной области."""
    print("\nПример из таблицы 2")

    def fib_memo(n, cache=None):
        cache = {} if cache is None else cache
        if n < 2:
            return n
        if n not in cache:
            cache[n] = fib_memo(n - 1, cache) + fib_memo(n - 2, cache)
        return cache[n]

    print(fib_memo(100))
    print("\nПример из таблицы 4")
    from functools import wraps

    def memoize(func):
        cache = {}

        @wraps(func)
        def wrapper(*args):
            if args not in cache:
                cache[args] = func(*args)
            return cache[args]

        wrapper.cache = cache
        return wrapper

    @memoize
    def grid_paths(rows, cols):
        """Число путей по сетке с движением вправо и вниз."""
        if rows == 1 or cols == 1:
            return 1
        return grid_paths(rows - 1, cols) + grid_paths(rows, cols - 1)

    print(grid_paths(3, 3), grid_paths(18, 18), len(grid_paths.cache))
    print("\nПример из таблицы 6")
    import time
    from functools import cache, lru_cache

    def fib_plain(n):
        return n if n < 2 else fib_plain(n - 1) + fib_plain(n - 2)

    @cache
    def fib_cached(n):
        return n if n < 2 else fib_cached(n - 1) + fib_cached(n - 2)

    t0 = time.perf_counter()
    fib_plain(27)
    t1 = time.perf_counter()
    fib_cached(27)
    t2 = time.perf_counter()
    print(f"без кэша: {t1 - t0:.4f} с, с кэшем: {t2 - t1:.6f} с")
    print(fib_cached.cache_info())

    @lru_cache(maxsize=3)
    def slow_square(x):
        return x * x

    for x in [1, 2, 3, 1, 4, 1, 2]:
        slow_square(x)
    print(slow_square.cache_info())
    print("\nПример из таблицы 9")
    from functools import cache

    def min_coins(coins, amount):
        coins = tuple(coins)

        @cache
        def solve(rest):
            if rest == 0:
                return 0
            if rest < 0:
                return float("inf")
            return 1 + min(solve(rest - c) for c in coins)

        result = solve(amount)
        return -1 if result == float("inf") else result

    def min_coins_bottom_up(coins, amount):
        best = [0] + [float("inf")] * amount
        for s in range(1, amount + 1):
            best[s] = min(
                (best[s - c] + 1 for c in coins if c <= s), default=float("inf")
            )
        return -1 if best[amount] == float("inf") else best[amount]

    print(
        min_coins([1, 5, 10, 20, 50], 93), min_coins_bottom_up([1, 5, 10, 20, 50], 93)
    )
    print(min_coins([4, 7], 5), min_coins_bottom_up([2, 5], 3))
    print("\nПример из таблицы 11")
    from functools import cache

    def lcs(a: str, b: str) -> str:
        @cache
        def go(i, j):
            if i == len(a) or j == len(b):
                return ""
            if a[i] == b[j]:
                return a[i] + go(i + 1, j + 1)
            return max(go(i + 1, j), go(i, j + 1), key=len)

        return go(0, 0)

    print(lcs("ФУНКЦИОНАЛЬНЫЙ", "ФУНДАМЕНТАЛЬНЫЙ"))
    print("\nПример из таблицы 13")
    from functools import cache

    def levenshtein(s: str, t: str) -> int:
        @cache
        def d(i, j):
            if i == 0:
                return j
            if j == 0:
                return i
            cost = 0 if s[i - 1] == t[j - 1] else 1
            return min(
                d(i - 1, j) + 1,  # удаление
                d(i, j - 1) + 1,  # вставка
                d(i - 1, j - 1) + cost,
            )  # замена

        return d(len(s), len(t))

    print(levenshtein("котёнок", "скотина"), levenshtein("python", "pyhton"))
    print("\nПример из таблицы 15")
    from functools import cache

    def knapsack(items, capacity):
        """items — кортеж (название, вес, ценность). Возвращает (ценность, набор)."""

        @cache
        def best(i, cap):
            if i == len(items):
                return 0, ()
            name, w, v = items[i]
            skip = best(i + 1, cap)
            if w > cap:
                return skip
            val, chosen = best(i + 1, cap - w)
            take = (val + v, (name,) + chosen)
            return max(skip, take, key=lambda r: r[0])

        return best(0, capacity)

    items = (
        ("ноутбук", 3, 2000),
        ("камера", 1, 1500),
        ("книга", 1, 300),
        ("гитара", 4, 3000),
        ("наушники", 1, 500),
    )
    print(knapsack(items, 5))
    print("\nПример из таблицы 17")

    def factorial(n):  # не хвостовая: после вызова выполняется умножение
        return 1 if n == 0 else n * factorial(n - 1)

    def factorial_tail(n, acc=1):  # хвостовая: результат вызова возвращается как есть
        return acc if n == 0 else factorial_tail(n - 1, acc * n)

    print(factorial(10) == factorial_tail(10))
    print("\nПример из таблицы 19")

    def factorial_loop(n):
        acc = 1
        while n != 0:  # условие, обратное базовому случаю
            n, acc = n - 1, acc * n  # «рекурсивный вызов» = обновление параметров
        return acc

    print(factorial_loop(10))
    print("\nПример из таблицы 21")

    def trampoline(func, *args):
        result = func(*args)
        while callable(result):
            result = result()
        return result

    def factorial_t(n, acc=1):
        if n == 0:
            return acc
        return lambda: factorial_t(n - 1, acc * n)  # вместо вызова — отложенный шаг

    def is_even_t(n):
        return True if n == 0 else (lambda: is_odd_t(n - 1))

    def is_odd_t(n):
        return False if n == 0 else (lambda: is_even_t(n - 1))

    print(trampoline(factorial_t, 5000).bit_length())  # число двоичных разрядов 5000!
    print(trampoline(is_even_t, 100_001))
    print("\nПример из таблицы 23")
    tree = ("A", [("B", [("D", []), ("E", [])]), ("C", [("F", [])])])

    def dfs_recursive(node):
        name, children = node
        return [name] + [n for child in children for n in dfs_recursive(child)]

    def dfs_stack(root):
        order, stack = [], [root]
        while stack:
            name, children = stack.pop()
            order.append(name)
            stack.extend(reversed(children))  # чтобы обходить детей слева направо
        return order

    print(dfs_recursive(tree), dfs_stack(tree))
    print("\nПример из таблицы 25")

    def walk(node, depth=0):
        name, children = node
        yield depth, name
        for child in children:
            yield from walk(child, depth + 1)

    tree = ("A", [("B", [("D", []), ("E", [])]), ("C", [("F", [])])])
    for depth, name in walk(tree):
        print("  " * depth + name)


if __name__ == "__main__":
    main()
