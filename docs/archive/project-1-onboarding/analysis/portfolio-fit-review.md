# Portfolio Fit Review — Which AEA Industry Fits the Onboarding Brief

**Owner of:**
- the comparison across industries;
- the selection criteria;
- the niche recommendation;
- the limitations of the comparison.

**Carried forward** from `Gauntlet AI/artifacts/2026-10-13-hiring-partner-project-choice-and-deadlines.md`
§0.1 (2026-10-14). That section stays as history; this file is now the project's working copy.
The firm and portfolio counts are owned by [AEA context](company-research/aea-investors.md). Each
company's evidence is owned by its profile.

**Status:** research recommendation. It is **not** an approved PRD and **not** a validated customer
need.

**2026-10-15 reassessment:** after the full five-platform comparison in the
[research report](2026-10-15-onboarding-research-report.md#anchor-reassessment-after-comparing-all-five),
the recommendation below stands. Commonwealth remains the anchor, AdaCare/ADC the second
configuration, Metro Vein the benchmark, FOH the long-packet example and Numotion adjacent. Updated
company facts are in the profiles; for example, Commonwealth now has 33 offices in 7 states.

---

## 1. The recommendation in one paragraph

Start with **administrative patient intake across multiple practices**, anchored on
**Commonwealth Pain & Spine**:

- **Second configuration:** an American Dental Companies affiliated practice.
- **Further core platforms:** Metro Vein Centers (reuse and benchmarking) and American Oncology
  Network (fourth core platform).
- **Adjacent opportunity:** Numotion.

Keep the product core general, because the brief targets general sensitive-service onboarding and
makes healthcare optional. Ground the research and examples in this niche.

The working concept:

> Help a prospective patient complete administrative intake, confirm information extracted from a
> document, understand missing requirements, and book an appropriate next step with less
> repetitive entry and uncertainty.

## 2. What the brief requires (why a niche choice is needed at all)

The [brief](../source/aea-proj1-onboarding-assistant.md) names its target industry as
"Sensitive-service onboarding".

- **Four core flows:**
  1. an LLM chatbot that does intake and an initial assessment;
  2. OCR of name, DOB and address, confirmed by the user;
  3. appointment booking that rejects double-booking;
  4. supportive content shown at friction points.
- **Regulation is conditional.** HIPAA applies only *if* the assumed domain is healthcare.
- **The brief does not choose an industry.** A demo needs one concrete service, so the choice is ours.

## 3. Coverage and method

1. **Screened all 118 profiles** linked from AEA's public portfolio directory, reading each one's
   investment group, status and business description.
2. **Narrowed to 56 current/active listings** (55 Current, 1 Active) by setting aside realized
   investments and the team's prior experience.
3. **Grouped the 56 into nine workflow groups.** The groups are ours, based on workflow, not AEA's
   industry taxonomy.
4. **Researched representative service flows** on company websites, especially for the plausible
   non-healthcare alternatives.

Each profile's URL, status and group are in the
[inventory](../evidence/2026-10-14-aea-portfolio-inventory.json).

| Workflow group | Listings |
|---|---|
| Patient-facing clinic and dental platforms | 4 |
| Complex rehabilitation and mobility | 1 |
| Veterinary practice platform | 1 |
| Recruitment and staffing | 3 |
| Home, property and facilities services | 8 |
| Logistics and transportation | 4 |
| Business technology and outsourced services | 6 |
| Consumer products, retail and hospitality | 7 |
| Industrial manufacturing, components and distribution | 22 |

## 4. Selection criteria, in priority order

1. **Natural fit with all four required flows.** The flows are conversational intake, document
   OCR, appointment booking and supportive help. Collecting name, DOB and address must serve a
   real purpose.
2. **Connection to the brief's business problem.** A person completes registration for a service
   and reaches the next step. A complicated back-office process alone is not enough.
3. **Reuse.** The same workflow and data meanings recur across current platforms and their
   locations, with realistic configuration changes.
4. **A coherent three-day demonstrator.** It must include the edge cases, and treat prerequisites
   and existing systems honestly.
5. **Evidence quality.** First-party descriptions and published intake steps count; missing public
   evidence stays unknown.

The rankings below are reasoned product-fit judgments. They are not measured ROI or market
statistics, and they do not confirm demand. Counting loosely related businesses heavily would
overstate reuse.

## 5. Comparison across the portfolio

| Group (current candidates) | Evidence and fit | Judgment |
|---|---|---|
| **Patient-facing care platforms:** Commonwealth Pain & Spine, Metro Vein Centers, American Dental Companies, American Oncology Network | Published registration steps, ID and document requirements, first visits and appointments form a common intake process. Patient uncertainty gives supportive content a concrete purpose. Evidence is in each profile. | **Strongest complete fit; four core platforms.** Privacy obligations and scheduling prerequisites add real work. |
| **Contract staffing:** NES Fircroft, RED Global; Bespoke Partners (adjacent executive search) | NES describes [assignment support](https://www.nesfircroft.com/talent-acquisition-services/contract-staffing/assignment-support/) covering mobility, work permits and contractor welfare. RED documents [identity and right-to-work checks and consultant onboarding](https://redglobal.com/anti-slavery). Bespoke's [executive search](https://www.bespokepartners.com/) is about candidate evaluation for client searches. | **Strongest non-healthcare alternative.** Two strong contractor-onboarding candidates; Bespoke's workflow means something different. Document collection is heaviest *after* placement, and the bottleneck is compliance and start-readiness, not first registration and booking. A scoped interview or document-review appointment could fit, but would need explicit justification. |
| **Home, property and facility services:** 50 Floor, Window Nation, Mark Spain Real Estate, BMS Enterprises, Polygon, Nations Roof, Pave America, SitelogIQ | [50 Floor](https://50floor.com/schedule-now/) and [Window Nation](https://www.windownation.com/) sell through consultations. [Mark Spain](https://markspain.com/blog/how-to-get-a-guaranteed-offer-on-your-home) collects property details before an agent consultation. [BMS CAT](https://www.bmscat.com/) handles urgent property damage. Restoration and commercial facilities differ from elective home improvement. | **A good sales-intake opportunity, but a weaker fit for the full brief.** Eight reachable businesses do not share one workflow. ID and DOB have no demonstrated need at the first consultation; collecting them only to justify OCR would add the friction we are trying to remove. Emergency restoration needs dispatch, not registration. |
| **Logistics:** Montway, American Expediting, Redwood Logistics, Scan Global Logistics | The profiles describe vehicle shipping, courier delivery, managed freight and forwarding. Montway's [vehicle preparation guide](https://www.montway.com/app/uploads/2024/07/prepare-vehicle-shipping-guide.pdf) documents inspection and bill-of-lading steps. | **Document automation fits; personal intake doesn't.** The core entities are shipments, vehicles and commercial accounts. A pickup window is not the brief's next-step appointment, and a person's DOB is not needed. |
| **Business technology and outsourced services:** Magna5, Trinamix, Huge, 829 Studios, ROI CX Solutions, AS Software | The profiles describe managed IT, enterprise software implementation, design, marketing, outsourced customer operations and clinical software. [Magna5's services](https://www.magna5.com/managed-it-services/) show the account- and system-level nature of the work. | **Potential for a different product.** Discovery calls and onboarding exist, but the documents and decisions concern organisations and systems. AS Software could be a channel or integration partner. That doesn't make it a patient-intake deployment. |
| **Veterinary practices:** AmeriVet | Its [practice directory](https://amerivet.com/partnership-locations) and [scheduling discussion](https://amerivet.com/blog/veterinary-appointment-scheduling?hs_amp=true) support reusable client-and-pet intake and appointments. | **A useful later adaptation, not a fifth patient platform.** Pet identity and medical records mean something different. The owner's ID and DOB are not shown to be needed for a first booking. Many practices still count as one AEA platform. |
| **Mobility and rehabilitation:** Numotion | Its [order process](https://www.numotion.com/order-process-and-timeline) runs from an evaluation appointment through medical documentation and funding approval to delivery. Detail is in the [profile](company-research/numotion.md). | **Strong adjacent fifth candidate.** Initial administrative intake reuses the core. The weeks-long equipment and funding workflow after it needs separate design. |
| **Consumer, retail and industrial:** 29 other current/active listings (7 consumer, 22 industrial) | Business descriptions cover consumer goods, hospitality, manufacturing, distribution and related services. Some involve organisational account setup or consultations. | **Low fit at the screening stage.** There is not enough evidence of a shared ID-to-appointment intake for a person. These internal workflows were not all investigated, so this is **not** proof that no onboarding opportunity exists. |

## 6. Why healthcare was recommended

Healthcare is the only group where the **complete combination** fits naturally:
- personal intake that depends on documents (photo ID, insurance, referral or forms);
- a real appointment as the next step;
- users who are often anxious or uncertain, which gives supportive content a purpose.

In this group, identity fields belong to the actual service process instead of being collected to
satisfy the OCR requirement. **Staffing** is the strongest alternative outside healthcare, but its
heaviest paperwork comes after placement, at the compliance and start-readiness stage.

## 7. The cohort and each company's role

| Company | AEA group | Role | Profile |
|---|---|---|---|
| Commonwealth Pain & Spine | Elevate | **Anchor.** Administrative intake and readiness for the next appointment; booking respects referral and coverage prerequisites. | [profile](company-research/commonwealth-pain-spine.md) |
| American Dental Companies | Elevate | **Second configuration.** Reuse within one platform: practice-specific fields, appointment types and help content. | [profile](company-research/american-dental-companies.md) |
| Metro Vein Centers | Elevate | **Reuse and benchmarking candidate.** It already runs a HubSpot-connected chatbot; not pitched as its first chatbot. | [profile](company-research/metro-vein-centers.md) |
| American Oncology Network | Elevate | **Fourth core platform.** Administrative intake fits; urgency and referrals add complexity. | [profile](company-research/american-oncology-network.md) |
| Numotion | Middle Market | **Adjacent fifth opportunity.** Initial intake reuses the core; the equipment and funding process needs separate design. | [profile](company-research/numotion.md) |

**Count: four directly relevant platforms plus one adjacent opportunity.** Practices and branches
can multiply reach within a platform. They are not separate AEA investments, and no shared
procurement or integration has been established.

## 8. Proposed reuse boundary (a hypothesis for the PRD, not a decision)

- **Reuse across configurations:**
  - consent and progress tracking;
  - the conversation and state flow;
  - OCR of synthetic documents with editable fields;
  - manual fallback;
  - slot availability and conflict handling;
  - supportive-content triggers;
  - staff hand-off;
  - deletion;
  - funnel events that carry no identifying data.
- **Configure per organisation:**
  - required fields;
  - permitted documents;
  - appointment types;
  - prerequisites;
  - reviewed help content.
- **Not portable by configuration alone:**
  - real scheduling and EHR integrations;
  - each organisation's policies.
- **The demo boundary:**
  - administrative intake only, with synthetic records and synthetic slots;
  - a completed intake summary is not a diagnosis, an urgency decision, an insurance approval or
    permission to bypass a referral;
  - missing prerequisites must not block access to help.

**Success hypothesis.** The product would raise the share of eligible new inquiries that finish
intake and book the appropriate next step, and reduce repeated entry and staff follow-up.

- **The demo can measure:** intake completion, corrections, time to complete and hand-offs caused
  by missing prerequisites.
- **Unvalidated:** production conversion, staff time saved, effect on no-shows and ROI.
- **Existing forms, portals and chatbots** are systems to investigate and possibly complement.
  Their existence is not evidence of failure.
- **Three baselines stay separate:** reference practice (guidance), company current-state evidence
  (published or reported), and measured performance (unknown for every company). A synthetic
  demonstration cannot establish real company revenue or completion improvement. Candidate
  solutions and their evidence are in the
  [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md).

## 9. Limitations

- **The directory is incomplete as evidence.** It may be stale, and "Current" may include minority
  or retained stakes.
- **No proprietary data was reviewed:** no funnel, ROI, procurement or integration data.
- **The evidence is published pages, not practice.** It shows what companies publish, not how
  intake actually runs, where it fails, or what tools staff use internally.
- **Variation within platforms is under-sampled.** One practice page each was read for ADC and AON.
- **Rankings are our judgment** against the criteria above, made by one reviewer in one day.
- **Existing digital tools were found at every platform.** The first two (2026-10-14) were
  Commonwealth's third-party request form and Metro Vein's chatbot. By 2026-10-15 the list also
  included Commonwealth's virtual agent and portal, AdaCare's group scheduler (which shows New
  Patient Visit slots before personal details, S-83), FOH's CareSpace portal and Numotion's app
  (documented capability, S-106). They do different jobs: contact capture, scheduling,
  administrative onboarding or ongoing coordination
  ([journey baseline](2026-10-15-patient-journeys-and-onboarding-baseline.md#what-a-published-tool-can-and-cannot-establish)).
  Their presence shows neither complete digital onboarding nor failure. The product may
  complement them rather than fill a gap.
- **Several answers could change the anchor or the implementation even though the niche holds:**
  - which fields are mandatory before which appointment;
  - who checks referral and coverage;
  - what may be self-booked;
  - where abandonment happens;
  - whether current software already closes the gap;
  - which system accepts a completed intake.

  These are tracked in [research questions](research-questions.md) as RQ-2, RQ-6–RQ-8, RQ-13,
  RQ-25 and RQ-28.
