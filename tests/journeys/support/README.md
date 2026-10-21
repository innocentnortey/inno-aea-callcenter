# Journey harness (AEA-57)

Runs the real FastAPI app (`create_app`) under uvicorn on `127.0.0.1` with an OS-assigned port, on a disposable copy of the
issued scheduling database made by the app's own first boot, with a scripted model at the provider boundary. Every
response a journey receives is checked against the signed OpenAPI, and a read-only reader checks what was stored. No
request leaves loopback (a socket guard fails any other connection). API level only: browser journeys are AEA-58's.

## Public fixtures
- `journey` — a running real app on a disposable DB copy with the scripted model; returns `JourneyRun`
- `journey_clock` — the run's wall clock (`StepClock`); `.advance(seconds)` moves `get_wall_clock()` forward; the demo clock stays

## Options
- `--journey-record=SCOPE` — write `docs/testing/journeys/<date>-<SCOPE>.md` for this run
- `--journeys-strict` — a blocked step fails instead of being skipped (wave merge, pre-deploy)

## The `journey` object
- `settings`, `app`, `container`, `base_url`, `demo_username` — the running app's own objects
- `script` — `JourneyScript`: `add(role, *raw_outputs)`, `calls`, `remaining(role=None)`, `problems()`
- `models` — the `ScriptedModel` per role (provider and model equal the configured `RoleSpec`)
- `db` — `DbReader` (read-only): `rows`, `one`, `scalar`, `count`, `table_rows`
- `logs` — `LogTap`: `structured(kind)`, `wait_for(kind, predicate)`, `all_text()`
- `guard` — `SocketGuard`; `guard.blocked` lists refused non-loopback connections
- `client()` — a new `JourneyClient` with its own cookie jar; `login(client=None)` signs in with the run's demo pair
- `step(journey, name, needs=(), operations=())` — one named journey step (see below)
- `secret_values()`, `files_containing(value)` — for "this value is not stored or logged" checks

## Writing a step
```python
pytestmark = pytest.mark.journey


def test_j2_something(journey):
    signed = journey.login()
    with journey.step("J-2", "1 open", needs=("session_service",), operations=("startChatSession",)):
        r = signed.client.call("POST", "/api/chat/sessions", operation_id="startChatSession")
        assert r.status_code == 201
        assert journey.db.count("conversations") == 1
```

## Blocked steps
`needs` are container keys (`NEED_OWNERS` in `steps.py`) and `operations` are operationIds (`OPERATION_OWNERS`). A step
whose need is not bound, or whose operation is not routed, is recorded as blocked with the owning ticket and the test is
skipped with `blocked-on AEA-NN`. With `--journeys-strict` the same step fails. A blocked step never counts as a pass.
A name missing from the maps is a follow-up on AEA-57.

## Rules for journey files
One file per ticket per journey: `tests/journeys/j<N>/test_aea_<NN>.py` (N 1..10); mark `pytest.mark.journey`; never edit
`support/`; no `dependency_overrides`, no monkeypatch of `meridian`, no `TestClient`, no doubles above the model ports;
every `/api` call names its operationId; assert what the client sees and what was stored.

## Commands
1. `uv run pytest tests/journeys/support -q -rs`
2. `uv run pytest -m journey tests/journeys/j1 -v --journey-record=AEA-57`
3. `uv run pytest -m journey tests/journeys --journeys-strict`

Ticket merge: `uv run python -m tests.journeys.affected --base <main SHA before the merge>`.
