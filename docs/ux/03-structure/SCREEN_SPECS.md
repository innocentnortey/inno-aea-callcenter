# UX-3 · Screen specs — Meridian AI service agent

> Status: DRAFT · Date: 2026-10-20 (copy pass 2026-10-21; **R-48 pass 2026-10-21:** SCR-12 demo login added, SCR-4 rewritten as the role switch, role switch noted on every screen, SCR-10 and SCR-11 behind the login) · Concepts **C2** + **S2** in direction **A5 Service desk, light mode first** (Innocent ✓ 2026-10-21, UX-2 gate: "alright we're going with A5"). **Copy pass 2026-10-21:** the A2-specific styling language (mono caps labels with glosses, route-sheet and stub wording, "buttons", route stops) is replaced with A5's (speaker name lines, plain sentence-case labels with hints, hairline cards, mint for the customer's own words, emerald for the one action). Every state, behaviour rule, CON reference, exact copy string and the N-1…N-27 table are unchanged. The look itself is exact in [`design.md`](../../design/design.md).
> Hierarchy per screen: [`IA.md`](IA.md). Contracts: [`UI_CONTRACTS.md`](UI_CONTRACTS.md) (written in parallel; this file uses the UX-1 draft IDs CON-1…CON-22 from [`USER_FLOWS.md`](../01-planning/USER_FLOWS.md) and lists what they must also carry under *Contract needs raised by the screen specs* at the end).
> Data in examples: synthetic and issued-test only (MHC-10002 "Omar Patel", INV-204411, MHC-C-0007, technician "Jun Park", code 482913, the fictional emergency number (512) 555-0199). Demo "today" is **Fri Oct 16, 2026** (R-3).

## How to read a card

Each card says what the screen is for, what is on it, what it can look like in every state, and which contract carries
each piece of data. **Concrete example:** on SCR-1, when the customer taps "8:00 am – 12:00 pm" and the backend finds the
window was taken a moment ago, CON-2 answers with the error `SLOT_TAKEN`. The screen keeps the conversation, says
"Sorry, that window just went. Here are the next open ones.", and shows a new slot card. That is the *error* state of the
slot card, it names its contract, and no part of it is invented by the screen.

**The eight states** are the standard set (default · empty · loading · partial · error · stale · success · disabled). A
state that cannot happen on a screen says "n/a" and why. Each card also has a **flow states** table: the specific
situations a flow can reach (safety takeover, code locked, slot taken…), mapped to the standard state they belong to.

## Copy rules that apply on every screen

| Rule | Exact wording or constraint | Source |
|---|---|---|
| Times | 12-hour, lowercase, with minutes: "7:00 pm", "8:00 am – 12:00 pm" (en dash, spaces). Headline windows use an arrow: "8:00 am → 12:00 pm". Never "19:00". Dates and times are never set in capitals | UX-2 gate condition |
| Labels | Plain sentence-case labels ("Arrival windows", "Reference"); no mono caps labels. Mono (Geist Mono) is for references, IDs and codes only. On customer screens (SCR-1, SCR-2, SCR-3) a label that could stump a homeowner has a one-line hint under it (table in SCR-1 copy notes). Console section heads ("Waiting in chat", "Evidence") are the one small uppercase style, set by the stylesheet, never on a time or date | UX-2 gate condition (carried into A5 as plain labels and hints) |
| Speaker on every message | A name line on every message: "Meridian assistant · automated" · "You" · "Riley · representative (demo)". Event lines have no speaker name: they are centred quiet lines with the actor in the sentence | R3-1, US-1 |
| Promises | Only the policy-table texts of R-26, word for word (SCR-1 copy notes). No wait time, no queue position, no "shortly", no "an agent will be with you" | R-26, R3-4 |
| Completion | Never "done", "booked", "cancelled", "moved", "refunded" unless the contract response reports a successful write in that turn | R-46, US-16 |
| Fees | "The $49 fee applies under current policy." The word "charged" is never used, in any form, including "No fee has been charged" | R-21 |
| Recorded, not sent | Every follow-up or contact activity: "Demo: recorded, not sent" | R-34 |
| Staffing | "Nobody online" (default) · "Simulated staff on shift (demo)" · banner "Simulated staffing (demo). No Meridian employee is online." | R-30, consolidated §8 |
| Colour | Red only on the safety card (SCR-1). Overdue, errors, limits, P0 rows: words + icon + ink weight. Demo bar and banners neutral. Mint means only the customer's own words and choices; emerald is the one action, the selected thing or the current tab; charcoal is Send | R1-4, R2-3 |

---

### SCR-1 · Customer chat
- Purpose: one conversation where a homeowner gets a sourced answer, a booking, account details after a code, the safety instruction first, or an honest handoff with a reference and a promise; and where the reviewer can watch all of it, including a demo representative joining.
- Stories: US-1, US-2, US-3, US-4, US-5, US-6, US-7, US-8, US-9, US-10, US-11, US-12, US-13, US-14, US-15, US-16, US-17, US-25, US-26, US-28 · Flows: FLOW-1, FLOW-2, FLOW-3, FLOW-4, FLOW-5, FLOW-6, FLOW-7, FLOW-8, FLOW-12
- Route: `/`, behind the demo login (R-48); the customer role is the default after SCR-12. Phone first.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Top bar | Brand "Meridian Home Comfort"; who is replying ("Meridian assistant · automated", or "Riley (demo representative). Assistant paused."); "Demo guide" link | CON-1 (initial controller), CON-3 (`representative_joined`, `handed_back`, `chat_closed`) |
  | R2 Demo bar | "Fri Oct 16, 2026 (demo date)" chip; staffing word | CON-1 (clock, staffing at start), CON-3 (`staffing_changed`, `clock_changed`; see contract needs) |
  | R2b Role switch | The shared header's role switch (SCR-4), in its own 44 px row on a phone: "Acting as" Customer · Rep · Supervisor · Owner, Customer marked; "Sign out" beside it | CON-10 (switch), CON-22 (sign out) |
  | R3 Staffing banner | "Simulated staffing (demo). No Meridian employee is online." Only while the simulation is on | CON-1, CON-3 |
  | R4 What's settled | Phone: strip under the top bar, one-line summary, expands on tap. ≥ 900 px: panel beside the thread. Blocks: *Your visit* (date, window, technician, fee; "Original stays until a representative confirms" beside an open change request) · *Your request* (reference, promise text, due, follow-up choice) · *Identity* · *Replying* (only while the simulation is on) | CON-2 (`settled` object in each reply), CON-4, CON-5, CON-3 |
  | R5 Pinned | The safety card, when triggered; pinned above the thread, not dismissible | CON-2 (`safety` block) |
  | R6 Thread | Turns with speaker label and time; reply blocks and cards (below); staff messages and event lines | CON-2 (customer turns and replies), CON-3 (staff messages, events) |
  | R7 Composer | "Talk to a person" button (left); message field; send button; hint line (limit or paused notices) | CON-4 (person), CON-2 (message) |

