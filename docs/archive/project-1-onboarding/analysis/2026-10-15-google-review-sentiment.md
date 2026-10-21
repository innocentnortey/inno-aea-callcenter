# AEA Healthcare Platforms — Google Review Evidence (attributed experience, not operational fact)

**Read:** 2026-10-15 · **Revised:** 2026-10-15, research completion pass (see *Revision notes*).
**What this file owns:** the public Google review evidence for the five candidate platforms: what was sampled, how it was counted, and the excerpts used elsewhere. Company facts live in the [company profiles](company-research/); the synthesis lives in the [research report](2026-10-15-onboarding-research-report.md).
**Sources:** S-77 (Commonwealth), S-84 (AdaCare), S-91 (Metro Vein), S-100 (Florida Oncology & Hematology), S-107 (Numotion) in the [source register](../source/source-register.md).

## How to read this evidence

- **A review is one person's attributed report of their experience.** It is not a verified operational fact, a failure rate or a measurement of the company's processes. Each location's average is 4.7–4.9★, so the complaints quoted here are a thin tail.
- **The method.** Google search → business card → the review count beside the stars → the review dialog, sorted **Lowest** and **Newest**. Full text, stars, relative date and "owner replied" were extracted by script. Reviewer names were not extracted.
- **Quotation rules.** Text in quotation marks is copied exactly, spelling included. "[…]" marks an omission, and "[name]" marks a removed name. Where a review contains a health narrative that could identify someone, it is paraphrased **without** quotation marks. Two excerpts are Google machine translations and are labelled as such.
- **Denominators.** Each theme count says which sample it comes from. The Lowest and Newest samples overlap at small locations, so their counts are **not added together**.
- **Theme counts are keyword-coded.** They indicate where complaints cluster and are approximate. The coding script is `docs/evidence/raw-google-reviews/scripts/themes.py` (local).
- **Locations, not networks.** One office's reviews describe that office (source-authority rule 4).
- **Not used:** Google AI Overview summaries, and employee ratings from Indeed/Glassdoor search snippets. The first version of this file used both. They were removed because they were not read at source.

## 0. Samples

| Platform | Listing (Google name → company name) | Rating · reviews | Lowest sample | Newest sample | Low tail captured? |
|---|---|---|---|---|---|
| Commonwealth Pain & Spine | "Shively, KY", 4420 Dixie Hwy → the company's **Louisville South** office (S-70) | 4.7 · 3,105 | 80 (all 1–2★; 58 with text) | 80 (about one week; 4 at ≤3★ with text) | Partly: 80 of an unknown number of 1–2★ reviews |
| Commonwealth Pain & Spine | Elizabethtown, KY, 1107 Crowne Pointe Dr | 4.7 · 2,844 | 60 (all 1–2★; 41 with text) | 40 (about one week; 1 at ≤3★) | Partly |
| American Dental Companies | Partner practice **AdaCare Dental & Dentures**, Meridian ID | 4.9 · 171 | 43 loaded, lowest first (all reviews under 5★) | — | Yes: 5 at ≤3★ |
| Metro Vein Centers | Queens – Forest Hills, NY | 4.8 · 881 | 60 (41 at ≤3★; 33 with text) | 70 (about 7 months) | Yes |
| American Oncology Network | Partner practice **Florida Oncology & Hematology, Naples** | 4.9 · 446 | 40 (7 at ≤3★; 6 with text) | 40 (about 3 weeks; none ≤3★) | Yes |
| Numotion (adjacent) | Nashville branch, 161 F Bain Dr, **LaVergne TN** (S-105) | 4.8 · 551 | 60 (31 at ≤3★; 27 with text) | 40 (about one month) | Yes |

**Observed in the extracted data (fact about the sample):**
- Commonwealth replied to 61 of its newest 80 reviews at Louisville South, which are mostly 5★. It replied to 12 of the 80 lowest.
- Metro Vein replied to 59 of 60, and Numotion to 47 of 60, of their lowest samples.

**Inference:** about 80 new reviews in one week at one Commonwealth office, plus one reviewer's complaint about "This constant pressure of asking for reviews", suggests active review requests. Treat recent averages with care.

---

## 1. Commonwealth Pain & Spine (Louisville South and Elizabethtown)

**Praise in the newest reviews:** "Wait time in the lobby was about 10 minutes." Others praise clinicians who explain and listen. One patient arrived from an acquired practice ("my first visit at the new location as a former Metro Pain Associates patient").

**Complaints relevant to onboarding (lowest samples):**

