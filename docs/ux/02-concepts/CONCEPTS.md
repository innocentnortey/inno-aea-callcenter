# UX-2 · Concepts — Meridian AI service agent

> **Decision:** **C2** for the chat and **S2** for the case view, first approved 2026-10-20 with the recommendations ("yeah you have my approval"), unchanged through every direction change since; confirmed with the A5 pick on 2026-10-21 ("alright we're going with A5"). Built in **direction A5 Service desk, light mode first** (picked 2026-10-21 after A1–A4 were dropped and A6 was shown).
> **Status before the gate:** DRAFT 2026-10-20 — every concept was a proposal until Innocent chose.
> **Inputs:** UX-1 (gate closed 2026-10-20 on PRD v0.4: [stories](../01-planning/USER_STORIES.md), [flows](../01-planning/USER_FLOWS.md), [sitemap](../01-planning/SITEMAP.md)); [REFERENCES.md](REFERENCES.md) (behaviour research, 19 findings); [DESIGN-DIRECTIONS.md](../../design/DESIGN-DIRECTIONS.md) (three directions; A1 and A2 built as clickable prototypes).
> A **concept** is a layout idea: where things sit and how screens hand over. A **direction** is a texture: how the parts are built. They are chosen separately. Innocent already chose the direction *family*: **A, dependable dispatch** (profile §7, 2026-10-20).
> **Light mode:** two concepts per core surface; wireframes for the core screens only (SCR-1 chat, SCR-6 case view), drawn in the chosen texture once the directions exist.
> **Data:** synthetic and issued-test examples only (MHC-10002, INV-204411, reference MHC-C-0007 come from the consolidated direction's seeded story).

## Recommendation

**Chat: C2 (thread + "what's settled" panel). Case view: S2 (three columns: queue → story → proof).**
- *Because:* both read left to right as one sentence (the scanning check). In C2 that sentence is "what we're saying → what is now settled". In S2 it is "what's next → what happened and what you decide → the proof".
- C2 keeps the four things a homeowner can check always in view: who is coming, when, what it costs, and who gets back to them by when (profile §6, *Trust*).
- S2 puts the eight-heading brief at the centre and the sources beside it, so checking a fact never hides the story (consolidated C2, C4).
- *Alternatives:* C1 if the chat must stay a plain thread on every width; S1 if laptops narrower than about 1100 px matter more than side-by-side proof.

---

## Customer chat (SCR-1)

### C1 · One thread, cards inline
- **Idea in one line:** a classic chat. Every answer, slot set, code prompt, confirmation and handoff is a card inside the thread; a sticky top bar holds the demo date, the staffing state and "Talk to a person".
- **Intent:** the most familiar shape for a phone, and the least to learn.
- **Layout sketch:** not drawn in light mode: C2 was built instead (the recommendation).
- **Safety:** a safety reply becomes a full-width card at the top of the thread and stays pinned until dismissed.
- **Handoff:** the handoff card (reference, promise, follow-up choice) stays reachable from a "Your request" chip in the top bar.
- **Good at:** phone, one hand; fast to build; nothing competes with the conversation.
- **Bad at:** a confirmed booking or a promise scrolls away; on a laptop the screen is mostly empty; the four trust items are scattered through the thread.
- **Serves best:** US-1, US-6, US-7, US-17 · **Struggles with:** US-10, US-12, US-14 (details scroll away).
- **Generated with:** Claude-built screens in each direction's construction (no Stitch).
- **Conflicts with a PRD rule?** None.

### C2 · Thread + "what's settled" panel (recommended)
- **Idea in one line:** the conversation on the left; on the right, a panel that fills as facts land: the visit (date, window, technician, fee), the request (reference, promise, due date, follow-up choice), and identity status. On a phone the panel becomes a strip under the top bar that expands on tap.
- **Intent:** trust. The homeowner can always see what is now true, not just what was said.
- **Layout sketch:** in the chosen direction A5: `wireframes/A5-chat-390-*.png`, `A5-chat-1280-*.png`; clickable in `docs/artifacts/2026-10-21-direction-A5-service-desk.html`. (History: A1–A3 were built the same way, `wireframes/A1|A2|A3-chat-*.png`.)
- **Linking:** when a card in the thread settles something (a booking, a handoff), the matching row in the panel highlights briefly; motion only to show where it landed, and off under reduced motion.
- **Safety:** the safety instruction takes over the panel *and* leads the thread; nothing else is in the panel while it shows.
- **Good at:** the scanning check; US-10, US-12, US-14 (the promise and reference never scroll away); the reviewer sees the honest promise at a glance.
- **Bad at:** more to build; the phone strip needs care so it doesn't eat the screen; risk of repeating the same fact twice (thread and panel).
- **Serves best:** US-5, US-10, US-12, US-14, US-15, US-25 · **Struggles with:** none outright; US-6 gains little.
- **Generated with:** Claude-built screens in each direction's construction (no Stitch).
- **Conflicts with a PRD rule?** None. R-4 (short replies) is helped: the panel carries the details so replies can stay short.

### Every customer flow, end to end

| Flow | C1 | C2 |
|---|---|---|
| FLOW-1 Question | Answer card with a source chip | same; nothing lands in the panel |
| FLOW-2 Safety | Pinned full-width card at the top of the thread | Leads the thread and takes over the panel |
| FLOW-3 Code | Code-prompt card with a field and "Open the demo inbox" link | same; panel shows "Identity: code sent to the phone ending in 02", then "verified" |
| FLOW-4 Account | Account card in the thread | Account card in the thread; the panel shows what was looked at |
| FLOW-5 Booking | Slot card → confirmation card | Slot card in the thread; the confirmation lands in the panel's *Your visit* block |
| FLOW-6 Change | Change-request card | The *Your visit* block shows "Original stays until a representative confirms" beside the request |
| FLOW-7 Handoff (nobody online) | Handoff card + "Your request" chip | The *Your request* block: reference, promise, due date, follow-up choice |
| FLOW-8 Live handoff | "Riley (demo representative) has joined" notice in the thread | same, plus the panel header shows who is in control: assistant or Riley |

---

## Staff case view (SCR-6) and the queue (SCR-5)

### S1 · Queue list, then one case page
- **Idea in one line:** an inbox. The queue is a full page (SCR-5); opening a case replaces it with the case page (SCR-6): brief on top, then tabs for *Sources* and *Conversation*.
- **Intent:** simple, and works on narrow laptops and phones.
- **Layout sketch:** not drawn in light mode: S2 was built instead (the recommendation).
- **Good at:** narrow screens; one thing at a time; quick to build server-side.
- **Bad at:** checking a fact means leaving the brief for a tab; going back to the queue loses your place; the live chat competes with the brief.
- **Serves best:** US-18, US-21 · **Struggles with:** US-19 (verify in place), US-20 (live chat beside the brief).
- **Generated with:** Claude-built screens in each direction's construction (no Stitch).
- **Conflicts with a PRD rule?** None.

### S2 · Three columns: what's next → the story → the proof (recommended)
- **Idea in one line:** left, the queue (P0/P1 first, then due time); centre, the case's eight-heading brief with the promise and follow-up preference at the top and the actions at its foot; right, the evidence: each source as "what the AI saw" vs "now", with the full conversation (and the live-chat box when joined) as the second tab.
- **Intent:** a representative understands a case in about a minute and checks any fact without losing the story (consolidated C2, C4).
- **Layout sketch:** in the chosen direction A5: `wireframes/A5-case-1280-*.png`; clickable at `#case` in `docs/artifacts/2026-10-21-direction-A5-service-desk.html`. (History: `wireframes/A1|A2|A3-case-1280-*.png`.)
- **Linking:** clicking a fact's source tag in the brief scrolls the right column to that source and highlights it.
- **Below about 1100 px:** the queue collapses to a drawer; below phone width the right column becomes a tab.
- **Good at:** the scanning check; US-19 and US-20 (brief, sources and live chat visible together); the reviewer playing Riley sees everything at once.
- **Bad at:** dense; needs a collapse rule; more layout work.
- **Serves best:** US-18, US-19, US-20, US-21 · **Struggles with:** phone width (acceptable: the console is laptop-first, SITEMAP).
- **Generated with:** Claude-built screens in each direction's construction (no Stitch).
- **Conflicts with a PRD rule?** None.

### Supervisor, owner, monitoring and evaluation (one concept each, not compared)

These screens are lists and numbers; there is no real layout choice worth a comparison in light mode.
- **SCR-7 Oversight:** five stacked lanes in fixed order (P0/P1, overdue, due soon, unowned, stuck waiting), each a compact table with owner, age and follow-up preference; assign inline; the demo controls (shift, advance time) in a labelled strip at the top.
- **SCR-8 Review list:** one table, newest first, each row linking its case and message.
- **SCR-9 Owner, SCR-10 Monitoring, SCR-11 Evaluation:** a short row of headline numbers, each with its denominator underneath ("*n* of *N* in-scope cases", filled only from a stored run), then the breakdown table; every number opens its cases or its run. Health and correctness never share a row (R-35).

## Comparison

| Criterion (from the PRD's metrics and rules) | C1 | C2 | S1 | S2 |
|---|---|---|---|---|
| Honest promise and reference always visible (R-26, US-14) | partly (chip) | **yes** | n/a | **yes** (top of brief) |
| Safety unmistakable (R-5, profile §7) | yes | **yes** (thread + panel) | n/a | P0 rows on top |
| Phone, one hand (profile §6) | **best** | good (strip) | good | weak (laptop-first) |
| Verify a fact without losing the story (R-29, US-19) | n/a | n/a | weak (tabs) | **yes** |
| Live takeover beside the brief (R-31, US-20) | n/a | n/a | weak | **yes** |
| Scanning check, left → right | n/a (one column) | **yes** | n/a | **yes** |
| Build cost for the time box | **lowest** | medium | **lowest** | medium |
