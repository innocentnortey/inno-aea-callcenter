# Research Questions

**Owner of:** every unresolved question this project must answer (or consciously assume) before
the PRD. IDs are stable (`RQ-N`) and never reused. Company profiles and the fit review link here
instead of restating questions.

**Started:** 2026-10-14 · **Status:** all open; RQ-6, RQ-10 and RQ-18 partly answered on 2026-10-15; RQ-8, RQ-40 and RQ-43 partly answered in the 2026-10-15 reconciliation pass. RQ-44 and RQ-45 remain Innocent's scope decisions.

**Related registers that stay in their own homes (linked, not copied):**
- Staff questions — `Gauntlet AI/open-questions.md`: **GQ-18** (one build for two partners)
  and **GQ-20** (submission due before the interview or by a portal deadline) remain open.
  **GQ-19** (which Riverside) was resolved 2026-10-15: the portal partner is The Riverside
  Company, legally Riverside Partners L.L.C. Riverside is deferred for this project's framing.
- Brief risks **T1–T23** and consistency review **C1–C11** — [brief audit](2026-10-14-brief-audit.md), now the owner. T1–T13 were
  reviewed against the brief and primary sources; T14–T23 were added on 2026-10-14. Source review
  does not close the workflow, applicability or implementation questions. Rows below cite the risk they feed.

**How a question can be closed.** *Public* = more public research. *Interview* = ask the partner on
Thu Oct 22 or later. *Staff* = Gauntlet staff. *Decide* = Innocent decides in the PRD, labelled as an
assumption if evidence is unavailable. A question closed by assumption stays visible as one.

---

## Business

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-1 | Which AEA team does the hiring role sit in (Elevate operating team, the Head of AI Solutions, or elsewhere), and who would sponsor a portfolio onboarding workflow? | The brief does not establish the hiring team; the two-layer framing should speak to the right owner. | Interview | [AEA context](company-research/aea-investors.md) |
| RQ-2 | Where does a new patient drop out today: inquiry, registration, paperwork, prerequisites, or booking? What is the current completion rate? | The brief's ~50% → ~70% is labelled illustrative. Without a baseline, the success claim stays a hypothesis. | Interview; Decide (assume) | T12 |
| RQ-3 | What does an incomplete intake cost: staff follow-up time, lost or delayed first visits, no-shows? | Turns completion into the partner's business metric (layer 2). | Interview | Metrics tree |
| RQ-4 | Is new-patient intake handled centrally (patient-access or call centre) or at each location? | Decides who the staff hand-off goes to and what "reuse across locations" means. | Public (job posts); Interview | Commonwealth, ADC |
| RQ-5 | Does any shared procurement, operating programme or common vendor exist across AEA's Elevate healthcare platforms? | "Four platforms" is a reach hypothesis, not a shared buyer. | Interview | [Fit review](portfolio-fit-review.md) |

