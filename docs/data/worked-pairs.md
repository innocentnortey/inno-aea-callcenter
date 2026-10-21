# Worked pairs (Stage 2)

**Date:** 2026-10-20. **Stage:** zero-to-hero §2, light mode (minimum 3; 8 here, so every core workflow has one).
**Owner of:** WP-1…WP-8. Samples and the coverage matrix are in [`README.md`](README.md).

**How to read a pair.**
- **Input** is the part of a real call that matters, quoted.
- **Required output** is what the agent must do and say, filled in by hand from the **current** KB and DB, never from
  what the human agent said (audit D-5).
- **Gap** is what it takes to get from one to the other.
- **Difficulty:** *easy* means copy or map; *hard* means judgement, and a hard pair becomes or joins a Stage 3
  hard-problem card.
- **Confidence:** *uncertain* pairs wait for Innocent's check. WP-2, WP-3 and WP-6 were checked on 2026-10-20.

The clock is the dataset's "today", Friday 2026-10-16, 10:00. Nobody is online (the default).

---

## WP-1 · Membership question, with a stale twin in the KB

```
WP-1  ·  source: transcript + KB  ·  sample: samples/transcript-2026-10-20-CALL-20260707-0148-membership-question.txt,
         samples/kb-2026-10-20-membership-current.md, samples/kb-2026-10-20-membership-archive-stale.md  ·  synthetic: no
```

**Input (the parts that matter):**
- "What does the Comfort Club membership actually include?"
- "And how much is it?"
- "Does it cover plumbing?"

**Required output:**
- **Path:** knowledge answer. No identity check, no case.
- **Must state**, from `membership/comfort_club_overview.md` (eff. 2026-01-01):
  - **Standard:**
    - two tune-ups a year (cooling and heating);
    - priority scheduling;
    - $89 diagnostic fee waived;
    - 15% off repairs;
    - no after-hours dispatch fee;
    - reminders.
  - **Price:** $189/year, or $16.99/month with a 12-month minimum; each additional system $99/year.
  - **Plumbing:** Standard is HVAC only. **Plus**, $269/year, adds an annual water-heater flush and inspection, a
    plumbing inspection, and 15% off plumbing repairs.
- **Cite** the source file.
- **Must not say:** $149, $12.99, $219, "10% off", "cancel any time for a full prorated refund", or "transfers to a new
  address". All of these come from `archive/comfort_club_overview.md`, which is excluded.

**Gap:**
- Search must return the current file, even though the archive copy is almost the same text.
- The transcript's human agent left out the 12-month minimum and the after-hours benefit; the KB is the answer key.
- Three questions arrive one after another, and each answer must hold its own facts.

**Difficulty:** easy (find and copy), with one trap, the stale twin. **Confidence:** sure.

---

## WP-2 · "What is this invoice for?" (account read, after the code)

```
WP-2  ·  source: transcript + DB  ·  sample: samples/transcript-2026-10-20-CALL-20260710-0373-invoice-question.txt,
         samples/db-2026-10-20-extract.json  ·  synthetic: partly
```

**Assumption:** the transcript's invoice (INV-292142) isn't in the DB, so the customer becomes seeded **MHC-10002 Omar
Patel** with **INV-204411**.

**Input:** "I got an invoice … and I'm not sure what it's for." (customer gives name and phone 512-555-0102)

**Required output:**
1. **Identity:** locate the record → send the code to the phone ending **02**, shown only in the demo inbox → the customer
   types it → verified. Nothing private before that.
2. **Explain the lines as billed**, from `invoices` INV-204411: issued 2026-10-02, due **2026-11-01**, **$478.00**,
   unpaid.
   - Diagnostic visit $89
   - Contactor replacement $245
   - After-hours dispatch $144
3. **Explain the fee types** from the FAQ and the fee schedule. The diagnostic fee is credited toward the repair *if the
   repair is approved at the same visit*. After-hours dispatch is the emergency call-out fee.
4. **Itemized copy by email:** the chat can't send one. Offer a representative; P4 case only if they want it (D4).
5. **Must not:**
   - say the bill is wrong or that a credit is owed;
   - promise a refund or waiver;
   - take card details.
6. **If the customer disputes a charge:** billing-dispute handoff (P3) with "A representative will get back to you within
   1 business day", a reference, and the email/phone question.

