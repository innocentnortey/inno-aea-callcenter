# Onboarding Configuration Checklist — AEA Healthcare Platforms

> **⚠️ Superseded 2026-10-15 by the [research report](2026-10-15-onboarding-research-report.md).**
> This first-pass checklist is kept as history. Known errors (corrected in the report and the
> company profiles): Commonwealth's footprint is 33 offices in 7 states, not "20 cities in 3
> states"; SSN appears in the referral packet a referring provider faxes, not in the patient request
> form (S-75); the FAQ publishes self-pay (uninsured only), a $50 late-cancellation fee and a
> scheduling aim that this file missed; Numotion documentation is 2–4 weeks; some "Yes" cells in
> §6B presented company requirements without sufficient evidence. Read the report, not this file.
> **Historical only — do not cite.** Current owners: the [research report](2026-10-15-onboarding-research-report.md) and its annexes for company configuration, and the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md) for candidate solutions. Its booking-widget and channel rows are also superseded (S-83 re-read 2026-10-15).


**Date:** 2026-10-15 · **Built from:** `aea-portfolio-research.md` (Parts 1–10, the 12-section report format, and the closing "What I Need to Configure" list).
**Companies:** Commonwealth Pain & Spine (anchor) · American Dental Companies · Metro Vein Centers · American Oncology Network · Numotion (adjacent).
**Evidence labels (from the research file, Part 7):** **V** = Verified on a live page · **P** = Verified in the 2026-10-14 company profile, not re-checked today · **I** = Inferred, needs validation · **N** = Not publicly established · **C** = Needs company confirmation.
**Companion file:** [Google review sentiment](2026-10-15-google-review-sentiment.md).

Status key: `[x]` done with evidence · `[~]` partly done or profile-only · `[ ]` open.

---

## Part 1 — Company intelligence

### 1A. Business profile

| Item | Commonwealth Pain & Spine | American Dental Companies | Metro Vein Centers | American Oncology Network | Numotion |
|---|---|---|---|---|---|
| [x] Legal/brand name | Commonwealth Pain & Spine (mypainsolution.com) · V | American Dental Companies (ameridentco.com) · V | Metro Vein Centers (metroveincenters.com) · V | American Oncology Network; practice: Florida Oncology & Hematology · V | Numotion (numotion.com) · V |
| [x] Model | Specialty physician practice group, interventional pain · P | Dental partnership organisation; practices owned by dentist-partners · P | Vein-disease clinics · V | Community oncology network; integrated care platform · P | Complex rehabilitation technology provider · P |
| [x] Specialties | Interventional pain management, spine · P | General and cosmetic dentistry, dentures, implants · P | Varicose and spider veins, minimally invasive procedures · V | Medical oncology, haematology · V | Power and manual wheelchairs, custom seating, mobility · P |
| [~] Footprint | 20 cities in 3 states (KY, IN, IL) listed on the registration page · P (count not re-checked) | ~76 practices in 15 states (machine count, 2026-10-14) · P | 17 NY clinics listed · V; "80 locations across 9 states" · P (not re-checked) | 5 offices in 4 cities in FL (Cape Coral, Naples ×2, Fort Myers, Clearwater) · V | Nashville HQ; home-visit and clinic service · P |
| [~] Target patients | Adults with chronic pain referred or self-referred · P | Patients of partner practices (AdaCare: Meridian, Idaho) · P | Adults with venous disease, plus cosmetic spider-vein patients · V | Adults with cancer or blood disorders · V | Adults and children with permanent disabilities needing custom equipment · P |
| [x] In person / virtual / home | In person · V | In person · P | In person · V | In person · V | In person, plus home visits for delivery and repair · P |
| [~] Care model | Multi-visit, recurring; procedures in between · P | Recurring general dental care · P | Procedures plus follow-up · P | Recurring treatment cycles · P | Long, multi-step equipment process (evaluation → documentation → funding → delivery) · V |
| [ ] Eligibility rules | Most plans need a referral; some allow direct booking · P | Not established | Not established beyond insurance plans · N | Not established · N | Insurance-based; medical documentation required · V |

### 1B. Services and care pathways

