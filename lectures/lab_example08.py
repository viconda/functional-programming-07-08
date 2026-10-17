"""Выполнение исходного примера из лабораторной работы."""


def main() -> None:
    """Выполнить пример преподавателя."""
    import re
    from dataclasses import dataclass
    from functools import reduce, wraps
    from typing import Any, Callable

    @dataclass(frozen=True)
    class Ok:
        value: Any

        def map(self, f):
            return Ok(f(self.value))

        def bind(self, f):
            return f(self.value)

    @dataclass(frozen=True)
    class Err:
        error: str

        def map(self, f):
            return self

        def bind(self, f):
            return self

    def pipeline(*steps: Callable[[Any], "Ok | Err"]) -> Callable[[Any], "Ok | Err"]:
        """Связывает шаги, каждый из которых возвращает Ok или Err."""
        return lambda x: reduce(lambda acc, step: acc.bind(step), steps, Ok(x))

    def step(name: str):
        """Декоратор: превращает исключение внутри шага в Err с именем шага."""

        def decorator(func):
            @wraps(func)
            def wrapper(value):
                try:
                    return func(value)
                except Exception as e:
                    return Err(f"{name}: {e}")

            return wrapper

        return decorator

    COURSES = frozenset({"CSE6742", "CSE6501"})

    @step("разбор")
    def parse(line: str):
        name, email, age, course = (p.strip() for p in line.split(";"))
        return Ok({"name": name, "email": email, "age": int(age), "course": course})

    def check(pred: Callable[[dict], bool], message: str):
        return lambda rec: Ok(rec) if pred(rec) else Err(message)

    register = pipeline(
        parse,
        check(
            lambda r: re.fullmatch(r"[\w.]+@[\w.]+\.\w+", r["email"]) is not None,
            "некорректный email",
        ),
        check(lambda r: 16 <= r["age"] <= 60, "возраст вне диапазона 16..60"),
        check(lambda r: r["course"] in COURSES, "неизвестный курс"),
        lambda r: Ok({**r, "login": r["email"].split("@")[0].lower()}),
    )

    requests = [
        "Нурланова Айгерим; a.nurlanova@stud.kz; 19; CSE6742",
        "Петров Иван; petrov@mail; 20; CSE6742",
        "Сейткали Ержан; e.seitkali@stud.kz; 15; CSE6742",
        "Ли Виктор; v.li@stud.kz; двадцать; CSE6501",
        "Омар Дана; d.omar@stud.kz; 22; MATH101",
    ]
    for req, res in zip(requests, map(register, requests)):
        match res:
            case Ok(rec):
                print("ПРИНЯТО  ", rec["login"], rec["course"])
            case Err(msg):
                print("ОТКЛОНЕНО", req.split(";")[0], "—", msg)


if __name__ == "__main__":
    main()
