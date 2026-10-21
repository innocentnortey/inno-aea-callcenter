"""AEA-01 AC-6, AC-7 and the ticket's example pair: the composition root and its 27 stubs."""

from __future__ import annotations

import inspect
import types
from typing import Any

import pytest
from fastapi import FastAPI

import meridian.web.container as container_mod
from meridian.policy.limits import Limits
from meridian.web.container import Container, ContainerError, Key, build_container

EXPECTED_HUNKS = (
    ("register_storage", "AEA-10"),
    ("register_web", "AEA-23"),
    ("register_ops", "AEA-32"),
    ("register_tracing", "AEA-19"),
    ("register_spend", "AEA-26"),
    ("register_anthropic", "AEA-17"),
    ("register_jev", "AEA-18"),
    ("register_gateway", "AEA-20"),
    ("register_retrieval", "AEA-33"),
    ("register_tool_dispatch", "AEA-22"),
    ("register_identity", "AEA-27"),
    ("register_scheduling", "AEA-28"),
    ("register_cases", "AEA-29"),
    ("register_demo", "AEA-30"),
    ("register_reset", "AEA-31"),
    ("register_staff_session", "AEA-44"),
    ("register_chat", "AEA-40"),
    ("register_events", "AEA-41"),
    ("register_person_request", "AEA-42"),
    ("register_demo_routes", "AEA-43"),
    ("register_staff_cases", "AEA-45"),
    ("register_staff_live", "AEA-46"),
    ("register_staff_clock", "AEA-47"),
    ("register_metrics_reader", "AEA-53"),
    ("register_reads", "AEA-48"),
    ("register_graph", "AEA-51"),
    ("register_frontend", "AEA-49"),
)

Call = tuple[str, tuple[Any, ...], dict[str, Any]]


def _stand_in() -> Any:
    return types.SimpleNamespace(name="stand-in")


def _spy_all(monkeypatch: pytest.MonkeyPatch) -> list[Call]:
    calls: list[Call] = []
    for name, _ in EXPECTED_HUNKS:

        def spy(*args: Any, _name: str = name, **kwargs: Any) -> None:
            calls.append((_name, args, kwargs))

        monkeypatch.setattr(container_mod, name, spy)
    return calls


def test_every_register_stub_present(monkeypatch: pytest.MonkeyPatch) -> None:
    originals = {
        n: f for n, f in inspect.getmembers(container_mod, inspect.isfunction) if n.startswith("register_")
    }
    assert set(originals) == {n for n, _ in EXPECTED_HUNKS}
    for name, ticket in EXPECTED_HUNKS:
        assert ticket in (originals[name].__doc__ or ""), name
    for name, func in originals.items():
        fresh = Container(settings=_stand_in(), limits=Limits())
        extra = {"overrides": None} if name == "register_graph" else {}
        assert func(fresh, FastAPI(), settings=fresh.settings, limits=fresh.limits, **extra) is None
        fresh.build()  # nothing to build
        assert not fresh._factories

    calls = _spy_all(monkeypatch)
    app = FastAPI()
    c = build_container(app, _stand_in())
    assert [call[0] for call in calls] == [n for n, _ in EXPECTED_HUNKS]
    for _, args, _kw in calls:
        assert args == (c, app)
    print([call[0] for call in calls])


