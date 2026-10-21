# A5 Service desk direction prototype (UX-2 clickable prototype)

Plan for one fan-out slice. Written 2026-10-21 by `fanout-planner`. Built by `fanout-implementer` (Sonnet), who has none of the planner's reading: every decision below is made, every name is exact. If a step cannot be finished from this plan, stop and report; do not improvise a design.

Paths. `P` = `/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter`. `DP` = `P/docs/artifacts/_build/direction-prototypes` (holds `src/`, `scripts/`, `fonts-out/`, `shots-src/`). `ART` = `P/docs/artifacts`. `WF` = `P/docs/ux/02-concepts/wireframes`. `TMP` = `/Users/innocentnortey/.claude/jobs/0d72ed71/tmp` (scratch only, outside the repo).

---

## 1. Goal and sources

**Goal.** Build the A5 "Service desk" skin for the shared story engine, so one self-contained file `ART/2026-10-21-direction-A5-service-desk.html` plays the same scripted story as A1 to A3 (8 hash steps `#greeting #answer #booking #code #handoff #safety #live #case`), in the look Innocent approved on the A5 look sheet, light first with a working dark theme. Add one engine feature: a "slow reply" demo toggle that shows the pending-turn lines. Switch the engine's direction list to A5 only. Write six wireframe PNGs.

**Sources (read before changing anything if a step is unclear).**

| What | Where |
|---|---|
| A5 anatomy table, palette, fonts, do-not-carry-over list, house-texture check | `P/docs/design/DESIGN-DIRECTIONS.md`, section `## A5 · Service desk` (lines 491-730) |
| The approved look: exact palettes, mockup markup and CSS | `P/docs/artifacts/_build/a5-look/build_a5_look.py` (dicts `LIGHT`, `DARK`; string `CSS`; mockups `PHONE_SLOTS`, `PHONE_HANDOFF`, `PHONE_SAFETY`, `CONSOLE`) and the built `ART/2026-10-20-a5-look-sheet.html` |
| Layouts | `P/docs/ux/02-concepts/CONCEPTS.md`: C2 (chat thread + "What's settled" panel, phone strip), S2 (queue, eight-heading brief, evidence with Sources / Conversation tabs) |
| Flows | `P/docs/ux/01-planning/USER_FLOWS.md`: FLOW-5 (windows, then code before the write), FLOW-3 (verify; "send a new code" on expiry, lines 191 and 201) |
| Screen copy, states, pending turn | `P/docs/ux/03-structure/SCREEN_SPECS.md`: SCR-1 `loading` row (line 79: "Meridian assistant is replying…" after 300 ms, "Still working on this…" after about 10 s, 60 s `TURN_TIMEOUT`, `BUSY`), copy notes (lines 135-151), accessibility notes (152-160) |
| Worked example of adding a skin | `DP/src/a3.skin.js`, `DP/src/a3.css`, `DP/scripts/build.py` |
| Engine (shared) | `DP/src/engine.js` (673 lines) |

---

## 2. Boundary

**Owned (the only files the implementer may create or edit).**

| File | Action |
|---|---|
| `DP/src/a5.skin.js` | create |
| `DP/src/a5.css` | create |
| `DP/scripts/build.py` | modify: A5 registration only (see Step 2) |
| `DP/src/engine.js` | modify: minimal (see Step 5) |
| `DP/fonts-out/a5-display.woff2`, `a5-sans.woff2`, `a5-mono.woff2` | create |
| `ART/2026-10-21-direction-A5-service-desk.html` | create (build output) |
| `DP/shots-src/2026-10-21-direction-A5-service-desk-dark.html` | create (build output, dark copy used for the dark wireframes) |
| `WF/A5-chat-390-light.png`, `A5-chat-1280-light.png`, `A5-case-1280-light.png`, `A5-chat-390-dark.png`, `A5-chat-1280-dark.png`, `A5-case-1280-dark.png` | create |

**Scratch (allowed, not deliverables, never inside `P`).** Any file named `a5-*` under `TMP` (check scripts, font work dir `TMP/fonts-work-a5/`, hash lists, scratch screenshots in `TMP/a5-shots/`). The check scripts must live there because `scripts/contrast.py`, `flow3.py` and `shoot.py` are read-only for this slice.

**Read only (never edit).** `DP/src/proto.css`, `DP/src/a1.*`, `a2.*`, `a3.*`, `a4.skin.js` (dropped; ignore), `DP/scripts/contrast.py`, `flow*.py`, `shoot.py`, `subset.sh`, every other `fonts-out/` file, `ART/2026-10-20-direction-A1-work-order.html`, `…A2-route-sheet.html`, `…A3-dispatchers-log.html` (**must stay byte-identical**), the look sheet and its generator, all `docs/design`, `docs/ux` text files, and everything outside `P/docs/artifacts` and `WF`.

**Other slices.** This plan assumes no other slice touches `engine.js` or `build.py`. If one does, that is a collision to report (section 8).

---

## 3. Requirements table

| # | Requirement (source) | How it is implemented | How it is verified |
|---|---|---|---|
| R1 | A5 skin registered; output `ART/2026-10-21-direction-A5-service-desk.html`; same 8 hash steps (brief; `engine.js` `STEPS`) | `a5.skin.js` + `a5.css` + build.py registration; engine `STEPS` untouched | `python3 DP/scripts/build.py a5` prints the path; click-through script visits all 8 hashes (Step 7.2) |
| R2 | Direction list shows only A5; A1-A3 dropped, their files left unchanged (brief) | `DIRS` in `engine.js` becomes the single A5 entry; the existing `filter(d.code !== SK.code)` then renders no switch links. build.py default list becomes `['a5']` | `document.querySelectorAll('.switch-link').length === 0`; `shasum -a 256` of the three A1-A3 files identical before and after (Step 0 / 7.7) |
| R3 | Engine change only for a pending-turn demo state: "Meridian assistant is replying…" then "Still working on this…" (brief; SCREEN_SPECS line 79) | Step 5: `slowMode` toggle in the prototype bar (`#slow-btn`), helper `thinking(g)`, skin renders `kind: 'pending'` | Pending test (Step 7.4): line 1 at about 0.3 s, line 2 after about 10 s, reply at about 13 s, toggle-off releases early |
| R4 | A1-A3 files are not rebuilt; say so if the engine changes (brief) | Not run; build.py default list changed so a no-argument run cannot rewrite them | This plan states it; final report restates it; hash check R2 |
| R5 | Light first, working dark theme (brief; A5 palette table) | Tokens in `a5.css` `:root` (light) and the `/*DARK-START*/ … /*DARK-END*/` block (dark); `build.py` `css_for` wraps the block into `prefers-color-scheme` and `[data-theme]` rules | Dark copy loads without console errors; dark wireframes; contrast script both themes (Step 7.5) |
| R6 | 12-hour times everywhere (brief; SCREEN_SPECS copy notes "Times 12-hour") | Skin formats windows through its own `WT` map ("8:00 am – 12:00 pm"); engine times are already "2:14 pm" | Click-through check: no `\d{1,2}:\d{2}` not followed by `am`/`pm` in `#app` text on every step (Step 7.2, check G) |
| R7 | Safety words (brief; look sheet) | Skin hard-codes: list item 1 `Leave the home immediately.` item 2 `Call 911 or your gas utility from outside.` paragraph `Don't flip any light switches, open windows near the furnace, or restart any equipment.`; engine's quiet line `Once you're outside and safe, you can leave a number here if you'd like.` is unchanged | Text assertion on `.safety` and the last thread line at `#safety` (Step 7.2) |
| R8 | Red only on the safety card; demo bar neutral (brief; A5 "Safety stays unmistakable") | `--danger` is read only by `.safety`, `.sf-band`, `.ic-warn` fill/stroke on that card; errors, overdue, Safety tags use ink, weight, icon, word. `proto.css` bar is `#262A31` (unchanged) and the slow button is neutral | Check B: no element outside `.safety` has colour, background or border colour equal to the danger rgb (light `rgb(180, 35, 24)`, dark `rgb(200, 49, 47)`) on any step |
| R9 | "Talk to a person" always present (brief; SCR-1) | `#talk` button (data-act `talk`) in the composer, above the field, on every chat step, including during safety and pending | Check F: `#talk` visible and enabled at the 7 chat steps and during a pending turn |
| R10 | A label on every message: A5 names each speaker above each message (brief; anatomy "Conversation") | Skin `turnHTML` always writes a `.name` line (no same-speaker collapsing) | Check D: every `#thread .turn` and every `.thread-mini .turn` has a `.name` child |
| R11 | No typing indicator beyond the plain "replying…" line; no confidence %; no wait times (brief; do-not-carry-over list) | Pending is a quiet text line, no dots, no animation; no confidence or timing text anywhere | Check E: regex `/\d\s?%|thought for|queue position|estimated wait|wait time/i` finds nothing in `#app` text on any step |
| R12 | Anatomy: framed canvas, hairline cards with tinted header rows, mint customer turns, grey assistant turns, tabs with emerald underline, charcoal Send, 8 px buttons, split button, tags not pills, safety the only square object | Sections 4-5 mapping; CSS ported from the look-sheet generator | Wireframe PNGs read with the Read tool and compared with the look sheet (Step 7.8) |
| R13 | Fonts Instrument Sans (headings) / Inter (body, `tabular-nums`) / Geist Mono (refs), all OFL, embedded (brief; anatomy "Typography") | Step 1 subsets three woff2 files; build.py `FONTS['a5']`; CSS `font-variant-numeric: tabular-nums` on every number | `document.fonts` check (Step 7.2, check I): the three families report `loaded` |
| R14 | FLOW-5: windows, then code, before the write; FLOW-3: "send a new code" on expiry (brief) | Engine order already is slots, then code, then booked. Skin adds a "Send a new code" link on the code card (data-act `stub`, toast explains) | Click-through: code card contains `[data-fk=resend]`; clicking it shows a toast |
| R15 | Copy rules: promise text, no wait or queue words, "Windows are shown, not held", 10-minute expiry and 3 tries stated before typing (SCREEN_SPECS) | Copy is reused from engine `TXT` and A3 strings; no new promises | Spot read in the wireframes; check E |
| R16 | No horizontal overflow at 390, 430, 500 px (brief) | Grid items use `minmax(0, 1fr)`, long strings `overflow-wrap: anywhere`; no fixed widths over 100% | Step 7.3: for 8 steps x 3 widths `scrollWidth <= clientWidth` and `bad` empty |
| R17 | AA contrast for all text pairs, both themes (brief; WCAG 2.2) | Tokens copied from the look sheet (already pass), plus `--line` and `--focus` tokens defined in 4.2 | Step 7.5 inline script prints `FAILS 0` |
| R18 | Click-through of all 8 steps with no console errors (brief) | All engine hooks preserved (section 4.1) | Step 7.2: zero entries in `errors` for light and dark files, reduced and normal motion |
| R19 | Wireframes `A5-chat-390-light.png`, `A5-chat-1280-light.png`, `A5-case-1280-light.png` plus dark (brief) | Step 7.6 | Files exist with sizes 390x844, 1280x800, 1280x800 (`file` command) |
| R20 | Headless runs capped with `perl -e 'alarm 60; exec @ARGV'`, temp profile under `TMP`, never touch or kill a running browser (brief) | `shoot.py` already launches its own persistent context with a temp profile under `TMP`; every command is wrapped in the alarm | Command lines in section 7 |
| R21 | Safety is never pending and "Talk to a person" is never pending (planner decision, protects R7 and R9) | `thinking(g)` is not called in `RUN.safety` and is skipped when `opt.trigger === 'button'` | Pending test: with slow mode on, `#safety` shows the card at once; the button path shows no pending line |

