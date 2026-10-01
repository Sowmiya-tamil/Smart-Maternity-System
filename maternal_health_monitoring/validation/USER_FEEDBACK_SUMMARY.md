# User / Stakeholder Validation Summary

**Project:** Remote Maternal Health Monitoring and Escalation System
**Phase:** 11 – User / Stakeholder Validation
**Date:** October 2026

---

> **Important Disclaimer**
>
> This validation is **simulated prototype stakeholder-style feedback**
> created for academic evaluation purposes only.
> It is **NOT clinical validation** and does **NOT** represent feedback from
> real patients or healthcare professionals.
> All stakeholder roles are anonymous and all feedback is simulated.
> This system has not been tested with or validated by real clinicians,
> community health workers, or pregnant patients.

---

## 1. Purpose

This document summarises the simulated stakeholder-style feedback collected
for Phase 11 of the Remote Maternal Health Monitoring and Escalation System.

The purpose of this validation exercise is to:

- Assess the clarity and usability of the system from a workflow perspective
- Identify the strongest and weakest aspects of the prototype design
- Document realistic improvement suggestions
- Demonstrate an awareness of user-centred design principles appropriate
  for an academic prototype

This validation is a **paper-based simulation** intended to practise the
process of stakeholder feedback collection in a research or academic setting.

---

## 2. Validation Approach

A simulated feedback dataset of **8 responses** was created to represent
four common stakeholder perspectives in a maternal health monitoring system.

Each simulated respondent was asked to evaluate the prototype system across
five criteria using a **1–5 scale** (1 = Poor, 5 = Excellent), and to provide
one positive observation and one improvement suggestion.

The feedback was designed to reflect realistic usability concerns, workflow
comprehension issues, and safety-related observations that would be raised
in a real prototype evaluation.

**Scoring Scale:**

| Score | Meaning |
|---|---|
| 5 | Excellent |
| 4 | Good |
| 3 | Acceptable |
| 2 | Needs Improvement |
| 1 | Poor |

---

## 3. Participant Roles

| Role | Responses |
|---|---|
| Community Health Worker | 2 |
| Clinician | 2 |
| Project Evaluator | 2 |
| Healthcare Workflow Reviewer | 2 |
| **Total** | **8** |

All roles are anonymous. No names, contact details, or personal identifiers
were used. These roles represent the typical audiences for a maternal health
monitoring system in a remote or low-resource setting.

---

## 4. Feedback Criteria

Each response was scored on five dimensions:

| Criterion | Description |
|---|---|
| **Workflow Clarity** | How clearly the overall system workflow is presented and understood |
| **Escalation Clarity** | How clearly the escalation pathways (LOW → CRITICAL → SAFE FALLBACK) are communicated |
| **Usability** | How easy the Streamlit dashboard is to navigate and understand |
| **Safety Fallback** | How well the safe fallback mechanism for incomplete/untrusted data is communicated |
| **Overall Score** | Overall impression of the prototype system |

---

## 5. Results

### 5.1 Average Scores

| Criterion | Average Score | Out of |
|---|---|---|
| Workflow Clarity | **4.12** | 5.00 |
| Escalation Clarity | **4.38** | 5.00 |
| Usability | **4.38** | 5.00 |
| Safety Fallback | **4.75** | 5.00 |
| **Overall Score** | **4.38** | 5.00 |

### 5.2 Strongest and Weakest Areas

| | Area | Score |
|---|---|---|
| **Strongest** | Safety Fallback | 4.75 / 5.00 |
| **Area for Improvement** | Workflow Clarity | 4.12 / 5.00 |

### 5.3 Score Distribution

| Criterion | Scores 4–5 (Positive) | Scores 1–3 (Needs Work) |
|---|---|---|
| Workflow Clarity | 7 / 8 | 1 / 8 |
| Escalation Clarity | 8 / 8 | 0 / 8 |
| Usability | 8 / 8 | 0 / 8 |
| Safety Fallback | 8 / 8 | 0 / 8 |

### 5.4 Average Overall Score by Role

| Role | Average Overall Score |
|---|---|
| Community Health Worker | 4.00 / 5.00 |
| Clinician | 4.50 / 5.00 |
| Project Evaluator | 4.50 / 5.00 |
| Healthcare Workflow Reviewer | 4.50 / 5.00 |

---

## 6. Positive Observations

The following themes were consistently praised across all stakeholder roles:

### 6.1 Safe Fallback Design
> *"The safe fallback message is very clear. I understood immediately that
> the system is asking me to repeat the measurement rather than ignoring
> the patient."* — Community Health Worker (FB002)

The safe fallback mechanism received the highest average score (4.75/5.00).
All 8 respondents gave it a score of 4 or 5. The key strength identified was
that the system **never silently classifies an incomplete record as LOW risk**,
which is a critical safety property.

### 6.2 Escalation Pathway Clarity
> *"The step-by-step escalation pathway is easy to follow. Knowing that
> offline cases are stored and not lost is very reassuring for field use."*
> — Community Health Worker (FB001)

