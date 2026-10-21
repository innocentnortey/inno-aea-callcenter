# Data reality: samples and selection matrix (Stage 2)

**Date:** 2026-10-20, America/Chicago. **Stage:** zero-to-hero §2 (light mode). **Owner of:** which samples were
chosen, why, and which cell of sources × request types × edge cases each one covers. Worked pairs live in
[`worked-pairs.md`](worked-pairs.md). The full analysis of all 420 calls is in the
[handoff information inventory](handoff-information-inventory.md); this file picks representative pieces from it.

**What's in `docs/data/`:**

| Path | What |
|---|---|
| `issued/` | The issued dataset, **read-only** (S-102…S-105) |
| `samples/` | 14 copies of issued items, each named `source-captureDate-id-topic` |
| `worked-pairs.md` | 8 worked pairs (WP-1…WP-8): input → required output → gap |
| `handoff-information-inventory.md`, `handoff-inventory-call-map.csv`, `scripts/` | All-420 classification and checks |

All data is Meridian's issued, fictional data. No real personal data is involved; nothing is redacted because nothing is
real. Samples are byte copies, so they can be diffed against `issued/`.

## How the samples were chosen

They were chosen **on purpose, not at random** (zero-to-hero §2 rule: every source, every type, the strange ones).
Twenty easy booking calls would make the job look easy, so the set leans on the cases most likely to go wrong:
- a stale document that out-scores the current one;
- a fee that must be stated before a change;
- a safety call;
- a policy gap;
- a request the systems can't complete;
- a dropped request.

| # | Sample | Source type | Request type (inventory) | Edge case it covers |
|---|---|---|---|---|
| S1 | `transcript-2026-10-20-CALL-20260707-0148-membership-question.txt` | Transcript | MEM-INCLUDE (F5 membership) | Three questions in one call; the archive copy is the closest wrong text |
| S2 | `transcript-2026-10-20-CALL-20260710-0373-invoice-question.txt` | Transcript | BILL-EXPLAIN (F3 billing) | Invoice number not in the DB; needs identity before reading |
| S3 | `transcript-2026-10-20-CALL-20260714-0246-billing-dispute.txt` | Transcript | BILL-DISPUTE (F4) | $60 gap that matches no fee; policy says a person decides |
| S4 | `transcript-2026-10-20-CALL-20260710-0136-refund-request.txt` | Transcript | BILL-REFUND (F4) | Refund wording; promise is 2 business days (OD-4) |
| S5 | `transcript-2026-10-20-CALL-20260814-0003-no-cooling-booking.txt` | Transcript | SCH-HVAC (F1 booking) | No cooling, nobody in danger (normal booking); asks for Saturday 4–7pm, which doesn't exist |
| S6 | `transcript-2026-10-20-CALL-20260902-0001-reschedule-inside-24h.txt` | Transcript | SCH-RESCHED (F2) | Inside 24 hours; the human agent never mentioned the $49 fee |
| S7 | `transcript-2026-10-20-CALL-20260721-0093-co-alarm-safety.txt` | Transcript | SAF-CO (F9) | Caller never identified; instruction must come first |
| S8 | `transcript-2026-10-20-CALL-20260706-0182-burning-smell.txt` | Transcript | SCH-BURNING (F1) | Policy gap: burning smell without breaker information |
| S9 | `transcript-2026-10-20-CALL-20260719-0153-compressor-dropped-schedule.txt` | Transcript | WAR-PARTS (F6 warranty) | Customer asks to schedule; the human agent never books |
| S10 | `transcript-2026-10-20-CALL-20260710-0364-cancel-membership.txt` | Transcript | MEM-CANCEL (F5) | The DB has no auto-renew field: the task can't be completed in chat |
| S11 | `kb-2026-10-20-membership-current.md` | KB, Markdown (current, eff. 2026-01-01) | Membership | The current source |
| S12 | `kb-2026-10-20-membership-archive-stale.md` | KB, Markdown (archive, excluded) | Membership | Stale twin: $149, "refund any time", transfers |
| S13 | `kb-2026-10-20-holiday-hours-image.png` | KB, **PNG image** | Hours | Content exists only as an image; hand-transcribed with a link to it |
| S14 | `db-2026-10-20-extract.json` | Scheduling DB (read-only extract) | Account, booking | Seeded customers, INV-204411, an appointment inside 24 h, slot sample, issue/service mismatches |

## Selection matrix: sources × request types × edge cases

✔ = covered by a sample (S-number) or worked pair (WP-number). "—" = not applicable.

| Request type ↓ / source → | Transcripts | KB Markdown/TXT | KB PDF / CSV | KB image | Scheduling DB | Worked pair |
|---|---|---|---|---|---|---|
| Membership answers (F5) | S1, S10 | S11, S12 (stale twin) | fee schedule PDF | — | S14 customers (tier, renewal) | WP-1, WP-8 |
| Billing questions (F3) | S2 | FAQ | fee PDF, price-book CSV | — | S14 INV-204411 | WP-2 |
| Disputes and refunds (F4) | S3, S4 | escalation policy | — | — | — | WP-7 (refund); WP-2 notes the dispute branch |
| New booking (F1) | S5 | FAQ (windows, texts) | fee PDF (member waiver) | — | S14 slots, seeded customers | WP-3 |
| Appointment changes (F2) | S6 | FAQ (24 h, $49) | fee PDF ($49 every tier) | — | S14 appointment 1 (inside 24 h) | WP-4 |
| Warranty (F6) | S9 | warranty policy | — | — | customers.system_* | covered by the matrix, no pair (light mode) |
| Safety (F9) | S7 | escalation and safety policy | — | — | — | WP-5 |
| Policy gap: burning smell | S8 | safety policy (breaker condition) | — | — | — | WP-6 |
| Unsupported action (D4) | S10 | membership cancellation rules | — | — | no auto-renew field | WP-8 |
| Hours and holidays | — (0 calls ask) | FAQ hours | — | S13 | — | — |

**Synthetic parts, and why.** No transcript caller exists in the DB (0 of 131 account numbers, 0 of 42 invoices;
inventory §1). Pairs that need a record **keep the transcript's words** but **substitute a real DB record**, marked
`synthetic: partly` in the pair with its assumption:
- WP-2 uses MHC-10002 and INV-204411;
- WP-3 and WP-8 use MHC-10001;
- WP-4 uses MHC-57204 and appointment 1.

The assumption: the request would read the same for that customer. No pair invents a fact the KB or DB doesn't hold.

## New data findings from this stage

| ID | Finding | Evidence | What the system does |
|---|---|---|---|
| D-11 | **Existing appointments' issue text doesn't match their service type** in 109 of 159 rows (69%), e.g. "AC not cooling" booked as `plumbing`, "Replacement estimate" as `hvac_repair`; the warranty flag sits on unrelated visits ("Annual tune-up" with `is_warranty_visit=1`). Technician skills always match the slot (0 mismatches) | Read-only query, 2026-10-20 (S14 shows four) | When confirming an appointment, state the **slot's** service type, date, window and technician; treat `issue_description` as "as recorded"; never infer warranty coverage from the flag |
| D-12 | No seeded test customer has an appointment inside 24 hours, so the fee rule can't be shown with them. Appointment 1 (MHC-57204, today 12:00–16:00) is inside 24 h of the fixed clock | S14 | WP-4 uses it |
| D-13 | `appointments.created_at` runs to 2026-11-04, after the dataset's "today" (87 of 159 rows) | Inventory §10.2 | Never use `created_at` to reason about when something was booked |

These extend the audit's D-1…D-10 (transcript and data traps) and are owned here.