---

## 4. Shared code to use

### 4.1 Hook contract: the skin must keep every one of these exactly (the engine and the check scripts depend on them)

Start `a5.skin.js` by **copying `a3.skin.js` whole**, then change markup and classes function by function as section 5 says. Do not rename anything in this table.

| Kind | Names |
|---|---|
| Element ids | `app` (engine-owned), `thread`, `panel`, `pinned`, `banner`, `strip`, `strip-body`, `strip-summary`, `staffing`, `assistant-state`, `composer-input`, `composer-hint`, `talk`, `case-root`, `where-input`, `code-input`, `code-err`, `inbox`, `ev-panel`, `brief`, `src-<id>` (on each source card, `tabindex="-1"`), `tab-sources`, `tab-conversation` |
| `data-act` | `talk`, `choose` (+ `data-key`, `data-val`), `slot-day` (+ `data-val` = day key), `slot-win` (+ `data-day`, `data-val` = window key), `slot-book`, `inbox`, `inbox-use`, `inbox-close`, `follow-ch`, `follow-when`, `follow-save`, `follow-change`, `demo-join`, `stub` (+ `data-msg`), `case-select`, `case-tab`, `src-jump`, `case-claim`, `case-call`, `case-flag`, `case-join` |
| `data-form` | `composer`, `where`, `locate`, `code`, `call`, `flag` (each on a `<form>`; submit buttons inside) |
| other `data-*` | `data-fk` on every focusable control exactly as in `a3.skin.js` (the engine restores focus by it); `data-bind="where.value"`, `"code.name"`, `"code.phone"`; `data-ref` on each queue button, which sits inside a `<ul data-queue>` |
| Names | radio inputs `name="fu-ch"`, `name="fu-when"`, `name="outcome"` (the call form reads `[name=outcome]:checked`); the flag form has one `<select>` |
| Skin API (window.SKIN) | `code`, `name`, `chatShell`, `caseShell`, `item`, `panel`, `stripSummary`, `staffing`, `banner`, `assistantState`, `safety`, `inbox`, `caseView`, plus the new boolean `pending: true` |
| Class hooks the engine itself adds or toggles | `is-arriving`, `is-hl`, `is-safety` on `#strip`, `data-safety` attribute on `#app`, `data-staffing` on `#app`, `data-view` on `#app` |

Engine objects the skin reads (signatures, from `engine.js`):

- `item(it, S, c)`: `it` = `{ kind: 'turn', who: 'assistant'|'customer'|'rep', time, html, card?: { type, key, ... }, sources?: [keys], after?: html, quiet?: true, viaButton?: true }` or `{ kind: 'event', time, html, icon: 'person'|'pause'|'info' }` or (new) `{ kind: 'pending', stage: 1|2 }`.
- `S` fields used: `S.items`, `S.cards[key]` (`done`, `choice`, `value`, `err`, `day`, `win`, `stage`, `name`, `phone`, `attempts`, `channel`, `when`), `S.visit` (`day {long, full, dow, d, key}`, `win {label}`, `winKey`, `tech`, `feeNote`, `freeUntil`), `S.request` (`ref`, `due`, `live`, `follow {channel, when}`), `S.identity` (`'sent'|'verified'|null`), `S.safety`, `S.staffing` (`'none'|'sim'`), `S.live` (`'queued'|'joined'|null`), `S.hl`.
- `c` (ctx): `TXT`, `SRC`, `CHECKS`, `DAYS`, `WIN`, `TECH`, `CASE`, `QUEUE`, `esc`.
- `CASE.sections[]` `{ n, h, kind: 'fact'|'quote'|'claim'|'decide'|'plain', items[{ t, src?, tag? }] }`; `CASE.sources[]` `{ id, title, file, ver, rows?, quote?, fact?, status }`; `CASE.transcript[]` `{ who: 'assistant'|'customer'|'event', time, text }`; `CS` = `{ sel, tab: 'sources'|'conversation', claimed, callOpen, flagOpen, flagged, hl, acts[] }`.

### 4.2 Palette tokens (copied from `build_a5_look.py` `LIGHT` / `DARK`; do not change a value except `--line` per the rule below)

Token names in `a5.css` are the look sheet's own names, prefixed `--`.

| Token | Light | Dark |
|---|---|---|
| ground | `#E5E9F0` | `#0B0F12` |
| panel | `#FFFFFF` | `#151A1E` |
| rail | `#F5F6F7` | `#11161A` |
| well | `#F3F5F7` | `#20272C` |
| selected | `#E5E9F0` | `#2A3238` |
| hair | `#E3E7EB` | `#2C343A` |
| mint | `#E2F8EF` | `#0F3326` |
| mint-edge | `#B4EDD5` | `#17513C` |
| ink | `#101216` | `#E9EDF0` |
| ink2 | `#5B656D` | `#A7B1B9` |
| primary | `#007847` | `#00BC6F` |
| on-primary | `#FFFFFF` | `#03140C` |
| signal | `#00BC6F` | `#00BC6F` |
| charcoal | `#202629` | `#DDE3E8` |
| on-charcoal | `#FFFFFF` | `#101216` |
| person | `#2A2663` | `#A9A4F0` |
| on-person | `#FFFFFF` | `#14123A` |
| danger | `#B42318` | `#C8312F` |
| on-danger | `#FFFFFF` | `#FFFFFF` |
| **line** (added; input and well edges, needs 3:1) | `#7F8A91` | `#6B767E` |
| **focus** (added; focus ring) | `#007847` | `#00BC6F` |

`--line` is the only value the implementer may adjust, and only if the contrast script fails on a pair that uses it: darken (light) or lighten (dark) in steps of about 4% lightness and record the final value in the report. All other tokens failing contrast is a plan error: stop and report.

`:root` block rules (so `scripts/contrast.py`-style parsing and `build.py` both work): colour tokens as `--name: #RRGGBB;` pairs in the first `:root { … }` block; the dark values as **bare declarations** between `/*DARK-START*/` and `/*DARK-END*/` placed **after** the closing brace of `:root` (exactly like `a3.css` lines 4-28). Do not put `rgba()` values in that block.

Font variables: `--display: "A5 Display", "Instrument Sans", "Helvetica Neue", Arial, sans-serif;` `--sans: "A5 Sans", Inter, system-ui, -apple-system, "Segoe UI", sans-serif;` `--mono: "A5 Mono", "Geist Mono", ui-monospace, Menlo, monospace;`

### 4.3 Look-sheet rules to port (source: the `CSS` string in `build_a5_look.py`, lines 189-300)

Copy these rules' declarations verbatim (values, radii, paddings, weights), renaming selectors per the right-hand column. The look sheet's `var(--x)` names already match the tokens above.

