# Design — Meridian AI service agent (A5 Service desk)

> **Status:** PROPOSED 2026-10-21 · UX-3 (`ux-pipeline` phases.md) · awaiting the ★ UX-3 gate (Innocent).
> **What this file is:** the chosen direction made exact. It is the single source of truth (UI-2) for the look of the
> customer chat (SCR-1, plus the demo pages SCR-2 and SCR-3) and the staff console (SCR-4…SCR-11): tokens, type,
> spacing, motion, and the anatomy of every part. It does **not** define screens, regions or states per screen (that is
> `docs/ux/03-structure/SCREEN_SPECS.md`) or data shapes (that is `UI_CONTRACTS.md`).
> **The decision it makes exact (Innocent, UX-2 gate, 2026-10-21):** "alright we're going with A5": **direction A5
> Service desk, light mode first**, on concepts **C2** (chat + "What's settled" panel; the strip on a phone) and **S2**
> (queue → eight-heading brief → evidence, with Sources and Conversation tabs). A1–A4 and A6 are dropped. The earlier
> A2 draft (`_superseded/2026-10-20-design-A2.md`) set the depth and the section order of this file; none of its look
> is carried.
> **Light is primary. Dark is defined and secondary:** every token has a dark value that meets contrast, but dark has had
> less visual polish and is finished last, at UX-5.
> **Sources of the look (A5 only):**
> - [`DESIGN-DIRECTIONS.md`](DESIGN-DIRECTIONS.md) "A5 · Service desk": anatomy, palette and its sources, fonts, the
>   texture check, the "do not carry over" list;
> - **the approved look sheet's generator**, `docs/artifacts/_build/a5-look/build_a5_look.py`: its `LIGHT` / `DARK`
>   palettes and mockup CSS are the source of every value below. Colours are copied exactly; where this file differs
>   from the sheet it says so (§13);
> - the Dribbble references `dr-25…dr-34` in [`references/`](references/) (internal design reference only, S-228);
> - colour roles from the [company profile §7](../analysis/2026-10-20-meridian-company-service-profile.md#7-brand-and-color-direction).
>
> **Not invented here:** no new aesthetic. Where a part was never in the look sheet (change request, limit notice,
> TURN_TIMEOUT, BUSY, the pending lines, the code prompt, the live box, the demo inbox), it is assembled from parts
> that were, and its *Traced to* cell says so.

**Reading order.** §1–2 say what it should feel like. §3–7 are the tokens (type, colour with computed contrast,
spacing, motion, dark). §8 is every component's anatomy, each with a *Traced to* column. §9 is responsive behaviour.
§10–11 are copy tone and project do/don'ts. §12 is the house-texture check, §13 what differs from the look sheet,
§14 what looks wrong upstream. The contrast script is in the appendix.

**Token tally** (counted from the tables in this file): **30 colour primitives → 21 semantic colour tokens → 71 component tokens**, plus 16 type, 15 spacing, 7 radius, 7 line, 2 elevation and 10 motion tokens = **179 tokens in all**.

---

## 1. Feeling & audience

**Organised · timed · plain.** "A well-run service desk has my case, and I can see exactly where it stands."

| Who | Where | What they need from the look |
|---|---|---|
| **Homeowner** (SCR-1) | Phone first, one hand, often at a broken unit, sometimes hot and stressed (profile §6) | A chat that looks like a competent company's support window: white, one green action, nothing decorative. "Which of these did I say?" answered without reading. The reference and the window easy to find; safety impossible to miss |
| **Representative / supervisor / owner** (SCR-5…SCR-9) | Laptop first, usable at phone width | A help desk: queue rail, the case with tabs, evidence beside it. Due times as numbers; facts and the customer's claims visibly different; proof next to the story |
| **Reviewer** (all screens, demo pages) | Laptop, both roles in two tabs | What is real and what is simulated is obvious and calm, never alarming |

**The one impression it must leave:** *a person at a desk has this written down, and I can see where it stands.*

## 2. Aesthetic direction

**Crisp service desk.** A cool blue-grey canvas frames one white app window with 24 px corners. Inside, hairline cards
with tinted header rows, tabs with an emerald underline, one emerald action per card, a charcoal Send. Instrument Sans
for the names and the promises, Inter for everything you read, Geist Mono for references.

| Reference | What it gives us | What we leave behind (DESIGN-DIRECTIONS "do not carry over") |
|---|---|---|
| dr-25 Kirridesk (Innocent's pick) | Blue-grey canvas framing a white app; rail `#F5F6F7`; mint block; deep-green primary; charcoal second action; name lines instead of bubbles; selected-row tone; the popover header row | "Thought for 2s" timers; the notification red `#FC303D`; the white-on-`#00BC6F` button (2.49:1); the `#7D878E` captions (~3.7:1); Auto Reply and Regenerate controls |
| dr-26 Kirridesk chat widget | Grey assistant blocks, mint customer blocks, option tiles, the charcoal Send, the grey composer | The "•••" typing bubble; the running chat timer; "Connecting with agent"; the purple robot mark |
| dr-27 Auto-reply activity | A checked list of steps in a hairline card | "Thought for 10 sec"; step-by-step reasoning shown to a homeowner |
| dr-28 Refund details | Reference header with a status word; label-over-value rows; a totals block | — |
| dr-29 Conversation summary | A tinted block marked for staff only; the "Waiting for…" line | The satisfaction rating |
| dr-30 Analytics (green) | The same green-on-white mood: white cards on a pale canvas, one green action | The red/green deltas; the satisfaction gauge |
| dr-31 / dr-32 MyAlice | Centred system-event lines; a green primary under summary rows | The orange bot avatar |
| dr-33 Agento inbox | The three-pane help-desk skeleton (queue · case · profile facts) | — |
| dr-34 Keitoto (phone) | The same inbox thread held at phone width | Its saturated blue bubbles |

---

## 3. Typography

### 3.1 Families, licences, and the tabular-figure check

| Role | Family | Weights shipped | Licence | Fallback stack |
|---|---|---|---|---|
| Display: names, card titles, the promise, the safety lines, big times | **Instrument Sans** (variable, instanced at `wdth` 96) | 600, 700 | SIL OFL 1.1, © The Instrument Sans Project Authors | `"Instrument Sans", "Helvetica Neue", Arial, sans-serif` |
| Body and UI | **Inter** | 400, 500, 600 | SIL OFL 1.1, © The Inter Project Authors | `"Inter", system-ui, -apple-system, "Segoe UI", sans-serif` |
| References, IDs, codes, file names | **Geist Mono** | 400, 500, 600 | SIL OFL 1.1, © Vercel, in collaboration with basement.studio | `"Geist Mono", ui-monospace, Menlo, monospace` |

- **Tabular figures, checked 2026-10-20 with fontTools** (DESIGN-DIRECTIONS A5 "Typography"): Inter has `tnum` (tabular
  digits 1328/2048 em) but its **default digits are proportional**; Instrument Sans has `tnum` (600/1000 em); Geist Mono
  digits are all 600/1000 em, the same width as Instrument Sans's tabular digits.
- **Consequence:** `font-variant-numeric: tabular-nums` is set **on `body`**, so no time, fee, count or code can be set
  in proportional digits by accident. The look sheet's `font-feature-settings: 'cv11'` (Inter's single-storey *a*) is kept
  on `body` and combines with it.
- **Why a display face at all:** Inter alone would match house-texture trait 5 (§12). Instrument Sans carries every
  headline role, so the system is two voices, not one.
- **Mono is for references, IDs, codes and file names only.** There are no mono caps labels in A5 (that was A2).
- **Delivery:** self-hosted woff2, Latin subset, features `kern liga tnum calt` (plus `cv11` for Inter);
  `font-display: swap`; preload only Inter 400 and Instrument Sans 600. **Ship each family's `OFL.txt` beside the font
  files** in the real frontend. Fallback metrics (`size-adjust`, `ascent-override`, `descent-override`) are computed from
  the font files at UX-4 and recorded here; not guessed now.
- **Smoothing and wrapping:** `-webkit-font-smoothing: antialiased`; headings `text-wrap: balance`; paragraphs
  `text-wrap: pretty`; chat text `max-width: 62ch`.

### 3.2 Type scale

Customer screens set body at **15 px**, the console at **14 px** (A5). Above body the steps run at roughly 1.2×
(15 → 18 → 20 → 24 → 28); below it they run in 1 px steps because dense row metadata needs them. Nothing is set below
12 px. Hierarchy comes from weight and grey as much as size (UI-8).

| Token | Size / line | Family · weight · tracking | Used for |
|---|---|---|---|
| `--text-caption` | 12 / 16 px | Inter 400 | Fine print, snapshot meta, the demo bar, source file names (mono 12), "Taken" under a window |
| `--text-section` | 12 / 16 px | Inter 600 · +.06em · **uppercase** | Console column and section heads only ("Waiting in chat", "Needs my action", "Evidence"). Never on a customer screen; never on text that holds a time or a date |
| `--text-small` | 13 / 18 px | Inter 400 / 600 | Name lines (name 600, rest muted), tags (600), tabs, the label above a value, hints |
| `--text-ui` | 14 / 20 px | Inter 400 / 500 / 600 | Console body, rows and tiles on both surfaces, buttons on the console (600), card-row values |
| `--text-body` | 15 / 22 px | Inter 400 (600 for buttons) | Chat text, the composer, phone buttons, the greeting |
| `--text-card-title` | 15 / 20 px | Instrument Sans 600 | Card header rows, brief section headings, panel block titles |
| `--text-name` | 16 / 22 px | Instrument Sans 600 | The top bar's "Meridian Home Comfort" |
| `--text-lead` | 18 / 26 px | Instrument Sans 600 | The promise sentence (chat and console), handoff headline, the code card's instruction |
| `--text-title` | 20 / 26 px | Instrument Sans 600 | The safety card's numbered lines, page titles on SCR-2 / SCR-3 |
| `--text-signal` | 18 / 20 px | Instrument Sans 700 · +.1em · **uppercase** | The signal word **DANGER** / **WARNING** only |
| `--text-code` | 24 / 28 px | Geist Mono 600 · +.2em | The 6-digit code field; the code on the demo inbox |
| `--text-ref` | 13 / 18 px | Geist Mono 500 | References ("MHC-C-0007") in headers, rows and chips |

### 3.3 The four time styles

| Token | Size / line | Family · weight | Where | Example |
|---|---|---|---|---|
| `--text-time-hero` | 28 / 32 px (24 / 28 px when the card's content is narrower than 300 px) | Instrument Sans 600, tabular | The confirmation card's window; headline KPIs on SCR-9 (`--text-figure` is the same style) | **8:00 am → 12:00 pm** |
| `--text-time-due` | 18 / 26 px | Instrument Sans 600, tabular | The brief header's due; *Your request* in the panel | **Due Mon Oct 19 · 7:00 pm** |
| `--text-time-row` | 15 / 22 px on chat, 14 / 20 px on the console | Inter 600, tabular | Label-over-value rows, window tiles ("8:00 am – 12:00 pm"), the handoff card's Due row | **Mon Oct 19 · 7:00 pm** |
| `--text-time-meta` | 12 / 16 px | Inter 400, tabular | The time in a name line, a queue row's due, the log | 2:04 pm · Mon 7:00 pm |

- **Width check at a 360 px phone** (card content ≈ 296 px): "8:00 am → 12:00 pm" is about 270 px at 28 px and about
  232 px at 24 px, from the digit and letter advance widths. **Estimated, not measured:** the real fonts are not
  loaded here, so UX-4 measures it and records the result. The 24 px step exists so it can never wrap.
- The meridiem ("am", "pm") is the same size and weight as the time, lowercase, after a normal space. A5 does not shrink
  it: Instrument Sans's 600 numerals at 28 px are already narrow enough, and a full-size "pm" keeps a window readable
  at arm's length.

### 3.4 12-hour time rules

| Context | Pattern | Example |
|---|---|---|
| Arrival window (a range) | `h:mm am – h:mm pm`; the meridiem on **both** ends; en dash with spaces | 8:00 am – 12:00 pm · 12:00 pm – 4:00 pm |
| Window as a headline | the same, with `→` in place of the dash | 8:00 am → 12:00 pm |
| A point in time (due, asked, event) | `h:mm am`, always with minutes | 7:00 pm · 2:14 pm |
| Date and time, short | `Ddd Mmm d · h:mm pm` | Mon Oct 19 · 7:00 pm |
| Date and time, in a sentence | as the policy table writes it | by Monday, October 19, 7:00 pm |
| Staff rows | `Ddd h:mm pm` | Mon 7:00 pm · Fri 2:14 pm |
| Noon and midnight | `12:00 pm`, `12:00 am` | never "noon", never "0:00" |
| The demo date | `Ddd Mmm d, yyyy (demo date)` | Fri Oct 16, 2026 (demo date) |

- **Never `text-transform: uppercase` on an element that holds a time or a date.** `--text-section` and `--text-signal`
  are the only uppercase styles, and neither holds one.
- **Machine-readable:** every time is a `<time datetime="2026-10-19T19:00-05:00">` (Austin, CDT until Nov 1, 2026). The
  hero arrow is `aria-hidden` with a visually hidden "to".
- **No 24-hour string reaches the screen.** Contracts carry ISO datetimes; formatting is the frontend's job (§14, item 5).
- Times shown are the scheduling DB's and the policy table's, never the model's.
- **No countdowns, no "in 3 days":** a due is a time, not a duration (R-26; the look sheet's console row said "in 3 days",
  §13).

### 3.5 Labels and hints (replaces A2's label-plus-gloss)

A5 labels are **plain sentence case**: "Your visit", "Reference", "Due", "Standard fee". There are no mono caps labels.
Where a label alone could stump a homeowner, a **one-line hint** sits directly under it in `--text-small`,
`--color-text-muted`. These are the former glosses, wording unchanged.

| Label | Hint (customer screens) |
|---|---|
| What's settled | What's been confirmed so far |
| Your visit | Your booking |
| Arrival windows | The technician arrives any time in the window you pick |
| Standard fee | What you pay if you're not a member |
| Verify | Prove it's your account |
| Reference | Your reference number |
| Due | The latest we've promised to get back to you |
| Keep this | Save or screenshot this |
| Identity | Whether you've confirmed it's you |
| Replying | Who is answering you now |
| Source | Where this comes from |

- **Placement:** the hint wraps freely, 2 px under its label; together they count as one header; the value follows after 6 px.
- **Cell labels** inside a label-over-value row ("Date", "Technician", "Fee") are one plain word and take no hint.
- **Speaker names** are names, not jargon, and take no hint.
- **Staff screens** take no hints except where the spec gives one ("Not checked", "Changed since").

---

## 4. Colour tokens

Three tiers (UI-10): **primitives** hold raw values; **semantic** tokens give them a job and are the only colour tokens
components read; **component** tokens (§8.0) bind semantic tokens to parts. Theming is a swap of the semantic tier.
Light tokens on `:root`; `color-scheme: light dark`.

### 4.1 Primitives (30)

| Primitive | Hex | Where it came from |
|---|---|---|
| `--cool-0` | `#FFFFFF` | dr-25 app surface, dr-26 widget (look sheet LIGHT `panel`) |
| `--cool-25` | `#F5F6F7` | dr-25 navigation rail `#F5F6F7` (`rail`) |
| `--cool-50` | `#F3F5F7` | dr-25 pills `#F3F5F7`, dr-26 bot bubble `#F4F5F7` (`well`) |
| `--cool-100` | `#E5E9F0` | dr-25 canvas `#E5E9F0` (`ground`, `selected`) |
| `--cool-150` | `#E3E7EB` | proposal in the look sheet: the shots' rules sit between `#E4E6EE` and `#ECF0F3` (`hair`) |
| `--cool-600` | `#5B656D` | **adjusted:** the shot's `#7D878E` captions are ~3.7:1 on white (`ink2`) |
| `--cool-800` | `#202629` | dr-25 "Accept & Send" `#202629`, dr-26 Send `#212528` (`charcoal`) |
| `--cool-900` | `#101216` | dr-25 text cores (`ink`) |
| `--night-950` | `#0B0F12` | look sheet DARK `ground` (a proposal: no dark shot exists) |
| `--night-900` | `#11161A` | look sheet DARK `rail` |
| `--night-850` | `#151A1E` | look sheet DARK `panel` |
| `--night-800` | `#20272C` | look sheet DARK `well` |
| `--night-700` | `#2A3238` | look sheet DARK `selected` |
| `--night-650` | `#2C343A` | look sheet DARK `hair` |
| `--night-300` | `#A7B1B9` | look sheet DARK `ink2` |
| `--night-200` | `#DDE3E8` | look sheet DARK `charcoal` |
| `--night-100` | `#E9EDF0` | look sheet DARK `ink` |
| `--mid-500` | `#78838B` | **new in this file:** the control edge; the one mid-grey that holds 3:1 on every surface in both themes (§4.3) |
| `--emerald-50` | `#E2F8EF` | dr-25 AI draft `#E2F8EF`, dr-26 customer bubble `#EDFFEF` (`mint`) |
| `--emerald-100` | `#B4EDD5` | dr-25 draft glow `#B0EBD0`–`#B4EDD5` (`mint-edge`; decoration only) |
| `--emerald-500` | `#00BC6F` | dr-25 emerald `#00BC6F`; the dark theme's primary |
| `--emerald-700` | `#007847` | **adjusted on light:** dr-25 `#00BC6F` carries white at 2.49:1; darkened at the same hue (155–156°) |
| `--emerald-800` | `#17513C` | look sheet DARK `mint-edge` |
| `--emerald-900` | `#0F3326` | look sheet DARK `mint` |
| `--emerald-950` | `#03140C` | look sheet DARK `on-primary` |
| `--indigo-300` | `#A9A4F0` | look sheet DARK `person` |
| `--indigo-900` | `#2A2663` | dr-25 studio avatar `#2A2663` |
| `--indigo-950` | `#14123A` | look sheet DARK `on-person` |
| `--red-600` | `#C8312F` | look sheet DARK `danger`; the shot's `#FC303D` badge red is **not** carried |
| `--red-700` | `#B42318` | look sheet LIGHT `danger`, the same red as A4 |

### 4.2 Semantic colour tokens (20 colours + 1 alpha), light / dark

| Token | Light | Dark | Job | Profile §7 role |
|---|---|---|---|---|
| `--color-canvas` | `#E5E9F0` · `--cool-100` | `#0B0F12` · `--night-950` | The page behind the app frame | Trust / base |
| `--color-surface` | `#FFFFFF` · `--cool-0` | `#151A1E` · `--night-850` | Content, cards, the composer dock | Trust / base |
| `--color-surface-rail` | `#F5F6F7` · `--cool-25` | `#11161A` · `--night-900` | The queue rail, strip, card header rows, banner | Trust / base |
| `--color-surface-well` | `#F3F5F7` · `--cool-50` | `#20272C` · `--night-800` | Assistant turns, pills, fields, the demo bar, claims, disabled controls | Trust / base |
| `--color-surface-selected` | `#E5E9F0` · `--cool-100` | `#2A3238` · `--night-700` | The selected queue row; the strong tag's fill | Status (with words) |
| `--color-border-hair` | `#E3E7EB` · `--cool-150` | `#2C343A` · `--night-650` | Decorative separators and card edges only (1.24:1) | — |
| `--color-border-control` | `#78838B` · `--mid-500` | `#78838B` · `--mid-500` | Field, radio and claim edges; the selected row (3:1) | Readability |
| `--color-customer` | `#E2F8EF` · `--emerald-50` | `#0F3326` · `--emerald-900` | **The customer's own words and choices** (§4.6) | Warmth (the homeowner's side) |
| `--color-customer-edge` | `#B4EDD5` · `--emerald-100` | `#17513C` · `--emerald-800` | The landed wash's bottom edge; decoration only | — |
| `--color-text` | `#101216` · `--cool-900` | `#E9EDF0` · `--night-100` | Body and names | Readability |
| `--color-text-muted` | `#5B656D` · `--cool-600` | `#A7B1B9` · `--night-300` | Captions, hints, meta (adjusted for 4.5:1) | Readability |
| `--color-accent` | `#007847` · `--emerald-700` | `#00BC6F` · `--emerald-500` | The one action, the selected thing, the current tab; links and glyphs | Primary action (green, never red or orange) |
| `--color-on-accent` | `#FFFFFF` · `--cool-0` | `#03140C` · `--emerald-950` | Text on an emerald fill | Primary action |
| `--color-focus` | `#007847` · `--emerald-700` | `#00BC6F` · `--emerald-500` | The focus ring | Primary action |
| `--color-send` | `#202629` · `--cool-800` | `#DDE3E8` · `--night-200` | The Send button only | — |
| `--color-on-send` | `#FFFFFF` · `--cool-0` | `#101216` · `--cool-900` | Text on Send | — |
| `--color-person` | `#2A2663` · `--indigo-900` | `#A9A4F0` · `--indigo-300` | A representative's disc | Warmth (a person joined) |
| `--color-on-person` | `#FFFFFF` · `--cool-0` | `#14123A` · `--indigo-950` | Initial on the disc | Warmth |
| `--color-safety` | `#B42318` · `--red-700` | `#C8312F` · `--red-600` | **The safety card only** (§4.5) | Safety / danger, reserved |
| `--color-on-safety` | `#FFFFFF` · `--cool-0` | `#FFFFFF` · `--cool-0` | Text, icon and focus ring on the red | Safety / danger, reserved |
| `--color-scrim` | `rgb(16 18 22 / .5)` | `rgb(0 0 0 / .6)` | Behind the one native `<dialog>` (the demo reset confirm) | — |

- **Hover** = the resting fill mixed 8% toward `--color-text`; **pressed** = 14% (`color-mix(in oklab, …)`). Both are
  derived at use, so they add no hex. Hover applies on pointer devices only (`@media (hover: hover)`).
- **Disabled** = `--color-surface-well` fill, `--color-text-muted` text, no edge. That pair is 5.45:1 light and 6.94:1
  dark, so even disabled text stays readable; the reason is always given in words (UI-11).
- `signal #00BC6F` in the look sheet is the dark theme's primary only; the light theme never uses it (white on it is 2.49:1).

### 4.3 Computed contrast (WCAG 2.x), every pair, both themes

Computed by the script in the appendix (`python3 -I contrast.py`). Text needs **4.5:1**; edges, icons, focus rings and
state fills need **3:1**. The script exits non-zero on any failure. All pairs pass.

**Lowest values:** light text **4.57:1** (`accent` on `surface-selected`); light UI **3.18:1** (`border-control` on
`canvas` and on `surface-selected`); dark text **5.23:1** (`accent` on `surface-selected`); dark UI **3.28:1**
(`safety` on `surface`).

#### Text pairs (need 4.5:1)

| Pair | Light | Dark |
|---|---|---|
| `text` on `canvas` | 15.40:1 | 16.34:1 |
| `text` on `surface` | 18.75:1 | 14.88:1 |
| `text` on `surface-rail` | 17.33:1 | 15.46:1 |
| `text` on `surface-well` | 17.15:1 | 12.85:1 |
| `text` on `customer` | 16.88:1 | 11.72:1 |
| `text` on `surface-selected` | 15.40:1 | 11.07:1 |
| `text-muted` on `canvas` | 4.89:1 | 8.83:1 |
| `text-muted` on `surface` | 5.95:1 | 8.04:1 |
| `text-muted` on `surface-rail` | 5.50:1 | 8.35:1 |
| `text-muted` on `surface-well` | 5.45:1 | 6.94:1 |
| `text-muted` on `customer` | 5.36:1 | 6.33:1 |
| `text-muted` on `surface-selected` | 4.89:1 | 5.98:1 |
| `accent` on `surface` | 5.56:1 | 7.03:1 |
| `accent` on `surface-rail` | 5.14:1 | 7.30:1 |
| `accent` on `surface-well` | 5.09:1 | 6.07:1 |
| `accent` on `customer` | 5.01:1 | 5.53:1 |
| `accent` on `surface-selected` | 4.57:1 | 5.23:1 |
| `on-accent` on `accent` | 5.56:1 | 7.59:1 |
| `on-send` on `send` | 15.32:1 | 14.49:1 |
| `on-person` on `person` | 13.50:1 | 7.86:1 |
| `on-safety` on `safety` | 6.57:1 | 5.34:1 |

#### UI parts: edges, icons, focus rings, state fills (need 3:1)

| Pair | Light | Dark |
|---|---|---|
| `border-control` on `surface` | 3.88:1 | 4.52:1 |
| `border-control` on `surface-rail` | 3.58:1 | 4.70:1 |
| `border-control` on `surface-well` | 3.55:1 | 3.90:1 |
| `border-control` on `surface-selected` | 3.18:1 | 3.36:1 |
| `border-control` on `canvas` | 3.18:1 | 4.96:1 |
| `accent` on `surface` | 5.56:1 | 7.03:1 |
| `accent` on `surface-rail` | 5.14:1 | 7.30:1 |
| `accent` on `surface-well` | 5.09:1 | 6.07:1 |
| `accent` on `customer` | 5.01:1 | 5.53:1 |
| `accent` on `surface-selected` | 4.57:1 | 5.23:1 |
| `accent` on `canvas` | 4.57:1 | 7.72:1 |
| `focus` on `surface` | 5.56:1 | 7.03:1 |
| `focus` on `surface-rail` | 5.14:1 | 7.30:1 |
| `focus` on `customer` | 5.01:1 | 5.53:1 |
| `focus` on `surface-selected` | 4.57:1 | 5.23:1 |
| `on-safety` on `safety` | 6.57:1 | 5.34:1 |
| `send` on `surface` | 15.32:1 | 13.54:1 |
| `send` on `surface-well` | 14.02:1 | 11.69:1 |
| `person` on `surface` | 13.50:1 | 7.72:1 |
| `person` on `surface-rail` | 12.47:1 | 8.02:1 |
| `safety` on `surface` | 6.57:1 | 3.28:1 |
| `safety` on `canvas` | 5.40:1 | 3.61:1 |

- **`border-control`** is new in this file. The look sheet draws inputs and radios with the 1 px hairline (1.24:1),
  which fails WCAG 1.4.11 for a field boundary. One mid-grey, `#78838B`, holds ≥ 3:1 on every surface in both themes.
- **Where each edge applies:** `border-control` draws text fields (the composer, the code field, the live box), unchecked
  radio rings, the dashed edge of the customer's claims, and the selected queue row. Buttons and tiles are identified
  by their text and icon, so they keep the hairline (WCAG 1.4.11 does not require a boundary for a control identified
  by its label); their *selected* state is the 2 px `accent` edge (≥ 4.57:1) plus a check, never the hairline.
- **Selected queue row** is `surface-selected` plus a 1 px `border-control` edge plus the title already at weight 600:
  the fill alone is 1.13:1 against the rail, so the edge and the weight carry it.

#### Decorative lines and tints (not relied on alone; ratios shown for honesty)

| Pair | Light | Dark |
|---|---|---|
| `border-hair` on `surface` | 1.24:1 | 1.38:1 |
| `border-hair` on `canvas` | 1.02:1 | 1.52:1 |
| `customer-edge` on `customer` | 1.18:1 | 1.50:1 |
| `customer` on `surface` | 1.11:1 | 1.27:1 |
| `surface-well` on `surface` | 1.09:1 | 1.16:1 |
| `surface-rail` on `surface` | 1.08:1 | 1.04:1 |
| `surface-selected` on `surface-rail` | 1.13:1 | 1.40:1 |
| `canvas` on `surface` | 1.22:1 | 1.10:1 |

Nothing carries meaning by these alone. Card edges and row rules only separate; the mint tint is always paired with the
speaker name line, a check or a text label.

### 4.4 APCA second opinion on the dark palette

APCA (Lc) is a candidate standard, not an adopted one, so it never replaces §4.3. It is reported because WCAG 2's math
overstates near-black pairs (`ui-accessibility-and-semantics.md`). Target: Lc 75 for body text, 60 for secondary.

| Pair (dark) | Lc |
|---|---|
| `text` on `canvas` | 95 |
| `text` on `surface` | 94 |
| `text` on `surface-rail` | 95 |
| `text` on `surface-well` | 93 |
| `text` on `customer` | 91 |
| `text` on `surface-selected` | 90 |
| `text-muted` on `canvas` | 59 |
| `text-muted` on `surface` | 58 |
| `text-muted` on `surface-rail` | 58 |
| `text-muted` on `surface-well` | 56 |
| `text-muted` on `customer` | 55 |
| `text-muted` on `surface-selected` | 54 |
| `accent` on `surface` | 52 |
| `accent` on `surface-rail` | 53 |
| `accent` on `surface-well` | 51 |
| `accent` on `customer` | 49 |
| `accent` on `surface-selected` | 48 |
| `on-accent` on `accent` | 55 |
| `on-send` on `send` | 88 |
| `on-person` on `person` | 58 |
| `on-safety` on `safety` | 80 |

**Finding:** primary text (`text`, `on-send`, `on-safety`) is 80–95, good. **`text-muted` is 54–59 and `accent` as text is
48–53**, below the Lc 60 secondary floor, even though both pass WCAG at ≥ 5.23. The look sheet's values are kept here
because the sheet is the approved source. **Proposal for UX-5, not applied:** raise dark `text-muted` to `#BDC6CD`
(Lc 66–70, 7.5:1 or more everywhere) and dark `accent` text to `#3DDC97` (Lc 65–69). Both are lighter, less saturated
steps of the same hues, so nothing blooms.

### 4.5 Colour rules (profile §7)

1. **Red is the safety card's alone.** `--color-safety` may be read by the safety card (and its pinned phone copy, the
   "Call 911" button inside it) and by no other component. These do **not** use red: errors, overdue, P0 in the queue,
   limits, the demo bar, the banner, destructive actions, and focus. A lint rule at UX-4 fails the build if any other
   selector reads `--color-safety`.
