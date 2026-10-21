# Service-team direction: make AI handoffs useful

**Date:** 2026-10-20, America/Chicago  
**Status:** ideation and research synthesis; feature candidates, not approved requirements or a PRD  
**Basis:** issued AEA brief (S-100, S-101), Meridian dataset (S-102…S-105),
[brief audit](2026-10-20-brief-audit.md), and external service-team sources S-132…S-137 in the
[source register](../source/source-register.md).

## Purpose

The business wants routine customer requests resolved correctly without hiring in proportion to
call volume. The customer-facing agent handles questions and eligible appointments; people handle
the exceptions that need judgment, account review or safety follow-up. That only saves staff time
if an exception reaches the **right person with enough context to act**. An AI system that merely
ends its chat with “a human will help” can move work into an invisible queue and make the next
human interaction harder.

This suggests a product with two connected workspaces: a simple customer conversation and a
focused service-team workspace. The latter is for the frontline representative and supervisor,
not only the business owner. The brief requires a public customer app, contextual escalation and
monitoring; a complete live human console is a **candidate extension**, not an issued deliverable.
If included in the prototype, it should demonstrate a genuine state transition from AI to human
ownership rather than imply that a staffed queue exists when it does not (S-101; audit C-7, E-5).

## What the external research suggests

- **Repetition is a handoff failure.** Zendesk's 2026 survey reports that 74% of customers find it
  frustrating to repeat their story to different agents (S-132). This is a broad customer survey,
  not a measurement of Meridian callers. The design implication is continuity of *verified*
  context, with the original conversation available when a summary is incomplete.
- **Information hunting competes with helping.** Salesforce's sixth State of Service report says
  69% of agents have difficulty balancing speed and quality. It reports that 58% of agents at
  underperforming organizations switch among multiple screens to find what they need, versus 36%
  at high performers (S-133). These are vendor-published associations, not evidence that a new
  dashboard alone causes better service.
- **AI shifts human work toward oversight and exceptions.** Intercom's analysis of 166 interviews
  describes changes in triage, routing, QA and frontline responsibilities after AI adoption
  (S-134). Its sample consists of Intercom customers or prospects, so it is directional. It
  supports designing for a representative who must *review and correct* the AI's work, not only
  receive a transcript.
- **Existing service tools already group these tasks.** Microsoft's product documentation shows
  customer, conversation, case and timeline context on one receiving-agent screen (S-135), plus
  context-bearing transfer into a queue and workspace (S-136). These are implementation examples,
  not proof that Meridian needs the same product breadth.

The three opportunities below are ranked for this brief: each addresses a direct handoff pain,
can be shown in a small prototype, and helps demonstrate the audit's requirement for honest
resolution. They are hypotheses to check against Stage 2 call drivers and, if possible, direct
feedback from a service representative.

## Three strongest feature candidates for service representatives

### 1. An actionable exception inbox

**Pain:** staff are already overloaded. A handoff without owner, reason, priority or next action
becomes another item they must interpret and chase. The audit distinguishes safety cases, urgent
dispatch, supervisor callbacks and routine out-of-scope questions; they should not appear as an
undifferentiated pile (C-7, C-8, K-16).

**Idea:** show each handoff with a short reason, customer-visible promise, urgency, waiting age,
status and assigned owner. A representative can claim, reassign or close it. Route by the
business rule that caused the handoff, while making the routing reason visible and correctable.
The inbox should distinguish “needs response now” from “callback within one business day.” A
safety instruction must reach the customer immediately, before any queue action (K-12, E-3).

**Small prototype proof:** a refund request creates a supervisor item with a clear callback
expectation; a service-area ambiguity creates an appropriate staff item; a person can claim and
resolve one item. If no staff member is actually on duty in the demo, label that state clearly.

### 2. A handoff brief that opens beside the original conversation

**Pain:** the receiving person has to ask the customer to repeat the issue, search the chat for
what the AI already tried, then check other screens for booking or account state (S-132, S-133,
S-135).

