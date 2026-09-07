# PROJECT PLAN — Remote Maternal Health Monitoring and Escalation System

This document describes the complete development roadmap for the project and its current status.

The project is a **student-level prototype** built for educational purposes using **simulated data only**.
It is NOT a medical diagnostic system.

Last updated: September 2026

---

## Phase 1 — Project Foundation ✅ COMPLETE

**Goal:** Set up the project structure, create documentation, and build a placeholder Streamlit app.

**Files created:**
- `app.py` (placeholder, later replaced in Phase 8)
- `requirements.txt`
- `README.md`
- `docs/PROJECT_PLAN.md`
- `docs/DATA_PRIVACY.md`

**Outcome:** Working placeholder application with project title, description, and planned phase list displayed.

---

## Phase 2 — Simulated Dataset Generation ✅ COMPLETE

**Goal:** Generate realistic but completely fake patient health data using Python.

**Files created:**
- `generate_data.py`
- `data/simulated_maternal_data.csv`

**What was implemented:**
- 100 anonymous patients (P001–P100), 5–15 observation days each (~1 000 rows total)
- Simulated fields: systolic/diastolic BP, heart rate, temperature, SpO2, pregnancy week, observation day, six patient-reported symptoms, internet status, communication status
- Deliberately introduced noise and missing values to simulate real-world data quality issues
- No real patient data was used at any point

---

## Phase 3 — Data Cleaning and Validation ✅ COMPLETE

**Goal:** Validate sensor readings and assign data quality labels.

**Files created:**
- `clean_data.py`
- `data/cleaned_maternal_data.csv`

**What was implemented:**
- Sensor range validation for all five sensor fields
- Records labelled: **Good**, **Incomplete** (missing values), **Invalid** (out of range)
- Cleaning report printed to console
- Original raw dataset left unchanged

**Results:** 994 rows processed — 818 Good, 151 Incomplete, 25 Invalid

---

## Phase 4 — Baseline Risk Detection ✅ COMPLETE

**Goal:** Apply simple rule-based logic to assign a risk level to every observation.

**Files created:**
- `risk_detection.py`
- `data/baseline_risk_results.csv`

**What was implemented:**
- Five risk levels: LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN
- Rules based on systolic BP, diastolic BP, heart rate, temperature, SpO2
- High-priority symptoms (bleeding, reduced fetal movement, headache+blurred vision) can elevate risk
- UNCERTAIN assigned automatically to all Incomplete/Invalid records (safe fallback)
- Human-readable `risk_reason` and `recommended_action` columns added

**Results:** LOW 420, MEDIUM 131, HIGH 205, CRITICAL 62, UNCERTAIN 176

---

## Phase 5 — Trend Analysis ✅ COMPLETE

**Goal:** Track per-patient systolic BP trends across multiple observation days.

**Files created:**
- `trend_analysis.py`
- `data/trend_results.csv`

**What was implemented:**
- Per-patient grouping sorted by `observation_day`
- Recent trend (last two valid readings): Increasing / Decreasing / Stable / Not Enough Data
- Overall trend (3+ readings): Consistently Increasing / Consistently Decreasing / Stable/Variable
- NaN values skipped — only valid readings used
- Prototype threshold: ±5 mmHg (demonstration only, not a medical guideline)

**Results:** 100 patients analysed — Increasing 18, Decreasing 11, Stable 71, Not Enough Data 0

---

## Phase 6 — Sensor-Symptom Conflict Detection ✅ COMPLETE

**Goal:** Identify cases where sensor risk and patient-reported symptoms disagree.

**Files created:**
- `conflict_detection.py`
- `data/conflict_results.csv`
- `data/demo_conflict_cases.csv` (6 hand-crafted edge cases)

**What was implemented:**
- Four conflict statuses: NO CONFLICT / SENSOR-SYMPTOM CONFLICT / SENSOR-ONLY CONCERN / INSUFFICIENT DATA
- Core safety rule: a low sensor reading never overrides a concerning symptom report
- Trend note attached to every conflict reason
- Six demonstration cases (DEMO001–DEMO006) covering every conflict category

**Results:** NO CONFLICT 692, SENSOR-ONLY CONCERN 126, INSUFFICIENT DATA 176, SENSOR-SYMPTOM CONFLICT 0 (in main dataset — demonstrated via DEMO001/DEMO006)

---

## Phase 7 — Escalation Workflow, Capacity and Safe Fallback ✅ COMPLETE

**Goal:** Route every case through a priority-based escalation pathway with capacity handling and offline support.

**Files created:**
- `escalation_workflow.py`
- `data/escalation_results.csv`

