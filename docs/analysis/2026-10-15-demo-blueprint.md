# Annex 2 — Fictional Patient Demo Blueprint (Research Report §10)

**Date:** 2026-10-15 · Parent: [research report](2026-10-15-onboarding-research-report.md) §10.
**Every person, answer, document, date and appointment in this file is SIMULATED.** Names use the pattern `SIM-<platform>-<n>` with an obviously synthetic name. They resemble no real person, and no real ID layout is reproduced (RQ-17). Company process facts are **Verified** with `S-N`. Our product's behaviour is **Proposed**.

> **Reconciliation notes (2026-10-15).**
> - **Scenarios are illustrations, not selected scope.** Which capabilities a demo shows beyond the brief's mandatory flows depends on Innocent's choice in the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md).
> - **⚑ RQ-44:** scenarios marked with this flag collect optional clinical-adjacent context (other conditions, prior treatment, sleep, dental anxiety, pregnancy, nutrition). The [configuration annex](2026-10-15-configuration-specification.md) excludes medical history. Until RQ-44 is decided, these scenarios are not demo-ready.
> - **"Today" in each before/after means what the company publishes or a reviewer reports**, not an observed internal workflow. "With the product" is simulated. A simulated comparison cannot measure company performance or revenue.

Each scenario covers:
- **A.** Profile.
- **B.** Patient-facing flow: the questions in order.
- **C.** Conditional non-clinical steps.
- **D.** How uncertainty is reduced.
- **E.** Staff summary.
- **F.** Items flagged for clinician review: patient-reported and unscored.
- **G.** Before and after, with the capabilities that make the difference.

---

## 1. Commonwealth Pain & Spine

### SIM-CPS-1 "Avery Testcase": a common referred patient
- **A.** Adult, has a PCP, commercial insurance, chronic low-back pain. Prefers the Louisville South office.
- **B.**
  1. Have you been seen here before? → No.
  2. Name, phone, email, DOB.
  3. Preferred office → Louisville South (hours shown: Mon–Fri 7:45–5:00, S-70).
  4. Referring provider → search by ZIP and name (mirrors S-75).
  5. Address and gender.
  6. Insurance carrier and member ID → "Photograph your card instead?" → OCR → **confirm each field**.
  7. Reason for referral, in the patient's words.
  8. MVA? No. Work injury? No.
  9. Contact preference → SMS (consent shown).
- **C.** Insured and not MVA or work injury → status label *Contacting your doctor for a referral* (our label for the company step "We'll Connect With Your Physician", S-70). The product does not judge whether this plan needs one (RQ-39).
- **D.** The status page shows the company's 3 steps (S-70), the company aim "within ten business days of referral or initial contact" (S-68) labelled as the company's aim, and a "What to bring" list (S-12).
- **E.** Staff summary: new patient; Louisville South; referring provider (synthetic); card confirmed (2 fields edited after OCR); referral not yet received; preferred contact SMS mornings; no missing items except the referral.
- **F.** None entered.
- **G.**

| Today (Verified) | With the product (Simulated) | Capability |
|---|---|---|
| Form submitted; follow-up timing not stated (S-75) | Instant acknowledgement plus status page | Readiness tracker |
| Card and ID brought in person (S-12) | Card captured and confirmed before the visit | OCR with confirmation |
| Staff contact the PCP (S-70) | The same, but the patient sees it happening | Status messaging |

### SIM-CPS-2 "Blake Placeholder": obstacles
- **A.** Work injury, no PCP referral, worried about cost, prefers Spanish (synthetic preference).
- **B.** As SIM-CPS-1 until question 8: Work injury? **Yes** → Employer (synthetic) → Claim number (optional).
- **C.**
  - Work injury → notice: "Treatment for worker’s compensation needs authorization before scheduling.Call (502) 919-9781 to speak with our Occupational Medicine Specialist directly." (company text, S-12)
  - Cost worry → the insurance FAQ excerpt on cost estimates and payment plans (S-12).
  - Language → the summary shows "Prefers Spanish". Whether Spanish service exists at CPS is **not publicly established**.