Escalation clarity scored 4.38/5.00 with all 8 respondents scoring 4 or 5.
The five-pathway structure (Continue Monitoring → Schedule Follow-up →
Clinician Review → Urgent Clinician Review → Safe Fallback) was considered
well-structured and logically ordered.

### 6.3 Conflict Detection Logic
> *"The separation between HIGH sensor risk with no symptoms and CRITICAL
> cases where both signals agree is clinically logical. This helps avoid
> alert fatigue."* — Clinician (FB003)

The distinction between sensor-only concern and full CRITICAL escalation was
noted as a thoughtful design decision that reduces unnecessary alerts while
still ensuring high-risk cases are not missed.

### 6.4 Offline / Store-and-Forward Behaviour
> *"The store-and-forward simulation is a good demonstration of offline
> resilience."* — Project Evaluator (FB006)

Respondents recognised that handling offline connectivity is an important
real-world concern for remote maternal health monitoring, and appreciated
that this was addressed in the prototype design.

---

## 7. Improvement Areas

### 7.1 Workflow Clarity (Lowest Scoring — 4.12/5.00)

One respondent (FB008, Healthcare Workflow Reviewer) gave Workflow Clarity
a score of 3, with the suggestion:

> *"The workflow clarity could be improved by adding short explanatory
> tooltips next to each metric on the dashboard page."*

Other workflow clarity suggestions included:

- A one-page printed escalation pathway guide for community health workers
  without smartphones (FB001)
- A simple visual diagram of how each pipeline phase feeds into the next
  on the System Summary page (FB005)

### 7.2 Escalation Queue Urgency Indicators

> *"The escalation queue shows many queued cases. A visual indicator of
> how long a case has been queued would improve urgency tracking."*
> — Clinician (FB003)

In a production system, a time-in-queue indicator and a timestamp filter
on the escalation queue would be important operational improvements.

### 7.3 Patient Trend Visualisation

> *"The patient monitoring page could show a small trend chart of BP
> readings over time rather than only the latest value."*
> — Clinician (FB004)

This is a practical suggestion. The current prototype shows only the latest
observation for a selected patient. A simple line chart of systolic BP
across all observation days would better communicate the trend analysis
results already computed in Phase 5.

### 7.4 Conflict Resolution Status

> *"The conflict cases page could display a count of how many cases were
> resolved by clinician review versus how many remained open."*
> — Project Evaluator (FB006)

This would require linking escalation outcomes back to conflict cases,
which is a reasonable future enhancement.

---

## 8. Limitations

1. **Simulated feedback only** — all 8 responses are created to represent
   realistic perspectives, not collected from real stakeholders.

2. **Not clinical validation** — this exercise does not constitute medical
   device validation, clinical trial evaluation, or usability testing under
   any healthcare regulatory framework.

3. **Small sample size** — 8 responses are insufficient for statistical
   conclusions; a real validation study would require a much larger and
   more diverse sample.

4. **No real user interaction** — real usability testing would involve
   participants actually using the Streamlit dashboard, not just reading
   descriptions.

5. **Confirmation bias risk** — simulated feedback created by the same team
   that built the system cannot be free of confirmation bias.

6. **Role simulation** — the four stakeholder roles are representative
   archetypes, not profiles based on real stakeholder analysis.

---

## 9. Conclusion

The simulated stakeholder validation exercise suggests that the prototype
system design is considered **clear, usable, and appropriately safe** across
all four stakeholder perspectives.

**Key findings:**

- **Safety Fallback** is the strongest feature (4.75/5.00) — the system's
  commitment to never silently classifying incomplete data as low risk is
  well-recognised and valued.
- **Escalation Clarity** and **Usability** both scored 4.38/5.00, with no
  respondent giving either a score below 4.
- **Workflow Clarity** (4.12/5.00) is the most actionable area for
  improvement — specifically the lack of inline explanations and visual
  aids on the dashboard.
- The **overall average score of 4.38/5.00** indicates a well-received
  prototype design.

These findings inform the following concrete improvements for a future
iteration of the system:

1. Add inline explanatory tooltips to all dashboard metrics
2. Add a BP trend line chart on the Patient Monitoring page
3. Add a queue age indicator on the Escalation Queue page
4. Create a one-page printable escalation guide for offline field use
5. Improve the System Summary workflow diagram

---

## 10. Files

| File | Description |
|---|---|
| `validation/user_feedback.csv` | 8 simulated stakeholder feedback responses |
| `validation/run_validation.py` | Script that processes feedback and prints results |
| `validation/validation_results.csv` | Average scores per criterion (output) |
| `validation/validation_detailed.csv` | Full feedback with per-row average (output) |
| `validation/USER_FEEDBACK_SUMMARY.md` | This summary document |

---

## 11. How to Reproduce

```bash
# From the maternal_health_monitoring/ folder:
python validation/run_validation.py
```
