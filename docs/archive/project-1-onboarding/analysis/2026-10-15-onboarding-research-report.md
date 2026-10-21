# Onboarding Research Report — Five AEA Healthcare Platforms

**Assessment date:** 2026-10-15 (website and review evidence read that day).
**Patient journey supplement:** [Patient journeys and standard onboarding practices](2026-10-15-patient-journeys-and-onboarding-baseline.md) adds professional guidance and reference journeys for evaluating the proposed experience. It does not reconstruct private company workflows.
**Task:** [`docs/aea-portfolio-research.md`](../aea-portfolio-research.md), Parts 1–10, delivered in its required 12-section order. It closes with *What I Need to Configure This Company in My Onboarding Software*. A requirement-by-requirement audit is in [Appendix A](#appendix-a--requirement-audit).
**Platforms:**
1. Commonwealth Pain & Spine (CPS)
2. American Dental Companies (ADC), with **AdaCare Dental & Dentures, Meridian ID** as the practice example
3. Metro Vein Centers (MVC)
4. American Oncology Network (AON), with **Florida Oncology & Hematology (FOH)** as the practice example
5. Numotion (NUM, adjacent), with its equipment workflow kept separate

**Annexes (same date):**
- [Annex 1 — Configuration specification](2026-10-15-configuration-specification.md): the full per-company tables for Section 8.
- [Annex 2 — Fictional demo blueprint](2026-10-15-demo-blueprint.md): 15 synthetic scenarios for Section 10.

**Reconciliation (2026-10-15, later the same day).** This report was written before the [journey baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md), the [review pitfalls synthesis](2026-10-15-review-pitfalls-and-solution-opportunities.md) and the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md). A reconciliation pass changed it as follows; the original evidence is otherwise kept.
- **Tool presence is not complete onboarding.** Key finding 1 now separates contact capture, scheduling, administrative onboarding, clinical assessment and ongoing coordination. A form, portal, app or assistant shows that a tool exists. It does not show complete digital onboarding, working integration, or failure.
- **AdaCare's Jarvis widget now loads.** It showed dates and times for a New Patient Visit before any personal details were requested (S-83 re-read, view only). The earlier "did not render" result is kept as a dated limitation.
- **Recommendations are candidates, not scope.** The opportunities in §1 and §12 map to `SOL-NNN` candidates in the selection matrix, where Innocent chooses. Only the brief's mandatory capabilities (M-01…M-15 there) are required regardless.
- **"Gap" means a difference from the reference baseline or a reported problem**, not an established company deficiency (§9). Three baselines are kept apart: reference practice, published or reported current state, and measured performance (unknown everywhere).
- **The clinical-adjacent optional questions in §7 are an unresolved scope decision (RQ-44)**, not settled design.
- **"Complete" in Appendix A means delivered against public evidence**, not signed off. Research is not complete until Innocent says so.

**Fact owners (linked, not copied):**
- company facts: [company profiles](company-research/);
- sources: [source register](../source/source-register.md) (`S-N`);
- unknowns: [research questions](research-questions.md) (`RQ-N`);
- review evidence: [Google review report](2026-10-15-google-review-sentiment.md).

## How to read the labels

| Label | Meaning |
|---|---|
| **Verified** | Read on an accessible first-party page or document on 2026-10-15 (or 2026-10-14 where marked), with its `S-N` |
| **Reported** | A public review: one person's attributed experience. Not an operational fact or a rate |
| **Not publicly established** | Looked for on the pages listed, not found. This does **not** mean the company lacks it |
| **Inferred** | A reasonable hypothesis, with what it rests on; needs validation |
| **Proposed** | Something our product would add or configure |
| **Simulated** | A synthetic placeholder for the demo, never presented as a company fact |

**Two constraints shape every section.**
1. **The research phase.** This is research, not a PRD, design or tickets.
2. **The administrative-only rule** (`.claude/rules/source-authority.md` rule 7). The product never diagnoses, triages urgency, recommends treatment or approves insurance. Where the template asks for clinical-adjacent content (Part 5; "clinician-approved urgency screening" in Part 6), the constraint is applied and explained in place.

---

## 1. Executive Summary

### Why this matters to AEA (the business layer)
The brief's own business case: onboarding "front-loads friction" on anxious users, "every abandoned registration is a lost customer plus wasted acquisition spend", and completion should rise from an assumed ~50% to ~70% (S-1, illustrative). Each of the five platforms makes a public promise that onboarding could support. Whether current onboarding meets it is not publicly established:

| Platform | Its own promise (Verified) | Where onboarding decides whether the promise holds |
|---|---|---|
| CPS | New-patient appointments "within ten business days of referral or initial contact" (S-68); "prompt scheduling" (S-64); "persistent follow-up" (S-65) | Request → referral → coverage → booking. Those are staff-coordinated steps the patient cannot currently see |
| ADC | Central "Scheduling services", recall, insurance verification and "Full Oversight of Patient Communications" for its practices (S-79) | Doing that consistently across ~76 practices |
| MVC | A free evaluation; 200+ plans; a quote before the first visit "as long as you provide your insurance information at time of scheduling" (S-87) | Capturing insurance once, confirming times, sending directions and preparation |
| AON/FOH | "strive to keep waiting times for appointments to a minimum" (S-95); integrated care and navigation (S-92) | Referral and transfer intake: records, packet, consents |
| NUM | A stepwise process with published durations (S-23); real-time order status in its app (S-106) | Front-of-journey intake, then status across weeks |

### Key findings
1. **Every platform publishes digital tools; none of them shows complete digital onboarding, and none shows failure.** The tools do different jobs:

   | Platform | Contact capture | Scheduling | Administrative onboarding (packet, documents, consents) | Ongoing coordination |
   |---|---|---|---|---|
   | CPS | Request form, "Powered by" prettygoodai (S-75) | Staff call back; "24/7 Virtual Agent" described for "scheduling needs" (S-66) | Bring ID, cards and imaging; forms on arrival if not done (S-12) | athenahealth portal for existing patients (S-64) |
   | ADC / AdaCare | Phone; widget | **Jarvis widget showed New Patient Visit dates and times before personal details** (S-83, re-read) | Paper packet, print or arrive early; insurance by phone (S-16, S-82) | Recall and reminders; reminder calls praised (S-15, S-84) |
   | MVC | Four-field form (S-88); chatbot for requests and insurance questions (S-19) | Staff call back (S-88) | Insurance captured at scheduling for a quote (S-87) | SMS reminders, reschedule by text (S-19, S-86) |
   | AON / FOH | Phone; referral forms (S-95, S-96) | Phone or CareSpace portal (S-96) | 14-page packet (S-98); portal completion unknown (RQ-42) | CareSpace portal (S-96) |
   | NUM | Referral; phone, chat (S-102, S-104) | Evaluation by appointment (S-105); app appointment calendar (S-106) | Insurance details, MBI, physician documents (S-102) | myNumotion app: status, service requests, chat (S-106, documented capability) |

   **Clinical assessment** sits with clinicians at every platform and is outside the product. A published tool establishes that the tool exists. It does not establish that onboarding is complete, that the tools exchange data, or that they fail. The product is positioned as a **complement**, not a first digital front door (source-authority rule 5).
2. **The published processes are document- and prerequisite-heavy where it counts.**
   - CPS: a referral packet, insurance and member ID, photo ID, and plan-dependent referral and authorisation (S-11, S-12, S-75).
   - FOH: a 14-page packet with records release, consents and insurance (S-98).
   - NUM: an MBI, primary and secondary insurance, a physician face-to-face visit and a Letter of Medical Necessity (S-102).
   - AdaCare: a 4-page paper packet (S-82).
   - MVC: light (four fields).
3. **Published timing promises exist, but performance data does not.**
   - CPS states its scheduling aim three ways (S-12, S-68, S-70).
   - MVC publishes 24–48-hour verification and estimate windows (S-87).
   - NUM publishes step durations (S-23) and a 15–60-day approval range (S-102).

   None publishes how often those promises are met (RQ-38).