- **D.** Status: "Waiting for workers' comp authorisation". The product gives no date. The $50 late-cancellation policy is shown before booking (S-12).
- **E.** Summary: work-injury route; authorisation pending; language preference; cost concern noted; **handoff to Occupational Medicine queue (simulated owner)**.
- **F.** None.
- **G.** Today the patient learns about the authorisation requirement only from the FAQ, if they read it (S-12). With the product, conditional logic shows it at the right moment, and the patient reaches a named human route.

### SIM-CPS-3 "Casey Mockdata": other needs for professional review ⚑ RQ-44
- **A.** A referred patient who chooses to answer optional questions.
- **B.** As SIM-CPS-1, plus optional questions:
  - "Are you being treated for any other long-term health conditions?" → "Diabetes, high blood pressure" (synthetic).
  - "Is pain affecting your sleep, mood or daily activities?" → "Sleep, mostly".
  - "Have you tried physical therapy?" → "Yes, 2024".
- **C.** No branch. The answers are stored as "patient-reported, not assessed".
- **D.** The patient sees: "Your answers go to your care team to review. They don't change your appointment."
- **E.** Summary includes a "Patient-reported context" box with the three answers verbatim.
- **F.** Flagged for clinician review only:
  - other chronic conditions → the clinician decides whether Chronic Care Management fits (S-66);
  - sleep impact → the clinician decides on Behavioral Health Integration (S-66);
  - prior PT → history only.
- **G.** Today, conditions and goals are first discussed at the visit (S-12 first-visit FAQ). With the product, the clinician arrives prepared. **No service is suggested to the patient.**

---

## 2. American Dental Companies (AdaCare, Meridian ID)

### SIM-ADA-1 "Drew Fictional": a common new adult patient
- **A.** Adult, one dental insurance, wants a check-up.
- **B.** Name, contact, DOB → reason → preferred times (office hours shown, S-81) → insurance card photo plus OCR plus confirmation → e-communications consent choice (text, email or voice, S-82).
- **C.** None.
- **D.** Pre-visit messages (our wording, based on S-16):
  - the "$89 New Patient Exam and X-rays" offer;
  - cleaning is usually a separate visit;
  - arrive 10 minutes early if the forms aren't complete.
- **E.** Summary: new adult patient; insurance captured for the benefits check; e-communications consent recorded.
- **F.** None.
- **G.** Today (published): book by phone or through the group scheduler, which shows New Patient Visit slots before personal details (S-83, re-read 2026-10-15); print the paper packet or arrive early; call the office with insurance (S-16, S-82). With the product (simulated): the same booking step, then a digital packet and insurance captured in advance (OCR, packet, consent capture). The scheduling step is not presented as an improvement.

### SIM-ADA-2 "Emery Synthetic": obstacles ⚑ RQ-44 (comfort question only)
- **A.** Anxious patient who wears dentures and has two dental insurances.
- **B.** As SIM-ADA-1, plus a secondary insurance card (OCR and confirm) and an optional question: "Is there anything that makes dental visits hard for you?" → "Very nervous".
- **C.** Two insurances → a policyholder-details step for each (mirrors S-82). The comfort answer is stored as patient-reported.
- **D.** Message: "Your dentist will talk through options with you at your visit." The product names no sedation option to the patient.
- **E.** Summary: two insurances captured; patient-reported anxiety; denture wearer.
- **F.** Comfort note → the dentist decides whether to discuss sedation (S-81).
- **G.** Today, a nervous patient fills in paper forms in the waiting room. With the product, it's done at home, and the dentist sees the comfort note first.

### SIM-ADA-3 "Finley Example": other needs plus a family member ⚑ RQ-44 (recall-gap question)
- **A.** Adult overdue for a cleaning, also asking about their 5-year-old.
- **B.** Last cleaning? → "Over 3 years". "Is anyone else in your family coming?" → child, age 5.
- **C.** Child has baby teeth → notice: "We work on grown-up teeth only … we will help you find a pediatric provider" (S-16). The guardian flow is not built in the demo (RQ-16).
- **D.** The patient learns the child's route now, not at the desk.
- **E.** Summary: recall gap (patient-reported); pediatric referral requested.
- **F.** Recall gap → the dentist decides on hygiene needs at the exam.
- **G.** Today the pediatric rule sits on the new-patient page (S-16). With the product, conditional logic shows it at the moment it applies.

