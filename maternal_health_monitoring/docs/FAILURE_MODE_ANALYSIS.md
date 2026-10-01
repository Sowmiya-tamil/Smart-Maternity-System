# Failure Mode Analysis

**Project:** Remote Maternal Health Monitoring and Escalation System
**Phase:** 10 – Failure Mode Analysis
**Date:** October 2026

> **Disclaimer:** This is an educational prototype using simulated and anonymous
> data. It is **not** a medical diagnostic system and has **not** been clinically
> validated. All patient IDs (P001–P100, DEMO001–DEMO006) are entirely fictional.
> Do **not** use this system to make real clinical decisions.

---

## 1. Purpose

This document identifies, describes, and evaluates the failure modes of the
Remote Maternal Health Monitoring and Escalation System built across Phases 2–7.

A **failure mode** is any condition in which the system may not perform as
intended — such as missing data, network outages, sensor errors, or exceeding
clinician capacity.

For each failure mode, this analysis records:
- What the failure is and its possible causes
- How the system detects it
- How the system responds
- What safety action is taken
- What risk remains after the response
- Whether the failure mode is fully handled, partially handled, or a future improvement

The analysis uses only existing CSV outputs from the Phase 2–7 pipeline.
No machine learning or complex algorithms are used.

---

## 2. Failure Modes Identified

Ten failure modes were identified for this prototype:

| ID | Failure Scenario |
|---|---|
| FM01 | Missing sensor readings |
| FM02 | Invalid or noisy sensor readings |
| FM03 | High sensor risk but no concerning symptoms |
| FM04 | Low sensor risk but concerning symptoms reported |
| FM05 | Sensor and patient-reported symptoms both concerning |
| FM06 | Insufficient data to make a reliable decision |
| FM07 | Internet or network connectivity offline |
| FM08 | Communication to clinician fails |
| FM09 | Clinician capacity exceeded |
| FM10 | Recommendation cannot be trusted (safe fallback) |

---

## 3. Failure Mode Table

### FM01 – Missing Sensor Readings

| Field | Detail |
|---|---|
| **Possible Cause** | Sensor disconnection, device fault, or patient not wearing device |
| **Detection Method** | Data cleaning flags records as `Incomplete` when any sensor value is missing |
| **System Response** | Record marked `Incomplete`; risk cannot be reliably assessed; routed to `SAFE_FALLBACK` |
| **Safety Action** | Repeat measurement prompted; record is **never** silently classified as LOW risk |
| **Remaining Risk** | Patient may be missed during the gap in sensor data |
| **Measured Count** | **176 records** had at least one missing sensor value (280 total missing values) |
| **Status** | ✅ Handled |

---

### FM02 – Invalid or Noisy Sensor Readings

| Field | Detail |
|---|---|
| **Possible Cause** | Sensor calibration error, motion artefact, or data transmission error |
| **Detection Method** | Data cleaning checks for values outside prototype physiological ranges; flags as `Invalid` |
| **System Response** | Record marked `Invalid`; excluded from reliable risk assessment; repeat measurement requested |
| **Safety Action** | Repeat measurement required; clinician notified if high priority context |
| **Remaining Risk** | Threshold-based validation cannot catch all realistic edge cases |
| **Measured Count** | **25 Invalid records** detected |
| **Status** | ✅ Handled |

---

### FM03 – High Sensor Risk but No Concerning Symptoms

| Field | Detail |
|---|---|
| **Possible Cause** | Patient has not yet reported symptoms; early-stage condition; patient under-reporting |
| **Detection Method** | Conflict detection identifies `SENSOR-ONLY CONCERN` when risk is HIGH/CRITICAL but no symptoms present |
| **System Response** | Case escalated to `CLINICIAN_REVIEW`; sensor finding is **not** dismissed due to absence of symptoms |
| **Safety Action** | Clinician review and repeat measurement recommended |
| **Remaining Risk** | Patient may delay reporting symptoms; sensor reading could occasionally be spurious |
| **Measured Count** | **126 sensor-only concern cases** |
| **Status** | ✅ Handled |

---

### FM04 – Low Sensor Risk but Concerning Symptoms Reported

| Field | Detail |
|---|---|
| **Possible Cause** | Early-stage condition not yet visible in sensor readings; intermittent symptoms; measurement timing |
| **Detection Method** | Conflict detection identifies `SENSOR-SYMPTOM CONFLICT` when sensor is LOW/MEDIUM but patient reports headache, blurred vision, or bleeding |
| **System Response** | Priority upgraded to HIGH; routed to `CLINICIAN_REVIEW`; symptoms take precedence over sensor reading |
| **Safety Action** | Clinician review required; sensor result alone is **not** sufficient to reassure |
| **Remaining Risk** | Symptom self-reporting depends on patient awareness and honesty |
| **Measured Count** | **0 cases** in this simulated dataset (the simulation did not generate this combination) |
| **Status** | ✅ Handled (rule implemented and demonstrated in DEMO001) |

