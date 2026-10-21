# American Dental Companies — Second Configuration

**Role in this project:** the second configuration. It tests whether the same administrative-intake
core can be reused across one platform's network of practices.
**Relevant users:** patients of affiliated dental practices. ADC's own site mostly addresses
dentists considering partnership; that recruiting funnel is a different workflow and out of scope.
**Practice example:** AdaCare Dental & Dentures, Meridian ID. Its facts are labelled **practice**
below and are not generalised to the group (source-authority rule 4).
**Sources read:** 2026-10-14 (S-13…S-16); re-read and extended **2026-10-15** (S-14, S-15, S-16,
S-78…S-83); booking widget S-83 rechecked later on 2026-10-15 (view only). See the [source register](../../source/source-register.md).

| AEA listing ([profile](https://www.aeainvestors.com/portfolio/american-dental-companies/)) | |
|---|---|
| Status / group | Current · Elevate |
| Investment | 2024 |
| Location | Phoenix, Arizona |
| AEA's description | "A tech-enabled dental partnership organization focused on general dentistry." |
| Company site | ameridentco.com |

---

## 1. Verified public facts

### 1.1 Platform level (ameridentco.com)
- **Network:** 76 practice-profile links and 74 city/state entries across 15 states on 2026-10-15
  (S-14). By state: AZ 26, CA 16, WA 6, WY 4, ID 3, PA 3, CO 2, AK 2, NM 2, GA 2, UT 2, FL 2, MD 2,
  MN 1, TX 1. These are machine counts; the two methods differ by 2.
- **Positioning** (S-78): "Patient Care, Team Care, Business Care"; "private practice culture";
  practices "owned and lead by doctors".
- **Central services ADC says it provides to practices** (S-79):
  - insurance verification, accounts-receivable processing, claim appeals and credentialing;
  - "Scheduling services", "Continued Care recall systems", "Continued Care and Treatment tracking
    and scheduling" and "Full Oversight of Patient Communications";
  - "Cloud-based centralized dental management software", integrated cloud X-ray imaging and
    "advanced practice analytics".
- **A claim made to dentists, not patients** (S-80): "a minimum increase of 30% in revenue in the
  first year of partnership for each partner practice." This is ADC's marketing to prospective
  partners, not a verified result.
- **Booking widget:** a group-level scheduler URL,
  `schedule.jarvisanalytics.com/frame/american-dental-companies?location_id=…` (S-16, S-83).
  *Historical limitation:* in the first 2026-10-15 completion pass its contents did not render for
  automated viewing, so appointment types and slot visibility were recorded as not established.
  *Reconciled the same day:* a view-only recheck (S-83, re-read entry) loaded the widget for
  AdaCare's location. See §1.2 *Booking* for what it shows. The scheduler URL is group-level; which
  other ADC practices use it, and how, is not established (RQ-40).
- **What the group site does not publish:** patient-facing insurance lists, fees or hours. Those
  are published per practice, where at all.

### 1.2 Practice example: AdaCare Dental & Dentures, Meridian ID (one practice)
- **Address and hours** (S-81): 3909 E Fairview Ave #150; Mon 9–5, Tue 9–5, Wed 8–3, Thu 10–6,
  every other Friday 9–4.
- **Services** (S-81): preventive, cosmetic, restorative (crowns, dentures, relines, implant
  restoration), periodontics, root canal, oral surgery (extraction, implants, full-arch), sedation
  (nitrous and oral conscious), clear aligners.
- **New patients** (S-16):
  - "$89 New Patient Exam and X-rays".
  - Cleaning is usually not done on the same day as the new-patient exam.
  - New patients of all ages are welcome, but very young children are referred to a pediatric
    dentist ("We work on grown-up teeth only").
  - Patients print and complete the forms, or arrive 10 minutes early to fill them in.
  - The first visit may include an exam, X-rays, an oral cancer screening, cleaning and a
    consultation, plus a "detailed financial consultation".
- **Insurance and payment** (S-16): contact the office before the visit with insurance details "for
  verification of benefits"; "accept most major dental insurances and will file most claims for you
  as a courtesy"; CareCredit, payment plans and major credit cards. No list of plans is published.
- **What to bring** (S-15): "Typically, you will be asked to bring a photo ID and a copy of your
  insurance details (if any)". The word *typically* matters: this is not a stated hard requirement.
- **Paper forms packet** (S-82; 4 pages, pages 2–4 scanned images):
  - an electronic-communications consent (text, email or voice);
  - patient information, including an **SS# field** (the form does not say whether it is
    required), primary and secondary dental insurance, policy-holder details and referral source;
  - a consent for services with **fees for walk-in visits, cancellations with less than 24 hours'
    notice, and arriving more than 10 minutes late**;
  - a medical and dental history (clinical; out of scope);
  - a HIPAA acknowledgment.
- **Booking:** phone, or the "Book Now" widget (S-16). The widget (S-83, re-read 2026-10-15,
  view only) asks New or Existing Patient and whether the booking is for the patient or "Someone
  Else". For a new patient it offers six services: Denture Repair, Emergency Visit, Implants, New
  Patient Visit, Second Opinion and Sedation Dentistry Consultation. Choosing **New Patient Visit
  displayed dates and times before any personal details were entered.** The later "Schedule" step
  was not opened and nothing was submitted, so the fields collected afterwards, the confirmation and
  whether the booking writes to the practice system are **not established**. This is published
  self-scheduling at one practice, not evidence of complete digital onboarding: the paper packet
  and phone-based insurance check still appear on the new-patient page (S-16, S-82).

## 2. Our interpretation (inference)

- **Reuse is plausible at the platform level.** ADC says it centralises scheduling, recall,
  patient communications, insurance verification and practice software (S-79). If true, one intake
  configuration could serve many practices behind one group scheduler. Whether every practice
  actually uses these services is unknown (RQ-9, RQ-40).
- **AdaCare already does the human version of onboarding by phone.** Reviewers praise its reminder
  and check-in calls, payment plans and insurance help (S-84). The opportunity is consistency and
  staff time across the network, not fixing a failing office.
- **Paper forms are the visible remaining step** at this practice: a printable packet, or arriving
  early to complete it. Scheduling itself is already self-service with visible slots (S-83).
  Contact capture, scheduling and the administrative packet are separate stages here, and only the
  first two are visibly digital. That is a description of what is published, not a failure.

## 3. What we must not assume

- That other ADC practices follow AdaCare's forms, fees, hours, scheduler or appointment types (RQ-9).
- That ADC buys software centrally or would approve a pilot (RQ-5, RQ-18).
- That SSN is required because the paper form has a field for it (RQ-15).
- That visible slots mean a booked visit is confirmed in the practice system, or that the widget
  collects insurance or forms; the post-slot steps were not viewed (RQ-40).
- That AdaCare's positive phone behaviours (reminder and check-in calls, insurance and payment help;
  S-84) indicate a gap. They are strengths to preserve.
- That 76 practices are 76 deployment opportunities; they are one AEA platform.

## 4. Open questions

RQ-2, RQ-5, **RQ-9**, RQ-10, RQ-14, **RQ-16** (minors and guardians), RQ-18, RQ-25, RQ-26,
**RQ-40** — see [research questions](../research-questions.md).