## Workflow

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-6 | At Commonwealth, which intake fields and documents are mandatory before which appointment type? | Defines "missing requirements" and the readiness summary. **Partly answered 2026-10-15:** the online request form's required fields are published (S-75; no SSN, no upload); the patient brings photo ID, insurance cards, co-payment and imaging (S-12); the referral packet contents are the referring provider's (S-11). Still unknown: what is mandatory before booking vs at check-in, and per appointment type. | Public; Interview | [Commonwealth](company-research/commonwealth-pain-spine.md) |
| RQ-7 | When is a referral required (by payer or service), who verifies referral and coverage, and how long does it take? | Booking must respect prerequisites; it decides whether the next step is a staff intake call or a visit. | Public; Interview | Commonwealth, T3 |
| RQ-8 | Which appointments may a prospective patient self-book, and which must staff schedule? | Defines "appropriate next step" without inventing clinical access. **Partly answered 2026-10-15 for one practice:** AdaCare's published scheduler offers a New Patient Visit (and five other new-patient services) with visible slots before personal details (S-83 re-read; view only, nothing submitted). Commonwealth and FOH publish staff-scheduled entry (S-70, S-96); Metro Vein's form leads to a call (S-88). Still unknown elsewhere, and whether a self-booked slot is confirmed without staff review. | Interview; Decide | All profiles |
| RQ-9 | How much do intake steps, forms and appointment types vary across American Dental Companies' affiliated practices? | Tests whether the "second configuration" is configuration or a new workflow. | Public (sample several practices) | [ADC](company-research/american-dental-companies.md) |
| RQ-10 | What reviewed, non-clinical help content do practices already publish (what to bring, what happens at the first visit, cost and coverage FAQs)? | Supportive content must be approved help, never invented advice or obstruction. **Partly answered 2026-10-15:** each platform publishes reusable help content — Commonwealth FAQ and insurance glossary (S-12, S-67), AdaCare first-visit and financing text (S-16), Metro Vein insurance steps and FAQ (S-86, S-87), FOH first-visit and contact guidance (S-95, S-96), Numotion process and insurance tips (S-23, S-102). Whether companies would approve reuse of it in a product remains open. | Public | T5 |
| RQ-11 | In oncology intake, which steps are administrative and which are clinician-directed (urgency, referral review, records)? | Draws the line the product must stay behind. | Public; Interview | [AON](company-research/american-oncology-network.md), T3 |
| RQ-12 | Which part of Numotion's process is initial intake that could reuse the core, and where does the equipment and funding workflow begin? | Bounds the adjacent opportunity. | Public; Interview | [Numotion](company-research/numotion.md) |
| RQ-13 | How does Metro Vein's existing chatbot hand off to staff, and is there any evidence of a gap in completed intake? | We must not assume its current process performs poorly. | Public; Interview | [Metro Vein](company-research/metro-vein-centers.md) |

