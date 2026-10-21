"""AEA-46 units that need no app: request rules, WP-2 bodies and frames, id parsing and the poll loop."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import anyio
import anyio.lowlevel
import pytest
from pydantic import JsonValue, ValidationError

from meridian.adapters.sqlite import rows
from meridian.domain.common import CaseRef
from meridian.services.live_chat import LiveView, StoredChatLine
from meridian.web.routes.staff_live import (
    case_event_frames,
    case_stream_key,
    parse_case_ref,
)
from meridian.web.schemas.staff_live import (
    HEARTBEAT_FRAME,
    MAX_LIVE_TEXT_CHARS,
    LiveActionRequest,
    encode_case_frame,
    live_action_response,
    parse_last_event_id,
)
from tests.api.openapi_check import load_document
from tests.fakes.clock import CHICAGO
from tests.services.live_chat_support import STAFF_TEXT


def _errors(payload: dict[str, Any]) -> list[Any]:
    with pytest.raises(ValidationError) as caught:
        LiveActionRequest.model_validate(payload)
    text = payload.get("text")
    if isinstance(text, str) and text.strip():
        assert text not in str(caught.value)  # hide_input_in_errors: the text is not echoed
    return caught.value.errors()


@pytest.mark.parametrize(
    ("payload", "loc", "msg"),
    [
        ({"action": "send", "text": None}, ("text",), "required for send"),
        ({"action": "send"}, ("text",), "required for send"),
        ({"action": "send", "text": "   "}, ("text",), "required for send"),
        ({"action": "send", "text": "a" * 2001}, ("text",), "at most 2000 characters"),
        ({"action": "join", "text": "placeholder"}, ("text",), "only for send"),
        ({"action": "wave"}, ("action",), None),
    ],
)
def test_text_rules_table(payload: dict[str, Any], loc: tuple[str, ...], msg: str | None) -> None:
    first = _errors(payload)[0]
    assert first["loc"] == loc
    if msg is not None:
        assert first["msg"] == msg


def test_text_rules_accepted() -> None:
    assert LiveActionRequest.model_validate({"action": "send", "text": "  hi  "}).text == "hi"
    assert LiveActionRequest.model_validate({"action": "join"}).text is None
    assert LiveActionRequest.model_validate({"action": "send", "text": "a" * 2000}).text == "a" * 2000
    assert MAX_LIVE_TEXT_CHARS == 2000


def _at(h: int, m: int, s: int = 0) -> datetime:
    return datetime(2026, 10, 16, h, m, s, tzinfo=CHICAGO)


def _wire(value: Any) -> Any:
    """The OpenAPI loader may hand back datetimes for YAML timestamps; the wire form is ISO text."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _wire(v) for k, v in value.items()}
    return value


def test_wp2_bodies_equal_openapi_examples() -> None:
    """PA-7: the four 200 bodies equal the OpenAPI examples JOINED, SENT, HANDED_BACK, CLOSED."""
    doc = load_document()
    examples = doc["paths"]["/api/staff/cases/{reference}/live"]["post"]["responses"]["200"]["content"][
        "application/json"
    ]["examples"]
    views = {
        "JOINED": LiveView(
            controller_kind="human", controller_name="Riley", state="joined", since=_at(14, 22)
        ),
        "SENT": LiveView(
            controller_kind="human",
            controller_name="Riley",
            state="joined",
            since=_at(14, 22),
            message=StoredChatLine(
                message_id="m-88", speaker_name="Riley", at=_at(14, 22, 40), text=STAFF_TEXT
            ),
        ),
        "HANDED_BACK": LiveView(
            controller_kind="ai", controller_name=None, state="handed_back", since=_at(14, 22)
        ),
        "CLOSED": LiveView(controller_kind="ai", controller_name=None, state="closed", since=_at(14, 23)),
    }
    for name, view in views.items():
        assert live_action_response(view).model_dump(mode="json") == _wire(examples[name]["value"]), name


@dataclass(frozen=True)
class _Row:
    id: int
    type: str
    payload: Mapping[str, JsonValue]
    at: datetime


def test_case_frames_equal_openapi_example() -> None:
    """PA-7: the CON-21 frames equal the FRAMES example byte for byte."""
    doc = load_document()
    text = doc["paths"]["/api/staff/cases/{reference}/events"]["get"]["responses"]["200"]["content"][
        "text/event-stream"
    ]["examples"]["FRAMES"]["value"]
    message = json.loads(text.split("data: ")[1].split("\n")[0])["message"]
    a = _Row(5, "customer_message", {"message": message}, _at(14, 23, 10))
    b = _Row(6, "chat_closed", {"reason": "closed_by_staff"}, _at(14, 24))
    assert (encode_case_frame(a) + encode_case_frame(b)).decode().rstrip("\n") == text.rstrip("\n")


def test_parse_last_event_id() -> None:
    assert parse_last_event_id(None) is None
    assert (parse_last_event_id("30"), parse_last_event_id(" 7 "), parse_last_event_id("0")) == (30, 7, 0)
    for bad in ("abc", "-3", "12abc", "+5", "", "9" * 19):
        assert parse_last_event_id(bad) is None, bad


def test_parse_case_ref() -> None:
    assert parse_case_ref("MHC-C-0007") == "MHC-C-0007"
    for bad in ("mhc-c-0007", "MHC-C-7", "MHC-C-00071"):
        assert parse_case_ref(bad) is None, bad


def test_case_stream_key_matches_rows() -> None:
    ref = CaseRef("MHC-C-0007")
    assert case_stream_key(ref) == rows.case_stream(ref) == "case:MHC-C-0007"


