# Patient journeys and standard onboarding practices

**Research date:** 2026-10-15 · **Status:** research synthesis and candidate requirements, awaiting Innocent's research sign-off.

The useful comparison for this project is the work needed to get a patient ready for a first visit. A public contact form shows only the entry point. Professional guidance, patient preparation instructions and the companies' published requirements give us a reference journey without assuming access to their internal systems.

The business hypothesis is that clearer steps, less repeated entry and a usable staff handoff can increase completed intake and reduce administrative effort. This is a reason to measure the product, not evidence that any company is losing revenue or that our approach will improve it.

Company facts remain in the [company profiles](company-research/). Source URLs, dates and authority are in the [source register](../source/source-register.md). The existing [research report](2026-10-15-onboarding-research-report.md) covers the company comparison. This supplement establishes the general workflow and evaluation baseline.

## What standard means here

| Evidence category | What it establishes | What it cannot establish |
|---|---|---|
| Issued brief, S-1 | Mandatory assessment capabilities and tests | That a clinic requires those exact features |
| Professional guidance, S-108 to S-114 | Recommended ways to organise registration, communication and referrals | Universal practice, company adoption or guaranteed outcomes |
| Accessibility guidance, S-115 and S-116 | Reference behaviours for usable forms | Compliance of a future product without evaluation |
| HHS and CMS guidance, S-117 and S-118 | Specific privacy and cost-information distinctions | A complete legal assessment for a real deployment |
| Other providers, S-119 and S-120 | Concrete examples of specialty journeys | The AEA companies' internal processes |
| Company pages and profiles | Their published services, prerequisites and preparation | Whether those steps work as intended internally |
| Our synthesis and candidate requirements | A workflow to test with synthetic scenarios | An approved PRD or proof of a competitor's deficiency |

**Timing is flexible.** Registration may happen before the appointment or at arrival. The AMA describes both approaches (S-108). The product should support advance completion and an assisted route at the clinic; an invitation to complete forms early is not proof that everyone can or must do so. We should not assume that all clinics onboard only on arrival, or that every patient can finish digitally at home.

## What a published tool can and cannot establish

Added 2026-10-15 (reconciliation pass). Companies publish request forms, portals, apps, schedulers and virtual assistants. Each shows that a tool exists. None, on its own, shows that onboarding is completely digital, that tools are integrated, or that anything fails. When comparing a company with this baseline, name which job a tool does:

| Job | What it covers | Example of a published tool (not an assessment) |
|---|---|---|
| Contact capture | A request, a callback or a referral arrives | Commonwealth request form (S-75); Metro Vein four-field form (S-88) |
| Scheduling | A date and time are chosen or offered | AdaCare's Jarvis widget showed New Patient Visit slots before personal details (S-83, re-read 2026-10-15) |
| Administrative onboarding | Identity, insurance, consents, records release, financial policies | FOH 14-page packet (S-98); AdaCare paper packet (S-82) |
| Clinical assessment | History, examination, urgency, treatment decisions | With clinicians at every platform; outside the assistant |
| Ongoing coordination | Status, reminders, rescheduling, service requests after the first contact | Numotion's app guide documents status, appointments, service requests and chat (S-106; documented capability, not tested) |

A company can be strong in one job and paper-based in another. AdaCare, for example, publishes self-scheduling with visible slots alongside a paper packet. The candidate solutions in the [selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md) say which job they address.

## The common first visit journey

This is a derived reference model. Stages can overlap and booking may occur before all paperwork is complete. Staff decide which prerequisites apply to a particular appointment.