1. **Reaching a person and getting called back.** Keyword hits: Louisville South 10 of 58; Elizabethtown 4 of 41.
   - "I've reached out multiple times via phone and the patient portal since April and not gotten any communication back." (1★, Louisville South, about 3 months ago)
   - "transferred to 5 different people just to reschedule an appointment. Only to be given a voicemail to someone who has not called back." (1★, Elizabethtown, about 3 months ago)
   - A referred new patient said they waited two weeks for a call that never came. (Paraphrased: the review names a diagnosis.)
2. **Automated phone and scheduling assistant.** Six low reviews name "AI": 4 at Louisville South and 2 at Elizabethtown, dated from about a month to about a year ago. A seventh describes a "robot answering" system.
   - "The AI set up an appointment of 8:30am and texted mea confirmation. when I arrived, I was told there was no appointment in the system" (2★, Louisville South, about a month ago)
   - "So tired of talking to your AI assistant answering machine. […] it is just very tiring to not be able to call and speak to a person." (2★, Louisville South)
   - "their wonderful answering AI hung up on me twice." (2★, Elizabethtown)
   - "I’ve been sent the link 4 times from your robot answering/directional answerer and filled it out…. Very frustrating" (2★, Elizabethtown)
   - "the AI system to either change or reschedule an appointment after wasting time to be told I can't do this transfer switching to attendant." (2★, Elizabethtown)

   **What this does and does not show.** Commonwealth itself publishes a "24/7 Virtual Agent" for "scheduling needs" (S-66). Its request form is "Powered by" prettygoodai (S-75). The reviews do **not** establish that these are the same system or the same vendor. They do not establish a technical cause, such as a failed write to the schedule, or how often any problem occurs.
3. **Re-entering information that was already given.** Keyword hits: Louisville South 4 of 58; Elizabethtown 2 of 41.
   - "I have to answer the same questions over and over 4 times in the past few days" (1★, Louisville South, about 9 months ago)
   - "I was sent a link to check in early and update insurance coverage, which is irrelevant and not accounted for when actually checking in because “they do not have access to the website”" (1★, Louisville South, about 2 years ago)
   - "a med asst and NP me all the same questions again that I answered twice online." (2★, Louisville South, about 3 years ago)
4. **Authorisation status the patient can't see.** Keyword hits for insurance or authorisation: Louisville South 10 of 58; Elizabethtown 5 of 41.
   - A family member reported that nobody called when a prior approval came through. Later, they found an approval had not been submitted. (Paraphrased: health narrative.)
   - "There is no excuse for patients not to be notified in advance if this is the case." (2★, Elizabethtown, about 8 years ago)
   - "The time from my initial referral to first MD appt was over six weeks. Prior auth for procedure takes an additional two weeks after that." (2★, Louisville South, about 5 years ago)
5. **No clear next step.** "From day one no one made it clear as to when the next injection would be." (1★, Louisville South, about 9 months ago)

Many low reviews are about clinical decisions: medication, sedation, procedure results. Those are outside an administrative intake product and were not used as onboarding evidence.

## 2. American Dental Companies (AdaCare, Meridian ID: one practice)

- **Five reviews at 3★ or below** across 171. Their themes are price and waiting: "Why do I have to wait in the lobby for 30mins when I made an appointment?" (1★, about 5 months ago). Older reviews are about denture outcomes (clinical).
- **Praise that maps to onboarding steps:**
  - "love their reminder calls" (5★)
  - "they give me a call and check in with me before my appointment" (5★)
  - "helpful with setting up a payment plan that was affordable" (5★)
  - "The office staff is always willing to help with insurance issues" (5★)
- **Reading (inference):** this practice already performs, by phone, the reminder, pre-visit check-in and cost-explanation steps the product would digitise. The case here is consistency across the group, not fixing this office.

## 3. Metro Vein Centers (Forest Hills)

All 41 reviews at 3★ or below were captured; 33 have text. Keyword hits in those 33: waiting in the office 13, front desk 12, insurance 9, appointment changes 3.

- "second time they change my appointment time with out even telling me" (1★, about 2 months ago)
- "I scheduled appointments twice and they cancel a day before the appointment" (1★, about a week ago)
- "Appointments are often set for one time, but upon arrival they tell you that your time is 30-45 minutes later." (2★, about a year ago)
- "I supposed to receive email and text and I have to call 2 times for that. […] They did not gave me address or instructions to I had to ask it." (2★, about a year ago)
- "The receptionist gave me a card and told me to call to schedule it." (1★, about 4 months ago; Google translation)
- "The ad says they'll serve you in your language, but that's false." (1★, about 2 years ago; Google translation)