| Item | Commonwealth | ADC (AdaCare) | Metro Vein | AON (FOH) | Numotion |
|---|---|---|---|---|---|
| [x] Patient problem served | Chronic back and neck pain · P | Dental care, extractions, dentures, cosmetics · P | Varicose and spider veins, leg discomfort · V | Cancer and blood disorders · V | Mobility loss, need for seating/wheelchair · P |
| [x] Clinician type | Pain physicians, nurses, X-ray techs · P | Dentist (DDS), dental team · P | Vein specialists, board-certified · V | Oncologists, haematologists, APRNs · V | Assistive Technology Professional (ATP), therapist, physician · V |
| [x] Referral or prerequisites | Referral needed for most plans; photo ID; insurance card; notes; imaging · V | Photo ID; insurance details · P | Free evaluation first · V | Records release and new-patient forms · V | Physician documentation · V |
| [x] Likely journey | Referral → insurance and prior auth → first appointment · P | Book → forms → visit · P | Free evaluation → insurance check → treatment · V | Referral or self-referral → forms and records → first visit · I | Evaluation → physician docs → funding → build/delivery · V |
| [~] Recurring care | Yes, injections and procedures · P | Yes · P | Yes, multi-session · P | Yes, treatment cycles · P | Yes, repairs and parts over years · P |
| [ ] Service relationships | Not established · N | Not established · N | Not established · N | Not established · N | Not established · N |

**Caution (research file, Part 5):** relationships between services are not clinical instructions. Do not assume one service is indicated because another is sought.

### 1C. Provider and resource availability

| Item | Status across companies |
|---|---|
| [x] Provider names | Published by practices and listed in reviews (e.g. Dr. Folz at CP&S; Dr. Larson at AdaCare). These are not verified against each provider's page. Do not use names for the demo without confirmation. **P / N** |
| [ ] Provider–location map | Not established for any company · N |
| [ ] Matching to providers, preferred-provider choice | Not established · N |
| [x] Appointment availability visible? | None of the five showed live slots on the pages checked. **V** (no slots shown) |
| [~] Referrals / prior auth | CP&S: referral and prior authorisation (days to weeks) · P. Numotion: funding approval 2–8 weeks · V. Others: not established · N |
| [~] Stated wait or response time | Numotion: about 1 week (evaluation) · V, 2–4 weeks (docs) · P (step 2 wording not re-checked), 2–8 weeks (funding) · V, 2–8 weeks (build) and about 1 week (delivery) · V. CP&S: "arrive 30 minutes early" · P. Others: not established · N |

### 1D. Financial and insurance

| Item | Status |
|---|---|
| [x] Insurance: explicit list | **Metro Vein:** 200+ plans, including Medicare and Medicaid · V. **Others:** no plan list found in the pages checked · N |
| [ ] Self-pay or cash-pay option | Not established for any company · N |
| [ ] Published fees or payment plans | Not established · N. AON has a "Make a Payment" link · V. Metro Vein offers a free evaluation · V. |
| [~] Verification requirement | Metro Vein: staff handle insurance submission · V. Numotion: insurance benefits verified during evaluation · V. AdaCare: patient contacts office before visit · P. CP&S: slow insurance follow-up reported by patients (review sentiment) · reviews |
| [ ] Financial assistance or billing support | Not established · N |
| [x] Financial information the product would need but can't get from the web | Plan IDs and member numbers; coverage for each service; expected patient cost; deductible status; referral or auth status; payment method preference. Needs company confirmation. **C** |

**Deliverable status:** a structured profile per company is in `docs/analysis/company-research/`. The rows above are the checklist view of that profile, plus today's live checks. Confidence per company is in §6.

---

## Part 2 — Positioning and patient expectations

- [~] Company claims, by company (from the 2026-10-14 profiles; **homepage claims were not re-read today**):
  - **CP&S:** interventional, non-surgical pain care; "compassionate" in reviews. Patients expect a calm, thorough start.
  - **ADC/AdaCare:** "doctor-led ownership"; gentle care for anxious patients (review evidence). Patients expect continuity with a known dentist.
  - **Metro Vein:** free evaluation, 200+ plans, "treat people, not symptoms" (V). Patients expect a no-cost first step and clear coverage.
  - **AON:** "integrated care and technology platform" (AEA description). Patients expect coordinated care; the public page shows paperwork, not coordination.
  - **Numotion:** complex rehabilitation technology for permanent disabilities. Patients expect a clear, managed path to funding and delivery.
