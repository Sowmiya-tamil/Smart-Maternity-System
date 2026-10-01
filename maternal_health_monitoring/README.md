# Remote Maternal Health Monitoring and Escalation System (Smart Maternity System)

> **Academic Prototype Notice & Medical Disclaimer:**  
> This software is an **educational research prototype** that uses **entirely synthetic, simulated, and anonymized maternal-health data**. It is **NOT** a certified medical diagnostic device or clinical decision support system, and it must **NOT** be used to make real-world clinical or diagnostic decisions. All clinical rules, thresholds, and simulated scenarios are designed solely for software engineering demonstration and academic review.

---

## 1. Project Title

**Remote Maternal Health Monitoring and Escalation System**  
*(Smart Maternity System)*

---

## 2. Project Overview

The **Remote Maternal Health Monitoring and Escalation System** is a modular, rule-based healthcare software prototype engineered to address maternal health tracking in low-resource and rural settings. 

In many underserved areas, expectant mothers interact with community health workers (CHWs) on an intermittent basis. Routine visits generate periodic vital sign readings and symptom reports, but detecting subtle health deterioration, resolving discrepancies between sensor readings and reported symptoms, and triaging high-risk cases under constrained healthcare infrastructure remain challenging.

This project implements a complete, transparent, and deterministic pipeline:
1. **Simulated Maternal Health Data Generation** (sensor vitals + maternal symptom logs)
2. **Data Cleaning and Validation** (range bounds, missing-data handling, data quality flags)
3. **Rule-Based Baseline Risk Detection** (vital threshold classification)
4. **Per-Patient Blood Pressure Trend Analysis** (longitudinal visit progression)
5. **Sensor-Symptom Conflict Detection** (identifying discrepancies and masking)
6. **Escalation Routing with Safe Fallback** (prioritized workflow allocation)
7. **Offline Store-and-Forward & Clinician Capacity Management** (connectivity resilience and queue management)
8. **Failure Mode Analysis** (rigorous edge-case and failure characterization)
9. **Interactive Streamlit Web Dashboard** (real-time monitoring, triage queue, patient drilldown, and analytics)

---

## 3. Problem Statement

Maternal mortality and preventable prenatal complications remain significant global public health challenges, particularly in remote and low-resource environments. Key operational challenges include:
- **Intermittent Monitoring:** Vital signs are recorded irregularly during field visits rather than continuously in clinical environments.
- **Sensor Noise and Missing Data:** Field sensors often drop readings, generate sensor artifacts, or run out of battery.
- **Sensor-Symptom Discrepancies:** A patient may present with severe pre-eclampsia symptoms (e.g., severe headache, visual disturbance) while blood pressure sensors show borderline or deceptive normal ranges, or vice versa.
- **Unreliable Network Infrastructure:** Rural clinics frequently face internet downtime, risking silent data loss during critical emergencies.
- **Clinician Scarcity and Burnout:** Primary health centers face strict staffing limits and cannot absorb unbounded emergency escalations simultaneously without a structured triage queue.

---

## 4. Objectives

The primary objectives of this project are:
- **Rule-Based Determinism:** Implement explainable, transparent, and auditable rule-based triage logic without opaque black-box machine learning dependencies.
- **Data Quality & Safe Fallback:** Prevent silent under-triage by ensuring incomplete, noisy, or invalid sensor records are never classified as "Low Risk" and are instead routed to a dedicated `SAFE_FALLBACK` protocol.
- **Sensor-Symptom Harmony:** Reconcile physiological measurements with subjective patient symptoms, ensuring subjective danger signs take precedence over reassuring sensor values.
- **Connectivity & Operational Resilience:** Model store-and-forward communication buffers for offline scenarios and manage clinician capacity limits (max 10 high-priority reviews per cycle) via a prioritized queue.
- **Comprehensive Visualization:** Deliver an interactive, multi-view Streamlit dashboard for community health workers and reviewing clinicians.

---

## 5. Key Features