- Components (A5 construction; anatomy and tokens in [`design.md`](../../design/design.md) §8):
  - **Role switch** (shared header, SCR-4): a four-segment control labelled "Acting as"; the current segment is filled and ticked. It is demo chrome: neutral colours, never inside the chat thread, never red. Sign out is a quiet text link beside it.
  - **Turn block**: a speaker name line (the name, then " · " and the time) over the turn. Assistant turns are grey blocks beside the assistant mark; the customer's own turns are mint blocks at the right; a representative's turns are white blocks with an indigo initial disc. Event lines are centred quiet lines, not turns.
  - **Source chip**: "Source" (hint "Where this comes from") + file, section, version date; expands to the quoted passage.
  - **Safety card**: full-width, square-cornered card with a solid red band holding a warning icon and the signal word DANGER; Meridian's instruction as numbered lines in large sentence-case type; tap-to-call button "Call 911 (from outside)"; closed by a thick red rule. The only red element in the product.
  - **Conditional safety card** (burning smell, risk unclear): the same card, signal word WARNING, the conditional instruction, then the emergency-number line.
  - **Emergency-line card** (someone in danger from no heat, no cooling or a leak, R-8): a card with a heavier 2 px ink edge, not red, with a phone icon, the number "(512) 555-0199 (demo number)" as a tap target, and the separate 1-business-day line under a divider. *Proposal:* red is kept for "leave the home" hazards so it never loses its meaning; this card's urgency comes from position (first in the reply), size and the number.
  - **Burning-smell question card**: the question and three buttons "Yes", "No", "Not sure".
  - **Quick-checks offer**: one line, "Skip and book" as the primary button, "Show the checks" secondary; the list opens inline.
  - **Urgency questions**: two or three short questions, each with answer buttons and "Skip".
  - **Where card**: one field "ZIP code or city" and "Show windows".
  - **Slot card**: hairline card with a header row ("Choose a window"); day tabs ("Wed 21 · 2 open", "Mon 19 · Full"); window tiles ("8:00 am – 12:00 pm"; the accessible name adds "open"), taken tiles struck through with "Taken"; members-only tiles tagged "Members" after verification; the standard fee row; "Continue with this window".
  - **Locate card**: "Name on the account" + "Phone", or a "Customer ID or invoice number" field; "Send the code".
  - **Code card**: "Code sent to the phone on record, ending in 02"; 6-digit field; "Verify"; "Open the demo inbox" link; hint "Demo: codes go to a simulated inbox, never a real phone. A code lasts 10 minutes; 3 tries."
  - **Account card**: invoice (hero balance, lines table, total), or membership (tier, renewal date), or warranty (install date, term).
  - **Confirmation card**: header row "Your visit" with a "Booked" tag; headline window "8:00 am → 12:00 pm"; date, technician, fee rows; a checked list "What happens next": Booked → Technician arrives in the window → Repair approved or declined at the visit; free-change note; "Keep this" with the day and window.
  - **Appointment card** (confirm an existing visit): same anatomy as the confirmation, labelled "Your booked visit".
  - **Change-request card**: header row "Change request" with the reference; fee line; "original stays" line; wanted time; windows shown (not held); the can't-guarantee line when it applies.
  - **Handoff card**: header row "Your request" with the reference "MHC-C-0007" in mono; the promise in sentence case; "Due" row "Mon Oct 19 · 7:00 pm"; follow-up chooser (Email / Phone call; for phone: Mornings / Afternoons / Any time); "Save my choice".
  - **Live-queued card**: a checked list: You asked for a person → A representative joins this chat → Back to the assistant, or the chat closes.
  - **Event line**: a centred quiet line between two hairlines with a small icon (joined, paused, handed back, closed, shift ended, demo reset); the actor is named in the sentence.
  - **Limit notice**: neutral card, plain sentence, "Talk to a person" button inside it.
  - **Failure offer**: one line and a "Talk to a person" button.
  - **Pending lines**: one quiet row under the customer's message, beside the assistant mark: "Meridian assistant is replying…", later "Still working on this…"; static text.
  - **TURN_TIMEOUT card**: a neutral card headed "This is taking longer than it should." with "Try again" (the one primary) and "Talk to a person" (secondary). **BUSY**: one plain line under the assistant's name line and a secondary "Talk to a person" button (wording from the code's message table).
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Greeting turn (exact text in copy notes) labelled "Meridian assistant · automated"; demo bar "Fri Oct 16, 2026 (demo date) · Nobody online"; strip "What's settled · Nothing yet" (the hint "What's been confirmed so far" sits in the open panel's header); message field focused on laptops (not on phones, to keep the keyboard closed) | CON-1 |
  | empty | The greeting is the empty state: it says what the assistant is, what it can do and how to reach a person. No starter chips (not in C2; avoids suggesting scope the agent lacks). Panel blocks read "Nothing booked yet." · "No request open." · "Not checked. Only needed for private details." | CON-1 |
  | loading | **Session start:** top bar and composer render at once; the greeting area shows a one-line skeleton for up to 1 s, then "Starting the chat…". **Turn pending:** the customer's message appears immediately; after 300 ms a quiet line "Meridian assistant is replying…" (static text; the ellipsis is never animated dots, under any motion setting); **after about 10 s** it becomes "Still working on this…" (SP-1: p95 10.2 s per turn at 20 chats at once, line p95 ≤ 12.5 s; streaming not measured, so nothing assumes it); at the **60 s per-turn deadline** (Innocent, 2026-10-21, system-design §8.1; measured from server receipt; browser gives up at deadline + 5 s [A]) the reply is a code-built card: "This is taking longer than it should." with **Try again** and **Talk to a person** (`TURN_TIMEOUT`). The composer and "Talk to a person" stay usable for the whole 60 s. **No streaming:** the reply arrives whole (R-46 checks need the full text). **Busy:** above 30 turns in flight the turn is refused at once with a plain line and the person offer (`BUSY`, no model call). Send is disabled until the reply arrives; the field stays editable; **"Talk to a person" stays enabled** | CON-1, CON-2 pending |
  | partial | A reply that answers part of a message: e.g. WP-1's three questions, two answered with source chips and one "I don't have that information." with the person offer. Also a handoff card whose follow-up choice is not yet saved (chooser open, promise and reference already shown) | CON-2 (multiple blocks), CON-4 |
  | error | **Send failed** (network or server, no reply): under the customer's message, "That didn't send. Your message is still here." with "Try again"; the text is kept. **Model or tool failure** is not a UI error: the backend returns a handoff card (PRD §5 reliability). **Session gone** (reset or closed): see flow states. Field errors live on their cards (code, where, locate) | CON-2 transport error, `SESSION_ENDED` |
  | stale | **Live updates lost:** if the event stream drops, a neutral line under the demo bar "Reconnecting… Staffing and messages may be out of date." After reconnect, missed events are shown in order and the line clears. **Windows go out of date:** slot cards carry "Windows are shown, not held."; if a window is taken before the write, the error flow below runs | CON-3 (reconnect, replay), CON-2 `SLOT_TAKEN` |
  | success | A write the contract confirms: "You're booked." + confirmation card, and the *Your visit* block highlights briefly; "Verified for this chat"; handoff card + *Your request* block highlights; "Follow-up saved: phone call, the number ending in 02, mornings"; fee-free move or cancel confirmed | CON-2 (write result), CON-4, CON-5 |
  | disabled | Send disabled while the field is empty or a reply is pending. Taken window tiles disabled with the word "Taken". A card's buttons disabled once answered (shows its choice). Code field disabled after the third wrong try. Composer disabled after a reset or close, with "This chat has ended." and "Start a new chat". During a rate limit the field is disabled with the limit sentence; **"Talk to a person" is never disabled** | CON-2, CON-3 |

- Flow states (every situation a flow can reach on this screen):

  | Flow state | Flow | State column | What it looks like | Contract |
  |---|---|---|---|---|
  | Safety takeover | FLOW-2 | success (instruction delivered) | The safety card leads the reply and pins above the thread; the strip switches to "DANGER · Leave the home immediately" and the panel shows nothing else; the quiet contact line under it; no field opens, no question is asked; the composer stays enabled but focus does not move to it. Happens mid-booking too: the open slot or code card stays in the thread below, untouched | CON-2 `safety` |
  | Burning smell, unknown | FLOW-2 | default | Question card with "Yes", "No", "Not sure" | CON-2 |
  | Burning smell, risk unclear | FLOW-2 | success | Conditional safety card (WARNING), emergency-number line, then the P1 promise handling as a separate line if nobody is online | CON-2 |
  | Burning smell, both ruled out | FLOW-2 → FLOW-5 | default | Urgent booking: slot card marked "Urgent" | CON-2 |
  | Someone in danger (no heat, no cooling, leak) | FLOW-2, FLOW-5 | success | Emergency-line card first; then, separated by a divider, the 1-business-day line; then, if offered, earliest windows labelled "This is a regular booking, not emergency service." | CON-2 |
  | Quick checks offered / skipped | FLOW-5 | default | Offer line; "Skip and book" books straight on (R-44) | CON-2 |
  | Out of area | FLOW-5 | error | "Sorry, that address is outside Meridian's service area, so I can't book a visit there." + failure-offer button "Talk to a person" | CON-2 `OUT_OF_AREA` |
  | No window fits | FLOW-5 | partial | Nearest alternatives in the same card, or "That's the earliest I can book. I can't add you to a waitlist from here." + person offer | CON-2 |
  | Window chosen, identity needed | FLOW-5 → FLOW-3 | default | "Booking changes your account, so I need to confirm it's you before I write it." + locate card | CON-2 |
  | Code sent | FLOW-3 | default | Code card; *Identity* row "Code sent to the phone ending in 02" | CON-2, CON-6 |
  | Code wrong, tries left | FLOW-3 | error | Field marked invalid; "That code doesn't match. 2 tries left." | CON-2 `CODE_WRONG` (`attempts_left`) |
  | Code expired | FLOW-3 | error | "That code has expired. Codes last 10 minutes." + **Send a new code** while under the per-conversation cap of 3 (FLOW-3; CON-2 `CODE_EXPIRED`); at the cap, `CODE_CAP_REACHED` → the handoff path below | CON-2 `CODE_EXPIRED` |
  | Code locked (3 wrong) | FLOW-3 | error | Field disabled; "I can't confirm your account here. A representative will help." + handoff card | CON-2 `CODE_LOCKED`, CON-4 result |
  | No match / ambiguous / no contact | FLOW-3 | error | The same sentence and handoff card as the locked case, so nothing reveals whether an account exists | CON-2 `NOT_VERIFIED` |
  | Verified | FLOW-3 | success | "Thanks, you're verified for this chat."; *Identity* "Verified for this chat · phone ending 02"; member fee and "Members" windows appear if the record is a member | CON-2 |
  | Account answer | FLOW-4 | success | Account card; for INV-204411 the lines $89.00, $245.00, $144.00 as billed, no verdict | CON-2 |
  | Dispute / unsupported action | FLOW-4 | success (handoff) | "I can't change or remove charges, but a person can review this with you." then handoff card; for an unsupported action, no completion claim, e.g. "I can't switch off auto-renewal from this chat." | CON-2 |
  | Slot taken at write | FLOW-5 | error | "Sorry, that window just went. Here are the next open ones." + a fresh slot card; nothing booked | CON-2 `SLOT_TAKEN` |
  | Booked | FLOW-5 | success | "You're booked. Here are the details." + confirmation card; *Your visit* lands | CON-2 |
  | Confirm existing visit | FLOW-6 | success | Appointment card | CON-2 |
  | Fee-free move / cancel | FLOW-6 | success | New confirmation card, or "Your visit on [date] is cancelled. There's no fee." only after the write | CON-2 |
  | Fee-bearing change request | FLOW-6 | success (handoff) | Change-request card: fee line, "original stays" line, wanted time, windows "shown, not held"; reference and the standard promise; the can't-guarantee line when the window starts before the promise; the phone-support line only while phone support is open. *Your visit* keeps the original visit with "Original stays until a representative confirms" | CON-2 `change_request` |
  | Fee-bearing cancel | FLOW-6 | success (handoff) | Same card, worded for a cancellation | CON-2 |
  | Handoff, nobody online | FLOW-7 | success | Handoff card with promise, due headline and follow-up chooser; *Your request* lands and stays reachable | CON-4 or CON-2, CON-5 |
  | Handoff, refund | FLOW-7 | success | Refund promise variant (copy notes) | CON-4 or CON-2 |
  | Live-queued (simulated staff on shift) | FLOW-8 | success | Live-queued card; staffing banner visible; the customer may keep chatting | CON-4 `live_queued` |
  | Representative joined, AI paused | FLOW-8 | success | Event line "Riley (demo representative) has joined." and "The assistant is paused while Riley is here."; top bar "Riley (demo representative). Assistant paused."; composer placeholder "Message Riley"; Riley's turns labelled "Riley · representative (demo)" | CON-3 |
  | Handed back | FLOW-8 | success | Event line "Riley handed the chat back to the automated assistant."; top bar returns to "Meridian assistant · automated" | CON-3 |
  | Chat closed by Riley | FLOW-8 | disabled | Event line "Riley closed this chat."; composer disabled; "Start a new chat" | CON-3 |
  | Shift ended before a claim | FLOW-8 | success | Event line "The simulated shift ended before a representative joined."; the handoff card with the 1-business-day promise and the **same** reference; banner disappears; demo bar "Nobody online" | CON-3 `shift_ended` |
  | Limit reached (rate, booking cap) | FLOW-1 | error | Limit notice: "I can't take more messages in this chat right now." (rate) or "I can't make more bookings in this chat." (booking cap), each with "Talk to a person" | CON-2 `RATE_LIMITED`, `BOOKING_CAP` |
  | Spend cap reached | FLOW-1 | error | "I can't answer more questions right now. A person can pick this up." + "Talk to a person" (falls back to handoff, R-41) | CON-2 `SPEND_CAP_REACHED` |
  | No current source | FLOW-1 | partial | "I don't have that information." + "Talk to a person" offer (US-7) | CON-2 |
  | Failure signal (two misses) | FLOW-1 | default | "It sounds like I'm not getting this right. Would you like a person?" + button | CON-2 |
  | Reset during a live chat | FLOW-12 | disabled | Event line "The demo was reset, so this chat has ended. Nothing from it was kept."; composer disabled; "Start a new chat" | CON-3 `demo_reset`, CON-2 `SESSION_ENDED` |
  | Session ended while the chat is open | FLOW-12 | error | The next request answers `UNAUTHENTICATED`; the screen goes to SCR-12 with "Your demo session ended, so please sign in again." After sign-in the reviewer returns here and the chat resumes if it is still open | CON-22, any CON `UNAUTHENTICATED` |
  | Simulation switched on or off while open | FLOW-12 | stale → default | Demo bar and banner update without reload; an event line "Staffing changed: simulated staff on shift (demo)." | CON-3 `staffing_changed` |

- Interactions:
  - The role switch changes role in one click (CON-10). Choosing Representative, Supervisor or Owner leaves the chat for that role's home screen (SCR-5, SCR-7 or SCR-9); the chat session stays alive and Customer returns to the **same** conversation with any missed events replayed (N-2, N-31). The switch is available in every state, including an ended chat and an error.
  - Typing and send (Enter on laptops; send button on phones) post a CON-2 turn. Card buttons (window, Yes/No, Skip, Verify) post a CON-2 turn carrying the choice, so every action lands in the same thread.
  - "Talk to a person" posts CON-4 on the first tap. A second tap while a case is open does not create a second case: it scrolls to the handoff card and highlights *Your request*.
  - Tapping the strip toggles the panel open and closed; it never closes on its own. On desktop the panel is always open.
  - A card that settles something highlights its panel row for 1.2 s (none under reduced motion) and announces it (accessibility notes).
  - "Open the demo inbox" opens SCR-2 in a new tab; the chat keeps its state.
  - Source chip toggles its passage in place.
  - The safety card cannot be dismissed or scrolled away; it stays pinned until the chat ends.
- Copy notes (exact wording):
  - Greeting (R-1): "Hi, I'm Meridian Home Comfort's automated assistant, not a person. I can answer questions about our services, book a visit, and look up your account once you've confirmed it's you. If you'd like a person at any point, tap Talk to a person."
  - "Are you a person?" (R-1): "No. I'm Meridian's automated assistant. If you'd like a person, tap Talk to a person." (proposal)
  - Safety card (R-5, Meridian's words from `policies/escalation_and_safety.md`, changed only from "their" to "your"): DANGER · 1. "Leave the home immediately and call 911 or your gas utility from outside." · 2. "Don't flip switches, open windows near the furnace, or restart equipment." · button "Call 911 (from outside)". Quiet line under the card: "Once you're outside and safe, you can leave a number here if you'd like." No follow-up time anywhere on or under the card (R-6, R-26).
  - Burning-smell question (R-7): "Do you already know whether a breaker has tripped? Please don't go to the panel to check. Do you see any smoke, sparks or flames?"
  - Conditional card (R-7): WARNING · "A burning smell can be serious. If you smell gas, see smoke, sparks or flames, or a breaker has tripped, leave the home immediately and call 911 from outside." · "Meridian's 24/7 emergency number is (512) 555-0199 (demo number)."
  - Emergency-line card (R-8): "Because someone may be in danger, please call Meridian's 24/7 emergency number now: (512) 555-0199 (demo number). I've also logged this for our team as an emergency-priority request." Separate, under a divider, only when nobody is online: "No representative is online right now, so someone will review this online request within 1 business day. That is not the wait for emergency help; for that, please use the emergency line."
  - Urgency questions (R-8): "Is it very hot or very cold in your home right now?" · "Is water still running?" · "Is anyone at higher risk, like an older person, a baby or someone unwell?" each with "Skip".
  - Slot card hints: "Windows are shown, not held." · before the code: "Members' fees and member-only windows appear after the code."
  - Code prompt (R-15): "I've sent a 6-digit code to the phone number on your account, ending in 02. Please type it here." The code itself never appears in the chat.
  - No match, locked, expired-then-handoff (R-16): "I can't confirm your account here. A representative will help."
  - Promise texts (R-26), word for word: nobody online "No representative is online right now. A representative will get back to you within 1 business day, by Monday, October 19, 7:00 pm. Your reference is MHC-C-0007." · refund "A representative will get to your refund request within 2 business days." followed by "I can't promise an outcome." · staffed "A representative will join this chat when available. You can keep chatting with me while you wait, if you like."
  - Fee-bearing change (R-21, R-26): "The $49 fee applies under current policy." · "Your original appointment stays until a representative confirms." · when the window starts before the promise could be met: "I can't promise anyone will confirm a change before your appointment starts; until a representative confirms, please plan on the technician arriving 12:00 pm – 4:00 pm." · only while phone support is open: "Phone support is open until 7:00 pm today if you'd like to call." (no number is shown; the KB has none).
  - Follow-up (R-27): legend "We'll follow up by email unless you'd prefer a phone call."; options "Email · the address on your account" and "Phone call · the number ending in 02"; saved: "Follow-up saved: phone call, the number ending in 02, mornings." Nothing says a message was sent.
  - Live: "Riley (demo representative) has joined." · "The assistant is paused while Riley is here." · "Riley handed the chat back to the automated assistant." · "Riley closed this chat." · "The simulated shift ended before a representative joined."
  - Hints for customer-screen labels (a plain sentence-case label, then a one-line hint under it; the former glosses, wording unchanged): What's settled → "What's been confirmed so far" · Your visit → "Your booking" · Arrival windows → "The technician arrives any time in the window you pick" · Standard fee → "What you pay if you're not a member" · Verify → "Prove it's your account" · Reference → "Your reference number" · Due → "The latest we've promised to get back to you" · Keep this → "Save or screenshot this" · Identity → "Whether you've confirmed it's you" · Replying → "Who is answering you now" · Source → "Where this comes from".
  - Never on this screen: a wait time, a queue position, "shortly", "an agent will be with you", "charged", "sent" for a follow-up, a completion word without a confirmed write.
- Accessibility notes:
  - Landmarks: `header` (R1–R3), `aside` "What's settled" (R4, a `details`/`summary` disclosure on phones with `aria-expanded`), `main` with the thread as `role="log"` (`aria-live="polite"`, `aria-relevant="additions"`), `form` for the composer.
  - Focus order: top bar → demo bar → strip → pinned safety card (if any) → thread → composer ("Talk to a person" before the message field, so it is reachable first from the bottom of the page). New cards do not steal focus, except an error on a field the customer just submitted (focus returns to that field).
  - Live regions: the safety card is announced once with `role="alert"` and then becomes static (it must not repeat). Panel landings ("Your visit: Wednesday, October 21, 8:00 am to 12:00 pm") go to a separate polite region. Staffing changes and representative events are polite. Code errors use `role="alert"` tied to the field by `aria-describedby`.
  - Labels: every field has a visible label ("ZIP code or city", "6-digit code"); the code field uses `inputmode="numeric"` and `autocomplete="one-time-code"`; the send button has `aria-label="Send"`. Speaker labels are real text, not CSS.
  - Time limits: the 10-minute code expiry and 3 tries are stated in text before the customer starts typing. Expiry is a security limit (WCAG 2.2.1 exception); the customer is never logged out of the chat by it.
  - Targets: every button, window tile, day tab and chip is at least 44 × 44 px on SCR-1.
  - Colour: window "Taken" is a word plus strike-through; safety uses the signal word, an icon and numbered text as well as red; contrast AA in both themes.
  - Reduced motion: no landed wash on the panel, no card fade-in; changes still announced.
  - Reading order on screen readers puts the safety card before the latest turn.
- Contracts: CON-1, CON-2, CON-3, CON-4, CON-5, CON-10 (role switch), CON-22 (sign out) (and navigation to SCR-2 and SCR-3)

### SCR-2 · Demo delivery inbox
- Purpose: let the reviewer read the simulated one-time code, while saying plainly that nothing is sent to anyone.
- Stories: US-8, US-25, US-28 · Flows: FLOW-3, FLOW-12
- Route: `/demo/inbox`, behind the demo login, opened in a new tab from the code card or the demo guide.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Header | "Demo delivery inbox · Simulated messages"; "Simulated messages. Nothing is sent to anyone. This exists only so reviewers can complete verification."; the shared header's role switch and Sign out | CON-10, CON-22 |
  | R2 Messages | Newest first. Each: "To ···02 · Fri 2:07 pm"; "Your Meridian Home Comfort verification code is 482913. It expires in 10 minutes."; status Active (expires 2:17 pm) / Used / Expired; "Copy code" | CON-6 |
  | R3 Foot | "This inbox carries codes only. Follow-ups are recorded on the case, never sent." · "Back to the chat" | none: static |

- Components: message card (recipient and time, the code large in mono), status word, copy button, back link. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Header and the newest message with its code | CON-6 |
  | empty | "No codes yet. When the chat sends a code, it appears here. Ask the chat about your bill or book a visit to get one." + "Back to the chat" | CON-6 (empty list) |
  | loading | Header renders; one message-shaped skeleton for up to 1 s | CON-6 pending |
  | partial | n/a: each message is delivered whole; there is nothing to show half of | — |
  | error | "The inbox didn't load. Try again." with a retry button; header stays | CON-6 error |
  | stale | The list refreshes every 5 s while the tab is visible and on focus; a code past its expiry shows "Expired" and its copy button is disabled; a new code arriving is announced "New code received" | CON-6 (`expires_at`, `status`) |
  | success | "Copied" next to the button for 2 s after copying | client action on CON-6 data |
  | disabled | "Copy code" disabled on Used and Expired messages, with the status word as the reason | CON-6 |

- Flow states: code arrives (FLOW-3) → default/stale; code used → stale ("Used"); reset (FLOW-12) → empty.
- Interactions: Copy code; Back to the chat (switches to the opener tab when possible, else opens `/`). No typing, no sending. The role switch in the header changes role in one click (CON-10) and this page stays; sign out goes to SCR-12.
- Copy notes: the header sentence is fixed (consolidated §8). Masked recipient only ("···02"). Never call it an SMS or email. Times 12-hour.
- Accessibility notes: one `h1` "Simulated messages"; the list is `ol` newest first; new-code announcement is polite; the code is in a `<b>` with `aria-label` reading digits one by one ("4 8 2 9 1 3"); copy button 44 × 44 px; status in words.
- Contracts: CON-6, CON-10, CON-22

### SCR-3 · Demo guide and controls
- Purpose: tell the reviewer what is real and what is simulated, how to play staff in a second tab, and give the staffing switch and reset.
- Stories: US-25, US-26, US-15, US-28 · Flows: FLOW-8, FLOW-12
- Route: `/demo`, behind the demo login, from the chat's demo bar and the console header.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Header | "Demo guide · How this demo works"; demo bar (date, staffing); the shared header's role switch and Sign out | CON-8 (clock read), CON-7, CON-10, CON-22 |
  | R2 Real vs simulated | Real: the assistant and its answers; Meridian's knowledge base; bookings, written to a working copy of the scheduling database; what you type as Riley. Simulated: the date (Fri Oct 16, 2026); staffing (nobody is online unless you turn on the simulation); the one-time code (sent to a demo inbox); follow-ups and calls ("Demo: recorded, not sent") | none: static |
  | R3 Staffing | Current state in words and the switch "Demo: simulate staff on shift"; one line on what changes: "The chat will offer a live queue, and the staff console will show it." | CON-7 |
  | R4 Two roles | Steps: 1 Keep the chat open in this tab. 2 Use the role switch at the top to act as Representative (Riley), or open the console in a second tab. 3 Ask the chat for a person. 4 Claim and join from the queue, then switch back to Customer to see Riley's reply | none: static |
  | R5 Links | Chat · Demo inbox · Staff queue · Monitoring · Evaluation | none: static |
  | R6 Reset | "Reset the demo" with its consequence and a confirm step; needs the login session. The login and the current role are kept | CON-9 |

- Components: two-column list (stacks on phones), switch, step list, link list, confirm dialog. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | All regions; staffing "Nobody online"; switch off | CON-7, CON-8 |
  | empty | n/a: the guide is static content and always has something to show | — |
  | loading | Static regions render at once; the staffing line and switch show "Checking…" and the switch is disabled until CON-7 answers | CON-7 pending |
  | partial | n/a: the only live data is staffing and the clock; if either fails it is the error state for that control while the static guide still shows | — |
  | error | Switch: "Staffing didn't change. Try again." next to it; switch returns to its last known state. Reset: "The reset didn't finish. Nothing was half-reset; try again." (depends on CON-9 being all-or-nothing, see contract needs). Status read: "Staffing status is unavailable." with retry | CON-7, CON-9 errors |
  | stale | Staffing changed elsewhere (the supervisor ended the shift on SCR-7): on focus or every 10 s the state is re-read; if it changed, "Staffing changed since you opened this page." and the switch moves | CON-7 |
  | success | Switch on: "Simulated staff on shift (demo). The banner now shows on the chat and the console." Switch off with waiting customers: "Shift ended. 1 waiting customer now has the 1-business-day promise." Reset: "Demo reset. Bookings, cases and codes are back to the start, and the date is Fri Oct 16, 2026. Open chats have ended." | CON-7, CON-9 |
  | disabled | Switch disabled while a change is saving; reset button disabled while a reset runs ("Resetting…") | CON-7, CON-9 pending |

- Flow states: simulation on / off (FLOW-8, FLOW-12) → success; shift ended with live-queued customers → success with the converted count; reset during a live chat (FLOW-12) → success line includes "Open chats have ended."
- Interactions: the switch puts CON-7; reset opens a confirm dialog ("Reset the demo? This ends every open chat, clears cases made during the demo, restores the seeded cases and sets the date back to Fri Oct 16, 2026.") with "Reset the demo" and "Cancel"; Cancel has focus by default. Links open the chat in this tab and the console in a new tab. The role switch in the header changes role in one click (CON-10) and this page stays; sign out goes to SCR-12.
- Copy notes: neutral styling for every demo element (R2-3). The word "simulated" is used for staffing, the date, codes and follow-ups, never for the assistant. No claim that anyone at Meridian is online.
- Accessibility notes: the switch is a native checkbox with `role="switch"` and a visible label; results announce politely; the confirm is a native `<dialog>` with focus trapped and returned to the reset button; targets 44 × 44 px.
- Contracts: CON-7, CON-8, CON-9, CON-10, CON-22

### SCR-4 · Role switch
- Purpose: let the reviewer, already signed in at SCR-12, switch between acting as the customer and acting as a representative, supervisor or business owner in one click from any screen, with no second password. It no longer signs anyone in (R-48).
- Stories: US-18, US-22, US-24, US-25, US-28 · Flows: FLOW-8, FLOW-9, FLOW-10, FLOW-11, FLOW-12
- Route: no route of its own as a control: it lives in the **shared header of every screen**. An optional full page at `/role` (proposed, behind the login) explains each role and holds the same four choices.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Switch (every screen) | Label "Acting as"; four segments: Customer · Representative · Supervisor · Owner (on a phone: Customer · Rep · Supervisor · Owner, full names kept in the accessible names); the current segment filled and ticked; "Sign out" beside it | CON-10 (current role, switch), CON-22 (sign out) |
  | R2 Role line (staff screens) | The console header's role name: "Riley · demo representative", "Demo supervisor", "Demo business owner" | CON-10 |
  | R3 Statement (full page) | "These are demo roles, not real accounts. There is no second password. Everything here is fictional." | none: static |
  | R4 Roles (full page) | Four buttons, each with one line: "Customer" (the chat, as a homeowner) · "Riley, demo representative" (the queue and cases; can claim, join, reply, log, flag) · "Demo supervisor" (urgent, unowned, due-soon, overdue and stuck cases; assigns; runs the demo shift and clock) · "Demo business owner" (outcomes and the cases behind them) | CON-10 |
  | R5 Foot (full page) | "Back to the demo guide" | none: static |

- Components: four-segment control (the same one in every header), role button (title + one line) on the full page, console header role line.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Four roles, the current one marked; the screen under it is unchanged | CON-10 (current role) |
  | empty | n/a: the four roles are fixed | — |
  | loading | The chosen segment shows "Switching…" and all four are disabled; the screen stays put until the answer arrives | CON-10 pending |
  | partial | n/a: a switch either changes the role or it doesn't | — |
  | error | "Couldn't switch role. Try again." under the control; the current role stays marked. A role the session may not use cannot occur (no passcode), so the only errors are transport or an ended session | CON-10 error |
  | stale | **Session ended:** the next call answers `UNAUTHENTICATED` and the screen goes to SCR-12 with "Your demo session ended, so please sign in again." **Staff screen opened while acting as the customer** (a bookmark or the browser's back button): the screen shows "You're acting as the customer. Switch to a staff role to see this." with the switch beside it and no staff data | CON-10 (`UNAUTHENTICATED`, `ROLE_NOT_ALLOWED`) |
  | success | Customer → SCR-1 (the same chat, resumed); Representative → SCR-5; Supervisor → SCR-7; Owner → SCR-9. On SCR-2, SCR-3, SCR-10 and SCR-11 the screen stays and only the role changes. The new role is marked and announced | CON-10 |
  | disabled | All four segments disabled while a switch is in flight; the current segment is not a button (it is marked, not pressable) | CON-10 pending |

- Flow states: switch role for FLOW-8, FLOW-9, FLOW-10, FLOW-11 → success; session ended or reset (FLOW-12) → stale (a reset ends open chats, keeps the login and sets the role back to customer; CON-9).
- Interactions: one click changes role (no menu to open first). Sign out ends the login session and goes to SCR-12. The role is held per browser tab [A], so a second tab can stay on another role.
- Copy notes: "demo" appears in every staff role name. No password field anywhere on this control (the password is on SCR-12 only). Labels on staff screens need no hint.
- Accessibility notes: the control is a `radiogroup` named "Acting as" with the four roles as radios (arrow keys move, a change is announced politely as "Now acting as Riley, demo representative"); it is the first control after the skip link in the header on every screen; targets ≥ 44 px tall (it is used on phones); the full page has one `h1`.
- Contracts: CON-10, CON-22 (sign out), CON-7, CON-8

### SCR-5 · Representative queue
- Purpose: show the representative what needs action, most urgent first, and the live queue while simulated staff are on shift.
- Stories: US-18, US-20 · Flows: FLOW-7, FLOW-8, FLOW-9, FLOW-12
- Route: `/staff/queue`, behind the demo login and a staff role (as the customer it shows the SCR-4 stale line). Laptop first.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Console header | "Meridian · Staff console"; "Riley · demo representative"; the role switch (SCR-4, current role marked); demo date and time; staffing word; staffing banner when on; nav (Queue · Review list); Sign out | CON-10, CON-22, CON-7, CON-8 |
  | R2 Live queue | Only while simulated staff are on shift: "Waiting in chat" rows, oldest first, P0/P1 on top: priority tag, reference, reason, customer, "Waiting since 2:14 pm" (a time, never a duration estimate), "Claim and join" | CON-11 |
  | R3 Needs my action | "Needs my action" with count; hint "Safety and danger first, then by due time."; rows: priority tag ("P0 · Safety"), "#MHC-C-0007", reason, customer name with initials disc, owner ("Unowned" or a name), due ("Mon Oct 19 · 7:00 pm"), "Overdue" with a clock icon when past due, "Waiting · wakes Tue 9:00 am" for Waiting cases, follow-up short form ("Phone · mornings"), "Demo seed" tag, "Brief being written" while the brief is pending | CON-11 |
  | R4 Keyboard hint | "J / K to move, Enter to open" (laptops only) | none: static |

- Components: console header, priority tag (a filled tag with its code and word, "P0 · Safety"), queue row (the selected row takes a darker tone and a thin edge), section head with count, tag. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Seeded rows: MHC-C-0008 P0 Safety unowned; MHC-C-0005 P3 refund, Overdue; MHC-C-0006 P3 conduct complaint; MHC-C-0007 P3 billing dispute, due Mon Oct 19 · 7:00 pm | CON-11 |
  | empty | "You're all caught up. No case needs your action. New handoffs from the chat appear here." | CON-11 (empty) |
  | loading | Header renders; five row-shaped skeletons | CON-11 pending |
  | partial | A row whose brief is still being written shows "Brief being written" in place of the follow-up line, and opens to a case page that says the same | CON-11 (`brief_status`) |
  | error | "The queue didn't load. Try again." with retry; header stays | CON-11 error |
  | stale | The list refreshes every 10 s and on focus. New or changed rows since the last read: a line "2 cases changed. Show them." that applies the update without moving the selected row; the demo clock moving (supervisor advanced time) re-computes Overdue on refresh | CON-11, CON-8 |
  | success | Returning from a resolved case: the row is gone and "MHC-C-0007 resolved." shows for 4 s; a claimed row shows "Claimed · Riley (demo)" | CON-11, CON-13 |
  | disabled | Nobody online: the live-queue region shows "Nobody is on shift, so there is no live queue. Turn on the simulation in the demo guide to try it." | CON-11 (`staffing`), CON-7 |

- Flow states: new handoff from the chat (FLOW-7) → stale then default; live-queued customer (FLOW-8) → R2 row; shift ended before claim (FLOW-8) → the row moves from R2 to R3 with the async promise and its original creation time; overdue after the clock advances (FLOW-10) → "Overdue" word; seeded demo cases → "Demo seed"; reset (FLOW-12) → seeds restored, live rows gone.
- Interactions: click or Enter opens SCR-6; J / K move the selection; "Claim and join" claims and opens SCR-6 with the live chat (CON-13 claim then CON-14 join, in that order). The role switch in the header changes role in one click (CON-10): Customer goes to SCR-1, another staff role to its home screen; sign out goes to SCR-12.
- Copy notes: due times 12-hour; "Overdue" is a word with an icon, never red, never a negative countdown; no wait estimates; priority word always beside the tag ("P1 · Danger", "P2 · Time-sensitive", "P3 · Standard", "P4 · Routine").
- Accessibility notes: the list is a `ul` of buttons with `aria-current` on the selected row; each row's accessible name reads in order "P0 safety, MHC-C-0008, gas smell reported in chat, unowned, no due time: safety"; the stale line is polite; J/K are additions, Tab still works; row height ≥ 44 px; P0 rows are not colour-coded red (ink weight and the word "Safety").
- Contracts: CON-11, CON-7, CON-8, CON-10, CON-13, CON-14, CON-22 (sign out)

### SCR-6 · Case view
- Purpose: let a representative understand a case in about a minute, check any fact against the record without losing the story, and act: claim, join and reply live, record contacts, wait, resolve, close, release or flag.
- Stories: US-19, US-20, US-21 (and the destination for US-18, US-22, US-23, US-24) · Flows: FLOW-8, FLOW-9, FLOW-10, FLOW-11
- Route: `/staff/cases/{reference}`. Laptop first; three columns ≥ 1100 px; queue drawer below; brief and evidence as tabs below 700 px.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Console header | As SCR-5 (role switch and Sign out included) | CON-10, CON-22, CON-7, CON-8 |
  | R2 Queue column / drawer | Compact SCR-5 list; the open case highlighted | CON-11 |
  | R3 Case header | "Billing dispute · P3 Standard"; the reference "MHC-C-0007"; the split button (see Interactions); headline "Due Mon Oct 19 · 7:00 pm" (or "No due time: safety" for P0); "Overdue" when past; "Created Fri Oct 16, 2:14 pm"; owner or "Unassigned, nobody owns it yet"; "Demo seed" | CON-12 |
  | R4 Lifecycle line | Unassigned → Claimed → In progress → Waiting → Resolved / Closed unresolved; Live-queued first on the staffed path; current state marked | CON-12 |
  | R5 Promise card | "Promise shown to the customer" + the exact text; cells Follow up by · Destination (on record / not on record) · Best time; promise status Open / Kept / Missed / Changed | CON-12 |
  | R6 Brief | Eight numbered sections, fixed headings (consolidated §5), facts with a source chip each; section 4 labelled "Customer says · not checked"; any section the fact check trimmed carries "Something here didn't match the record and was removed." | CON-12 |
  | R7 Action bar | Buttons for the current state (Interactions); "Flag"; reason / outcome / wake-up forms inline; activity log under it | CON-13, CON-14, CON-15, CON-16 |
  | R8 Evidence column | "Evidence" with the line "What the AI saw, next to what is true now"; tabs **Sources (n)** and **Conversation** | CON-12 |
  | R8a Sources | One card per pertinent source: title, file or record, version; a snapshot-vs-now table or the quoted passage; status "No change since the snapshot" or "Changed since the AI saw it: was $144.00, now $149.00" | CON-12 |
  | R8b Conversation | Full chat with speaker labels and times; when joined, the live box at the bottom: "You are replying as Riley (demo representative). The assistant is paused." + field + "Send" + "Hand back to the assistant" + "Close the chat" | CON-12, CON-14, CON-3 (customer messages while joined; see contract needs) |
  | R9 Other cases | "Other cases for this customer" by reference, status in words | CON-12 |

- Components: case header with due headline and split button, lifecycle line (the current state as a strong tag), promise card with label/value rows, brief section card (numbered, heading, sentence-case items, source chips; the claims section dashed and grey), source card, snapshot table, tab set, live box, action buttons (white with a hairline), inline forms, activity log. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | MHC-C-0007: header, Unassigned, promise card with "Phone, his choice (email is our default) · the number on his record, ending 02 · mornings", eight sections, "Claim" as the split button's main segment, Sources tab open | CON-12 |
  | empty | No case selected (the route opened without a reference, or after a resolve): centre column "Pick a case from the queue." Evidence column hidden. A brief section with nothing to say reads "Nothing recorded." rather than disappearing (headings are fixed) | CON-11, CON-12 |
  | loading | Header and eight section skeletons in final layout; evidence column skeleton; buttons disabled | CON-12 pending |
  | partial | **Brief still being written:** header, promise and conversation show; the brief area says "The brief is being written. The conversation is complete." **Source unavailable:** that source card reads "This record can't be read right now; the snapshot is shown alone." **Fact check trimmed a section:** the section shows its flag line | CON-12 (`brief_status`, per-source `current_unavailable`, per-heading `trimmed`) |
  | error | Case not found: "No case MHC-C-0099. It may have been cleared by a demo reset." + "Back to the queue". Owner role: the case opens **read-only** (no action buttons; a quiet line "Read-only for the business owner role") — every staff role may read cases (FLOW-11; CON-12, settled 2026-10-21). An action failed: message under the action bar, e.g. "Waiting needs a wake-up time." / "Add a reason to release this case." / "Resolving needs an outcome." | CON-12 errors, CON-13 `REASON_REQUIRED`, `WAKE_UP_REQUIRED`, `OUTCOME_REQUIRED`, `NOT_ALLOWED_IN_STATE` |
  | stale | **Changed since:** a source whose current value differs from the snapshot shows "Changed since the AI saw it" with both values, and the brief fact's source chip carries a "changed" mark. **Case changed by someone else:** an action returns a version conflict: "This case changed since you opened it (claimed by the demo supervisor at 2:31 pm). Reload to see it." with "Reload" | CON-12 (`changed_since`), CON-13 `VERSION_CONFLICT` (409) |
  | success | Claim: "Claimed · Riley (demo)", lifecycle moves, "Log a call" enabled. Contact logged: activity "Called ···02 · Reached the customer · Demo: recorded, not sent". Resolved: outcome recorded, promise "Kept" (or "Missed" if past due), redirect to the queue with the success line. Flag: "Added to the review list." | CON-13, CON-15, CON-16 |
  | disabled | "Join chat" disabled unless the case is live-queued and staff are on shift: "Join chat works only while the customer is waiting in a live chat." "Log a call / email", "Set waiting", "Resolve", "Close unresolved" disabled until claimed: "Claim the case first." Assign and priority controls hidden for the representative role. Live box disabled after hand-back or close | CON-12 (`allowed_actions`) |

- Flow states:

  | Flow state | Flow | State column | What it looks like | Contract |
  |---|---|---|---|---|
  | Live-queued case | FLOW-8 | default | Lifecycle on "Live-queued"; primary button "Claim and join"; header line "The customer is waiting in the chat since 2:14 pm." | CON-12 |
  | Joined, AI paused | FLOW-8 | success | Conversation tab opens with the live box; header "Live · you are replying · assistant paused" | CON-14, CON-3 |
  | Handed back | FLOW-8 | success | Event in the conversation "Handed back to the assistant at 2:22 pm"; lifecycle In progress; live box disabled | CON-14 |
  | Chat closed | FLOW-8 | success | "Chat closed at 2:23 pm"; next buttons Resolve / Close unresolved | CON-14 |
  | Customer chat ended by reset | FLOW-12 | error | Live box: "This chat ended because the demo was reset." Case page then 404s on reload | CON-14 `NOT_LIVE`, CON-3 |
  | Shift ended before claim | FLOW-8 | stale | Case returns to Unassigned with the async promise; promise card shows the new text with status "Changed" and the reason "Shift ended before a claim" | CON-12 |
  | Waiting | FLOW-9 | success | Lifecycle on Waiting; header "Wakes Tue Oct 20 · 9:00 am" | CON-13 |
  | Stuck waiting | FLOW-10 | stale | Header "Wake-up time passed (Tue 9:00 am). Pick it back up." | CON-12 |
  | Overdue | FLOW-9, FLOW-10 | stale | Due headline followed by "Overdue" with a clock icon; promise status turns "Missed" only when the case closes past due | CON-12 |
  | Released | FLOW-9 | success | Back to Unassigned; reason in the activity log | CON-13 |
  | Changed since | FLOW-9 | stale | As in the state table | CON-12 |
  | Fee-bearing change request | FLOW-6 | default | Section 2 holds the wanted time; section 3 the booked appointment and the windows shown (not held) as facts; P2; due headline is the window start ("Due Fri Oct 16 · 12:00 pm, the window start") | CON-12 |
  | Safety case | FLOW-2 | default | P0; "No due time: safety"; section 1 holds the trigger words, the instruction shown and its time; section 8 "No account match needed for safety." | CON-12 |
  | Seeded demo case | FLOW-10 | default | "Demo seed" tag in the header; everything else normal | CON-12 |
  | Assign or reprioritise (supervisor) | FLOW-10 | success | Owner or priority changes with the reason in the log | CON-13 |

- Interactions:
  - The role switch in the header changes role in one click (CON-10) from here: Customer goes to SCR-1 (the same chat, resumed), another staff role to its home screen. A joined live chat stays joined; the switch never hands the chat back by itself.
  - Placement (A5, design.md §8.9): the case header carries one emerald split button: **Claim** (**Claim and join** when live-queued), then **Resolve** once the case is claimed, its menu holding Release, Set waiting and Close unresolved; the other actions (Log a call, Log an email, Flag, and for a supervisor Assign / Change priority) are buttons in the action bar under the brief. While a chat is live the live box's Send is the one action. Where each action sits changes nothing about when it is allowed.
  - Buttons by state: Unassigned → Claim (and, if live-queued, Claim and join). Claimed / In progress → Log a call, Log an email, Set waiting (wake-up time required), Resolve (outcome required), Close unresolved (reason required), Release (reason required). Live → Send, Hand back to the assistant, Close the chat. Always → Flag. Supervisor → Assign / Reassign, Change priority (reason required).
  - A source chip in the brief scrolls the evidence column to that source and highlights it for 1.2 s (none under reduced motion); on a phone it switches to the Evidence tab first.
  - Brief section index (1–8) jumps to a section.
  - Flag opens an inline form: what is wrong ("An answer was wrong", "The brief left something out", "The escalation was not needed"), optional note, "Add to review list".
  - Log a call opens: outcome (Reached the customer / No answer / Left a message), note, "Record"; the activity reads "Demo: recorded, not sent". No call is placed.
- Copy notes: the eight headings exactly as consolidated §5; facts and claims never mixed; a visible "Customer says · not checked" tag on section 4; promise text quoted exactly as shown to the customer; identity line "He entered the code sent to the phone on file. (Demo simulation. Not real ID proof.)"; times 12-hour; "Overdue" never red; activity label "Demo: recorded, not sent" (R-34); no wording that judges the customer ("$149, not $144" is a fact; "overcharged" never appears).
- Accessibility notes:
  - Landmarks: `nav` (queue), `main` (brief, one `h1` = case title), `aside` (evidence). Brief sections are an ordered list with `h3` headings.
  - Focus order: header → promise → brief → action bar → evidence tabs → queue (the queue is reachable by a skip link "Go to queue"). After an action, focus moves to its result line.
  - Tabs follow the ARIA tab pattern (arrow keys between tabs). The live box has a visible label; incoming customer messages are announced politely; "assistant paused" state is text, not colour.
  - Targets ≥ 24 × 24 px minimum with 32 px buttons on laptops; ≥ 44 px on phone width.
  - Snapshot tables use `th scope` for field, snapshot and now; "Changed since" is text plus an icon.
- Contracts: CON-12, CON-13, CON-14, CON-15, CON-16, CON-21 (staff-side live stream: customer messages, controller changes), CON-11, CON-3, CON-10, CON-7, CON-8, CON-22 (sign out)

### SCR-7 · Supervisor oversight
- Purpose: at shift start, show every P0/P1, overdue, due-soon, unowned and stuck-waiting case with owner, age and follow-up preference, let the supervisor assign or reprioritise with a reason, and run the demo's shift and clock.
- Stories: US-22, US-23 · Flows: FLOW-8, FLOW-10
- Route: `/staff/oversight`.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Console header | As SCR-5, role "Demo supervisor" (role switch shows Supervisor current); nav (Oversight · Review list · Queue) | CON-10, CON-22, CON-7, CON-8 |
  | R2 Demo controls | "Demo controls" strip: "Simulated shift: off / on" switch; "Advance simulated time" with "+1 hour", "+4 hours", "Next business morning (Mon 7:00 am)"; the current demo time "Fri Oct 16 · 2:20 pm" | CON-7, CON-8 |
  | R3 Alerts | Decision lines, newest first (examples in copy notes) | CON-17 |
  | R4 Lanes | P0 and P1 · Overdue · Due soon · Unowned · Stuck waiting, fixed order; each with a count and rows: priority tag, reference, reason, owner, age ("Open 2 h 6 min", from the demo clock), due, follow-up preference, "Assign" | CON-17 |
  | R5 Live queue line | While staffed: "2 customers waiting in chat." No estimate | CON-17 |
  | R6 Review list link | "Review list · 3 new flags" | CON-16 |
  | R7 Assign dialog | Owner choice (Riley (demo) · Demo supervisor), required reason, "Assign"; Change priority: P0–P4 with words, required reason | CON-13 |

- Components: switch, three advance buttons, alert line, lane (header + count + compact rows), dialog. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Seeds: P0 MHC-C-0008 in "P0 and P1"; MHC-C-0005 in "Overdue"; MHC-C-0006 and MHC-C-0007 in "Unowned"; alert "P0 safety case MHC-C-0008 created at 2:16 pm, unowned. Assign it." | CON-17 |
  | empty | All lanes empty: "Nothing urgent, unowned, due soon, overdue or stuck. Every case has an owner and is on time." A single empty lane shows "None" under its header (it stays, so the order never shifts) | CON-17 |
  | loading | Demo controls and lane headers render; row skeletons | CON-17 pending |
  | partial | n/a: one oversight read returns every lane together (CON-17); there is no half-loaded lane to show | — |
  | error | "Oversight didn't load. Try again." Advance failed: "The clock didn't move. Try again." Assign without a reason: "Add a reason to assign this case." | CON-17, CON-8, CON-13 errors |
  | stale | Refresh every 10 s and on focus; after an advance the lanes re-read at once; changes since the last read: "Lanes updated." | CON-17 |
  | success | Advance: "Demo time is now Mon Oct 19 · 7:00 am. 1 case became overdue." and the case moves lanes. Shift ended: alert "Simulated shift ended with 1 customer waiting. Their case now has the 1-business-day promise." Assigned: row shows the owner and leaves "Unowned" | CON-8, CON-7, CON-13 |
  | disabled | Advance buttons and switch disabled while saving; "Assign" disabled until a reason is typed; time cannot move backwards (only reset does that, on SCR-3), so there is no "back" button, with the line "To go back to Fri Oct 16, reset the demo." | CON-8, CON-13 |

- Flow states: advance time and a seeded case turns overdue (FLOW-10) → success; end the shift with someone live-queued (FLOW-8 error branch) → success + alert; P0/P1 case created → alert; stuck waiting → lane row; seeded demo cases → "Demo seed" tag.
- Interactions: row opens SCR-6; "Assign" opens the dialog; the switch and advance buttons act at once (no confirm; they are reversible by reset and labelled demo). The role switch in the header changes role in one click (CON-10): Customer goes to SCR-1, another staff role to its home screen; sign out goes to SCR-12.
- Copy notes: alerts are decision lines: what happened + what to do ("Assign it.", "Pick it back up."). Ages and due times 12-hour; "Overdue" never red. The demo controls strip is neutral and labelled "Demo".
- Accessibility notes: lanes are `section`s with `h2` headers including counts; alerts list is polite on change; the dialog is a native `<dialog>` with the reason field required (`aria-required`); buttons ≥ 32 px on laptops, 44 px at phone width.
- Contracts: CON-17, CON-13, CON-7, CON-8, CON-16, CON-10, CON-22 (sign out)

### SCR-8 · Review list of flags
- Purpose: list what staff flagged as AI mistakes so a person decides each fix; nothing here changes the knowledge base.
- Stories: US-21, US-23 · Flows: FLOW-9, FLOW-10
- Route: `/staff/flags`.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Console header | As SCR-5 (role switch and Sign out included) | CON-10, CON-22, CON-7, CON-8 |
  | R2 Statement | "Nothing on this list changes the knowledge base, prompts or tests. People decide each fix." | none: static |
  | R3 Flags | Newest first: kind (Answer · Brief · Escalation), reason, case reference link, "Open the message" link, flagged by, when, status New / Reviewed, optional note; "Mark reviewed" | CON-16 |

- Components: table on laptops, stacked rows on phones; status word; inline expand for the flagged message text. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Rows, New first within date | CON-16 |
  | empty | "No flags yet. Staff flag a wrong answer, a brief that left something out, or an escalation that wasn't needed, from any case." | CON-16 (empty) |
  | loading | Header and statement render; row skeletons | CON-16 pending |
  | partial | n/a: each flag is stored whole with its case and message references | — |
  | error | "The review list didn't load. Try again." | CON-16 error |
  | stale | Refresh on focus; "1 new flag since you opened this page. Show it." | CON-16 |
  | success | "Marked reviewed." and the status word changes | CON-16 |
  | disabled | For the representative role, "Mark reviewed" is disabled with "Supervisors mark flags reviewed." | CON-16, CON-10 |

- Flow states: flag added from SCR-6 (FLOW-9) → stale/default; reviewed (FLOW-10) → success; reset (FLOW-12) → empty.
- Interactions: reference opens SCR-6; "Open the message" opens SCR-6 on the Conversation tab at that message; "Mark reviewed" with an optional note. The role switch in the header changes role in one click (CON-10): Customer goes to SCR-1, another staff role to its home screen; sign out goes to SCR-12.
- Copy notes: no word suggesting an automatic fix ("learned", "updated the model"). Times 12-hour.
- Accessibility notes: table with `th scope`; row actions are buttons with the reference in their accessible name ("Mark flag on MHC-C-0007 reviewed"); status is text.
- Contracts: CON-16, CON-12, CON-10, CON-22 (sign out)

### SCR-9 · Business-owner outcomes
- Purpose: show whether the AI cuts load without hurting customers, from stored data only, with every number opening its cases.
- Stories: US-24 · Flows: FLOW-11
- Route: `/staff/owner`.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Console header | As SCR-5, role "Demo business owner" (role switch shows Owner current) | CON-10, CON-22, CON-7, CON-8 |
  | R2 Headline tiles | An **estimate** of in-scope correct resolution, labelled "Estimate from live chats (no verified answers)", with a link to the measured number from the latest held-out eval run (SCR-11, CON-20), "n of N in-scope conversations"; promises kept on time "n of N promises due"; handoffs "n of N conversations". Each tile: the rate large, the denominator line under it, a link "Open the cases" | CON-18 |
  | R3 Basis line | "From stored conversations and cases, as of Fri Oct 16 · 2:20 pm (demo time). Includes 4 demo seed cases. These are not targets." | CON-18 |
  | R4 Outcomes table | Resolved by the AI · Escalated, resolved by staff · Escalated, still open · Abandoned · Failed; count and share of N | CON-18 |
  | R5 Handoffs by reason | Reason, count, "Open the cases" | CON-18 |
  | R6 Missed promises | References, due time, outcome | CON-18 |
  | R7 Cases behind a number | Inline list of references with reason and status, each opening SCR-6 | CON-18, CON-12 |
  | R8 Health link | "System health is on the Monitoring page. Evaluation results are on the Evaluation page." | none: static |

- Components: tile (rate, denominator, link), table, inline case list. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | Tiles, basis line, tables | CON-18 |
  | empty | No conversations since the reset: "No outcomes yet. Numbers appear once conversations end. Nothing here is a target." Tiles show "—" with "0 conversations" | CON-18 (zero denominators) |
  | loading | Tile and table skeletons | CON-18 pending |
  | partial | A measure with no denominator yet shows "—" and the reason ("No promises are due yet."), while the others show numbers | CON-18 (per-measure nulls) |
  | error | "Outcomes didn't load. Try again." | CON-18 error |
  | stale | The demo clock has moved past the basis time: "These numbers are as of 2:20 pm; the demo time is now Mon 7:00 am. Refresh." | CON-18 (`as_of`), CON-8 |
  | success | n/a: the page is read-only; opening cases is navigation, not an action with a result | — |
  | disabled | A number with a zero denominator is not a link: "No cases to open." | CON-18 |

- Flow states: owner opens the cases behind a number (FLOW-11) → R7 list → SCR-6; seeded demo cases counted and named in the basis line; a missed promise after the clock advances → R6 row.
- Interactions: "Open the cases" expands R7 in place; a reference opens SCR-6. The role switch in the header changes role in one click (CON-10): Customer goes to SCR-1, another staff role to its home screen; sign out goes to SCR-12.
- Copy notes: every rate has its denominator in words; a handoff is never called containment; seeds are named; "Not a target" stays on the basis line.
- Accessibility notes: each tile is a `section` with an `h2`; rates are text, not only a chart; the inline list announces its count when opened; tables with `th scope`.
- Contracts: CON-18, CON-12, CON-10, CON-8, CON-22 (sign out)

### SCR-10 · Monitoring
- Purpose: show whether the system is healthy (volume, failures, latency, spend, restarts) and, kept apart, whether it is correct, with alerts as decision lines on the page.
- Stories: US-27 · Flows: FLOW-11
- Route: `/monitoring`. Behind the demo login, readable in any role (R-48 reversed the SITEMAP proposal of open access; redacted aggregates only). Without a session it answers `UNAUTHENTICATED`.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Header | "Monitoring · Is it running, and is it right?"; the shared header's role switch and Sign out; data-age line "Updated [time] (demo time) · redacted · traces are not shown here" | CON-19, CON-10, CON-22 |
  | R2 Alerts | Firing first, then quiet ones; each a decision line, e.g. "p95 latency is over 12.5 s per turn: check the model route." · "Spend reached the $30 daily cap: new chats hand off and no model calls run until tomorrow." (Alert at the cap only; no early warning is approved, DO-6/DO-7) · "The health check restarted the service at [time]: check the logs." | CON-19 |
  | R3 Health | Volume (conversations, turns) · Failures (count and share) · Latency p50 and p95 · Spend today against the $30 cap · Last health-check restart | CON-19 |
  | R4 Correctness | Containment as an **estimate** of correct resolution from live chats (labelled so; the measured number is on SCR-11), with denominator · Escalations by reason | CON-19 |
  | R5 Definitions | What each measure counts | none: static |

- Components: alert line, metric tile with unit and denominator, bar for spend against the cap (with the numbers in text). The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | All groups with values | CON-19 |
  | empty | "No conversations since the last reset, so there is nothing to measure yet." Health tiles show "—"; the restart line still shows | CON-19 (zero volume) |
  | loading | Tile skeletons | CON-19 pending |
  | partial | Latency shows "Not enough turns yet (fewer than 20)" while volume and spend show values; any measure the service couldn't compute says why | CON-19 (per-measure nulls with reason) |
  | error | "Monitoring didn't load. Try again." | CON-19 error |
  | stale | Auto-refresh every 30 s while visible; if the data is older than 2 minutes, "This data is [n] minutes old." | CON-19 (`as_of`) |
  | success | n/a: read-only page with no actions | — |
  | disabled | n/a: no controls on this page | — |

- Flow states: alerts firing (FLOW-11) → R2; spend cap reached → alert line; reset (FLOW-12) → empty.
- Interactions: none beyond refresh and reading definitions. The role switch in the header changes role in one click (CON-10) and the page stays; sign out goes to SCR-12.
- Copy notes: health and correctness never share a row or tile group (R-35); no codes, card-like numbers or names anywhere (R-36); no trace links; alert lines say what to do; no invented example numbers in the build: values come only from CON-19.
- Accessibility notes: groups are `section`s with `h2` "Health" and "Correctness"; the spend bar has its values in text; auto-refresh changes are not announced except a newly firing alert (polite).
- Contracts: CON-19, CON-10, CON-22

### SCR-11 · Evaluation report
- Purpose: show the latest evaluation run honestly: the headline from the sealed held-out split, dev-split numbers labelled as dev, each with its denominator, run and date.
- Stories: US-27 · Flows: FLOW-11
- Route: `/eval`. Behind the demo login, readable in any role (R-48 reversed the SITEMAP proposal of open access). Without a session it answers `UNAUTHENTICATED`.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R0 Header | The shared header's role switch and Sign out | CON-10, CON-22 |
  | R1 Headline | Correct-resolution rate from the held-out split, "n of N held-out cases"; "Held-out split: scored only, never tuned against."; run ID and date | CON-20 |
  | R2 Run identity | Run ID, date, split sizes (dev, held-out), test-set size and mix summary (transcript-derived vs labelled synthetic) | CON-20 |
  | R3 Measures | Per split: accuracy on handled drivers · escalation recall (out of scope) · false escalation (in scope) · wrong-answer rate · retrieval hit rate (top 3) · safety-first gate · request-honoured gate · promise consistency; each "n of N" | CON-20 |
  | R4 Test-set mix | By category, in proportion to the corpus; synthetic cases labelled with what they test | CON-20 |
  | R5 Dev failures | Redacted examples from the dev split only | CON-20 |

- Components: headline tile, run line, measures table with split columns, mix table. The shared header's role switch (SCR-4: "Acting as" with four roles, the current one marked, plus Sign out) is part of the header on this screen.
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | All regions from the latest run | CON-20 |
  | empty | "No evaluation run yet. When one runs, its results appear here with their test set. No number is shown before then." | CON-20 (no run) |
  | loading | Skeletons | CON-20 pending |
  | partial | Only a dev run exists: the headline reads "No held-out run yet." and the dev column shows, labelled "Dev (we read and fixed these, so it overstates)" | CON-20 (per-split presence) |
  | error | "The evaluation report didn't load. Try again." | CON-20 error |
  | stale | The run predates the current agent or knowledge-base version: "This run used an earlier version of the agent ([run version]); the deployed version is [current]." | CON-20 (`agent_version`, `current_version`) |
  | success | n/a: read-only page | — |
  | disabled | n/a: no controls | — |

- Flow states: reviewer reads the latest run (FLOW-11) → default; held-out not yet scored → partial; agent changed since the run → stale.
- Interactions: none beyond reading; measures expand to their definitions. The role switch in the header changes role in one click (CON-10) and the page stays; sign out goes to SCR-12.
- Copy notes: a target (60–75%, ≥ 90%) never appears as a result; if a target is shown at all, it is labelled "Target" in its own column. Every number has "n of N". Dev numbers always carry the dev label.
- Accessibility notes: one `h1`; the measures table has a caption naming the run; split columns have `th scope="col"`; nothing depends on colour.
- Contracts: CON-20, CON-10, CON-22

### SCR-12 · Demo login
- Purpose: the entry to the whole deployment. One shared demo username and password (from Railway variables, given to the reviewer in the README) open the customer chat, the staff console, the demo controls, monitoring and the evaluation report. It says plainly that this is a demonstration, not a Meridian account.
- Stories: US-25, US-28 · Flows: FLOW-12
- Route: `/login`. The only route, with `/healthz`, that answers without a session. Every other route answers `UNAUTHENTICATED` and sends the visitor here. Phone first, one column.
- Regions and content:

  | Region | Content | Contract |
  |---|---|---|
  | R1 Header | Brand mark and "Demo access"; the statement "This is a demonstration of Meridian's assistant. These are not Meridian accounts, and everything here is fictional." | none: static |
  | R2 Message line | Empty by default. Holds the one refusal sentence, the session-ended line or the already-signed-in line (see states) | CON-22 |
  | R3 Form | "Username" (hint "From the README"); "Password" (hint "From the README"); "Show password" checkbox; "Sign in" (the one emerald button) | CON-22 |
  | R4 Foot | "The username and password are in the README that came with the submission." Never the values | none: static |

- Components: Meridian-neutral card (no Meridian logo treatment that could pass as a real sign-in), two text fields with hint lines, checkbox, primary button, message line (neutral, not red: red stays on the safety card).
- States:

  | State | What it looks like | Comes from |
  |---|---|---|
  | default | The form with both fields empty; focus on Username | none: static |
  | empty | n/a: nothing is listed; the empty form is the default state | — |
  | loading | The button reads "Signing in…"; both fields read-only | CON-22 pending |
  | partial | n/a: a login is accepted or refused; there is no half-signed-in state | — |
  | error | **Refused:** one line in R2, whatever the cause (wrong username, wrong password, too many tries): "That username or password didn't work. Check the README and try again." The password field is cleared, the username kept, focus on Password. **Can't reach the server:** "Couldn't reach the demo. Try again." (this one is about the network, not the login) | CON-22 `LOGIN_FAILED`, transport error |
  | stale | **Sent back from another screen after the session ended:** "Your demo session ended, so please sign in again." After sign-in the visitor lands on the page they asked for. **Opened while already signed in:** "You're already signed in. Continue to the demo, or sign out." with "Continue" and "Sign out" and the form hidden | CON-22 (`UNAUTHENTICATED`, current session) |
  | success | Redirect: to the page that was asked for, else SCR-1 as the customer (role = customer). No separate success screen | CON-22 |
  | disabled | "Sign in" is disabled while either field is empty and while a sign-in is in flight; the fields are read-only while in flight | CON-22 pending |

- Flow states: first visit (FLOW-12) → default; wrong login (FLOW-12) → error; session expired on any screen (every flow) → stale; signed in already → stale (continue or sign out).
- Interactions: Enter submits. The username and password are never echoed into the URL or the page. The three refusal causes give the same sentence, the same timing and the same field handling, so nothing reveals which part was right. "Show password" toggles the field type and nothing else.
- Copy notes: plain and honest: "Demo access · this is a demonstration of Meridian's assistant" and never "staff login", "customer portal" or "Meridian account". No "Forgot password", no "Create account", no "Need help?". The credentials are in the README only, as placeholders there (`<DEMO_USERNAME>`, `<DEMO_PASSWORD>`) until the real ones are set in Railway; this screen, its hints and its screenshots never show a value. A2/A5 wording: sentence case, name line style, emerald is the one action.
- Accessibility notes: one `h1` "Demo access"; the fields are labelled, with `autocomplete="username"` and `autocomplete="current-password"` so a password manager works; the message line is an `aria-live="polite"` region and the error also sets `aria-invalid` on both fields with the message as their description; the button is a real `<button type="submit">`; targets ≥ 44 px; the page works with the keyboard alone and reads in order statement → message → form.
- Contracts: CON-22

---

## Flow-state coverage (what the brief asked to be visible, and where it is)

| Required state | Screen(s) | State column |
|---|---|---|
| Safety takeover | SCR-1 (card, strip, panel); SCR-5 / SCR-7 (P0 row, alert); SCR-6 (P0 case) | success · default |
| Code wrong / expired / locked | SCR-1 code card; SCR-2 "Expired" / "Used" | error · stale |
| Slot taken | SCR-1 slot card | error |
| Out of area | SCR-1 | error |
| Fee-bearing change request | SCR-1 change-request card and *Your visit*; SCR-6 P2 case due at the window start | success · default |
| Nobody online vs simulated staff | SCR-1 demo bar and banner; SCR-3 switch; SCR-5 live queue (disabled when nobody online); SCR-7 controls | default · disabled · success |
| AI paused / representative joined / handed back | SCR-1 event lines and top bar; SCR-6 live box | success |
| Limit reached | SCR-1 limit notice (rate, booking cap, spend cap) | error |
| Stale data ("changed since") | SCR-6 Sources; SCR-1 stream reconnect; SCR-2 expiry; SCR-5/7/8 refresh; SCR-9 as-of; SCR-10 data age; SCR-11 run version | stale |
| Overdue | SCR-5 row; SCR-6 header; SCR-7 lane; SCR-9 missed promises | default · stale |
| Seeded demo cases | SCR-5, SCR-6, SCR-7 "Demo seed"; SCR-9 basis line | default |
| Reset during a live chat | SCR-1 ended notice; SCR-6 live box; SCR-3 success line (the login and role are kept) | disabled · error · success |
| Wrong login; session ended | SCR-12 error and stale; SCR-4 stale; SCR-1 session-ended event | error · stale |

## State matrix

Cell text is the short name of what shows; **n/a** cells give their reason in the card.

| Screen | default | empty | loading | partial | error | stale | success | disabled |
|---|---|---|---|---|---|---|---|---|
| SCR-1 Chat | greeting, nobody online | greeting is the empty state | starting / replying line | part answered; follow-up unsaved | send failed; code, area, slot, limit | stream reconnecting; windows not held | booked, verified, handoff, saved | send, taken rows, ended chat; person button never |
| SCR-2 Inbox | newest code | no codes yet | skeleton | n/a | didn't load | expired / used, new code | copied | copy on used / expired |
| SCR-3 Demo guide | guide + switch | n/a | checking staffing | n/a | switch / reset failed | staffing changed elsewhere | sim on/off, reset done | saving, resetting |
| SCR-4 Role switch | four roles, current marked | n/a | switching | n/a | couldn't switch | session ended / staff screen as customer | lands on the role's home | segments during a switch |
| SCR-5 Queue | seeded rows | all caught up | row skeletons | brief being written | didn't load | cases changed | resolved / claimed | no live queue when nobody online |
| SCR-6 Case | brief + Claim | no case picked; "Nothing recorded." | section skeletons | brief pending; source unreadable; trimmed section | not found; not allowed; reason missing | changed since; version conflict | claimed, logged, resolved, flagged | join / act before claim |
| SCR-7 Oversight | lanes + alert | nothing left | lane skeletons | n/a | didn't load; clock; reason | lanes updated | advanced; shift ended; assigned | saving; no back-in-time |
| SCR-8 Review list | flags | no flags yet | skeletons | n/a | didn't load | new flag | marked reviewed | mark reviewed for rep |
| SCR-9 Owner | tiles + tables | no outcomes yet | skeletons | some measures "—" | didn't load | clock moved past as-of | n/a | zero-denominator links |
| SCR-10 Monitoring | groups + alerts | nothing to measure | skeletons | too few turns | didn't load | data age | n/a | n/a |
| SCR-11 Evaluation | latest run | no run yet | skeletons | dev only | didn't load | run predates agent | n/a | n/a |
| SCR-12 Demo login | form, fields empty | n/a | signing in | n/a | one refusal line; unreachable | session ended / already signed in | redirect to the page asked for, else the chat | button until both fields filled; fields in flight |

**Count:** 96 cells (12 screens × 8 states; SCR-12 added by R-48): **82 real states, 14 n/a.** The n/a cells: SCR-2 partial; SCR-3 empty, partial; SCR-4 empty, partial; SCR-7 partial; SCR-8 partial; SCR-9 success; SCR-10 success, disabled; SCR-11 success, disabled; SCR-12 empty, partial.

---

## Contract needs raised by the screen specs

These are states the screens above must show that the one-line UX-1 drafts do not yet carry. They are requests for
the parallel `UI_CONTRACTS.md` / OpenAPI work and the System track; this file does not edit either.

| # | Contract | What the screen needs | Why (screen and state) |
|---|---|---|---|
| N-1 | CON-3 | Event types beyond the draft: `staffing_changed`, `clock_changed`, `demo_reset`, `shift_ended` (carrying the async promise and the same reference), plus `representative_joined`, `representative_message`, `ai_paused`, `handed_back`, `chat_closed`. The stream must be open on **every** chat, not only in FLOW-8 | SCR-1 header and demo bar must not stay "Nobody online" after the reviewer turns the simulation on in another tab; reset during a live chat |
| N-2 | CON-3 | Resumable delivery: an event ID and replay of missed events after a reconnect | SCR-1 stale state ("Reconnecting…") without losing Riley's messages |
| N-3 | CON-3 or CON-14 | A staff-side stream (or a read) of the customer's messages for a joined case | SCR-6 live box: CON-14 is write-only in the draft, so the representative cannot see replies arrive |
| N-4 | CON-1, CON-2 | A `settled` object in every reply (visit, request with promise text and due, follow-up choice, identity status, controller), so the panel and strip render from the contract, not from client inference | SCR-1 R4 in every state |
| N-5 | CON-2 | Speaker on every block (`assistant`, `customer`, `representative` + display name, `event`) and a time | SCR-1 label on every message (R3-1) |
| N-6 | CON-2 | Reply block types beyond the draft list: `burning_check`, `conditional_safety`, `emergency_line`, `quick_checks`, `urgency_questions`, `where_prompt`, `locate_prompt`, `appointment`, `cancelled`, `live_queued`, `failure_offer`, `no_info`, `session_ended`; and the code prompt's sub-states `sent`, `wrong` (`attempts_left`), `expired`, `locked` with the masked hint only | SCR-1 flow states |
| N-7 | CON-2 | Named errors: `SLOT_TAKEN` (with fresh windows), `OUT_OF_AREA`, `CODE_WRONG`, `CODE_EXPIRED`, `CODE_LOCKED`, `NOT_VERIFIED` (identical for no match, ambiguous, no contact), `RATE_LIMITED`, `BOOKING_CAP`, `SPEND_CAP_REACHED`, `SESSION_ENDED` | SCR-1 error states; `NOT_VERIFIED` must not differ between causes (R-16) |
| N-8 | CON-2 | A write result flag per turn (`write: booked / moved / cancelled / none`) so completion wording appears only with a write | SCR-1 success (R-46) |
| N-9 | CON-4 | Works while CON-2 is rate-limited or spend-capped (no model call), idempotent per session (a second tap returns the open case, `already_open`), and returns either the async promise or `live_queued` | SCR-1: "Talk to a person" is never disabled |
| N-10 | CON-5 | Destination options masked ("the number ending in 02", "the address on your account"), an `on_record` flag, window options, and a general-only mode for unverified customers | SCR-1 follow-up chooser; SCR-6 promise stub (R-27) |
| N-11 | CON-6 | Per message: `expires_at`, `status` (active, used, expired), masked recipient; **scoped to the requesting browser's demo session**, so two reviewers at once never see each other's codes | SCR-2 stale and disabled states; privacy |
| N-12 | CON-7 | On ending the shift, the count of live-queued cases converted to the async promise | SCR-3 and SCR-7 success lines |
| N-13 | CON-8 | Advance steps (+1 hour, +4 hours, next business morning), the new time, and how many cases became overdue; no backwards move | SCR-7 success and disabled |
| N-14 | CON-9 | All-or-nothing reset, the number of open chats ended. **R-48 change:** the reset keeps the login session and the current role (the reviewer who resets is not thrown to SCR-12); it ends open chats and clears case-store state only. Needs the session | SCR-3 error/success, SCR-1 ended notice |
| N-15 | CON-10 | **Role switch (R-48, UXR-27):** read the current role; switch among `customer`, `representative`, `supervisor`, `owner` with no passcode; the role list with display names and what each sees. Needs the login session. The switch is a label, not security; the login (CON-22) is the only gate | SCR-4 all states; the shared header on every screen |
| N-16 | CON-11 | Row fields: priority and word, reference, reason, customer display name, owner, `due_at`, due state (on time / due soon / overdue), wake-up time, lifecycle state, follow-up short form, `seed`, `brief_status`; live rows with `queued_at` and no estimate; the current staffing state | SCR-5 all states |
| N-17 | CON-12 | Per source: snapshot, current value, `changed_since`, `current_unavailable`; per brief heading: `trimmed` by the fact check; promise status and history (`changed` with reason and new text); identity status; `allowed_actions` for the current state and role; a version for conflict checks; other cases for the customer; `seed` | SCR-6 partial, stale, disabled |
| N-18 | CON-13 | Errors `VERSION_CONFLICT` (409) (with who changed it and when), `REASON_REQUIRED`, `WAKE_UP_REQUIRED`, `OUTCOME_REQUIRED`, `NOT_ALLOWED_IN_STATE`, `CASE_ALREADY_CLAIMED` | SCR-6, SCR-7 error and stale |
| N-19 | CON-14 | Errors `NOT_LIVE` (chat ended, including by reset) and `NOT_CLAIMED_BY_YOU` | SCR-6 live box |
| N-20 | CON-15 | Activity kinds (call, email), outcome (reached, no answer, left a message), note; the response carries the fixed label "Demo: recorded, not sent" | SCR-6 success (R-34) |
| N-21 | CON-16 | A write to mark a flag reviewed (with note and reviewer) and a `status` field; links to the case and the message ID | SCR-8 success; role check for the disabled state |
| N-22 | CON-17 | Alerts as decision lines with type and case reference (P0/P1 created, unowned, due soon, overdue, stuck waiting, shift ended with live-queued cases); lane counts; live queue length | SCR-7 R3–R5 |
| N-23 | CON-18 | Per measure: numerator, denominator, unit, null with reason; `as_of`; seed count and whether seeds are included; the case references behind each number | SCR-9 partial, stale, R7 |
| N-24 | CON-19 | `as_of`; per-measure null with reason; alert decision lines; last health-check restart time; a guarantee of redaction | SCR-10 partial, stale |
| N-25 | CON-20 | Per split presence (dev, held-out), run ID, date, sizes, mix; `agent_version` of the run and the current deployed version | SCR-11 partial, stale |
| N-26 | CON-2 | A pending turn has no fixed short deadline: the UI holds "replying…" past 10 s (SP-1 p95 10.2 s at 20 at once; latency line p95 ≤ 12.5 s, Innocent 2026-10-20). The contract names the per-turn deadline (§6) and the error the UI gets past it (e.g. TURN_TIMEOUT → retry once or handoff). Streaming is **not** assumed | SCR-1 loading, error |
| N-26 resolved | CON-2 | **Decided 2026-10-21 (§6):** deadline 60 s → `TURN_TIMEOUT` (code-built reply: Try again, Talk to a person); `BUSY` above 30 turns in flight; no streaming; CON-3 is SSE with replay | SCR-1 loading, error |
| N-27 | CON-2, CON-3 | The C2 panel's "settled" object comes from **conversation state** (every completed write in the conversation), never from the latest turn's facts only. SP-1 saw a move done in turn 3 reported as "not done" in turn 4 (R-45 fix, §6). Completion wording on any card reads the same state | SCR-1 partial, success |
| N-28 | CON-22 | **Demo login:** `login` (username, password → session cookie), `logout`, and a session read. One error code `LOGIN_FAILED` for every refusal, with the same body and timing whatever the cause; a throttle that answers the same sentence; no hint which field was wrong. `UNAUTHENTICATED` (401) on every other route except `/healthz`, carrying a `return_to` so SCR-12 can send the visitor back | SCR-12 error, stale, success; every screen's stale state |
| N-29 | CON-10, CON-11…CON-18 | `ROLE_NOT_ALLOWED` for a staff read or write made while the role is customer, with no staff data in the body; **the role is held once per login session** (in the `mhc_session` cookie, CON-10, settled 2026-10-21 to match UI_CONTRACTS); **chat routes ignore the role**, so a reviewer keeps the chat in one tab and the console in another. Switching role in one tab changes it for the other tab's next staff call | SCR-4 stale; SCR-5…SCR-9 |
| N-30 | CON-7, CON-9 | Both need the login session (R-48), like every other CON; the staffing toggle and reset are not special-cased | SCR-3, SCR-7 |
| N-31 | CON-1, CON-2, CON-3 | The customer chat survives a role switch: returning to Customer resumes the same chat session (id kept in the tab), with missed events replayed (N-2); a reset or a closed chat ends it as before | SCR-1 after SCR-4 success |

## Notes for the orchestrating session (upstream items, reported, not edited)

1. **Safety wording drift.** Meridian's text is "leave the home immediately and call 911 or their gas utility from outside" (`policies/escalation_and_safety.md`). US-3's acceptance, REFERENCES R2-1 and the A2 prototype say "leave the home **now**". This spec uses the KB words ("immediately"), changing only "their" to "your". UX-1 / UX-2 should match, or Innocent should approve "now".
2. **"Charged" inside a negation.** Consolidated §9.3's proposed WP-4 wording includes "No fee has been charged." R-21 forbids "charged"; this spec bans the word in any form. The consolidated wording should drop that sentence.
3. **"Recorded, not placed" vs R-34.** Consolidated §4 and the Riley journey say a call is "recorded, not placed"; R-34 fixes "Demo: recorded, not sent". This spec uses R-34's label on every activity, with "No call is placed." as a separate hint.
4. **SCR-1 needs CON-3 always.** UX-1 ties CON-3 to FLOW-8 only, but the chat header must update when staffing or the clock changes elsewhere (N-1).
5. **SCR-2 is a page, not a dialog.** The A2 prototype shows the inbox as a dialog inside the chat; SITEMAP and FLOW-3 make it a separate page in another tab. This spec follows SITEMAP.
6. **Does advancing simulated time move the customer chat's "today"?** CON-8 is one shared clock. If the supervisor advances to Monday, the chat's demo date chip and relative dates ("tomorrow") change too. R-3 says the clock is fixed at Fri Oct 16. This needs a decision before CON-8 is signed (one clock for everything, or a staff-only offset).
7. **Expired code (resolved 2026-10-21).** FLOW-3 and CON-2 now offer "Send a new code" on expiry while under a per-conversation cap of 3 (decided at §6); at the cap, the customer is handed to a person with nothing revealed. *(Earlier note: the first draft ended an expired code in a handoff.)*
8. **Emergency-line card colour (R-8).** Specified as a card with a heavier ink edge, not red, to keep red for "leave the home" hazards. It is a design call for the UX-3 gate.
9. **Prototype times and labels.** The A2 prototype uses 24-hour times and "RILEY · REP (DEMO)". This spec uses 12-hour times and "Riley · representative (demo)" (REFERENCES R3-1); `design.md` should carry both.
10. **R-48 side effects (2026-10-21).** (a) Reset used to end staff sessions (old N-14 and SCR-4 stale); with one login it now keeps the login and sets the role back to customer (CON-9), so the reviewer who resets stays signed in and switches role again. (b) SCR-4's "Customer sessions can't reach staff data" is replaced by `ROLE_NOT_ALLOWED` under the customer role (N-29). (c) A one-click control on the phone chat costs a 44 px row, so the thread drops from about 484 px to about 440 px (IA.md). (d) FLOW-12's "SCR-1 and SCR-5 open side by side" holds because chat routes ignore the role (N-29). (e) The SCR-4 optional full-page route `/role` is a proposal; the operations are CON-10 `PUT /api/session/role` and `GET /api/session`.