| Stage | Patient needs | Administrative work | Assistant's possible role | What remains with staff or clinicians |
|---|---|---|---|---|
| 1 Find and request care | Know whether this is the right service | Request reason, preferred location and contact route | Explain published services and collect a request in the patient's words | Clinical suitability and urgency |
| 2 Establish the patient record | Give accurate details without unnecessary repetition | Demographics, contact details, existing/new patient status; identify a representative when relevant | Guided entry; confirm extracted identity fields; flag a possible existing record for staff | Identity verification policy and record matching decisions |
| 3 Arrange the next appointment | Know what can be booked and what is pending | Appointment type, staff-reviewed referral requirements, availability | Show authorised next-step slots or route an incomplete request to staff | Clinical routing and permission to book a visit |
| 4 Complete the administrative packet | Understand why documents and permissions are needed | Insurance details, applicable records-release request, notices, financial policies and communication choices | Ask relevant questions, explain purpose, allow review and correction | Which documents and authorisations are required |
| 5 Prepare for the visit | Know where to go and what to bring | Directions, arrival time, accessibility needs, interpreter request, missing items | A checklist and company-approved preparation information | Clinical preparation instructions and accommodations that must be arranged |
| 6 Arrive and reconcile | Avoid starting the same paperwork again | Confirm attendance, changes and remaining documents | Make the submitted administrative summary available to authorised staff | Physical ID checks, payment handling and clinical reconciliation |
| 7 Have the consultation | Be understood and receive an appropriate assessment | Staff handoff into care | Supply the administrative record and any approved patient-reported note | History review, examination, diagnosis and treatment decisions |
| 8 Leave with a next step | Know whom to contact and what happens next | Follow-up booking or a separate order/authorisation process | Display approved administrative next steps | Treatment and test-result interpretation |

The AMA's preregistration guidance addresses demographic and payment information, insurance checks, appointment logistics and records transfer (S-108). Its sample packet separates demographic, history, privacy and financial documents (S-109). These support a configurable packet rather than one identical questionnaire for every clinic.

## How the journey changes by service

These are reference sequences informed by the cited sources. They describe the work to accommodate, not an observed end-to-end implementation at each company.

### Pain management and Commonwealth

**Reference sequence:** request or referral → staff review of referral/coverage needs → consultation booking → administrative preparation → clinician history/examination and goals → clinician-selected next step → separate preparation or authorisation for a procedure if needed.

Commonwealth publishes first-visit history review and examination, ID/insurance preparation, plan-dependent referral rules and procedure-specific requirements (S-11, S-12; [profile](company-research/commonwealth-pain-spine.md)). Cleveland Clinic's pain service illustrates a broader multidisciplinary assessment model (S-120); it does not establish Commonwealth's workflow.

**Onboarding emphasis:** referring-provider details, document readiness, clear consultation-versus-procedure expectations and a route to staff when prerequisites are unclear. Do not assume that someone seeking pain care has already been approved for an injection or another procedure. Do not generate medication or fasting instructions.

### Dentistry and AdaCare

**Reference sequence:** request or booking → administrative packet and benefits information → arrival → dental-team interview and examination → clinician recommendation → separate treatment appointment when needed.

ADA guidance places explanation and a patient interview around the first examination and asks teams to check for prior radiographs (S-110). AdaCare publishes advance forms and explains that cleaning usually cannot take place with the first exam (S-15, S-16; [profile](company-research/american-dental-companies.md)).

**Onboarding emphasis:** patient and policyholder details, relevant prior-record requests, comfort concerns and accurate expectations about what the first appointment includes. A new-patient exam is not a promise of cleaning, implant treatment or a completed treatment plan. AdaCare remains one practice example within ADC.

### Vein care and Metro Vein

**Reference sequence:** evaluation request → insurance/logistics → specialist evaluation and ultrasound → clinician plan → treatment authorisation where needed → treatment appointments.

Metro Vein publishes this evaluation-to-treatment distinction (S-121), alongside insurance coordination (S-87; [profile](company-research/metro-vein-centers.md)).

**Onboarding emphasis:** distinguish the initial evaluation from treatment, explain any condition attached to a free evaluation, capture insurance when appropriate, and make directions and confirmation clear. A request should not automatically become a treatment recommendation or a coverage promise.

### Oncology and Florida Oncology and Hematology

**Reference sequence:** referral or transfer → staff coordination of outside records → administrative registration and first-visit preparation → specialist consultation → clinician-selected tests or treatment, with further education and financial support as appropriate.