**What was implemented:**
- Five priority levels: LOW / MEDIUM / HIGH / CRITICAL / UNTRUSTED
- Five escalation pathways: CONTINUE_MONITORING / SCHEDULE_FOLLOW_UP / CLINICIAN_REVIEW / URGENT_CLINICIAN_REVIEW / SAFE_FALLBACK
- **Safe fallback:** UNCERTAIN/incomplete data → UNTRUSTED → SAFE_FALLBACK (never classified as LOW)
- **Store-and-forward:** Offline escalation cases → STORED (not discarded)
- **Clinician capacity:** First 10 HIGH/CRITICAL = WITHIN_CAPACITY; remainder = QUEUED / QUEUED_NEXT_SLOT
- Simulated communication (no real APIs): FIRST_ATTEMPT / STORED_FOR_FORWARD / NOT_REQUIRED

**Results (994 records):** LOW 420, MEDIUM 131, HIGH 126, CRITICAL 141, UNTRUSTED 176 | Stored for Forward: 94 | Queued: 257

---

## Phase 8 — Streamlit Application ✅ COMPLETE

**Goal:** Build a working five-page interactive prototype in Streamlit.

**Files modified:**
- `app.py` (fully replaced Phase 1 placeholder)

**Pages implemented:**

| Page | Description |
|------|-------------|
| Dashboard | Priority metrics, workflow status metrics, 2 bar charts |
| Patient Assessment | Live form — runs full Phase 4–7 workflow on new input |
| Escalation Queue | Filterable, sorted table of all 994 records with capacity summary |
| Conflict Demo | DEMO001–DEMO006 case browser with explanations |
| Data Quality | Missing value report and quality distribution |

**Key UI features:**
- `st.success` / `st.warning` / `st.error` colour coding by risk level
- Sensor-symptom conflict clearly highlighted
- Offline store-and-forward banner for offline cases
- Safe fallback banner for incomplete data
- Privacy notice in sidebar on all pages

---

## Phase 9 — Simple Machine Learning Model 🔜 PENDING

**Goal:** Train a simple supervised ML model and compare it with the rule-based approach.

**Planned approach:**
- Use `data/cleaned_maternal_data.csv` as input
- Train a Decision Tree or Logistic Regression classifier (Scikit-learn)
- Target label: `risk_level` from Phase 4 (or a binary HIGH/not-HIGH label)
- Evaluate using accuracy, precision, recall, confusion matrix
- Save model to `models/risk_model.pkl`
- Integrate predictions into the Streamlit app (optional)

**Status:** Not started. No ML code exists in the repository at this time.

---

## Phase 10 — Formal Experiment and Evaluation 🔜 PENDING

**Goal:** Run documented experiments to evaluate the system's rule-based and ML-based detection.

**Planned activities:**
- Compare rule-based risk detection results with the ML model
- Evaluate conflict detection against the demo cases
- Document experiment results in `experiments/`
- Produce evaluation charts (precision/recall, confusion matrix)

**Status:** Not started. The `experiments/` directory is reserved but empty.

---

## Phase 11 — Failure-Mode Analysis and Stress Testing 🔜 PENDING

**Goal:** Document what happens when the system receives bad, extreme, or adversarial input.

**Planned activities:**
- Test with all-missing sensor data
- Test with extreme out-of-range values
- Test with contradictory symptom combinations
- Document all failure cases in `docs/FAILURE_CASES.md`

**Status:** Not started. Basic safe fallback (UNCERTAIN → SAFE_FALLBACK) already handles common missing-data scenarios.

---

## Phase 12 — Final Documentation and Presentation 🔜 PENDING

**Goal:** Prepare the final project report and presentation.

**Planned deliverables:**
- `docs/FINAL_REPORT.md` — full summary of all phases and findings
- `docs/FAILURE_CASES.md` — documented known failure cases and limitations
- Updated `README.md`
- Presentation slides (if required for submission)

**Status:** Not started.

---

## Summary of Repository Status

| Category | Count |
|----------|-------|
| Python scripts implemented | 7 (`generate_data.py`, `clean_data.py`, `risk_detection.py`, `trend_analysis.py`, `conflict_detection.py`, `escalation_workflow.py`, `app.py`) |
| CSV data files generated | 7 (in `data/`) |
| Documentation files | 3 (`README.md`, `docs/PROJECT_PLAN.md`, `docs/DATA_PRIVACY.md`) |
| Phases complete | 8 of 12 |
| Phases pending | 4 (9, 10, 11, 12) |

---

*End of PROJECT_PLAN.md*
