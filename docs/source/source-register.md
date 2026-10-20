# Source Register

**Owner of:** every source this project relies on: where it is, how authoritative it is, when it
was reviewed, and what it supports. Other documents cite sources by `S-N`. IDs are stable and
grouped by company, not strictly in order.

**Authority labels:**
- **ISSUED:** a document from the partner, via Gauntlet. It is what gets graded.
- **DERIVED:** our own analysis.
- **EVIDENCE:** our own record of public data.
- **CONTEXT-AEA:** AEA's own website.
- **CONTEXT-CO:** a portfolio company's or practice's own website.
- **CONTEXT-PEER:** another provider's published patient journey; an example, not evidence about an AEA company.
- **PROFESSIONAL-GUIDANCE:** a professional association's practice guidance; not a universal operational or legal requirement.
- **PRIMARY-LAW:** official statutory text; scope and effective law still depend on jurisdiction.
- **PRIMARY-GUIDANCE:** regulator or standards-body guidance, not independent legal clearance.
- **PRIMARY-VENDOR:** vendor terms/documentation; not proof of our account configuration or an executed agreement.

Context sources prove what an organisation *publishes*, not how it operates (see
`.claude/rules/source-authority.md`).

**What "Reviewed" means:**
- **2026-10-15 ✓:** fetched and checked in the research completion pass (see the section near the end).
- **2026-10-14 ✓:** fetched and checked against the claims in this repo on 2026-10-14, during
  project initialisation.
- **2026-10-13/14 (notes):** read during the earlier Gauntlet research and recorded there; not
  re-read in this session.

---

## Provenance of the issued brief (S-1)

| Field | Value |
|---|---|
| Local copy | `docs/source/aea-proj1-onboarding-assistant.md` (unchanged) |
| Copied from | `Gauntlet AI/artifacts/2026-10-13-partner-briefs/aea-proj1-onboarding-assistant.md` |
| Received | 2026-10-13, via the Gauntlet hiring-partner portal. The `Gauntlet AI` copy was itself copied from `~/Downloads` (companion doc header). |
| Copied | 2026-10-14; byte-identical (`cmp` passed) |
| SHA-256 | `0de4e06ea72524b1725af63fdd48a3fb364712d16c21f79c9b1d8e49a0011331` |
| Rule | Never edit. A new version from the partner gets a new dated file and a new row here. |
| Related | Riverside's onboarding brief sits beside the original in `Gauntlet AI/`. It is out of frame for this project for now. |

## Local sources

| ID | Source | Authority | Reviewed | Supports |
|---|---|---|---|---|
| S-1 | AEA Project 1 brief (above) | ISSUED | 2026-10-14 ✓ | Scope, required flows, edge cases, metrics (illustrative), stack, security, rubric, submission requirements; re-read for the audit's C1–C11 internal-consistency comparison on the same date |
| S-2 | `Gauntlet AI/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md` (§0, §0.1, §2) | DERIVED | 2026-10-15 ✓ | General-domain finding and Riverside identity correction (§0); portfolio comparison carried into [fit review](../analysis/portfolio-fit-review.md) (§0.1); AEA context and role hypothesis (§2) |
| S-3 | `Gauntlet AI/artifacts/2026-10-13-partner-projects-todo.md` (Project 1) | DERIVED | 2026-10-15 ✓ | Pipeline; historical T1–T13 hypotheses, superseded by the [local audit](../analysis/2026-10-14-brief-audit.md); dates feeding [SUBMISSION](../../SUBMISSION.md); GQ-19 identity closure |
| S-4 | AEA portfolio inventory: [local copy](../evidence/2026-10-14-aea-portfolio-inventory.json), original at `Gauntlet AI/artifacts/2026-10-14-aea-portfolio-inventory.json` | EVIDENCE (our record of S-6 and the profiles) | 2026-10-14 ✓ | 118 profiles; 56 current/active; workflow groups. Copy is byte-identical; SHA-256 `20f9dc63f3a30cd57a2a03f34f738aec71e17d3c16cee78f013ad2d06f87e639` |
| S-5 | `Gauntlet AI/open-questions.md` (GQ-18…GQ-20) | DERIVED | 2026-10-15 ✓ | GQ-19 Riverside identity resolved from first-party disclosures; GQ-18 shared submission and GQ-20 deadline remain open |

## AEA web sources