MSK gives a concrete external example: care advisors help gather records and test results and connect patients to the appropriate appointment (S-119). FOH publishes referral/transfer entry, preparation information and its own packet (S-95, S-98; [profile](company-research/american-oncology-network.md)). Neither establishes the other organisation's internal process.

**Onboarding emphasis:** records-release status, referring practice, contact permissions, practical attendance barriers and an accessible human contact. Completing registration does not establish readiness for treatment. Urgency and results follow-up remain clinical responsibilities. FOH evidence is not network-wide AON evidence.

### Mobility equipment and Numotion

**Reference sequence:** customer/referrer contact → evaluation coordination → clinical documentation → funding decision → build/delivery and fitting → ongoing service.

The published process and prerequisites are in the [Numotion profile](company-research/numotion.md) (S-23, S-102). This is an equipment-service journey, not a clinic visit followed immediately by treatment.

**Onboarding emphasis:** establish who is completing the request, collect appropriate primary/secondary insurance information, show what documents staff still need and arrange the evaluation. Medical necessity and funding decisions are outside the assistant. The later equipment and repair tracker remains a separate opportunity, subject to comparison with the existing app.

## Candidate baseline for evaluating our assistant

These are research-backed candidates for later requirements. They do not claim that the companies lack these capabilities. The last column makes each candidate concrete enough to assess using synthetic scenarios without starting application design.

| Candidate | Source and status | What to check in a demonstration |
|---|---|---|
| Ask only what the current stage needs | AHRQ form guidance, S-112; recommended practice | Someone can start without completing a full specialist packet; additional questions have a stated purpose |
| Reuse administrative answers | S-112; recommended practice | A confirmed address carries through; a correction changes the summary; justified clinical re-confirmation is not counted as waste |
| Explain steps and progress | W3C, S-115; recommended practice | Patients can tell what is done and what remains; optional steps are distinguishable |
| Allow review and recovery | S-115, S-116; recommended practice | Going back does not erase prior answers; field errors explain how to fix them; completion is acknowledged |
| Support both advance and assisted completion | S-108; candidate application | A synthetic patient without a smartphone can continue with staff or manual entry |
| Explain information in everyday words | AHRQ, S-111 and S-112 | Referral and insurance questions have understandable explanations; help does not depend on medical vocabulary |
| Record language and access preferences | AHRQ, S-113; recommended practice | A preference is visible to staff; the product does not promise an interpreter is arranged until confirmed |
| Keep referral work owned | AHRQ, S-114; recommended practice | Missing records produce a named staff action/status rather than making the patient the sole messenger |
| Separate received, reviewed and approved | Derived from referral guidance and company prerequisites | Uploading a referral does not mark it staff-reviewed; an insurance card does not mark coverage approved |
| Give appointment logistics | S-108 and company preparation pages | Confirmed visit type, location, date/time and appropriate instructions are accessible together |
| Present distinct notices and choices | S-109, S-117 and issued brief | Privacy acknowledgement, records release, communication preference and upload consent are not one blanket checkbox |
| Support cost questions | S-118 and company financial pages; conditions vary | The patient sees an estimate request or staff route, not invented coverage or an AI-generated price |
| Produce a usable staff summary | Issued brief; proposed format | Confirmed fields, missing information, patient preferences and pending tasks are distinguished |

**Standard information categories are not universal mandatory fields.** A candidate administrative packet includes identity/contact details, address where needed, insurance and policyholder information when applicable, referring-provider details, communication preferences and applicable notices. Representative authority, emergency contact and records release depend on the workflow. An SSN, government-ID image or every demographic field should not become mandatory merely because it appears on a sample form. The issued brief specifically requires synthetic OCR examples with name, DOB and address; that assessment requirement does not justify collecting those fields at every company's first contact.

## Clinical information and the administrative boundary

Real first-visit workflows often include medical/dental history, medications, allergies and symptom discussions. They cannot be omitted from the patient journey simply because they are outside our software's current scope. The AMA includes history collection in its model (S-108), and ADA guidance describes the dental-team interview (S-110).

