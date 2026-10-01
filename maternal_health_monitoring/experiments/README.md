# Phase 9 – Experiment and Evaluation

## Objective

Evaluate the operational performance of the Remote Maternal Health Monitoring
and Escalation System (Phases 2–7) using the existing simulated and anonymous
dataset.

The experiment answers three questions:

1. **How does the full workflow distribute risk and escalation decisions?**
2. **Do the system rules work correctly on controlled demonstration cases?**
3. **Where are the risk categories that would need attention in a real deployment?**

---

## Dataset Used

| File | Records | Description |
|---|---|---|
| `data/baseline_risk_results.csv` | 994 | Phase 4 risk detection output (sensor only) |
| `data/conflict_results.csv` | 994 | Phase 6 conflict detection output |
| `data/escalation_results.csv` | 994 | Phase 7 full escalation workflow output |
| `data/trend_results.csv` | 100 | Phase 5 trend analysis per patient |
| `data/demo_conflict_cases.csv` | 6 | Hand-crafted demonstration edge cases |

All data is simulated and anonymous. Patient IDs are P001–P100 and DEMO001–DEMO006.
No real patient data was used.

---

## Metrics Measured

### General
- Total records processed
- Unique patients
- Data quality (Good / Incomplete / Invalid)
- Missing sensor values

### Priority (Final Workflow)
- LOW / MEDIUM / HIGH / CRITICAL / UNTRUSTED counts

### Conflict Detection
- No conflict
- Sensor-symptom conflict
- Sensor-only concern
- Symptom-only concern
- Insufficient data

### Communication and Store-and-Forward
- Communication completed / pending / failed
- Store-and-forward STORED count

### Clinician Capacity
- Within capacity (immediate review)
- Queued (next available slot)

### Edge Case Routing Accuracy
- 6 demonstration cases tested against expected escalation pathway
- Accuracy = correct / total × 100

---

## Baseline

The **baseline** uses Phase 4 risk detection only:
- Sensor readings (BP, HR, SpO2, temperature) plus data quality
- Assigns: LOW / MEDIUM / HIGH / CRITICAL / UNCERTAIN
- Does **NOT** consider: patient-reported symptoms, trend history, conflict detection,
  capacity management, or communication status

| Baseline Risk | Count |
|---|---|
| LOW | 420 |
| MEDIUM | 131 |
| HIGH | 205 |
| CRITICAL | 62 |
| UNCERTAIN | 176 |

---

## Final Workflow

The **full workflow** (Phases 4–7) adds:
- Symptom reconciliation (Phase 6 conflict detection)
- Trend analysis — rising/falling BP patterns (Phase 5)
- Conflict detection — sensor vs symptom mismatch
- Safe Fallback — untrusted/incomplete data never classified as LOW risk
- Escalation routing — 5 pathways (Phase 7)
- Clinician capacity management
- Store-and-forward for offline cases

| Priority | Count | Escalation Pathway |
|---|---|---|
| LOW | 420 | CONTINUE_MONITORING |
| MEDIUM | 131 | SCHEDULE_FOLLOW_UP |
| HIGH | 126 | CLINICIAN_REVIEW |
| CRITICAL | 141 | URGENT_CLINICIAN_REVIEW |
| UNTRUSTED | 176 | SAFE_FALLBACK |

---

## Results

### Baseline vs Full Workflow Comparison

| Metric | Count |
|---|---|
| Decisions unchanged after full workflow | 890 / 994 |
| Decisions changed by full workflow | 104 / 994 |
| Cases escalated to URGENT_CLINICIAN_REVIEW | 79 |
| Cases routed to SAFE_FALLBACK | 25 |

The full workflow changed the decision for **104 out of 994** cases compared to
the sensor-only baseline. This demonstrates that symptoms, trends, and data quality
provide meaningful additional information beyond raw sensor readings.

### Edge Case Routing Accuracy

| Case | Scenario | Expected | Actual | Result |
|---|---|---|---|---|
| DEMO001 | LOW sensor + symptoms | CLINICIAN_REVIEW | CLINICIAN_REVIEW | PASS |
| DEMO002 | HIGH sensor + no symptoms | CLINICIAN_REVIEW | CLINICIAN_REVIEW | PASS |
| DEMO003 | Both signals concerning | URGENT_CLINICIAN_REVIEW | URGENT_CLINICIAN_REVIEW | PASS |
| DEMO004 | Incomplete data + offline | SAFE_FALLBACK | SAFE_FALLBACK | PASS |
| DEMO005 | All clear | CONTINUE_MONITORING | CONTINUE_MONITORING | PASS |
| DEMO006 | HIGH + offline + symptoms | URGENT_CLINICIAN_REVIEW | URGENT_CLINICIAN_REVIEW | PASS |

**Edge Case Routing Accuracy: 100.0% (6/6 correct)**

### Conflict Detection Results

| Conflict Status | Count |
|---|---|
| NO CONFLICT | 692 |
| SENSOR-ONLY CONCERN | 126 |
| INSUFFICIENT DATA | 176 |
| Total Flagged | 302 |

### Communication Results

| Communication Status | Count |
|---|---|
| Completed | 71 |
| Pending | 102 |
| Failed | 81 |
| Stored for Forward (offline) | 94 |

### Clinician Capacity Results

| Capacity Status | Count |
|---|---|
| WITHIN CAPACITY (immediate review) | 10 |
| QUEUED (next slot) | 257 |
| NOT APPLICABLE (routine/fallback) | 727 |

### Error Analysis

| Risk Category | Count | Notes |
|---|---|---|
| Sensor-only concern | 126 | Abnormal sensors but no symptoms |
| Insufficient data | 176 | Data quality too poor to classify |
| Communication failed | 81 | Clinician may not have been reached |
| Capacity queued | 257 | Delayed review due to capacity limit |
| False reassurance risk | 0 | No LOW-risk + symptom cases found |

---

## How to Run

```bash
# From the maternal_health_monitoring/ folder:
python experiments/run_experiment.py
```

Output files:
- `experiments/experiment_results.csv` — flat summary of all metrics
- `experiments/demo_case_results.csv` — per-case demo routing results

---

## Files in This Folder

| File | Description |
|---|---|
| `run_experiment.py` | Main experiment script |
| `experiment_results.csv` | Flat CSV of all measured metrics |
| `demo_case_results.csv` | Per-case demo routing results |
| `README.md` | This file |

---

## Limitations

1. **Simulated data only** — all 994 records are generated, not real patient data
2. **No ground truth** — there is no real clinical outcome to compare against
3. **No machine learning** — all rules are hand-crafted (by design, for clarity)
4. **Prototype rules** — thresholds (e.g. BP ≥ 140 = HIGH) are simplified for
   educational demonstration, not clinically validated
5. **Single review cycle** — the capacity rule (10 cases) is applied once;
   a real system would operate continuously
6. **No real network** — communication and store-and-forward are simulated

---

## Disclaimer

This is an educational prototype using simulated and anonymous data.
It is **NOT** a medical diagnostic system.
Do **NOT** use this output to make real clinical decisions.
