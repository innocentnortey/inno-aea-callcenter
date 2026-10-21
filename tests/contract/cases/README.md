# Server contract cases

Read by `tests/contract/test_openapi_server.py` (AEA-59). The runner is `tests/contract/openapi_driver.py`; the format
checks are `tests/contract/openapi_cases.py`. Run your cases with the commands at the end.

## 1. What a case file is

One file per route ticket. Each holds `ROUTE_FILE: Final = "<stem>"` and `CASES: Final[dict[str, dict[str, object]]]`,
keyed by operationId; each value is `{"public": bool, "drives": (<drive>, ...)}`. The operation to file map comes from the
operation's `x-con` (a file in the wrong place fails `test_case_files_are_well_formed`):

| File | Operations |
|---|---|
| `auth.py` | CON-22: `login`, `logout` |
| `chat.py` | CON-1, CON-2: `startChatSession`, `getChatThread`, `submitTurn` |
| `events.py` | CON-3: `streamChatEvents` |
| `handoff.py` | CON-4, CON-5: `requestPerson`, `saveFollowUp` |
| `demo.py` | CON-6, CON-7, CON-9: demo inbox, staffing, reset (CON-8's clock is `staff_clock.py`) |
| `staff_session.py` | CON-10: `getSession`, `listDemoRoles`, `switchRole` |
| `staff_cases.py` | CON-11, 12, 13, 15, 16, 17: queue, case detail, claim and the other case actions |
| `staff_live.py` | CON-14, CON-21: `liveChatAction`, `streamCaseEvents` |
| `staff_clock.py` | CON-8: `advanceDemoClock` |
| `reads.py` | CON-18, 19, 20: monitoring, owner metrics, latest eval |

## 2. Drive keys

| Key | Meaning |
|---|---|
| `name` | Unique within the operation, `[a-z0-9_]+`. |
| `status` | The expected HTTP status; must be documented for the operation. |
| `code` | Expected `error.code` (error statuses only). |
| `preconditions` | Words from section 3, run in order before the request. |
| `setup` | One setup word from section 3. |
| `body` | `None`; `{"example": NAME}` (a named OpenAPI request example, optionally with `credentials` or `turn_id`); `{"raw": JSON}`; `{"text": str}` (not JSON). |
| `path` | Path-parameter values, from the path words in section 4. |
| `thread` | Shorthand for `path["thread_id"]`. |
| `reference` | A case reference, sent literally. When `path` also names `reference`, `path` wins. |
| `events` | Chat event types appended to the started thread's stream (`streamChatEvents` only; the last must end the stream). |
| `last_event_id` | `None`, `{"after_event": n}` (id of the n-th seeded event), or an int sent as the header. |
| `frames` | Number of SSE frames to read (required for a 200 on a stream). |
| `response_example` | Checked by the route's own driver; the runner ignores it. |

## 3. Vocabulary

Canonical preconditions: `login` (sign in with the configured demo pair), `thread` (start a chat session), `open_case`
(press the BUTTON request), `verified` (seed a verified identity), `ended` (reset the demo; the thread is then ended),
`unknown` (no session needed, the path id is a fresh UUID), `role:customer|representative|supervisor|owner` (switchRole).
Canonical setups: `login_rejects_exhausted`, `reset_held`, `other_session_thread`, `ended` (the thread is ended).

Aliases accepted for files written before this format: `started_thread` and `start_thread` mean `thread`;
`as_<role>` means `role:<role>`; `reset_gate_held` means `reset_held`; `ended_thread` means the setup `ended`.

Local-driver-only words (the real app cannot produce them without a double): `handoff_fails`, `turn_running`,
`live_case_claimed`, `live_case_joined`, `live_case_unclaimed`, `case_claimed_by_supervisor`, `case_events`. A drive using
one is listed by the completeness test and proved by the route's own driver (`mock-tested`), not run here. A word the
runner does not know fails the format check by name; adding it is a follow-up on AEA-59, not an edit to your file.

## 4. Path words

`started`, `unknown`, `malformed` (`thr_9d41`), `other_session`, `ended`, `seeded_case`. Any other string is sent literally.

## 5. What the runner adds itself

401 `UNAUTHENTICATED` without a session for every operation except `login`; 401 `LOGIN_FAILED` for a wrong pair on
`login`; 400 `VALIDATION_ERROR` for a malformed body on every operation that documents 400 and takes a body. Other
documented statuses are your cases.

## 6. Skip reasons and strict mode

A drive whose route is not registered is skipped with `route not registered: <operationId>`; one that meets
`RuntimeError("not bound: <name>")` is skipped with that message. Nothing else is ever skipped. With
`CONTRACT_STRICT=1` both are failures and a missing case fails the completeness test (the wave-merge form).

## 7. The documented example case

<!-- example-case:start -->
```python
EXAMPLE_CASES = {
    "getChatThread": {
        "public": False,
        "drives": (
            {
                "name": "read",
                "status": 200,
                "preconditions": ("login", "thread"),
                "path": {"thread_id": "started"},
                "body": None,
            },
            {
                "name": "no_session",
                "status": 401,
                "code": "UNAUTHENTICATED",
                "preconditions": (),
                "path": {"thread_id": "unknown"},
                "body": None,
            },
            {
                "name": "unknown_thread",
                "status": 404,
                "code": "SESSION_NOT_FOUND",
                "preconditions": ("login",),
                "path": {"thread_id": "unknown"},
                "body": None,
            },
            {
                "name": "ended_thread",
                "status": 410,
                "code": "SESSION_ENDED",
                "preconditions": ("login", "thread"),
                "setup": "ended_thread",
                "path": {"thread_id": "ended"},
                "body": None,
            },
        ),
    },
}
```
<!-- example-case:end -->

## 8. How to run your cases

`uv run pytest tests/contract/test_openapi_server.py -k <operationId> -rs`, and the same with `CONTRACT_STRICT=1`.
