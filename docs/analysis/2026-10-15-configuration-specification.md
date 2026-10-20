# Annex 1 — Configuration Specification (Research Report §8)

**Date:** 2026-10-15 · Parent: [research report](2026-10-15-onboarding-research-report.md) §8.
**This is research output, not a product design.** It records what each company publishes and what our general onboarding product would be configured to show. Company facts are owned by the [profiles](company-research/); sources are `S-N` in the [register](../source/source-register.md).

**Columns:**
- **Published (Verified):** what the company states, with its source.
- **Proposed config:** what we would configure (*Proposed*).
- **Demo value:** a synthetic placeholder (*Simulated*). Never shown as a company fact.
- **Confidence:** H = published and specific; M = published but partial or one practice; L = inferred.
- **Still needed:** the open question (`RQ-N`) or "none for demo".

**Product-wide rules (core, not configured per company):**
- OCR results are always shown for confirmation or editing before saving.
- SSN is never collected in the demo.
- The product never states urgency, diagnosis, eligibility or coverage decisions.
- Every automated path offers a human route.
- Messages never promise a time the company has not confirmed.

> **Unresolved scope decision — RQ-44 (flagged 2026-10-15, reconciliation pass).** This annex marks medical and dental history, clinical sections and clinical justification as **not collected by the product**. Research report §7 and three fictional scenarios (SIM-CPS-3, SIM-ADA-2/3, SIM-MVC-3, SIM-FOH-3) instead ask optional questions about other conditions, prior treatment, sleep, pregnancy, dental anxiety and nutrition. Rows below that depend on that choice are marked **⚑ RQ-44**. Until Innocent decides, the exclusion in this annex is the conservative default, and the ⚑ rows are not product scope. The [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md) parks clinical patient-reported context as `P-01`.
>
> **Booking and paperwork order varies.** The workflow lines below are each company's published or inferred order. They are not a universal sequence; registration may happen before a visit, on arrival, or both (S-108).

---

## 1. Commonwealth Pain & Spine

### 1.1 Company configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Identity | Commonwealth Pain & Spine; legal entity Commonwealth Pain Associates, PLLC (S-73) | Display name and logo slot | Synthetic logo placeholder | H | Brand assets (permission) |
| Tone | "being heard"; "compassionate" (S-64, S-65) | Calm, plain, non-judgemental | — | M | Approved copy (RQ-10) |
| Locations and hours | 33 offices, per-office hours (S-69, S-70) | Office picker with address, phone and hours | Louisville South Mon–Fri 7:45–5:00 (published) | H | Hours change; refresh rule |
| Services shown | Service and condition lists (S-76) | "What we treat" help panel only; no service selection by the patient | — | H | — |
| Providers | Directory; office pages (S-70, S-71) | Show the providers at the chosen office; optional preference note | — | M | Matching rules (Not publicly established) |
| Contact channels | 502-890-5639 / newpatients@… (S-11); (502) 855-7200 (S-12); referral fax (866) 697-2464 (S-11); athenahealth portal (S-64) | "Call us" button per office; the portal for existing patients | — | H | Which number owns new patients |
| Insurance and payment | Plans by state (S-67); self-pay uninsured only; $50 <24 h cancellation fee; payment plans; fees due at time of service (S-12, S-72) | Plan lookup by state; self-pay and fee notices shown before booking | — | H | Plan list refresh |
| Resources | FAQ; insurance glossary; preparation list (S-12, S-67) | Approved help content library | — | H | Permission to reuse (RQ-10) |

