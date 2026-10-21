# Browser journeys (AEA-58)

## What it is

System Chrome, driven by `pytest-playwright`, against **the production build** of `apps/web` served by **the real
FastAPI app** over a disposable copy of the issued scheduling DB, with the scripted model at the provider boundary.
Sign-in goes through the real SCR-12 form. Every `/api/*` response Chrome receives is checked with AEA-23's
`assert_response_matches`. Level of the evidence: `integrated with a scripted model` (integrated-journeys rule, section 4).

## Prerequisites

- System Chrome (`/usr/bin/google-chrome`; the default channel is `chrome`). Never run `playwright install`.
- Node 24 (for `check:dist`), and `df -h /home` with a few GB free.

## Build

```bash
npm --prefix apps/web run build && npm --prefix apps/web run check:dist
```

A backend worktree has no `apps/web/node_modules` and must not get one. Build in the primary checkout and point the
tests at it:

```bash
npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run build && \
npm --prefix /home/linuxuser/workspaces/inno-aea-callcenter/apps/web run check:dist
export MERIDIAN_WEB_DIST_DIR=/home/linuxuser/workspaces/inno-aea-callcenter/apps/web/dist
```

A missing build is an **error** (never a skip) that names the build command and `MERIDIAN_REQUIRE_FRONTEND`.

## Run

The reviewer command:

```bash
npm --prefix apps/web run build && npm --prefix apps/web run check:dist && \
perl -e 'alarm 300; exec @ARGV' uv run pytest -m journey tests/journeys/browser tests/journeys/j1/test_aea_58.py tests/journeys/j9/test_aea_58.py --browser-channel chrome
```

The merge-gate command, after the build:

```bash
uv run python -m tests.journeys.affected --base <sha> -- --browser-channel chrome
```

Add `--journeys-strict` at a wave merge or before a deploy: every blocked step and every blocked API exchange then fails.

## Watch it headed

Add `--headed --slowmo 300`. Never add `--tracing`, `--video` or `--screenshot` from pytest-playwright when recording
evidence: traces hold typed text.

## Walk J-1 by hand (wave walkthrough)

1. Choose two synthetic values and set `MERIDIAN_DEMO_USERNAME` and `MERIDIAN_DEMO_PASSWORD` in your shell.
2. `uv run python -m tests.journeys.browser.serve` prints `serving http://127.0.0.1:<port> ...`.
3. Open that URL with chrome-devtools MCP (`navigate_page`) or a headed Chrome.
4. Walk: `/` goes to SCR-12 -> sign in -> greeting -> type "Hi, what can you help me with?" -> the reply -> reload ->
   same thread, no second session -> Sign out -> `/` redirects to SCR-12 again.
5. Never tick "Show password" and never screenshot a filled password field unmasked.

## Which journeys a wave touched

```bash
uv run python -m tests.journeys.affected --base <wave base> --list-only
```

## Records and screenshots

`--journey-record=<scope>` writes `docs/testing/journeys/<date>-<scope>.md` and the screenshots in
`docs/testing/journeys/<date>-<scope>/`. A walkthrough record is `docs/testing/journeys/<date>-wave-N-walkthrough.md`
with the nine fields of integrated-journeys section 4. Screenshot names hold only the test name, the device and a
fixed label.

## Adding a browser journey later

One file `tests/journeys/j<N>/test_aea_<NN>.py` with `pytest_plugins = ("tests.journeys.browser.plugin",)`, the
`browser_journey` fixture, `browser_step(...)` for every step, and selectors only by key from `selectors.py`. A missing
helper is a follow-up on AEA-58, merged first. A test file never calls `locator(` or `get_by_` itself.

## Selectors

`selectors.py` is the only file that builds locators. Its rows come from `docs/plans/ux-join/selectors.md` (the UX
session's contract) and from nowhere else. To add one: find the row that names the state, copy it literally into
`CONTRACT_ROWS` as a `SelectorRow` (an attribute selector is `css`; "role=X name=Y" is `role`; "input labelled Y" is
`label`), put the row's exact id or heading in `row`, set `SELECTORS_REVISION` to the file's short SHA, and end the
line with `# selectors.md <row> @ <rev>`. A state the file does not list stays absent, and the steps that need it
report `blocked-on UX session`. Never invent a row, use copy text as a selector, or read `apps/web/src` to fill a gap.
