# Healthcare Company Website Analysis — Onboarding Product Research

## Role

Act as a multidisciplinary team consisting of:

- A healthcare CEO experienced in patient acquisition, intake operations, care delivery, and revenue management.
- A healthcare operations consultant specializing in patient onboarding and administrative workflows.
- A UX researcher specializing in patient experience, behavioral psychology, accessibility, and reducing friction.
- A software product architect designing configurable onboarding software for healthcare organizations.
- A healthcare growth strategist experienced in retention, patient conversion, and identifying unmet patient needs.

Your objective is to analyze the healthcare company website(s) provided earlier in this conversation and produce a comprehensive, evidence-based research report that I can use to configure and demonstrate my patient onboarding software.

**Important context:** I am building general-purpose healthcare onboarding software that can be configured for different healthcare organizations.

I am not building a custom application from scratch for each organization.

My goal is to extract the company-specific information, operational requirements, patient journeys, and service details necessary to configure my existing software for that company's business.

For demonstration purposes, the software will use fictional patients and simulated workflows. The company information should be grounded in publicly verifiable information wherever possible.

I also need to understand how the company currently handles and presents its patient onboarding experience, what appears to be missing, and how my product could create additional value.

---

## Part 1 — Company Intelligence

Investigate the company's website, including its homepage, About pages, service descriptions, provider directories, locations, patient resources, FAQs, pricing, insurance information, contact pages, and publicly accessible intake and scheduling pages.

Determine:

### A. Business profile

- Company name, business model, and type of healthcare organization.
- Medical specialties and services offered.
- Target patient populations.
- Geographic service areas and locations.
- Whether services are in person, virtual, at home, or a combination.
- Whether the business primarily provides one-time procedures, recurring care, longitudinal care, or multiple models.
- Any special eligibility criteria for receiving services.

### B. Services and care pathways

For each major service, determine:

- What patient problem the service addresses.
- Who the intended patient is.
- Which type of healthcare professional delivers the service.
- Any publicly stated eligibility requirements.
- Any prerequisites, referrals, or supporting documentation.
- What the patient's likely journey looks like from initial inquiry through care delivery and follow-up.
- Whether the service naturally involves recurring appointments, follow-up visits, complementary services, or long-term care.

Identify relationships between services, but do not assume that one service is clinically indicated simply because a patient seeks another.

### C. Provider and resource availability

Identify:

- Provider names, credentials, and specialties where published.
- Which locations offer which services.
- How patients are matched to providers.
- Whether patients can select their preferred provider.
- Whether actual appointment availability is visible.
- Whether referrals or prior authorizations are required.
- Any publicly stated wait times or response-time commitments.

Do not invent provider availability, appointment slots, credentials, or clinical capabilities.

### D. Financial and insurance information

Determine:

- Insurance plans accepted, where explicitly stated.
- Self-pay or cash-pay options.
- Published consultation fees, procedure prices, or payment plans.
- Insurance verification requirements.
- Information provided about expected costs.
- Any financial assistance or billing support options.

Identify financial information patients would need during onboarding but that cannot be established from the public website.

**Deliverable:** A structured company profile containing the information my software would need to represent this organization accurately.

---

## Part 2 — Company's Positioning and Patient Expectations

Analyze how the company portrays itself to prospective patients.

Identify its primary value propositions and differentiators.

Examples include:

- Faster access to care.
- Highly qualified specialists.
- Compassionate or personalized care.
- Affordable treatment.
- Convenient scheduling.
- Advanced technology.
- Comprehensive or coordinated care.
- Better patient outcomes.

For each major claim:

1. Explain what the company promises or communicates.
2. Identify the website evidence supporting it.
3. Explain what a patient would reasonably expect because of that claim.
4. Determine whether the publicly visible onboarding experience reinforces that expectation.
5. Identify opportunities for my onboarding product to help the company deliver on its positioning.

Distinguish explicit company claims from your interpretation of its marketing.

**Key question:** What experience is the company teaching customers to expect, and how could onboarding reinforce that promise?

---

## Part 3 — Reconstruct the Existing Patient Onboarding Journey