| Look-sheet selector | A5 prototype selector | Notes |
|---|---|---|
| `.topbar`, `.topbar b`, `.topbar span`, `.topbar div` | `.ch-head`, `.brand-n`, `.brand-s`, `.brand-t` | `b` = 16 px Instrument Sans 600; `span` = 12.5 px ink2 |
| `.mark`, `.topbar .mark`, `.cap .mark` | `.mark`, `.ch-head .mark` (30x30, radius 8), `.name .mark` (18x18, radius 5) | mint square, primary-coloured glyph, `box-shadow: inset 0 0 0 1px var(--mint-edge)` |
| `.demo` | `.demo-bar` | well strip, 12 px, ink2, centred; the two `.chip` children are plain text separated by a `·` pseudo-element (see 5.1) |
| `.cap`, `.cap b`, `.cap.right` | `.name`, `.name b`, `.turn-customer .name` | 12 px, ink2, `b` ink 600 |
| `.ai` | `.turn-assistant .blk` | well, radius `4px 12px 12px 12px` |
| `.me` | `.turn-customer .blk` | mint, radius `12px 4px 12px 12px` |
| `.card`, `.cardhead`, `.cardhead .i`, `.cardhead span`, `.cardbody` | `.acard`, `.cardhead`, `.cardhead .ic`, `.cardmeta`, `.cardbody` | radius 12, hairline, header on `rail` with bottom hairline, icon in `primary` |
| `.tabs`, `.tabs span`, `.tabs b`, `.tabs .on` | `.daytabs`, `.daytab`, `.daytab b`, `.daytab[aria-pressed="true"]` | 2 px primary underline on the chosen day; `min-height: 48px` |
| `.wins`, `.wins span`, `.wins .taken`, `.wins .taken i`, `.wins .pick` | `.wins`, `.win`, `.win.is-taken`, `.win.is-taken i`, `.win.is-sel` | `min-height: 44px`; taken sinks to `well`, time struck through, the word "Taken" below |
| `.row`, `.row>span`, `.row b` | `.row`, `.row-l`, `.row-v` | dashed hair rule, label ink2 left, value 600 right, `tabular-nums` |
| `.tag`, `.tag.strong` | `.tag`, `.tag-strong` and `.ptag` | filled 6 px corners, icon + word; strong = `selected` fill + `box-shadow: inset 0 0 0 1px var(--ink2)` |
| `.cardbody h3` | `.promise` | 18 px Instrument Sans 600 |
| `.choices span`, `.choices .on`, `.radio` | `.fu .radio`, `.fu .radio:has(input:checked)` | option tiles with 8 px radius; checked = mint + 2 px primary edge. The native radio input stays (accent-color: primary) |
| `.pri` | `.btn-p` | primary, 8 px radius, `min-height: 44px`, 600 15 px Inter |
| `.fine` | `.hint` | 12 px ink2 |
| `.dock`, `.opt` | `.composer`, `.talk` | Talk to a person = white tile, hairline, 8 px radius; **raise `min-height` to 44px** (the sheet's 34 px fails the 44 px rule for SCR-1) |
| `.composer`, `.send` | `.cp-well`, `.send` | well field, charcoal Send, 7 px radius, text "Send" |
| `.safety`, `.band`, `.safety ol`, `.safety li`, `.safety p`, `.quiet` | `.safety`, `.sf-band`, `.sf-list`, `.sf-list li`, `.sf-p`, `.is-quiet .blk` | square corners, no hairline, no tint, `border-bottom: 4px solid var(--danger)`; list text 20 px Instrument Sans 600; paragraph 15 px |
| `.console`, `.app`, `aside.q`, `.who`, `.disc`, `.console h4` | `.console`, `.cs-frame`, `.q-col`, `.who`, `.disc`, `.q-g` | 24 px frame on ground; rail column; uppercase 12 px section labels (`text-transform: uppercase; letter-spacing: .06em`; text in the markup stays sentence case) |
| `.qrow`, `.qrow.sel` | `.qrow`, `.qrow.is-sel` | selected row takes `selected` |
| `.bar`, `.id`, `.titlepill`, `.split`, `.split i` | `.bar`, `.bar .mono`, `.titlepill`, `.split`, `.split-c` | header row spans brief + evidence |
| `.tabs2`, `.tabs2 .on` | `.tabrow`, `.tabrow [aria-selected="true"]`, `.brief-h` | 2 px primary underline |
| `.draft`, `.dhead`, `.draft .row`, `.big` | `.draft`, `.dhead`, `.draft .row`, `.big` | the mint "written by the assistant" block with the glow: `linear-gradient(135deg, var(--mint-edge) 0%, var(--mint) 22%, var(--mint) 100%)` |
| `.sec`, `.sec h5`, `.lbl`, `.claims` | `.bsec`, `.bsec > summary`, `.lbl`, `.claims` | hairline section; customer claims in a `well` block |

Typography: phone body 15 px (`.9375rem`), console 14 px (`.875rem`); headings `font-family: var(--display); font-stretch: 96%`; refs and IDs `font-family: var(--mono)`; every time, fee, date and number element gets `font-variant-numeric: tabular-nums`; `body { font-feature-settings: "cv11"; -webkit-font-smoothing: antialiased; }`; `text-wrap: balance` on headings, `pretty` on paragraphs; `q, blockquote, em, i { font-style: normal }` (no italic face is embedded).

---

## 5. Steps

Run every step from `P` unless it says otherwise. Do the steps in order; each ends with a check.

### Step 0. Pre-flight (read-only snapshots)

```
mkdir -p /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-shots /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/fonts-work-a5
cd /Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts
shasum -a 256 2026-10-20-direction-A1-work-order.html 2026-10-20-direction-A2-route-sheet.html 2026-10-20-direction-A3-dispatchers-log.html > /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-before.sha
cp _build/direction-prototypes/src/engine.js /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-engine.before.js
cp _build/direction-prototypes/scripts/build.py /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-build.before.py
```

### Step 1. Fonts (three woff2 files)

Sources already exist: `TMP/fonts-src-a5/InstrumentSans.ttf` (axes wdth 75-100, wght 400-700), `Inter.ttf` (opsz 14-32, wght 100-900), `GeistMono.ttf` (wght 100-900). All SIL OFL 1.1. Run (this is the proven recipe from `scripts/subset.sh`; do not edit that file):

```
S=/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/fonts-src-a5
W=/Users/innocentnortey/.claude/jobs/0d72ed71/tmp/fonts-work-a5
O=/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/_build/direction-prototypes/fonts-out
U="U+0020-007E,U+00A0-00FF,U+0131,U+0152-0153,U+2010-2027,U+2030-203A,U+2190-2193,U+2212,U+20AC,U+2122"
run() { uv run -q --with fonttools --with brotli "$@"; }
run fonttools varLib.instancer "$S/InstrumentSans.ttf" wght=400:700 wdth=90:100 -o "$W/is.ttf" -q
run fonttools varLib.instancer "$S/Inter.ttf" opsz=14 wght=400:700 -o "$W/inter.ttf" -q
run fonttools varLib.instancer "$S/GeistMono.ttf" wght=400:600 -o "$W/gm.ttf" -q
sub() { run pyftsubset "$1" --unicodes="$U" --layout-features='kern,liga,tnum,lnum,case,calt,cv11' --flavor=woff2 --output-file="$2"; }
sub "$W/is.ttf" "$O/a5-display.woff2"
sub "$W/inter.ttf" "$O/a5-sans.woff2"
sub "$W/gm.ttf" "$O/a5-mono.woff2"
ls -la "$O"/a5-*.woff2
```

Pass: three files, each between 10 KB and 70 KB. If `instancer` fails on an axis range, report the error text; do not substitute another font.

### Step 2. build.py registration (A5 only)

Edit `DP/scripts/build.py`, four insertions and one default change, nothing else:

1. In `FONTS`, after the `'a3'` entry add:
```python
  'a5': [('A5 Display', 'a5-display.woff2', 'normal', '400 700', 'font-stretch: 90% 100%;'),
         ('A5 Sans', 'a5-sans.woff2', 'normal', '400 700', ''),
         ('A5 Mono', 'a5-mono.woff2', 'normal', '400 600', '')],
```
2. In `META`, after `'a3'` add:
```python
  'a5': ('2026-10-21-direction-A5-service-desk.html', 'Meridian · A5 Service desk',
         'Direction prototype A5 Service desk for the Meridian AI service agent (UX-2). Synthetic demo data.'),
```
3. In `LICENCE`, after `'a2'` add:
```python
  'a5': 'Fonts: Instrument Sans, (c) 2022 The Instrument Sans Project Authors; Inter, (c) 2016 The Inter Project Authors; Geist Mono, (c) 2024 The Geist Project Authors; SIL Open Font License 1.1; Latin subsets.',
```
4. In `__main__`: change `ks = sys.argv[1:] or ['a1', 'a2', 'a3']` to `ks = sys.argv[1:] or ['a5']`. (This keeps a bare `build.py` from rewriting the A1-A3 files with the new engine.)

Pass: `python3 -c "import ast,sys; ast.parse(open('docs/artifacts/_build/direction-prototypes/scripts/build.py').read())"` exits 0; `diff` against `TMP/a5-build.before.py` shows only those four insertions and the one changed line.

### Step 3. `src/a5.css`

Create `DP/src/a5.css`. Header comment: one line naming A5 Service desk, the look sheet and the font stack. Structure, in this order:

1. `:root { color-scheme: light dark; --display…; --sans…; --mono…; <all light tokens of 4.2> }` then `/*DARK-START*/ <dark tokens as bare declarations> /*DARK-END*/`.
2. Base: `* { box-sizing: border-box }`, `body` (margin 0, `background: var(--ground)`, `color: var(--ink)`, `font: 400 .9375rem/1.5 var(--sans)`, smoothing, `cv11`), `#app { height: calc(100dvh - 40px) }`, `button, input, select { font: inherit; color: inherit }`, `.sr` (copy from a3.css line 34), `.ic { width:18px; height:18px; fill:none; stroke:currentColor; stroke-width:1.8; stroke-linecap:round; stroke-linejoin:round; flex:none }`, `.ic[viewBox="0 0 20 20"] { stroke-width: 1.5 }`, `:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px }`, tabular-nums rule for `time, .row-v, .win, .daytab, .lines, .snap, .qrow, .chip, .mono`, heading `text-wrap`, `.mono { font-family: var(--mono); font-size: .92em; white-space: nowrap }`.
3. Proto bar additions (neutral): `.pb-btn[aria-pressed="true"] { background: #E9EDF0; color: #262A31 }` (the bar itself comes from `proto.css`; do not restate it).
4. **Chat frame and layout** (write exactly this skeleton, then fill the rest from 4.3):
   - `.chat { height: 100%; display: flex; flex-direction: column; background: var(--panel); overflow: hidden }`
   - `@media (min-width: 760px) { #app { padding: 12px } .chat { border-radius: 24px; box-shadow: 0 0 0 1px var(--hair) } }` (the "framed white app on a cool canvas"; below 760 px the page itself is the phone, canvas shows as the demo strip and device edge)
   - `.ch-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 12px 14px; background: var(--panel); border-bottom: 1px solid var(--hair) }`, `.brand { display: flex; align-items: center; gap: 10px; min-width: 0 }`, `.brand-n` (Instrument Sans 600 16 px, margin 0), `.brand-s` (12.5 px ink2, margin 0), `.link-b` (no background, `color: var(--primary)`, underline, 600, `min-height: 44px`, `padding: 0 8px`).
   - `.demo-bar { display: flex; flex-wrap: wrap; justify-content: center; gap: 0 6px; padding: 6px 12px; background: var(--well); color: var(--ink2); font-size: .75rem }`, `.chip { background: none; padding: 0 }`, `.demo-bar .chip + .chip::before { content: "·"; margin-right: 6px }`.
   - `.banner` = staffing banner: `background: var(--rail); border-bottom: 1px solid var(--hair); padding: 8px 14px; font-size: .875rem; display: flex; flex-wrap: wrap; gap: 8px 14px; align-items: center`.
   - `.strip` (phone summary): `border-bottom: 1px solid var(--hair); background: var(--panel)`; `.strip > summary { min-height: 48px; padding: 8px 40px 8px 14px; list-style: none; cursor: pointer; position: relative; display: flex; gap: 10px; align-items: center; font-size: .8125rem }` with a chevron `::after` copied from `a3.css` lines 69-72 (colours `var(--ink2)`); `.st-l { font: 600 .875rem var(--display) }`; `.strip-b { padding: 0 12px 12px; max-height: 52vh; overflow-y: auto }`; `.strip.is-safety { display: none }`.
   - `.ch-main { flex: 1; min-height: 0; display: grid; grid-template-columns: minmax(0, 1fr) }`, `.ch-col { display: flex; flex-direction: column; min-height: 0; min-width: 0 }`, `.panel { display: none }`.
   - `@media (min-width: 1024px) { .ch-main { grid-template-columns: minmax(0, 1fr) 360px } .panel { display: block; overflow-y: auto; padding: 16px; background: var(--rail); border-left: 1px solid var(--hair) } .strip { display: none } }`.
   - `.thread { flex: 1; min-height: 0; overflow-y: auto; display: flex; flex-direction: column; gap: 14px; padding: 16px 14px 20px; background: var(--panel) }`; children `max-width: 640px`.
   - `.pinned { flex: none }`.
5. Conversation: `.day-div` (centred quiet line on hairlines: `display:flex; align-items:center; gap:12px; font-size:.75rem; color: var(--ink2)`, `::before/::after { content:""; flex:1; height:1px; background: var(--hair) }`), `.turn { display:flex; flex-direction:column; align-items:flex-start; gap:5px; container-type: inline-size; width:100% }`, `.turn-customer { align-items:flex-end }`, `.name`, `.blk { max-width: 62ch; padding: 10px 12px }` with the radii of 4.3, `.turn-rep .blk` = assistant style, `.disc` (indigo initial disc 24 px for Riley), `.logevt` (centred quiet system line: `.logevt .evt { justify-content:center }` with hairline pseudo-elements like `.day-div`), `.logevt.is-join` same, `.pending` line (`color: var(--ink2); font-size: .875rem; text-align: center`; **no animation**).
6. Cards and controls: `.acard`, `.cardhead`, `.cardmeta`, `.cardbody` (4.3), `.btn` (`min-height: 44px; padding: 0 18px; border-radius: 8px; border: 1px solid transparent; font-weight: 600; cursor: pointer`), `.btn-p` (primary), `.btn-q` (white, `border-color: var(--hair)`, hover `background: var(--well)`), `.btn-s` (`min-height: 44px; font-size: .875rem`), `.btn:disabled { opacity: .5; cursor: not-allowed }`, `.acts`, `.in` (label above input), `.in input, select { min-height: 46px; padding: 0 12px; border: 1px solid var(--line); border-radius: 8px; background: var(--panel) }`, `.in input[aria-invalid="true"] { border: 2px solid var(--ink) }`, `.in-code input` (letter-spacing .3em, 20 px, tabular), `.inl`, `.two`, `.err { margin: 10px 0 0; font-weight: 600 }` with `.err::before { content: "! " }` (ink, **never red**), `.hint`, `.links a`, `.linkbtn` (text button for "Send a new code": `background:none; border:0; color: var(--primary); font-weight:600; text-decoration:underline; min-height:44px; padding:0 4px`), `.checks`, `.q-t`, `.fu` + `.radio` tiles (4.3), `.saved` (`background: var(--mint); border: 1px solid var(--mint-edge)`), `.lines` table (copy a3.css lines 178-182, colours via tokens), `.reason`, `.promise`.
   - Day tabs and windows: `.daytabs { display:grid; grid-template-columns: repeat(6, minmax(0,1fr)); border-bottom: 1px solid var(--hair) }`, `.daytab { min-height: 48px; background: none; border: 0; border-bottom: 2px solid transparent; margin-bottom: -1px; color: var(--ink2); font-size: .8125rem; cursor:pointer; padding: 6px 0 }`, `.daytab b { display:block; font-size: 1rem; color: var(--ink) }`, `.daytab[aria-pressed="true"] { color: var(--ink); font-weight: 600; border-bottom-color: var(--primary) }`, `.daytab:disabled { cursor: default }`. `.wins { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 6px; margin: 10px 12px 0 }`, `.win { min-height: 44px; border: 1px solid var(--hair); border-radius: 8px; background: var(--panel); font-size: .84rem; padding: 6px; display:flex; align-items:center; justify-content:center; gap:4px; flex-wrap:wrap; cursor:pointer }`, `.win.is-sel { background: var(--mint); border: 2px solid var(--primary); font-weight: 600 }`, `.win.is-sel .ic { color: var(--primary); width: 16px; height: 16px }`, `.win.is-taken { background: var(--well); border-color: var(--well); color: var(--ink2); cursor: not-allowed }`, `.win.is-taken s { text-decoration-thickness: 1px }`, `.win.is-taken i { flex-basis: 100%; font-style: normal; font-size: .75rem; font-weight: 600; text-align: center }`.
   - Slot card margins: `.acard > .wins, .acard > .daytabs, .acard > .hint, .acard > .acts, .acard > .rows { margin-left: 12px; margin-right: 12px }` (the card body is not a wrapper for the slot card in 5.2; follow that section).
   - Source chips: `.srcs { display:flex; flex-wrap:wrap; gap:6px }`, `.src > summary { display:inline-flex; align-items:center; flex-wrap:wrap; gap:4px 8px; min-height:44px; padding: 4px 10px; border-radius: 6px; background: var(--well); font-size: .8125rem; cursor:pointer; list-style:none }`, `.src > summary::-webkit-details-marker { display:none }`, `.src[open] > summary { background: var(--mint) }`, `.src-v { color: var(--ink2) }`, `.src-b { margin-top: 6px; padding: 10px 12px; border: 1px solid var(--hair); border-radius: 8px; background: var(--panel); font-size: .875rem; max-width: 62ch }`.
7. Safety: from 4.3, plus `.pinned { padding: 0 }`, `.safety-panel` same look, `#app[data-safety] .thread > :not(:last-child) { opacity: .45; filter: grayscale(1) }`, `.ic-warn { width: 24px; height: 24px; color: var(--on-danger); flex: none }`. **`--danger` and `--on-danger` appear only in rules whose selector starts with `.safety` or `.sf-` or `.ic-warn`.** The dark-theme safety card keeps `--danger` band on `--panel`.
8. Composer: `.composer { flex: none; padding: 8px 12px 14px; background: var(--panel); border-top: 1px solid var(--hair) }`, `.cp-top { display:flex; flex-wrap:wrap; align-items:center; gap: 4px 10px; margin-bottom: 8px }`, `.talk` (4.3), `.cp-hint { font-size: .75rem; color: var(--ink2) }`, `.cp-well { display:flex; align-items:center; gap: 8px; min-height: 56px; padding: 6px 6px 6px 12px; background: var(--well); border-radius: 10px; box-shadow: inset 0 0 0 1px var(--line) }`, `.cp-well input { flex:1; min-width:0; min-height: 44px; border:0; background: transparent; outline-offset: 4px }`, `.send { min-height: 44px; min-width: 64px; padding: 0 16px; border:0; border-radius: 7px; background: var(--charcoal); color: var(--on-charcoal); font-weight: 600; cursor:pointer }`.
9. What's settled panel: `.pn-h h2` (Instrument Sans 600 19 px), `.pn-h p` (ink2 14 px), `.pn-s` = `.acard` (hairline card, 12 px radius, margin-bottom 12 px, `overflow: hidden`), `.pn-s.is-empty .cardbody p { color: var(--ink2) }`, `.strip-b .pn-s { background: var(--panel) }`. Landing wash: `@keyframes a5-wash { from { background-color: var(--mint) } }`.
10. Console (S2): `.console { min-height: 100%; display:flex; flex-direction:column }`; `.cs-head` = same as `.ch-head`; `.cs-frame` and grid:
    - default (below 1100 px): `.cs-grid { display:grid; grid-template-columns: minmax(0,1fr); background: var(--panel) }`, `.cs-main { min-width: 0 }`, `.cols { display:grid; grid-template-columns: minmax(0,1fr) }`, `.brief, .evidence { min-width:0; padding: 14px 16px }`, `.evidence { border-top: 1px solid var(--hair) }`, `.q-col { background: var(--rail); border-bottom: 1px solid var(--hair) }`, `.q-sum { min-height: 48px; padding: 0 14px; display:flex; align-items:center; gap:10px; font-weight:600; cursor:pointer }`.
    - `@media (min-width: 760px) { .cs-frame { border-radius: 24px; overflow: hidden; box-shadow: 0 0 0 1px var(--hair); margin: 0 12px 12px } .console { padding: 0 } }` (the canvas shows around the frame) and `@media (min-width: 900px) { .cols { grid-template-columns: minmax(0,1fr) 300px } .evidence { border-top: 0; border-left: 1px solid var(--hair) } }`.
    - `@media (min-width: 1100px) { #app[data-view="case"] { height: calc(100dvh - 40px) } #app[data-view="case"] .console { height: 100% } .cs-frame { flex: 1; min-height: 0 } .cs-grid { height: 100%; grid-template-columns: 280px minmax(0,1fr) } .q-col { border-bottom: 0; border-right: 1px solid var(--hair); overflow-y: auto } .q-sum { display: none } .cs-main { display:flex; flex-direction:column; min-height:0 } .cols { flex:1; min-height:0; grid-template-columns: minmax(0,1fr) 340px } .brief, .evidence { overflow-y: auto; min-height: 0 } }` and `@media (max-width: 1099px) { #app[data-view="case"] { height: auto; min-height: calc(100dvh - 40px) } }`.
    - Pieces: `.who`, `.disc`, `.q-g` (uppercase section label), `.qlist` (list-style none), `.qrow` (full-width button, `text-align:left`, grid, padding 9px 8px, 8 px radius, `min-height: 56px`), `.qr-1`, `.qr-n`, `.qr-r`, `.qr-d`, `.ptag`, `.ptag-strong`; `.bar` (flex, wrap, gap 10, padding 12px 16px, bottom hairline), `.titlepill`, `.split` (inline-flex, `margin-left: auto`, radius 8, primary background, `overflow:hidden`) with `.split-m` main button and `.split-c` caret button (both `background: transparent; color: var(--on-primary); border: 0; min-height: 40px; font-weight: 600`; caret has `border-left: 1px solid rgba(255,255,255,.35)`; in dark the on-primary colour is near-black so use `border-left: 1px solid var(--on-primary)` instead of rgba: **use `border-left: 1px solid var(--on-primary)` with `opacity` untouched**), `.tabrow { display:flex; gap: 22px; border-bottom: 1px solid var(--hair) }`, `.tabrow [role="tab"], .brief-h { min-height: 40px; background:none; border:0; border-bottom: 2px solid transparent; margin-bottom: -1px; color: var(--ink2); font-weight: 500; cursor:pointer; padding: 0 }`, `.tabrow [aria-selected="true"], .brief-h { color: var(--ink); font-weight: 600; border-bottom-color: var(--primary) }` (`.brief-h` is a heading, not interactive), `.draft`, `.dhead`, `.big`, `.bsec`, `.bs-n` (22 px square, `background: var(--well)`, radius 6, tabular), `.bsec ul`, `.claims` + `.lbl`, `.srcchip` (6 px radius tag, `background: var(--well)`, `min-height: 28px`, hover `background: var(--mint)`), `.cacts`, `.cbtn` (white, hairline `border: 1px solid var(--hair)`, 8 px radius, `min-height: 40px`), `.cbtn-p` (primary), `.mini`, `.activity`, `.src-card` (an `.acard`; `.src-card.is-hl { background: var(--mint); box-shadow: 0 0 0 2px var(--primary) }`), `.src-meta`, `.snap` (copy a3.css 303-308, zebra uses `var(--well)`), `.quote` (well block), `.fact`, `.thread-mini` (unbubbled: `.thread-mini .blk { background: transparent; padding: 0 }`, `.thread-mini .turn-customer { align-items: flex-start }`, `.thread-mini .turn { flex-direction: column }`), `.note` (internal note: `background: var(--well); border: 1px dashed var(--ink2); border-radius: 8px; padding: 10px 12px`), `.note-h`.
11. Dialog and toast: `.inbox` (white, 12 px radius, hairline, `::backdrop { background: rgba(11,15,18,.5) }`), `.inbox-m` (well block), `#toast` (fixed bottom, `background: var(--charcoal); color: var(--on-charcoal); border-radius: 8px; padding: 10px 16px`; opacity transition under no-preference).
12. `@media (max-width: 480px)` tighten paddings only; **no fixed widths**.
13. Motion (opt-in only): `@media (prefers-reduced-motion: no-preference) { .is-arriving { animation: a5-in .22s ease-out both } .is-hl > .cardhead { animation: a5-wash .4s ease-out } .win.is-sel .ic path { stroke-dasharray: 20; animation: a5-draw .16s ease-out } .logevt.is-join.is-arriving { animation: a5-fade .3s ease-out both } .btn, .win, .qrow, .cbtn, .talk { transition: background-color .15s ease-out, color .15s ease-out } #toast { transition: opacity .2s } }` with keyframes `a5-in { from { opacity: 0; transform: translateY(4px) } }`, `a5-draw { from { stroke-dashoffset: 20 } to { stroke-dashoffset: 0 } }`, `a5-fade { from { opacity: 0 } }`. Nothing slides; no typing animation; no looping animation.

Pass: file parses (build in Step 6); the two token blocks match 4.2 exactly.

### Step 4. `src/a5.skin.js`

Create it by `cp DP/src/a3.skin.js DP/src/a5.skin.js`, then rewrite function by function. File header comment: one line, "A5 · Service desk: markup construction…". Keep the IIFE and `'use strict'`. Final line registers `window.SKIN` with `code: 'A5', name: 'Service desk'` plus `pending: true`. Target length: 330-420 lines.

#### 5.1 Icons and small helpers
- Keep the A3 20x20 icon table `I` and add a second table `I24` (viewBox 24) with these exact paths (from the look sheet; stroke is set in CSS):
  - `head`: `<path d="M4 14v-2a8 8 0 0 1 16 0v2"/><rect x="3" y="14" width="4" height="6" rx="1.5"/><rect x="17" y="14" width="4" height="6" rx="1.5"/>`
  - `cal`: `<rect x="3.5" y="5" width="17" height="15" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>`
  - `clock`: `<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>`
  - `ticket`: `<path d="M4 7h16v3a2 2 0 0 0 0 4v3H4v-3a2 2 0 0 0 0-4z"/><path d="M14 7v10" stroke-dasharray="2 2"/>`
  - `check`: `<path d="M5 12.5l4.5 4.5L19 7.5"/>`
  - `warn`: `<path d="M12 3.5L2.5 20h19z"/><path d="M12 10v4.5M12 17.2v.3"/>`
  - `spark`: `<path d="M12 4v4M12 16v4M4 12h4M16 12h4M7 7l2 2M15 15l2 2M17 7l-2 2M9 15l-2 2"/>`
  - `doc`: `<path d="M7 3.5h7l4 4V20.5H7z"/><path d="M14 3.5v4h4M10 12h5M10 15.5h5"/>`
  - `chev`: `<path d="M6 9l6 6 6-6"/>`
  - `mk`: `<path d="M5 7.5h14v9H5z"/><path d="M9 11.5h6"/>` (the assistant's mark glyph: a plain mint square holding this; never a face or a robot)
- `ic(n)`: if `I24[n]` exists return `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true" focusable="false">…`; else the 20x20 form as in A3 (keeps `person`, `pin`, `receipt`, `info`, `shield`, `tool`, `phone`, `mail`, `lock`, `flag`, `pause`, `wait`, `question`, `chat`, `hand`). Unknown name falls back to `info`.
- `mark(cls)`: `<span class="mark ' + (cls||'') + '" aria-hidden="true">' + ic('mk') + '</span>'`.
- `WT` map (12-hour windows, both ends with am/pm): `{'08:00-12:00':'8:00 am – 12:00 pm','12:00-16:00':'12:00 pm – 4:00 pm','13:00-17:00':'1:00 pm – 5:00 pm','16:00-19:00':'4:00 pm – 7:00 pm'}`; `wtxt(k) { return WT[k] || k; }`. **Every place A3 printed `W.label` or `v.win.label` uses `wtxt(key)` instead** (`S.visit.winKey` holds the key; the slot card has the key in hand).
- `lv(icon, label, value, cls)`: keep the signature, ignore `icon`, return `'<div class="row ' + (cls || '') + '"><span class="row-l">' + label + '</span><b class="row-v">' + value + '</b></div>'`. CSS: `.row.stack { flex-direction: column; gap: 2px } .row.stack .row-v { text-align: left }`.
- `evt(icon, text, time, cls)`: `'<p class="evt ' + (cls||'') + '">' + (cls && /evt-in|evt-status|evt-good/.test(cls) ? ic(icon) : '') + '<span class="evt-t">' + text + '</span>' + (time ? '<time>' + time + '</time>' : '') + '</p>'`. Inline status lines (`evt-in`, `evt-status`) left-aligned with a check/status icon; lines placed inside `.logevt` are centred by CSS.
- `acard(icon, title, meta, body, cls)` replaces A3's `step()`: `'<section class="acard ' + (cls||'') + '"><header class="cardhead">' + ic(icon) + '<h3>' + title + '</h3><span class="cardmeta">' + meta + '</span></header><div class="cardbody">' + body + '</div></section>'`. `.cardhead h3 { margin:0; font: 600 .9375rem var(--display); font-stretch: 96% }`; `.cardmeta { margin-left: auto; color: var(--ink2); font-size: .8125rem }`.
- `sources(keys, c)`: keep A3's `details.src` markup, doc icon first (CSS makes it a 44 px grey 6 px-radius tag).

#### 5.2 Cards (function `card(cd, S, c)` and the `c*` helpers; keep the A3 switch)
Keep every control, attribute and branch from A3; change only wrappers and words as listed.

- `cChecks`: `acard('tool', 'Quick checks', 'Optional', body)`. Buttons unchanged (`Skip the checks` stays the one `btn-p`; the other `btn-q`).
- `cQuestion`: `acard('question', 'Question N of 2', 'Optional', body)`. All three answer buttons `btn-q`.
- `cWhere`: `acard('pin', 'Where is the visit?', 'Assistant step', body)`; done state is `lv('', 'Visit area', 'Kyle 78640 · our south zone')`.
- `cSlots` (the biggest change). Build, in this order, inside **one** `acard('cal', 'Choose a window', 'this week', …, 'step-slots')`:
  1. `<div class="daytabs" role="group" aria-label="Day">` + for each `c.DAYS` entry `d` a `<button type="button" class="daytab" aria-pressed="' + (st.day === d.key) + '" data-act="slot-day" data-val="' + d.key + '" data-fk="day-' + d.d + '"' + (st.done ? ' disabled' : '') + '><span>' + d.dow + '</span><b>' + d.d + '</b></button>'`.
  2. `<div class="wins">` + for the selected day (`st.day`, find it in `c.DAYS`) every `[key, state]` in `d.wins`: if `state === 'open'` then `<button type="button" class="win' + (sel ? ' is-sel' : '') + '" data-act="slot-win" data-day="' + d.key + '" data-val="' + key + '" data-fk="chip-' + d.d + '-' + key + '" aria-pressed="' + sel + '"' + (st.done ? ' disabled' : '') + '>' + (sel ? ic('check') : '') + wtxt(key) + '</button>'`; else `<button type="button" class="win is-taken" disabled><s>' + wtxt(key) + '</s><i>Taken</i></button>` (**no `data-act` on taken tiles**). If the day has no open window, add `<p class="hint">Every window on this day is taken.</p>` after the grid.
  3. Rows: `lv('', 'Area', 'Kyle 78640 · south zone')`, `lv('', 'Diagnostic visit', '$89')` (inside `<div class="rows">`).
  4. If `st.done`: `evt('check', 'Window chosen: ' + day.long + ', ' + wtxt(st.win), '', 'evt-in')`. Else: hint `Windows are shown, not held. Members’ fees and member-only windows appear after the code.` then `<div class="acts"><button type="button" class="btn btn-p" data-act="slot-book" data-fk="slot-book">Continue with this window</button></div>` and the `.err` paragraph when `st.err`.
  The card has no inner `.cardbody` padding conflict: give the body wrapper class `cardbody` as usual and drop the margin rules of Step 3 item 6 that assumed a bare card.
- `cCode`: locate stage: `acard('shield', 'Confirming it’s you', 'Before booking', …)` with the A3 form unchanged (primary `Send the code`). Code stage: `acard('shield', 'Confirming it’s you', 'Code sent', …)` with `lv('', 'Code sent to', 'The phone on record, ending in 02')`, the A3 code form (`Verify` primary), the `.err` paragraph, then `<p class="links"><a href="#code" data-act="inbox" data-fk="inbox-link">Open the demo inbox</a> <button type="button" class="linkbtn" data-act="stub" data-msg="Demo: a new code is offered here when a code has expired, up to the per-conversation cap. The code in the demo inbox stays 482913." data-fk="resend">Send a new code</button></p>` and the hint `Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries.` Done state: `<p class="evt evt-in">` + `ic('shield')` + "Verified for this chat · phone ending 02" + time (use `evt('shield', …, '2:08 pm', 'evt-in')`).
- `cConfirm` becomes the "Your visit" ticket: `acard('cal', 'Your visit', '<span class="tag">' + ic('check') + 'Booked</span>', body, 'step-visit')` where body = rows `Date` (`v.day.full + ', 2026'`), `Window` (`wtxt(v.winKey)`), `Technician` (`v.tech`), `Fee that applies` (`'$89 diagnostic visit'`), then `<p class="hint">` with `v.feeNote`, then `<h4 class="next-h">What happens next</h4><ul class="next">` with two `<li>` + `ic('check')`: `The technician arrives any time inside your window.` and `Changes are free until ' + v.freeUntil + '. After that, a $49 late-cancellation fee applies.` (existing A3 sentences; no new promise).
- `cAccount`: `acard('receipt', 'Invoice INV-204411', 'Balance $478.00 · unpaid', body)` with rows `Issued` `Oct 2, 2026`, `Due` `Nov 1, 2026`, then the A3 `.lines` table (caption `sr`, Total in `tfoot`).
- `cHandoff`: first `'<div class="logevt">' + evt('receipt', 'Case ' + r.ref + ' created', '2:14 pm') + '</div>'`, then `acard('ticket', 'Your request', '<code class="mono">' + r.ref + '</code>', body, 'step-handoff')`. Body, in order: `<p class="reason">` (A3 reason text, `byButton` logic kept), `<h3 class="promise">` + `c.TXT.promise`, rows `Due` (`Mon Oct 19, 7:00 pm`) and `Status` (`<span class="tag">` + `ic('clock')` + `Waiting for a representative</span>`). Then, **not done**: `<fieldset class="fu"><legend>` + `c.TXT.followAsk` + `</legend>` + the two `radio()` tiles exactly as A3 (hooks unchanged), the phone-time fieldset when `st.channel === 'phone'`, and `<div class="acts"><button type="button" class="btn btn-p" data-act="follow-save" data-fk="fu-save">Save my choice</button></div>`. **Done**: `.saved` row as A3 (icon, sentence, `Change` `btn-q btn-s` with `data-act="follow-change" data-fk="fu-change"`). No countdown, no queue position, no copy icon (see section 8).
- `cQueued`: same as `cHandoff` but promise = `c.TXT.queued`, no Due row, Status tag = `Waiting for a representative` (or, when `S.live === 'joined'`, `<span class="tag">` + `ic('person')` + `A representative has joined this chat</span>`), no form. Keep the `Case … created` line.

#### 5.3 Conversation (`turnHTML`, `item`)
- `NAME` map: `assistant: 'Meridian assistant'`, `customer: 'You'`, `rep: 'Riley'`. Suffix text: assistant ` · automated`, rep ` · Representative (demo)`.
- **Delete** the A3 `cont()` logic. `turnHTML(who, time, html, extra)` always returns:
  `'<div class="turn turn-' + who + '"><p class="name">' + lead + '<b>' + NAME[who] + '</b>' + suffix + ' · <time>' + time + '</time></p>' + (html ? '<div class="blk">' + html + '</div>' : '') + (extra || '') + '</div>'`, with `lead` = `mark()` for assistant, `<span class="disc" aria-hidden="true">R</span>` for rep, empty for customer.
- `item(it, S, c)`: 
  - `kind === 'pending'`: return `'<div class="logevt pending"><p class="evt"><span class="evt-t">' + (it.stage === 2 ? 'Still working on this…' : 'Meridian assistant is replying…') + '</span></p></div>'`. Nothing else: no dots, no spinner, no time.
  - `kind === 'event'`: `'<div class="logevt' + (it.icon === 'person' ? ' is-join' : '') + '">' + evt('info', it.html, it.time) + '</div>'`.
  - turns: `extra` = card + `after` + sources as in A3; the quiet line keeps `is-quiet` on the turn (CSS makes its `.blk` transparent, ink2). The name line stays (R10).
- The console transcript (`logTranscript`) calls `turnHTML` for every turn (no `prev` collapsing) and renders events as `<div class="logevt">`. Customer avatar: none; the name line is enough. Internal notes: `.note` with `ic('lock')`, `Internal note · <who>`, text, time; unchanged strings.

#### 5.4 Safety (`safety(c, mode)`)
```
'<section class="safety' + (mode ? ' safety-' + mode : '') + '"' + (mode ? '' : ' role="alert"') + ' aria-label="Danger: safety instruction">' +
'<div class="sf-band">' + warnSolid() + '<p class="sf-w">DANGER</p></div>' +
'<ol class="sf-list"><li>Leave the home immediately.</li><li>Call 911 or your gas utility from outside.</li></ol>' +
'<p class="sf-p">Don’t flip any light switches, open windows near the furnace, or restart any equipment.</p></section>'
```
Use the straight apostrophe in the source file exactly as quoted in R7 (`Don't`), written with `\'` or double quotes in JS. Do not use `c.TXT.safety1/2` (engine text differs). `warnSolid()` keeps A3's SVG but its inner exclamation `stroke` becomes `var(--danger)`. The numbered list is a real `<ol>` (numbers via `list-style: decimal`, 20 px, Instrument Sans 600). `stripSummary` when `S.safety`: `ic('warn') + 'Leave the home'` in ink (the strip is hidden by CSS anyway).

#### 5.5 Chat shell and panel
- `chatShell()` markup (ids exactly as 4.1):
```
<div class="chat">
 <header class="ch-head"><div class="brand">MARK<div class="brand-t"><p class="brand-n">Meridian Home Comfort</p><p class="brand-s" id="assistant-state"></p></div></div>
  <button type="button" class="link-b" data-act="stub" data-msg="The demo guide (SCR-3) is not part of this direction prototype.">Demo guide</button></header>
 <div class="demo-bar" aria-label="Demo status"><span class="chip">Fri Oct 16, 2026 · demo date</span><span class="chip" id="staffing"></span></div>
 <div id="banner" class="banner" hidden></div>
 <details id="strip" class="strip"><summary id="strip-summary"></summary><div id="strip-body" class="strip-b"></div></details>
 <div class="ch-main"><div class="ch-col"><div id="pinned" class="pinned" hidden></div>
  <div id="thread" class="thread" role="log" aria-label="Conversation" tabindex="0"><p class="day-div"><span>Fri Oct 16, 2026 (demo date)</span></p></div>
  <form class="composer" data-form="composer"><div class="cp-top"><button type="button" class="talk" id="talk" data-act="talk">HEAD Talk to a person</button><span id="composer-hint" class="cp-hint"></span></div>
   <div class="cp-well"><label for="composer-input" class="sr">Message</label><input id="composer-input" autocomplete="off"><button class="send">Send</button></div></form></div>
  <aside id="panel" class="panel" aria-label="What’s settled"></aside></div></div>
```
  (`MARK` = `mark()`, `HEAD` = `ic('head')`.) There is deliberately **no back button** (section 8).
- `assistantState(S)`: `S.live === 'joined' ? 'Riley (demo representative) is replying · assistant paused' + ref : 'Automated assistant' + ref`, where `ref = S.request ? ' · Reference <code class="mono">' + S.request.ref + '</code>' : ''`.
- `staffing(S)`: plain text, no icon: `S.staffing === 'sim' ? 'Simulated staff on shift (demo)' : 'Nobody online'`.
- `banner(S, c)`: `'<p>' + ic('info') + c.TXT.staffBanner + '</p>'` plus, when `S.live === 'queued'`, the `Demo: Riley claims the case and joins` `btn btn-q btn-s` with `data-act="demo-join"`. Empty string when not simulated.
- `panel(S, c, mode)`: header `<header class="pn-h"><h2>What’s settled</h2><p>Fills in as things are confirmed.</p></header>` (omitted in `'strip'` mode). If `S.safety` return header + `safety(c, 'panel')`. Otherwise each block is `'<section class="acard pn-s' + hl(k) + (empty ? ' is-empty' : '') + '"><header class="cardhead">' + ic(icon) + '<h3>Title</h3><span class="cardmeta">meta</span></header><div class="cardbody">…</div></section>'`:
  - "Who is replying" (only when `S.staffing === 'sim'`, `hl('control')`, icon `chat`/`pause`): body = the A3 sentence.
  - "Your visit" (`hl('visit')`, icon `cal`): empty body `<p>Nothing booked yet.</p>`; booked body = rows `Date` (`v.day.long`), `Window` (`wtxt(v.winKey)`), `Technician` (`v.tech`), `Fee` (`$89 diagnostic visit`).
  - "Your request" (`hl('request')`, icon `ticket`, meta = mono ref when `S.request`): none open `<p>No request open.</p>`; live: rows `Reference` + `<p>` (A3 live sentences); standard: `<p>A representative will get back to you within 1 business day.</p>` + rows `Due` (`r.due`), `Follow-up` (`r.follow ? r.follow.channel + (r.follow.when ? ', ' + r.follow.when.toLowerCase() : '') : 'Not chosen yet'`).
  - "Identity" (`hl('identity')`, icon `shield`): the three A3 sentences.
  `hl(k)` = `S.hl === k ? ' is-hl' : ''`. The mint wash is the `.is-hl > .cardhead` rule.
- `stripSummary(S)`: `<span class="st-l">What’s settled</span><span class="st-b">` + bits (`ic('cal')` + `day.long + ', ' + wtxt(winKey)`; `ic('ticket')` + `ref + ', due Mon 7:00 pm'`) or `<span class="st-none">Nothing yet</span>` + `</span>`.
- `inbox(c)`: A3 markup unchanged (class names kept; styled by 11).

#### 5.6 Console (`caseShell`, `qrow`, `caseView`)
- `caseShell()`: `<div class="console"><header class="ch-head cs-head"><div class="brand"><span class="disc" aria-hidden="true">R</span><div class="brand-t"><p class="brand-n">Meridian staff console</p><p class="brand-s">Demo staff sign-in · Riley (demo representative)</p></div></div><div class="demo-bar-inline"><span class="chip">Fri Oct 16, 2026 · demo date</span></div></header><div id="case-root" class="case-root"></div></div>`. (`.demo-bar-inline { font-size: .75rem; color: var(--ink2) }`.)
- `qrow(q, CS, c)`: `<li><button type="button" class="qrow' + (sel ? ' is-sel' : '') + '" data-act="case-select" data-val="' + q.ref + '" data-ref="' + q.ref + '" data-fk="q-' + q.ref + '"' + (sel ? ' aria-current="true"' : '') + '>` line 1 `<span class="qr-1"><b class="qr-n">' + q.reason + '</b>' + TAG + '</span>`; line 2 `<span class="qr-d">' + q.who + ' · <code class="mono">' + q.ref + '</code> · ' + DUE + '</span></button></li>'`. `TAG` = overdue: `<span class="ptag ptag-strong">` + `ic('clock')` + `Overdue</span>`; band `safety`: `<span class="ptag">` + `ic('warn')` + `Safety</span>` (icon in **ink**, not red); else `<span class="ptag">` + `q.p + ' ' + q.pword</span>` (e.g. `P3 Standard`). `DUE` = overdue: `'was due ' + q.due`; safety: `q.note`; else `'Due ' + q.due`. No preview line.
- `caseView(CS, c)` returns `'<div class="cs-frame"><div class="cs-grid">' + queue + '<div class="cs-main">' + bar + '<div class="cols">' + brief + evidence + '</div></div></div></div>'`:
  - `queue`: `<details class="q-col"' + (wide ? ' open' : '') + '><summary class="q-sum">' + ic('chat') + 'Queue · ' + n + ' cases</summary><div class="q-in"><div class="who"><span class="disc" aria-hidden="true">R</span><div><b>Riley</b><small>Representative (demo)</small></div></div><h3 class="q-g">Needs attention first</h3><ul data-queue class="qlist">safety rows</ul><h3 class="q-g">By due time</h3><ul data-queue class="qlist">rest</ul></div></details>` (same `wide` test as A3: `matchMedia('(min-width: 1100px)')`).
  - `bar` (spans brief and evidence): for the selected queue row `q` (find in `c.QUEUE` by `CS.sel`): `<div class="bar"><code class="mono">' + q.ref + '</code><span class="titlepill">' + (q.ref === K.ref ? 'Billing dispute · due ' + K.due : q.reason) + '</span>' + CLAIM + '</div>'`. `CLAIM` only for `q.ref === K.ref`: not claimed: `<span class="split"><button type="button" class="split-m" data-act="case-claim" data-fk="act-claim">Claim</button><button type="button" class="split-c" data-act="stub" data-msg="Release and Resolve live in this menu in the product. They are not built in this prototype." aria-label="More actions">' + ic('chev') + '</button></span>'`; claimed: `<span class="tag">` + `ic('person')` + `Claimed by Riley (demo)</span>`.
  - `brief`: when `CS.sel !== K.ref` keep A3's message and `Open MHC-C-0007` button (`cbtn cbtn-p`, hooks unchanged). Otherwise `<main class="brief" id="brief"><h2 class="brief-h">Brief</h2>` then, in order:
    1. status line: A3's `evt('person'|'wait', …, '', 'evt-status')` (word + icon, ink).
    2. the mint block: `<section class="draft" aria-label="Promise shown to the customer"><div class="dhead">' + ic('spark') + '<b>Promise shown to the customer</b></div><p class="big">' + K.promise + '</p>' + lv('', 'Due', K.due) + lv('', 'Follow up by', K.follow.channel) + lv('', 'Destination', K.follow.dest) + lv('', 'Best time', K.follow.when) + '</section>'` (rows dashed with `mint-edge`). Text inside the first 22% of the gradient uses `--ink` only (rule in 7.5).
    3. the **eight** `details.bsec` sections from `K.sections`, `open`, exactly as A3's loop (summary = `<span class="bs-n">n</span>` + heading; items `<li>` with `ic('question')` for `decide`; `srcchip` buttons `data-act="src-jump"`). Differences: for `kind === 'claim'` render the list inside `<div class="claims"><p class="lbl">' + ic('info') + 'Customer says · not checked</p><ul>…</ul></div>` and drop A3's `.nc` paragraph.
    4. `cacts` section as A3 **minus the Claim button** (Claim now lives in the header): `Log a call` (`data-act="case-call" data-fk="act-call"`, disabled until claimed), `Flag` (`case-flag`, `act-flag`), `Join chat` disabled; hint; the call and flag mini-forms and `.activity` list exactly as A3 (buttons `cbtn`).
  - `evidence`: `<aside class="evidence" aria-label="Evidence"><header class="col-h"><h2>Evidence</h2><p>What the AI saw, next to what is true now.</p></header>` + `<div class="tabrow" role="tablist" aria-label="Evidence">` with the two A3 tab buttons (ids `tab-sources`, `tab-conversation`, `aria-selected`, `aria-controls="ev-panel"`, `data-act="case-tab"`, `data-fk`) + `<div id="ev-panel" role="tabpanel" aria-labelledby="tab-…" class="ev-p">` + (sources: one `acard src-card` per source with `id="src-' + s.id + '"` `tabindex="-1"`, header `ic('doc') + title` and `cardmeta` = `s.ver`, body `src-meta` (`s.file`), the snapshot table with column heads `What the AI saw` / `Now` and `<small>Fri 2:10 pm</small>` / `<small>Fri 2:20 pm</small>` or the `blockquote.quote`, the `fact`, and `evt('check', s.status, '', 'evt-in')`; conversation: `logTranscript`).

Pass: `node --check DP/src/a5.skin.js` (if `node` is installed; otherwise rely on Step 6's console-error check).

### Step 5. `src/engine.js` (minimal; exactly these edits)

Before editing, confirm `TMP/a5-engine.before.js` exists (Step 0). Edits, in file order:

1. Line 1-3 header comment: change "Shared, word for word, by the A1 and A2 files." to "Shared by the direction files (A1-A3 embed an earlier copy; only A5 is current).".
2. After `var DEFAULTS = …` block is unaffected. After `function firstLine(…)` (line 265) add the pending helpers:
```js
  /* ---------- pending-turn demo (SCREEN_SPECS SCR-1 loading): line after 0.3 s, "still working" after 10 s ---------- */
  var slowMode = false, pendingCancel = null;
  var PENDING = { line: 300, still: 10000, reply: 13000 };
  function rerender(it) {
    var old = document.getElementById(it.id);
    if (!old) return;
    var wrap = document.createElement('div');
    wrap.innerHTML = SK.item(it, S, ctx);
    var el = wrap.firstElementChild;
    el.id = it.id;
    old.replaceWith(el);
  }
  function drop(it) {
    var i = S.items.indexOf(it);
    if (i >= 0) S.items.splice(i, 1);
    var el = document.getElementById(it.id);
    if (el) el.remove();
  }
  function thinking(g) {
    if (!slowMode || S.fast || !SK.pending) return Promise.resolve();
    return new Promise(function (done) {
      var it = null, t1, t2, t3;
      function finish() {
        clearTimeout(t1); clearTimeout(t2); clearTimeout(t3);
        pendingCancel = null;
        if (it) drop(it);
        done();
      }
      pendingCancel = finish;
      t1 = setTimeout(function () { if (g !== gen) { finish(); return; } it = say({ kind: 'pending', stage: 1 }); }, PENDING.line);
      t2 = setTimeout(function () { if (g !== gen) { finish(); return; } if (it) { it.stage = 2; rerender(it); } }, PENDING.still);
      t3 = setTimeout(finish, PENDING.reply);
    }).then(function () { if (g !== gen) throw new Stop(); });
  }
```
3. In `RUN`, insert `.then(function () { return thinking(g); })` immediately after the `pause(…, g)` call at the start of these five steps (and nowhere else; **not** in `safety`, not in the booking sub-steps that follow card answers):
   - `answer`: `return pause(450, g).then(function () { return thinking(g); }).then(function () { say(turn('assistant', '2:03 pm', TXT.a1, …`
   - `booking`: the first `pause(450, g)` (after the customer's `TXT.c2` message), same insertion before the `.then(function () { say(turn('assistant', '2:05 pm', TXT.checksIntro…`
   - `code`: after `pause(450, g)` (customer `TXT.c4`).
   - `handoff`: after `pause(500, g)`, but as `.then(function () { return byButton ? null : thinking(g); })`.
   - `live`: after `pause(500, g)`, same `byButton ? null : thinking(g)` form.
   Everything after the inserted `.then` is unchanged.
4. In `goTo(id)`: directly after `gen++; var g = gen; waiters = {};` add `if (pendingCancel) pendingCancel();`. In `talk()`: directly after `gen++; var g = gen; waiters = {}; S.busy = false; S.next = '';` add `if (pendingCancel) pendingCancel();`.
5. Replace the `DIRS` array (lines 508-512) with the single entry `{ code: 'A5', name: 'A5 Service desk', file: '2026-10-21-direction-A5-service-desk.html' }`. Leave `protoBar()`'s `DIRS.filter(d.code !== SK.code)` as is (it now yields no links). Update the comment above `protoBar` only if it names A1/A2.
6. `protoBar()`: between the "Jump to" button and the theme button add `'<button type="button" class="pb-btn" id="slow-btn" data-act="slow" aria-pressed="false" title="Demo: hold the assistant’s next replies back so the waiting lines show.">Slow reply</button>' +`.
7. In the click handler's `switch (act)` add, next to `case 'theme'`:
```js
      case 'slow': slowMode = !slowMode; a.setAttribute('aria-pressed', slowMode ? 'true' : 'false');
        toast(slowMode ? 'Slow reply is on. The next replies wait about 13 seconds: a replying line first, “Still working on this…” after 10 seconds.' : 'Slow reply is off.');
        if (!slowMode && pendingCancel) pendingCancel();
        break;
```
That is the entire engine change. No other behaviour, text or timing changes.

Pass: `diff TMP/a5-engine.before.js DP/src/engine.js` shows only hunks 1-7; `node --check DP/src/engine.js` if node exists.

### Step 6. Build

```
cd /Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter
python3 docs/artifacts/_build/direction-prototypes/scripts/build.py a5
```
Pass: prints `…/docs/artifacts/2026-10-21-direction-A5-service-desk.html <size>` (expect 150-300 KB) and writes the dark copy to `DP/shots-src/2026-10-21-direction-A5-service-desk-dark.html`. A KeyError or regex error means the `DARK-START/DARK-END` markers or `META/FONTS` entries are wrong: fix and rebuild. **Do not run `build.py` with `a1`, `a2` or `a3`.** Then confirm A1-A3 untouched: `cd docs/artifacts && shasum -a 256 -c /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-before.sha` prints three `OK`.

### Step 7. Verify (details in section 7)

Run the checks in order: 7.1 smoke, 7.2 click-through, 7.3 overflow, 7.4 pending, 7.5 contrast, 7.6 wireframes, 7.7 A1-A3 untouched, 7.8 visual comparison. Fix and rebuild until all pass; each fix rebuilds with `build.py a5`.

---

## 6. Data and fixtures

Synthetic only. Nothing new is invented: every name, number and sentence comes from `engine.js` (`TXT`, `SRC`, `DAYS`, `QUEUE`, `CASE`: Omar Patel, MHC-C-0007, INV-204411, Kyle 78640, Jun Park, code 482913, demo date Fri Oct 16 2026), themselves drawn from the issued Meridian dataset and the consolidated direction. The only new strings are UI labels listed in section 5 and the three safety lines quoted in R7. The demo phone `(512) 555-0199` stays marked "(demo number)" by the engine copy. Fonts are OFL files already downloaded under `TMP/fonts-src-a5/`.

---

## 7. Checks

Wrap every headless command: `perl -e 'alarm 60; exec @ARGV' <command>`. `shoot.py` launches its own Chrome with a temp profile under `TMP`; never attach to, restart or kill any running browser. Playwright is not installed for the system `python3`; run scratch scripts with `uv run -q --with playwright python <script>`. All scratch scripts live in `TMP` and start with:

```python
import sys, json
sys.path.insert(0, '/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/_build/direction-prototypes/scripts')
from shoot import run          # shoot.py is import-safe (its __main__ block is guarded)
import pathlib
ART = '/Users/innocentnortey/Desktop/Nortorious-Technologies/inno-aea-callcenter/docs/artifacts/'
LIGHT = ART + '2026-10-21-direction-A5-service-desk.html'
DARKF = ART + '_build/direction-prototypes/shots-src/2026-10-21-direction-A5-service-desk-dark.html'
```
`run(jobs, outdir, motion)` returns `(results, errors)`; a job is `{'url', 'w', 'h', 'shot': filename or None, 'actions': [(kind, arg)…]}` with action kinds `click`, `eval`, `wait`, `fill`, `check`, `press` (see `shoot.py`).

**7.1 Smoke.** After Step 6, load the light file at `#greeting` (1280x800) with no actions: `errors` must be `[]` and the `check` `document.querySelectorAll('.switch-link').length` must be `0`.

**7.2 Click-through** (`TMP/a5-flow.py`). Copy `scripts/flow3.py`'s `flow(a)` action list as the base, then change:
- file list = the light file only; run it a second time against `DARKF`, and a third time with motion `'no-preference'` (third argument of `run`) on the light file; all three must return `errors == []`.
- remove the `'after change (A3 only)'` label text; keep the follow-up change/save sequence (the A5 card supports it).
- the day/window step already works (`slot-day` Fri 23, then `slot-win` `12:00-16:00`); keep it. Add before the code step a `check` that `document.querySelector('[data-fk=resend]')` exists after the locate form is submitted, then `('click', '[data-fk=resend]')` and a `check` that `document.getElementById('toast').textContent` contains `new code`.
- visit all 8 hashes explicitly with fresh loads (a short job each, `('check', 'location.hash')` plus the checks below): `#greeting #answer #booking #code #handoff #safety #live #case`. For `#live` click `[data-act=demo-join]` and check `document.getElementById('thread').innerText` contains `Riley (demo representative) has joined`.
- replace the `redBg` check by **Check B**: 
  `(() => { const d = getComputedStyle(document.documentElement).colorScheme; const dark = document.documentElement.getAttribute('data-theme') === 'dark'; const red = dark ? 'rgb(200, 49, 47)' : 'rgb(180, 35, 24)'; const bad = [...document.querySelectorAll('body *')].filter(e => !e.closest('.safety') && ['color','backgroundColor','borderTopColor','borderBottomColor','borderLeftColor','borderRightColor','fill','stroke'].some(p => getComputedStyle(e)[p] === red)).map(e => e.tagName + '.' + (e.className.baseVal === undefined ? e.className : 'svg')); return JSON.stringify(bad.slice(0, 8)); })()` must return `[]` at every step; at `#safety` also check `document.querySelector('.safety .sf-band')` background equals the red and `document.querySelector('.safety').innerText` contains `Leave the home immediately.`, `Call 911 or your gas utility from outside.` and `Don't flip any light switches, open windows near the furnace, or restart any equipment.`; and the last `#thread` child text equals `Once you're outside and safe, you can leave a number here if you'd like.` (after the `Meridian assistant · automated` label).
- add these checks (each as a `check` action, run at every chat step unless noted; expected value in brackets):
  - **C** mint customer turns: first `.turn-customer .blk` background equals `rgb(226, 248, 239)` light / `rgb(15, 51, 38)` dark [true at steps with a customer turn].
  - **D** labels: `[...document.querySelectorAll('#thread .turn, .thread-mini .turn')].every(t => t.querySelector('.name'))` [true].
  - **E** banned words: `/\d\s?%|thought for|queue position|estimated wait|wait time/i.test(document.getElementById('app').innerText)` [false].
  - **F** Talk to a person: `const t = document.getElementById('talk'); !!t && !t.disabled && t.getBoundingClientRect().height >= 44` [true at the 7 chat steps; skip `#case`].
  - **G** 12-hour: `/\b\d{1,2}:\d{2}(?!\s?[ap]m)/i.test(document.getElementById('app').innerText)` [false at all 8 steps].
  - **H** targets on the chat: every visible `button, [data-act], input:not([type=radio])` inside `.chat` that is not `.pb-btn` has height >= 44 [report offenders].
  - **I** fonts: `Promise.all(['A5 Display','A5 Sans','A5 Mono'].map(f => document.fonts.load('16px "' + f + '"').then(r => r.length > 0)))` then `JSON.stringify` [`[true,true,true]`].
  - **J** keyboard: after `#booking`, `document.querySelector('.send')` is a `BUTTON`; a `focus()` on `[data-act=slot-book]` leaves `getComputedStyle(document.activeElement).outlineStyle` not `none` (when focus-visible applies via `keyboard.press('Tab')` first).
- Console errors: the returned `errors` list must be empty for all three runs.

Run: `perl -e 'alarm 60; exec @ARGV' uv run -q --with playwright python /Users/innocentnortey/.claude/jobs/0d72ed71/tmp/a5-flow.py`. If a single run needs more than 60 s, split it into two scripts (steps 1-4, steps 5-8); do not raise the cap.

**7.3 Overflow at 390, 430, 500** (`TMP/a5-overflow.py`, one run per width to stay under the cap): for each of the 8 hashes (and `#booking` after clicking the slot tiles and `#handoff` after choosing Phone, so the longest cards show) set `w` to the width, `h` 844, and read the result's `scrollWidth`, `clientWidth`, `bad`. Pass: `scrollWidth <= clientWidth` and `bad == []` for all 24+ results, light file; repeat the three widths on the dark file for `#handoff` and `#case` only.

**7.4 Pending state** (`TMP/a5-pending.py`, motion `'reduce'`): load `LIGHT + '#greeting'`, `('click', '#slow-btn')`, check `document.getElementById('slow-btn').getAttribute('aria-pressed') === 'true'`; `('click', '#jump-btn')`, `('click', '#jump-menu a[data-step=answer]')`; then, using `('wait', n)` and `('check', …)` on `document.getElementById('thread').innerText`:
- at +1000 ms: contains `Meridian assistant is replying…`, does not contain `Still working on this…`, does not contain `$189`;
- at +10800 ms (wait 9800 more): contains `Still working on this…`;
- at +13800 ms (wait 3000 more): contains neither pending line and contains `$189 per year`;
- `#talk` is enabled during the pending window (check at +1000 ms);
- second job: same start, then at +1000 ms click `#slow-btn` again; within 600 ms the thread contains `$189 per year` and no pending line (toggle-off releases the wait);
- third job: slow mode on, load `#safety` directly: `.safety` is visible with no wait and `#thread` never contains a pending line; and from `#handoff`'s predecessor click `#talk` with slow on: no pending line appears (R21).
Pass: all assertions; `errors == []`.

**7.5 Contrast** (inline, both themes; `TMP/a5-contrast.py`, run with plain `python3`). Parse tokens exactly like `scripts/contrast.py` (first `:root{}` block for light; the `DARK-START…DARK-END` declarations override for dark), using `DP/src/a5.css`. Compute WCAG ratios and require, in both themes:
- text >= 4.5: `ink/ground, ink/panel, ink/rail, ink/well, ink/mint, ink/mint-edge, ink/selected, ink2/ground, ink2/panel, ink2/rail, ink2/well, ink2/mint, ink2/selected, primary/panel, primary/well, primary/rail, primary/mint, on-primary/primary, on-charcoal/charcoal, on-person/person, on-danger/danger` (ink never sits on the red band, so there is no ink/danger pair);
- UI >= 3: `primary/panel, primary/mint, danger/panel, charcoal/panel, line/panel, line/well, focus/panel, focus/well, focus/mint, focus/ground`.
Print one line per theme and finally `FAILS <n>`; pass is `FAILS 0`. Rule that makes `ink/mint-edge` the only constraint on the glow: inside `.draft` the first 22% of the gradient never carries `--ink2` text (header and promise sentence are `--ink`; rows below sit on solid mint).

**7.6 Wireframes** (`TMP/a5-wireframes.py`, motion `'reduce'`, `out` = the `WF` directory). Six jobs, each with `wait: 1200`, `shot` as named, `full: False`:

| shot | url | w x h |
|---|---|---|
| `A5-chat-390-light.png` | `LIGHT#handoff` | 390 x 844 |
| `A5-chat-1280-light.png` | `LIGHT#handoff` | 1280 x 800 |
| `A5-case-1280-light.png` | `LIGHT#case` | 1280 x 800 |
| `A5-chat-390-dark.png` | `DARKF#handoff` | 390 x 844 |
| `A5-chat-1280-dark.png` | `DARKF#handoff` | 1280 x 800 |
| `A5-case-1280-dark.png` | `DARKF#case` | 1280 x 800 |

Pass: `file <png>` reports 390 x 844 or 1280 x 800 as above; no `errors`. The `#handoff` step ends with the handoff card and its follow-up choice visible. Do not scroll the thread or add actions to move it: the engine's own scroll-to-latest decides the frame, as it did for the A3 wireframes.

**7.7 A1-A3 untouched.** `cd docs/artifacts && shasum -a 256 -c TMP/a5-before.sha` prints three `OK`; `git`-free equivalent for the fonts: `ls -la docs/artifacts/_build/direction-prototypes/fonts-out/` shows no change in any pre-existing file (only the three `a5-*` files are new).

**7.8 Visual comparison.** Read each of the six PNGs with the Read tool, and read the look sheet's mockups by taking `TMP/a5-shots/look-1280.png` from `ART/2026-10-20-a5-look-sheet.html` (one extra `run` job, 1280 x 900, `full: True`; the sheet loads Google Fonts, a failed load is fine). Confirm and list in the report, each as yes/no: canvas visible around a white framed app (desktop); mint customer blocks and grey assistant blocks with a name line over each; hairline cards with a tinted header row and an emerald icon; one emerald button per card; charcoal Send; day tabs with an emerald underline; mint-selected window tile with a check; the safety card the only red and only square object (`#safety` shot via a scratch job); case header with mono reference, reason pill and the split button; mint "Promise shown to the customer" block; the evidence tabs; dark theme keeps the same structure with the emerald brightened.

**Tests that must stay green.** None exist for the prototypes. The regression guard is 7.7 (A1-A3 files and fonts unchanged). There is no unit-test suite for this slice, so no fast gates (type check, lint, format) apply; the equivalent gates are `node --check` on the two JS files (if `node` is installed), `python3 -c "import ast…"` on build.py, and zero console errors. The full suite is not run (nothing else in the repo imports these files).

---

## 8. Risks and requests

1. **Read-only check tooling.** `contrast.py`, `flow3.py` and `shoot.py` hardcode A1-A3 and cannot be edited by this slice, so A5 checks run as scratch scripts in `TMP`. **Request to the integrator (after the slice):** add an `'a5'` pairs entry to `scripts/contrast.py` and an A5 file to `flow3.py`'s `files` list, using the pairs and checks in 7.2 and 7.5.
2. **Engine shared surface.** `engine.js` is edited (seven hunks). A1-A3 built files keep their embedded older engine and are **not rebuilt**; they still work, but they would show their own switch links to A1-A3 only and no Slow reply button. If a rebuild of A1-A3 is ever wanted it needs `build.py a1 a2 a3` plus a decision on the direction list. Collision risk: any other slice editing `engine.js` or `build.py` in parallel.
3. **`build.py` change is slightly wider than "registration only"**: the default list in `__main__` becomes `['a5']` so a bare run cannot overwrite A1-A3. Flag if the integrator objects.
4. **Safety wording conflict (copy, not a blocker).** The brief and the look sheet use `Don't flip any light switches, open windows near the furnace, or restart any equipment.` and the two-line `Leave the home immediately.` / `Call 911 or your gas utility from outside.` `SCREEN_SPECS.md` line 138 words them differently (`Don't flip switches, open windows near the furnace, or restart equipment.`, one sentence for step 1) and the knowledge base says `leave the home immediately and call 911 or their gas utility from outside` / `Do not advise the customer to flip switches, open windows near the furnace, or restart equipment`. The prototype follows the brief for this task; UX-3 should settle the one canonical string and update the spec, the engine `TXT.safety1/2` (currently unused by A5) and the skin together.
5. **"Send a new code" is a stub.** USER_FLOWS (FLOW-3, lines 191 and 201) offers it; `SCREEN_SPECS.md` note 7 (line 624) says the signed spec has none. The prototype shows a link whose toast explains it; no expiry flow is simulated. UX-3 to reconcile.
6. **Deliberate deviations from the look sheet**, all to meet the 44 px target rule, the "label on every message" rule or honesty (no dead controls): no back button in the top bar; no copy icon beside the reference; "Talk to a person" tile is 44 px high (sheet: about 34 px); windows read "12:00 pm – 4:00 pm" and "1:00 pm – 5:00 pm" (sheet drops the first "pm"); the quiet safety follow-up line carries a name line; the console's "Brief · Conversation" tabs become a static underlined "Brief" heading plus real "Sources / Conversation" tabs in the evidence column (the engine's case state has only those two tabs, and CONCEPTS S2 specifies them); the Claim split button's caret is a stub that explains the menu is not built. If Innocent wants any of these closer to the sheet, that is a follow-up, not this slice.
7. **Not built (named so nobody assumes it is):** the 60 s `TURN_TIMEOUT` card ("This is taking longer than it should." with Try again / Talk to a person) and the `BUSY` refusal; both need new engine states and the brief limited the engine change to the two pending lines. The mint token carries two meanings (homeowner's turns on the phone, assistant-written block on the console), as the A5 risk note says; they never share a screen in this prototype.
8. **Context upkeep (integrator, not this slice).** The new HTML, wireframes and the engine change mean `docs/ux/02-concepts/CONCEPTS.md` layout-sketch lines (38, 77) still name A1/A2 files; `.claude/state/resume.md`, the ICM checklist rows and any `SUBMISSION.md` UX evidence rows should point at the A5 file and wireframes (rule `context-maintenance`). The dev log entry and the resume note are written by the integrator.
9. **Worktrees, commits, pushes:** none. The implementer does not commit.

---

## 9. Readiness

**READY.** No `NEEDS-DECISION` and no `BLOCKED-ON`: every design value comes from the A5 section, the look-sheet generator, the engine or the brief; the font sources and the Chrome binary already exist on the machine (`TMP/fonts-src-a5/`, `/Applications/Google Chrome.app`, `uv` at `/Users/innocentnortey/.local/bin/uv`).

## Deviations

1. Check E regex: the planned `\d\s?%` matches the engine's own Comfort Club text "15% off repairs" (TXT.a1, from the issued KB), so the scratch check used `confidence|\d\s?%(?! off)|…`. No confidence or percentage figure is shown anywhere else.
2. `a5.skin.js` carries a small addition not in the plan: once the three embedded fonts load, the thread is scrolled back to its latest message (fonts swap after first paint and changed line wraps left the safety step about 50 px short of the bottom at 390 px).
3. Check H lists the native radio inputs (13 px) inside the 44 px-high option tiles; the tile (label) is the target, so this is not a failure.
4. Overflow script clicks through the checks, questions and ZIP at `#booking` to show the slot tiles (the slots card does not exist when `#booking` loads).