> **Note:** Although 0 cases of this type appear in the main simulated dataset,
> this scenario is fully demonstrated by DEMO001 (LOW sensor + headache + blurred vision → CLINICIAN_REVIEW).
> The detection and escalation logic is implemented and verified.

---

### FM05 – Sensor and Patient-Reported Symptoms Both Concerning

| Field | Detail |
|---|---|
| **Possible Cause** | Genuine high-risk clinical situation; severe or rapidly progressing condition |
| **Detection Method** | Risk level is HIGH/CRITICAL **and** patient reports concerning symptoms — both signals agree |
| **System Response** | Priority set to `CRITICAL`; routed to `URGENT_CLINICIAN_REVIEW` immediately |
| **Safety Action** | Urgent clinician review required; communication attempt initiated |
| **Remaining Risk** | Communication may fail or clinician capacity may be exceeded (see FM08, FM09) |
| **Measured Count** | **141 cases** with both sensor and symptoms concerning (all assigned CRITICAL priority) |
| **Status** | ✅ Handled |

---

### FM06 – Insufficient Data to Make a Reliable Decision

| Field | Detail |
|---|---|
| **Possible Cause** | Multiple sensor values missing; record quality too poor for safe assessment |
| **Detection Method** | Conflict detection marks record as `INSUFFICIENT DATA` when data quality is Incomplete/Invalid and key sensor values are absent |
| **System Response** | Priority set to `UNTRUSTED`; routed to `SAFE_FALLBACK`; recommendation explicitly marked as unreliable |
| **Safety Action** | Repeat measurement and clinician review requested; case is **never** silently classified as LOW risk |
| **Remaining Risk** | Patient could be at risk if repeat measurement is not performed promptly |
| **Measured Count** | **176 cases** marked as INSUFFICIENT DATA / UNTRUSTED |
| **Status** | ✅ Handled |

---

### FM07 – Internet or Network Connectivity Offline

| Field | Detail |
|---|---|
| **Possible Cause** | Remote area with no signal; network outage; device connectivity fault |
| **Detection Method** | `internet_status` field checked at time of escalation; `Offline` status detected before communication |
| **System Response** | Case stored locally using store-and-forward mechanism; record is **not** discarded |
| **Safety Action** | Case stored locally; forwarded when connectivity returns |
| **Remaining Risk** | Delay in clinician receiving an urgent case during offline period; forwarding depends on connectivity recovery |
| **Measured Count** | **153 offline cases** detected; **94 cases** stored for forward |
| **Status** | ⚠️ Partially Handled |

> **Partially Handled because:** The system correctly saves offline cases, but a
> real store-and-forward implementation would require actual local storage and
> automatic retry logic. In this prototype, store-and-forward is simulated.

---

### FM08 – Communication to Clinician Fails

| Field | Detail |
|---|---|
| **Possible Cause** | Network error after first attempt; clinician device unreachable; message delivery failure |
| **Detection Method** | `communication_result` column records the outcome of each attempt; `FAILED` status is logged |
| **System Response** | Failure is logged; offline cases stored for forward; no silent failure |
| **Safety Action** | Failure recorded; case remains in escalation queue; retry logic is a future improvement |
| **Remaining Risk** | Clinician may not be aware of urgent case if all retry attempts fail |
| **Measured Count** | **81 communication failures** recorded |
| **Status** | ⚠️ Partially Handled |

> **Partially Handled because:** The system detects and logs communication failure,
> but does not implement automatic multi-attempt retry or escalation to a backup
> contact. These are future improvements.

---

### FM09 – Clinician Capacity Exceeded

| Field | Detail |
|---|---|
| **Possible Cause** | High volume of simultaneous HIGH/CRITICAL cases; limited clinician availability in remote setting |
| **Detection Method** | Capacity rule: first 10 HIGH/CRITICAL cases per cycle = `WITHIN_CAPACITY`; remaining = `QUEUED` |
| **System Response** | Cases beyond capacity are marked `QUEUED` and assigned to next available slot; they are **not** discarded |
| **Safety Action** | Queued cases scheduled for next review cycle; priority level is preserved |
| **Remaining Risk** | Queued CRITICAL cases may experience a clinically significant review delay |
| **Measured Count** | **257 cases queued** (only **10 within immediate capacity**) |
| **Status** | ⚠️ Partially Handled |

> **Partially Handled because:** The queue preserves all cases and their priority,
> but does not implement adaptive capacity (e.g. dynamic load balancing across
> multiple clinicians). In this prototype, a fixed limit of 10 is applied once.

---

### FM10 – Recommendation Cannot Be Trusted (Safe Fallback)