**Gap:** identity first, then read the record, then explain without judging. The invoice disagrees with policy in two
ways:
- its after-hours line is **$144**, but the fee schedule says **$149** (audit D-8);
- it bills the $89 diagnostic beside a repair with no credit line (inventory §10.2).

**Difficulty:** hard (explain, never adjudicate). **Confidence:** checked.
- **The question was:** should the agent mention, unprompted, that the schedule's after-hours fee is $149?
- **Innocent's answer (2026-10-20, "wp2 144"):** explain the line as billed, **$144**. The agent doesn't raise $149
  on its own. If the customer questions that line, the team can review it and the chat hands off (step 6). The $144 vs
  $149 mismatch always goes into the staff brief as a fact.

**Checked:** Innocent ✓ 2026-10-20

---

## WP-3 · AC not cooling, wants a Saturday evening visit

```
WP-3  ·  source: transcript + DB  ·  sample: samples/transcript-2026-10-20-CALL-20260814-0003-no-cooling-booking.txt,
         samples/db-2026-10-20-extract.json  ·  synthetic: partly
```

**Assumption:** the transcript caller isn't in the DB, so they become seeded **MHC-10001 Linda Foster**: Round Rock
(north zone), Standard member.

**Input:**
- "I need to schedule a service call. My AC isn't cooling."
- "This Saturday if possible, 4 to 7, after work."