| ID | URL | Authority | Reviewed | Supports |
|---|---|---|---|---|
| S-6 | https://www.aeainvestors.com/portfolio/ | CONTEXT-AEA | 2026-10-14 (inventory) | The directory of 118 profiles |
| S-7 | https://www.aeainvestors.com/elevate/ | CONTEXT-AEA | 2026-10-13/14 (notes) | Elevate covers business and healthcare services; SLATE framework |
| S-8 | https://www.aeainvestors.com/middle-market-private-equity/ | CONTEXT-AEA | 2026-10-14 (notes) | Middle Market focuses on industrials |
| S-9 | https://www.aeainvestors.com/team-member/avi-shah/ | CONTEXT-AEA | 2026-10-13 (notes) | Head of AI Solutions; former Salesforce Agentforce product director |
| S-24 | https://www.aeainvestors.com/aea-elevate-adds-experienced-operating-professionals-to-further-accelerate-portfolio-value-creation/ | CONTEXT-AEA | 2026-10-13 (notes) | Elevate operating hires (Feb 2026); possible source of the SLATE wording. Which of S-7 or S-24 holds the quote was not recorded. |

## Company web sources (anchor cohort)

| ID | URL | Authority | Reviewed | Supports |
|---|---|---|---|---|
| S-10 | https://www.aeainvestors.com/portfolio/commonwealth-pain-spine/ | CONTEXT-AEA | 2026-10-14 ✓ | Current · Elevate · 2022 · Louisville; description; AEA board members |
| S-11 | https://www.mypainsolution.com/about/new-patient-registration/ | CONTEXT-CO | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | What a *complete referral* from a referring provider contains (demographics incl. SSN, insurance cards, notes, imaging) — **not** a list of patient-entered fields; fax referral; new-patient scheduling phone and email; valid unexpired photo ID and the accepted ID types; downloads (new-patient letter S-72, NPP/bill of rights S-73). 2026-10-15: no list of "cities served" appeared in the fetched text; footprint now comes from S-69. |
| S-12 | https://www.mypainsolution.com/faq/ | CONTEXT-CO | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | Arrival instructions (new patients 30 min early if forms not done; follow-ups 15 min; procedures 30 min); what to bring (insurance cards, photo ID, co-payment, recent imaging/consults); scheduling aim "within 10 days of referral or initial contact" and "within ten business days of initial contact"; **$50 fee for cancellations with <24 h notice; >10 min late may be rescheduled**; **self-pay "to accommodate uninsured patients only"**; payment plans; cost estimates; referral answers are inconsistent ("most insurance plans require a referral" vs "Some … Others allow you to schedule directly"); prior authorisation days to weeks; MVA after PIP exhausted; workers' comp needs authorisation; procedure prep (fasting, driver after sedation). **The 2026-10-14 reading missed the fee, self-pay and scheduling-aim items.** |
| S-13 | https://www.aeainvestors.com/portfolio/american-dental-companies/ | CONTEXT-AEA | 2026-10-14 ✓ | Current · Elevate · 2024 · Phoenix; description |
| S-14 | https://www.ameridentco.com/partner-practices | CONTEXT-CO | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | Practice network: 76 practice-profile links; 74 city/state entries across 15 states (AZ 26, CA 16, WA 6, WY 4, ID 3, PA 3, CO 2, AK 2, NM 2, GA 2, UT 2, FL 2, MD 2, MN 1, TX 1). Machine counts; the two methods differ by 2. |
| S-15 | https://dentistinmeridian.com/frequently-asked-questions/ | CONTEXT-CO (one practice) | 2026-10-14 ✓; re-read 2026-10-15 ✓ (wording "Typically, you will be asked…" unchanged) | AdaCare: photo ID, insurance details, forms in advance |
| S-16 | https://dentistinmeridian.com/new-patients/ | CONTEXT-CO (one practice) | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | AdaCare: **$89 new-patient exam and X-rays**; cleaning usually not the same day as the new-patient exam; all ages but very young children referred to a pediatric dentist; print forms or arrive 10 min early; first-visit contents; contact office with insurance before the visit; accepts most major dental insurance and files claims as a courtesy; financial consultation; CareCredit, payment plans, major credit cards; Book Now widget (S-83). |
| S-17 | https://www.aeainvestors.com/portfolio/metro-vein-centers/ | CONTEXT-AEA | 2026-10-14 ✓ | Current · Elevate · New York; no investment date shown |
| S-18 | https://www.metroveincenters.com/locations/new-york | CONTEXT-CO | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | Free evaluations in each NY clinic; 200+ plans incl. Medicare and Medicaid; 17 NY clinics with Google review counts. Network count now owned by S-89. |
| S-19 | https://www.metroveincenters.com/privacy-policy | CONTEXT-CO | 2026-10-14 ✓; re-read 2026-10-15 ✓ | Chatbot for appointment requests, insurance verification and general inquiries; data stored in HubSpot; SMS programme sends opted-in appointment reminders and marketing |
| S-20 | https://www.aeainvestors.com/portfolio/american-oncology-network/ | CONTEXT-AEA | 2026-10-14 ✓ | Current · Elevate · 2023 · Fort Myers; description |
| S-21 | https://www.aoncology.com/practices/florida-oncology-and-hematology/ | CONTEXT-CO (one practice) | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | Links to the FOH new-patient packet (S-98), records release and NPP (S-99) and the practice site floridaonc.com (S-94); 5 offices in 4 cities (Cape Coral, Clearwater, Fort Myers, Naples ×2). |
| S-22 | https://www.aeainvestors.com/portfolio/numotion/ | CONTEXT-AEA | 2026-10-14 ✓ | Current · Middle Market · 11/2018 · Nashville; description |
| S-23 | https://www.numotion.com/order-process-and-timeline | CONTEXT-CO | 2026-10-14 ✓; **re-read 2026-10-15 ✓** | Four steps with stated times: evaluation about 1 week; **medical documentation about 2–4 weeks**; funding approval about 2–8 weeks; delivery process about 2–8 weeks (build 2–8 weeks, delivery ~1 week). |

