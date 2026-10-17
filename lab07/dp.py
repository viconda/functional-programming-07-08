"""Парные нисходящие и восходящие решения задач ДП."""

from functools import cache


def positive(values: tuple[int, ...]) -> tuple[int, ...]:
    """Проверить и нормализовать множество шагов или номиналов."""
    if any(v <= 0 for v in values):
        raise ValueError("Ожидаются положительные значения")
    return tuple(sorted(set(values)))


def stairs(n: int, steps: tuple[int, ...], top: bool = True) -> int:
    """Число упорядоченных последовательностей шагов с суммой n."""
    steps = positive(steps)
    if n < 0:
        raise ValueError("n < 0")

    @cache
    def go(k: int) -> int:
        return 1 if k == 0 else sum(go(k - s) for s in steps if s <= k)

    if top:
        return go(n)
    d = [1] + [0] * n
    for k in range(1, n + 1):
        d[k] = sum(d[k - s] for s in steps if s <= k)
    return d[n]


def coin_ways(amount: int, coins: tuple[int, ...], top: bool = True) -> int:
    """Число неупорядоченных разменов с неограниченным числом монет."""
    coins = positive(coins)
    if amount < 0:
        raise ValueError("amount < 0")

    @cache
    def go(i: int, rest: int) -> int:
        if rest == 0:
            return 1
        if i == len(coins):
            return 0
        return go(i + 1, rest) + (go(i, rest - coins[i]) if coins[i] <= rest else 0)

    if top:
        return go(0, amount)
    d = [1] + [0] * amount
    for coin in coins:
        for value in range(coin, amount + 1):
            d[value] += d[value - coin]
    return d[amount]


def lis(xs: tuple[int, ...], top: bool = True) -> tuple[int, tuple[int, ...]]:
    """Длина и одна строго возрастающая подпоследовательность."""
    @cache
    def ending(i: int) -> tuple[int, ...]:
        prefix = max((ending(j) for j in range(i) if xs[j] < xs[i]),
                     key=len, default=())
        return prefix + (xs[i],)

    if top:
        seq = max((ending(i) for i in range(len(xs))), key=len, default=())
    else:
        d: list[tuple[int, ...]] = []
        for i, x in enumerate(xs):
            d.append(max((d[j] for j in range(i) if xs[j] < x),
                         key=len, default=()) + (x,))
        seq = max(d, key=len, default=())
    return len(seq), seq


def lcs_table(a: str, b: str) -> list[list[int]]:
    """Таблица длин LCS для суффиксов, включая пустые границы."""
    d = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(len(a) - 1, -1, -1):
        for j in range(len(b) - 1, -1, -1):
            d[i][j] = (1 + d[i + 1][j + 1] if a[i] == b[j]
                       else max(d[i + 1][j], d[i][j + 1]))
    return d


def lcs(a: str, b: str, top: bool = True) -> str:
    """Восстановить LCS; при ничьей пропустить символ первой строки."""
    @cache
    def go(i: int, j: int) -> str:
        if i == len(a) or j == len(b):
            return ""
        if a[i] == b[j]:
            return a[i] + go(i + 1, j + 1)
        return max(go(i + 1, j), go(i, j + 1), key=len)

    if top:
        return go(0, 0)
    d = lcs_table(a, b)
    i = j = 0
    out: list[str] = []
    while i < len(a) and j < len(b):
        if a[i] == b[j]:
            out.append(a[i]); i += 1; j += 1
        elif d[i + 1][j] >= d[i][j + 1]:
            i += 1
        else:
            j += 1
    return "".join(out)


def knapsack(items: tuple[tuple[str, int, int], ...], capacity: int,
             top: bool = True) -> tuple[int, tuple[str, ...]]:
    """Рюкзак 0/1 с восстановлением; одинаковые предметы различает индекс."""
    if capacity < 0 or any(w <= 0 for _, w, _ in items):
        raise ValueError("Недопустимая вместимость или масса")

    @cache
    def go(i: int, cap: int) -> tuple[int, tuple[str, ...]]:
        if i == len(items):
            return 0, ()
        name, w, v = items[i]
        skip = go(i + 1, cap)
        if w > cap:
            return skip
        val, chosen = go(i + 1, cap - w)
        return max(skip, (val + v, (name,) + chosen), key=lambda x: x[0])

    if top:
        return go(0, capacity)
    d = [[(0, ()) for _ in range(capacity + 1)] for _ in range(len(items) + 1)]
    for i in range(len(items) - 1, -1, -1):
        name, w, v = items[i]
        for cap in range(capacity + 1):
            d[i][cap] = d[i + 1][cap]
            if w <= cap:
                val, chosen = d[i + 1][cap - w]
                d[i][cap] = max(d[i][cap], (val + v, (name,) + chosen),
                               key=lambda x: x[0])
    return d[0][capacity]


def min_coins(coins: tuple[int, ...], amount: int, top: bool = True) -> int:
    """Минимальное число монет или -1, если размен невозможен."""
    coins = positive(coins)
    if amount < 0:
        raise ValueError("amount < 0")
    infinity = amount + 1

    @cache
    def go(n: int) -> int:
        return 0 if n == 0 else min((1 + go(n - c) for c in coins if c <= n),
                                   default=infinity)

    if top:
        result = go(amount)
    else:
        d = [0] + [infinity] * amount
        for n in range(1, amount + 1):
            d[n] = min((1 + d[n - c] for c in coins if c <= n), default=infinity)
        result = d[amount]
    return result if result < infinity else -1


def matrix_path(matrix: tuple[tuple[int, ...], ...], top: bool = True) -> tuple:
    """Вариант 3: стоимость, путь по индексам и статистика кэша."""
    if not matrix or not matrix[0] or any(len(r) != len(matrix[0]) for r in matrix):
        raise ValueError("Нужна непустая прямоугольная матрица")
    m, n = len(matrix), len(matrix[0])

    @cache
    def go(i: int, j: int) -> int:
        if i == 0 and j == 0:
            return matrix[0][0]
        candidates = ([go(i - 1, j)] if i else []) + ([go(i, j - 1)] if j else [])
        return matrix[i][j] + min(candidates)

    if top:
        value = go(m - 1, n - 1)
        get = go
    else:
        d = [[0] * n for _ in range(m)]
        for i in range(m):
            for j in range(n):
                prev = ([d[i - 1][j]] if i else []) + ([d[i][j - 1]] if j else [])
                d[i][j] = matrix[i][j] + min(prev, default=0)
        value = d[-1][-1]
        get = lambda i, j: d[i][j]
    i, j = m - 1, n - 1
    path = [(i, j)]
    while i or j:
        if i and (not j or get(i - 1, j) <= get(i, j - 1)):
            i -= 1
        else:
            j -= 1
        path.append((i, j))
    return value, tuple(reversed(path)), go.cache_info() if top else None