---

## 3. Metro Vein Centers

### SIM-MVC-1 "Gray Sampleton": a common Medicare patient
- **A.** Adult with leg aching, Medicare, near Forest Hills.
- **B.** First name, last name, email, phone (S-88) → **optional** Medicare card photo plus OCR plus confirmation → clinic (Forest Hills hours shown, S-90).
- **C.** Insurance supplied → status *Checking your coverage*, with the company estimate "about 24–48 hours" (S-87) labelled as an estimate.
- **D.** Messages: the free evaluation is "subject to insurance eligibility" (S-88); our wording explains that the first visit is quoted before arrival when insurance is provided (based on S-87).
- **E.** Summary: request plus insurance captured, ready for verification.
- **F.** None.
- **G.** Today: four-field form → call → insurance by phone (inferred from S-87). With the product: insurance optionally captured at request, saving a call (G5).

### SIM-MVC-2 "Harper Notreal": obstacles
- **A.** Prefers Spanish; works shifts; the appointment time later changes (synthetic event).
- **B.** Language → Spanish (the site has a Spanish version, S-85). Preferred times → early mornings.
- **C.** A staff-side time change (simulated) → automatic change notice with the reason and a "Reply to reschedule" option (mirrors S-86), plus directions and preparation (approved content).
- **D.** The patient never arrives at an old time.
- **E.** Summary: Spanish; time-change acknowledged by the patient.
- **F.** None.
- **G.** Today: reviews report time changes without notice and missing directions (S-91, Reported). With the product: change notices and confirmation content (G6).

### SIM-MVC-3 "Indigo Mockwell": other needs for professional review ⚑ RQ-44
- **A.** Mostly cosmetic concern; recently pregnant.
- **B.** Optional questions:
  - "Are you currently pregnant?" → No, gave birth 2 months ago (synthetic).
  - "Have you had vein treatment or worn compression stockings before?" → No.
- **C.** The concern is described as cosmetic → price notice "In some cases, if your doctor determines treatments to be purely cosmetic … costs $425 per session" (S-86). Pregnancy answers are stored for staff and the clinician.
- **D.** The patient knows the possible cost before booking.
- **E.** Summary: patient-reported recent pregnancy; cosmetic concern; no prior treatment.
- **F.** Timing considerations → clinician review (the company publishes pregnancy guidance, S-86).
- **G.** Today, cost is learned in the FAQ or at the visit. With the product, the published price is shown at the relevant moment.

---

## 4. American Oncology Network (Florida Oncology & Hematology)

### SIM-FOH-1 "Jules Fakename": a common referred patient
- **A.** Referred by a synthetic PCP; Naples–Goodlette office.
- **B.** "How are you coming to us?" → Referred → referring physician (synthetic) → demographics → contact permissions (voicemail, email) → insurance card OCR plus confirm → emergency contact → SMS/email consent (S-98 wording).
- **C.** Referred → status *A Patient Services Specialist will contact you* (our wording, based on S-96).
- **D.** Messages (our wording, based on S-95 and S-97): what to bring — medication list, prior illnesses, previous surgeries, allergies and insurance card; a financial counsellor will meet you during one of your initial visits.
- **E.** Summary: administrative sections of the packet complete; clinical history to be done with the clinical team.
- **F.** None.
- **G.** Today: a 14-page paper packet (S-98). With the product: administrative sections done in advance; clinical sections untouched.

### SIM-FOH-2 "Kai Testperson": obstacles
- **A.** Transferring from an out-of-state practice; says earlier calls weren't returned (synthetic); worried about cost.
- **B.** "How are you coming to us?" → Transferring → prior practice name and address → records-release request (mirrors S-98 p.8) → cost question.
- **C.**
  - Transfer → records-release step.
  - Cost worry → financial-support content (S-97) and the patient-assistance authorisation shown in full (S-98 p.14), signed only if the patient chooses.
- **D.** Acknowledgement with a reference number; status "Records requested". The emergency notice is always visible: "If you are experiencing a medical emergency, please call 911 right away" (S-96).
- **E.** Summary: transfer; records release signed; cost concern; **priority for human contact flagged by the request type, not by clinical judgement**.
- **F.** None.
- **G.** Today, reviews report unreturned new-patient calls (S-100, Reported). With the product, the request lands in a visible queue with an acknowledgement (G8).