### 1.2 Intake configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Initial contact fields | Request form: name, phone, email, DOB, clinic, seen before, referring provider, address, gender, insurer, member ID, reason, contact method, MVA, work injury (S-75) | Same set, split: contact and reason first, then insurance, then referring provider | Synthetic patient (Annex 2) | H | Which are mandatory before booking (RQ-6) |
| Reason for care | "Reason for Referral" free text (S-75) | Patient's own words; no symptom scoring | — | H | — |
| Desired outcome ⚑ RQ-44 | Not asked on the form | Optional "what would you like to be able to do again?" for staff (clinical-adjacent goal; scope undecided) | — | L | Company approval; RQ-44 |
| Provider or location preference | Preferred clinic (S-75) | Office picker | Nearest office to the synthetic address | H | — |
| Scheduling preferences | Not asked | Optional days and times | "Mornings" | L | Whether staff use it |
| Medical history | Clinical; not on the request form | **Not collected by the product** | — | — | Out of scope |
| Insurance | Insurer and member ID (S-75); bring cards (S-12) | Card photo plus OCR plus confirmation at pre-visit; text fields at request | Synthetic card | H | — |
| Existing treatment and referral | Referring provider search (S-75); referral fax packet (S-11) | Referring provider field; status "Referral requested" | "Referral requested" | H | Referral rule by plan (RQ-39) |
| Accessibility and communication | Contact method phone or email (S-75) | Add SMS consent, language and accessibility needs (optional) | English, SMS | L | Consent text |
| Conditional: work injury | Authorisation before scheduling; occupational medicine line (S-12) | "Yes" → notice plus line (502) 919-9781 | Scenario 2 | H | — |
| Conditional: MVA | Seen once PIP is exhausted (S-12) | "Yes" → PIP notice | — | H | — |
| Conditional: uninsured | Self-pay for uninsured only; call before the appointment (S-12) | "No insurance" → self-pay notice and a call prompt | — | H | Self-pay prices (Not publicly established) |
| Pre-visit items | Photo ID (unexpired; listed types S-11); cards; co-payment; imaging (S-12) | Checklist with ID-type list; OCR for ID name, DOB and address | Synthetic ID | H | — |

### 1.3 Workflow (company-specific step names)
Request received → **Contacting your doctor for a referral** (S-70) → **Checking your insurance** (S-12) → **Ready to schedule** → Appointment confirmed → Pre-visit checklist → Visit.
- **Staff handoff:** new-patient scheduling queue (owner unknown; RQ-4, RQ-27).
- **Escalation:** a company-approved emergency notice only. No triage.
- **Timing display:** the company's pledge, quoted exactly: "Our scheduling staff is devoted to finding appointments for new patients within ten business days of referral or initial contact" (S-68), shown as the company's aim, never as a promise to this patient.