**Reading (inference):** the complaints are about what happens after the request is captured: confirmed times, change notices, directions and preparation, and language preference. They are not evidence that the published chatbot (S-19) or evaluation form (S-88) fails.

## 4. American Oncology Network (Florida Oncology & Hematology, Naples: one practice)

There are seven reviews at 3★ or below out of 446. The newest 40 are all 4–5★.
- A new patient said the new-patient scheduling contact never returned calls over two weeks. The patient's outside oncologist then sent an order and records, and the patient went elsewhere. (Paraphrased: health narrative.)
- A transferred patient reported no follow-up call after an early test. The same reviewer wrote that "it took me four days to get someone on the telephone" (3★, about 8 months ago). (The rest is paraphrased.)
- "System to collect info was hard to fill out. Bad software" (4★, about 7 months ago)
- "I was charged on my 1st appointment when I should not have been charged." (4★, about 8 months ago)

**Reading (inference):** both serious complaints sit at new-patient or transfer intake, which is administrative. Following up clinical results is out of scope.

## 5. Numotion (Nashville branch, LaVergne TN)

There are 31 reviews at 3★ or below out of 551; 27 have text. Long lead times account for 10 of those 27.
- "I was not offered a loaner chair or kept abreast of the progress of my wheelchair repair." (1★, about 2 months ago)
- "NuMotion, for some reason, now routes EVERY single phone call to an offshore call center." (1★, about 2 years ago)
- "a one -month delay simply to submit a claim to insurance is unacceptable" and "I have had to take the initiative to follow up repeatedly throughout the process rather than being proactively updated." (1★, about a month ago)
- A family reported that the insurer and Numotion gave them conflicting approval and denial messages about an expensive item. (Paraphrased.)
- Technicians are praised even in low reviews: "the Techs that come to the house are great!" (2★); "There isn’t a way to split my review up showing office staff and actual service tech" (3★).

**Reading (inference):** the friction is status visibility over a weeks-long, multi-party funding and repair process. Numotion's own app advertises order-status notifications (S-106), so the gap concerns proactive updates and reaching a person. The app's existence is not proof that it works.

## 6. Cross-platform themes

These counts come from each location's **Lowest** sample, keyword-coded. The denominator is reviews at 3★ or below with text. LS = Commonwealth Louisville South; ET = Commonwealth Elizabethtown.

| Theme | LS (58) | ET (41) | Metro Vein (33) | FOH Naples (6) | Numotion (27) | AdaCare (5) |
|---|---|---|---|---|---|---|
| Reaching a person, callbacks | 10 | 4 | 1 | 3 | 3 | 0 |
| "AI" named explicitly | 4 | 2 | 0 | 0 | 0 | 0 |
| Robot, automated or offshore phone | 0 | 1 | 0 | 0 | 1 | 0 |
| Appointment changed or cancelled | 6 | 4 | 3 | 1 | 2 | 0 |
| Waiting in the office | 0 | 2 | 13 | 1 | 0 | 0 |
| Long lead time | 7 | 4 | 2 | 0 | 10 | 0 |
| Insurance or prior authorisation | 10 | 5 | 9 | 0 | 5 | 0 |
| Billing or charges | 9 | 3 | 3 | 2 | 1 | 3 |
| Front desk or attitude | 10 | 6 | 12 | 2 | 2 | 0 |
| Next step unclear or follow-up | 10 | 3 | 5 | 3 | 5 | 0 |
| Repeated forms, data not reused | 4 | 2 | 2 | 0 | 0 | 0 |
| Referral or records | 8 | 4 | 1 | 2 | 1 | 0 |
| Language or access | 0 | 1 | 2 | 0 | 0 | 0 |

**Pattern (inference):** praise goes to clinicians and in-person staff. Complaints cluster in the administrative layer between visits: reaching someone, schedule changes, authorisation status, repeated data entry and next steps. This is a hypothesis to test with each company, not a measured rate.

## 7. Patient status and journey stage of the cited complaints

Added 2026-10-15 (reconciliation pass) after re-reading the full text of each quoted or paraphrased complaint in the local raw extracts. **Many cited complaints concern established patients or an existing appointment, not first registration.** Each is labelled here so the later solution work does not count it as new-patient intake evidence. The patient status comes from what the review itself says; "unclear" means the text does not say. Nothing below is quoted beyond the excerpts already in §1–§5.