Act as a prospective patient investigating how to receive care.

Trace the publicly visible journey from discovering the company to becoming ready for the first appointment.

Investigate:

1. How the patient determines whether the company treats their particular condition or concern.
2. How they find the appropriate provider or service.
3. How they request care or schedule an appointment.
4. What personal, medical, insurance, and administrative information is requested.
5. What online forms, portals, third-party scheduling tools, or contact methods are available.
6. Whether the company communicates expected response times.
7. How patients receive appointment confirmation and preparation instructions.
8. How patients are informed of what happens next.
9. How patients can contact the organization with questions.
10. What information is provided about follow-up care.

For each stage, document:

- The patient's objective.
- What the website currently offers.
- Any visible steps or requirements.
- The likely source of friction.
- What remains unclear or unverified.
- The potential consequence for the patient or organization.

Inspect publicly accessible interactions where feasible, but do not submit actual appointments, patient information, medical forms, or inquiries.

Do not assume an internal workflow does not exist just because it is not displayed on the public website.

**Deliverable:** A current-state onboarding journey map.

---

## Part 4 — Identify Distinct Patient Friction Points

Evaluate the experience using these eight categories:

| Category | Primary question |
|---|---|
| Urgency and responsiveness | How quickly can someone help me? |
| Qualified provider access | Does this organization have the right professional for my problem? |
| Intake speed and simplicity | How much work must I do before receiving care? |
| Journey transparency | What will happen between now and my desired outcome? |
| Communication and visibility | How will I stay informed? |
| Financial certainty | What will this cost, and what will insurance cover? |
| Trust and psychological safety | Can I safely share my personal concerns and information? |
| Confidence in being understood | Will the company understand my needs without making me repeat myself? |

For every category:

- Determine what the company currently offers publicly.
- Identify observed friction or missing public information.
- Explain why that friction matters to patients.
- Describe how onboarding software could address it.
- Identify the potential operational or financial consequences.
- Recommend measurable indicators of improvement.

Avoid repeating essentially identical friction points under different categories.

Consider the patient's emotional state. Patients may be anxious, embarrassed, physically uncomfortable, financially stressed, uncertain, or concerned about their health.

Evaluate whether the visible onboarding experience could intensify those feelings and suggest how thoughtful communication, transparency, accessibility, and control could reduce unnecessary stress.

---

## Part 5 — Identify Clinically Appropriate Service Opportunities

One goal of my onboarding product is to collect useful information that helps a qualified healthcare professional recognize additional patient needs.

This is not an automated medical upselling engine.

The software should identify potentially relevant information for professional review. The healthcare professional independently determines medical necessity and whether to recommend additional care.

Analyze the company's service catalog and identify opportunities where broader patient context could help clinicians recognize:

- Relevant complementary services.
- Preventive care needs.
- Follow-up care opportunities.
- Chronic condition management needs.
- Rehabilitation or supportive care needs.
- Care coordination requirements.
- Unaddressed patient goals or barriers to receiving treatment.

For each opportunity, provide:

1. The primary service the patient initially seeks.
2. The additional patient information that may be relevant.
3. A short, patient-friendly intake question that could capture that information.
4. What the patient's answer would reveal.
5. What the clinician might need to assess further.
6. Which other service offered by the company may be relevant, if any.
7. Why the information could improve patient care.
8. How it might create legitimate additional revenue if an appropriate service is subsequently recommended and accepted.

Do not recommend unnecessary testing, procedures, appointments, or treatments to increase revenue.

**Prioritize questions that collect high-value information with minimal effort for the patient.**

---

## Part 6 — Translate the Research Into Software Configuration

This is one of the most important parts of the research.

I need to know exactly how to configure my general onboarding software for this organization.

Create a structured configuration specification covering:

### Company configuration

- Organization identity and branding.
- Patient-facing language and tone.
- Locations and operating hours.
- Services and service descriptions.
- Available specialties and providers.
- Contact and communication channels.
- Accepted insurance and published payment options.
- Relevant patient resources.

### Patient intake configuration