| Field | Detail |
|---|---|
| **Possible Cause** | Data quality is Incomplete or Invalid; key measurements absent; conflicting signals with no reliable resolution |
| **Detection Method** | Priority set to `UNTRUSTED` when data quality prevents reliable risk classification |
| **System Response** | Escalation path set to `SAFE_FALLBACK`; recommendation explicitly flagged as unreliable |
| **Safety Action** | System **never** silently classifies an unreliable record as LOW risk; safe fallback always raises awareness |
| **Remaining Risk** | Relies on the health worker or clinician acting on the safe fallback alert |
| **Measured Count** | **176 safe fallback cases** triggered |
| **Status** | ✅ Handled |

---

## 4. Measured Results (from Existing Data)

All counts are taken from the existing Phase 2–7 CSV outputs (994 simulated records).

| Metric | Count |
|---|---|
| Total records processed | 994 |
| Records with ≥ 1 missing sensor value | 176 |
| Total missing sensor values | 280 |
| Invalid records (out-of-range values) | 25 |
| Incomplete records (missing values) | 151 |
| Sensor-only concern cases | 126 |
| Sensor-symptom conflict cases | 0 |
| Cases with both signals concerning (CRITICAL) | 141 |
| Insufficient data / UNTRUSTED cases | 176 |
| Offline cases detected | 153 |
| Store-and-forward stored | 94 |
| Communication failures | 81 |
| Capacity queued cases | 257 |
| Safe fallback cases | 176 |

---

## 5. Safety Responses Summary

| Status | Count | Failure Modes |
|---|---|---|
| ✅ **Handled** | 7 | FM01, FM02, FM03, FM04, FM05, FM06, FM10 |
| ⚠️ **Partially Handled** | 3 | FM07, FM08, FM09 |
| 🔧 **Future Improvement** | 0 | — |

**Key safety principles applied in this prototype:**

1. **No silent LOW-risk classification** — Incomplete, Invalid, or UNTRUSTED records are never classified as LOW risk.
2. **Symptoms override sensors** — A low sensor reading does not override concerning patient-reported symptoms.
3. **No silent discard** — Offline cases and communication failures are logged and stored, never silently dropped.
4. **Explicit uncertainty** — When a decision cannot be trusted, this is stated explicitly and a safe fallback is triggered.

---

## 6. Limitations

1. **Simulated data only** — all 994 records are generated, not from real patients.
2. **No clinical validation** — thresholds and rules are simplified for educational demonstration.
3. **Single review cycle** — the capacity rule (limit = 10) is applied once; a real system operates continuously.
4. **No real network** — store-and-forward and communication are simulated in Python, not real networking.
5. **No retry logic** — communication failures are logged but there is no automatic retry in this prototype.
6. **No adaptive capacity** — the fixed capacity limit of 10 does not adapt to the number of available clinicians.
7. **Patient self-reporting** — the system cannot verify patient-reported symptoms; under-reporting is a real risk.
8. **FM04 gap in simulation** — no sensor-symptom conflicts appeared in the main dataset (0 cases); this scenario is demonstrated only in DEMO001.

---

## 7. Future Improvements

| Priority | Improvement |
|---|---|
| High | Implement automatic communication retry (e.g. 3 attempts before escalating to backup contact) |
| High | Implement real local storage for offline store-and-forward (e.g. SQLite) |
| High | Add adaptive capacity management (load balancing across multiple clinicians) |
| Medium | Add wearable sensor validation (e.g. cross-check multiple sensor readings) |
| Medium | Detect and flag repeated failed measurements as a separate failure mode |
| Medium | Add patient education alerts for under-reported symptoms |
| Low | Add audit trail logging for all escalation decisions |
| Low | Add time-stamped retry log for communication failures |

---

## 8. How to Reproduce

```bash
# From the maternal_health_monitoring/ folder:
python experiments/failure_mode_analysis.py
```

**Output files:**
- `experiments/failure_mode_results.csv` — 10-row failure mode table
- `experiments/failure_mode_summary.csv` — single-row flat summary of all counts

---

## 9. Files Referenced

| File | Purpose |
|---|---|
| `data/cleaned_maternal_data.csv` | Source for FM01, FM02 counts |
| `data/baseline_risk_results.csv` | Baseline risk distribution |
| `data/conflict_results.csv` | Source for FM03, FM04, FM06 counts |
| `data/escalation_results.csv` | Source for FM05, FM07, FM08, FM09, FM10 counts |
| `data/demo_conflict_cases.csv` | Verification of FM04 (DEMO001) |
| `experiments/failure_mode_analysis.py` | Script that produces this analysis |
| `experiments/failure_mode_results.csv` | Machine-readable failure mode table |
| `experiments/failure_mode_summary.csv` | Flat summary of all measured counts |