| Location · excerpt (section) | Patient status in the text | Journey stage it concerns | Use as onboarding evidence |
|---|---|---|---|
| CPS Louisville South · referred patient waited two weeks for a call (§1 item 1, paraphrased) | **New patient, referred** | Request/referral → first contact | Direct: new-patient ownership and follow-up |
| CPS Louisville South · "reached out multiple times via phone and the patient portal" (§1 item 1) | Established (uses the existing-patient portal) | Ongoing contact | Indirect: ownership of messages, not first registration |
| CPS Elizabethtown · "transferred to 5 different people just to reschedule" (§1 item 1) | Existing appointment; new vs established unclear | Rescheduling | Indirect: human route and ownership |
| CPS Louisville South · AI confirmation not found at check-in (§1 item 2) | Established (names their own clinicians) | Booking confirmation → arrival | Indirect for first visits: confirmation reliability |
| CPS · other "AI"/"robot" complaints (§1 item 2) | Unclear, or existing appointments (two concern changing or rescheduling) | Phone access, rescheduling, repeated link | Indirect: automation without a working human route |
| CPS Louisville South · "same questions over and over 4 times" (§1 item 3) | Unclear; the reviewer refers to "medical forms" | Forms | **Uncertain:** may be clinical forms, which can legitimately repeat |
| CPS Louisville South · early check-in link and insurance update not available at check-in (§1 item 3) | Established (insurance change on an existing appointment) | Pre-visit update → arrival | Direct for administrative carry-through, but for a returning visit |
| CPS Louisville South · "a med asst and NP me all the same questions again" (§1 item 3) | Appears to be a first visit; not stated | Arrival → consultation | **Uncertain:** the repeat questions came from clinical staff and may be clinical confirmation |
| CPS · prior approval not communicated; treatment not authorised on arrival (§1 item 4) | Established (procedures) | Authorisation between visits | Indirect: status visibility after onboarding |
| CPS Louisville South · "initial referral to first MD appt was over six weeks" (§1 item 4) | **New patient** (about 5 years ago) | Referral → first visit | Direct but old |
| CPS Louisville South · next injection unclear (§1 item 5) | Established | Between procedures | Indirect: next-step clarity in ongoing care |
| MVC Forest Hills · times changed or cancelled (§3) | Booked patients; one mentions an initial visit | Booking → arrival | Mixed: includes at least one initial visit |
| MVC Forest Hills · confirmations, address and instructions not received (§3) | Booked; did not attend; reports self-paying | Pre-first-visit logistics | Direct: logistics before a visit |
| MVC Forest Hills · told to call to schedule (§3, translation) | Prospective patient | Request → booking | Direct: booking route |
| FOH Naples · new-patient scheduling never returned calls (§4, paraphrased) | **New patient** (the reviewer says new-patient appointment) | Request → first contact | Direct |
| FOH Naples · transferred patient, four days to reach someone (§4) | New/transferred patient | Access after the first visit; the main complaint is results follow-up | Partly: access is administrative; results follow-up is clinical and out of scope |
| FOH Naples · "System to collect info was hard to fill out" (§4, 4★) | Unclear | Information collection | Direct but single and mild (4★) |
| Numotion Nashville · repair and funding delays (§5) | Established customers | Equipment service after delivery or during funding | Adjacent only: not first-visit onboarding |

**What this changes:** the direct new-patient evidence is narrower than the theme counts suggest. It is strongest for ownership of first contact (CPS, FOH), visit logistics (MVC) and authorisation/next-step visibility (CPS, mostly established patients). Repeated-question reports are partly about clinical staff and may describe necessary clinical confirmation. **Evidence that long registration forms cause abandonment is limited in this sample**; the brief states that hypothesis (S-1), and the reviews do not establish it.

## Revision notes (2026-10-15 completion pass)

- **Quotations.** Several first-version quotations had been tidied or contained inserted words. All quotations are now exact, with omissions marked "[…]". Health narratives that could identify someone are paraphrased without quotation marks.
- **AI count.** The first version said "seven reviews name it". Corrected: six name "AI" and one describes a "robot answering" system. Nothing here establishes a vendor or a technical cause.
- **Denominators.** The first version mixed Lowest and Newest samples without saying so. Each count now states its sample.
- **Listing name.** Google's "Shively" listing is the company's Louisville South office (same address, S-70).
- **Removed:** employee-rating claims and the use of AI Overview summaries.

## Revision notes (2026-10-15 reconciliation pass)

- **Added §7**, which labels each cited complaint by patient status and journey stage. No quotation, count or denominator changed.
- **Interpretation is owned elsewhere:** the pitfall synthesis is in [review pitfalls and solution opportunities](2026-10-15-review-pitfalls-and-solution-opportunities.md); candidate solutions are in the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md).
