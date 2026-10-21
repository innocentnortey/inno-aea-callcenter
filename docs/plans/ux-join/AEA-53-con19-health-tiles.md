# CON-19 health tiles (AEA-53, AC-12)

The CON-19 `health` list is fixed and always has these seven tiles in this order, on an empty store too
(`HEALTH_TILES` in `src/meridian/services/metrics_reader.py`; asserted by
`tests/unit/services/test_metrics_reader.py::test_health_tiles_fixed_list`).

| # | id | label | unit | null reason |
|---|---|---|---|---|
| 1 | `M-22` | Conversations | count | never null (0 on an empty store) |
| 2 | `M-22` | Turns | count | never null |
| 3 | `M-24` | Failures | count (value = numerator, with denominator = live turns) | `No turns yet` |
| 4 | `M-23` | Latency p50 | ms | `No turns yet`; `Not enough turns yet (fewer than 20)` |
| 5 | `M-23` | Latency p95 | ms | same as tile 4 |
| 6 | `scheduler_last_run` | Overdue job last ran | ms (age of the last job run) | `The overdue job has not run yet` |
| 7 | `handoff_only` | Handoff-only mode (1 = on) | count (1 or 0) | never null |

- SCR-10's empty state keys on tile 1 (`M-22` Conversations) having value 0.
- `scheduler_last_run` and `handoff_only` are not DO-7 registry ids. `handoff_only` is how the page shows handoff-only
  mode (an open provider circuit or the spend cap), because `MonitoringResponse` has no field for it (D-5).
- `trace_export` reads "sent n of N turns" (n sent, N live turns).