## Alternative-group evidence (used only in the fit review)

All of these were read in the 2026-10-14 research and recorded in S-2 §0.1. **None was re-read in
this session.** All are CONTEXT-CO.

| ID | URL | Supports |
|---|---|---|
| S-25 | https://www.nesfircroft.com/talent-acquisition-services/contract-staffing/assignment-support/ | NES: assignment support (mobility, work permits, welfare) |
| S-26 | https://redglobal.com/anti-slavery | RED: identity and right-to-work checks, consultant onboarding |
| S-27 | https://www.bespokepartners.com/ | Bespoke: executive search |
| S-28 | https://50floor.com/schedule-now/ | 50 Floor: consultation-led sales |
| S-29 | https://www.windownation.com/ | Window Nation: consultation-led sales |
| S-30 | https://markspain.com/blog/how-to-get-a-guaranteed-offer-on-your-home | Mark Spain: property details before consultation |
| S-31 | https://www.bmscat.com/ | BMS CAT: urgent property-damage restoration |
| S-32 | https://www.montway.com/app/uploads/2024/07/prepare-vehicle-shipping-guide.pdf | Montway: inspection and bill-of-lading steps |
| S-33 | https://www.magna5.com/managed-it-services/ | Magna5: account- and system-level managed IT |
| S-34 | https://amerivet.com/partnership-locations | AmeriVet: practice directory |
| S-35 | https://amerivet.com/blog/veterinary-appointment-scheduling?hs_amp=true | AmeriVet: scheduling discussion |

## Brief audit primary sources

Reviewed **2026-10-14** for the [brief audit](../analysis/2026-10-14-brief-audit.md).
Claims are limited to the identified passages. Web documentation and account offerings can change;
recheck selected services before use. Review means public source review, not contract execution,
deployment verification or jurisdiction-specific legal clearance. S-48's indexed official passage
was checked; direct page retrieval repeatedly failed. The other sources below were opened.

