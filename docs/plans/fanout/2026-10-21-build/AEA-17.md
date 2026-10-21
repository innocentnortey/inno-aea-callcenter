
## Deviations

- The adapter's `__init__` caps the SDK `anthropic` logger at WARNING (when its effective level is lower). The plan put the cap only in the `register_anthropic` hunk, but frozen `test_no_key_or_message_in_failure` builds adapters directly and the SDK's DEBUG header log line carried the sentinel request id. Behavior of the hunk is unchanged.
- `tests/contract/test_anthropic_adapter.py` lines 376-377 (frozen) fail `uv run mypy` with two `arg-type` errors (dict literals in a `tuple[JsonValue, ...]` comparison). Not editable by the implementer; request: the test-writer or integrator fixes the literal typing (for example a `cast` or annotating the expected tuple).
- The `ToolCall`/`raw` values are cast to `JsonValue` in the adapter for mypy; no runtime change.