For this research, the default assistant scope is the administrative packet, documents and coordination. Clinical questionnaires stay with the clinical team or the approved existing system. Optional patient-reported context may be passed through only under an explicitly agreed collection policy; it must not be interpreted into diagnosis, urgency, treatment eligibility or a recommendation. Resolve this consistently across the configuration annex and fictional scenarios before a PRD (RQ-44).

**Status after the 2026-10-15 reconciliation:** still unresolved. The configuration annex and the demo blueprint now flag the conflicting items explicitly, and the selection matrix parks clinical patient-reported context as `P-01`. Innocent decides RQ-44; nothing in the research files decides it for him.

Repeated administrative typing is a candidate inefficiency. A clinician confirming medications or history for safety is a different activity. The product should not claim to eliminate all repeated questions.

## Requirements that come from the issued brief

The brief remains the owner of these requirements (S-1), independent of which clinic example we choose:

- Guided conversation with a structured record and graceful handling of unknown inputs.
- Document OCR for name, DOB and address; user confirmation before saving; partial extraction and manual fallback.
- Available next-step slots, durable confirmation and double-booking rejection. A request-for-callback screen alone is insufficient.
- Supportive content at defined friction triggers.
- Consent before document upload/processing; minimum necessary demo fields; private storage; image disposal and verifiable deletion; scoped access; no personal data in logs; safe upload and provider-failure handling.

Only synthetic data belongs in the demonstration. A clinical visit with prerequisites may require a staff-coordination appointment as the next bookable step; the appointment type and rules remain an explicit decision, not an automatic referral bypass (RQ-8, RQ-35).

## Privacy and financial distinctions

HHS explains that acknowledging receipt of a privacy notice is not agreement to special uses of health records, and that the patient is not required to sign that acknowledgement (S-117). The candidate flow should allow the clinic to record provision/refusal appropriately instead of treating that signature as universal permission or blocking care automatically. This is distinct from the brief's explicit upload consent.

CMS describes good-faith estimates for people not using insurance, with conditions including a request or scheduling sufficiently in advance (S-118). The research implication is an appropriate billing-team route. The assistant should not invent an estimate or apply the same legal rule to every insured visit. Operational policies require confirmation for a real deployment (RQ-33, RQ-46).

## How to evaluate the proposed improvement

Use three synthetic reference situations first:

1. **Commonwealth first consultation:** correctable identity extraction, insurance supplied, referral status pending; patient and staff can see who has the next action.
2. **AdaCare first exam:** patient expects cleaning today; published preparation explains the exam and possible later cleaning, while administrative answers carry into the staff summary.
3. **FOH transfer:** outside records are outstanding; patient can finish the administrative portion, see the records task and reach staff without an automated clinical-priority decision.

For each, compare a conventional packet-and-staff handoff **simulation** with the proposed guided experience. Use identical required information and explicitly label both as simulated. Neither is an observed reconstruction of the named practice's internal workflow.

Measure administrative completion, completion time, fields corrected, missing required items and staff re-entry/actions. Define what counts as completion before measuring it. Clinical readiness, first-visit attendance and contribution margin are separate later outcomes. A task-time improvement in a synthetic demonstration is not a measured revenue improvement at an AEA company.

## Decisions still needed before requirements

- **RQ-44:** exactly which optional patient-reported context, if any, the assistant collects; reconcile the annex and scenarios with the administrative-only boundary.
- **RQ-45:** when the representative journey starts and ends, what makes an intake administratively complete, and how patients continue before the visit or on arrival.
- **RQ-46:** which notices, permissions, financial disclosures and staff-reviewed prerequisites apply to each configured workflow.

Existing RQ-6 to RQ-8 cover required documents, referral prerequisites and bookable next steps. RQ-15 and RQ-16 cover sensitive fields and representatives; RQ-25 and RQ-27 cover staff handoff. Research sign-off, company integration access and production requirements remain open.