4. **Attributed review evidence clusters in the administrative layer between visits:** reaching a person, schedule changes, authorisation status, repeated data entry and unclear next steps. Clinicians and in-person staff are usually praised. At CPS, six low reviews name an "AI" system and one a "robot answering" system. They report a booking that was not found at check-in, no route to a human, and the same link sent four times. **These reports do not establish a vendor, a technical cause or a frequency.** Many cited low reviews concern established patients or existing appointments rather than first registration ([review report §7](2026-10-15-google-review-sentiment.md#7-patient-status-and-journey-stage-of-the-cited-complaints)). Positive reviews identify behaviours worth preserving: listening, explanations, reminder and pre-visit calls, insurance and payment help.
5. **The first pass got several facts wrong** (corrected here):
   - CPS has 33 offices in 7 states.
   - CPS publishes self-pay (uninsured only), a $50 fee for cancelling with less than 24 hours' notice, and a scheduling aim.
   - The SSN in the CPS referral packet is a referring-provider field, not a patient request field.
   - Numotion's documentation step is 2–4 weeks.

### Highest-value opportunities (first-pass view; now candidates in the selection matrix)
These were this report's first-pass ranking. They are now candidates `SOL-001`, `SOL-002`, `SOL-003` and `SOL-004` in the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md), which owns the ranking. None is selected.
1. **Readiness tracker.** One record of what the patient has already given, plus a patient-visible readiness status: referral, coverage, authorisation, documents, appointment. It is reusable on every platform. It is the most direct support for CPS's ten-day promise and MVC's quote-before-visit promise.
2. **Collect once, reuse everywhere.** Insurance card and ID capture with confirmation, carried into every later form (CPS, FOH, AdaCare).
3. **Guaranteed human handoff and honest status messaging.** No message promises a time the company has not set.

### Proposed demo angle (not selected)
**Commonwealth new-patient readiness.** A synthetic patient requests care, photographs an insurance card and a photo ID (OCR with confirmation), and answers the motor-vehicle and work-injury questions. They see a status page reading "We're contacting your doctor for a referral — here's what happens next". Staff see a summary with what is missing. The scenario uses the company's real published fields (S-75), arrival instructions (S-12), fee policy (S-12) and scheduling aim (S-68), with synthetic everything else. Which capabilities the demo shows beyond the mandatory four flows depends on Innocent's selection in the matrix.

### Anchor reassessment (after comparing all five)
**Commonwealth remains the anchor.**
- It has the richest published intake requirements.
- It has an explicit, measurable access promise.
- It has 33 offices on one website, with one request form and one fax line.
- It is in AEA's Elevate group.

AdaCare/ADC is the best **second** configuration: it tests reuse across a group scheduler and shows a lighter dental flow. MVC is the best **benchmark** of a light front door. FOH is the best example of a **long administrative packet** but should not lead a demo (clinical urgency). Numotion stays adjacent.

### Is "closing the seams between existing systems" a finding?
**It remains a hypothesis**, now better grounded.

What is **verified**: CPS operates several patient-facing tools at once — a third-party request form (S-75), a virtual agent for scheduling (S-66), an athenahealth portal (S-64) and records requests via ChartRequest (S-64).

What is **reported**: patients describe information asked repeatedly and an automated booking confirmation not found at check-in (S-77).

What is **not established**: whether those tools exchange data, which tool any reviewer used, and how often anything fails. The claim may be stated as "patients report seams; the company runs several front-door tools" and should be tested in discovery (RQ-28, RQ-38). It must not be stated as a diagnosis.

---

## 2. Company Intelligence Profile

Full facts with sources are in each company profile. This section is the comparison view (Part 1A, 1C, 1D).

### 2.1 Business profile (Part 1A)

| Item | CPS | ADC (platform) · AdaCare (practice) | MVC | AON (platform) · FOH (practice) | NUM |
|---|---|---|---|---|---|
| Organisation type | Specialty physician practice group, interventional pain (AEA, S-10) | Dental partnership organisation; doctor-led practices (S-78) · general and restorative dental practice (S-81) | Vein-disease clinic network (S-17, S-85) | Community-oncology platform: pharmacy, pathology, EMR and management services (S-92) · oncology and hematology practice (S-94) | Complex rehab technology supplier plus service and repair (S-101) |
| Footprint | 33 offices, 7 states (S-69) | 76 practice links / 74 entries, 15 states (S-14) · 1 office, Meridian ID (S-81) | 80 clinics, 9 states (S-89) | Network count **not publicly established** (S-93 paged) · 5 offices in 4 FL cities (S-96) | 114 branches, 45 states (S-105) |
| Mode | In person; telehealth not stated on the pages read; portal and virtual agent (S-66) | In person (S-81) | In person (S-90) | In person; AON offers browser telehealth to practices (S-92) | Clinic or branch evaluation; in-home, in-shop and remote repair (S-106) |
| Care model | Longitudinal: procedures in series, medication management, chronic care management (S-12, S-66) | Recurring preventive plus episodic restorative (S-16) | Evaluation, then a series of procedures (S-86) | Longitudinal treatment and survivorship (S-97) | Episodic equipment order plus years of repair |
| Stated eligibility | Referral required for some or most plans (conflicting, S-12); MVA after PIP is exhausted; workers' comp needs authorisation (S-12) | AdaCare treats "grown-up teeth only"; young children referred on (S-16) | Free evaluation "subject to insurance eligibility" (S-88); cosmetic care self-pay (S-86) | Entry "through a physician's referral or transfer", or by phone (S-95) | Medical necessity, a physician face-to-face visit and an LMN for complex chairs (S-102) |

### 2.2 Providers and resources (Part 1C)

| Item | CPS | AdaCare | MVC | FOH | NUM |
|---|---|---|---|---|---|
| Names and credentials | Directory with credential and offices (S-71); physicians "Board Certified Pain Medicine" and "Board Certified Anesthesiology" (S-72); NPs, APRNs and a PT listed | One dentist named on the site (S-16) | ABVLM certification claimed for all doctors (S-86); physicians named per clinic (S-90) | 10 physicians, 15 advanced practitioners (S-94) | ATPs and technicians (roles, S-101); named staff not used |
| Which office offers what | Office pages list providers (S-70); referral form maps physicians to offices (S-74) | Single office | Per-clinic pages (S-90) | Per-office referral forms (S-96) | Per-branch services (S-105) |
| Matching to a provider | Request form asks for a preferred clinic, not a provider (S-75); the referral form lets a referrer tick a physician (S-74) | Not established | Not established | Referral names a physician only if the referrer chooses | ATP assigned (inferred) |
| Live availability visible | No (form → callback, S-75) | **Yes for a New Patient Visit:** dates and times shown before personal details (S-83, re-read 2026-10-15). The first pass recorded slots as not established because the widget did not render | No (form → callback, S-88) | No (call or portal, S-96) | No |
| Stated response or wait | Scheduling aim of 10 days, ten business days or two weeks after referral (S-12, S-68, S-70) | None found | Verification 24–48 h; estimate callback 24–48 business h (S-87) | "Minimum" waits; no number (S-95) | Step durations (S-23); approval 15–60 days (S-102) |

### 2.3 Financial and insurance (Part 1D)

| Item | CPS | AdaCare | MVC | FOH | NUM |
|---|---|---|---|---|---|
| Plans accepted | Listed per state, with notes (S-67) | "most major dental insurances"; no list (S-16) | 200+; top-plans list; Medicaid in select states (S-87) | "most major insurance plans"; no list (S-95) | Medicaid and Medicare in all states plus most major carriers (S-103) |
| Self-pay | Uninsured patients only (S-12) | Implied by financing; one review mentions cash (S-84) | Yes (S-87) | Not stated; payment plans exist (S-97) | Out-of-pocket upgrades (S-104 FAQ) |
| Published prices | $50 fee for cancelling with <24 h notice (S-12) | $89 new-patient exam and X-rays (S-16); walk-in, cancellation and late fees on the paper form (S-82) | $425 per cosmetic session; $425–$1,500 self-pay range (S-86) | None | None |
| Verification | Staff verify before scheduling (S-12) | Patient sends insurance before the visit (S-16) | First call; 24–48 h (S-87) | Financial counsellor at an initial visit (S-97) | Verification, then prior authorisation after a referral (S-102) |
| Cost information | Estimates on request; payment plans (S-12) | Financial consultation at the first visit; CareCredit (S-16) | Quote before the first visit; estimate on request (S-87) | Counsellor; payment plans; assistance programmes (S-97, S-98) | Self-pay estimate in the app (S-106); CareCredit (S-103) |

**Financial information onboarding would need that no public page establishes (all platforms):** the patient's specific coverage and benefits; referral and authorisation status; the expected patient responsibility for the first visit; and whether a financial-assistance screen happens before or after booking. → RQ-7, RQ-39, RQ-41.

**Deliverable status:** complete for the public evidence available. Remaining unknowns are in Section 11.

---

## 3. Service Catalog and Patient Pathways (Part 1B)

For each major service: the problem, the patient, who delivers it, published prerequisites, the likely journey and whether it recurs. "Likely journey" is **Inferred** from published steps unless cited.

### 3.1 CPS
| Service | Problem / patient | Delivered by | Published prerequisites | Likely journey | Recurring? |
|---|---|---|---|---|---|
| New-patient pain consultation | Chronic pain lasting 3+ months (S-12) | Physicians, NPs, APRNs (S-71) | Referral for some or most plans; insurance verification; ID, card, co-pay, imaging (S-11, S-12) | Request (S-75) → staff contact PCP (S-70) → booking → first visit | Yes: care plan |
| Interventional procedures (injections, blocks, ablation, kyphoplasty, neurostimulation) | Spine and joint pain (S-76) | Physicians | Prior authorisation (days to weeks, S-12); fasting; a driver if sedated (S-12) | Consult → plan → authorisation → procedure → follow-up | Often in "a series of two or three" (S-12) |
| Medication management | Chronic pain (S-76) | Physicians, APRNs | Not publicly established | Recurring visits | Yes |
| Chronic care management, behavioral health integration, remote therapeutic monitoring | Chronic pain plus other conditions; emotional effects (S-66) | Care team | "eligible patients" (S-66) | Enrolled by the care team | Yes |
| Occupational medicine and workers' comp | Work injuries (S-76) | Occupational medicine specialist (S-12) | Authorisation before scheduling (S-12) | Employer or insurer authorisation → visit | Episode |
| Motor-vehicle injuries | MVA pain (S-12) | Physicians | Seen "once PIP is exhausted" (S-12) | Claim status → visit | Episode |

**Relationships (Inferred, not clinical indications):** a procedure follows a consultation; care management and behavioral support are offered to "eligible patients" at the care team's discretion (S-66).

### 3.2 ADC / AdaCare
| Service | Problem / patient | Delivered by | Prerequisites | Likely journey | Recurring? |
|---|---|---|---|---|---|
| New-patient exam and X-rays ($89) | New adult patients (S-16) | Dentist and team | Insurance details before the visit; forms (S-15, S-16) | Book → forms → exam; cleaning usually a separate visit (S-16) | Recall about every 6 months (S-15) |
| Restorative (dentures, crowns, implants, full-arch) | Missing or damaged teeth (S-81) | Dentist; on-site lab mentioned in reviews (S-84) | Financial consultation (S-16) | Exam → plan → financing → multi-visit | Episode, then maintenance |
| Periodontics and cleaning | Gum disease (S-81) | Dentist, hygienist | Exam first (S-16) | Exam → separate cleaning visit | Yes |
| Sedation (nitrous, oral) | Anxious patients (S-81) | Dentist | Not publicly established | Discussed at consultation | Per procedure |

At platform level, ADC lists central scheduling, recall and treatment tracking (S-79). Whether AdaCare uses them is **not publicly established** (RQ-40).

### 3.3 MVC
| Service | Problem / patient | Delivered by | Prerequisites | Likely journey | Recurring? |
|---|---|---|---|---|---|
| Free evaluation with ultrasound | Leg symptoms, visible veins (S-88) | Vein specialists and ultrasound techs (S-86) | "Subject to insurance eligibility" (S-88) | Form or call → verification → evaluation → plan (S-87) | No |
| Medical vein treatments (RFA, sclerotherapy, VenaSeal and others) | Chronic venous insufficiency (S-86) | Physicians | Pre-authorisation after evaluation (S-87) | Evaluation → authorisation → treatment series → compression | Often a series (inferred) |
| Cosmetic spider-vein treatment | Cosmetic concern (S-86) | Physicians | Self-pay, $425 per session (S-86) | Evaluation → self-pay | Sessions |

### 3.4 AON / FOH
| Service | Problem / patient | Delivered by | Prerequisites | Likely journey | Recurring? |
|---|---|---|---|---|---|
| New-patient oncology or hematology visit | Cancer or blood disorder; second opinions (S-95) | Physicians, APRNs, PAs (S-94) | Referral or transfer, or a phone call; insurance card; medication list (S-95); 14-page packet (S-98) | Referral → Patient Services Specialist contact (S-96) → packet and records → first visit → financial counsellor (S-97) | Yes |
| Infusion, BiTE, radioligand, oral oncolytics (pharmacy) | Treatment (S-94) | Clinical team | Clinician-directed | Out of intake scope | Yes |
| Imaging, lab | Diagnostics (S-94) | Imaging and lab | Imaging preparation instructions published | Clinician-ordered | As ordered |
| Care coordination, dietitian, financial support, survivorship | Barriers to care, nutrition, cost (S-97) | Coordinators, RD, counsellors | None stated; the dietitian is free (S-97) | Offered during care | Yes |

### 3.5 NUM (equipment workflow kept separate)
| Service | Problem / patient | Delivered by | Prerequisites | Likely journey | Recurring? |
|---|---|---|---|---|---|
| New complex wheelchair / seating | Permanent mobility limitation; all ages (S-101) | ATP plus physician or therapist | Referral; physician face-to-face visit; LMN; primary and secondary insurance; MBI for Medicare (S-102) | Evaluation (1 wk) → documentation (2–4 wk) → funding (2–8 wk) → build and delivery (2–8 wk) (S-23) | Replacement subject to payer rules (Medicare 5 years, S-102) |
| Repair (in-home, in-shop, remote) | Equipment failure (S-106) | Technicians | Serial number, make, model; description of the issue (S-106) | Request → diagnosis → parts → return visit | Yes |
| Catheters, speech solutions, retail | Other needs (S-101) | Specialists | Not reviewed | Separate lines | — |

---

## 4. Company Positioning and Promises (Part 2)

Claims are quoted from company pages (**Verified**). Expectations and assessments are **Inferred**.

| Platform | Claim (source) | What a patient will expect | Does the visible onboarding reinforce it? | Opportunity for our product |
|---|---|---|---|---|
| CPS | "prompt scheduling" (S-64); appointments "within ten business days" (S-68) | A booking in under two weeks, and contact soon after asking | Partly. The form promises a follow-up but no timing; the path depends on the PCP referral, which the patient cannot see (S-70, S-75) | A readiness status ("referral requested on [date]"); a staff queue that watches the company's own ten-day target |
| CPS | "Care That's Built Around You"; "Our People Are The Difference … the best care starts with being heard" (S-64) | Being known and not repeating themselves | Reviews report repeated questions (S-77, Reported) | Collect once; staff summary |
| CPS | "24/7 Virtual Agent … connect you with the appropriate member of your care team when needed" (S-66) | Reaching a human when needed | Reviews report not reaching one (Reported) | Every automated path ends with a documented human handoff |
| ADC | "Patient Care, Team Care, Business Care"; "Full Oversight of Patient Communications" (S-78, S-79) | Consistent, well-run practices | AdaCare is consistent but paper-based (S-82) | A digital packet reusable across practices |
| AdaCare | "One-Stop-Shop for Complete Dental Care"; "detailed financial consultation" (S-81, S-16) | Clear costs before treatment | Yes: $89 published; financing explained (S-16) | Show the published price and financing at booking |
| MVC | "We treat people, not symptoms."; free evaluation; 200+ plans; "No chat bots, no guesswork" for insurance (S-85, S-87) | Free, simple, a person on insurance | The front door is simple (4 fields); the chatbot (S-19) and the "No chat bots" wording may confuse | Honest labelling of automated vs human steps; capture insurance at request to enable the published pre-visit quote |
| AON/FOH | "Patient First, Always"; navigation "throughout your entire care journey" (S-94, S-97) | Guidance from the first call | Entry is by phone or referral; scheduling is phone or portal only (S-96) | Referral/transfer intake with records checklist and acknowledgement |
| NUM | "Expert guidance & support … ensuring a smooth, stress-free process"; "Real-Time Order Information" (S-101, S-106) | Knowing where the order is | The app provides status; reviews report chasing (Reported) | Front-of-journey intake; status explanations tied to the published step times |

**What experience is each company teaching patients to expect?**
- CPS teaches **speed and being heard**.
- MVC teaches **free and easy**.
- FOH teaches **guided and personal**.
- AdaCare teaches **comfort and clear cost**.
- Numotion teaches **guidance through a complex process**.

In every case, onboarding reinforces the promise by doing three things. It shows the patient where they stand. It never asks twice. It tells the truth about timing.

---

## 5. Current Onboarding Journey (Part 3)

The patient's objective is in brackets after each stage name. "Unclear" means not publicly established. No requests, forms or appointments were submitted.

**What this section can and cannot show.** These tables reconstruct the *publicly visible* journey: entry points, published requirements and attributed reports. They do not reconstruct internal workflows. Registration can happen before a visit, on arrival, or across both, and booking and paperwork have no universal order (S-108). The [journey baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md) owns the reference journey used for comparison.

### 5.1 CPS
| Stage [objective] | What the site offers (Verified) | Friction / unclear | Consequence |
|---|---|---|---|
| 1 Is my problem treated? [know it's the right place] | Conditions and services pages (S-76); FAQ (S-12) | Clear | — |
| 2 Right provider or service [choose] | Office finder with hours (S-69); provider directory (S-71) | Patients pick a clinic, not a provider (S-75); how matching works is unclear | A patient may expect a specific doctor |
| 3 Request care [start] | Online form (S-75); phone (S-12); referral fax (S-11) | Two new-patient numbers (502-890-5639 on S-11; (502) 855-7200 in the FAQ, S-12) plus each office's own number (S-69) | Uncertainty about which number to use |
| 4 Information requested [give it once] | Form fields (S-75); bring card, ID, co-pay and imaging (S-12) | No upload; ID and card are seen in person; the referral comes separately from the PCP | Re-entry at check-in (Reported, S-77) |
| 5 Tools and channels [know the path] | Form, phone, email, fax, athenahealth portal, virtual agent (S-11, S-66, S-75) | Which tool to use for what is unclear | Patients bounce between channels (Reported) |
| 6 Response time [know when] | Aim: 10 days / ten business days / two weeks after referral (S-12, S-68, S-70) | Three phrasings; no time for the first callback | Anxious waiting |
| 7 Confirmation and preparation [be ready] | Arrival times; what to bring; procedure preparation (S-12) | How confirmations are sent is not publicly established; review describes an automated text confirmation (Reported) | Arriving unprepared, or for an appointment not in the system (Reported) |
| 8 What happens next [see the path] | 3-step path (S-70) | Referral and authorisation status not visible | "Run around" (Reported) |
| 9 Ask questions [reach someone] | Phone; portal for existing patients; virtual agent (S-64, S-66) | Reaching a person (Reported) | Lost new patients (Reported) |
| 10 Follow-up [continuity] | Procedures in series; care management (S-12, S-66) | How follow-ups are scheduled is unclear | Gaps between procedures (Reported) |

### 5.2 AdaCare (practice example for ADC)
| Stage [objective] | Offered (Verified) | Friction / unclear | Consequence |
|---|---|---|---|
| 1 Treated here? | Services list (S-81); not young children (S-16) | Clear | — |
| 2 Provider | One dentist named | — | — |
| 3 Request | Phone; Book Now widget (S-16, S-83) | Widget shows new-patient services and New Patient Visit slots before personal details (S-83, re-read); later steps not viewed | — |
| 4 Information | Paper packet: demographics incl. SS# field, two insurances, consents with fees (S-82) | Print or arrive 10 min early (S-16) | Paperwork in the waiting room |
| 5 Channels | Phone, widget; e-communications consent (S-82) | — | — |
| 6 Response time | Not stated | Unclear | — |
| 7 Confirmation and preparation | Bring ID and insurance "typically" (S-15); send insurance in advance (S-16) | Benefits check depends on the patient calling | First visit without verified benefits |
| 8 Next steps | Cleaning usually a separate visit; financial consultation (S-16) | Patients may expect same-day cleaning | Disappointment avoided only if told early |
| 9 Questions | Phone | — | — |
| 10 Follow-up | Recall (S-15) | — | — |

### 5.3 MVC
| Stage [objective] | Offered (Verified) | Friction / unclear | Consequence |
|---|---|---|---|
| 1 Treated? | FAQ; treatment pages (S-86) | "Free" is "subject to insurance eligibility" (S-88) | A surprise if not eligible |
| 2 Provider | Clinic pages with physicians and hours (S-90) | Provider choice unclear | — |
| 3 Request | 4-field form; phone; chatbot (S-88, S-19) | Callback timing for scheduling not stated | — |
| 4 Information | Insurance at scheduling for the pre-visit quote (S-87) | Captured by phone (inferred) | Quote fails if insurance is missing |
| 5 Channels | Form, chatbot, five phone numbers across pages, SMS (S-86, S-87, S-88) | Many numbers | Confusion |
| 6 Response | Verification 24–48 h; estimate 24–48 business h (S-87) | Clear | — |
| 7 Confirmation and preparation | SMS reminders; reschedule by text (S-86) | Directions and preparation delivery unclear; Reported missing | Arriving at the wrong time (Reported) |
| 8 Next steps | Six-step insurance process (S-87) | Clear on paper | — |
| 9 Questions | Specialist phone line (S-87) | — | — |
| 10 Follow-up | Treatment series; compression (S-86) | — | — |

### 5.4 FOH (practice example for AON)
| Stage [objective] | Offered (Verified) | Friction / unclear | Consequence |
|---|---|---|---|
| 1 Treated? | Services (S-94) | Clear | — |
| 2 Provider | Team page (S-94) | Assignment unclear | — |
| 3 Request | Referral, transfer or phone (S-95); per-office referral forms (S-96) | Contact form cannot schedule (S-96) | Self-referring patients must phone |
| 4 Information | 14-page packet (S-98); bring medications and history (S-95) | Packet on paper | Long first visit |
| 5 Channels | Phone, CareSpace portal, fax (S-96) | Whether the packet can be done in the portal is unclear (RQ-42) | — |
| 6 Response | "Minimum" waits (S-95) | No number | Uncertainty for a frightened patient |
| 7 Confirmation and preparation | SMS/email consent covers reminders (S-98); imaging preparation (S-94) | — | — |
| 8 Next steps | Financial counsellor; care coordination (S-97) | — | — |
| 9 Questions | Phone; after-hours answering service (S-96) | Reaching scheduling (Reported) | Lost referral (Reported) |
| 10 Follow-up | Survivorship, coordination (S-97) | — | — |

### 5.5 NUM (front of journey; equipment workflow after)
| Stage [objective] | Offered (Verified) | Friction / unclear | Consequence |
|---|---|---|---|
| 1 Right supplier? | Services, adult and pediatric pages (S-101) | — | — |
| 2 Branch | Branch finder (S-105) | — | — |
| 3 Request | Referral starts the insurance process (S-102); evaluation by appointment (S-105) | How a customer self-starts is unclear (RQ-43) | — |
| 4 Information | Primary and secondary insurance; MBI (S-102) | Collected by phone (inferred) | Delays if missing (S-102 says so) |
| 5 Channels | National line, chat, app, branch phone (S-104, S-105) | Branch reachability (Reported) | — |
| 6 Response | Step times (S-23); approval 15–60 days (S-102) | Clear on paper | — |
| 7 Preparation | Repair: have the serial number ready (S-106) | — | — |
| 8 Next steps | App status (S-106) | Proactive updates (Reported) | Chasing |
| 9 Questions | 800 number; after-hours hours (S-104) | — | — |
| 10 Follow-up | Repairs; replacement eligibility (S-102) | — | — |

---

## 6. Patient Friction Assessment (Part 4)

Each row combines published evidence (Verified) and attributed reports (Reported). Product responses are **Proposed**. Indicators are suggestions; baselines are unknown (Section 9).

| Category | What companies publish | Friction or gap | Why it matters (patient state) | Onboarding response | Operational / financial consequence | Indicator |
|---|---|---|---|---|---|---|
| Urgency and responsiveness | CPS ten-day aim; MVC 24–48 h; NUM step times | No first-callback time at CPS, FOH or AdaCare; reports of unreturned calls (CPS, FOH, NUM) | People in pain or facing cancer read silence as being forgotten | Instant acknowledgement; status page; callback windows **only if the company sets them** | Repeat calls; lost referrals | Time to first human contact; repeat calls per request |
| Qualified provider access | Directories, clinic pages | Matching rules unpublished; CPS form chooses a clinic only | Uncertainty whether "my doctor" is there | Show the providers at the chosen office; record a preference for staff | Wrong-office bookings | Reassignments per new patient |
| Intake speed and simplicity | CPS form about 20 required fields; MVC 4 fields; FOH 14-page packet; AdaCare 4-page paper packet | Paper packets; re-entry reported at CPS | Fatigue, pain and anxiety make long forms harder | OCR with confirmation for card and ID; contact data first, everything else at pre-visit; conditional questions | Front-desk minutes; late starts | Completion time; packet complete before arrival (%) |
| Journey transparency | CPS 3-step path; MVC 6 steps; NUM 4 steps | Referral and authorisation status invisible to patients | Not knowing "what's next" increases stress and calls | Readiness tracker that mirrors each company's published steps | Calls asking "where am I?" | Status-page visits vs calls |
| Communication and visibility | SMS reminders (MVC); SMS/email consent (FOH, AdaCare); app (NUM) | Reports of time changes without notice and missing directions (MVC) | Arriving at the wrong time wastes a day off work | Change notices with reason and rebook; preparation messages from approved content | Lost slots; no-shows | Arrivals with a mismatched time; same-day reschedules |
| Financial certainty | CPS fee and self-pay; AdaCare $89; MVC price range and quote; NUM CareCredit | Coverage specifics unknown until verified; FOH counsellor at the visit | Fear of surprise bills | Show the published prices and policies; "coverage check in progress" status; never promise approval | Bad debt; cancellations | Coverage verified before visit (%) |
| Trust and psychological safety | Privacy notices (S-73, S-99); FOH form says don't send SSN by web form | SSN fields on paper forms (AdaCare, FOH) and in the CPS referral packet | Sensitive data plus sensitive conditions | Ask only what each step needs; explain why; consent capture; human route at any point | Abandonment at sensitive fields | Drop-off by field |
| Confidence in being understood | "being heard" (CPS); "Patient First" (FOH) | Repeated questions reported (CPS) | Repeating a pain or cancer story is tiring | One shared administrative summary; reuse confirmed data | Staff time; duplicate data | Fields re-asked per visit |

**Avoiding duplication:** callbacks appear only under urgency and responsiveness; status only under transparency; change notices only under communication.

**Emotional state:** pain patients may be exhausted and sceptical, especially those who expect to be treated as "drug seekers" (Reported at CPS). Oncology patients are frightened and time-sensitive. Mobility customers are often caregivers managing long waits. Onboarding reduces stress with control (save and resume, choose a channel), clear "what's next" information, accessible text and a human handoff. It must avoid the dark-pattern line set out in RQ-24.

---

## 7. Additional Care Opportunity Matrix (Part 5)

> **Unresolved scope decision (RQ-44).** The [configuration annex](2026-10-15-configuration-specification.md) excludes medical history from the product, while this matrix and three fictional scenarios ask optional questions about other conditions, prior treatment, sleep, pregnancy and nutrition. Those questions are clinical-adjacent patient-reported context. Until Innocent decides RQ-44, treat this section as research on the template's Part 5, **not** as product scope. The selection matrix parks the idea as `P-01`. The administrative items here (#8 practical barriers and #11 existing equipment) are separate candidates there (`SOL-017`) or adjacent.

**How the administrative-only rule constrains this part.** The template asks for intake questions that help a clinician "recognize additional patient needs", and for the revenue such needs might create. In this product, the software **only records what the patient chooses to tell it, in the patient's words**. It passes that to staff and clinicians as a labelled, unscored note. The software never suggests a service to the patient, never scores need, never orders tests and never states that a service is indicated. Revenue arises only if a clinician independently recommends a service and the patient accepts. The column below explains that chain; it is not a target.

| # | Platform · primary service | Information (patient-reported) | Patient-friendly question | What the answer shows | Clinician assesses | Possibly relevant company service | Why it may improve care | Legitimate revenue chain |
|---|---|---|---|---|---|---|---|---|
| 1 | CPS · new-patient consult | Other ongoing conditions | "Are you being treated for any other long-term health conditions? (optional)" | Possible multiple chronic conditions | Eligibility and appropriateness | Chronic Care Management (S-66) | Coordinated care between visits | Clinician offers → patient enrols → billable care management |
| 2 | CPS · consult | Effect on mood and sleep (self-described) | "Is pain affecting your sleep, mood or daily activities? (optional)" | The patient's own priorities | Whether behavioral support fits | Behavioral Health Integration; psychological pain assessment (S-66, S-76) | Whole-person care the company itself advertises | Clinician refers → patient accepts |
| 3 | CPS · consult | Prior physical therapy | "Have you tried physical therapy for this pain?" | Treatment history | Next steps | PT referral (S-12, S-74) | Avoids repeating what failed | Clinician decides |
| 4 | AdaCare · new-patient exam | Date of last cleaning | "When was your last dental cleaning?" | Recall gap | Hygiene needs at exam | Cleaning visit (S-16) | Sets expectations (cleaning is usually separate) | Dentist recommends → scheduled |
| 5 | AdaCare · exam | Dental anxiety | "Is there anything that makes dental visits hard for you?" | Comfort needs | Whether sedation options are appropriate | Sedation dentistry (S-81) | Reduces avoided care | Dentist offers → patient accepts |
| 6 | MVC · free evaluation | Pregnancy status (administrative scheduling flag only) | "Are you currently pregnant? (We ask because it can affect timing.)" | A timing consideration the company publishes (S-86) | Timing of evaluation and treatment | — | Avoids unsuitable scheduling | None: a safety and timing item |
| 7 | MVC · evaluation | Prior vein treatment or compression use | "Have you had vein treatment or worn compression stockings before?" | History for the evaluation | Treatment planning and coverage documentation | Compression therapy (S-90) | Fuller history | Clinician decides |
| 8 | FOH · new-patient visit | Practical barriers (transport, cost, caregiving) | "Would help with transportation, costs or caregiving make it easier to attend appointments? (optional)" | Non-medical barriers | Care-coordination referral | Care coordination; financial counsellor; assistance programmes (S-97, S-98) | The company says it addresses these barriers | Coordinator engages; assistance offsets cost |
| 9 | FOH · first visit | Interest in clinical trials | "Would you like information about clinical trials? (optional)" | Patient preference only | Eligibility | Clinical trials (S-94) | Access to studies close to home | Research team decides |
| 10 | FOH · first visit | Nutrition concerns | "Do you have concerns about eating or weight? (optional)" | Self-reported concern | Need for a dietitian | Free dietitian (S-97) | Supports treatment tolerance | None (dietitian visits are free) |
| 11 | NUM · new equipment | Existing equipment and its condition | "Do you already use a wheelchair or seating system? How old is it, and does it need repair?" | Repair need; replacement timing | ATP review; payer rules (e.g. Medicare 5-year, S-102) | Repair service (S-106) | Keeps the person mobile during the order | Repair billed if covered or self-pay |
| 12 | NUM · intake | Communication needs | "Does the user have difficulty speaking that affects daily communication? (optional)" | Possible AAC need | Specialist assessment | Speech solutions (S-101) | Unmet communication need | Specialist recommends → funded or self-pay |

**Prioritised for minimal patient effort:** #1, #4, #8 and #11 (one short question each, high value to staff). Every item is optional, labelled with why it is asked, and shown to staff as "patient-reported, not assessed".

---

## 8. Software Configuration Specification (Part 6)

The full per-company tables are in [Annex 1](2026-10-15-configuration-specification.md). Each row has *item · published value (Verified) · proposed configuration · simulated demo value · source · status · information still needed*. Summary:

### 8.1 Reusable core vs company configuration
| Core capability (build once) | What each company configures |
|---|---|
| Request intake with conditional questions | Field list (CPS: the ~20 required fields of S-75; MVC: 4 fields; FOH: referral/transfer branch; NUM: who is completing intake) |
| Document capture with OCR **and user confirmation** | Which documents: CPS photo ID and insurance cards; FOH insurance and records release; NUM insurance plus MBI; AdaCare insurance |
| Readiness tracker | Step names and published durations (CPS 3 steps; MVC 6; NUM 4; FOH referral → packet → counsellor) |
| Staff summary and handoff queue | Who receives it (unknown everywhere: RQ-4, RQ-27) |
| Approved help content library | Each company's own FAQ and preparation text (RQ-10) |
| Consent and communication preferences | SMS/email consent text (FOH S-98; AdaCare S-82; MVC SMS terms S-19) |
| Scheduling handoff (no live booking against real calendars in the demo) | Target system: CPS staff callback; ADC Jarvis widget; MVC callback; FOH phone or portal; NUM branch |
| Status and reminder messaging | Wording, timing windows **set by the company** |
| Accessibility and language | Spanish (MVC has /es; FOH has Spanish documents) |

### 8.2 Intake configuration: contact vs pre-visit
- **Initial contact (minimum):** name, best contact method, date of birth (CPS requires it; MVC does not), reason for request in the patient's words, preferred location, and insurance carrier and member ID where the company quotes before the visit (CPS, MVC).
- **Pre-visit:** ID and insurance-card images (confirmation required), policyholder details, consents, records release (FOH), referring and primary-care provider, MVA and work-injury details (CPS), equipment details (NUM).
- **Conditional examples:**
  - CPS "work injury = yes" → authorisation notice and the occupational medicine line (S-12).
  - CPS "MVA = yes" → the PIP notice (S-12).
  - CPS "uninsured" → the self-pay notice (S-12).
  - FOH "transfer = yes" → records-release step (S-98).
  - NUM "standard Medicare" → MBI field (S-102).
  - AdaCare "child with baby teeth" → pediatric referral notice (S-16).
- **Never collected by the product in the demo:** SSN. The CPS online form does not require it (S-75), and FOH tells patients not to send it by web form (S-96). Whether a company needs it later is RQ-15.

### 8.3 Workflow steps (template list)
Initial request → acknowledgement → **routing for staff review** → scheduling request → pre-visit intake → documents → preparation instructions → status updates → staff handoffs → clinician review of patient-reported notes → follow-up coordination.

**Constraint applied:** the template's "clinician-approved urgency screening or escalation" is implemented only as **displaying a company-approved emergency notice** (FOH's own wording: "If you are experiencing a medical emergency, please call 911", S-96) and **routing every request to staff**. The software does not classify urgency.

### 8.4 Communication examples (wording is Proposed; times only if the company confirms them)
- **Request received (CPS):** "Thanks, [first name]. We've received your request for Commonwealth Pain & Spine [office]. Next, our team will contact your doctor's office for a referral if your plan needs one. We'll update this page as each step is done."
- **Missing information:** "We still need a photo of the front and back of your insurance card. You can add it here or bring it to your visit."
- **Appointment confirmation:** "Your appointment is set for [date/time] at [office address]. New patients: please arrive 30 minutes early if you haven't completed your forms (company instruction)."
- **Preparation:** company-approved text only. For example, CPS's published list: "your current insurance card(s), photo ID, method of co-payment and any recent imaging" (S-12).
- **Scheduling delay:** "Your request is still with our scheduling team because we're waiting for [referral/insurance approval]. We'll message you when that changes." (No date unless the company supplies one.)
- **Status update (NUM):** "Your order is in Funding Approval. Numotion says this step usually takes about 2–8 weeks (company estimate). If your insurer contacts you, please respond quickly."
- **Follow-up reminder:** "Your new-patient forms aren't finished yet. Completing them before your visit can shorten check-in."

### 8.5 Integration requirements (visible; **not** integration evidence)
| Platform | Visible systems | Integration status |
|---|---|---|
| CPS | athenahealth portal and billing; prettygoodai request form; ChartRequest; virtual agent (S-64, S-66, S-75) | Requires company confirmation (RQ-18, RQ-25, RQ-28) |
| ADC | Jarvis Analytics scheduler; "Cloud-based centralized dental management software" (S-79, S-83) | Requires confirmation (RQ-40) |
| MVC | HubSpot (chatbot data); SMS programme (S-19) | Requires confirmation (RQ-13, RQ-41) |
| AON/FOH | OncoEMR; CareSpace portal; personapay (S-92, S-96, S-97) | Requires confirmation (RQ-42) |
| NUM | myNumotion app and portal; live chat (S-104, S-106) | Requires confirmation (RQ-43) |

---

## 9. Gap and Business Impact Matrix (Parts 7 and 8)

Each gap gives the current state with evidence, the gap, the proposed capability, value to the patient, operations and business, and how it would be measured.

**What "gap" means here.** A gap is a difference between the [reference baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md) and what is publicly visible or reported. It is not an established company deficiency: general guidance cannot prove a company's process falls short, and "Not publicly established" does not mean absent. Each row maps to candidates in the [selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md): G1 → SOL-001, SOL-006; G2 → SOL-003, SOL-004; G3 → SOL-002, SOL-007; G4 → SOL-005, SOL-004; G5 → SOL-004; G6 → SOL-007, SOL-008; G7 → SOL-005, SOL-009; G8 → SOL-002; G9 → SOL-004 (Numotion configuration) and parked P-03.

| # | Platform | Current state (evidence) | Gap | Proposed capability | Patient value | Operational value | Business value | KPI |
|---|---|---|---|---|---|---|---|---|
| G1 | CPS | Form → staff contact PCP → booking (Verified S-70, S-75); ten-day aim (S-68) | Patient can't see referral or coverage progress; first-contact time not stated (Not publicly established) | Readiness tracker with the company's 3 steps | Less uncertainty | Fewer status calls | Supports the access promise; conversion from request to visit | Days from request to first visit vs the company aim; requests that stall |
| G2 | CPS | Card, ID and imaging brought in person (S-12); re-entry reported (S-77) | No pre-visit capture of documents; data re-asked (Reported) | OCR with confirmation; collect-once record | Less typing and repetition | Shorter check-in | Fewer late starts and reschedules | Check-in minutes; fields re-asked |
| G3 | CPS | Several front-door tools (S-66, S-75, S-64) | Handoffs between tools unclear; reports of no human route and an unseen booking (Reported) | Documented human handoff; booking confirmed only from the system of record (**hypothesis**) | Reach a person | Clear ownership | Trust and retention | Handoff time; bookings matched at check-in |
| G4 | ADC/AdaCare | Paper packet (S-82); insurance sent by phone (S-16) | No digital pre-visit packet | Digital packet with insurance capture | Less waiting-room paperwork | Benefits verified in advance | Fewer first-visit surprises; reusable across practices (inferred) | Packet complete before arrival (%) |
| G5 | MVC | 4-field form; quote needs insurance at scheduling (S-87, S-88) | Insurance collected by phone after the form (inferred) | Optional card capture at request | A quote sooner | Fewer verification calls | Faster scheduling | Time to verified quote |
| G6 | MVC | SMS reminders exist (S-19, S-86); reports of times changed without notice (Reported) | Change and preparation messaging unclear | Change notices with reason; directions and preparation | Arrive at the right time | Fewer wasted slots | Higher show rate | Wrong-time arrivals; no-shows |
| G7 | FOH | 14-page paper packet; scheduling by phone or portal (S-96, S-98) | Packet completion before visit unclear (RQ-42) | Digital administrative packet; records-release checklist | Less burden at a frightening time | Records arrive earlier | Visits start on time | Records received before visit (%) |
| G8 | FOH | New-patient voicemails reported unanswered (Reported) | Referral and request queue visibility unclear | Acknowledgement plus a staff queue for referrals and transfers | Know the request landed | Nothing lost | Fewer lost referrals | Referral-to-contact time |
| G9 | NUM | Step times and an app (S-23, S-106); reports of chasing (Reported) | Front-of-journey data gaps (MBI, secondary insurance) cause delays (S-102 says so) | Front-of-journey intake with insurance completeness check | Fewer restarts | Fewer documentation loops | Faster funding submission | Days from referral to submission |

**Prioritisation** (impact × confidence × complexity, all Inferred):
- **G1, G2 and G7:** high impact, high confidence in the published process, medium complexity.
- **G5 and G4:** medium impact, high confidence, low complexity.
- **G6 and G8:** medium impact, medium confidence (rests on reports), low complexity.
- **G3:** high potential impact, **low** confidence (a hypothesis), high complexity (integration).
- **G9:** medium impact, medium confidence, and it touches a separate product.

### 9.1 Revenue and ROI hypotheses (Part 8)
**Mechanisms (cause → effect):**
- **Revenue:**
  - more requests become first visits (G1, G8): a visible status reduces silent drop-off;
  - fewer no-shows and wrong-time arrivals (G6): clear confirmation and change notices;
  - appropriate additional services only via clinician recommendation (Section 7).
- **Cost:**
  - fewer status and verification calls (G1, G5);
  - shorter check-in and fewer re-keyed fields (G2, G4, G7);
  - fewer documentation loops (G9).

**Three baselines, kept apart.**
- **Reference baseline:** recommended practice from guidance (S-108…S-118).
- **Company current-state evidence:** what each company publishes or a reviewer reports (this report, the profiles, the review report).
- **Measured baseline:** actual starting performance. **Unknown for every platform.** A synthetic demonstration can show behaviour; it cannot establish a real company's revenue or completion improvement.

**Baselines required from each company before any quantitative claim:**
- monthly new-patient requests by channel;
- request-to-first-visit conversion;
- the median and 90th percentile of days from request to first visit;
- calls per new patient;
- check-in minutes;
- no-show and late-cancellation rates;
- the share of visits with complete paperwork and verified coverage;
- referral/authorisation turnaround;
- and, for NUM, days per order step.

**Illustrative calculations (ILLUSTRATIVE — the numbers are assumptions, not company data):**
- *Conversion (revenue):* if a network receives **R** new-patient requests a month, a share **s** stall before a first visit, onboarding recovers a fraction **f** of those, and each completed first episode is worth **V** in contribution, then added contribution = R × s × f × V.
  Example with assumed values R = 1,000, s = 20%, f = 10%, V = $300: 1,000 × 0.20 × 0.10 × $300 = **$6,000 a month**. Every input must be replaced by company data.
- *Staff time (cost):* if each new patient generates **c** status calls of **m** minutes and the tracker removes a fraction **r** of them, minutes saved = R × c × m × r.
  Example with assumed c = 2, m = 6, r = 30%: 1,000 × 2 × 6 × 0.30 = **3,600 minutes ≈ 60 staff hours a month**.
- *No-shows (revenue protection):* if **N** booked first visits have a no-show rate **n**, and change and confirmation messaging reduces it by **d** points, recovered visits = N × d.
  Example with assumed N = 800, d = 2 points: **16 visits a month**.

The brief's own illustrative completion lift (50% → 70%, S-1) is an assumption too, and it is labelled as one there.

---

## 10. Fictional Patient Demo Blueprint (Part 9)

All 15 scenarios — three per company — are in [Annex 2](2026-10-15-demo-blueprint.md). Every patient, answer and document there is **SIMULATED**. Each scenario includes the patient-facing questions, the conditional non-clinical steps, how uncertainty is reduced, the staff summary, the items flagged for clinician review (patient-reported only), and a before/after comparison that separates what is Verified (public process) from what is Simulated.

| Platform | Scenario 1 (common) | Scenario 2 (obstacles) | Scenario 3 (other needs for professional review) |
|---|---|---|---|
| CPS | Referred patient with insurance, card and ID by photo | Work-injury patient without a PCP referral, worried about cost | Patient reports other chronic conditions and poor sleep (optional fields) |
| AdaCare | New adult patient wanting the $89 exam | Anxious patient with dentures, two insurances | Patient overdue for cleaning, with a child needing a referral |
| MVC | Leg-pain patient booking a free evaluation with Medicare | Spanish-preferring patient whose appointment time changes | Patient with cosmetic concerns, recently pregnant |
| FOH | Referred new patient with records to transfer | Transfer patient who can't reach scheduling and has cost worries | Patient reporting transport barriers and interest in trials |
| NUM | Caregiver starting a first power-chair order with Medicare plus secondary | Customer missing their MBI | Existing user needing repair while a new chair is funded |

**Proposed demo order (not selected):** CPS scenario 1, then scenario 2 to show conditional logic and the handoff. The third scenario for each platform depends on the unresolved RQ-44 scope decision; until it is decided, those scenarios are research illustrations, not demo-ready flows.

---

## 11. Unknowns and Company Discovery Questions (Part 10)

Format: **checked** (pages) → **unknown** → **effect on configuration or demo** → **placeholder (Simulated)** → **question** (RQ). Essential items come first.

### Essential (before any production system)
| Platform | Checked | Unknown | Effect | Placeholder (Simulated) | Question |
|---|---|---|---|---|---|
| All | Every page listed in S-64…S-106 | Request volumes, conversion, abandonment, days to first visit | No ROI claim possible | Illustrative inputs (Section 9.1) | RQ-2, RQ-3, RQ-38 |
| All | Contact and FAQ pages | Who owns intake follow-up (central vs office) | Handoff target | "Central intake team" queue | RQ-4, RQ-27 |
| CPS | S-12, S-67, S-75 | Which plans or services need a referral | Routing to booking vs referral step | Referral step shown for every insured patient | RQ-7, RQ-39 |
| CPS | S-66, S-75, reviews | What the virtual agent and form connect to; handoff rule | Whether we complement or overlap | Demo uses its own stub scheduler | RQ-28 |
| CPS | S-12 | What is mandatory before booking vs at check-in | The readiness rules | Insurance and member ID before booking; ID and card at pre-visit | RQ-6 |
| ADC | S-79, S-83 | Practice use of central services; which appointment types can be self-booked | Reuse claim | One demo practice; "new-patient exam" slot type | RQ-9, RQ-40 |
| MVC | S-87, S-88 | Eligibility rule for "free"; who sends directions and preparation | Messages | "Coverage check pending" notice | RQ-41 |
| FOH | S-95, S-96, S-98 | Hours; portal packet completion; referral queue | Packet and queue | Hours "Mon–Fri (company to confirm)" | RQ-42 |
| NUM | S-102, S-105, S-106 | Who starts intake; what the app shows per step | Scope boundary | Caregiver-started demo order | RQ-12, RQ-43 |
| All | Privacy pages (S-19, S-73, S-99) | Consent, retention and communications policy for a new tool | Legal readiness | Synthetic-only demo; consent screen text drafted | RQ-20, RQ-21, RQ-33 |
| All | — | Clinical escalation policy | Emergency notice wording | FOH's published 911 wording (S-96) | RQ-22 |

### Optional (optimisation)
- Brand voice and approved copy (RQ-10).
- Language coverage (MVC `/es`; FOH Spanish documents).
- Provider-level matching rules (CPS directory, S-71).
- Hours for every office (CPS publishes them; FOH not found).
- The full AON network list (S-93 paged).

---

## 12. Prioritized Product Recommendations

Ranked by likely impact, evidence confidence and implementation complexity (all Inferred).

> **Reconciled 2026-10-15.** This list was the first-pass recommendation. "Must-have" below meant "recommended for the demo", not "required by the brief". The brief's own requirements (four core flows, edge cases, security, performance, evals, submission) are mandatory regardless and are listed as M-01…M-15 in the [selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md). Every other item is a discretionary candidate there, ranked with a transparent rubric, and **Innocent selects the scope**. Mapping: 1 → SOL-001 (+ SOL-002); 2 → M-02 + SOL-004; 3 → SOL-005 (conditional branches) and SOL-006; 4 → SOL-002, SOL-003; 5 → M-04 + SOL-014; 6 → M-03; 7 → SOL-007, SOL-008; 8 → SOL-004; 9 → SOL-005, SOL-009; 10 → SOL-013; 11 → P-04; 12 → P-03; 13 → SOL-019; 14 → P-04 / RQ-28.

### Must-have for the demonstration (first-pass recommendation)
1. **Request plus readiness tracker** mirroring each company's published steps. It is the core of G1, G7 and G9. Confidence: high (the published processes). Complexity: medium.
2. **OCR with user confirmation** for ID and insurance card, with partial-extraction handling and a manual fallback (brief Core #2 and edge cases). It addresses G2 and G4. Confidence: high. Complexity: medium.
3. **Conditional, minimal question sets per company** (Section 8.2), including CPS's motor-vehicle, work-injury and self-pay branches. Confidence: high (S-12, S-75). Complexity: low.
4. **Staff summary and handoff queue**: what is missing, what the patient said, preferences. Confidence: medium (owners unknown). Complexity: medium.
5. **Approved help content at friction points**, drawn from each company's own pages (brief Core #4). Confidence: high (published content). Complexity: low.
6. **Synthetic scheduling handoff** with a booking confirmation and double-booking rejection (brief Core #3). It does not book into real calendars.

### High-value enhancements
7. Change notices and preparation messages (G6).
8. Optional insurance-card capture at the first request (G5).
9. Digital administrative packets: FOH and AdaCare forms (G4, G7).
10. Spanish language (brief stretch #5; MVC and FOH evidence).

### Longer term
11. Integration with systems of record — athenahealth, Jarvis, HubSpot, OncoEMR, myNumotion — only after discovery (Section 8.5).
12. A Numotion equipment-status companion (a separate design).
13. A network-wide funnel dashboard (brief stretch #7), once baselines exist.
14. Testing the "seams" hypothesis (G3) with CPS data (RQ-28, RQ-38).

---

## What I Need to Configure This Company in My Onboarding Software

### Commonwealth Pain & Spine
- **Verified and ready to use:**
  - 33 offices with addresses, phones and hours (S-69, S-70);
  - request-form field list (S-75);
  - published 3-step path (S-70);
  - arrival and what-to-bring instructions (S-12);
  - accepted ID types (S-11);
  - plans by state (S-67);
  - self-pay rule, $50 late-cancellation fee, payment plans (S-12);
  - scheduling aim in three phrasings (S-12, S-68, S-70);
  - MVA, PIP and workers' comp notices (S-12);
  - provider-to-office maps (S-70, S-74).
- **Can be simulated for the demo:** patients and their documents; staff queue and owners; referral outcomes; slots and confirmations; status timing within the company's stated aim, labelled as company aims.
- **Requires company confirmation:**
  - referral rules by plan (RQ-39);
  - mandatory-before-booking items (RQ-6);
  - virtual-agent and form integration and the handoff rule (RQ-28);
  - who owns intake follow-up (RQ-4);
  - baselines (RQ-38);
  - consent and communication policy.
- **Reusable vs company-specific:** see [Annex 1 §1](2026-10-15-configuration-specification.md#1-commonwealth-pain--spine).

### American Dental Companies (AdaCare as the example practice)
- **Verified and ready to use:**
  - AdaCare hours, address, services (S-81);
  - $89 new-patient offer and first-visit description (S-16);
  - forms packet contents and fees (S-82);
  - financing options (S-16);
  - group scheduler URL pattern (S-83);
  - ADC central services list (S-79).
- **Can be simulated:** appointment types and slots; benefits verification results; patients and documents.
- **Requires company confirmation:** which practices use central scheduling, recall and the dental management software (RQ-40); variation in forms and fees across practices (RQ-9); self-bookable appointment types; SSN need (RQ-15); minors and guardians (RQ-16).
- **Reusable vs company-specific:** [Annex 1 §2](2026-10-15-configuration-specification.md#2-american-dental-companies--adacare).

### Metro Vein Centers
- **Verified and ready to use:**
  - 80 clinics and states (S-89);
  - Forest Hills hours (S-90);
  - 4-field request form (S-88);
  - six-step insurance process and 24–48 h windows (S-87);
  - prices and self-pay (S-86);
  - reschedule-by-text rule (S-86);
  - SMS programme (S-19);
  - treatment list (S-86).
- **Can be simulated:** clinic schedules; verification outcomes; reminders; patients.
- **Requires company confirmation:** the eligibility rule for a free evaluation (RQ-41); confirmation and directions ownership (RQ-41); chatbot and CRM handoff (RQ-13); language capture.
- **Reusable vs company-specific:** [Annex 1 §3](2026-10-15-configuration-specification.md#3-metro-vein-centers).

### American Oncology Network (FOH as the example practice)
- **Verified and ready to use:**
  - FOH's 5 offices with phones and faxes (S-96);
  - entry routes (S-95);
  - what to bring (S-95);
  - the 14-page packet structure (S-98);
  - records-release form (S-99);
  - financial counsellor and payment plans (S-97);
  - contact-form limits and emergency wording (S-96);
  - AON platform systems (S-92).
- **Can be simulated:** office hours (placeholder); referral queue; patients; records.
- **Requires company confirmation:** hours; whether the packet can be completed in the portal; referral queue handling (RQ-42); variation across AON practices (RQ-11); escalation policy (RQ-22).
- **Reusable vs company-specific:** [Annex 1 §4](2026-10-15-configuration-specification.md#4-american-oncology-network--florida-oncology--hematology).

### Numotion (adjacent; equipment workflow kept separate)
- **Verified and ready to use:**
  - 114 branches in 45 states (S-105);
  - Nashville branch hours (S-105);
  - four-step process with published durations (S-23);
  - insurance tips: primary and secondary, MBI, Medicare 5-year rule (S-102);
  - medical-necessity steps (S-102);
  - payment options (S-103);
  - contact and after-hours channels (S-104);
  - repair preparation (S-106).
- **Can be simulated:** orders and step progress; insurer responses; customers and caregivers.
- **Requires company confirmation:** who starts intake and what is captured before the evaluation; what myNumotion shows per step (RQ-43); the boundary with the equipment workflow (RQ-12).
- **Reusable vs company-specific:** [Annex 1 §5](2026-10-15-configuration-specification.md#5-numotion-front-of-journey-only).

---

## Appendix A — Requirement audit

Checked on 2026-10-15 against [`docs/aea-portfolio-research.md`](../aea-portfolio-research.md). "Complete" means the template's requirement is **covered with the public evidence available** for all five platforms, with remaining unknowns stated. It does not mean the research is finished or signed off: company discovery questions remain open and Innocent has not approved the research stage.

| Requirement | Where | Status | Notes and remaining gaps |
|---|---|---|---|
| Part 1A Business profile | §2.1; profiles | Complete | AON network size not established (S-93 paged) |
| Part 1B Services and pathways | §3 | Complete | Journeys labelled Inferred where not published |
| Part 1C Providers and resources | §2.2 | Complete with gaps | CPS directory not fully enumerated (pager); AdaCare widget slots now seen for a New Patient Visit (S-83 re-read; post-slot steps not viewed); provider matching rules unpublished |
| Part 1D Financial | §2.3 | Complete | Plan lists not published by AdaCare or FOH |
| Part 1 deliverable (structured profile) | Profiles + §2 | Complete | — |
| Part 2 Positioning (5 sub-items, explicit vs interpretation) | §4 | Complete | — |
| Part 3 Journey (10 stages × 6 attributes) | §5 | Complete | Objectives given per stage; "unclear" items cross-referenced to RQs |
| Part 4 Eight friction categories × 6 attributes, emotional state | §6 | Complete | Indicators need baselines |
| Part 5 Additional care (8 fields), no upselling | §7 | Complete **under the administrative-only constraint** | The revenue field is explained as a clinician-and-patient chain, not a product target. Whether any optional clinical-adjacent question enters product scope is unresolved (RQ-44) |
| Part 6 Company, intake, workflow, communication, integration config; table with value/source/confidence/needed | §8 + Annex 1 | Complete | Urgency screening replaced by a company emergency notice plus staff routing (constraint) |
| Part 7 Gap analysis with the four evidence classes; prioritisation | §9 | Complete | Labels used: Verified / Reported / Not publicly established / Inferred / Proposed |
| Part 8 ROI mechanisms, revenue vs cost, baselines, illustrative calculations | §9.1 | Complete | No company data; all numbers labelled illustrative |
| Part 9 Three scenarios per company; patient, staff and before/after views | §10 + Annex 2 | Complete | All synthetic |
| Part 10 Unknowns; essential vs optional; placeholders | §11; RQ-38…RQ-43 | Complete | — |
| Research standards: URLs, assessment date, no fabrication, HIPAA/consent as review items | Throughout; register | Complete | UX research claims are labelled Inferred; no external UX study cited |
| 12-section order plus closing checklist | This file | Complete | — |
| Reviews as attributed experience; exact quotes; denominators; AI 6+1 | [Review report](2026-10-15-google-review-sentiment.md) | Complete | Reviewer names and identifiable narratives excluded |

**Disclosed limits:**
- **Automation limits:** pages that could not be read fully — the CPS provider pager and the AON locations map. The AdaCare booking widget did not render in the first pass; a later view-only recheck the same day loaded it (S-83). Its post-slot steps were not viewed, and no appointment request was submitted.
- **Not checked:** the AON locations of practices other than FOH; other ADC practices; MVC clinics other than Forest Hills and New York. One-practice evidence is labelled as such.
- **No company was contacted.** Every discovery question remains open.