- **Synthetic Cohort Generation:** 994 observational records across 100 anonymous patients (P001–P100), with 5–15 sequential visits each.
- **6 Hand-Crafted Edge Cases (DEMO001–DEMO006):** Demonstrating normal vitals, hypertensive crisis, sensor-symptom conflict, sensor-only concern, offline store-and-forward, and missing data fallback.
- **5-Tier Priority Framework:** Categorizes records into `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`, and `UNTRUSTED`.
- **Longitudinal Trend Tracking:** Evaluates multi-visit systolic blood pressure velocity (Increasing, Decreasing, Stable, Insufficient Data).
- **Safety Precedence Rules:** Patient-reported danger signs (headache, blurred vision, bleeding) strictly override normal sensor readings.
- **Store-and-Forward Buffer:** Offline high-risk records are persisted in local queues (`STORED`) rather than discarded.
- **Clinician Workload Governor:** Enforces a capacity boundary of 10 concurrent reviews per cycle, queuing excess cases transparently.
- **Failure Mode Matrix (Phase 10):** Documents 10 specific failure modes with measured mitigation outcomes (7 Handled, 3 Partially Handled).
- **Interactive Multi-Page Dashboard:** Built in Streamlit featuring high-level KPI cards, risk/escalation charts, patient detail exploration, triage queue management, edge case demos, and data quality diagnostics.

---

## 6. System Workflow / Architecture

The system executes a strictly sequential, transparent data and logic pipeline:

```
┌─────────────────────────────────────────────────────────┐
│ 1. Data Generation (generate_data.py)                   │
│    994 simulated records across 100 synthetic patients  │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 2. Data Cleaning & Validation (clean_data.py)           │
│    Range checks & Quality tagging (Good/Incomplete/     │
│    Invalid)                                             │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 3. Baseline Risk Detection (risk_detection.py)          │
│    Physiological thresholds (LOW, MEDIUM, HIGH,         │
│    CRITICAL, UNCERTAIN)                                 │
└───────────────┬───────────────────────────┬─────────────┘
                │                           │
                ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────────┐
│ 4. BP Trend Analysis          │ │ 5. Conflict Detection │
│    (trend_analysis.py)        │ │    (conflict_         │
│    Multi-visit BP trajectory  │ │     detection.py)     │
│    (Increasing/Decreasing/    │ │    Sensor vs. Symptom │
│    Stable)                    │ │    Discrepancy Check  │
└───────────────┬───────────────┘ └───────────┬───────────┘
                │                             │
                └───────────────┬─────────────┘
                                ▼
┌─────────────────────────────────────────────────────────┐
│ 6. Escalation Workflow & Capacity (escalation_          │
│    workflow.py)                                         │
│    Prioritization, Safe Fallback, Offline Buffer,       │
│    Capacity Governor                                    │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 7. Failure Mode & Usability Analysis (Phase 10 & 11)    │
│    Risk mitigation audit & Stakeholder evaluation       │
└──────────────────────────┬──────────────────────────────┘
                           ▼
┌─────────────────────────────────────────────────────────┐
│ 8. Interactive Streamlit Dashboard (app.py)             │
│    Multi-view analytics, triage queue, and live engine  │
└─────────────────────────────────────────────────────────┘
```

---

## 7. Technologies Used

| Technology | Purpose | Implementation Status |
|---|---|---|
| **Python 3.10+** | Core programming language for entire pipeline | ✅ Implemented |
| **Streamlit** | Interactive multi-page web application & UI | ✅ Implemented |
| **Pandas** | Tabular data manipulation, aggregation, and CSV serialization | ✅ Implemented |
| **NumPy** | Numerical data operations and vector utilities | ✅ Implemented |
| **Scikit-learn** | Supervised learning & model comparison | 🔜 *Future Enhancement* |

> **Architecture Note:** No external databases, third-party cloud APIs, or heavy deep-learning frameworks (TensorFlow, PyTorch) are used. The implementation is self-contained, offline-capable, and easily reproducible.

---

## 8. Dataset

The project operates on synthetic datasets generated specifically to model community maternal health parameters without privacy risks:

- **Primary Dataset (`data/cleaned_maternal_data.csv`):** 994 observational records for 100 synthetic patients (`P001`–`P100`), each with 5 to 15 sequential observation days.
- **Demonstration Dataset (`data/demo_conflict_cases.csv`):** 6 curated edge cases (`DEMO001`–`DEMO006`) showcasing distinct operational boundary conditions.

### Monitored Parameters:
1. **Physiological Vitals (Sensors):**
   - Systolic Blood Pressure (`systolic_bp` in mmHg)
   - Diastolic Blood Pressure (`diastolic_bp` in mmHg)
   - Heart Rate (`heart_rate` in bpm)
   - Body Temperature (`body_temp` in °C)
   - Blood Oxygen Saturation (`spo2` in %)
2. **Subjective Reported Symptoms (Boolean flags):**
   - Headache, Blurred Vision, Severe Fatigue, Swelling, Reduced Fetal Movement, Vaginal Bleeding
3. **Environment & Context:**
   - Gestational Age (weeks), Observation Day, Internet Connectivity (`Online` / `Offline`), Communication Result

---

## 9. Implemented Phases