## Data

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-14 | Which documents do new patients actually present (driver's licence, state ID, insurance card, referral letter), and in what condition (photo, scan, fax)? | The brief requires name/DOB/address extraction; an insurance card or referral may matter as much. | Public; Interview | Stage 2 samples |
| RQ-15 | What is the minimum data needed for administrative intake before the first visit? | Data minimisation; every collected field needs a purpose. | Public; Decide | T10 |
| RQ-16 | How should minors be handled (guardian completes intake; age gate)? | DOB reveals minors; dental and oncology both see children. | Decide | T11 |
| RQ-17 | How do we build a realistic synthetic ID and document set without imitating real state layouts or security features? | Golden-set realism versus forgery-material risk. | Decide | T8, T9 |

## Vendor

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-18 | Which practice-management, EHR, scheduling, forms and CRM systems does each platform use (portal links, job posts, privacy policies)? | Decides what a completed intake record must plug into, and what already exists. **Visible 2026-10-15 (not integration evidence):** Commonwealth — athenahealth portal/billing, prettygoodai request form, ChartRequest, "24/7 Virtual Agent" (S-64, S-66, S-75); ADC — Jarvis Analytics scheduler, "cloud-based centralized dental management software" (S-79, S-83); Metro Vein — HubSpot CRM for chatbot data, SMS reminders (S-19); AON/FOH — OncoEMR, CareSpace portal, personapay billing (S-92, S-96, S-97); Numotion — myNumotion app and portal, live chat (S-104, S-106). | Public | All profiles |
| RQ-28 | What does Commonwealth's existing online request-appointment form (hosted on `commonwealth.prettygoodai.net`) do: capture only, AI-assisted intake, or scheduling? Who runs it, and where does it hand off? | Found on 2026-10-14. An existing intake tool changes the framing from "first digital intake" to "complement or benchmark". **2026-10-15:** seven low Google reviews (Shively and Elizabethtown, within about the last year) describe an AI phone and scheduling assistant. They report a booking missing from the schedule, no route to a human, and the same link sent four times ([review sentiment §1.1](2026-10-15-google-review-sentiment.md)). It is not established whether this is the prettygoodai tool. Also ask: does it write to the practice schedule, and what is the human-handoff rule? | Public; Interview | [Commonwealth](company-research/commonwealth-pain-spine.md) |
| RQ-19 | What are the data-use, retention, training and BAA terms of each LLM and OCR provider we might use, including fallbacks? | A free tier is not a privacy guarantee. | Public | T1, T2 |

## Privacy and safety

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-20 | If a pilot handled real patient data, which HIPAA roles and obligations would apply (covered entity, business associate, minimum necessary)? The demo stays synthetic. | The brief asks candidates to name the regime for their assumed domain. | Public (primary sources) | Brief §Security, T1 |
| RQ-21 | How do the brief's deletion-on-request and image-purge rules interact with medical-records retention once intake becomes part of a record? | A possible conflict between the brief and real obligations. | Public | T10 |
| RQ-22 | What reviewed crisis protocol, verified local resources and operational hand-off apply when a user expresses distress or self-harm, including provider failure/refusal? | The brief defines an intent, but not safe escalation or a staffed response. | Public; Interview; Decide | T4 |
| RQ-23 | Which ID-image and biometric rules apply, given that we extract three text fields only and never match faces? | Government ID photos are the most sensitive input. | Public | T7 |
| RQ-24 | Where is the line between supportive content at friction points and a dark pattern that obstructs leaving? | The brief triggers content on likely abandonment. | Public (FTC guidance) | T5 |

## Integration

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-25 | Which system would accept a completed intake record, and in what form (FHIR Patient/Coverage, HL7, CSV, PDF packet, CRM record)? | Determines the hand-off contract even if the demo stubs it. | Public; Interview | All profiles |
| RQ-26 | Are real schedules reachable by API, and how would double-booking be prevented against an external calendar? | The demo uses synthetic slots; production portability depends on this. | Public | Brief Core #3 |
| RQ-27 | Where does a prerequisite-blocked or incomplete intake go for staff follow-up (queue, CRM task, phone call)? | Missing prerequisites must not block access to help. | Interview; Decide | Commonwealth |

## Questions added by the 2026-10-15 research completion pass

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-38 | At Commonwealth, how long does it actually take from request or referral to first visit, and how many requests stall before scheduling? The site states three phrasings of one aim (10 days; ten business days; two weeks after the referral arrives). | The aim is the measurable promise onboarding could support; without a baseline, any improvement claim is illustrative. | Interview | [Commonwealth](company-research/commonwealth-pain-spine.md), report §9 |
| RQ-39 | Which Commonwealth plans or services require a PCP referral, given the FAQ's conflicting answers ("most insurance plans require a referral" vs "Some … Others allow you to schedule directly") and plan-level notes on the insurance page? | Decides whether intake can route to booking or must route to a staff referral step. | Interview; Public (plan list) | Commonwealth, RQ-7 |
| RQ-40 | Which ADC central services (scheduling, recall, patient communications, insurance verification, dental management software, Jarvis scheduler) does each partner practice actually use, and which appointment types may a new patient self-book? | Tests whether one configuration can serve many practices. **Partly answered 2026-10-15 for AdaCare only:** the Jarvis widget lists six new-patient services and showed New Patient Visit slots before personal details (S-83 re-read). The first pass could not render it; that limitation is kept in the register. Still unknown: the fields and confirmation after slot selection, whether the booking writes to the practice system, and other practices' use. | Interview; Public (sample practices) | [ADC](company-research/american-dental-companies.md), RQ-9 |
| RQ-41 | At Metro Vein, what makes a free evaluation "subject to insurance eligibility"; how are arrival times set and changed after booking; who sends confirmations, directions and preparation; and is preferred language captured at request? | Matches the attributed review themes to the actual process before proposing change alerts or preference capture. | Interview | [Metro Vein](company-research/metro-vein-centers.md) |
| RQ-42 | At FOH, what are office hours; can the 14-page packet be completed in the CareSpace portal before the visit; and how are new-patient calls, voicemails and outside referrals queued? | The packet and referral queue are the administrative surfaces an intake product would touch. | Interview; Public | [AON](company-research/american-oncology-network.md) |
| RQ-43 | At Numotion, who starts new-equipment intake (customer, family, clinician or referral source), what is captured before the evaluation, and do myNumotion status notices cover documentation and funding steps? | Bounds the reusable front of the journey and avoids duplicating an existing status tool. **Partly answered 2026-10-15:** the public app guide documents order status, status-change notifications, an appointment calendar, service requests and live chat, with registration by customers and a separate clinician entry (S-106). That is documented capability, not a live-account test; which steps notify, and who starts intake, remain unknown. | Interview; Public | [Numotion](company-research/numotion.md), RQ-12 |

## Questions added by patient journey baseline research

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-44 | Which optional patient-reported context, if any, may the assistant collect and pass through, while clinical questionnaires and all assessment remain with the care team? Reconcile the configuration annex's exclusion of medical history with the demo's chronic-condition and prior-treatment questions. | A real patient journey includes clinical history, but that does not automatically put it in this assistant's scope. **2026-10-15 reconciliation:** still open. The conflict is now flagged (⚑ RQ-44) in the configuration annex, the demo blueprint and report §7; the conservative default is the annex's exclusion; the selection matrix parks the idea as P-01. | Decide; company/clinician review before real deployment | [Journey baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md), configuration annex, demo blueprint, [selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md) |
| RQ-45 | Where does the representative intake start and end, what counts as administratively complete, and how can the patient finish before the visit or with staff on arrival? | Defines a fair completion/time comparison without confusing registration with clinical readiness or assuming a universal order of booking and paperwork. Also decides whether established-patient problems (rescheduling, authorisation between procedures, repairs), which many cited reviews concern, are in scope or parked (selection matrix P-11). | Decide; Interview for company-specific workflow | Journey baseline; RQ-6, RQ-8, RQ-30 |
| RQ-46 | Which notices, upload/communication consents, records releases, financial disclosures and staff-reviewed prerequisites apply to each workflow, and what happens if a patient declines or cannot complete one digitally? | Avoids a blanket checkbox, automatic denial of access and treating every published form as a universal requirement. | Public; Interview; appropriate legal review before real use | Journey baseline; RQ-15, RQ-20, RQ-33 |

## Questions added by the brief audit

Primary-source findings and their limits live in the [audit](2026-10-14-brief-audit.md); these
questions own the remaining decisions and missing evidence.

| ID | Question | Why it matters | Close by | Feeds |
|---|---|---|---|---|
| RQ-29 | Will optional sentiment inference be omitted, and how should explicit help requests, long pauses and accessibility needs be handled without emotion profiling? | Separates useful assistance from an inferred emotional profile and coercion. | Decide; Public if biometric sensing is proposed | T5, T6, T21 |
| RQ-30 | What are the required fields, permissible unknown/declined states, OCR scoring rules and holdout boundaries, and when is a field provisional versus user-confirmed? | Prevents fabricated completeness, ambiguous persistence and inflated OCR scores. | Decide; Staff if a literal rubric conflict arises | T9, T22 |
| RQ-31 | Where could intake data persist or be exported, what are deletion/backup/provider limits, and how will in-flight work and restore behavior respect revocation? | Covers storage, temp files, queues, framework errors, traces and third parties. | Public; Decide; later verification | T10, T18, T20 |
| RQ-32 | How will the later Rails/Supabase integration prove record, file, role and practice isolation for every route? | Login and RLS availability do not prove that the actual connection enforces scope. | Decide; later integration proof | T13, T16 |
| RQ-33 | Which jurisdictions, legal entities, data categories and incident-response owners would a real pilot involve, including obligations outside HIPAA? | No general regime label clears every actual deployment. | Interview; Public; appropriate legal review before real use | T14 |
| RQ-34 | How will the demo enforce synthetic-only inputs, and which adversarial document/chat/upload cases will prove that untrusted input cannot change permissions, consent or actions? | A banner alone cannot prevent real-data submission or prompt injection. | Decide; later verification | T1, T15, T20 |
| RQ-35 | What does request-reschedule mean, who owns slot availability, and how should retries or uncertain commits affect booking confirmation? | Preserves one durable, authorized booking under concurrency and failure. | Interview; Decide; later verification | T17 |
| RQ-36 | What exact response boundaries, request mix, failure reporting, cold-start conditions and uptime window will benchmark claims use? | Preserves the brief's required tests without turning small samples or fast errors into false results. | Decide; Staff if evaluation-window clarification is needed; later measurement | T19, T21 |
| RQ-37 | Does any unmet must-have, listed failure mode, security requirement or AI threshold cause an automatic fail regardless of the 70/100 total, and how do the rubric's partial-credit descriptions interact with those gates? | Mandatory pass/fail language and a weighted rubric specify different apparent routes to passing. | Staff; Decide a conservative assumption until answered | C1 |
