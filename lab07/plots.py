"""Чистая подготовка данных и отдельная оболочка Matplotlib."""

from collections.abc import Iterable
from pathlib import Path


def timing_series(records: Iterable[dict]) -> dict:
    """Преобразовать готовые замеры в столбцы, не обращаясь к часам."""
    rows = tuple(records)
    return {
        key: [row[key] for row in rows] for key in ("n", "plain", "cached", "iterative")
    }


def call_series(records: Iterable[dict]) -> dict:
    """Подготовить число реальных выполнений и обращений к кэшу."""
    rows = tuple(records)
    return {
        key: [row[key] for row in rows]
        for key in ("n", "plain_calls", "misses", "hits")
    }


def plot_times(data: dict, output: Path, xlabel: str = "n") -> None:
    """Только отобразить переданные измерения и сохранить PNG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.3))
    for key, label in (
        ("plain", "Без кэша"),
        ("cached", "Холодный кэш"),
        ("iterative", "Итеративно"),
    ):
        if key in data:
            ax.plot(data["n"], data[key], marker=".", label=label)
    ax.set(xlabel=xlabel, ylabel="Время, с", yscale="log")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_calls(data: dict, output: Path) -> None:
    """Показать вызовы и промахи на логарифмической шкале."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4.3))
    positions = list(range(len(data["n"])))
    ax.bar([x - 0.2 for x in positions], data["plain_calls"], 0.4, label="Без кэша")
    ax.bar(
        [x + 0.2 for x in positions], data["misses"], 0.4, label="Выполнения с кэшем"
    )
    ax.set_xticks(positions, data["n"])
    ax.set(xlabel="n", ylabel="Число выполнений тела функции", yscale="log")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)


def plot_heatmap(
    table: list[list[int]], rows: str, cols: str, output: Path, suffix: bool = False
) -> None:
    """Показать готовую таблицу ДП; вычисления алгоритма здесь нет."""
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 5))
    image = ax.imshow(table, cmap="Blues")
    ax.set_xticks(
        range(len(cols) + 1), list(cols) + ["∅"] if suffix else ["∅"] + list(cols)
    )
    ax.set_yticks(
        range(len(rows) + 1), list(rows) + ["∅"] if suffix else ["∅"] + list(rows)
    )
    for i, row in enumerate(table):
        for j, value in enumerate(row):
            ax.text(
                j,
                i,
                str(value),
                ha="center",
                va="center",
                fontsize=9,
                color="white" if value > max(map(max, table)) * 0.6 else "black",
            )
    fig.colorbar(image, ax=ax)
    fig.tight_layout()
    fig.savefig(output, dpi=160)
    plt.close(fig)
