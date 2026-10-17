"""Выполнение исходного примера из лабораторной работы."""


def main() -> None:
    """Выполнить пример преподавателя."""
    from functools import cache

    def edit_script(s: str, t: str) -> tuple[int, tuple[str, ...]]:
        """Минимальное число операций и сами операции, превращающие s в t."""

        @cache
        def go(i: int, j: int) -> tuple[int, tuple[str, ...]]:
            if i == len(s):
                return len(t) - j, tuple(f"вставить '{c}'" for c in t[j:])
            if j == len(t):
                return len(s) - i, tuple(f"удалить '{c}'" for c in s[i:])
            if s[i] == t[j]:
                return go(i + 1, j + 1)
            options = (
                (go(i + 1, j), f"удалить '{s[i]}'"),
                (go(i, j + 1), f"вставить '{t[j]}'"),
                (go(i + 1, j + 1), f"заменить '{s[i]}' на '{t[j]}'"),
            )
            (cost, ops), op = min(options, key=lambda o: o[0][0])
            return cost + 1, (op,) + ops

        result = go(0, 0)
        print("статистика кэша:", go.cache_info())
        return result

    dist, ops = edit_script("лямбда", "лампа")
    print(dist, ops)


if __name__ == "__main__":
    main()