- [ ] **Still to do:** read each company's homepage and About page claims verbatim and record the URL and date. The research file requires this for "Distinguish explicit claims from your interpretation."
- [x] **Key question answered in part:** the public experience teaches patients to expect *a free or simple first step* (Metro Vein, AdaCare). The visible onboarding process does not always match. Metro Vein's coverage step and CP&S's referral step are less simple.

---

## Part 3 — Current onboarding journey (per company, public view)

| Stage | CP&S | ADC/AdaCare | Metro Vein | AON/FOH | Numotion |
|---|---|---|---|---|---|
| 1. Can they treat my condition? | Services page · P | Services page · P | Vein treatments page · V | Practice page · V | Product and service pages · P |
| 2. Find the right provider | Location and provider pages · P | Partner-practice directory · P | Location pages · V | Location list · V | Local branch search · P |
| 3. Request care | Phone, email, online form (third-party domain), referral by fax · P | Phone or "Book Now" widget · P | "Book Your Free Evaluation" form or phone · V | Refer A Patient; phone at each office · V | Phone or order process · P |
| 4. Information requested | *(Corrected: the SSN list is the referring provider's referral packet, not patient-entered fields — see S-11, S-75)* Referral packet: demographics incl. SSN, insurance cards, notes, imaging · V | Photo ID, insurance details · P | Name, email, phone, postcode, insurance (chatbot) · V (privacy policy) | New Patient Forms, privacy notice, records release (PDF) · V | Insurance; physician documentation · V |
| 5. Channels | Phone, email, fax, third-party form, athenahealth portal · P | Phone, booking widget · P | Form, phone, chatbot · V | Phone, PDF forms · V | Phone; order steps · V |
| 6. Response time stated | *(Corrected: 30 minutes is an arrival instruction, not a response time.)* Scheduling aim within 10 days / ten business days / two weeks after referral (S-12, S-68, S-70) | "Bring forms ahead" · P | Not stated · N | Not stated · N | Step times · V |
| 7. Confirmation and prep | Photo ID must not be expired; bring ID · V | Forms ahead or 10 minutes early · P | Not stated · N | Not stated · N | Step timelines · V |
| 8. What happens next | Staff coordinate referral with PCP · P | Not stated · N | Staff follow up; CRM hand-off · V | Not stated · N | Funding then delivery · V |
| 9. Ask a question | Scheduling line (multiple numbers) · P | Phone · P | Phone · V | Phone per office · V | Phone · P |
| 10. Follow-up care | Not stated · N | Not stated · N | Not stated · N | Not stated · N | Repairs and parts · P |

**Verification note:** stage 4 and stage 7 for CP&S and Metro Vein were checked live today. Other rows are from the profiles. No forms or appointments were submitted.

---

## Part 4 — Eight friction categories

| Category | Public offer | Observed friction (evidence) | Product lever | Measurable indicator |
|---|---|---|---|---|
| Urgency and responsiveness | Phone/form; no stated response time at most | Unreturned calls and long holds are the most common CP&S complaint at both locations read; a referred new patient waited two weeks with no callback; FOH new-patient voicemails unanswered for two weeks; Numotion calls routed to an offshore call centre (Google reviews, 2026-10-15) | Acknowledgement, status page, realistic callback window (**C**) | Time to first human response |
| Qualified provider access | Provider pages; referral rules | CP&S: referral needed; patients unsure which doctor (**I**) | Route to the right location or service after eligibility check | Share of requests routed without a restart |
| Intake speed and simplicity | Paper and PDF forms; chatbot at Metro Vein; AI phone/scheduling assistant at CP&S | CP&S: the same forms requested 4–5 times; pre-check-in data not visible at the desk; the AI assistant re-sends the same link. FOH: "System to collect info was hard to fill out. Bad software" (Google reviews, 2026-10-15) | Pre-visit form completion and document checklist | Share of visits starting with complete paperwork |
| Journey transparency | Step timelines at Numotion only | Numotion: repairs and parts taking months, no proactive updates; CP&S: next injection date never made clear; prior-auth status unknown to patients (Google reviews, 2026-10-15) | Visible step map with stated and typical times | Days from request to first visit |
| Communication and visibility | Phone, email, form | Metro Vein: appointment times changed without notice, day-before cancellations, missing confirmations and address/instructions; CP&S: an AI-booked appointment missing from the system (Google reviews, 2026-10-15) | Status updates and change alerts | Calls per completed request |
| Financial certainty | Metro Vein's 200+ plans; Numotion's verification step | Insurance follow-up delays (CP&S, Metro Vein, Numotion reviews) | Coverage status and cost-of-visit explanation (no promise) | Coverage-verified before visit (%) |
| Trust and psychological safety | Staff reassurance (reviews); privacy notice (Metro Vein) | Anxious patients (AdaCare); sensitive diagnoses (oncology, pain) | Calm copy, clear data use, opt-outs, human route | Abandonment at SSN or sensitive-data steps |
| Confidence in being understood | Reviews say clinicians listen | CP&S: questions "answered twice online" asked again in the room; Metro Vein: interpreter request refused despite an advertised language promise (Google reviews, 2026-10-15) | Shared intake summary for staff (no clinical judgement) | Repeat questions per visit |

**Avoid duplication:** urgency and communication overlap at Numotion, and CP&S and Numotion share the call-back problem. They are grouped above under one lever each.

---

## Part 5 — Additional care opportunities (for clinician review only)

These are hypotheses for a clinician to assess. They are not recommendations, and none should be presented as upselling.

| Company | Primary service | Information that may help a clinician | Patient-friendly question (draft) | Clinician assesses | Other service that may be relevant |
|---|---|---|---|---|---|
| CP&S | Pain procedure | Prior imaging, prior treatments, medication list | "Have you had any scans or treatments for this pain before?" | Whether prior care changes next steps | Physical therapy or second opinion (**C**, not confirmed) |
| ADC | Dental restoration or extraction | Dental anxiety, prior dental work, medical conditions relevant to dental care | "Is there anything that makes dental visits harder for you?" | Comfort plan and medical risk | Preventive hygiene (**C**) |
| Metro Vein | Vein evaluation | Prior vein treatment, family history, leg symptoms | "Have you had any vein treatment before?" | Medical necessity (cosmetic vs medical) | Compression or follow-up (**C**) |
| AON/FOH | Oncology consult | Outside records, prior treatment, support needs | "Do you have records from other doctors or hospitals we should request?" | Clinical priority and records need | Supportive care referral (**C**) |
| Numotion | Equipment evaluation | Current equipment, repair history, caregiver support | "Is there equipment you already have that needs repair or replacement?" | Clinical need and equipment fit | Repair service or ATP follow-up (**C**) |

**Rule:** the product collects and organises information. Clinicians decide. No recommendation without independent clinical assessment.

---

## Part 6 — Software configuration specification

### 6A. Company configuration (per company)

| Item | CP&S | ADC/AdaCare | Metro Vein | AON/FOH | Numotion |
|---|---|---|---|---|---|
| Name and brand | Commonwealth Pain & Spine | American Dental Companies (partner practice: AdaCare) | Metro Vein Centers | Florida Oncology & Hematology (AON) | Numotion |
| Tone | Calm, clinical, reassuring | Warm, personal | Friendly, direct | Supportive, precise | Practical, step-by-step |
| Locations and hours | 20 cities / 3 states (list) · P; hours not checked | 76 practices (partner list) · P; hours not checked | 17 NY clinics · V; hours not checked | 5 FL offices · V; hours not checked | Nashville HQ · P; hours not checked |
| Services | From §1B | From §1B | From §1B | From §1B | From §1B |
| Insurance | Not established · C | Not established · C | 200+ plans, Medicare/Medicaid · V | Not established · C | Not established · C |
| Patient resources | Registration, FAQ, bill-pay · V/P | Partner-practice pages · P | Insurance check, privacy policy · V | New patient forms, records release · V | Order process · V |
| Contact channels | Phone, email, fax, third-party form, athenahealth | Phone, booking widget (jarvisanalytics) | Form, phone, chatbot (HubSpot) | Phone per office, Refer A Patient | Phone; order steps |

### 6B. Patient intake configuration (common core, company-specific values)

| Field | Required at first contact? | CP&S | ADC | Metro Vein | AON | Numotion |
|---|---|---|---|---|---|---|
| Name, DOB, contact | Yes | Yes (OCR target) | Yes | Yes (chatbot) | Yes | Yes |
| Reason for care | Yes | Pain | Dental need | Vein concern | Cancer or blood condition | Mobility need |
| Desired outcome | Optional | Yes | Optional | Optional | Optional | Yes |
| Service selection | Yes | Pain procedure | Dental service | Evaluation | Consult | Evaluation |
| Location or provider preference | Optional | Yes | Yes | Yes | Yes | Yes |
| Insurance (plan, ID) | At booking | Yes | Yes (details) | Yes | Yes (to verify) | Yes |
| Referral | Conditional | Yes (most plans) | No | No | Possibly (**C**) | Physician documentation |
| Prior treatment and records | Conditional | Yes | Conditional | Conditional | Yes (records release) | Equipment history |
| Photo ID | Pre-visit | Yes | Yes | Not established · N | Not established · N | Not established · N |
| Accessibility or communication needs | Optional | Yes | Optional | Optional | Yes | Yes |

**Separation of contact and pre-visit data:** initial contact asks for name, contact, reason and insurance. Pre-visit collects forms, ID, records and consents. Insurance is collected once and reused. SSN is requested by CP&S: **treat it as high-sensitivity and collect only at the step where it is needed, after confirming the company's policy (C).**

**Conditional logic:** referral question only when the plan requires it; records release only for oncology; equipment history only for Numotion.

### 6C. Workflow configuration

| Step | Core product (reusable) | Company-specific | Status |
|---|---|---|---|
| Initial request | Yes | Channel and routing rules | [ ] Confirm channels per company |
| Acknowledgement | Yes | Wording and timing | [ ] Company confirms timing |
| Clinician-approved urgency screening | Reusable hook, human-approved | Who approves; triggers | [ ] Company confirms policy (**C**) |
| Routing to service or provider | Yes | Service map | [ ] Needs provider map |
| Scheduling request | Yes | Booking system and rules | [ ] Confirm booking system (AdaCare widget, CP&S third-party form) |
| Pre-visit intake | Yes | Forms and ID rules | [~] Forms known for CP&S, AON, AdaCare |
| Document collection | Yes | Records, referral, ID | [~] Known for CP&S and AON |
| Preparation instructions | Yes | Per service | [~] CP&S 30-minute early arrival; ID rule |
| Status updates | Yes | Stages and wording | [ ] Needs company step map |
| Staff handoff | Yes | Queues and owners | [ ] Confirm staff roles (**C**) |
| Clinician review of additional needs | Yes | Clinician-owned | [ ] Confirm process (**C**) |
| Follow-up | Yes | Schedule | [ ] Not established · N |

### 6D. Communication configuration (examples, not promises)

| Message | Example wording (placeholder until confirmed) |
|---|---|
| Request received | "Thanks, we have your request. A team member will be in touch. [Confirm response time with company.]" |
| Missing information | "We need your insurance card and photo ID before your visit. You can upload them here." |
| Appointment confirmation | "Your appointment is [date/time] at [location]. [Confirm booking rules.]" |
| Preparation | "Please arrive 30 minutes early for paperwork. Bring a valid photo ID that is not expired." (CP&S wording, **V**) |
| Scheduling delay | "Your insurance check is still in progress. We will tell you when it is complete." (no date promised) |
| Status update | "Your referral has been received and is being reviewed." |
| Follow-up reminder | "Your forms are not complete yet. Finish them before [date]." |

Rule: never promise an appointment, response time, service or outcome that the company has not confirmed.

### 6E. Integrations (to confirm, not assume)

| Company | Visible system | Status |
|---|---|---|
| CP&S | athenahealth patient portal and bill-pay · P; third-party request form (`prettygoodai.net` domain) · P | Integration not established · C |
| ADC | Booking widget (`schedule.jarvisanalytics.com`) · P | Not established · C |
| Metro Vein | HubSpot CRM for chatbot data · V (privacy policy) | Not established · C |
| AON/FOH | Not visible on the page checked · V | Not established · C |
| Numotion | Not established · N | C |

---

## Part 7 — Gap and business impact

| # | Gap (current → proposed) | Evidence | Confidence | Measure |
|---|---|---|---|---|
| G1 | Phone-dependent request and status → digital request with acknowledgement and status | Google reviews: unreturned calls at CP&S (both locations), FOH and Numotion | Review evidence (partial sample); impact inferred (I) | Calls per request; time to first response |
| G2 | Missing or stale paperwork at visit → pre-visit checklist | AON reviews; CP&S ID and referral packet | Verified forms (V); impact inferred (I) | Visits with complete paperwork |
| G3 | Insurance follow-up stalls → coverage status view | Reviews at CP&S, Metro Vein, Numotion | Inferred (I) | Days in insurance step |
| G4 | Unclear multi-step timelines → step map with typical times | Numotion step timeline (V) and long-wait reviews | Verified timeline (V); improvement inferred (I) | Days from request to first visit |
| G5 | Chatbot exists at Metro Vein → post-chat handoff quality | Privacy policy (V); pre-auth complaints (reviews) | Inferred (I). **Existing tool is not a failure.** | Follow-up calls after chat |
| G6 | Records and release gaps (oncology) → records checklist | Records release form (V); FOH reviews: an outside referral with records went unanswered, and a transferred patient's results were not followed up | Inferred (I) | Visits delayed by missing records |
| G7 | CP&S's existing AI phone/scheduling assistant → seams between systems | Seven low reviews (2 locations, last ~year): a booking missing from the schedule, no human handoff, the same link sent 4 times | Review evidence; vendor and integration unknown (RQ-28). **Existing tool is not a failure; frame as closing seams.** | Bookings confirmed in system of record; handoff time to a human |
| G8 | Collected-once data not reused → single intake record visible to staff | CP&S forms repeated 4–5 times; pre-check-in data not visible at the desk; FOH "bad software" | Review evidence (I) | Repeat questions per visit; check-in time |
| G9 | Appointment changes not communicated (Metro Vein) → change alerts with reason and rebook | Forest Hills reviews: times shifted after confirmation, day-before cancellations, missing confirmations | Review evidence (I) | Arrivals at wrong time; same-day reschedules |

**Business hypotheses (not claims):** conversion from request to visit; fewer no-shows from missing paperwork; lower staff time per intake. **Every ROI figure needs company baseline data (see Part 8).**

---

## Part 8 — Revenue and ROI

- [ ] Baseline data needed from each company: request volume, request-to-visit conversion, abandonment at each step, no-show and cancellation rates, staff minutes per intake, average time to first visit. **N for all five.**
- [x] Mechanisms identified (no numbers): conversion, abandonment, cancellations, time to care, admin labour, incomplete visits, follow-up, service recommendations via clinician review, satisfaction and referrals.
- [ ] Illustrative calculations: none yet. Any calculation must state assumptions and must not be presented as a company result.

---

## Part 9 — Demo blueprint (simulated)

- [ ] Three fictional patients per company (or one company as anchor). **Not started.** Recommended: CP&S only, as the anchor, to keep the first demo focused.
- Planned scenarios (anchor, all **SIMULATED**):
  1. **Straightforward:** a patient with a referral, an insurance card and a valid ID, who completes forms online.
  2. **Personalised:** a patient with anxiety about procedures and an expired ID, needing a staff call.
  3. **Clinician review:** a patient whose intake shows prior treatments and imaging, flagged for clinician review (no clinical judgement by software).
- [ ] Staff view and before/after comparison: not drafted.

---

## Part 10 — Unknowns and discovery questions

**Essential (before any production build):**
- [ ] Who handles intake and insurance per company, and how many staff? (C)
- [ ] Intake volumes, abandonment and no-show rates. (C)
- [ ] Referral and eligibility rules (CP&S, AON). (C)
- [ ] Clinical escalation and review policy: who sees additional needs, and how. (C)
- [ ] Systems: athenahealth, booking widget, HubSpot, third-party forms; integration access. (C)
- [ ] Insurance verification steps and who owns them. (C)
- [ ] Consent and privacy requirements, including SSN handling. (C)
- [ ] Patient communication policy (SMS, email, consent to message). (C)

**Optional:**
- [ ] Appointment completion and follow-up process.
- [ ] Brand voice guidance and approved copy.

**Placeholders for demo only (label as placeholders):** response times, booking windows, staff roles, and the hours shown in §6A.

---

## Report sections (12-part format) — status

| # | Section | Status |
|---|---|---|
| 1 | Executive summary | [ ] Not written. Key points are in the companion review file and §2–§4 above. |
| 2 | Company intelligence profile | [x] In `company-research/` (2026-10-14) · [~] Re-checked today for 5 key claims |
| 3 | Service catalogue and pathways | [x] §1B |
| 4 | Positioning and promises | [~] Profile-level. Homepage claims not re-read. |
| 5 | Current onboarding journey | [x] Part 3 |
| 6 | Patient friction assessment | [x] Part 4 with review evidence |
| 7 | Additional care opportunity matrix | [x] Part 5 (clinician-only framing) |
| 8 | Software configuration specification | [x] Part 6 (with confirmation flags) |
| 9 | Gap and business impact matrix | [x] Part 7 · [ ] Part 8 needs baselines |
| 10 | Fictional patient demo blueprint | [~] Outline only |
| 11 | Unknowns and discovery questions | [x] Part 10 |
| 12 | Prioritised product recommendations | [ ] Not written. Candidate list: pre-visit checklist; status page; coverage status view; step map; clinician-review summary. |

---

## What I Need to Configure This Company in My Onboarding Software

### 1. Verified and ready to use

- Company names, locations and specialties for all five platforms, from live pages or the 2026-10-14 profiles.
- **CP&S:** photo-ID rule; referral contents (demographics, insurance card, notes, imaging); fax-based referral; 30-minute early arrival; new-patient forms and records.
- **Metro Vein:** free evaluation; 200+ plans including Medicare and Medicaid; 17 NY clinics; chatbot data handling and HubSpot CRM (privacy policy).
- **AON / FOH:** five offices in four Florida cities; new-patient forms; medical records release; "Refer A Patient"; make-a-payment link.
- **Numotion:** four-step order process; stated step timelines (evaluation about 1 week; medical documentation about **2–4** weeks; funding about 2–8 weeks; delivery process about 2–8 weeks, with delivery ~1 week). *(Corrected 2026-10-15: this line previously said 2–8 weeks for documentation.)*
- **ADC:** partner-practice list; AdaCare's photo-ID and insurance-details requirement (profile).

### 2. Can be simulated for the demo (label as simulated)

- All patient identities, histories, answers and appointments.
- Staff queues, statuses and handoffs.
- Response times and booking windows (as placeholders).
- Review-based talking points, presented as public sentiment and not as company facts.

### 3. Requires company confirmation

- Response and callback times; who handles intake; insurance verification ownership.
- Booking rules, appointment types, provider–location map, provider matching.
- Referral and eligibility rules; clinical escalation policy.
- Integrations: athenahealth, booking widget, HubSpot, third-party forms.
- Volumes, abandonment, no-shows, staff time: all baselines.
- Consent, privacy, SSN handling, and patient communication policy.
- Homepage claims, verbatim, for Part 2 (can be checked independently; no company contact needed).

### 4. Reusable product capabilities vs company-specific configuration

| Reusable core (build once) | Company-specific configuration |
|---|---|
| Guided chat intake and conditional questions | Question set, wording and tone |
| Document checklist, upload and confirmation (OCR with user confirmation) | Which documents, and the ID rules |
| Coverage status view (no approval promised) | Which plans and verification steps |
| Status page and reminders | Stage names, timelines, message copy |
| Staff summary and handoff queue | Staff roles and routing |
| Clinician review flag (human decides) | Which clinicians, what they review |
| Scheduling hand-off to existing booking tool | Booking system and rules |
| Audit log and consent capture | Consent text and retention policy |
| Accessibility and language support | Brand and language |

---

## Gaps in this pass (be explicit)

1. **Google reviews were read from the review dialogs** (Lowest and Newest sorts; one or two locations per platform; every low review captured at four locations, a partial low tail at Commonwealth's two). See the companion file's §4 for what the evidence does not show.
2. **Several profile facts were not re-checked today:** the ADC practice count, Metro Vein's "9 states" figure, the CP&S "20 cities" figure, CP&S's 30-minute instruction, and the Numotion step 2 wording. Each is marked `[P]`.
3. **Homepage and About claims** were not re-read (Part 2 is incomplete).
4. **Part 8 and Part 9** are not filled. They need company data or a deliberate demo design decision.
5. **Fees, insurance lists (except Metro Vein) and hours** were not found on the pages checked.
6. The dev-log entry required by the project CLAUDE.md has not been written yet.