2. **The demo bar and the staffing banner are neutral** (grey surfaces, muted text): no amber, yellow, orange or red; no
   warning triangle; no hatching; no pulsing. "Simulated" is a fact to state, not a hazard.
3. **Status is never colour alone.** Every state is a word plus an icon or a shape:
   - a tag always has its word; priority pairs the P-code with its word;
   - the customer's claims pair a dashed edge and a grey fill with the visible words "Customer says · not checked";
   - a changed value pairs a "Changed since" tag with weight 600 and a tail line.
4. **Emerald is the only accent.** It means **the one action, the selected thing, or the current tab**. It never fills a
   large area: the largest emerald fill is a card's primary button. Charcoal is the **Send** button only. Indigo is a
   representative's disc only.
5. **No hex in components.** Components read semantic or component tokens only.

### 4.6 Mint has one meaning (decision: resolves DESIGN-DIRECTIONS A5's "Mint means two things")

**The conflict.** On the phone, mint marks **the customer's turns** (dr-26). On the console the look sheet put mint on
the block "everything the assistant wrote" (dr-25's AI draft). The look sheet's assistant mark was also mint, so on the
phone itself the assistant's mark and the customer's turns shared a colour. Staff will move between the two surfaces,
and the customer's own words are exactly what a representative must tell apart from what the assistant said.

**Decision: mint means "the customer's own words and choices", everywhere, and nothing else.** The console's
assistant-written block is retinted to neutral; the assistant is grey.

| Where | Before (look sheet) | After (this file) |
|---|---|---|
| Phone: customer turns | mint | **mint** (unchanged) |
| Phone: assistant turns | grey well | **grey well** (unchanged) |
| Assistant mark (the small square beside "Meridian assistant") | mint with a mint edge | **grey well with a hairline edge and an emerald glyph**, so assistant = grey on every surface |
| Chosen tile, chosen option (the customer's choice) | mint + 2 px emerald edge | **mint + 2 px emerald edge** (unchanged: it is the customer's choice) |
| The "landed" wash on a card header the customer just settled | mint | **mint** (unchanged: it is the customer's fact) |
| Console: the promise shown to the customer | mint "AI draft" block with a glow | **a hairline card with a rail-tone header row**, the assistant mark and the words "Promise shown to the customer"; no glow |
| Console: the Conversation tab | — | the customer's turns are **mint**, the assistant's grey: the same as the phone |

**Why this answer and not the other.** The alternative was to keep mint for "assistant-written" on the console and
retint the phone's customer turns. That would have thrown away dr-26's clearest signal ("what I said / what they said")
on the surface a stressed homeowner uses, to keep a signal on the console that a text label does just as well. Also,
the promise is **policy-table text, not model text** (R-26), so tinting it as "AI-written" on the console would have
been inaccurate. The authorship cue moves to words and the mark: the brief header reads "Brief written by the assistant"
with the mark, and the promise card's header carries the mark and "Promise shown to the customer". What is lost: the
console no longer has one coloured block that says "machine wrote this". What is gained: mint is a rule a reviewer can
state in one sentence.

---

## 5. Spacing, grid, radii, hairlines, elevation

### 5.1 Spacing scale (4 px base, 2 px half-steps up to 14)

| Token | px | Token | px |
|---|---|---|---|
| `--space-0-5` | 2 | `--space-5` | 20 |
| `--space-1` | 4 | `--space-6` | 24 |
| `--space-1-5` | 6 | `--space-8` | 32 |
| `--space-2` | 8 | `--space-10` | 40 |
| `--space-2-5` | 10 | `--space-12` | 48 |
| `--space-3` | 12 | `--space-14` | 56 |
| `--space-3-5` | 14 | `--space-16` | 64 |
| `--space-4` | 16 | | |

Side gutters: 16 px on a phone, 24 px from 700 px. Card padding: 12 px (phone), 16 px (console). Element sizes (mark 24,
disc 18 / 32, control 44) are component tokens, not spacing.

### 5.2 Layout grid

| Surface | Grid | Widths |
|---|---|---|
| Chat < 900 px | one column: top bar, demo bar, banner, strip, thread, composer | thread max 62ch text, cards full width of the column |
| Chat ≥ 900 px | `minmax(0, 1fr) var(--panel-width)` inside the white frame, centred | `--panel-width` 340 px; frame max 1200 px; the thread column's content max 720 px, centred in its column |
| Console ≥ 1100 px | `var(--col-queue) minmax(0, 1fr) var(--col-evidence)`, each column scrolls on its own | `--col-queue` 280 px (the sheet's 270, widened for two-line rows at 14 px); `--col-evidence` 300 px (the sheet's 270, widened so the snapshot tables fit) |
| Console 700–1099 px | the queue becomes a drawer (§9.2); brief and evidence side by side | evidence 300 px |
| Console < 700 px | one column; queue drawer; brief and evidence become two tabs | — |
| Canvas | the page background is `--color-canvas`; the app frame sits on it with 16 px (phone: 0 on the sides) | no texture, no grid |

The console's column heads ("Waiting in chat" / the case header / "Evidence") share one baseline, so the left-to-right
read lines up (scanning check).

### 5.3 Radii

| Token | Value | Used for |
|---|---|---|
| `--radius-frame` | 24 px | The app frame; the phone frame in screenshots |
| `--radius-card` | 12 px | Cards, the composer, chat turns (with one 4 px corner), popovers |
| `--radius-control` | 8 px | Tiles, buttons, fields inside cards, the source chip, the split button, brief-index chips |
| `--radius-tag` | 6 px | Tags, the assistant mark |
| `--radius-tip` | 4 px | The one corner of a chat turn that points at its speaker |
| `--radius-sharp` | 0 | **The safety card only** |
| `--radius-round` | 50% | Discs, radio rings |

Buttons are never pills (A5 anatomy).

### 5.4 Hairlines and edges

| Token | Value | Used for |
|---|---|---|
| `--line-hair` | 1 px solid `--color-border-hair` | Card edges, header-row rules, rail and column rules, tabs rule |
| `--line-dash` | 1 px dashed `--color-border-hair` | Row separators inside a card; the *Now* column's left rule |
| `--line-control` | 1 px solid `--color-border-control` | Text fields, unchecked radio rings, the selected queue row |
| `--line-claim` | 1 px dashed `--color-border-control` | The customer's claims card |
| `--line-selected` | 2 px solid `--color-accent` | A chosen tile or option; the active tab's underline |
| `--line-emergency` | 2 px solid `--color-text` | The emergency-line card only |
| `--line-safety` | 4 px solid `--color-safety` | The safety card's closing rule |

### 5.5 Elevation

| Token | Light | Dark | Used for |
|---|---|---|---|
| `--elev-frame` | `0 0 0 1px var(--color-border-hair)` | same | The app frame on the canvas |
| `--elev-popover` | `0 8px 24px -12px rgb(16 18 22 / .28), 0 0 0 1px var(--color-border-hair)` | `0 0 0 1px var(--color-border-hair)` | The split-button menu, the one `<dialog>`; the only soft shadow in the product |

Everything else is flat: depth is **three surface steps** (canvas → rail → white) and the framed window. In dark,
elevation is **lighter surfaces, not shadows**: canvas `#0B0F12` → rail `#11161A` → surface `#151A1E` → well `#20272C`
→ selected `#2A3238`.

---

## 6. Motion

Motion is used for exactly two jobs: **show the next action** and **show where a fact landed**. Nothing else moves. All
motion is written as an opt-in under `@media (prefers-reduced-motion: no-preference)`; the default is calm.

| Token | Value |
|---|---|
| `--dur-control` | 150 ms (background and colour on buttons, rows, tabs, tiles) |
| `--dur-fade` | 200 ms (a new card or event line fades in) |
| `--dur-check` | 160 ms (the chosen tile's check draws; the strip's chevron turns) |
| `--dur-landed-in` / `--dur-landed-hold` / `--dur-landed-out` | 160 ms / 640 ms / 400 ms = **1.2 s** (the landed wash, matching the spec's 1.2 s) |
| `--delay-pending` | 300 ms (before "Meridian assistant is replying…" shows) |
| `--ease-enter` | `cubic-bezier(0, 0, .58, 1)` |
| `--ease-exit` | `cubic-bezier(.42, 0, 1, 1)` |
| `--ease-move` | `cubic-bezier(.42, 0, .58, 1)` |

| Moment | What moves | Why (which job) | Reduced motion |
|---|---|---|---|
| A card settles a fact (booking, handoff, identity) | The matching **panel card's header row** takes a mint wash: in 160 ms, held 640 ms, out 400 ms (`opacity` on a `::after` layer, `--color-customer` with a 1 px `--color-customer-edge` bottom edge). The thread card's header gets the same wash | Shows where the fact landed (CONCEPTS C2 "Linking") | **No wash.** The block already shows its new content and the change is announced in the polite region (SCREEN_SPECS) |
| A source chip is clicked (S2) | The evidence column scrolls to the source (`scroll-behavior: smooth`), then the source card's header row gets the same wash | Shows where the proof is | Instant scroll, no wash |
| The chosen tile or option | Its check icon draws in 160 ms (`stroke-dashoffset`: an SVG paint property, the one exception to "transform and opacity only", because it is one 14 px glyph) | Confirms the choice was received | Check appears at once |
| A new card or event line arrives | `opacity 0 → 1`, `--dur-fade`. **No slide** (dr-25: no sliding) | Leads the eye to the newest thing | Appears instantly |
| Strip opens or closes | The chevron turns 180° in `--dur-check`; the panel opens at once (a `<details>`) | Shows the state | No turn |
| Button, row, tab, tile state change | `background-color`, `color`, `border-color` over `--dur-control` | Confirms input was received | Instant |
| Pending line | **None.** "Meridian assistant is replying…" is static text; the ellipsis is the "…" character, never animated dots | Honest status without a typing indicator (A5 "do not carry over") | Same |

**Never:** bouncing, pulsing, spinners that spin forever, shimmering skeletons (skeletons are static `--color-surface-well`
blocks at the final height), attention loops on the safety card (it has **no motion at all**: it appears instantly),
typing indicators for the assistant, animated countdowns. Only `opacity`, `background-color`, `color`, `border-color`
and the one chevron `transform` animate; never `width`, `height`, `top`, `left` or `box-shadow`.

---

## 7. Dark theme (secondary)

- **Mechanics:** light tokens on `:root`; dark overrides under `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { … } }`
  and again under `:root[data-theme="dark"]`; `color-scheme: light dark`.
- **Base surface** `#0B0F12` (dark blue-grey, not black). **Elevation** steps lighter (§5.5). The look sheet's
  dark values are used as drawn; there is no dark Dribbble shot, so dark is a proposal from the sheet, not from a reference.
- **Accent:** the light theme's deepened emerald `#007847` becomes the shot's own `#00BC6F`, with near-black text
  (`#03140C`, 7.59:1). It is the brightest thing on a dark screen besides the safety card, so there is **one emerald
  fill per card** and no bloom.
- **Mint** becomes deep green `#0F3326` with a `#17513C` edge; `text` on it is 11.72:1.
- **Charcoal** inverts to a light chip (`#DDE3E8` / `#101216`): Send is still the one inverted-contrast button.
- **Indigo** lightens to `#A9A4F0` with dark text.
- **Safety red** lightens to `#C8312F`, so the band separates from the dark surface (3.28:1) while white text keeps 5.34:1.
- **Polish owed:** dark is checked by computed contrast, plus the APCA finding in §4.4, and no screenshots yet. UX-5's
  light/dark screenshot pass is where it is finished, including the §4.4 proposal.

---

## 8. Components

### 8.0 Component tokens (71)

Components read these, which read §4.2. No component reads a primitive or a hex.

| Token | Reads | Part |
|---|---|---|
| `--app-bg` | `--color-surface` | App frame and cards |
| `--app-frame-radius` | `--radius-frame` | App frame |
| `--rail-bg` | `--color-surface-rail` | Queue rail, strip, panel column |
| `--well-bg` | `--color-surface-well` | Pills, quotes, the composer's tile |
| `--turn-assistant-bg` | `--color-surface-well` | Assistant turn |
| `--turn-customer-bg` | `--color-customer` | Customer turn (mint) |
| `--turn-rep-bg` | `--color-surface` | Representative turn |
| `--turn-rep-edge` | `--color-border-hair` | Representative turn edge |
| `--mark-bg` | `--color-surface-well` | Assistant mark |
| `--mark-edge` | `--color-border-hair` | Assistant mark edge |
| `--mark-glyph` | `--color-accent` | Assistant mark glyph |
| `--disc-person-bg` | `--color-person` | Representative disc |
| `--disc-person-text` | `--color-on-person` | Initial on the disc |
| `--event-line` | `--color-border-hair` | System-event rules |
| `--event-text` | `--color-text-muted` | System-event text |
| `--chip-bg` | `--color-surface` | Source chip |
| `--chip-edge` | `--color-border-hair` | Source chip edge |
| `--card-bg` | `--color-surface` | Card |
| `--card-edge` | `--color-border-hair` | Card edge |
| `--card-head-bg` | `--color-surface-rail` | Card header row |
| `--tile-bg` | `--color-surface` | Window and option tile |
| `--tile-edge` | `--color-border-hair` | Tile edge |
| `--tile-selected-bg` | `--color-customer` | Chosen tile (the customer's choice) |
| `--tile-selected-edge` | `--color-accent` | Chosen tile edge (2 px) |
| `--tile-taken-bg` | `--color-surface-well` | Taken window |
| `--tile-taken-text` | `--color-text-muted` | Taken window text |
| `--radio-edge` | `--color-border-control` | Unchecked radio ring |
| `--radio-checked` | `--color-accent` | Checked radio fill |
| `--field-bg` | `--color-surface-well` | Text field |
| `--field-edge` | `--color-border-control` | Text field edge |
| `--field-focus-edge` | `--color-focus` | Focused field edge |
| `--field-invalid-edge` | `--color-text` | Invalid field edge (2 px, never red) |
| `--btn-primary-bg` | `--color-accent` | Primary button |
| `--btn-primary-text` | `--color-on-accent` | Primary button text |
| `--btn-primary-split-rule` | `--color-on-accent` at 35% | Split button divider |
| `--btn-secondary-bg` | `--color-surface` | Secondary button |
| `--btn-send-bg` | `--color-send` | Send button |
| `--btn-send-text` | `--color-on-send` | Send text |
| `--btn-ghost-text` | `--color-accent` | Text button |
| `--focus-ring` | `--color-focus` | Focus ring colour |
| `--focus-ring-on-safety` | `--color-on-safety` | Focus ring on the red |
| `--tag-bg` | `--color-surface-well` | Tag |
| `--tag-text` | `--color-text` | Tag text |
| `--tag-strong-bg` | `--color-surface-selected` | Strong tag fill |
| `--tag-strong-edge` | `--color-text` | Strong tag edge (1 px) |
| `--demo-bar-bg` | `--color-surface-well` | Demo bar |
| `--demo-bar-text` | `--color-text-muted` | Demo bar text |
| `--banner-bg` | `--color-surface-rail` | Staffing banner |
| `--strip-bg` | `--color-surface-rail` | Phone strip |
| `--strip-rule` | `--color-border-hair` | Strip rule |
| `--landed-wash` | `--color-customer` | The landed wash |
| `--landed-edge` | `--color-customer-edge` | Landed wash edge |
| `--qrow-selected-bg` | `--color-surface-selected` | Selected queue row |
| `--qrow-selected-edge` | `--color-border-control` | Selected queue row edge |
| `--claims-bg` | `--color-surface-well` | The customer's claims card |
| `--tab-underline` | `--color-accent` | Active tab underline |
| `--safety-band-bg` | `--color-safety` | Safety band |
| `--safety-band-text` | `--color-on-safety` | Safety band text |
| `--safety-bg` | `--color-surface` | Safety sheet |
| `--safety-btn-bg` | `--color-safety` | Call 911 button |
| `--safety-btn-text` | `--color-on-safety` | Call 911 text |
| `--dialog-bg` | `--color-surface` | The one dialog |
| `--target-min` | `44px` | Phone and coarse-pointer target |
| `--control-h-console` | `32px` | Console button, field |
| `--control-h-split` | `36px` | Console split primary |
| `--mark-size` | `24px` | Assistant mark |
| `--composer-min-h` | `72px` | Composer field |
| `--panel-width` | `340px` | C2 panel (≥ 900 px) |
| `--col-queue` | `280px` | Console queue column |
| `--col-evidence` | `300px` | Console evidence column |
| `--focus-ring-width` | `2px (offset 2px)` | Focus ring |

### 8.1 Frame, surfaces, top bar, icons

| Part | Construction | Traced to |
|---|---|---|
| **Canvas and frame** | The page is `--color-canvas`. The product is one `--app-bg` window with `--radius-frame` corners and `--elev-frame`. Inside: white content, a barely-grey rail (`--rail-bg`) for the queue or the strip, grey wells (`--well-bg`) for pills, the composer and assistant turns. Three steps: canvas → rail → white. On a phone the canvas shows only as the frame edge above and below | dr-25 (white app on `#E5E9F0`, rail `#F5F6F7`), dr-33, look sheet `.phone`, `.console`, `.app` |
| **Top bar** (chat) | White, 12 / 14 px padding, hairline bottom. A back button (30 px, `--well-bg`, 8 px), the assistant mark, then two lines: **Meridian Home Comfort** (`--text-name`) over "Automated assistant" (`--text-small`, muted). Once a case exists the second line adds "· Reference" and the mono reference. While a representative is in the chat the second line reads "Riley (demo representative). Assistant paused." (SCREEN_SPECS R1) | dr-26 (widget header with the bot mark), dr-25 ("#TC-192" in the header), look sheet `.topbar`, `TOP_REF` |
| **Assistant mark** | 24 px square, `--radius-tag`, `--mark-bg` (grey well) with a `--mark-edge` hairline and an `--mark-glyph` emerald ticket glyph. Never a face or a robot. Used in the top bar (30 px), name lines (18 px), card header rows that speak for the assistant (the promise card) | look sheet `MARK` (retinted, §4.6); dr-26 (purple robot not carried) |
| **Icons** | One set: 24-unit grid, 1.8 px rounded strokes, `currentColor`, 14–18 px; the look sheet's drawn set (back, headset, calendar, clock, ticket, copy, check, warning, doc, chevron) plus info-circle, phone, question-circle and quote from the same grid. Ink by default; emerald only inside card header rows and on the mark's glyph; **one icon per header row, tag or label row**. Never emoji, never a second set | dr-25, dr-27; look sheet `ico()` |
| **Tab** | 13 px; label `--color-text-muted`; the active tab is `--color-text` at weight 600 with a 2 px `--tab-underline` (emerald) bottom edge. Tabs are a real `role="tablist"` | dr-25 (Conversation · Task · Activity Logs, green underline), look sheet `.tabs`, `.tabs2` |

### 8.2 Primitives: buttons, fields, option tiles, tags, focus

**Buttons** (8 px corners, never pills; 44 px tall on a phone and for coarse pointers, 32 px on the console, the console's
split primary 36 px; at least 8 px between targets).

| Variant | Construction | Where | Traced to |
|---|---|---|---|
| **Primary** | `--btn-primary-bg` / `--btn-primary-text`, weight 600. **One per card or header** | "Continue with this window", "Verify", "Send the code", "Save my choice", "Try again", "Claim" | dr-25 ("Submit as Closed"), dr-32 (green primary under summary rows), look sheet `.pri` |
| **Split primary** (console) | A primary with a second segment (a chevron) after a 1 px `--btn-primary-split-rule`; the chevron opens a menu in `--elev-popover` | The case header ("Claim ▾") | dr-25 (split button), look sheet `.split` |
| **Secondary** | `--btn-secondary-bg` (white), 1 px hairline, `--color-text` | "Talk to a person" (composer tile and inside cards), "Show the checks", "Log a call", "Hand back to the assistant" | dr-32 (green primary beside a hairline secondary), look sheet `.opt` |
| **Send** | `--btn-send-bg` (charcoal) / `--btn-send-text`, 7 px 16 px padding. **The only charcoal button** | The composer, the live box | dr-25 ("Accept & Send"), dr-26 (Send), look sheet `.send` |
| **Text** | `--btn-ghost-text` (emerald), underline on hover and focus | "Open the demo inbox →", "Back to the chat", "Reload" | look sheet (links) |
| **Call 911** | The only red button: `--safety-btn-bg` / `--safety-btn-text`, 48 px, **square corners**; it lives inside the safety card only | Safety card | deliberately unlike dr-25 / dr-26; SCREEN_SPECS |

States for every variant: **default** · **hover** (pointer only; §4.2) · **focus-visible** (§ below) · **pressed**
(§4.2) · **loading** (the control keeps its width and is disabled against double-submit; its label changes after 300 ms,
e.g. "Signing in…", never a spinner) · **disabled** (§4.2, with the reason in words) · **success** (the card's done line).

**Focus ring** (all interactive elements): `outline: 2px solid var(--focus-ring); outline-offset: 2px`, never removed.
It is ≥ 4.57:1 on every surface (§4.3). On the safety card it is `--focus-ring-on-safety` (white, 6.57:1 on the red).
`scroll-padding-top` equals the sticky header's height so a focused item is never hidden (WCAG 2.4.11).

**Fields** (the composer, the code field, "Name on the account", "Phone", "ZIP code or city", the live box):
`--field-bg` (well) with a `--field-edge` 1 px control edge, `--radius-control` (the composer: `--radius-card`), a real
visible `<label>` (never placeholder-as-label), 44 px tall on a phone.

| State | Construction |
|---|---|
| default / hover | well fill, control edge; hover mixes the fill 8% toward `--color-text` |
| focus | the focus ring plus the edge turns `--field-focus-edge` |
| invalid | a 2 px `--field-invalid-edge` (ink) edge, a circle-i icon and the message under the field in `--text-small`, `aria-invalid="true"`, `aria-describedby`. **Never red** (§4.5). On blur, then live once shown |
| disabled | `--color-surface-well` with muted text and no edge; the reason is in the hint below |

**Option tiles and radios** (window tiles, follow-up options, "Yes" / "No" / "Not sure"): 8 px, 1 px hairline, white, 44 px
tall minimum. A native radio drives the follow-up chooser (a 14 px ring in `--radio-edge`, 1.5 px). **Chosen:**
`--tile-selected-bg` (mint), a 2 px `--tile-selected-edge` (emerald) edge, a check or a 4 px emerald ring-fill, weight 600.
**Taken:** `--tile-taken-bg`, `--tile-taken-text`, the time struck through at 1 px, and the word **Taken** in 12 px 600 (never
colour alone; disabled, not focusable).

**Tags** (6 px corners, filled, **never outlined pills**): `--tag-bg` (grey well), `--tag-text`, 13 px 600, an icon and a
word. **Strong tag** (for "Overdue", "Safety", "Changed since", P0 / P1): `--tag-strong-bg` plus a 1 px `--tag-strong-edge`
(ink) edge. Colour is never the whole signal: the strong tag adds an edge and its word and icon.

### 8.3 Message rows (the four speakers) and the pending lines

Every row has a **speaker name line**: the name in `--text-small` 600 ink, then " · " and the rest in muted, then the time.

| Row | Name line | Body | Traced to |
|---|---|---|---|
| **Assistant** | the 18 px mark, **Meridian assistant** · automated · 2:04 pm | `--turn-assistant-bg` (grey well), `--text-body`, `--radius-card` with a 4 px top-left tip, `margin-right: 36px`; may hold one card, then an "after" sentence, then source chips | dr-26 (grey bot bubbles), look sheet `.ai`, `.cap` |
| **Customer** | right-aligned, no mark: **You** · 2:03 pm | `--turn-customer-bg` (**mint**), `--text-body`, `--radius-card` with a 4 px top-right tip, `margin-left: 56px`. A reply sent from a card's button also says "You" | dr-26 (mint customer bubbles), look sheet `.me` |
| **Representative** | an 18 px `--disc-person-bg` indigo disc with the initial, **Riley** · representative (demo) · 2:20 pm | `--turn-rep-bg` (white) with a `--turn-rep-edge` hairline, `--text-body`, a 4 px top-left tip. White, so it is a third look, neither grey nor mint | dr-25 (indigo avatar disc), look sheet `.disc` |
| **System event** | no speaker name: the actor is in the sentence, the time at its end; screen readers get a hidden "System event" first | a centred line between two `--event-line` hairlines, `--text-small`, `--event-text` (muted), a small icon (joined, paused, handed back, closed, shift ended, demo reset). Example: "Riley (demo representative) has joined. · 2:20 pm" | dr-31 (centred event lines), dr-25 ("Sunday, 04 November"), look sheet (A5 anatomy) |

- On the console's **Conversation tab** the transcript is unbubbled (avatar, name line, text) as in dr-25, with the same
  speaker rules and the customer's text on mint.
- The thread is `role="log"` with `aria-live="polite"`; new rows are announced; the safety card is announced once (§8.6).
- **Source chip** (under an answer): a `<details>` whose summary is a `--chip-bg` 32 px chip, `--chip-edge` hairline,
  `--radius-control`, with a 44 px hit area (padding, not size). It holds a doc icon, "Source", the file in mono 12 px and
  the version date in muted 12 px. Open, the quoted passage shows below in a `--well-bg` block, 14 px. *Traced to:* dr-27
  (steps in a hairline card), dr-29 (a tinted block for the supporting text); the look sheet has no chip, so it is assembled
  from the card and tag constructions.

**The pending lines** (loading state of SCR-1; wording from SCREEN_SPECS). Both are one quiet row under the customer's
message: the 18 px mark, then the text in `--text-small` muted, **static**, no dots, no bubble.

| Moment | Row |
|---|---|
| After 300 ms with no reply | "Meridian assistant is replying…" |
| At about 10 s | the same row's text changes in place to "Still working on this…" (the height was reserved, so nothing jumps; announced once in a polite `role="status"`) |
| At 60 s (TURN_TIMEOUT) | the row is replaced by the TURN_TIMEOUT card (§8.4) |

Send is disabled until the reply arrives, the field stays editable, and **"Talk to a person" stays enabled** throughout.
*Traced to:* assembled from the name line and the event line; dr-26's "•••" typing bubble is deliberately not carried.

### 8.4 Cards in the thread

**Generic card** (every card below): `--card-bg`, `--card-edge` hairline, `--radius-card`, overflow hidden, 6 px margin
top and 4 px bottom. **Header row:** `--card-head-bg` (rail tone), hairline under it, 9 / 12 px padding, one emerald-ink
icon, the title in `--text-card-title`, and on the right a muted `--text-small` meta (a count, "this week", a reference
and a copy icon). Body: label-over-value rows split by `--line-dash`, values right-aligned, 600, tabular. One primary
button at the foot, full width. *Traced to:* dr-25 (popover header row), dr-28 (reference and status in the header),
look sheet `.card`, `.cardhead`, `.row`.

| Card | Anatomy | States | Traced to |
|---|---|---|---|
| **Slot card** | Header: calendar icon, "Choose a window", "this week" (or the zone, "South zone · Kyle"). **Day tabs** ("Mon 19 · Tue 20 · Wed 21 · Thu 22"; each tab's second line "2 open" or "Full"; the active one 600 with the emerald underline). **Window tiles** in two columns ("8:00 am – 12:00 pm"); members-only tiles carry a "Members" tag. A `--line-dash` row: "Diagnostic visit" · **$89** (hint: "What you pay if you're not a member"). **Continue with this window** (primary). Hint: "Windows are shown, not held." | loading (three tile-shaped static skeletons at the final height) · a day with no windows ("Full", the next open day named) · **stale** ("Sorry, that window just went. Here are the next open ones." and a fresh card) · chosen (the tile is mint with a 2 px emerald edge and a check; the card keeps its choice, the button is disabled once answered) | look sheet `PHONE_SLOTS`; dr-25 (popover), dr-26 (selected tile: green edge on mint), dr-32 |
| **Locate and code prompt** | Header: "Verify" with the hint "Prove it's your account"; right: "Before booking" / "Code sent". Stage 1: fields "Name on the account" and "Phone" (or one "Customer ID or invoice number"), **Send the code**, the demo hint. Stage 2: "Code sent to the phone on record, ending in 02", the code field (`--text-code`, `inputmode="numeric"`, `autocomplete="one-time-code"`), **Verify**, the text link "Open the demo inbox →", the hint "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries." | wrong ("That code doesn't match. 2 tries left." in the invalid-field style) · expired · locked (field disabled, then the handoff card) · verified (a done line with a check: "Verified for this chat") | assembled from the generic card and the field; dr-32 (green primary under the fields) |
| **Account card** | Header: doc icon, "Invoice INV-204411" (or "Membership", "Warranty"). The balance in `--text-time-hero` size, "Balance · unpaid · due Nov 1, 2026", a lines table (right-aligned tabular amounts, a 1 px ink rule above the total) | loading · unavailable | dr-28 (label-over-value rows, a totals block) |
| **Confirmation** (and *Your booked visit*) | Header: check icon, "Your visit", a "Booked" tag. The window in `--text-time-hero` ("8:00 am → 12:00 pm"), the sentence "Wednesday, October 21, 2026 · arrives between 8:00 am and 12:00 pm" (`--text-ui`, muted). Rows: Date · Technician · Fee that applies · Address. **"What happens next"** as a short checked list: Booked (done, with its time) → Technician arrives in the window (current) → Repair approved or declined at the visit; the free-change note. Foot: "Keep this", hint "Save or screenshot this" | booked · rebooked (a new card; the old one gets a done line "Moved to …") | dr-28 (header status word, rows), dr-27 (checked step list); look sheet `.row` |
| **Handoff card** ("Your request") | Header: ticket icon, **Your request**, the reference in `--text-ref` with a copy icon at the right (hint "Your reference number"). The promise as one `--text-lead` sentence, **word for word from the policy table**. Rows: **Due** · "Mon Oct 19 · 7:00 pm" (`--text-time-row`; hint "The latest we've promised to get back to you"); **Status** · a tag "Waiting for a representative" with a clock icon. Then the follow-up chooser (below) and **Save my choice**. **No countdown, no queue position.** For a safety-related case: no Due row (R-26) | nobody online · follow-up saved · refund variant · **safety: no due line** · pinned into the panel's *Your request* block as soon as it shows | look sheet `PHONE_HANDOFF`; dr-28, dr-29 ("Waiting for…") |
| **Follow-up chooser** | Legend (R-27): "We'll follow up by email unless you'd prefer a phone call." Two option tiles with native radios: **Email** · the address on your account; **Phone call** · the number ending in 02. Choosing phone reveals "Best time to call": Mornings · Afternoons · Any time. **Save my choice**, then the done line "Follow-up saved: phone call, the number ending in 02, mornings." Nothing says a message was sent | unsaved · saved | look sheet `.choices`; dr-26 (option tiles) |
| **Live-queued card** | Header: clock icon, "Your request", the reference. "A representative will join this chat when available. You can keep chatting with me while you wait, if you like." and a checked list: You asked for a person (done) → A representative joins this chat (current) → Back to the assistant, or the chat closes | queued · joined · handed back | dr-27 (checked list); assembled |
| **Change request** (fee-bearing change or cancel) | Header: ticket icon, "Change request", hint "Waiting for a representative to confirm", the reference. Rows: **Your visit stays** · the original window in `--text-time-due` and its date (the hero, because it is what will happen); **Requested** · the asked-for day and window, normal weight (not struck: it is unconfirmed, not cancelled); **Fee** · "The $49 fee applies under current policy." The promise line and its Due row. When the window starts before the promise could be met: R-26's sentence. **No primary button:** it is a receipt | one state per change or cancel wording | assembled from the handoff card and the account card's rows; dr-28; R-21, R-26 |
| **Limit notice** | A card with a circle-i icon, **no primary emerald** (neutral): one sentence saying what happened and what next ("I can't take more messages in this chat right now." / "I can't make more bookings in this chat."), and a **secondary** "Talk to a person". Never a triangle, amber or red | rate · booking cap · spend cap | assembled; FLOW-1 error branch, CON-2 error block |
| **TURN_TIMEOUT card** | Code-built reply under the assistant's name line. Header: clock icon, **This is taking longer than it should.** Two buttons: **Try again** (primary) and **Talk to a person** (secondary, headset icon). Neutral: no red, no triangle | shown at 60 s; "Try again" disables while it re-sends | assembled from the limit notice; SCREEN_SPECS loading, N-26 |
| **BUSY** | Code-built reply under the assistant's name line: one plain sentence and a secondary **Talk to a person**; no card header. Shown at once, no model call. **Wording is owned by the code's message table (CON-2 `BUSY`); the line here is a design placeholder:** "I'm busy with a lot of chats right now. Please try again in a moment, or a person can help." | one state | assembled from the assistant row and the secondary button; SCREEN_SPECS loading (above 30 turns in flight) |
| **Failure offer** | One line and a secondary "Talk to a person" | — | as BUSY |
| **Emergency-line card** (R-8) | A card with a **2 px `--line-emergency` ink edge** (heavier than every other card, so it reads as more urgent with no hue), a phone icon, "Because someone may be in danger…" and the number "(512) 555-0199 (demo number)" in `--text-title` as a `tel:` link with a 44 px target. Under a divider, only when nobody is online, the separate 1-business-day line. Not red | one state | assembled from the card; SCREEN_SPECS note 8 |
| **Question, quick checks, where card** | A card with Yes · No · Not sure (or Skip) option tiles; the quick-checks offer is a primary "Skip and book" beside a secondary "Show the checks"; the where card is one field and "Show windows" | answered (tiles disabled, the choice kept) | assembled from the generic card |

### 8.5 The C2 "What's settled" panel, block by block

At ≥ 900 px it is a right column (`--panel-width`, `--line-hair` on its left, `--rail-bg`). Below 900 px it is the strip
(§9.1). Each block is a generic card whose header row says the block title; each is a `<section>` named by its title.

| Block | Anatomy | States | Traced to |
|---|---|---|---|
| **Panel header** | "What's settled" (`--text-card-title`) with the hint "What's been confirmed so far" | — | dr-25 (rail section label), look sheet `.cap` |
| **Replying** (only while staffing is simulated) | Title "Replying" with the hint "Who is answering you now"; "The automated assistant" or "Riley (demo representative). Assistant paused." | assistant · representative | assembled |
| **Your visit** | Title "Your visit" (hint "Your booking"); the window in `--text-time-hero`, the date line in `--text-ui` muted ("Wed Oct 21"); rows Technician · Fee | empty ("Nothing booked yet.", dashed `--line-dash` card edge) · booked · **change pending** (adds "Original stays until a representative confirms.") | dr-28 (label-over-value), look sheet `.row` |
| **Your request** (asynchronous) | Title "Your request"; Reference (mono) with its hint; the promise sentence; "Due" in `--text-time-due`; "Follow-up" ("Phone · mornings" / "Not chosen yet") | empty ("No request open.") · open · follow-up saved · refund variant · **safety: no due time is ever shown** | dr-28, dr-29 |
| **Your request** (live) | "Waiting for a representative to join. No time is promised." / "A representative has joined this chat." | queued · joined · handed back | assembled |
| **Identity** | Title "Identity" with its hint; "Not checked. Only needed for private details." / "Code sent to the phone ending in 02" / "Verified for this chat · phone ending 02" | not checked · sent · verified · locked (→ handoff) | assembled |
| **Safety takeover** | The panel shows nothing else; the strip's line reads "DANGER · Leave the home immediately" (§8.6) | — | CONCEPTS C2 "Safety" |

**Landing:** when a card in the thread settles a fact, the matching block's header row takes the mint wash (§6) and
the fact is announced in a separate polite region.

### 8.6 Safety card

**What it does:** stops everything and tells the homeowner Meridian's instruction, in Meridian's words. It is **the only
red, the only square-cornered object, the only full-bleed block and the only thing outside the hairline-card
construction**, so it is unlike its neighbours in form, not only colour.

| Part | Spec |
|---|---|
| Sheet | Full width, `--radius-sharp` (0), `--safety-bg` (white), no hairline card, no tint. **Pinned** at the top of the chat column, outside the scrolling log, with content aligned to the thread's column |
| Band | A solid `--safety-band-bg` band, 10 / 16 px padding, holding a warning triangle icon (18 px, `--safety-band-text`) and **DANGER** in `--text-signal` (**WARNING** for the conditional card) |
| Actions | An ordered list in `--text-title` (20 px, 600, ink on white, 4 px between items). The words are **Meridian's KB instruction, verbatim**, changed only from "their" to "your" (SCREEN_SPECS R-5): **1** "Leave the home immediately and call 911 or your gas utility from outside." **2** "Don't flip switches, open windows near the furnace, or restart equipment." Fixed text owned by the code's safety table; this file fixes only how it looks |
| Call button | **Call 911 (from outside)**: the red 48 px square-cornered button, a `tel:911` link, full width of the content, white focus ring |
| Closing rule | A 4 px `--line-safety` rule under the card |
| Below it | One quiet line in `--text-small` muted on the page: "Once you're outside and safe, you can leave a number here if you'd like." No field, question or prompt invites typing; the composer stays enabled but focus does not move to it |
| Non-dismissible | No close control; pinned until the chat ends; nothing on it books, charges or asks. **No follow-up time anywhere on or under it** (R-6, R-26) |
| Strip | On a phone the strip stays and its one line reads **"DANGER · Leave the home immediately"** (warning icon and the word, in ink, not red: the card is the only red) |
| Panel | At ≥ 900 px the panel shows nothing else (§8.5) |
| Screen readers | `role="alert"` on the first render only, so it is announced once; the pinned copy is a `<section aria-label="Danger: safety instruction">`; it comes before the latest turn in the reading order |
| Motion | None, ever: it appears instantly |
| Conditional variant (R-7) | The same construction; signal word WARNING; the conditional instruction, then "Meridian's 24/7 emergency number is (512) 555-0199 (demo number)." |

*Traced to:* deliberately unlike dr-25 and dr-26; look sheet `PHONE_SAFETY` (band, numbered lines, 4 px rule; the sheet's
signal word is 15 px, raised to 18 px here, and its example lines are not the KB's, §13); REFERENCES R2; the ANSI Z535
signal-word convention (profile §7, S-180).

### 8.7 Chrome: demo bar, staffing banner, composer, the phone strip

| Part | Spec | Traced to |
|---|---|---|
| **Demo bar** | A centred 12 px strip, `--demo-bar-bg` (grey well), `--demo-bar-text` (muted): "Fri Oct 16, 2026 (demo date) · Nobody online" (or "Simulated staff on shift (demo)"). Plus a "Demo guide" text link in the top bar. **Neutral:** no icon, no amber, no motion | dr-25 (system line on `#F3F5F7`), look sheet `.demo` |
| **Staffing banner** (while the simulation is on) | A full-width row under the demo bar, `--banner-bg` (rail), a `--line-dash` bottom rule, a circle-i icon (not a triangle) and `--text-small` 500: "Simulated staffing (demo). No Meridian employee is online." When a demo action applies, a small secondary button ("Demo: Riley claims the case and joins") | assembled; dr-29 (a quiet tinted line) |
| **Composer** | A docked bar on white with a hairline top. "Talk to a person" (a secondary tile with a headset icon, **always present, always in the same place**: WCAG 3.2.6) above a `--field-bg` field ("Type a message", 72 px minimum, `--radius-card`) with the charcoal **Send** at its lower right. Hint line (limit or paused notices) in `--text-small` muted. After a reset or close: disabled with "This chat has ended." and a primary "Start a new chat" | dr-26 (option tile, grey composer, charcoal Send), look sheet `.dock`, `.opt`, `.composer` |
| **Phone strip** (C2, < 900 px) | A `<details>` directly under the top bar and banner. Summary: min 44 px, `--strip-bg` (rail), `--strip-rule` hairline under it, "What's settled" in 13 px 600 then the settled facts in 13 px tabular ("Wed Oct 21 · 8:00 am – 12:00 pm", "MHC-C-0007 · due Mon 7:00 pm", or "Nothing yet") and a chevron. Open: the panel blocks, scrolling inside `max-height: 52vh` | assembled; dr-34 (phone thread), SCREEN_SPECS R4 |

### 8.8 The console: header, queue rows, priority tags

**Console header** (every staff screen): "Meridian · Staff console", the role ("Riley · demo representative") with the
indigo disc, the demo date and time, the staffing word, the staffing banner when on, the nav ("Queue · Review list") as
tabs, and a sign-out text button. Neutral demo items as in §8.7. *Traced to:* dr-25 (top rail), dr-33.

**Queue rail:** `--rail-bg`, hairline on its right; the role's indigo disc and name at the top; then section labels in
`--text-section` ("Waiting in chat" with a count, "Needs my action" with a count) and the hint "Safety and danger first, then
by due time." with "J / K to move, Enter to open" (laptops only, `<kbd>` styled as a muted 12 px tag).

| Part | Construction | Traced to |
|---|---|---|
| **Row** | A `<button>` in a `<ul>`, `--radius-control`, 9 / 8 px padding, min 44 px high, grid `1fr auto`. **Line 1:** the reason in 600 + the priority tag at the right. **Line 2:** `--text-time-meta` muted: "Omar Patel · `MHC-C-0007` · Due Mon 7:00 pm" (the reference in `--text-ref`). **Line 3 (when it applies):** owner ("Unowned" or a name) · follow-up short form ("Phone · mornings") · tags ("Demo seed", "Brief being written", "Waiting · wakes Tue 9:00 am") | dr-33 (inbox rows with a meta line), dr-25 (rail rows), look sheet `.qrow` |
| **Selected** | `--qrow-selected-bg` + a 1 px `--qrow-selected-edge`; `aria-current="true"` | dr-25 (selected nav row), look sheet `.qrow.sel` |
| **Hover / focus** | Hover mixes 8% toward ink (pointer only); focus ring | — |
| **Overdue** | A strong tag "Overdue" with a clock icon replaces the plain due text's tag; a **word, never red, never a negative countdown** | dr-25, look sheet `Overdue` tag |
| **States** | empty (the cleared kind): "You're all caught up. No case needs your action. New handoffs from the chat appear here." · loading: five row-shaped static skeletons · error: "The queue didn't load. Try again." with a secondary button · stale: the polite line "2 cases changed. Show them." | — |

**Priority tags P0–P4** (6 px, filled, word always beside the code; the word is the spec's):

| Tag | Fill | Icon | Text |
|---|---|---|---|
| **P0** | strong (`--tag-strong-*`: grey fill + ink edge) | warning triangle, in ink | "P0 · Safety" (a P0 row shows "No due time: safety" in place of a due) |
| **P1** | strong | warning triangle, in ink | "P1 · Danger" |
| **P2** | plain (`--tag-bg`) | — | "P2 · Time-sensitive" |
| **P3** | plain | — | "P3 · Standard" |
| **P4** | plain | — | "P4 · Routine" |

Two fill levels plus the word: the edge tells high (P0 / P1, above everything in every queue) from the rest at a squint;
the code and word carry the exact level. **Not red, ever** (§4.5). *Traced to:* look sheet (`Safety` with a warning icon in ink,
`P3 Standard`), dr-25 ("Auto Reply" chip: a grey filled chip with an icon).

### 8.9 The case: header, state line, promise, eight headings

**Case header** (centre column top): row 1: `MHC-C-0007` in `--text-ref`, the reason pill ("Billing dispute · P3 Standard",
`--well-bg`, 6 px, weight 500), and at the right the **split primary** (§8.2). Row 2: the due in `--text-time-due`
("Due Mon Oct 19 · 7:00 pm", or "No due time: safety"), the Overdue strong tag when past, and a meta line in `--text-small`
muted: "Created Fri Oct 16, 2:14 pm · Unassigned, nobody owns it yet" and a "Demo seed" tag when it is one.
*Traced to:* look sheet `.bar`, `.titlepill`, `.split`; dr-25 ("#TC-192" with a title pill), dr-28.

- **Split primary:** while Unassigned it reads **Claim** (Claim and join when live-queued); once claimed its main
  segment is **Resolve** (an outcome is required, so it opens the inline form); its menu holds Release, Set waiting and
  Close unresolved (each needs its reason or time, as SCREEN_SPECS says). Disabled menu items carry the reason as their
  description ("Claim the case first."). While a chat is live there is no emerald primary: Send (charcoal) in the live
  box is the one action. *Placement, not behaviour:* the rest (Log a call, Log an email, Flag; Assign and Change
  priority for a supervisor) are secondary buttons in the action area under the brief.
- **State line** (the lifecycle): the words Unassigned → Claimed → In progress → Waiting → Resolved / Closed
  unresolved (Live-queued first on the staffed path) in a hairline row separated by chevrons. The **current** state is a
  strong tag; done states carry a check and muted text; upcoming states are muted. Case state over time is the dated
  activity log below, not a stepper (DESIGN-DIRECTIONS A5 "Navigation / steps").
- **Tabs:** the centre column is the brief alone. The conversation lives in the **evidence column's** tabs, "Sources (n) ·
  Conversation" (S2), with the emerald underline on the active one.
- **Promise card:** the generic card; header row: the assistant mark, "Promise shown to the customer"; body: the exact
  promise text in `--text-lead`; rows Follow up by · Destination (on record / not on record) · Best time; a promise-status
  tag (Open · Kept · Missed · Changed, plus "Shift ended before a claim" as the reason on Changed). **Not mint** (§4.6).
  *Traced to:* look sheet `.draft` (retinted), dr-29.

**Brief header line:** "Brief written by the assistant" (a copy proposal; the mark plus the words carry the authorship
cue that mint no longer does, §4.6) with the mark and the time, `--text-small` muted; while it is pending: "The brief is being written. The conversation is complete."

**The brief index:** a sticky row of eight 32 px control chips "1"…"8" (44 px on a phone), each with the section name as its
accessible name; activating one scrolls to and focuses that section.

**The eight headings** (fixed order, SCREEN_SPECS and consolidated §5): each is a generic card; the header row holds a
numeral tag (13 px 600, tabular, `--well-bg`) and the heading in `--text-card-title`. **Empty headings say "Nothing recorded."**

| # | Heading | Kind | Construction |
|---|---|---|---|
| 1 | Why this came to you | fact | solid card edge; label-over-value rows; each fact ends in a **source chip** (§8.10) |
| 2 | What the customer needs | quote | the customer's need in quotation marks, 600, with a quote icon |
| 3 | What we know for sure | fact | as 1 |
| 4 | What the customer says (not checked) | **claim** | the **claims card** (below) |
| 5 | What the AI did | plain | plain items |
| 6 | What we told the customer | quote | the same promise text the customer saw, in quotation marks, 600; no tint |
| 7 | What you need to decide | decide | each item led by a question-circle icon |
| 8 | Who they are and how to reach them | plain | identity status in words ("Verified · phone ending 02"), contact, window |

**Facts versus claims differ in four ways at once**, so any one survives greyscale, colour-blindness and a screen reader:

1. **Edge:** facts have a solid 1 px hairline card; claims have a **dashed** 1 px `--line-claim` edge (3:1).
2. **Fill:** facts are white; claims sit on a `--claims-bg` grey well.
3. **Words:** claims carry a strong tag with a circle-question icon and the visible words **"Customer says · not checked"**
   (the spec's "Not checked" label); facts carry none.
4. **Proof:** every fact ends in a source chip; a claim has **none**.

A heading the fact check trimmed (US-19) carries a circle-i icon and the spec's sentence under its header: "Something here
didn't match the record and was removed." *Traced to:* dr-29 (a block marked not visible to the customer; staff-only tint),
dr-33 (right-aligned profile facts), look sheet `.claims`, `.sec`.

### 8.10 Sources: "What the AI saw" and "Now"

- **Source chip** (in the brief, at the end of a fact): 28 px, `--radius-control`, `--chip-bg`, hairline, a doc icon and the
  short name ("policy: escalation_and_safety.md"), the icon and name in `--color-accent`. Activating it scrolls the
  evidence column to that source and gives its header row the landed wash (§6). On a phone it switches to the Evidence
  tab first.
- **Evidence column head:** "Evidence" in `--text-section` and the line "What the AI saw, next to what is true now" in
  `--text-small` muted.
- **Source card** (the generic card): header row: doc icon and the title; under it the meta line in mono 12 px muted (the
  file or record, "Snapshot read Fri Oct 16, 2:10 pm").
  - **Record sources** get a table with a visually hidden `<caption>` and `th scope`: columns *(field)* ·
    **What the AI saw · 2:10 pm** · **Now · 2:20 pm**. The *Now* column sits behind a `--line-dash` left rule. Money and
    times are tabular and right-aligned.
  - **KB sources** get a blockquote of the passage on `--well-bg`, then a "Fact the brief drew from it" row.
  - **Tail** (under a `--line-dash`): a check icon and "No change since the snapshot." or a circle-i icon and "Changed since
    the AI saw it: was $144.00, now $149.00" at weight 600.
- **Changed since:** in a changed row the *Now* cell shows the new value at **600** beside a strong tag "Changed since"
  (circle-i icon). The *What the AI saw* cell keeps the old value at normal weight and is **not struck through** (it is
  what the AI actually saw). The word, the tag edge, the weight and the tail icon carry the change; colour carries none.
- **States:** loading (a static skeleton card at the final height) · source missing ("This record can't be read right now;
  the snapshot is shown alone.") · error with a retry button.

*Traced to:* look sheet `CONSOLE` ("What the AI saw · 2:10 pm" / "Now · 2:20 pm", "No change since the snapshot."), dr-28,
dr-29.

### 8.11 Actions area, live box, and the demo pages

| Part | Spec | Traced to |
|---|---|---|
| **Action area** (under the brief) | A hairline card: secondary buttons for the state (Log a call, Log an email, Flag; supervisors: Assign, Change priority); a disabled button explains why in a hint line; **mini-forms** open inline in a `--well-bg` block with native radios and selects and one primary. Activity log: `--text-ui`, a 56 px time column in 12-hour times ("2:20 pm"), "Demo: recorded, not sent" on every contact | dr-25 (Task and Activity Logs tabs), dr-27 |
| **Live box** (Conversation tab, once joined) | A hairline card with the head row "You are replying as Riley (demo representative). The assistant is paused.", the field, the charcoal **Send**, secondary **Hand back to the assistant** and **Close the chat**. Disabled after hand-back or close | dr-25 (composer header and "Accept & Send"); assembled |
| **Demo inbox message** (SCR-2) | A card, header row "To ···02 · Fri 2:07 pm", the message text, the code in `--text-code`, a status tag (Active · Used · Expired), a secondary **Copy code** (disabled on Used and Expired with the status word as the reason) and the "Copied" confirmation for 2 s | assembled from the card and the code field |
| **Role buttons** (SCR-4) | Three full-width cards that are `<button>`s: title (`--text-card-title`) over a one-line description; one primary is **not** used (all three are equals); the chosen one shows "Signing in…" and the others disable | assembled |
| **Lanes, tables, numbers** (SCR-7…SCR-11) | A lane is a card with a header row holding the title and a count tag; rows follow §8.8. Tables use `th scope` and tabular figures; a null reads with its reason (N-23); headline numbers use `--text-figure` | dr-30 (white cards on a pale canvas, one green action), dr-33 |

---

## 9. Responsive rules

### 9.1 Customer chat (C2)

| Width | Behaviour |
|---|---|
| **< 700 px (phone)** | One column. The strip is under the top bar, **collapsed by default**. The composer stacks: "Talk to a person" tile, then the field with Send, then the hint. All targets ≥ 44 px. The frame has no side margin |
| **700–899 px** | Still one column; the strip is under the top bar; the composer on one row for the tile and the field |
| **≥ 900 px** | Two columns inside the white frame: thread \| panel (`--panel-width` 340 px), max 1200 px, centred. The panel is always open |
| **Safety** | The card pins at the top of the thread; the strip's line becomes "DANGER · Leave the home immediately" (§8.6) |

Inside cards, container queries (not media queries) decide: a card under 300 px content width drops the hero time to 24
px; under 420 px the locate fields go to one column; from 520 px the day tabs may show a full week.

### 9.2 Staff console (S2)

| Width | Behaviour |
|---|---|
| **≥ 1100 px** | Three columns `--col-queue` \| case \| `--col-evidence`, each scrolling on its own; the queue is always open |
| **700–1099 px: the queue drawer** | The queue becomes a `<details>` drawer across the top: a 44 px summary row on `--rail-bg` reading "Queue · 4 cases"; it opens over the brief's top. Below it: case \| evidence (300 px) |
| **< 700 px** | One column: the queue drawer, then the case. **Evidence becomes a tab beside the brief** ("Brief · Evidence"); a source chip switches to the Evidence tab first. Buttons are ≥ 44 px |

Everything works at 320 px without horizontal page scroll; only the snapshot tables scroll inside their own container.

---

## 10. Copy tone for states

- **Voice:** a competent service desk on the customer's side. Short sentences, lead with the one thing to know or do,
  numbers in plain digits, sentence case everywhere.
- **Empty:** says what goes there and that it fills on its own ("Nothing booked yet."). In the staff queue, the cleared
  kind: "You're all caught up."
- **Errors:** what happened, why, what to do, in one sentence, next to the field ("That code doesn't match. 2 tries
  left."). Never "Something went wrong"; never red.
- **Success:** quiet. A done line in the past tense with a check; the landed wash; no green banners.
- **Promises:** only the policy table's text, word for word; never a countdown, a queue position or a wait estimate.
- **Demo:** factual and calm: "Simulated", "(demo)", "Demo: recorded, not sent".

## 11. Do / Don't (project rules; they override the general `ui-*` defaults where they differ)

**Do**
- Put a **speaker name line** on every message.
- Keep **mint for the customer's own words and choices**, and nothing else.
- Use **one emerald button per card or header**, and the charcoal button for Send only.
- Use `<time>` with an ISO `datetime` for every time, shown in 12-hour form with minutes.
- Keep the safety card plain, red, square, verbatim and pinned.
- Show status as word + icon; show facts and claims four ways apart.
- Read semantic tokens only.

**Don't**
- Use red, orange or amber anywhere but the safety card, including errors, overdue, P0 or the demo surfaces.
- Uppercase a time or a date; show 24-hour times; show a countdown or "in 3 days".
- Add a typing indicator, animated dots, a confidence meter or "thinking" time for the assistant.
- Use mono caps labels, a coloured left border, an outlined pill, or a card grid of identical tiles.
- Tint a console block mint to mean "the assistant wrote this".
- Animate anything that isn't the next action or a fact landing; animate `box-shadow`, width or position.
- Put two emerald primaries in one card or header.

---

## 12. House-texture check on the final spec (`ux-pipeline` phases.md, 7 traits)

| # | Trait | Verdict | Why |
|---|---|---|---|
| 1 | Cream or beige canvas with a serif heading | **No** | A cool blue-grey canvas `#E5E9F0`; Instrument Sans and Inter; no serif anywhere |
| 2 | Coloured left-border cards, thin grey outlines, identical 10–12 px radii in an even grid | **Watch** | Cards do have 1 px hairline outlines and 12 px radii: that is the construction this direction borrows from dr-25. Mitigations: tinted header rows, mixed radii (24 / 12 / 8 / 6 / 4 / 0), a dashed edge for claims, a 2 px ink edge for the emergency card, and **no coloured left borders**. Cards stack in a thread and a three-column layout, not an even grid. The new `border-control` edges make fields heavier than the sheet; they are fields, not cards |
| 3 | Outlined pill status badges on everything | **No** | Tags are filled 6 px rectangles with an icon and a word; the strong tag's thin ink edge is a rectangle, not a pill, and appears only on P0 / P1, Overdue, Changed since |
| 4 | Muted sage, teal or forest as the only accent | **Watch** | The accent is emerald, hue 156°, **saturation 100%**, so it is not a muted sage. But the light theme's `#007847` is lightness 24%, a deep green that can read as forest. Mitigations: mint as a *surface*, charcoal as the second action, indigo and the safety red as distinct hues, and the dark theme's bright `#00BC6F`. Judge `#007847` on the look sheet |
| 5 | System-ui or one safe sans, no display face | **No** | Instrument Sans carries every headline role (names, card titles, the promise, the safety lines, big times) beside Inter and Geist Mono. (The proposal had this as a watch because Inter alone would match; the final spec uses the display face throughout.) |
| 6 | Flat: no texture, depth, imagery or motion | **No** | Depth comes from the framed canvas and three surface steps; motion marks where a fact landed. There is no texture or imagery, so the signature has to come from the construction. The look sheet's mint glow is gone with the retinted console block (§4.6) |
| 7 | The previous project's skeleton, recoloured | **Watch** | C2 (chat + panel) and S2 (queue · case · evidence) come from the concepts, not the direction. They resemble generic help desks and Riverside's three columns (DESIGN-DIRECTIONS review notes). The framed canvas, mint/grey turn split, tinted header rows and the facts-versus-claims construction differ; the skeleton is shared |

**Result: 0 matches, 3 watches (traits 2, 4, 7) → passes** (the rule rejects more than 2 *matches*). The proposal had 4
watches (2, 4, 5, 7); trait 5 is now a clear no. Traits 2 and 4 are the price of matching the shot he chose.

---

## 13. What differs from the approved look sheet

Colours are copied exactly (§4). These are the deliberate differences, each with its reason.

| # | Sheet | This file | Why |
|---|---|---|---|
| 1 | Assistant mark is mint; the console's promise block is a mint "AI draft" with a glow | Mark is grey well with an emerald glyph; the promise is a hairline card; no glow | One meaning for mint (§4.6) |
| 2 | Field, radio and composer edges are the 1.24:1 hairline | New `border-control` `#78838B` (≥ 3.18:1) on fields, radios, claims and the selected row | WCAG 1.4.11 (§4.3) |
| 3 | The DANGER band's text is 15 px | `--text-signal` 18 px | A safety word should outweigh body text; construction unchanged |
| 4 | Safety lines in the mockup: "Leave the home immediately." / "Call 911 or your gas utility from outside." / "Don't flip any light switches…" | The KB words in SCREEN_SPECS (two numbered lines) | The sheet's copy is mockup text, not Meridian's (§14, item 1) |
| 5 | 12.5 / 13.5 / 16 / 17 px sizes | Normalised to 13 / 14 / 16 (name) / 18 (lead) | A scale with named steps (§3.2) |
| 6 | Name lines at 12 px | 13 px | A stressed homeowner reads the speaker first |
| 7 | Queue rows end "Due Mon 7:00 pm, in 3 days"; section labels "Needs attention first" / "By due time" | No "in 3 days"; the spec's "Waiting in chat" / "Needs my action" | No countdown (R-26); the spec's copy wins |
| 8 | Times "Mon Oct 19, 7:00 pm", "12:00 – 4:00 pm" | `Mon Oct 19 · 7:00 pm`, "12:00 pm – 4:00 pm" | SCREEN_SPECS copy rules |
| 9 | Composer radius 10, frame 28 (the phone mockup), console 20 | 12 and 24 | A5 anatomy (24 / 12 / 8) |
| 10 | Rail 270, evidence 270 | 280 and 300 | Two-line rows at 14 px; snapshot tables need room |
| 11 | Hover, pressed and loading states not drawn | Derived (§4.2, §8.2) | UI-11 |
| 12 | The console mockup has "Brief · Conversation" tabs in the centre column | The centre is the brief alone; the conversation is a tab in the evidence column beside Sources | S2 as the concepts and SCREEN_SPECS define it |

---

## 14. Upstream issues found (not edited here; owners should fix)

1. **Safety wording in the look sheet.** `build_a5_look.py`'s `PHONE_SAFETY` uses three lines that are not Meridian's words
   (see §13, row 4). Nothing downstream reads it, but anyone copying from the sheet to the prototype would paraphrase the KB.
2. **DESIGN-DIRECTIONS A5's closing "Wireframe impact" line** ("If A5 is chosen, UX-3 swaps the A2 conventions in
   `SCREEN_SPECS.md` … for sentence-case labels") is now done; it can be marked resolved. Its anatomy row "Brief layout"
   also still shows "Brief · Conversation" tabs in the centre, which S2 puts in the evidence column (§13, row 12).
3. **A5's "Mint means two things" risk** in DESIGN-DIRECTIONS is resolved by §4.6; the A5 anatomy rows "Brief layout" and
   "Component anatomy → Canvas" still describe the mint "AI-written" block and should note the retint.
4. **dr-25's "Thought for 2s"** appears in DESIGN-DIRECTIONS only as a do-not-carry-over; confirm nothing in the prototype
   brief reintroduces it.
5. **Formatting is the frontend's job.** Contracts must carry ISO datetimes, not display strings, or the 12-hour rule
   (§3.4) cannot be enforced; `UI_CONTRACTS.md` (written in parallel) should say so.
6. **BUSY wording** is a placeholder here (§8.4); the code's message table (CON-2 `BUSY`) must own the string.
7. **Placement of case actions** (§8.9: the split primary and the action area) is a layout decision made here to give the
   case one emerald primary; SCREEN_SPECS' list of which buttons exist per state is unchanged.
8. **Dark APCA proposal** (§4.4) is open for UX-5.

---

## Appendix: the contrast script

Save as `contrast.py` and run `python3 -I contrast.py` (add `--md` for table rows). It exits 1 on any failing pair.

```python
#!/usr/bin/env python3
"""A5 design.md contrast check. Run: python3 -I contrast.py [--md]
Primitives -> semantic -> component tokens, WCAG 2.x ratios for every text pair (>= 4.5) and
UI edge (>= 3.0), both themes, plus APCA as a second opinion on dark. Exits 1 on any failure."""
import sys

PRIM = {  # raw values; nothing but this tier holds a hex
    "cool-0": "#FFFFFF", "cool-25": "#F5F6F7", "cool-50": "#F3F5F7", "cool-100": "#E5E9F0", "cool-150": "#E3E7EB",
    "cool-600": "#5B656D", "cool-800": "#202629", "cool-900": "#101216",
    "night-950": "#0B0F12", "night-900": "#11161A", "night-850": "#151A1E", "night-800": "#20272C",
    "night-700": "#2A3238", "night-650": "#2C343A", "night-300": "#A7B1B9", "night-200": "#DDE3E8", "night-100": "#E9EDF0",
    "mid-500": "#78838B",
    "emerald-50": "#E2F8EF", "emerald-100": "#B4EDD5", "emerald-500": "#00BC6F", "emerald-700": "#007847",
    "emerald-800": "#17513C", "emerald-900": "#0F3326", "emerald-950": "#03140C",
    "indigo-300": "#A9A4F0", "indigo-900": "#2A2663", "indigo-950": "#14123A",
    "red-600": "#C8312F", "red-700": "#B42318",
}
SEM = {  # semantic token -> (light primitive, dark primitive)
    "canvas": ("cool-100", "night-950"), "surface": ("cool-0", "night-850"), "surface-rail": ("cool-25", "night-900"),
    "surface-well": ("cool-50", "night-800"), "surface-selected": ("cool-100", "night-700"),
    "border-hair": ("cool-150", "night-650"), "border-control": ("mid-500", "mid-500"),
    "customer": ("emerald-50", "emerald-900"), "customer-edge": ("emerald-100", "emerald-800"),
    "text": ("cool-900", "night-100"), "text-muted": ("cool-600", "night-300"),
    "accent": ("emerald-700", "emerald-500"), "on-accent": ("cool-0", "emerald-950"), "focus": ("emerald-700", "emerald-500"),
    "send": ("cool-800", "night-200"), "on-send": ("cool-0", "cool-900"),
    "person": ("indigo-900", "indigo-300"), "on-person": ("cool-0", "indigo-950"),
    "safety": ("red-700", "red-600"), "on-safety": ("cool-0", "cool-0"),
}
TEXT = [  # (foreground, background): all need >= 4.5
    ("text", "canvas"), ("text", "surface"), ("text", "surface-rail"), ("text", "surface-well"), ("text", "customer"),
    ("text", "surface-selected"),
    ("text-muted", "canvas"), ("text-muted", "surface"), ("text-muted", "surface-rail"), ("text-muted", "surface-well"),
    ("text-muted", "customer"), ("text-muted", "surface-selected"),
    ("accent", "surface"), ("accent", "surface-rail"), ("accent", "surface-well"), ("accent", "customer"),
    ("accent", "surface-selected"),
    ("on-accent", "accent"), ("on-send", "send"), ("on-person", "person"), ("on-safety", "safety"),
]
UI = [  # edges, icons, focus rings, fills that mark state: all need >= 3.0 against what they touch
    ("border-control", "surface"), ("border-control", "surface-rail"), ("border-control", "surface-well"),
    ("border-control", "surface-selected"), ("border-control", "canvas"),
    ("accent", "surface"), ("accent", "surface-rail"), ("accent", "surface-well"), ("accent", "customer"),
    ("accent", "surface-selected"), ("accent", "canvas"),
    ("focus", "surface"), ("focus", "surface-rail"), ("focus", "customer"), ("focus", "surface-selected"),
    ("on-safety", "safety"),
    ("send", "surface"), ("send", "surface-well"),
    ("person", "surface"), ("person", "surface-rail"),
    ("safety", "surface"), ("safety", "canvas"),
]
DECOR = [  # never relied on alone; ratios shown for honesty
    ("border-hair", "surface"), ("border-hair", "canvas"), ("customer-edge", "customer"), ("customer", "surface"),
    ("surface-well", "surface"), ("surface-rail", "surface"), ("surface-selected", "surface-rail"), ("canvas", "surface"),
]

def lum(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)

def ratio(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + .05) / (y + .05)

def apca(txt, bg):  # APCA-W3 0.0.98G-4g, Lc; informational second opinion on dark only
    def y(h):
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
        v = .2126729 * r ** 2.4 + .7151522 * g ** 2.4 + .072175 * b ** 2.4
        return v if v >= .022 else v + (.022 - v) ** 1.414
    yt, yb = y(txt), y(bg)
    if yb > yt:
        s = (yb ** .56 - yt ** .57) * 1.14
        return 0 if s < .1 else (s - .027) * 100
    s = (yb ** .65 - yt ** .62) * 1.14
    return 0 if s > -.1 else (s + .027) * 100

def hexof(theme, name):
    return PRIM[SEM[name][0 if theme == "light" else 1]]

def run(md=False):
    fails, low = [], {}
    for theme in ("light", "dark"):
        rows = []
        for kind, pairs, need in (("text", TEXT, 4.5), ("ui", UI, 3.0), ("decor", DECOR, None)):
            for fg, bg in pairs:
                r = ratio(hexof(theme, fg), hexof(theme, bg))
                ok = "pass" if need is None else ("pass" if r >= need else "FAIL")
                if ok == "FAIL":
                    fails.append((theme, fg, bg, round(r, 2)))
                if need:
                    low.setdefault((theme, kind), []).append((r, fg, bg))
                rows.append((kind, fg, bg, r, need, ok))
        print(f"\n## {theme}")
        for kind, fg, bg, r, need, ok in rows:
            note = "decorative" if need is None else f">= {need}"
            line = f"{kind:5} {fg:16} on {bg:17} {r:5.2f}  {note:11} {ok}"
            if md:
                line = f"| {fg} on {bg} | {hexof(theme, fg)} on {hexof(theme, bg)} | {r:.2f} | {note} | {ok} |"
            print(line)
        for kind in ("text", "ui"):
            r, fg, bg = min(low[(theme, kind)])
            print(f"LOWEST {theme} {kind}: {r:.2f}  ({fg} on {bg})")
    print("\n## APCA Lc, dark text pairs (informational; 60 = large/UI floor, 75 = body target)")
    for fg, bg in TEXT:
        print(f"{fg:12} on {bg:17} Lc {abs(apca(hexof('dark', fg), hexof('dark', bg))):5.1f}")
    print(f"\nprimitives={len(PRIM)} semantic={len(SEM)}")
    if fails:
        print("FAILURES:", fails)
        sys.exit(1)
    print("ALL PAIRS PASS")

if __name__ == "__main__":
    run("--md" in sys.argv)
```
