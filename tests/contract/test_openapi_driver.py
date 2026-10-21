"""FIX-W1 driver unit tests: `reference` is sent literally and a stream drive is bounded.

Level: `integrated with a scripted model` (real app on a first-boot DB copy; no model is reached).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, cast

import pytest

import tests.contract.openapi_driver as openapi_driver
from tests.api.openapi_check import load_contract
from tests.api.web_shell_support import demo_pair, session_cookie_value
from tests.contract.cases.staff_live import CASES
from tests.contract.openapi_cases import Drive
from tests.contract.openapi_driver import (
    _checked,
    _resolve_path_param,
    install_exception_tap,
    install_socket_guard,
    real_app,
    run_drive,
    seeded_case_ref,
    send_stream,
)
from tests.contract.openapi_variants import request_examples

_PRECONDITIONS = ["login", "role:representative"]


@pytest.fixture(autouse=True)
def socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    return install_socket_guard(monkeypatch)


@pytest.fixture
def taps(monkeypatch: pytest.MonkeyPatch) -> list[BaseException]:
    return install_exception_tap(monkeypatch)


def _real_drive(operation_id: str, name: str) -> Drive:
    drives = cast(tuple[dict[str, Any], ...], CASES[operation_id]["drives"])
    spec = next(d for d in drives if d["name"] == name)
    return Drive(operation_id, "staff_live", spec)


def test_reference_is_sent_literally(tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        run.main_token = "signed-in"
        drive = Drive("liveChatAction", "staff_live", {"name": "x", "status": 404, "reference": "MHC-C-0099"})
        assert _resolve_path_param(run, drive, "reference", _PRECONDITIONS) == "MHC-C-0099"


def test_path_reference_wins_over_reference_key(tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        spec = {"name": "x", "status": 404, "path": {"reference": "seeded_case"}, "reference": "MHC-C-0099"}
        resolved = _resolve_path_param(
            run, Drive("liveChatAction", "staff_live", spec), "reference", _PRECONDITIONS
        )
        assert resolved == seeded_case_ref(run)
        assert resolved != "MHC-C-0099"


def test_reference_default_is_unchanged_without_the_key(tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        drive = Drive("liveChatAction", "staff_live", {"name": "x", "status": 200})
        run.main_token = "signed-in"
        assert _resolve_path_param(run, drive, "reference", _PRECONDITIONS) == seeded_case_ref(run)
        run.main_token = None
        assert _resolve_path_param(run, drive, "reference", _PRECONDITIONS) == "MHC-C-0001"


def test_unknown_case_request_carries_the_literal_reference(
    tmp_path: Path, taps: list[BaseException], monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[str] = []
    real_send = openapi_driver.send

    def spy(run: Any, operation_id: str, **kwargs: Any) -> Any:
        if operation_id == "liveChatAction":
            seen.append(kwargs["path"])
        return real_send(run, operation_id, **kwargs)

    monkeypatch.setattr(openapi_driver, "send", spy)
    with real_app(tmp_path, taps) as run:
        evidence = run_drive(run, _real_drive("liveChatAction", "unknown_case"))
    assert evidence == "liveChatAction/unknown_case: 404"
    template = load_contract().operations["liveChatAction"].path_template
    assert seen[-1] == template.replace("{reference}", "MHC-C-0099")


def test_stream_unknown_case_answers_404_within_bound(tmp_path: Path, taps: list[BaseException]) -> None:
    started = time.monotonic()
    with real_app(tmp_path, taps) as run:
        evidence = run_drive(run, _real_drive("streamCaseEvents", "unknown_case"))
    assert evidence == "streamCaseEvents/unknown_case: 404"
    assert time.monotonic() - started < 10.0


def test_stream_send_is_bounded_on_an_open_stream(tmp_path: Path, taps: list[BaseException]) -> None:
    with real_app(tmp_path, taps) as run:
        login = _checked(run, "login", 200, "login", token=None, body={"json": dict(demo_pair(run.settings))})
        token = session_cookie_value(login)
        assert token is not None
        _checked(
            run, "switchRole", 200, "switchRole representative",
            token=token, body={"json": request_examples("switchRole")["REPRESENTATIVE"]},
        )  # fmt: skip
        template = load_contract().operations["streamCaseEvents"].path_template
        path = template.replace("{reference}", seeded_case_ref(run))
        started = time.monotonic()
        response = send_stream(run, "streamCaseEvents", path=path, token=token, timeout_s=1.0)
        assert time.monotonic() - started < 5.0
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
