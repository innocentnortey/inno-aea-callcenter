# Build ledger (AEA Stage 8)

Maintained by the build workflow's merge step; truth if the session is compacted. States: planned / frozen-tests / built / reviewed / merged / blocked / sent-back. Gated, not in this run: AEA-09 (human), AEA-55 (UX-5), AEA-56 (human deploy).

| ticket | issue | lane | state | branch | commit | evidence | blockers |
|---|---|---|---|---|---|---|---|
| AEA-01 | #1 | B | merged | aea-01-aea-01-foundation | 07924f5 (code commit 893b825) | ruff check/format clean; mypy clean (68 files); full suite 121 passed (pyproject, lock and conftest are new); journeys: 0 affected, record mock-tested, blocked by AEA-57 | - |
| AEA-02 | #2 | B sec | planned |  |  |  | AEA-04 |
| AEA-03 | #3 | B | merged | aea-03-fixed-customer-texts | 60617f9 | merge of 44730d2: ruff check/format clean; 14 tests pass (policy texts, import direction); type check n/a (no pyproject yet); journey record at mock-tested, blocked by AEA-57 | - |
| AEA-04 | #4 | B sec | blocked | aea-04-aea-04-redaction | 22023f2 (code commit 9145044) | merge gate failed: Format gate red. After merging (no conflicts), `uv run ruff check src tests` passed and `uv run ruff format --check` failed (latest state from the build workflow; text shortened) | - |
| AEA-05 | #5 | B | planned |  |  |  | AEA-02 |
| AEA-06 | #6 | B | ready |  |  |  | - |
| AEA-07 | #7 | D | merged | main | 5073dd0 (docs, pushed to main as a fast-forward); ledger row in bc02266 | docs/technical-documentation.md: 13 sections, links resolve, figures sourced or pending, 6+1 open decisions labelled proposed; diff touches docs, SUBMISSION.md and .claude/state only | - |
| AEA-08 | #8 | D | merged | main | c0621de (documents); ledger and ICM row in 5f2e1bb | DO-3 at revision 3 (103 modules recounted); area map has a Tickets column (01-62 except the six direct/human tickets, AEA-14 twice); stale-name greps leave only history, Superseded notes and retired-name sentences; check_context no FAIL; diff touches docs and .claude/state only | - |
| AEA-10 | #10 | B | planned |  |  |  | AEA-01,AEA-02 |
| AEA-11 | #11 | B | planned |  |  |  | AEA-01,AEA-02 |
| AEA-12 | #12 | B sec | planned |  |  |  | AEA-01,AEA-02,AEA-04,AEA-05 |
| AEA-13 | #13 | B | blocked |  |  | NEEDS-DECISION (plan) | AEA-02,AEA-03 |
| AEA-14 | #14 | B | planned |  |  |  | AEA-02,AEA-03 |
| AEA-15 | #15 | B | ready |  |  |  | AEA-02 |
| AEA-16 | #16 | B | planned |  |  |  | AEA-02 |
| AEA-17 | #17 | B sec | ready |  |  |  | AEA-02 |
| AEA-18 | #18 | B sec | ready |  |  |  | AEA-02 |
| AEA-19 | #19 | B sec | ready |  |  |  | AEA-02,AEA-04 |
| AEA-20 | #20 | B sec | ready |  |  |  | AEA-01,AEA-02,AEA-04 |
| AEA-21 | #21 | B | ready |  |  |  | AEA-02,AEA-03 |
| AEA-22 | #22 | B sec | ready |  |  |  | AEA-02,AEA-04 |
| AEA-23 | #23 | B sec | ready |  |  |  | AEA-01,AEA-02,AEA-04 |
| AEA-24 | #24 | B sec | ready |  |  |  | AEA-01 |
| AEA-25 | #25 | D | merged | main | 0ad71f9 (README, SUBMISSION D-3, resume); ledger row in the next commit | README.md has the 8 sections in order; ruff, format, mypy, pytest (121 passed) exit 0; env names, percentages, secret words and links checked by grep; diff touches README.md, SUBMISSION.md and .claude/state only | - |
| AEA-26 | #26 | B | ready |  |  |  | AEA-10 |
| AEA-27 | #27 | B sec | ready |  |  |  | AEA-04,AEA-10,AEA-13 |
| AEA-28 | #28 | B | ready |  |  |  | AEA-10,AEA-13 |
| AEA-29 | #29 | B sec | ready |  |  |  | AEA-10,AEA-11,AEA-14,AEA-16 |
| AEA-30 | #30 | B | ready |  |  |  | AEA-10,AEA-11,AEA-14 |
| AEA-31 | #31 | B | ready |  |  |  | AEA-10,AEA-14,AEA-23 |
| AEA-32 | #32 | B | ready |  |  |  | AEA-10,AEA-23 |
| AEA-33 | #33 | B | ready |  |  |  | AEA-16 |
| AEA-34 | #34 | B | ready |  |  |  | AEA-10,AEA-21 |
| AEA-35 | #35 | B | ready |  |  |  | AEA-11,AEA-20,AEA-22 |
| AEA-36 | #36 | B sec | ready |  |  |  | AEA-11,AEA-12,AEA-14,AEA-21 |
| AEA-37 | #37 | B | ready |  |  |  | AEA-11,AEA-12,AEA-21 |
| AEA-38 | #38 | B | ready |  |  |  | AEA-10,AEA-11,AEA-15,AEA-21 |
| AEA-39 | #39 | B | ready |  |  |  | AEA-11,AEA-14,AEA-21 |
| AEA-40 | #40 | B sec | ready |  |  |  | AEA-03,AEA-10,AEA-11,AEA-12,AEA-23 |
| AEA-41 | #41 | B | ready |  |  |  | AEA-10,AEA-11,AEA-23 |
| AEA-42 | #42 | B | ready |  |  |  | AEA-23 |
| AEA-43 | #43 | B sec | ready |  |  |  | AEA-23 |
| AEA-44 | #44 | B sec | ready |  |  |  | AEA-10,AEA-23 |
| AEA-45 | #45 | B | ready |  |  |  | AEA-23 |
| AEA-46 | #46 | B | ready |  |  |  | AEA-10,AEA-23 |
| AEA-47 | #47 | B | ready |  |  |  | AEA-23 |
| AEA-48 | #48 | B | ready |  |  |  | AEA-23 |
| AEA-49 | #49 | B | ready |  |  |  | AEA-23 |
| AEA-50 | #50 | B sec | ready |  |  |  | AEA-16,AEA-31,AEA-32,AEA-33,AEA-19,AEA-23 |
| AEA-51 | #51 | B | ready |  |  |  | AEA-17,AEA-18,AEA-20,AEA-26,AEA-27,AEA-28,AEA-29,AEA-33,AEA-34,AEA-35,AEA-36,AEA-37,AEA-38,AEA-39,AEA-40,AEA-42,AEA-43,AEA-11,AEA-19,AEA-30,AEA-44,AEA-46,AEA-57,AEA-59 |
| AEA-52 | #52 | B | ready |  |  |  | AEA-29,AEA-30,AEA-40,AEA-41,AEA-44,AEA-45,AEA-46,AEA-47,AEA-31,AEA-32,AEA-43,AEA-57,AEA-59 |
| AEA-53 | #53 | B | ready |  |  |  | AEA-26,AEA-29,AEA-32,AEA-48,AEA-44 |
| AEA-54 | #54 | D | ready |  |  |  | AEA-50 |
| AEA-57 | #57 | B | ready |  |  |  | AEA-02,AEA-10,AEA-11,AEA-23 |
| AEA-58 | #58 | B | ready |  |  |  | AEA-40,AEA-49,AEA-57 |
| AEA-59 | #59 | B | ready |  |  |  | AEA-02,AEA-23 |
| AEA-60 | #60 | B | ready |  |  |  | AEA-20,AEA-22,AEA-35,AEA-37,AEA-38,AEA-39,AEA-17,AEA-18,AEA-27,AEA-28,AEA-33,AEA-57 |
| AEA-61 | #61 | B | ready |  |  |  | AEA-51,AEA-57,AEA-60,AEA-06,AEA-50 |
| AEA-62 | #62 | B | ready |  |  |  | AEA-58,AEA-51,AEA-52,AEA-29,AEA-40,AEA-57 |
| AEA-09 | #9 | gated | gated |  |  | human: Railway project, variables, Langfuse (Innocent) |  |
| AEA-55 | #55 | gated | gated |  |  | UI integration (waits UX-5 sign-off) |  |
| AEA-56 | #56 | gated | gated |  |  | human: deploy and smoke (Innocent) |  |