def test_build_and_close_without_adapters(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _spy_all(monkeypatch)
    stand_in = _stand_in()
    c = build_container(FastAPI(), stand_in)
    assert len(calls) == 27
    for _, _args, kwargs in calls:
        assert kwargs["settings"] is stand_in
        assert kwargs["limits"] is c.limits
    assert isinstance(c.limits, Limits)
    assert c.settings is stand_in
    assert not c.closed
    with pytest.raises(ContainerError, match="not provided: uow"):
        c.get(Key[object]("uow"))
    c.close()
    assert c.closed
    c.close()


def test_overrides_reach_register_graph_untouched(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _spy_all(monkeypatch)
    sentinel = object()
    build_container(FastAPI(), _stand_in(), overrides=sentinel)
    graph = [c for c in calls if c[0] == "register_graph"]
    assert len(graph) == 1
    assert graph[0][2]["overrides"] is sentinel
    for name, args, kwargs in calls:
        if name == "register_graph":
            continue
        assert "overrides" not in kwargs
        assert all(v is not sentinel for v in (*args, *kwargs.values()))
    print("sent", id(sentinel), "received", id(graph[0][2]["overrides"]))

    calls.clear()
    build_container(FastAPI(), _stand_in())
    graph = [c for c in calls if c[0] == "register_graph"]
    assert graph[0][2]["overrides"] is None


def test_example_pair_one_limits_object(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _spy_all(monkeypatch)
    build_container(FastAPI(), _stand_in())
    seen = {
        n: kw["limits"] for n, _a, kw in calls if n in {"register_gateway", "register_spend", "register_web"}
    }
    assert len(seen) == 3
    one = next(iter(seen.values()))
    assert all(v is one for v in seen.values())
    assert one.brakes.sonnet_calls == 6
    assert one.spend.daily_cap_usd == 30.0
    assert one.web.chat_turns_per_thread_per_min == 20


def _bare() -> Container:
    return Container(settings=_stand_in(), limits=Limits())


def test_provide_get_builds_once_in_any_order() -> None:
    c = _bare()
    count = {"a": 0}

    def make_a(_: Container) -> int:
        count["a"] += 1
        return 41

    c.provide(Key[int]("B"), lambda cc: cc.get(Key[int]("A")) + 1)
    c.provide(Key[int]("A"), make_a)
    assert c.get(Key[int]("B")) == 42
    c.build()
    assert c.get(Key[int]("A")) == 41
    assert c.get(Key[int]("B")) == 42
    assert count["a"] == 1


def test_unknown_duplicate_and_cycle_raise() -> None:
    c = _bare()
    with pytest.raises(ContainerError, match="not provided: x"):
        c.get(Key[int]("x"))
    c.provide(Key[int]("x"), lambda _: 1)
    with pytest.raises(ContainerError, match="already provided: x"):
        c.provide(Key[int]("x"), lambda _: 2)
    c.provide(Key[int]("A"), lambda cc: cc.get(Key[int]("B")))
    c.provide(Key[int]("B"), lambda cc: cc.get(Key[int]("A")))
    with pytest.raises(ContainerError, match="provider cycle: A -> B -> A"):
        c.get(Key[int]("A"))
    d = _bare()
    d.build()
    with pytest.raises(ContainerError, match="provide after build"):
        d.provide(Key[int]("y"), lambda _: 1)


def test_build_runs_starters_after_every_object() -> None:
    c = _bare()
    seen: list[str] = []
    c.on_start(lambda: seen.append(c.get(Key[str]("late"))))
    c.provide(Key[str]("late"), lambda _: "value")
    c.build()
    assert seen == ["value"]
    with pytest.raises(ContainerError, match="on_start after build"):
        c.on_start(lambda: None)


def test_close_runs_closers_once_newest_first() -> None:
    c = _bare()
    log: list[int] = []

    def bad() -> None:
        raise ValueError("middle")

    c.on_close(lambda: log.append(1))
    c.on_close(bad)
    c.on_close(lambda: log.append(3))
    with pytest.raises(ExceptionGroup):
        c.close()
    assert log == [3, 1]
    c.close()
    assert log == [3, 1]

    ok = _bare()
    order: list[int] = []
    for i in (1, 2, 3):
        ok.on_close(lambda i=i: order.append(i))  # type: ignore[misc]
    ok.close()
    assert order == [3, 2, 1]


def test_failed_build_closes_what_was_opened(monkeypatch: pytest.MonkeyPatch) -> None:
    log: list[str] = []

    def storage(container: Container, app: FastAPI, **_: Any) -> None:
        container.on_close(lambda: log.append("closed"))

    def ops(container: Container, app: FastAPI, **_: Any) -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(container_mod, "register_storage", storage)
    monkeypatch.setattr(container_mod, "register_ops", ops)
    with pytest.raises(RuntimeError, match="boom"):
        build_container(FastAPI(), _stand_in())
    assert log == ["closed"]
