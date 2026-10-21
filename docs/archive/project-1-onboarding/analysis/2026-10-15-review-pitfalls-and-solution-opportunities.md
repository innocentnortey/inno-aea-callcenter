# Review patterns and onboarding solution opportunities

**Date:** 2026-10-15 · **Status:** research interpretation, not selected scope or demonstrated product impact.

The collected reviews align most strongly with five onboarding pitfalls: unreturned calls and unclear ownership; uncertainty about status and next steps; repeated administrative entry; scheduling changes and missing instructions; and automation without an effective recovery or human route. They give us useful problems to investigate and design around, although they do not establish frequency, technical cause or network-wide conditions. Several concern established patients rather than first registration ([review report §7](2026-10-15-google-review-sentiment.md#7-patient-status-and-journey-stage-of-the-cited-complaints)).

The business hypothesis is that a clearer administrative process can reduce preventable restarts, delays and staff work while helping patients reach appointments. The reviews do not establish a company revenue baseline or prove that a proposed capability will improve it.

## Evidence and baseline

- [Google review evidence](2026-10-15-google-review-sentiment.md) owns the sample definitions, exact excerpts, dates and approximate theme counts. Its sources are S-77, S-84, S-91, S-100 and S-107 in the [source register](../source/source-register.md).
- [Patient journeys and standard onboarding practices](2026-10-15-patient-journeys-and-onboarding-baseline.md) owns the general journey and candidate evaluation baseline, supported by S-108 to S-121. Professional guidance describes recommended practice, not a measured company defect.
- [Company profiles](company-research/) own published company facts and AEA listing context.
- The [research report](2026-10-15-onboarding-research-report.md) and [configuration annex](2026-10-15-configuration-specification.md) contain related candidate capabilities. They remain proposals until selected and demonstrated.

## How reported problems align with the baseline

All rows below are interpretations of attributed reports. The capability and benefit columns are hypotheses. A source link identifies the supporting passage without reproducing a reviewer's name or health narrative.

| Pitfall | What reviewers reported and where | Baseline expectation | Possible response | What would need to be proved |
|---|---|---|---|---|
| Nobody clearly owns the next action | Unreturned calls at Commonwealth's Louisville South and Elizabethtown offices and FOH Naples; one prospective FOH patient reported going elsewhere after unsuccessful scheduling attempts. Review report §1 and §4; S-77, S-100 | A request or referral has a clear owner and follow-up process. AHRQ referral guidance, S-114 | Acknowledgement, a staff queue and a clear human contact | Requests actually reach an authorised owner; staff can track and act on them; a queue alone does not create staffing capacity |
| Patients cannot see what is happening | Uncertainty about referrals and authorisations at Commonwealth, and funding/repairs at Numotion's Nashville-area branch. Review report §1 and §5; S-77, S-107 | Explain the next step and responsibilities. General journey and referral guidance, S-114 | Show the current step, outstanding item and who handles it | Status comes from a reliable source and stays current; manually simulated status is labelled; equipment tracking remains a separate scope |
| Submitted information does not carry through | Commonwealth patients reported repeated questions or submitted insurance updates being unavailable at check-in. Review report §1 item 3; S-77 | Collect needed administrative information once and share it with appropriate staff. AHRQ form guidance, S-112 | Reuse confirmed administrative information and include it in a staff summary | Staff can use the summary without re-entering it; correction is supported; clinical re-confirmation is preserved |
| Scheduling expectations break down | Forest Hills reviewers reported changed times and missing directions; a Commonwealth reviewer reported a confirmation that could not be found at arrival. Review report §3 and §1 item 2; S-91, S-77 | Clear appointment logistics and confirmed next steps; company-published policies. S-108 and company profiles | Reliable confirmation, visit details and explicit change notifications | Confirmation reflects a durable authorised booking; changes reach the patient; double-booking is rejected in the demo |
| Automation becomes another obstacle | Commonwealth complaints describe repeated links, difficulty rescheduling and difficulty reaching a person. Review report §1 item 2; S-77 | Errors and incomplete work have a recovery route; progress and next steps remain understandable. W3C guidance, S-115, S-116 | A recovery route that preserves context when staff take over | The patient can reach the stated route; already supplied information survives; the system does not claim a human has responded before that happens |

## What the positive reviews teach us

AdaCare patients praise reminder calls, pre-appointment check-ins and help with insurance and payment arrangements (review report §2; S-84). These are examples of existing strengths. They support asking how software could preserve those behaviours or make them consistent where needed; they do not establish a deficiency at AdaCare or elsewhere in ADC.

Commonwealth patients praise listening and explanations (review report §1; S-77). Numotion reviewers praise technicians even while criticising coordination (review report §5; S-107). Together, these reports suggest preserving personal attention and clarity when adding automation. A software feature should help the people doing this work, rather than assume they can be removed from it.

## What the reviews support less directly

- **Long-form abandonment:** relatively little direct evidence here that a long registration form caused abandonment. This remains a hypothesis supported by the issued brief and broader guidance, rather than a measured finding at these locations.
- **Repeated questions:** they do not automatically prove wasted work. Clinical confirmation can be necessary; administrative retyping and clinical reconciliation are different activities. Of the Commonwealth reports, one refers to "medical forms" and one to questions asked again by clinical staff; the clearest administrative case is an insurance update not available at check-in (review report §7).
- **Office waiting and staff capacity:** an intake assistant cannot alone resolve overbooking, staffing shortages, payer decisions, appointment capacity or treatment delays. The cause of a reported wait is not established by its duration.
- **Treatment outcomes:** medication decisions, procedure outcomes and clinical result interpretation fall outside administrative intake.
- **Equipment repair:** months-long repair/funding complaints are useful adjacent context, but they do not validate a first-visit onboarding feature or prove a particular repair delay is avoidable.
- **Ongoing care:** several reports concern established patients. First registration, rescheduling and later coordination need separate evidence labels rather than being grouped as one intake failure.
- **Vendor fault:** the Commonwealth reports do not establish which tools were involved or their technical cause. The existence of a portal, assistant or app establishes neither failure nor successful handoff.

## The strongest product opportunity to investigate

The opportunity is to make administrative intake feel like a process someone is actively managing. Easier data entry contributes, but patients also need answers to four questions:

1. Was my information received?
2. What is missing?
3. Who handles the next action?
4. What happens next?

A useful synthetic demonstration is a patient completing the administrative intake while a prerequisite remains outstanding. Both patient and staff can see the next action. The demonstration could then evaluate uncertainty, repeated entry and follow-up work. It must not imply that an appointment request, received document or insurance card is itself a confirmed booking, a reviewed referral or approved coverage.

The published listing ratings are high, and the samples deliberately include low-rated reviews. Treat the complaints as specific reported problems that inspire scenarios, not evidence that the companies' onboarding generally fails. Evidence concerns the sampled locations, not whole networks.

## Traceability for selecting solutions and explaining the project

For each future candidate, preserve this chain:

**AEA platform and specific practice or branch → journey stage → baseline expectation → reported or published issue → proposed capability → mechanism of improvement → demonstration/test → measured outcome.**

Keep three meanings of baseline distinct:

- **Reference baseline:** what guidance says a good process should support.
- **Company current state:** what its pages publish or a reviewer reports, with scope and date.
- **Measured starting point:** actual completion, time, error or revenue data. Where unavailable, record unknown; a simulated comparison is not company performance data.

An interview claim should grow with the evidence. At research stage, it is defensible to say that a public report inspired a capability intended to address a particular failure mode. After implementation, describe only the behaviour built and demonstrated. Claim a measured company improvement only when company-level measurement exists.

For portfolio relevance, use the company profiles and their AEA source IDs, counting platforms rather than practices. An AEA Current listing is public context; it does not establish ownership control, procurement access, a deployment agreement or a customer endorsement.

The ranked candidate inventory and shortlist are now in the [solution selection matrix](2026-10-15-solution-selection-and-evidence-matrix.md) (2026-10-15), which owns candidate IDs, ranks and Innocent's selection record. No candidate in this document is selected, implemented or proven effective merely because it appears here. Mandatory brief capabilities remain required regardless of that later selection.