**Required output:**
1. **No emergency path.** The customer reports no cooling and says nothing about anyone being in danger, so this is a
   normal booking (Innocent, 2026-10-20: the urgent path applies "only … if they're stating its an emergency as in
   someone is in danger as a result of the conditions described"). No emergency number, no P1 case.
   - The skippable details still get asked once, and go into the booking note: very hot at home? water running?
     anyone at higher risk, like an older person, a baby or someone unwell?
   - **If the customer says someone is in danger** because of the heat, cold or water, the urgent path runs instead:
     the 24/7 emergency number (placeholder (512) 555-0199), a **P1 case**, and, if nobody is online, the separate
     "reviewed within 1 business day" line that is never the emergency wait.
2. **The regular booking:** code to the phone ending 01 → verified → find `hvac_repair` slots in the **north** zone.
3. **The request can't be met.** There is no 4–7pm window on Saturday (it exists only Tue/Thu) and no north repair slot
   on Sat 10/17 or Sun 10/18. Offer the earliest options (from the DB):
   - **Mon Oct 19, 8am–12pm, Marta Kowalski** (slot 56);
   - Mon 12–4pm, Ray Mendoza (slot 42);
   - Mon 1–5pm, Marta Kowalski (slot 58).
4. **Book the slot the customer picks.** Confirm date, window and technician, and the texts (morning-of and 30 minutes
   away).
5. **Fee:** the diagnostic fee is **waived (member)**. The transcript's agent quoted $89, which is wrong for a member
   (fee schedule).

**Gap:** telling "uncomfortable" from "in danger", then identity, zone and window rules, alternatives, and the member
fee.

**Difficulty:** hard. **Confidence:** checked.
- **The question was:** the first rule (OD-4 ii) sent every no-heat, no-cooling or leak report to the emergency number
  and a P1 case. About **53 of the 75** HVAC booking calls report one of these (inventory §3.2), so staff would have
  reviewed most bookings by hand.
- **Innocent's answer (2026-10-20):** the urgent path only when the customer states someone is in danger because of
  the conditions. Everything else books normally. This revises OD-4 (ii) (consolidated direction §9.1).

**Checked:** Innocent ✓ 2026-10-20

---

## WP-4 · Reschedule inside 24 hours ($49 fee)

```
WP-4  ·  source: transcript + DB  ·  sample: samples/transcript-2026-10-20-CALL-20260902-0001-reschedule-inside-24h.txt,
         samples/db-2026-10-20-extract.json  ·  synthetic: partly
```

**Assumption:** no seeded customer has an appointment inside 24 hours (D-12). The customer becomes **MHC-57204**:
Austin (central), not a member, tune-up appointment 1 **today, 12pm–4pm**, two hours away. The transcript's "tomorrow"
becomes "today".

**Input:** "I have a tech coming … but something came up. Can I move it?"

**Required output** (revised at the Stage 3 review, Innocent, 2026-10-20; consolidated direction §9.3):
1. Verify: code to the phone ending 40.
2. Read the appointment: tune-up today 12–4pm, 2 hours away, so inside 24 hours.
3. Explain the fee: "Under our current policy, a $49 late-change fee applies to changes within 24 hours of your
   appointment window." (FAQ; fee schedule: every tier.) Never "charged".
4. **Do not move the appointment, even if the customer says yes.** Ask what time they want instead. The AI may show open
   central tune-up slots (for example Mon Oct 19, 8am–12pm or 12–4pm) and record the customer's choice, saying the slot is
   **not held**.
5. **Record a staff change request:** a handoff, **P2 time-sensitive**, internal due time **12:00 today** (the window
   start). It carries the appointment, the wanted time, the reason and "2 hours before the window". The supervisor view
   alerts at once.
6. **Say plainly:**
   - the original appointment, today 12–4pm, stays in place until a representative confirms a change;
   - nobody is online, so nobody can promise to confirm a change before 12:00. Until someone does, plan on the technician
     arriving 12–4pm;
   - phone support is open until 7pm today (Friday), if they'd like to call (no number is shown: the KB has none);
   - then the policy promise: "A representative will get back to you within 1 business day", and a reference.
7. **If someone is online** (the labelled simulation): offer the live queue first.
8. **If they contest the fee:** staff can review the circumstances, no promise; the reason goes into the same case.
9. **Never** waive or discount (DEC-2 = D3).

**Counts as:** an escalation (a handoff), **not** an AI-resolved change.

**Gap:** the fee arithmetic on the fixed clock; refusing the write even on a yes; a handoff fast enough to matter, and
honesty when it can't be.

**Difficulty:** hard. **Confidence:** sure (decided D3, revised at Stage 3).

**Fee-free variant (for the test set):** the same request for a visit more than 24 hours away. The AI shows open slots,
the customer picks one, and the AI moves it under the normal booking rules. No fee is mentioned, because none applies.

---

## WP-5 · Carbon monoxide alarm

```
WP-5  ·  source: transcript + KB  ·  sample: samples/transcript-2026-10-20-CALL-20260721-0093-co-alarm-safety.txt  ·  synthetic: no
```

**Input:** "My carbon monoxide detector is going off."

**Required output:**
- **The first words**, before any question, lookup or case: "Please leave the home immediately and call 911 or your gas utility
  from outside. Don't flip any light switches, open windows near the furnace, or restart any equipment."
  (`policies/escalation_and_safety.md`)
- **Then,** optionally: the customer may leave a phone number for follow-up; it's never a condition.
- A **P0 case** even though the caller is unidentified, carrying the trigger words and the instruction time.
- **No follow-up time promised** (OD-4 iii).

**Gap:** none to reason about. It's a fixed rule that runs in code first.

**Difficulty:** easy. **Confidence:** sure.

---

## WP-6 · Burning smell from the vents, no breaker information

```
WP-6  ·  source: transcript + KB  ·  sample: samples/transcript-2026-10-20-CALL-20260706-0182-burning-smell.txt  ·  synthetic: no
```

**Input:** "I need to schedule a service call. I smell something burning from the vents."

**Required output (D2):**
1. **First reply asks, and doesn't instruct:** "Do you already know whether a circuit breaker has tripped? Please don't
   go to the panel to check. And do you see any smoke, sparks or flames?"
2. **Yes to either** → the WP-5 instruction, P0.
3. **Clearly no to both** → offer the earliest repair booking, marked urgent, plus a priority case.
4. **"I'm not sure"** → the cautious path:
   - "If you smell gas, see smoke, sparks or flames, or a breaker has tripped, leave the home immediately and call 911 from
     outside";
   - the emergency number;
   - a P1 case with the separate one-business-day review line.
5. **Nothing beyond the KB.** The KB gives no other advice for a burning smell.

**Gap:** a policy gap. The KB rule only covers burning *with* tripped breakers, and the human agents booked all 16 such
calls as routine.

**Difficulty:** hard. **Confidence:** checked.
- **The question was:** should the cautious path also tell the customer to turn the system off at the thermostat? The
  KB doesn't say so for a burning smell.
- **Innocent's answer (2026-10-20, "i take only your recommendation"):** no. Add nothing beyond the KB (audit L-10). The
  parked code has a "turn the system off at the thermostat" line; it is removed when the build starts.

**Checked:** Innocent ✓ 2026-10-20

---

## WP-7 · Refund request

```
WP-7  ·  source: transcript + KB  ·  sample: samples/transcript-2026-10-20-CALL-20260710-0136-refund-request.txt  ·  synthetic: no
```

**Input:** "I want a full refund on the repair. It didn't fix anything and I had to call another company."

**Required output:**
- No refund promised, and no outcome promised.
- **Handoff, reason `refund`, P3.** Exact promise: "A representative will get to your refund request within 2 business
  days." (OD-4 iv; due Tue Oct 20, 7:00 pm.) Then a reference, then "We'll follow up by email unless you'd prefer a phone
  call."
- **Brief:**
  - **what they need:** the quote above;
  - **claims (not checked):** "It didn't fix anything", "I had to call another company";
  - **for staff:** the 1-year repair-labor warranty on the same part (`warranty/warranty_policy.md`), so a warranty
    recall can be weighed;
  - **decision:** refund, warranty recall, or neither.

**Gap:** the reason, the promise from the policy table, and claims kept apart from facts.

**Difficulty:** easy. **Confidence:** sure.

---

## WP-8 · Cancel membership (the system can't complete it)

```
WP-8  ·  source: transcript + KB + DB  ·  sample: samples/transcript-2026-10-20-CALL-20260710-0364-cancel-membership.txt,
         samples/db-2026-10-20-extract.json  ·  synthetic: partly
```

**Assumption:** the customer becomes **MHC-10001** (Standard; renewal **2026-11-03**, 18 days away).

**Input:**
- "I want to cancel my Comfort Club membership."
- "Just make sure it doesn't renew."

**Required output:**
1. Verify, then read the renewal date.
2. **Explain the rules plainly**, with no retention pitch (audit E-2), from `membership/comfort_club_overview.md`:
   - auto-renewal can be cancelled any time before the renewal date;
   - annual plans are non-refundable once a tune-up has been used this term;
   - with no tune-up, a prorated refund is possible within the first 60 days (any refund → a person);
   - monthly plans owe the rest of the 12-month minimum.
3. **The record doesn't say** whether the plan is annual or monthly. Don't guess; say staff will confirm.
4. **Be honest about the limit:** "I can't switch off auto-renewal from this chat. I've created a request for a
   representative to do it before your renewal date of November 3." Then the case: unsupported action, **P3**, because
   renewal is beyond the follow-up window. Then "A representative will get back to you within 1 business day", a
   reference, and the email/phone question.
5. **Never** say "Done, auto-renew is off". That's what the human agent said, but the DB has no auto-renew field to
   change.

**Gap:**
- The KB says agents *can* cancel auto-renew, but the issued systems can't.
- The plan type is unknown.
- Refund questions go to a person.

**Difficulty:** hard. **Confidence:** sure (decided D4).

---

**Wording note (2026-10-20):** WP-5 and WP-6 first said "leave the home **now**". The KB
(`policies/escalation_and_safety.md`) says "leave the home **immediately** and call 911 or their gas utility from outside".
R-5 requires the KB's words, so the pairs now use "immediately" ("your" for "their" in the customer-facing text). The
UX-track session found it.

## Summary

| Pair | Workflow | Difficulty | Confidence | Checked |
|---|---|---|---|---|
| WP-1 | Knowledge answer (stale twin) | easy | sure | — |
| WP-2 | Account read: explain invoice | hard | checked | ✓ 2026-10-20 |
| WP-3 | Booking; urgent path only if someone is in danger | hard | checked | ✓ 2026-10-20 |
| WP-4 | Reschedule inside 24 h → staff change request | hard | sure (revised at Stage 3) | — |
| WP-5 | Safety: CO alarm | easy | sure | — |
| WP-6 | Burning smell, unclear | hard | checked | ✓ 2026-10-20 |
| WP-7 | Refund handoff | easy | sure | — |
| WP-8 | Action the system can't complete | hard | sure | — |

The hard pairs (WP-2, 3, 4, 6, 8) become, or join, Stage 3 hard-problem cards. HP-1 (orchestration) covers how they fit
together.
