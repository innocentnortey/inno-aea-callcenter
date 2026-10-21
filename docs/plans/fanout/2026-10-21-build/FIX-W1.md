# Plan — [FIX-W1] Wave-1 audit fixes: contract driver honours `reference` and bounds stream drives; J-7 reports blocked on AEA-51

**Status:** planned (READY) · **Lane:** `lane::build-loop` (test code only; not `risk::security`: no auth, secret, PII or
network surface changes; nothing under `src/` is edited)
**Issue:** wave-fix item from the wave-1 seam audit (no GitLab issue) · **Base revision:** `main` `eb51ba4`
**Planner model:** claude-opus-5-5 · **Implementer:** `fanout-implementer` (Sonnet)

## Goal

Two findings from the wave-1 audit, both making the wave-merge gate red on `main`:

1. **[high] Contract driver seam (AEA-59 driver × AEA-46 case file).** `tests/contract/cases/staff_live.py` gives the
   two `unknown_case` drives a top-level `"reference": "MHC-C-0099"`, and `tests/contract/cases/README.md` §2 documents
   that key as "A case reference, sent literally". `tests/contract/openapi_driver.py::_resolve_path_param` ignores it and,
   when logged in, substitutes `seeded_case_ref(run)` (a real seeded case). Result: `liveChatAction/unknown_case` gets
   403 `NOT_CLAIMED_BY_YOU` instead of 404 `CASE_NOT_FOUND`, and `streamCaseEvents/unknown_case` opens a real SSE stream
   through `TestClient.request`, which never returns, so the contract suite hangs.
   **Fix:** honour `drive.spec["reference"]` literally, and send every drive of an event-stream operation through a
   bounded read so a stream that should have answered an error fails the drive instead of hanging.
