# Remote Maternal Health Monitoring and Escalation System

> **Educational Prototype — Simulated Data Only**
> This project is NOT a medical diagnostic system and must NOT be used to make real clinical decisions.

---

## 1. Project Title

**Remote Maternal Health Monitoring and Escalation System**

---

## 2. Problem Statement

Pregnant women living in remote or rural areas often receive only periodic community health worker visits. It is difficult to track changes in health readings over time, spot danger signs early, or know when a case should be escalated to a clinic or hospital — especially when internet connectivity is unreliable and clinician capacity is limited.

This project demonstrates a simulated software workflow that could help community health workers monitor maternal health, detect risk, and route cases through a structured escalation process.

---

## 3. Project Objective

Build a beginner-friendly, rule-based prototype (no real patient data) that:

- Generates and processes simulated maternal health observations
- Detects baseline health risk from sensor readings and reported symptoms
- Tracks blood pressure trends across multiple patient visits
- Identifies conflicts between sensor readings and patient-reported symptoms
- Routes cases through a priority-based escalation workflow
- Handles offline scenarios using a store-and-forward simulation
- Enforces a clinician capacity limit and queues excess high-priority cases
- Presents the complete workflow through a multi-page Streamlit application

---

## 4. Current Project Status

**Phases 1–8 are implemented and working.**

| Phase | Title                                          | Status          |
|-------|------------------------------------------------|-----------------|
| 1     | Project Foundation                             | ✅ Complete     |
| 2     | Simulated Dataset Generation                   | ✅ Complete     |
| 3     | Data Cleaning and Validation                   | ✅ Complete     |
| 4     | Baseline Risk Detection                        | ✅ Complete     |
| 5     | Trend Analysis                                 | ✅ Complete     |
| 6     | Sensor-Symptom Conflict Detection              | ✅ Complete     |
| 7     | Escalation Workflow, Capacity & Safe Fallback  | ✅ Complete     |
| 8     | Streamlit Application (5-page prototype)       | ✅ Complete     |
| 9     | Simple Machine Learning Model                  | 🔜 Pending     |
| 10    | Formal Experiment and Evaluation               | 🔜 Pending     |
| 11    | Failure-Mode Analysis and Stress Testing       | 🔜 Pending     |
| 12    | Final Documentation and Presentation           | 🔜 Pending     |

---

## 5. Key Features Implemented

| Feature | Description |
|---------|-------------|
| **Simulated dataset** | ~1 000 observations across 100 anonymous patients (P001–P100), 5–15 visits each |
| **Data cleaning** | Missing-value detection, sensor range validation, data quality labels (Good / Incomplete / Invalid) |
| **Rule-based risk detection** | Five risk levels: LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN |
| **Trend analysis** | Per-patient systolic BP trend: Increasing / Decreasing / Stable / Not Enough Data |
| **Conflict detection** | Compares sensor risk with reported symptoms; produces NO CONFLICT / SENSOR-SYMPTOM CONFLICT / SENSOR-ONLY CONCERN / INSUFFICIENT DATA |
| **Escalation workflow** | Five priority levels; five escalation pathways including SAFE_FALLBACK |
| **Safe fallback** | Incomplete or invalid data is never classified as LOW risk |
| **Store-and-forward** | Offline high-priority cases are flagged as STORED, not discarded |
| **Clinician capacity** | First 10 HIGH/CRITICAL cases = WITHIN_CAPACITY; remainder queued |
| **Streamlit app** | Dashboard, Patient Assessment, Escalation Queue, Conflict Demo, Data Quality pages |
| **Demo conflict cases** | Six hand-crafted cases (DEMO001–DEMO006) illustrating every scenario |
| **Privacy by design** | No real names, addresses, phone numbers, or real patient records at any point |

---

## 6. Technology Stack

| Tool       | Purpose                             | Used? |
|------------|-------------------------------------|-------|
| Python 3   | Main programming language           | ✅    |
| Streamlit  | Interactive web application         | ✅    |
| Pandas     | Data loading, processing, CSV I/O   | ✅    |
| NumPy      | Numerical operations                | ✅    |
| Scikit-learn | Simple ML model (Phase 9)        | 🔜 Pending |