### SIM-FOH-3 "Lane Specimen": other needs for professional review ⚑ RQ-44 (nutrition and trials questions; the practical-barrier question is administrative)
- **A.** Referred patient who uses optional questions.
- **B.** Optional:
  - "Would help with transportation, costs or caregiving make it easier to attend?" → Transportation.
  - "Would you like information about clinical trials?" → Yes.
  - "Do you have concerns about eating or weight?" → Yes.
- **C.** Stored as patient-reported.
- **D.** "Your care team will review these with you."
- **E.** Summary: "Patient-reported context: transport barrier; trial information requested; nutrition concern."
- **F.** Care coordination (barriers), research team (trials) and dietitian (free; S-97, S-94) → each team decides.
- **G.** Today, barriers are identified by care coordination during care (S-97). With the product, they're known before the first visit.

---

## 5. Numotion (front of journey; the equipment workflow is outside this demo)

### SIM-NUM-1 "Morgan Notaperson": a common caregiver-started order
- **A.** A caregiver for an adult user; Medicare plus a secondary insurance; Nashville branch.
- **B.** "Who is completing this?" → family member → user details → branch (Nashville, Mon–Fri 8:30–5:00, S-105) → primary insurance Medicare → **MBI field** (S-102) → secondary insurance card OCR → physician name → "Has the user had a face-to-face visit with their doctor about this chair?" → Not sure.
- **C.** Medicare selected → MBI required. "Not sure" → message: "For Complex power and manual wheelchairs Step 1 will be a Face-to-Face appointment with the Doctor" (S-102).
- **D.** Status shows the company's four steps with estimates (S-23), labelled as estimates. "Provide both primary and secondary insurance information when you start the process to avoid unnecessary delays" (S-102) is shown as satisfied.
- **E.** Summary: both insurances captured; MBI present; face-to-face status unknown; ready to book an evaluation.
- **F.** None.
- **G.** Today, insurance details are gathered across calls (inferred); Numotion itself says missing data causes delays (S-102). With the product, the data is complete at the start (G9).

### SIM-NUM-2 "Nico Imaginary": obstacles
- **A.** Customer without their MBI to hand; anxious about delays.
- **B.** As SIM-NUM-1, but MBI → "I don't have it now".
- **C.** Save and resume; reminder message with the item missing. No order step is blocked by the product (staff decide).
- **D.** "Here's what's still needed: your Medicare number (MBI)."
- **E.** Summary: MBI missing; reminder sent.
- **F.** None.
- **G.** Today, missing insurance details may surface later in documentation (inferred from S-102 tips). With the product, they surface on day one.

### SIM-NUM-3 "Oakley Pretend": other needs for professional review
- **A.** Existing user whose current chair needs repair while a new one is funded.
- **B.** "Do you already use a wheelchair or seating system? How old is it? Does it need repair?" → Yes, 6 years, joystick fault. → Repair details: serial number, make, model, issue (mirrors S-106).
- **C.** Repair need → a separate repair request (S-106).
- **D.** "Your repair request is separate from your new-equipment order."
- **E.** Summary: existing equipment and age; repair request raised.
- **F.** ATP review of equipment history; payer replacement rules (e.g. "Medicare only covers one wheelchair every 5 years, unless your medical condition changes", S-102) are for staff, not the product, to apply.
- **G.** Today, reviews report long repair waits and little proactive updating (S-107, Reported). With the product, the repair is logged at intake with complete details. Status after that belongs to the separate equipment design.

---

## Demo order and talking points (proposal, not selected)
1. **SIM-CPS-1** (the core flow), then **SIM-CPS-2** (conditional logic, human handoff), then **SIM-CPS-3** (clinician-review boundary; only if RQ-44 allows optional patient-reported context).
2. One reuse example: **SIM-ADA-1** (same core, different configuration).
3. Close on the staff view and the metrics the company would measure (report §9).

**Always say aloud:** the patients are synthetic; company processes are as published on 2026-10-15; nothing here measures real performance.