### 1.4 Communication
Examples are in the [report §8.4](2026-10-15-onboarding-research-report.md#84-communication-examples-wording-is-proposed-times-only-if-the-company-confirms-them). Company-specific inserts:
- the arrival instructions (S-12);
- the $50 <24-hour cancellation fee and the 10-minute-late rule (S-12);
- "bring a valid form of photo ID … It must NOT be expired" (S-11).

### 1.5 Integration (visible only)
athenahealth portal and billing; prettygoodai request form; ChartRequest; virtual agent (S-64, S-66, S-75). **Status: requires company confirmation (RQ-18, RQ-25, RQ-28).** The demo stubs the handoff.

### 1.6 Reusable vs company-specific
- **Reusable:** request flow, OCR and confirmation, readiness tracker, help library, staff queue, consent, messaging engine.
- **Company-specific:** the ~20 field set, the MVA and work-injury branches, the self-pay rule, the plans by state, the office list, the 3-step names, the fee and arrival text.

---

## 2. American Dental Companies / AdaCare

### 2.1 Company configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Identity | Platform ADC; practice AdaCare Dental & Dentures (S-78, S-81) | Practice-branded front with group configuration underneath | AdaCare | H (practice) | Which practices to include (RQ-40) |
| Tone | Comfort and education ("white knuckle" patients welcomed, S-84 Reported) | Warm, reassuring | — | M | Approved copy |
| Location and hours | Meridian; Mon 9–5, Tue 9–5, Wed 8–3, Thu 10–6, every other Fri 9–4 (S-81) | Hours panel | As published | H | Other practices vary (RQ-9) |
| Services | Preventive, cosmetic, restorative, perio, endo, surgery, sedation, aligners (S-81) | "What we offer" panel | — | H | — |
| Contact | (208) 996-5808; Book Now widget (S-16, S-81). Widget re-read 2026-10-15 (view only): New/Existing Patient, "Booking for" Myself/Someone Else, six new-patient services, **New Patient Visit slots shown before personal details** (S-83) | Call button; link to or mirror the group scheduler's appointment types; our demo uses synthetic slots | Stub slot list | M (one practice) | Post-slot fields and confirmation; other practices' configuration (RQ-40) |
| Insurance and payment | Most major dental insurances; claims filed as a courtesy; CareCredit, plans, cards; $89 new-patient exam and X-rays (S-16) | Show the $89 offer and financing options; "send your insurance before the visit" step | — | H | Plan list (Not publicly established) |
| Policies | Walk-in, <24 h cancellation and >10 min late fees (amounts not stated) (S-82) | Show the policy text at booking | — | M | Fee amounts |

### 2.2 Intake configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Initial contact | Phone or widget (S-16); widget asks patient type and service before slots (S-83) | Name, contact, DOB, reason, preferred times | Synthetic | M | Fields collected after slot selection (not viewed; RQ-40) |
| Pre-visit packet | Patient info incl. SS# field, two insurances, policyholder, referral source; e-communications consent; HIPAA acknowledgement (S-82) | Digital administrative packet; **no SSN**; dual insurance with card OCR | Two synthetic cards | H (form contents) | SSN need (RQ-15) |
| Medical and dental history | Clinical form (S-82) | **Not collected by the product** (out of scope) | — | — | — |
| Conditional: child | Very young children referred to a pediatric dentist (S-16) | "Patient has baby teeth" → referral notice | Scenario 3 | H | Guardian rules (RQ-16) |
| Conditional: anxious patient ⚑ RQ-44 | Sedation services exist (S-81); the scheduler lists a "Sedation Dentistry Consultation" service (S-83) | Optional comfort question shown to the dentist (Report §7 #5); scope undecided | Scenario 2 | M | RQ-44 |
| Expectation setting | Cleaning usually not the same day as the new-patient exam (S-16) | Pre-visit message | — | H | — |

### 2.3 Workflow, communication, integration
- **Workflow:** at AdaCare the published routes allow booking first: the scheduler offers New Patient Visit slots before details (S-83), while the new-patient page asks patients to send insurance before the visit and complete forms in advance or on arrival (S-16, S-82). Reference order for configuration: Exam booked → Benefits check (patient sends insurance) → Packet complete (before or at arrival) → Visit → Cleaning visit (separate). How the steps interleave in practice is not established (RQ-40).
- **Communication:** reminder and check-in calls are praised (S-84 Reported). Configure SMS or email reminders only with the e-communications consent (S-82).
- **Integration:** Jarvis Analytics scheduler; "Cloud-based centralized dental management software" (S-79, S-83). **Requires confirmation (RQ-40).**
- **Reusable vs company-specific:** the core is the same as CPS. Company-specific items are the dual dental insurance, the pediatric rule, the $89 offer, the fee policy text and the per-practice hours.

---

## 3. Metro Vein Centers

### 3.1 Company configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Identity and tone | "We treat people, not symptoms." (S-85) | Friendly, direct; English and Spanish | — | H | Spanish copy approval |
| Locations and hours | 80 clinics, 9 states (S-89); Forest Hills hours (S-90) | Clinic picker with hours | Forest Hills as published | H | Other clinics' hours |
| Services | Treatment list; free evaluation with ultrasound (S-86, S-88) | Help panel | — | H | — |
| Contact | Book 888-660-3494; patient care 866-715-9121; insurance 866-932-1217 (S-86–S-88) | One button per purpose, labelled | — | H | Which number is the canonical one |
| Insurance and payment | 200+ plans; Medicaid in select states; $425 per cosmetic session; $425–$1,500 self-pay; financing (S-86, S-87) | Plan check prompt; price notice for cosmetic care | — | H | State Medicaid list |

### 3.2 Intake configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Initial contact | First name, last name, email, phone (S-88) | Keep it to four fields; **optional** insurance card capture to enable the pre-visit quote (S-87) | Synthetic | H | Whether the company wants card capture at request |
| Pre-visit | Insurance needed at scheduling for the automatic quote (S-87) | Insurance step before the confirmation message | Synthetic Medicare card | H | — |
| Conditional: pregnancy ⚑ RQ-44 | Treatment not recommended during pregnancy (S-86) | Optional timing question routed to staff (Report §7 #6); clinical-adjacent, scope undecided | Scenario 3 | M | Company approval; RQ-44 |
| Conditional: cosmetic only | Self-pay $425 per session (S-86) | Price notice | Scenario 3 | H | — |
| Language | Spanish site exists (S-85) | Language preference at request | Spanish | M | RQ-41 |

### 3.3 Workflow, communication, integration
- **Workflow (company's six steps, S-87):** verification → automatic quote → evaluation → pre-authorisation → estimate callback → treatment or financing → claims.
- **Communication:** confirmations with address and directions; change notices with reason; "Reply by text to reschedule" (S-86).
- **Integration:** HubSpot for chatbot data and the SMS programme (S-19). **Requires confirmation (RQ-13, RQ-41).**
- **Reusable vs company-specific:** company-specific items are the four-field front door, the six insurance steps, the 24–48 h windows (company-stated), the price notices and the Spanish copy.

---

## 4. American Oncology Network / Florida Oncology & Hematology

### 4.1 Company configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Identity and tone | "Patient First, Always" (S-94); platform AON (S-92) | Supportive, precise; never clinical | — | H | Approved copy |
| Locations | 5 offices with phones, faxes and referral forms (S-96) | Office picker | Naples–Goodlette | H | — |
| Hours | **Not publicly established** (pages checked: S-94–S-97) | Placeholder clearly labelled | "Mon–Fri, hours to be confirmed" | — | RQ-42 |
| Services | Oncology, hematology, imaging, pharmacy, coordination, trials, financial support (S-94, S-97) | Help panel | — | H | — |
| Contact | New patients (239) 217-8011 (S-95); billing (855) 963-2100 (S-97); care coordination (833) 271-9737 (S-97) | Labelled buttons | — | H | — |
| Insurance and payment | Most major plans; financial counsellor; payment plans; assistance programmes (S-95, S-97, S-98) | "A financial counsellor will meet you" message | — | H | Plan list |

### 4.2 Intake configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Entry route | Referral, transfer or phone (S-95) | First question: "How are you coming to us?" (referred / transferring / self) | Referred | H | — |
| Administrative packet | Demographics (language, contact permissions, pharmacy); PCP and referring physician; emergency contact; insurance (incl. policy-holder SS#); records release; disclosure consent; SMS/email consent; financial policy; NPP acknowledgement; patient-assistance authorisation (S-98) | Digital administrative sections only; **no SSN**; consents shown in full | Synthetic | H | Portal completion possible? (RQ-42) |
| Clinical sections | History, medications, review of systems (S-98) | **Not collected by the product** | — | — | Out of scope |
| What to bring | Medication list; prior illnesses; surgeries; allergies; insurance card (S-95) | Pre-visit checklist (display only) | — | H | — |
| Conditional: transfer | Records release (S-98, S-99) | Records-release step with the prior-practice name | Scenario 2 | H | — |

### 4.3 Workflow, communication, integration
- **Workflow:** Referral or transfer received → Patient Services Specialist contact (S-96) → Packet and records → First visit → Financial counsellor (S-97).
- **Escalation:** display FOH's own "If you are experiencing a medical emergency, please call 911 right away" (S-96). There is no product triage.
- **Communication:** SMS/email only with consent (S-98). Never discuss results or clinical matters; point to CareSpace or a phone call (S-96).
- **Integration:** OncoEMR; CareSpace; personapay (S-92, S-96, S-97). **Requires confirmation (RQ-42).**
- **Reusable vs company-specific:** company-specific items are the entry-route branch, the records release, the consents set, the counsellor step and the emergency wording.

---

## 5. Numotion (front of journey only)

### 5.1 Company configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Identity and tone | "Expert guidance & support" (S-101) | Practical, step-by-step; written for caregivers too | — | H | — |
| Branches and hours | 114 branches; Nashville branch Mon–Fri 8:30–5:00 (S-105) | Branch picker | Nashville (LaVergne) | H | Other branches |
| Contact | (800) 500-9150; chat; after-hours hours (S-104) | Labelled channels | — | H | — |
| Insurance and payment | Medicaid and Medicare in all states plus most carriers; CareCredit; payment plans (S-103) | Notices | — | H | — |

### 5.2 Intake configuration
| Item | Published (Verified) | Proposed config | Demo value | Confidence | Still needed |
|---|---|---|---|---|---|
| Who is completing intake | Customers include children and injured workers (S-101) | "Are you the user, a family member or a clinician?" | Caregiver | M | RQ-16, RQ-43 |
| Insurance | Primary and secondary; MBI for standard Medicare (S-102) | Both insurances with card OCR; an MBI field when Medicare is selected | Synthetic | H | — |
| Referral and physician | Referral starts the process; face-to-face doctor visit for complex chairs (S-102) | Physician name; "Face-to-face visit done? yes / no / not sure" | "Not sure" | H | — |
| Existing equipment | Medicare one chair per 5 years (S-102); repair needs (S-106) | Current equipment and age; repair request link | Scenario 3 | H | — |
| Clinical justification | LMN written by a clinician (S-102) | **Not collected by the product** | — | — | Out of scope |

### 5.3 Workflow, communication, integration
- **Workflow (company steps, S-23):** Evaluation (~1 wk) → Medical documentation (~2–4 wk) → Funding approval (~2–8 wk) → Delivery process (~2–8 wk). The intake product ends at "evaluation booked". Later steps belong to the separate equipment-status design.
- **Communication:** status explanations quote the company estimates, labelled as estimates.
- **Integration:** myNumotion app and portal (S-106). **Requires confirmation (RQ-43).**
- **Reusable vs company-specific:** company-specific items are the who-is-completing branch, the MBI and dual-insurance rules, the equipment questions and the step names. The equipment workflow is outside this configuration.