| ID | Source and passage | Authority | Supports |
|---|---|---|---|
| S-36 | [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms?hl=en), effective March 23, 2026; Age Requirements, Use Restrictions, Unpaid/Paid Services | PRIMARY-VENDOR | Personal/sensitive input restriction, review/improvement use, age/region/medical-use limits |
| S-37 | [Groq BAA](https://console.groq.com/docs/legal/customer-business-associate-addendum), §1.1 | PRIMARY-VENDOR | Covered Cloud Services exclude free/trial and other listed services |
| S-38 | [Your Data in GroqCloud](https://console.groq.com/docs/your-data), retention sections | PRIMARY-VENDOR | Default inference behavior; feature-state and reliability/abuse exceptions, controls and retention |
| S-39 | [HHS cloud computing guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html), introduction and Q1–2 | PRIMARY-GUIDANCE | HIPAA role conditions; cloud BAA obligations including encrypted storage |
| S-40 | [Supabase shared responsibility](https://supabase.com/docs/guides/deployment/shared-responsibility-model), Managing healthcare data | PRIMARY-VENDOR | At least Team plan for BAA, HIPAA add-on and configuration responsibilities |
| S-41 | [HIPAA on Render](https://render.com/docs/hipaa-compliance), setup and important considerations | PRIMARY-VENDOR | Eligible workspaces/plans; free instances excluded; resource/log restrictions |
| S-42 | [Railway compliance](https://docs.railway.com/enterprise/compliance), HIPAA BAA | PRIMARY-VENDOR | Shared responsibility and BAA add-on with paid monthly spend threshold |
| S-43 | [Ollama FAQ](https://docs.ollama.com/faq), disabling cloud features | PRIMARY-VENDOR | Local-only mode requires actual configuration; cloud functionality exists |
| S-44 | [FDA administrative-support software scope](https://www.fda.gov/medical-devices/digital-health-center-excellence/step-2-software-function-intended-administrative-support-health-care-facility) | PRIMARY-GUIDANCE | Administrative functions excluded by statutory provision; not clearance of clinical uses |
| S-45 | [NIST AI 600-1](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf), July 2024, §§2.3, 2.7 and testing/evaluation actions | PRIMARY-GUIDANCE | Dangerous recommendations, human–AI interaction risks and contextual evaluation; voluntary guidance |
| S-46 | [FTC dark-pattern report announcement](https://www.ftc.gov/news-events/news/press-releases/2022/09/ftc-report-shows-rise-sophisticated-dark-patterns-designed-trick-trap-consumers), September 2022 | PRIMARY-GUIDANCE | Manipulative data/consumer choice practices; does not condemn every help trigger |
| S-47 | [European Commission AI Act Article 3](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-3), definition (39); [Recital 18](https://ai-act-service-desk.ec.europa.eu/en/ai-act/recital-18) | PRIMARY-LAW (Commission presentation) | Emotion-recognition definition based on biometric data; does not establish applicability to this demo |
| S-48 | [Illinois BIPA §10](https://www.ilga.gov/legislation/ilcs/fulltext?DocName=074000140K10) | PRIMARY-LAW; official indexed passage, direct retrieval unavailable | Photograph/demographic exclusions and face-geometry inclusion; no determination of this project's jurisdiction or other state laws |
| S-49 | [18 USC §1028, official text through October 7, 2026](https://uscode.house.gov/us/usc/119-118/t18/s1028/), (a), (c), (d) | PRIMARY-LAW | Identification-document offense elements and definitions; supports conservative fixture choice, not clearance of a specimen |
| S-50 | [HHS medical-record retention FAQ](https://www.hhs.gov/hipaa/for-professionals/faq/does-hipaa-require-covered-entities-to-keep-medical-records-for-any-period/index.html) | PRIMARY-GUIDANCE | HIPAA Privacy Rule does not set medical-record retention; state law generally does; safeguards through disposal |
| S-51 | [FTC COPPA FAQ](https://www.ftc.gov/business-guidance/resources/complying-coppa-frequently-asked-questions), A and H | PRIMARY-GUIDANCE | Child-directed services, actual knowledge and direct under-13 collection; FAQ flags April 2025 rule amendments, so not a complete current compliance checklist |
| S-52 | [FTC Health Breach Notification Rule compliance guidance](https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0) | PRIMARY-GUIDANCE | Conditional duties outside HIPAA for qualifying personal health record businesses |
| S-53 | [PCI SSC FAQ 1217](https://www.pcisecuritystandards.org/faqs/1217/) | PRIMARY-GUIDANCE (industry standards body) | PCI DSS applies to storing, processing or transmitting cardholder data; industry standard, not general financial-data law |
| S-54 | [OWASP LLM prompt-injection prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) | PRIMARY-GUIDANCE (security guidance) | Direct/indirect instructions, least privilege and layered defenses |
| S-55 | [Supabase JWT guidance](https://supabase.com/docs/guides/auth/jwts), verification | PRIMARY-VENDOR | Verify tokens with appropriate libraries; identity verification does not replace authorization |
| S-56 | [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security), Bypassing Row Level Security | PRIMARY-VENDOR | Privileged service role/DB roles may bypass RLS; keys and request context matter |
| S-57 | [PostgreSQL constraints](https://www.postgresql.org/docs/current/ddl-constraints.html), unique and exclusion constraints | PRIMARY-VENDOR (official project documentation) | Database enforcement mechanisms; not proof of a future booking implementation |
| S-58 | [k6 built-in metrics](https://grafana.com/docs/k6/latest/using-k6/metrics/reference/), http_req_duration and http_req_failed | PRIMARY-VENDOR | Duration boundaries and separate failure metric |
| S-59 | [Render free-service limits](https://render.com/docs/free), idle spin-down | PRIMARY-VENDOR | 15-minute idle sleep, roughly one-minute restart and other free-service limits |
| S-60 | [OWASP file upload guidance](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html) | PRIMARY-GUIDANCE (security guidance) | Layered format validation, authorization, limits and storage isolation |
| S-61 | [W3C understanding timing adjustable](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html), WCAG 2.2 SC 2.2.1 | PRIMARY-GUIDANCE (accessibility standard explanation) | User control over content time limits; not a jurisdiction-specific legal compliance verdict |
| S-62 | [HHS de-identification guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html), methods and identifier conditions | PRIMARY-GUIDANCE | Removing a name alone does not establish de-identification |

## Related partner identity source

| ID | Source and passage | Authority | Supports |
|---|---|---|---|
| S-63 | [The Riverside Company regulatory disclosures](https://www.riversidecompany.com/regulatory-disclosures), reviewed 2026-10-15 | FIRST-PARTY COMPANY | Identifies Riverside Partners L.L.C. as doing business as The Riverside Company; corroborates the portal card's name and website. Context only; does not change the AEA brief or niche. |

## Sources added in the 2026-10-15 research completion pass

All read **2026-10-15**. Text was cached locally for checking (`docs/evidence/raw-page-text/`, git-ignored and re-fetchable); claims cite the live URL. Commonwealth's site sits behind a Cloudflare check, so its pages were read through the `stealth-chrome` browser session; forms were **viewed only — nothing was entered or submitted**.

### Commonwealth Pain & Spine (CONTEXT-CO)

| ID | Source | Supports |
|---|---|---|
| S-64 | https://www.mypainsolution.com/ (home) | Claims: "Led by Dual Board-Certified Physicians", "Care That's Built Around You", "Advanced, Minimally Invasive Pain Treatments", "Convenient Access … 32+ locations … prompt scheduling"; existing patients directed to the Patient Portal |
| S-65 | https://www.mypainsolution.com/about/ | "more than 30 clinics"; mission ("quickly responding with compassionate, personalized, and comprehensive treatment plans"); P.R.O.U.D. values incl. Responsiveness ("From timely access to care to persistent follow-up"); states served |
| S-66 | https://www.mypainsolution.com/about/complete-care/ | Complete Care components: physician-led team, interventional treatments, Remote Therapeutic Monitoring, Chronic Care Management, Behavioral Health Integration, patient portal (messaging, appointment requests), **"24/7 Virtual Agent"** that helps "with scheduling needs and connect you with the appropriate member of your care team", educational resources |
| S-67 | https://www.mypainsolution.com/about/insurance-information/ | Accepted plans by state (KY & IN, OH, IL, WV, VA, TN, SC, NC) with plan-specific notes (e.g. UHC Medicare "Referral required", Devoted Health out-of-network only); insurance FAQ (cost estimates, payment plans, denials and appeals, self-pay for uninsured) |
| S-68 | https://www.mypainsolution.com/about/patient-guarantee/ | Pledge: "Our scheduling staff is devoted to finding appointments for new patients within ten business days of referral or initial contact"; accept all new patients |
| S-69 | https://www.mypainsolution.com/locations/ | 33 offices in 7 states (KY 14, IN 6, SC 5, TN 4, OH 2, IL 1, NC 1); address, phone and today's hours per office; 11 offices marked "By Appointment Only" on the day read |
| S-70 | https://www.mypainsolution.com/louisville-south/ | Louisville South (4420 Dixie Hwy — the office Google labels "Shively"): Mon–Fri 7:45 AM–5:00 PM by appointment, Sat–Sun closed; 2 MDs + 1 APRN listed; self-referral explanation; 3-step path ending "We aim to get you seen within two weeks" after the physician's referral is received |
| S-71 | https://www.mypainsolution.com/providers/ | Provider directory (17 pages; filter by name/gender; each provider shows credential and offices); "We accept nearly all insurance and are accepting new patients at all our locations." Full enumeration not completed (pager not scriptable) |
| S-72 | https://sa1s3.patientpop.com/assets/docs/93508.pdf (new-patient letter, linked from S-11) | Welcome letter; physicians listed as board certified in pain medicine and anesthesiology; ten-business-day pledge; patient obligations incl. "Payment of fees at the time of service" |
| S-73 | https://sa1s3.patientpop.com/assets/docs/93509.pdf (NPP and bill of rights, linked from S-11) | Legal entity "Commonwealth Pain Associates, PLLC dba Commonwealth Pain & Spine"; privacy notice |
| S-74 | Referral forms: https://www.mypainsolution.com/documents/Referral.-updated-03.06.25.pdf ; https://www.mypainsolution.com/documents/newpatientreferral_502.-updated-07.30.26.pdf ; https://sa1s3.patientpop.com/assets/docs/440434.pdf | Physician-to-office map (versions differ; 2025-03-06 form lists 20 physicians + 1 PT); referral reasons, pain areas, MVA and workers' comp sections; fax (866) 697-2464 |
| S-75 | https://commonwealth.prettygoodai.net/request-appointment/start?pagemode=Live (request form; viewed only) | Required fields: first/last name, phone, email, DOB, preferred clinic, seen before (Y/N), previous or referring provider (search or manual), street address, city, state, ZIP, gender, insurance company (list), member ID, reason for referral, preferred contact method (phone/email), MVA (Y/N), work injury (Y/N); optional "how did you hear". **No SSN, no ID upload.** "Powered by" prettygoodai |
| S-76 | https://www.mypainsolution.com/services/ ; /conditions-we-treat/ ; selected service pages (injections, medication management, nerve ablation, neurostimulation, kyphoplasty, chronic care management, psychological pain assessment, occupational medicine) | Service catalogue and condition list |

### American Dental Companies and AdaCare (CONTEXT-CO)

| ID | Source | Supports |
|---|---|---|
| S-78 | https://www.ameridentco.com/ ; /about | Positioning to dentists: "Patient Care, Team Care, Business Care"; doctor-led ownership; leadership |
| S-79 | https://www.ameridentco.com/what-we-do/insurance-verification ; /patient-communication ; /information-technology | Central services to practices: insurance verification, A/R, claims, credentialing; scheduling services, continued-care recall, "Full Oversight of Patient Communications"; "Cloud-based centralized dental management software", cloud X-ray, practice analytics |
| S-80 | https://www.ameridentco.com/partnership | Partner-facing claim of "a minimum increase of 30% in revenue in the first year of partnership" (a claim to dentists, not a patient fact) |
| S-81 | https://dentistinmeridian.com/ (AdaCare home) and service pages | Office hours (Mon 9–5, Tue 9–5, Wed 8–3, Thu 10–6, every other Fri 9–4); address and phone; service catalogue incl. sedation (nitrous, oral conscious), dentures, implants, full-arch |
| S-82 | https://dentistinmeridian.com/wp-content/uploads/2024/04/AdaCare-Dental-Dentures-New-Patients-Forms.pdf | 4-page packet: electronic-communications consent; patient information (incl. SS# field, two dental insurances, policy-holder data, referral source); consent for services with fees (walk-in, <24 h cancellation, >10 min late); medical and dental history; HIPAA acknowledgement. Pages 2–4 are scanned images, read visually |
| S-83 | https://schedule.jarvisanalytics.com/frame/american-dental-companies?location_id=10886 | **First reading (2026-10-15, completion pass):** booking widget exists; its contents did not render for automated viewing (the cached text fetch returned an empty frame), so appointment types and slot visibility were not established. **Re-read 2026-10-15 (reconciliation pass, Chrome DevTools, isolated browser context; view only):** the widget rendered for AdaCare's Meridian address. Step 1 asks New or Existing Patient and "Booking for" Myself / Someone Else (Adult). New Patient lists six services: Denture Repair, Emergency Visit, Implants, **New Patient Visit**, Second Opinion, Sedation Dentistry Consultation. Choosing New Patient Visit showed dates and times for 19–26 Oct 2026 **before any personal details were requested**; the next step ("2 Schedule") was not opened, no slot was selected and nothing was submitted. This matches an earlier chat walkthrough reported by Innocent. It establishes that published self-scheduling with visible slots exists at this practice. It does not establish what happens after submission, whether the booking reaches the practice system, or whether other ADC practices use the same configuration (RQ-40). |

### Metro Vein Centers (CONTEXT-CO)

| ID | Source | Supports |
|---|---|---|
| S-85 | https://www.metroveincenters.com/ | "We treat people, not symptoms."; patient-centred care, board-certified specialists, innovation; 200+ plans |
| S-86 | https://www.metroveincenters.com/faqs | ABVLM certification; cosmetic treatment $425 per session; self-pay range $425–$1,500; "91% of our vein treatments are covered"; reschedule by phone 866-715-9121 or by texting the reminder number; records by email; treatment list; pregnancy guidance |
| S-87 | https://www.metroveincenters.com/insurance | Insurance specialist role ("A real person … No chat bots"); six-step insurance process; verification "about 24–48 hours"; estimate callback "within 24-48 business hours"; Medicaid "accepted in select states"; self-pay and financing; top plans list |
| S-88 | https://www.metroveincenters.com/consult (form viewed only) | Free-evaluation form: first name, last name, email, phone (required), newsletter opt-in; free evaluation "subject to insurance eligibility"; 98% satisfaction and "20,000 5-Star reviews" claims; payment methods |
| S-89 | https://www.metroveincenters.com/locations (and the clinic list on S-87) | 80 clinics in 9 states (TX 24, NY 17, NJ 12, MI 8, AZ 7, CT 6, IL 4, GA 1, PA 1) |
| S-90 | https://www.metroveincenters.com/locations/new-york/queens-forest-hills | Forest Hills hours (Mon 9:30–7, Tue 8–5, Wed 8–4, Thu 8–5, Fri 8–4:30); named physicians; IAC accreditation claim; bilingual-office testimonial |

### American Oncology Network and Florida Oncology & Hematology (CONTEXT-CO)

| ID | Source | Supports |
|---|---|---|
| S-92 | https://www.aoncology.com/who-we-are/ ; /for-patients/ ; /technology/ ; /patient-centric-care/ | Platform: launched 2018; centralised pharmacy, pathology, "fully integrated electronic medical records" (OncoEMR), patient portal, browser-based telehealth, care coordination, financial assistance |
| S-93 | https://www.aoncology.com/locations/ | Network location list (paged/map-driven; full count not established in this pass) |
| S-94 | https://www.floridaonc.com/ ; /about-us/ ; /your-team/ | FOH services (medical oncology, hematology, BiTE, imaging, radioligand, pathology, pharmacy, care coordination, clinical trials, financial support); 10 physicians and 15 advanced practitioners linked |
| S-95 | https://www.floridaonc.com/new-patient-information/ | Entry by "physician's referral or transfer"; second opinions welcome; call (239) 217-8011; documents incl. Spanish; what to bring (medication list, prior illnesses, surgeries, allergies, insurance card); "strive to keep waiting times for appointments to a minimum" |
| S-96 | https://www.floridaonc.com/patient-referral/ ; /contact-us/ | Per-office referral forms, phones and faxes; contact form cannot schedule ("call our office or use the patient portal"); do not send SSNs via the form; CareSpace patient portal for clinical questions; after-hours answering service |
| S-97 | https://www.floridaonc.com/make-a-payment/ ; /service/financial-support/ ; /service/care-coordination/ | Online payment and payment plans; financial counsellor at an initial visit; care coordination (barriers to care, navigation) and free dietitian visits |
| S-98 | https://www.aoncology.com/wp-content/uploads/2023/05/13680_FOH_New-Patient_Form_251105_FINAL.pdf | 14-page packet: consent to treat; demographics (incl. SS#, language, contact preferences, pharmacy); PCP and referring physician; emergency contact; advance directives; clinical history; photo authorisation; records-release request; disclosure consent; insurance (incl. policy-holder SS#); NPP acknowledgement; financial policies; SMS/email consent; patient-assistance authorisation |
| S-99 | FOH records-release PDF (…/12913_FOH_MRR_Medical-Records-Release_Form_240716_FINAL.pdf) and NPP PDF (…/13817_FOH_Notice-of-Privacy-Practices-NPP-HIE_Form_260123_Final.pdf) | Records release and privacy notice |

### Numotion (CONTEXT-CO)

| ID | Source | Supports |
|---|---|---|
| S-101 | https://www.numotion.com/ ; /who-we-are | "nation's largest and leading provider of Complex Rehab Technology"; services (CRT, service & repair, urology supplies, speech solutions, workers' comp via CorLife, SpinLife retail); accreditations |
| S-102 | https://www.numotion.com/what-to-expect ; /understanding-the-insurance-process ; /medical-necessity | Insurance process after a referral (verification → prior authorisation 15–60 days → follow-up/appeal); provide primary and secondary insurance; Medicare MBI; one wheelchair per 5 years under Medicare; face-to-face doctor visit and Letter of Medical Necessity for complex chairs |
| S-103 | https://www.numotion.com/billing-and-financing | Medicaid and Medicare in all states; online payment; payment plans; CareCredit |
| S-104 | https://www.numotion.com/faqs ; /contact | National customer care (800) 500-9150; live chat; track your order; after-hours support hours |
| S-105 | https://www.numotion.com/locations ; /locations/nashville-tn | 114 branches in 45 states; Nashville branch = 161 F Bain Drive, LaVergne, TN (Mon–Fri 8:30–5:00; new-equipment evaluation by appointment) |
| S-106 | https://www.numotion.com/in-home-service-repair ; /about-mynumotion-app | Repair scheduling steps and what to have ready; myNumotion app guide lists real-time order information, text/email notification of order status change, equipment listing, request service, appointment calendar, self-pay estimate, invoices and live chat with a representative; its home-screen image shows order status, appointments, service requests and a clinical-team entry. **This is documented capability from a public guide, not a test of a live customer account or of how well it performs** (noted 2026-10-15, reconciliation pass). |

### Public review evidence (EVIDENCE — attributed reports of experience, not operational facts)

| ID | Source | Supports |
|---|---|---|
| S-77 | Google review dialogs: Commonwealth Pain and Spine Louisville South (Google listing labelled "Shively", 4420 Dixie Hwy; 4.7, 3,105 reviews) and Elizabethtown (4.7, 2,844) | Lowest and Newest samples; see [review report](../analysis/2026-10-15-google-review-sentiment.md) |
| S-84 | Google review dialog: AdaCare Dental & Dentures, Meridian ID (4.9, 171) | As above |
| S-91 | Google review dialog: Metro Vein Centers Queens–Forest Hills (4.8, 881) | As above |
| S-100 | Google review dialog: Florida Oncology & Hematology Naples (4.9, 446) | As above |
| S-107 | Google review dialog: Numotion Nashville branch, LaVergne TN (4.8, 551) | As above |

Raw review extracts are kept locally in `docs/evidence/raw-google-reviews/` (git-ignored; they contain reviewers' own names and health details).

**Not used as evidence:** Google AI Overview summaries and Indeed/Glassdoor employee ratings seen in search results on 2026-10-15. Both appeared in the first version of the review report and were removed in the completion pass because they were not read at source.

## Patient journey and onboarding baseline sources

Reviewed **2026-10-15** for [patient journeys and standard onboarding practices](../analysis/2026-10-15-patient-journeys-and-onboarding-baseline.md). Guidance establishes reference practices, not the five companies' actual internal implementation. No source below establishes measured revenue lift. Previously registered company sources retain their existing IDs.

| ID | Source | Authority | Passage and scope |
|---|---|---|---|
| S-108 | [AMA Patient Pre-Registration](https://edhub.ama-assn.org/steps-forward/module/2702557), published 2016, renewed March 2024 | PROFESSIONAL-GUIDANCE | Introduction and Steps 1–3: registration before a visit or on the day; administrative/history collection, coordinator responsibilities, logistics and baseline measurement. Broader than this project's administrative software scope. |
| S-109 | [AMA Private Practice Playbook Sample Forms](https://www.ama-assn.org/system/files/steps-forward-private-practice-playbook-sample-forms.pdf), pp. 2–3 | PROFESSIONAL-GUIDANCE | Sample packet categories: demographic/history information, benefits assignment, privacy notice and acknowledgement; forms require adaptation. Not legal clearance or a mandate to use every form. |
| S-110 | [ADA Meeting the Doctor](https://www.ada.org/resources/practice/practice-management/meeting-the-doctor) | PROFESSIONAL-GUIDANCE | Patient-intake guidance: explain the visit, interview concerns, check prior radiographs, use understandable language and attend to anxiety. Does not establish AdaCare's implementation. |
| S-111 | [AHRQ Key Strategies for Clear Communication](https://www.ahrq.gov/health-literacy/improve/precautions/tool4a.html) | PRIMARY-GUIDANCE | Toolkit 3rd edition, Tool 4: qualified interpreters, manageable information, questions and checking understanding. |
| S-112 | [AHRQ Assess, Select, and Create Easy-to-Understand Materials](https://www.ahrq.gov/health-literacy/improve/precautions/tool11.html) | PRIMARY-GUIDANCE | Tool 11: streamline forms, everyday words, collect need-to-know information once, get patient feedback and assess missing answers. |
| S-113 | [AHRQ Address Language Differences](https://www.ahrq.gov/health-literacy/improve/precautions/tool9.html) | PRIMARY-GUIDANCE | Tool 9: ask and record spoken/written language preferences and arrange appropriate language access. Scope of legal duties is not assessed here. |
| S-114 | [AHRQ Make Referrals Easy](https://www.ahrq.gov/health-literacy/improve/precautions/tool21.html) | PRIMARY-GUIDANCE | Tool 21: referral responsibilities, direct information exchange, assistance, instructions, attendance barriers and tracking. Clinical triage and results interpretation are outside the assistant's role. |
| S-115 | [W3C WAI Multi-page Forms](https://www.w3.org/WAI/tutorials/forms/multi-page/) | PRIMARY-GUIDANCE | Logical steps, progress, optional stages, timing flexibility and preserving entered data during review. Tutorial guidance, not a complete accessibility certification. |
| S-116 | [W3C WAI User Notification](https://www.w3.org/WAI/tutorials/forms/notifications/) | PRIMARY-GUIDANCE | Explain errors, correction routes and successful submission; provide accessible feedback. |
| S-117 | [HHS Notice of Privacy Practices](https://www.hhs.gov/hipaa/for-individuals/notice-privacy-practices/index.html) | PRIMARY-GUIDANCE | Receipt acknowledgement is distinct from permission for special disclosures; patient signature is not mandatory; provider documents refusal. Not a complete deployment-specific legal checklist. |
| S-118 | [CMS Good Faith Estimate](https://www.cms.gov/initiatives/your-patient-rights/medical-bill-rights/get-help/guides-resources/what-good-faith-estimate) | PRIMARY-GUIDANCE | Expected charges and conditional estimate rights for people not using insurance; no blanket rule asserted for every insured visit or equipment order. |
| S-119 | [MSK Request an Appointment](https://www.mskcc.org/experience/become-patient/appointment?appointment_type=new), What to expect next | CONTEXT-PEER | Care advisors gather records/test results and help connect patients with the appropriate first appointment. An oncology example, not FOH/AON evidence. |
| S-120 | [Cleveland Clinic Comprehensive Pain Recovery](https://my.clevelandclinic.org/services/comprehensive-pain-recovery-treatment) | CONTEXT-PEER | Multidisciplinary pain service and assessment context. Does not establish Commonwealth's clinical model or booking rules. |
| S-121 | [Metro Vein What to Expect](https://www.metroveincenters.com/what-to-expect) | CONTEXT-CO | Published consultation → ultrasound → clinician plan → insurance work → treatment sequence. A published pathway, not an observed patient workflow or individual coverage promise. |

The indexed ADA intake PDF returned a 404 when opened, and an American Venous Forum PDF redirected inconsistently. Neither was used to establish the baseline.

## Adding a source

Give it the next free `S-N`, label its authority, give the date it was actually read, and say in
one line what it supports. A source that changes after it was read gets a new review date and a
note on what changed. Never silently overwrite the old reading.