> **No** TensorFlow, PyTorch, LSTM, databases, APIs, authentication, or external services are used.

---

## 7. Project Structure

```
maternal_health_monitoring/
│
├── app.py                    ← Streamlit application (5 pages)
├── generate_data.py          ← Phase 2: simulated dataset generation
├── clean_data.py             ← Phase 3: data cleaning and validation
├── risk_detection.py         ← Phase 4: rule-based risk detection
├── trend_analysis.py         ← Phase 5: per-patient BP trend analysis
├── conflict_detection.py     ← Phase 6: sensor-symptom conflict detection
├── escalation_workflow.py    ← Phase 7: escalation, capacity, safe fallback
│
├── requirements.txt          ← Python packages required
├── README.md                 ← This file
│
├── data/
│   ├── simulated_maternal_data.csv   ← Raw simulated data (~1 000 rows)
│   ├── cleaned_maternal_data.csv     ← Cleaned and quality-labelled data
│   ├── baseline_risk_results.csv     ← Risk levels from Phase 4
│   ├── trend_results.csv             ← Per-patient trend from Phase 5
│   ├── conflict_results.csv          ← Conflict labels from Phase 6
│   ├── escalation_results.csv        ← Full escalation output from Phase 7
│   └── demo_conflict_cases.csv       ← 6 hand-crafted demo cases
│
├── docs/
│   ├── PROJECT_PLAN.md       ← Detailed phase-by-phase plan
│   └── DATA_PRIVACY.md       ← Privacy-by-design policy
│
├── models/                   ← Reserved for Phase 9 ML model
└── experiments/              ← Reserved for Phase 10 evaluation scripts
```

---

## 8. How to Install Requirements

```bash
pip install -r requirements.txt
```

Required packages: `streamlit`, `pandas`, `numpy`

---

## 9. How to Run the Project

### Option A — Run the full data pipeline first (required once)

```bash
cd maternal_health_monitoring

python generate_data.py        # Phase 2 — creates simulated_maternal_data.csv
python clean_data.py           # Phase 3 — creates cleaned_maternal_data.csv
python risk_detection.py       # Phase 4 — creates baseline_risk_results.csv
python trend_analysis.py       # Phase 5 — creates trend_results.csv
python conflict_detection.py   # Phase 6 — creates conflict_results.csv
python escalation_workflow.py  # Phase 7 — creates escalation_results.csv
```

### Option B — Launch the Streamlit application

```bash
python -m streamlit run app.py
```

Open your browser at: **http://localhost:8501**

> The data CSV files are already included in the repository.
> You only need to re-run the pipeline scripts if you want to regenerate the data.

---

## 10. Data Pipeline

```
generate_data.py
    └─► data/simulated_maternal_data.csv
            └─► clean_data.py
                    └─► data/cleaned_maternal_data.csv
                            └─► risk_detection.py
                                    └─► data/baseline_risk_results.csv
                                            ├─► trend_analysis.py
                                            │       └─► data/trend_results.csv
                                            └─► conflict_detection.py  (uses trend_results too)
                                                    └─► data/conflict_results.csv
                                                            └─► escalation_workflow.py
                                                                    └─► data/escalation_results.csv
```

---

## 11. Module Descriptions

### Phase 2 — Simulated Dataset Generation (`generate_data.py`)
Generates approximately 1 000 rows of completely fake patient observations across 100 anonymous patients (P001–P100). Each patient has 5–15 observation days. Fields include systolic/diastolic BP, heart rate, temperature, SpO2, six patient-reported symptoms, internet status, and communication status. No real patient data is used.

### Phase 3 — Data Cleaning (`clean_data.py`)
Validates each sensor reading against safe prototype ranges. Records are labelled **Good**, **Incomplete** (missing values), or **Invalid** (out-of-range). The cleaned dataset is saved without modifying the original raw file.