**Idea:** provide a compact, editable brief: the customer's goal; why the AI stopped; relevant
facts and verification status; steps already tried; any booking result or failed attempt; the
specific unresolved question; and links to the source documents or records used. Keep the full
conversation one click away. Mark AI-generated summary text as such and never turn an unverified
customer claim into a settled fact. Show only data the staff role is allowed to see (audit D-5,
D-6, G-2, G-9).

**Small prototype proof:** for the seeded disputed invoice, the representative sees the invoice
line items, the current fee reference, the inconsistency, and the fact that the AI did **not**
promise a refund. The customer need not restart the explanation (audit D-8, K-16).

### 3. Human takeover and resolution in the same work view

**Pain:** a summary is helpful only if the person can finish the work. Switching to another
channel to reply, while the AI might continue speaking, creates duplicate or conflicting
responses (S-134, S-136).

**Idea:** let an authorized representative claim a conversation, pause the AI, reply in the same
thread, inspect or complete a permitted booking action, and mark the actual outcome. They can
correct the handoff reason or flag a bad answer or document for review. A correction goes to a
review queue; it does not automatically alter the knowledge base or evaluation set (audit C-13,
G-6). Supervisor-only decisions remain supervisor-owned.

**Small prototype proof:** a staff member takes over one escalated case, the AI stops responding,
the customer sees who is handling it, and the item closes with an outcome distinct from “AI
contained.” If live staffing is not part of the deployment, this can be a labelled demo flow
with persisted states and a reviewer-visible audit trail.

## What the owner or service manager would need

The manager's first question is operational: **what needs a person, who owns it, and how long has
it waited?** Start with the same exception inbox, filtered by urgency, owner and age. A second
view can show confirmed bookings, failed booking attempts, and the reasons for escalation. A
small trend view could show top customer concerns, knowledge gaps, containment on *correctly
resolved* requests, wrong answers, handoff wait, tool failures and latency. A booking count alone
does not reveal whether customers received the right help.

Keep “resolved,” “escalated,” “abandoned” and “failed” separate. Microsoft's bot dashboard, for
example, defines *deflected* to include conversations abandoned before resolution (S-137). That
definition would be misleading for this brief's containment claim (audit C-4, E-1). Metrics
should be read from recorded outcomes and show their denominators, not be inferred from whether
the AI stopped talking.

## A possible end-to-end story

A customer asks why an invoice includes an after-hours fee. The AI explains what each line means
from the current records but sees that the amount conflicts with the fee schedule. It does not
declare the bill wrong or promise money back. It tells the customer a supervisor callback is
needed and gives the documented time expectation. The supervisor's inbox shows the reason and
age; the handoff brief shows the invoice line, source, discrepancy and conversation. The
supervisor claims the item, checks the full record, responds, and records the outcome. That
single story demonstrates the customer, representative and manager sides of the product without
requiring a broad contact-center platform (audit D-8, K-16, E-5).

## Boundaries and next questions

- The required submission can succeed with a text interface. Voice, telephony, a message broker
  and a full enterprise case system are not prerequisites (S-101).
- A booking is only **confirmed** after an eligible slot is written successfully. Follow-up
  notifications and analytics may be asynchronous; a pending request is not a confirmed booking
  (S-101, S-104; audit G-7).
- This note does not settle the audit's open choices about scheduling breadth, fee waivers,
  identity proof, old-document indexing or voice (DEC-1…DEC-5).
- Stage 2 should test whether the most frequent exceptions, handoff reasons and booking flows in
  the issued transcripts support these three features. Transcript patterns are evidence of
  customer requests, while external research suggests staff pain points; neither substitutes for
  speaking with actual service staff.
- A deeper pass should compare agent, supervisor and customer workflows; inspect real product
  patterns; identify the smallest reviewable handoff slice; and define evidence that it saves
  staff effort without hiding unresolved work. Those are research questions, not PRD decisions.