# -- the poll loop ------------------------------------------------------------------------------------------------
class FakeTime:
    """sleep() advances the clock and yields to the loop; nothing sleeps for real."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    async def sleep(self, seconds: float) -> None:
        self.now += seconds
        await anyio.lowlevel.checkpoint()


class Reads:
    """A scripted read_after: each call returns the next batch and records the `last` it was given."""

    def __init__(self, batches: Sequence[tuple[int, Sequence[_Row]]]) -> None:
        self.batches = list(batches)
        self.lasts: list[int | None] = []

    async def __call__(self, last: int | None) -> tuple[int, Sequence[_Row]]:
        self.lasts.append(last)
        if self.batches:
            return self.batches.pop(0)
        return (last or 0, [])


def _loop(
    reads: Reads,
    clock: FakeTime,
    *,
    start: int | None = None,
    held: Any = lambda: False,
    heartbeat_s: float = 15.0,
    on_replayed: Any = None,
) -> AsyncIterator[bytes]:
    async def never() -> bool:
        return False

    return case_event_frames(
        start=start,
        read_after=reads,
        reset_held=held,
        disconnected=never,
        poll_s=1.0,
        heartbeat_s=heartbeat_s,
        on_replayed=on_replayed,
        monotonic=clock.monotonic,
        sleep=clock.sleep,
    )


def _row(i: int, kind: str, payload: Mapping[str, JsonValue] | None = None) -> _Row:
    return _Row(i, kind, payload or {}, _at(14, 22))


def test_loop_skips_reads_while_held() -> None:
    """AC-16 at unit level: no read while the gate is held; nothing but heartbeats; then one read."""
    polls = {"n": 0}

    def held() -> bool:
        polls["n"] += 1
        return polls["n"] <= 3

    async def scenario() -> tuple[list[bytes], Reads]:
        reads = Reads([(1, [_row(1, "demo_reset")])])
        frames = [f async for f in _loop(reads, FakeTime(), held=held, heartbeat_s=2.0)]
        return frames, reads

    frames, reads = anyio.run(scenario)
    assert reads.lasts == [None]  # exactly one read, after the gate cleared
    assert frames[-1].startswith(b"id: 1\n")
    assert all(f == HEARTBEAT_FRAME for f in frames[:-1])


def test_loop_closes_after_demo_reset_not_chat_closed() -> None:
    async def collect(batch: list[_Row], rounds: int) -> tuple[list[bytes], Reads]:
        reads = Reads([(batch[-1].id, batch)])
        frames: list[bytes] = []
        clock = FakeTime()
        gen = _loop(reads, clock, heartbeat_s=1e9)
        with anyio.move_on_after(0.5):
            async for frame in gen:
                frames.append(frame)
                if len(frames) >= rounds:
                    break
            await gen.aclose()  # type: ignore[attr-defined]
        return frames, reads

    async def scenario() -> None:
        frames, reads = await collect(
            [_row(1, "chat_closed", {"reason": "closed_by_staff"}), _row(2, "case_changed")], 2
        )
        assert len(frames) == 2
        assert len(reads.lasts) >= 1
        frames, _ = await collect([_row(3, "demo_reset"), _row(4, "case_changed")], 5)
        assert [f.split(b"\n")[0] for f in frames] == [b"id: 3"]

    anyio.run(scenario)


def test_loop_closes_generator_after_demo_reset() -> None:
    async def scenario() -> list[bytes]:
        reads = Reads([(4, [_row(3, "demo_reset"), _row(4, "case_changed")])])
        return [frame async for frame in _loop(reads, FakeTime())]

    frames = anyio.run(scenario)
    assert len(frames) == 1 and frames[0].startswith(b"id: 3\n")


def test_loop_skips_foreign_types_and_advances() -> None:
    async def scenario() -> Reads:
        reads = Reads([(7, [_row(7, "staff_message")]), (7, [_row(8, "demo_reset")])])
        frames = [f async for f in _loop(reads, FakeTime())]
        assert len(frames) == 1 and frames[0].startswith(b"id: 8\n")
        return reads

    reads = anyio.run(scenario)
    assert reads.lasts[:2] == [None, 7]


def test_loop_heartbeat_after_idle() -> None:
    async def scenario() -> tuple[bytes, float, int]:
        clock, reads = FakeTime(), Reads([])
        async for item in _loop(reads, clock, heartbeat_s=15.0):
            return item, clock.now, len(reads.lasts)
        raise AssertionError("no item")

    item, at, polls = anyio.run(scenario)
    assert item == HEARTBEAT_FRAME
    assert at >= 15.0 and polls >= 15


def test_start_none_resolved_by_first_read() -> None:
    async def scenario() -> Reads:
        reads = Reads([(12, []), (12, [_row(13, "demo_reset")])])
        [f async for f in _loop(reads, FakeTime(), start=None)]
        return reads

    assert anyio.run(scenario).lasts[:2] == [None, 12]


def test_on_replayed_called_once() -> None:
    async def scenario() -> list[int]:
        calls: list[int] = []
        reads = Reads([(2, [_row(1, "case_changed"), _row(2, "case_changed")]), (3, [_row(3, "demo_reset")])])
        [f async for f in _loop(reads, FakeTime(), start=0, on_replayed=calls.append)]
        return calls

    assert anyio.run(scenario) == [2]


def test_on_replayed_zero_when_closed_before_any_read() -> None:
    async def scenario() -> list[int]:
        calls: list[int] = []
        gen = _loop(Reads([]), FakeTime(), held=lambda: True, on_replayed=calls.append)
        with anyio.move_on_after(0.05):
            async for _ in gen:
                pass
        await gen.aclose()  # type: ignore[attr-defined]
        return calls

    assert anyio.run(scenario) == [0]