- Required basic patient information.
- Reason for seeking care.
- Desired outcome or patient goals.
- Service selection.
- Provider or location preferences.
- Scheduling preferences.
- Relevant medical-history questions.
- Insurance and payment information.
- Existing treatment or referral information.
- Optional concerns, accessibility needs, or communication preferences.

Separate information needed for initial contact from information better collected later during previsit preparation.

Use conditional questions so patients only receive questions relevant to their situation.

### Workflow configuration

Describe the steps the software would need to represent, including:

- Initial patient request.
- Acknowledgment.
- Clinician-approved urgency screening or escalation.
- Appropriate service or provider routing.
- Scheduling or appointment requests.
- Previsit intake.
- Documentation collection.
- Preparation instructions.
- Status updates.
- Staff handoffs.
- Clinician review of additional patient needs.
- Follow-up coordination.

Distinguish company-specific configuration from reusable functionality that should exist in the core product.

### Communication configuration

Suggest company-appropriate example messages for:

- Request received.
- Missing information.
- Appointment confirmation.
- Preparation instructions.
- Scheduling delays.
- Status updates.
- Follow-up reminders.

Never promise an appointment, response time, service, or outcome that the company has not confirmed.

### Integration requirements

Identify publicly visible patient portals, electronic health record platforms, scheduling systems, payment tools, and contact platforms, if discoverable.

Do not assume technical integrations or API access merely because a vendor or portal is visible.

Mark unknown integration details as requiring company confirmation.

**Deliverable:** A configuration table with fields for configuration item, recommended value, source, confidence, and information still needed.

---

## Part 7 — Gap Analysis and Business Opportunities

Compare the company's publicly visible current state with a proposed onboarding experience using my software.

For every meaningful gap, explain:

- **Current state:** What the company appears to be doing today.
- **Evidence:** What supports that assessment.
- **Gap:** What is missing, unclear, manual, or potentially inefficient.
- **Proposed product capability:** What my software would add or change.
- **Patient value:** Why the patient benefits.
- **Operational value:** What work is reduced or made more reliable.
- **Business value:** Whether the opportunity affects conversion, retention, revenue realization, clinician utilization, appropriate service expansion, or administrative costs.
- **Measurement:** What KPIs would validate the impact.

Prioritize opportunities by likely impact, confidence in the evidence, and implementation complexity.

For example, if patients must call to request an appointment and no digital request workflow is publicly visible, explain how a digital intake-and-request experience could reduce friction.

However, do not claim the company lacks digital scheduling if it might exist behind a patient portal or another unexamined system.

Use these evidence classifications consistently:

- **Verified:** Directly supported by accessible website evidence.
- **Not publicly established:** Could not be confirmed from the website.
- **Inferred:** A reasonable hypothesis that requires validation.
- **Proposed:** A new capability or workflow I could implement.

Do not confuse the absence of public evidence with proof that a company is not already performing a function.

---

## Part 8 — Revenue and ROI Hypotheses

For each proposed improvement, identify the business mechanism through which it might create value.

Potential mechanisms include:

- More inquiries becoming scheduled appointments.
- Fewer patients abandoning intake.
- Fewer cancellations and no-shows.
- Shorter time between inquiry and appropriate care.
- Reduced administrative labor per patient.
- Fewer incomplete appointments caused by missing paperwork.
- Improved repeat engagement and appropriate follow-up.
- Better recognition of medically justified additional services.
- Increased patient satisfaction and referrals.

Separate direct revenue opportunities from cost savings.

Explain the chain of cause and effect rather than simply claiming that improving onboarding increases revenue.

Identify which baseline metrics would need to be obtained from the company before making a credible quantitative ROI claim.

When actual data is unavailable, provide illustrative calculations with clearly stated assumptions, not invented business results.

---

## Part 9 — Demo Blueprint Using Fictional Patients

Using what you learned about the organization, design a realistic software demonstration.

Provide:

### A. Fictional patient scenarios

Create three distinct fictional patient scenarios tailored to the company's actual service offerings:

1. A straightforward patient needing a common service.
2. A patient with additional concerns or obstacles requiring a more personalized onboarding experience.
3. A patient whose intake reveals other potentially relevant care needs requiring professional review.

All patient identities, histories, and responses must be fictional and explicitly labeled as simulated.

### B. Patient-facing demonstration

Show:

- How the patient begins intake.
- Which questions appear.
- How answers determine subsequent nonclinical questions.
- How the patient receives information about the care process.
- How uncertainty is reduced.
- How the journey proceeds toward scheduling and clinical review.

### C. Staff and clinician demonstration

Show:

- The intake summary staff receive.
- Missing administrative information.
- Scheduling or coordination actions.
- Patient goals and concerns.
- Information flagged for clinician review.
- Potentially relevant services requiring independent clinical assessment.

### D. Before-and-after demonstration

Present the publicly observed process alongside the proposed software-enabled process.

Identify exactly which product capabilities create the difference.

Distinguish real findings from simulated improvements.

---

## Part 10 — Remaining Questions for the Healthcare Company

Identify information the public website cannot reliably establish but that I would need before implementing a production onboarding system.

Prioritize questions about:

- Internal intake workflows.
- Patient volumes and abandonment rates.
- Scheduling and staff responsibilities.
- Patient eligibility and referral rules.
- Clinical escalation and review policies.
- System integrations and access.
- Insurance verification.
- Consent and privacy requirements.
- Patient communication policies.
- Appointment completion and follow-up processes.

Separate essential implementation questions from optional optimization questions.

For demo configuration, recommend reasonable placeholders for unknown information and label them clearly. Do not present placeholders as company facts.

---

## Research Standards

1. Use the referenced websites as the primary sources of evidence.
2. Review relevant accessible subpages, linked patient resources, and public scheduling experiences.
3. Cite supporting page URLs for meaningful findings.
4. Include the date of the website assessment.
5. Avoid unsupported assumptions about hidden internal processes.
6. Do not fabricate patient volumes, conversion rates, revenue, provider availability, insurance coverage, or integration capabilities.
7. Keep clinical decision-making with qualified healthcare professionals.
8. Do not use fictional patient data as though it were real.
9. Consider HIPAA, privacy, consent, accessibility, and other applicable compliance requirements as items requiring proper implementation review, not as automatic guarantees of compliance.
10. Where a recommendation is based on UX or healthcare research rather than website evidence, distinguish it and provide a credible source when possible.
11. Avoid generic consulting advice. Tailor every major finding to the specific organization and its actual services.
12. Prioritize practical information I can use to configure and demonstrate working software.

## Required Final Report Format

Produce the final report in the following order:

1. **Executive Summary** — Key findings, highest-value opportunities, and strongest demo angle.
2. **Company Intelligence Profile** — Everything learned about the company.
3. **Service Catalog and Patient Pathways** — Services, providers, requirements, and relationships.
4. **Company Positioning and Promises** — How the company portrays itself and what patients are led to expect.
5. **Current Onboarding Journey** — How the visible process works today.
6. **Patient Friction Assessment** — Distinct patient problems and supporting evidence.
7. **Additional Care Opportunity Matrix** — Information intake could surface for clinician review.
8. **Software Configuration Specification** — Exact company-specific configuration needed for my general onboarding product.
9. **Gap and Business Impact Matrix** — Current state versus proposed improvement, with measurable business hypotheses.
10. **Fictional Patient Demo Blueprint** — Three scenarios and their patient/staff experiences.
11. **Unknowns and Company Discovery Questions** — Information requiring confirmation.
12. **Prioritized Product Recommendations** — Must-have demo capabilities, high-value enhancements, and longer-term functionality.

Finish with a concise section titled:

**"What I Need to Configure This Company in My Onboarding Software"**

This should be an implementation-ready checklist divided into:

- Information verified and ready to use.
- Information that can be simulated for the demo.
- Information that requires company confirmation.
- Reusable product capabilities versus company-specific configuration.

The result should make it possible for me to take a general healthcare onboarding application, configure it for this specific healthcare organization, demonstrate realistic patient journeys, and clearly explain the potential business value of the improvements.