### Phase 4 — Baseline Risk Detection (`risk_detection.py`)
Applies simple if/elif rules to assign one of five risk levels:

| Level | Meaning |
|-------|---------|
| LOW | All readings within prototype normal ranges |
| MEDIUM | Moderately elevated readings |
| HIGH | Clearly elevated readings requiring clinician review |
| CRITICAL | Severely abnormal readings or high-priority symptoms |
| UNCERTAIN | Data quality is too poor to assess reliably |

### Phase 5 — Trend Analysis (`trend_analysis.py`)
Groups observations by `patient_id`, sorts by `observation_day`, and computes:
- **Recent trend** (last two readings): Increasing / Decreasing / Stable / Not Enough Data
- **Overall trend** (3+ readings): Consistently Increasing / Consistently Decreasing / Stable/Variable

The ±5 mmHg threshold used here is a **prototype demonstration value, not a medical threshold**.

### Phase 6 — Sensor-Symptom Conflict Detection (`conflict_detection.py`)
Compares the sensor-based risk level with patient-reported symptoms and assigns one of four conflict labels:

| Status | Meaning |
|--------|---------|
| NO CONFLICT | Sensor and symptoms are consistent |
| SENSOR-SYMPTOM CONFLICT | Sensors appear normal but concerning symptoms reported → Clinician Review |
| SENSOR-ONLY CONCERN | Sensor risk is high but no matching symptoms reported |
| INSUFFICIENT DATA | Data quality too poor to reconcile → Safe Fallback |

**Core safety rule:** A low/normal sensor reading never overrides a concerning symptom report.

### Phase 7 — Escalation Workflow (`escalation_workflow.py`)
Assigns priority, escalation pathway, communication simulation, store-and-forward status, clinician capacity, and schedule status.

**Safe fallback:** UNCERTAIN or incomplete data is always classified UNTRUSTED and routed to SAFE_FALLBACK. It is never labelled LOW.

**Store-and-forward:** Offline cases requiring escalation are marked STORED (not discarded).

**Clinician capacity:** The first 10 HIGH/CRITICAL cases per cycle are WITHIN_CAPACITY; the rest are QUEUED.

### Phase 8 — Streamlit Application (`app.py`)
Five-page interactive prototype:

| Page | Description |
|------|-------------|
| Dashboard | Summary metrics and two distribution charts |
| Patient Assessment | Live assessment form — runs the full Phase 4–7 workflow on new input |
| Escalation Queue | Sortable, filterable queue of all 994 processed records |
| Conflict Demo | Interactive browser for all six DEMO001–DEMO006 edge cases |
| Data Quality | Missing value report and quality distribution |

---

## 12. Privacy-by-Design Approach

- All patient records are **entirely simulated** by `generate_data.py`
- No names, phone numbers, addresses, Aadhaar numbers, hospital IDs, or real medical records are used at any point
- Patients are identified only by anonymous IDs: P001–P100 and DEMO001–DEMO006
- All data files are stored locally; no external database, server, or API is used
- See [`docs/DATA_PRIVACY.md`](docs/DATA_PRIVACY.md) for the full privacy policy

---

## 13. Pending Work

The following items remain to be completed:

- **Phase 9:** Train a simple supervised ML model (Decision Tree or Logistic Regression) on the simulated dataset and compare it with the rule-based approach
- **Phase 10:** Formal experiment and evaluation (accuracy, precision, recall, confusion matrix)
- **Phase 11:** Failure-mode analysis and stress testing (edge cases, extreme values, all-missing data)
- **Phase 12:** Final documentation (`docs/FINAL_REPORT.md`, `docs/FAILURE_CASES.md`) and presentation

---

## ⚠️ Important Disclaimer

> This prototype is **not a medical diagnostic system** and must **not** be used to make real clinical decisions.
>
> All data is entirely simulated. All thresholds and rules are for **software workflow demonstration only** and do not represent official medical guidelines.
>
> If you are a patient or caregiver, please consult a qualified medical professional for any health concerns.