| Phase | Module Name | Primary Script / Output | Status |
|:---:|---|---|:---:|
| **Phase 1** | Project Architecture & Governance | `docs/PROJECT_PLAN.md`, `docs/DATA_PRIVACY.md` | ✅ Complete |
| **Phase 2** | Synthetic Dataset Generation | `generate_data.py` → `data/simulated_maternal_data.csv` | ✅ Complete |
| **Phase 3** | Data Cleaning & Quality Labeling | `clean_data.py` → `data/cleaned_maternal_data.csv` | ✅ Complete |
| **Phase 4** | Baseline Risk Engine | `risk_detection.py` → `data/baseline_risk_results.csv` | ✅ Complete |
| **Phase 5** | Longitudinal Trend Analysis | `trend_analysis.py` → `data/trend_results.csv` | ✅ Complete |
| **Phase 6** | Sensor-Symptom Conflict Detection | `conflict_detection.py` → `data/conflict_results.csv` | ✅ Complete |
| **Phase 7** | Escalation, Capacity & Fallback | `escalation_workflow.py` → `data/escalation_results.csv` | ✅ Complete |
| **Phase 8** | Streamlit Interactive Dashboard | `app.py` (Full multi-page user interface) | ✅ Complete |
| **Phase 9** | Experiment & Evaluation Suite | `experiments/run_experiment.py` → `experiments/experiment_results.csv` | ✅ Complete |
| **Phase 10** | Failure Mode Analysis | `experiments/failure_mode_analysis.py` → `docs/FAILURE_MODE_ANALYSIS.md` | ✅ Complete |
| **Phase 11** | Stakeholder Usability Validation | `validation/run_validation.py` → `validation/USER_FEEDBACK_SUMMARY.md` | ✅ Complete |

---

## 10. Risk Detection

The baseline risk engine (`risk_detection.py`) applies deterministic physiological rules to classify records:

| Risk Category | Distribution (994 records) | Defining Criteria / Clinical Logic |
|---|:---:|---|
| **LOW** | 420 | All vitals within normal parameters; no concerning symptoms reported. |
| **MEDIUM** | 131 | Mild physiological elevation (e.g., Systolic BP 130–139 mmHg or mild tachycardia). |
| **HIGH** | 126 | Significant elevation (e.g., Systolic BP 140–159 mmHg, SpO2 90–94%, or moderate fever). |
| **CRITICAL** | 141 | Severe hypertension (Systolic BP ≥ 160 mmHg), SpO2 < 90%, or acute danger signs (e.g., bleeding). |
| **UNCERTAIN** | 176 | Sensor readings missing, corrupted, or physiologically implausible (triggers safe fallback). |

---

## 11. Trend Analysis

The trend analysis engine (`trend_analysis.py`) groups visits by patient and analyzes systolic blood pressure velocity across consecutive observation days:
- **Short-Term Trend (2-point velocity):**
  - `Increasing`: Systolic BP increase > +5 mmHg between recent visits.
  - `Decreasing`: Systolic BP decrease > -5 mmHg.
  - `Stable`: Fluctuation within ±5 mmHg.
- **Longitudinal Trend (3+ visits):** Evaluates persistent multi-visit upward drift indicating gradual onset of pre-eclampsia.
- **Safety Role:** A patient presenting with "Medium" baseline risk whose blood pressure shows a continuous upward trajectory is flagged for closer follow-up.

---

## 12. Sensor-Symptom Conflict Detection

The conflict detection module (`conflict_detection.py`) cross-references vital sign levels with maternal symptom reports:

| Conflict Classification | Count | Operational Rule & Action |
|---|:---:|---|
| **NO CONFLICT** | 692 | Vitals and reported symptoms are fully concordant. |
| **SENSOR-ONLY CONCERN** | 126 | Vitals are elevated (HIGH/CRITICAL), but the patient reports no symptoms (asymptomatic risk). Triage to `CLINICIAN_REVIEW`. |
| **SENSOR-SYMPTOM CONFLICT** | 0 *(in bulk data, tested in DEMO001)* | Normal vitals accompanied by red-flag symptoms (headache, vision loss, bleeding). **Rule:** Symptoms strictly override sensors → Escalated to `CLINICIAN_REVIEW`. |
| **INSUFFICIENT DATA** | 176 | Missing or corrupt measurements prevent conflict reconciliation. Escalated to `SAFE_FALLBACK`. |

---

## 13. Escalation Workflow

The escalation engine (`escalation_workflow.py`) synthesizes baseline risk, trend velocity, and conflict tags into 5 actionable pathways:

| Escalation Pathway | Priority | Count | Target Action |
|---|---|:---:|---|
| `CONTINUE_MONITORING` | **LOW** | 420 | Routine community health worker monitoring. |
| `SCHEDULE_FOLLOWUP` | **MEDIUM** | 131 | Schedule non-urgent checkup within 48–72 hours. |
| `CLINICIAN_REVIEW` | **HIGH** | 126 | Priority review by primary care physician/midwife. |
| `URGENT_CLINICIAN_REVIEW` | **CRITICAL** | 141 | Immediate emergency clinical evaluation. |
| `SAFE_FALLBACK` | **UNTRUSTED** | 176 | Immediate vitals re-measurement & supervisor check. |

---

## 14. Safe Fallback

A cornerstone of the system's design is the **Safe Fallback Protocol**:
- **Anti-Under-Triage Principle:** Incomplete, corrupted, or out-of-range sensor readings are **never** assumed to be normal or assigned `LOW` priority.
- Any record flagged as `Incomplete` or `Invalid` in Phase 3 is automatically assigned `UNTRUSTED` priority and routed to `SAFE_FALLBACK`.
- The system explicitly alerts health workers to repeat measurements and check device sensors rather than providing false reassurance.

---

## 15. Offline / Store-and-Forward

To operate reliably in remote rural areas with intermittent connectivity:
- The system checks connectivity status (`Online` vs. `Offline`) before attempting remote data dispatch.
- Out of 348 cases requiring clinical escalation, **153 offline encounters** were detected.
- **94 high-risk offline records** were successfully buffered into local persistence (`STORED`) for automated forwarding upon signal recovery.
- Critical patient records are never silently dropped due to lack of network connectivity.

---

## 16. Clinician Capacity Handling

Rural medical staff have bounded review capacity. To prevent unmanaged inbox flooding and clinician fatigue:
- The system enforces a configurable **Capacity Limit of 10 HIGH / CRITICAL reviews per review cycle**.
- **Execution in Current Dataset:**
  - **10 cases** allocated to `WITHIN_CAPACITY` for immediate review.
  - **257 cases** assigned to `QUEUED` status, strictly preserving priority rank for the subsequent review window.
- The triage queue interface makes backlogs fully visible to supervisory staff.

---

## 17. Failure Mode Analysis (Phase 10 Summary)

Phase 10 audited the system against 10 distinct failure modes (`docs/FAILURE_MODE_ANALYSIS.md`):

| ID | Failure Mode Scenario | System Handling & Mitigation | Status |
|:---:|---|---|:---:|
| **FM01** | Missing sensor readings (176 records) | Flagged `Incomplete`, routed to `SAFE_FALLBACK` | ✅ Handled |
| **FM02** | Invalid/noisy sensor values (25 records) | Flagged `Invalid`, repeat measurement required | ✅ Handled |
| **FM03** | High sensor risk with no symptoms (126 records) | Categorized `SENSOR-ONLY CONCERN` → Clinician review | ✅ Handled |
| **FM04** | Normal sensors with red-flag symptoms | Symptoms override sensors (demonstrated in `DEMO001`) | ✅ Handled |
| **FM05** | High sensors + concerning symptoms (141 records) | Immediate `CRITICAL` priority & urgent escalation | ✅ Handled |
| **FM06** | Insufficient data for decision (176 records) | Explicit `UNTRUSTED` label, no silent low-risk classification | ✅ Handled |
| **FM07** | Network connectivity offline (153 records) | Store-and-forward local buffer (`STORED`) | ⚠️ Partially Handled *(Simulated buffer)* |
| **FM08** | Communication transmission failure (81 records) | Error logged, case retained in queue | ⚠️ Partially Handled *(Manual retry)* |
| **FM09** | Clinician capacity exceeded (257 queued) | Capacity governor queues excess cases | ⚠️ Partially Handled *(Fixed quota)* |
| **FM10** | Untrusted recommendations (176 records) | Explicit `SAFE_FALLBACK` workflow | ✅ Handled |

**Summary:** 7 Handled, 3 Partially Handled (connectivity, transmission retry, and dynamic capacity require live infrastructure).

---

## 18. Streamlit Dashboard

The web application (`app.py`) is fully implemented and provides a multi-page interface for health workers and clinicians:

1. **Dashboard Overview:** High-level KPI metric cards (Total Records, Critical, High, Conflicts, Safe Fallback), interactive risk & escalation distributions, and communication status panels.
2. **Patient Assessment / Live Triage:** Interactive vital sign and symptom entry form that processes real-time inputs through the complete Phase 4–7 engine with instant visual risk badges.
3. **Escalation Queue:** Filterable triage queue displaying all 994 records with priority sorting, search capabilities, and clinician capacity utilization indicators.
4. **Conflict Demo Cases:** Interactive inspector for the 6 hand-crafted edge case demonstrations (`DEMO001`–`DEMO006`).
5. **Data Quality & Insights:** Detailed missing-value diagnostics, sensor anomaly distributions, and longitudinal BP trend visualizations.

---

## 19. Privacy and Safety

- **100% Synthetic Data:** All records are programmatically generated. No real patient identities, medical history, or protected health information (PHI) exist in this project.
- **Anonymized Identifiers:** Patients are identified solely through synthetic codes (`P001`–`P100`, `DEMO001`–`DEMO006`).
- **No External Data Exfiltration:** The system runs entirely on the local machine with zero third-party cloud data transmission.
- Full details are available in [`docs/DATA_PRIVACY.md`](docs/DATA_PRIVACY.md).

---

## 20. Current Project Status

### ✅ Completed & Fully Functional:
- [x] End-to-end data pipeline (`generate_data.py` → `clean_data.py` → `risk_detection.py` → `trend_analysis.py` → `conflict_detection.py` → `escalation_workflow.py`)
- [x] Deterministic 5-level risk & priority engine
- [x] Longitudinal BP trend detection
- [x] Sensor-symptom conflict resolution rules
- [x] Safe fallback and offline store-and-forward modeling
- [x] Clinician capacity queue management
- [x] Multi-page interactive Streamlit dashboard (`app.py`)
- [x] Formal experiment suite (`experiments/run_experiment.py`)
- [x] Comprehensive failure mode analysis (`docs/FAILURE_MODE_ANALYSIS.md`)
- [x] Usability & stakeholder feedback evaluation (`validation/USER_FEEDBACK_SUMMARY.md`)

---

## 21. Pending / Future Improvements

The following architectural and clinical enhancements represent future work:

- **Machine Learning Benchmarking:** Train simple interpretable models (e.g., Logistic Regression, Decision Trees) to benchmark predictive performance against the deterministic rule-based baseline.
- **Hardware Telemetry Integration:** Direct Bluetooth Low Energy (BLE) ingestion from digital sphygmomanometers and pulse oximeters.
- **Dynamic Multi-Clinician Load Balancing:** Adaptive queuing across regional health networks rather than a fixed single-clinic quota.
- **Automated Communication Protocols:** Integration of cellular SMS and IVR alerting mechanisms for offline-to-online synchronization.
- **Clinical Validation Studies:** Prospective clinical trials and ethical review (IRB) under certified medical supervision.

---

## 22. How to Run the Project

### Prerequisites
- Python 3.10 or higher installed on your system.

### Step 1: Clone or Open the Repository
```bash
cd maternal_health_monitoring
```

### Step 2: Install Required Dependencies
```bash
pip install -r requirements.txt
```
*(Dependencies: `streamlit`, `pandas`, `numpy`)*

### Step 3: (Optional) Re-run the Data Pipeline
> **Note:** All precomputed CSV results are included in `data/`. If you wish to regenerate and re-run all pipeline stages:
```bash
python generate_data.py        # Generates synthetic observations
python clean_data.py           # Validates sensor ranges & data quality
python risk_detection.py       # Computes baseline risk categories
python trend_analysis.py       # Analyzes longitudinal BP trends
python conflict_detection.py   # Reconciles sensor-symptom conflicts
python escalation_workflow.py  # Executes escalation, capacity & fallback logic
python experiments/run_experiment.py          # Runs operational metrics evaluation
python experiments/failure_mode_analysis.py   # Executes failure mode verification
python validation/run_validation.py           # Processes usability feedback survey
```

### Step 4: Launch the Streamlit Web Dashboard
```bash
streamlit run app.py
```
Open your web browser at: **`http://localhost:8501`**

---

## 23. Project Disclaimer

```
========================================================================================
                               ACADEMIC DISCLAIMER
========================================================================================
This software project is developed strictly for educational, academic, and research 
demonstration purposes. 

1. NOT A MEDICAL DEVICE: This software is NOT approved, certified, or intended for use 
   as a medical diagnostic device, clinical decision support system, or treatment tool.
2. SYNTHETIC DATA: All data, including patient identifiers, physiological readings, and 
   clinical encounters, are 100% synthetically generated. Any resemblance to real persons 
   or medical records is purely coincidental.
3. CLINICAL CONSULTATION: Real-world maternal health concerns must always be evaluated 
   by licensed healthcare professionals and medical doctors.
========================================================================================
```