2. **[high] J-7 fails instead of reporting blocked (AEA-30 × AEA-51).**
   `tests/journeys/j7/test_aea_30.py::test_j7_shift_end_converts_queued_case` calls `startChatSession`, which answers an
   undocumented 500 on the assembled app because `Key("reply_composer")` is not provided until AEA-51
   (`register_chat`'s `lazy()` raises `RuntimeError("not bound: reply_composer")`). Other journeys declare
   `reply_composer` in their step `needs` and skip `blocked-on AEA-51`. **Fix:** J-7's step 2 declares the same needs,
   so the harness's `missing_needs` skips it with `blocked-on AEA-51: reply_composer not bound`. The 500 itself is
   expected until AEA-51 lands and is **not** fixed here.

## Context

AEA-59 (driver) and AEA-46 (case file) were built in parallel. AEA-46 wrote the `reference` key the README documents, but
the driver only reads `path`. J-7 was written while AEA-40 and AEA-43 were open; both are now merged, so the test gets
further and hits the AEA-51 gap with no `needs` guard. Both are seams between merged tickets. This plan fixes only the
test side. No route, service or contract changes.

## Sources checked

| Source | Location | What it obliges here |
|---|---|---|
| Requirements | n/a: test-harness fix; no product behaviour changes | — |
| Component contracts | `docs/design/contracts/stage7/staff.md` §5 table row 1 ("no such case → `CASE_NOT_FOUND` {reference} (404)"), §7 step 1 ("unknown case → 404 before the stream starts"); OpenAPI `liveChatAction` / `streamCaseEvents` 404 | The expected result of both `unknown_case` drives: 404 `CASE_NOT_FOUND`, a JSON error body, no stream |
| Case format | `tests/contract/cases/README.md` §2 (drive keys: `path`, `reference`), §4 (path words), §6 (skip reasons) | `reference` is sent literally; the only skip reasons stay `route not registered: …` and `not bound: …` |
| Test layout | `docs/design/code-design.md` §9 (`contract/`, `journeys/`) | New driver unit test lives in `tests/contract/`; journey stays in `tests/journeys/j7/` |
| Journey rules | `.claude/rules/integrated-journeys.md` §3 rule 5 (reproduce, then protect), §4 (levels, record) | Reproduce both failures first; write a record at `docs/testing/journeys/2026-10-21-FIX-W1.md` |
| Test scope | `.claude/rules/build-loop-test-scope.md` incl. *AEA addition* | Affected tests + fast gates + affected journeys; no full suite (no shared fixture, settings or lockfile changes) |
| Harness | `tests/journeys/support/steps.py` (`NEED_OWNERS["reply_composer"] = "AEA-51"`, `missing_needs`, `blocked_message`), `tests/journeys/support/run.py` (`JourneyRun.step`) | J-7 reuses the existing `needs=` mechanism; no harness edit |
| Evaluation plan / Observability / Metrics | DO-5, DO-6, DO-7 | n/a: no entry point, workflow, eval case or metric changes |
| Signed decisions | `docs/plans/stage7-signoff.md` D-4…D-15 | None touched |

## Source-contract reconciliation

| Obligation | Governing source | In finding | Disposition | Plan step or owner |
|---|---|---|---|---|
| `reference` drive key sent literally | cases/README.md §2 | yes | in-ticket | Step 2 |
| When both `path.reference` and `reference` are given, one wins deterministically | (gap: README silent) | no | added: `path` wins; README row says so | Step 2, Step 6 |
| Existing defaults unchanged when `reference` is absent (logged in → seeded case; else `MHC-C-0001`) | current driver behaviour; `test_validation_error_matches_contract` relies on `path: seeded_case` | no | added (regression test) | Step 5 tests 2–3 |
| Unknown case → 404 `CASE_NOT_FOUND` before any frame | staff.md §5 row 1, §7 step 1 | yes | in-ticket (the route already does it; the drive now reaches it) | Steps 2, 4 |
| A stream drive never hangs the suite | finding (per-drive timeout) | yes | in-ticket | Steps 1, 3, 4 |
| Skip reasons stay exactly the two documented ones | cases/README.md §6 | no | added: `send_stream` uses the same `blocked(...)` reasons as `send` | Step 3 |
| J-7 skip names AEA-51 via `missing_needs` | finding; steps.py | yes | in-ticket | Step 7 |
| Test files ≤ 500 lines (hard cap) | workspace `code-structure.md` §1 | no | added: move the ASGI stream reader to `tests/contract/openapi_sse.py` (driver is 462 lines today) | Step 1 |
| Area map lists the new test-support file | `context-maintenance.md` rule 1 | no | added | Step 8 |
| Evidence record with level | integrated-journeys §4 | no | added | Step 9 |

## Entry-point registration

| Entry point | Workflow | Registered in contract | Inherits |
|---|---|---|---|
| None | — | — | — |

## Acceptance criteria

1. **AC-1** `liveChatAction/unknown_case` and `streamCaseEvents/unknown_case` both pass: 404 `CASE_NOT_FOUND`, each in
   under 10 s. *Verify:* `timeout 120 uv run pytest tests/contract/test_openapi_server.py -k "unknown_case" -rs --durations=0`
   → both `test_route_cases_match_contract[…/unknown_case]` passed; each duration < 10 s; exit 0. Same with
   `CONTRACT_STRICT=1`.
2. **AC-2** A unit test proves a literal reference is sent: `tests/contract/test_openapi_driver.py::test_unknown_case_request_carries_the_literal_reference`
   (the request path holds `MHC-C-0099`) and `::test_reference_is_sent_literally` pass.
3. **AC-3 (plan-added)** A stream drive is bounded: `::test_stream_send_is_bounded_on_an_open_stream` passes (an open
   SSE stream on a real seeded case returns from `send_stream(..., timeout_s=1.0)` in < 5 s with status 200).
4. **AC-4 (plan-added)** No regression in the contract runner: `tests/contract/test_openapi_server.py` after the change
   has exactly the baseline counts (Step 0) plus `liveChatAction/unknown_case` moved from failed to passed and
   `streamCaseEvents/unknown_case` added as passed. No other drive changes outcome or skip reason.
5. **AC-5 [journey] (level: `integrated with a scripted model`; steps 2–3 `Blocked by` AEA-51)** `uv run pytest tests/journeys/j7 -rs`
   reports **0 failed**, and `test_j7_shift_end_converts_queued_case` is **skipped** with reason
   `blocked-on AEA-51: reply_composer not bound` (step 1 "staffing on" passes before the skip). The finding names
   revision `3725c90`, but `main` has moved on. Verify on this branch, which is cut from `eb51ba4`.
6. **AC-6 (plan-added)** Record `docs/testing/journeys/2026-10-21-FIX-W1.md` exists with every §4 field.

**WP-N worked pair:** none applies. This is a test-harness fix with no customer-facing behaviour, so no WP-1…WP-8 case
moves. Its worked pair is the two reproduction/protection pairs: (a) the `unknown_case` drives (red 403 / hang →
green 404) and (b) J-7 (red 500 → skipped `blocked-on AEA-51`).

## File map

| File | Current or planned | Change |
|---|---|---|
| `tests/contract/openapi_sse.py` | **new** | `STREAM_READ_TIMEOUT_S`, `SseRead` (+ `headers`, `body`), `read_asgi_stream` (moved from the driver's `_read_sse`), `as_response` |
| `tests/contract/openapi_driver.py` | current (462 lines) | import from `openapi_sse`; delete the moved code; `_resolve_path_param` honours `reference`; new `send_stream`; `run_drive` routes stream drives through it |
| `tests/contract/test_openapi_driver.py` | **new** | 6 unit tests (Step 5) |
| `tests/contract/cases/README.md` | current | §2 `reference` row: add the precedence sentence |
| `tests/journeys/j7/test_aea_30.py` | current | docstring; step 2 `needs` |
| `.claude/reference/area-map.md` | current | row "Integration and journeys": add `openapi_sse` to the `tests/contract/{…}.py` list |
| `docs/testing/journeys/2026-10-21-FIX-W1.md` | **new** | evidence record |

**Read-only shared surfaces (never edit):** `tests/contract/cases/staff_live.py` (AEA-46; it is correct),
`tests/contract/openapi_cases.py`, `tests/contract/openapi_variants.py`, `tests/contract/test_openapi_server.py`,
`tests/api/openapi_check.py`, `tests/api/web_shell_support.py`, `tests/journeys/support/**`, `tests/journeys/browser/**`,
every other `tests/journeys/j*/` file, everything under `src/`, `docs/design/**`, `ui-contracts.openapi.yaml`,
`UI_CONTRACTS.md`, `apps/web/**`, `docs/ux/**`, `docs/archive/`, `docs/parked/`, the briefing and issued data.

## Shared code to use (copied from `main` `eb51ba4`)

```python
# tests/contract/openapi_cases.py
@dataclass(frozen=True)
class Drive:
    operation_id: str
    file: str
    spec: Mapping[str, Any]
    @property
    def id(self) -> str: ...            # f"{operation_id}/{spec['name']}"
    @property
    def status(self) -> int: ...
PATH_WORDS: Final = frozenset({"started", "unknown", "malformed", "other_session", "ended", "seeded_case"})

# tests/contract/openapi_driver.py (kept as is)
def blocked(reason: str) -> NoReturn
def install_exception_tap(monkeypatch: pytest.MonkeyPatch) -> list[BaseException]
def install_socket_guard(monkeypatch: pytest.MonkeyPatch) -> list[str]
@dataclass
class AppRun:  # app, client, settings, registered, taps, main_token=None, main_thread=None, other_thread=None, event_ids
@contextmanager
def real_app(tmp_path: Path, taps: list[BaseException]) -> Iterator[AppRun]
def send(run, operation_id, *, path: str, token: str | None, body: Mapping[str, Any] | None,
         extra_headers: Mapping[str, str] | None = None) -> Any
def _checked(run, operation_id, expect: int, what: str, **kwargs) -> Any
def seeded_case_ref(run: AppRun) -> str          # first row of cases ORDER BY case_ref (MHC-C-0005 on a first boot)
def run_drive(run: AppRun, drive: Drive) -> str  # returns f"{drive.id}: {status}"

# tests/api/openapi_check.py
class SseFrame: event: str | None; id: str | None; data: str
def assert_response_matches(response: _ResponseLike, operation_id: str) -> None
#   _ResponseLike needs .status_code, .headers (with X-Request-ID), .content, .json()
def load_contract() -> ...  # .operations[op] has .method, .path_template, .responses, .event_schema

# tests/api/web_shell_support.py
def cookie_header(token: str) -> dict[str, str]          # {"Cookie": "mhc_session=<token>"}
def demo_pair(settings: Settings) -> dict[str, str]
def session_cookie_value(response: Any) -> str | None

# tests/contract/openapi_variants.py
def sse_frames(text: str) -> list[SseFrame]
def request_examples(operation_id: str) -> dict[str, Any]   # request_examples("switchRole")["REPRESENTATIVE"]

# tests/journeys/support/steps.py
NEED_OWNERS["reply_composer"] == "AEA-51"; NEED_OWNERS["demo_clock"] == "AEA-30"; NEED_OWNERS["demo_service"] == "AEA-30"
def blocked_message(missing) -> str   # f"blocked-on {owners}: {'; '.join(m.what)}" → "blocked-on AEA-51: reply_composer not bound"
# JourneyRun.step(journey, name, *, needs=(), operations=()) skips via missing_needs before the body runs.
```

Route facts the drives rely on (`src/meridian/web/routes/staff_live.py`, read only): `stream_case_events` resolves the
role dependency first (401/403), then `known_case` (404 `CASE_NOT_FOUND` before any frame unless the reset gate is
held). `live_chat_action` → `LiveChatService.join` returns `CASE_NOT_FOUND` for an unknown case. Seeded refs are
`MHC-C-0005`…`MHC-C-0008` (`services/reset.py`), so `MHC-C-0099` is always unknown. `STREAM_HEARTBEAT_S` is 15 s, so an
open stream with no events sends nothing for 15 s.

## Steps

**Step 0: reproduce, and record a baseline.** In the worktree (`export UV_LINK_MODE=hardlink`; no `node_modules`):
- `timeout 120 uv run pytest tests/contract/test_openapi_server.py -k "liveChatAction and unknown_case" -rs` → fails with
  `expected 404, got 403 (NOT_CLAIMED_BY_YOU)`.
- `timeout 30 uv run pytest tests/contract/test_openapi_server.py -k "streamCaseEvents and unknown_case"` → exit 124 (hang).
- `uv run pytest tests/journeys/j7/test_aea_30.py -rs` → fails with `startChatSession -> HTTP 500 … status 500 is not documented`.
- Baseline counts, skipping the hanging drive:
  `timeout 1500 uv run --with pytest-xdist pytest tests/contract/test_openapi_server.py -n 2 -q -rs --deselect "tests/contract/test_openapi_server.py::test_route_cases_match_contract[streamCaseEvents/unknown_case]" > /tmp/fixw1-baseline.txt 2>&1`
  Keep the final summary line and the sorted skip reasons (`grep SKIPPED /tmp/fixw1-baseline.txt | sort`) for AC-4.

**Step 1: create `tests/contract/openapi_sse.py`** (one job: read one ASGI response with a time bound). Move, do not
rewrite: `STREAM_READ_TIMEOUT_S`, `SseRead` and the body of `_read_sse` (driver lines 58 and 373–462) move here.
`_read_sse` is renamed `read_asgi_stream`. Three changes only:
1. `SseRead` gains two trailing fields with defaults: `headers: Mapping[str, str] = field(default_factory=dict)` and
   `body: bytes = b""`. *Invariant:* every existing positional construction stays valid.
2. In `send_message`, on `http.response.start`, also keep the full lowercase header dict (`state["headers"] = sent`,
   initialise `"headers": {}` in `state`). On `http.response.body`, append each non-empty chunk to a local
   `raw = bytearray()` (`raw.extend(chunk)`) before `send_side.send_nowait(chunk)`. *Invariant:* the frame-reading loop
   and both `move_on_after(timeout_s)` bounds are unchanged, so a read still ends within about 2 × `timeout_s`.
3. Return `SseRead(state["status"], state["content_type"], tuple(sse_frames(complete)), state["error"], dict(state["headers"]), bytes(raw))`.

Add:
```python
def as_response(read: SseRead) -> httpx.Response:
    """The read as an httpx.Response for assert_response_matches (status, every header, the raw body)."""
    assert read.status is not None, "no response start was read"
    return httpx.Response(read.status, headers=list(read.headers.items()), content=read.body)
```
Module docstring (≤ 4 lines): AEA-59 runner support; one bounded read of an ASGI response on the TestClient's loop;
used for every drive of an event-stream operation (FIX-W1), so a stream that should have answered an error fails
instead of hanging. Imports: `anyio`, `httpx`, `fastapi.FastAPI`, `SseFrame` from `tests.api.openapi_check`,
`sse_frames` from `tests.contract.openapi_variants`. It must **not** import `tests.contract.openapi_driver` (no cycle).

**Step 2: `_resolve_path_param` honours `reference`.** Insert as the second statement, right after `given = …`:
```python
    if given is None and param == "reference" and "reference" in drive.spec:
        return str(drive.spec["reference"])  # cases/README.md section 2: sent literally; `path` wins when both are given
```
*Invariant:* when the drive has no `reference` key, every existing branch runs exactly as before (logged in →
`seeded_case_ref(run)`, else `"MHC-C-0001"`; `path.reference` words such as `seeded_case` still resolve).

**Step 3: add `send_stream` to the driver**, directly after `send`:
```python
def send_stream(
    run: AppRun,
    operation_id: str,
    *,
    path: str,
    token: str | None,
    extra_headers: Mapping[str, str] | None = None,
    timeout_s: float = STREAM_READ_TIMEOUT_S,
) -> httpx.Response:
    """`send` for an event-stream operation, read with a time bound: a stream where an error was due fails, never hangs."""
```
Body, in this order:
1. `spec = load_contract().operations[operation_id]`; if `(spec.method, spec.path_template) not in run.registered`:
   `blocked(f"route not registered: {operation_id}")`.
2. `headers = dict(cookie_header(token)) if token is not None else {}`; `headers.update(extra_headers or {})`.
3. `seen = len(run.taps)`; `result = read_sse(run, path, headers, frames=1, timeout_s=timeout_s)`.
4. If `result.status == 500 and len(run.taps) > seen`: the same two lines as `send` (`not bound: ` → `blocked(str(exc))`,
   else `pytest.fail(f"{operation_id}: unhandled {type(exc).__name__} (500)")`).
5. If `result.error is not None`: `not bound: ` → `blocked(str(exc))`, else
   `pytest.fail(f"{operation_id}: stream raised {type(exc).__name__}")`.
6. If `result.status is None`: `pytest.fail(f"{operation_id}: no response within {timeout_s}s")`.
7. `return as_response(result)`.
*Invariants:* the skip reasons stay exactly the two in cases/README §6. No response body is ever printed. `frames=1`
means a JSON error body is read to its end (no `\n\n`, the stream closes on `more_body=False`), while an unexpected
open stream stops at its first frame or at the timeout.

Keep `read_sse(run, path, headers, *, frames, timeout_s=STREAM_READ_TIMEOUT_S) -> SseRead` in the driver as a thin
wrapper: the same body as today, but `portal.call(read_asgi_stream, run.app, path, dict(headers), frames, timeout_s)`.
Driver imports: add `import httpx` and
`from tests.contract.openapi_sse import STREAM_READ_TIMEOUT_S, SseRead, as_response, read_asgi_stream`. Remove what
ruff reports unused after the move (expected: `anyio`, `SseFrame`, `sse_frames`). Keep `GUARD_MESSAGE`, `AppRun`,
`install_exception_tap`, `install_socket_guard`, `real_app`, `run_drive` and `send` importable, because
`test_openapi_server.py` imports them.

**Step 4: `run_drive` routes stream drives through `send_stream`.** The 200 SSE branch (`if spec.event_schema and
drive.status == 200:`) is unchanged. Replace the final `if setup == "reset_held": … else: …` pair with:
```python
    def dispatch() -> Any:
        if spec.event_schema:
            return send_stream(run, op, path=path, token=token, extra_headers=headers)
        return send(run, op, path=path, token=token, body=body, extra_headers=headers)

    if setup == "reset_held":
        with run.app.state.container.get(RESET_GATE).hold():
            response = dispatch()
    else:
        response = dispatch()
```
The status, `code` and `assert_response_matches` lines after it are unchanged. They work on the `httpx.Response`
from `as_response`. This puts **every** non-200 drive of `streamCaseEvents` **and** `streamChatEvents` on the bounded
path. That is the per-drive timeout. AC-4 proves it changes no other outcome.

**Step 5: write `tests/contract/test_openapi_driver.py`.** Module docstring: FIX-W1 driver unit tests; level
`integrated with a scripted model` (real app on a first-boot DB copy). Fixtures copied from `test_openapi_server.py`:
an autouse `socket_guard` (`install_socket_guard(monkeypatch)`) and `taps` (`install_exception_tap(monkeypatch)`). Import
the module as `import tests.contract.openapi_driver as openapi_driver` for the spy, plus named imports. Load the real
drives from `tests.contract.cases.staff_live.CASES` with
`cast(tuple[dict[str, Any], ...], CASES[op]["drives"])` and pick by `name`. Tests:
1. `test_reference_is_sent_literally`: inside `real_app`, set `run.main_token = "signed-in"`, then
   `_resolve_path_param(run, Drive("liveChatAction", "staff_live", {"name": "x", "status": 404, "reference": "MHC-C-0099"}), "reference", ["login", "role:representative"]) == "MHC-C-0099"`.
2. `test_path_reference_wins_over_reference_key`: spec `{"name": "x", "status": 404, "path": {"reference": "seeded_case"}, "reference": "MHC-C-0099"}`
   resolves to `seeded_case_ref(run)`, and that is not `"MHC-C-0099"`.
3. `test_reference_default_is_unchanged_without_the_key`: spec without `reference`. With `run.main_token` set →
   `seeded_case_ref(run)`. With `run.main_token = None` → `"MHC-C-0001"`.
4. `test_unknown_case_request_carries_the_literal_reference`: monkeypatch `openapi_driver.send` with a spy that
   records `path` when `operation_id == "liveChatAction"` and delegates to the real `send`. `run_drive` on the real
   `liveChatAction/unknown_case` drive returns `"liveChatAction/unknown_case: 404"`, and the last recorded path equals
   `load_contract().operations["liveChatAction"].path_template.replace("{reference}", "MHC-C-0099")`.
5. `test_stream_unknown_case_answers_404_within_bound`: `run_drive` on the real `streamCaseEvents/unknown_case` drive
   returns `"streamCaseEvents/unknown_case: 404"`, and `time.monotonic()` elapsed < 10.0.
6. `test_stream_send_is_bounded_on_an_open_stream`: log in with `_checked(run, "login", 200, "login", token=None, body={"json": dict(demo_pair(run.settings))})`,
   take `token = session_cookie_value(login)`, switch with
   `_checked(run, "switchRole", 200, "switchRole representative", token=token, body={"json": request_examples("switchRole")["REPRESENTATIVE"]})`.
   Then `send_stream(run, "streamCaseEvents", path=<template with seeded_case_ref(run)>, token=token, timeout_s=1.0)`
   returns status 200, its `content-type` starts with `text/event-stream`, and elapsed < 5.0. (Before this fix,
   `send` on this path never returned.)
Run: `uv run pytest tests/contract/test_openapi_driver.py -rs`: 6 passed.

**Step 6: `tests/contract/cases/README.md` §2.** Change only the `reference` row's meaning cell to:
`A case reference, sent literally. When `path` also names `reference`, `path` wins.`

**Step 7: J-7.** In `tests/journeys/j7/test_aea_30.py`:
- Step "2 person request live-queued": `needs=("session_service", "demo_service", "demo_clock", "reply_composer", "handoff_service", "person_requests")`.
  Leave `operations` and the body unchanged. Steps 1 and 3 are unchanged.
- Replace the module docstring with: J-7 (proposed extension): with staffing on, a person request is live-queued;
  turning staffing off converts the case and tells the chat. API level on AEA-57's harness. Step 2 starts a chat, and
  startChatSession builds its settled view through AEA-51's `reply_composer`, so until AEA-51 binds it the test
  reports `blocked-on AEA-51` after step 1 passes. The service-level behaviour is in tests/services/test_demo.py
  (test_shift_end_commits_with_conversions, mock-tested).
- Run `uv run pytest tests/journeys/j7 -rs` → 0 failed; the reason for `test_j7_shift_end_converts_queued_case` is
  `blocked-on AEA-51: reply_composer not bound`. If the reason also names another owner, report it (AC-5 needs only
  that AEA-51 is named). If another `j7` test fails for an unrelated reason, report it. Do not fix it: it is outside
  this slice.

**Step 8: area map.** In `.claude/reference/area-map.md`, row "Integration and journeys", change
`tests/contract/{test_openapi_server,openapi_cases,openapi_driver,test_openapi_fixtures,openapi_variants,test_types_gen_drift}.py`
to `tests/contract/{test_openapi_server,openapi_cases,openapi_driver,openapi_sse,test_openapi_driver,test_openapi_fixtures,openapi_variants,test_types_gen_drift}.py`.
Change no other cell.

**Step 9: record.** Write `docs/testing/journeys/2026-10-21-FIX-W1.md` in the `2026-10-21-AEA-59.md` shape (the §4
field table). Claim: both findings fixed. Level: contract drives and driver tests `integrated with a scripted model`
(no model reached). J-7 step 1 `integrated with a scripted model`, steps 2–3 not run. Tested revision: the
commit that adds this record (branch, cut from `eb51ba4`). Environment: as AEA-59's row. Commands: Step 10's. Result:
counts vs the baseline, the two durations, the J-7 skip reason quoted. Remaining limitations: the J-7 500 stays until
AEA-51, and the local-driver-only `staff_live` drives are still not run here. Blocked by: AEA-51 (J-7 steps 2–3).
No secrets, demo password or personal data.

**Step 10: gates, then commit** (Checks below). Commit with explicit `git add` of the seven files only. Message
`fix(FIX-W1): contract driver honours reference and bounds stream drives; J-7 blocked on AEA-51`, last line
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Do not push.

## Data and fixtures

Synthetic and issued only. `MHC-C-0099` is a made-up case reference that is never seeded (seeds are `MHC-C-0005`…`0008`,
`services/reset.py`). Every drive runs on `real_app`'s first-boot copy of the issued DB in `tmp_path`. The demo login
comes from `make_settings` / `demo_pair` and is never printed or asserted as a literal. No new fixture files.

## Checks

Iterating:
- `uv run pytest tests/contract/test_openapi_driver.py -rs`
- `timeout 120 uv run pytest tests/contract/test_openapi_server.py -k "unknown_case" -rs --durations=0`
- `uv run pytest tests/journeys/j7 -rs`

Once before the final commit, cheapest first; stop at the first red:
1. `uv run ruff format --check tests/contract tests/journeys/j7` and `uv run ruff check tests/contract tests/journeys/j7`
2. `uv run mypy tests/contract tests/journeys/j7`
3. Affected tests (only `test_openapi_server.py` imports the driver):
   `timeout 1500 uv run --with pytest-xdist pytest tests/contract/test_openapi_server.py tests/contract/test_openapi_driver.py -n 2 -q -rs`.
   Pass means the Step 0 baseline plus exactly: `liveChatAction/unknown_case` passed (was failed),
   `streamCaseEvents/unknown_case` passed (was deselected), and the 6 new tests passed. Skip reasons are identical
   (`diff` the sorted SKIPPED lines). There are no new failures.
4. Strict form for the fixed drives: `CONTRACT_STRICT=1 timeout 120 uv run pytest tests/contract/test_openapi_server.py -k "unknown_case" -rs` → 2 passed.
5. Affected journeys: `uv run python -m tests.journeys.affected --base main`, plus `uv run pytest tests/journeys/j7 -rs`
   (0 failed; J-7 skipped `blocked-on AEA-51: reply_composer not bound`).

No full suite: no `conftest.py`, settings, dependency, lockfile or cross-package module changes
(`build-loop-test-scope.md`). `pytest -n 2` at most.

**Do not:**
- edit `tests/contract/cases/staff_live.py`, `openapi_cases.py`, `test_openapi_server.py`, any `tests/journeys/support/`
  or `browser/` file, or anything under `src/`;
- add `pytest-timeout` or any dependency, or touch `pyproject.toml` / `uv.lock`;
- change `STREAM_READ_TIMEOUT_S`, `PATH_WORDS` or the skip vocabulary;
- make J-7 pass by binding `reply_composer`, catching the 500, or using `pytest.mark.skip`. Use `needs=` only;
- print a response body, cookie or the demo password in any message;
- bind ports 4019 or 5184, use `git add -A`, push, or force-push.

## Risks and requests

- **Collision: `.claude/reference/area-map.md`** is a shared file other tickets in a parallel wave may edit (same row).
  The edit is one token in one cell. If a merge conflicts, the merge step keeps both lists' entries.
- **`streamChatEvents` error drives move onto the bounded path** (Step 4). The 200 drives already use the same ASGI
  scope, so the risk is low. AC-4's baseline diff is the guard. If any `streamChatEvents` drive changes outcome,
  stop and report it. Do not special-case it.
- **Seam note (no action here):** AEA-51 will bind `reply_composer`. J-7 then runs steps 2–3 for real, with no edit.
- **Acceptance revision:** the finding says "0 failed on 3725c90". `main` is now `eb51ba4` (identical for every file in
  this slice). Evidence is recorded on this branch's commit.
- No contract, OpenAPI or signed-decision change is needed; no shared primitive is requested.

## Gates

None. No human, paid or live gate; no model call.

## Readiness

**READY.** Blocked on nothing. AEA-51 is only the reason J-7 skips; nothing here imports it.
