# experiments/failure_mode_analysis.py
# Phase 10 – Failure Mode Analysis
# Remote Maternal Health Monitoring and Escalation System
#
# PURPOSE:
#   Analyse the failure modes of the Phase 2-7 system using existing CSV outputs.
#   Identifies how each failure mode is detected and handled.
#   Produces a terminal summary and saves results to failure_mode_results.csv.
#
# HOW TO RUN:
#   python experiments/failure_mode_analysis.py
#   (Run from the maternal_health_monitoring/ project folder)
#
# REQUIREMENTS:
#   All Phase 2-7 CSV files must already exist in data/
#
# NOTE:
#   - Uses only pandas and simple Python logic
#   - No machine learning, no complex algorithms
#   - All data is simulated and anonymous (educational prototype only)

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR     = os.path.join(PROJECT_ROOT, "data")
DOCS_DIR     = os.path.join(PROJECT_ROOT, "docs")
OUTPUT_DIR   = os.path.dirname(os.path.abspath(__file__))   # experiments/
OUTPUT_CSV   = os.path.join(OUTPUT_DIR, "failure_mode_results.csv")

sys.path.insert(0, PROJECT_ROOT)


# ---------------------------------------------------------------------------
# HELPER: LOAD CSV SAFELY
# ---------------------------------------------------------------------------

def load_csv(filename):
    """Load a CSV from the data/ folder. Exit with a clear message if missing."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"\n[ERROR] Required file not found: {path}")
        print("        Please run the Phase 2-7 pipeline first.")
        sys.exit(1)
    return pd.read_csv(path)


def safe_count(series, key):
    """Return count for a key from a pandas Series, or 0 if not present."""
    return int(series.value_counts().get(key, 0))


def divider(char="=", width=54):
    print(char * width)


def section(title):
    print()
    divider()
    print(f"  {title}")
    divider()


def row_print(label, value, indent=4):
    spaces = " " * indent
    print(f"{spaces}{label:<42} {value}")


# ---------------------------------------------------------------------------
# LOAD DATA FILES
# ---------------------------------------------------------------------------

print()
print("Loading data files...")

cleaned    = load_csv("cleaned_maternal_data.csv")
baseline   = load_csv("baseline_risk_results.csv")
conflict   = load_csv("conflict_results.csv")
escalation = load_csv("escalation_results.csv")
demo_cases = load_csv("demo_conflict_cases.csv")

print(f"  cleaned_maternal_data.csv    : {len(cleaned)} rows")
print(f"  baseline_risk_results.csv   : {len(baseline)} rows")
print(f"  conflict_results.csv        : {len(conflict)} rows")
print(f"  escalation_results.csv      : {len(escalation)} rows")
print(f"  demo_conflict_cases.csv     : {len(demo_cases)} rows")


# ---------------------------------------------------------------------------
# MEASURE COUNTS FROM EXISTING DATA
# ---------------------------------------------------------------------------

total_records = len(escalation)

# -- FM01: Missing sensor readings --
sensor_cols = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "spo2"]
existing_sensor_cols = [c for c in sensor_cols if c in cleaned.columns]
rows_with_any_missing = int(cleaned[existing_sensor_cols].isna().any(axis=1).sum())
missing_value_total   = int(cleaned[existing_sensor_cols].isna().sum().sum())

# -- FM02: Invalid/noisy sensor records --
invalid_records  = safe_count(cleaned["data_quality"], "Invalid") \
    if "data_quality" in cleaned.columns else 0
incomplete_records = safe_count(cleaned["data_quality"], "Incomplete") \
    if "data_quality" in cleaned.columns else 0

# -- FM03: High sensor risk but no concerning symptoms (sensor-only concern) --
sensor_only_count = safe_count(conflict["conflict_status"], "SENSOR-ONLY CONCERN") \
    if "conflict_status" in conflict.columns else 0

# -- FM04: Low sensor risk but concerning symptoms (sensor-symptom conflict) --
sensor_symptom_conflict = safe_count(conflict["conflict_status"], "SENSOR-SYMPTOM CONFLICT") \
    if "conflict_status" in conflict.columns else 0

# -- FM05: Both sensor and symptoms concerning --
both_concerning = len(escalation[
    (escalation["risk_level"].isin(["HIGH", "CRITICAL"])) &
    (escalation["concerning_symptoms"].notna()) &
    (escalation["concerning_symptoms"].str.strip() != "")
]) if "concerning_symptoms" in escalation.columns else 0

# -- FM06: Insufficient data --
insuff_data = safe_count(conflict["conflict_status"], "INSUFFICIENT DATA") \
    if "conflict_status" in conflict.columns else 0
untrusted   = safe_count(escalation["priority"], "UNTRUSTED") \
    if "priority" in escalation.columns else 0

# -- FM07: Internet/network offline --
offline_count = safe_count(escalation["internet_status"], "Offline") \
    if "internet_status" in escalation.columns else 0
stored_count  = safe_count(escalation["store_forward_status"], "STORED") \
    if "store_forward_status" in escalation.columns else 0

# -- FM08: Communication failure --
comm_failed = safe_count(
    escalation["communication_result"],
    "First communication attempt failed."
) if "communication_result" in escalation.columns else 0
comm_pending = safe_count(
    escalation["communication_result"], "Clinician contact pending."
) if "communication_result" in escalation.columns else 0
comm_completed = safe_count(
    escalation["communication_result"], "Clinician contact completed."
) if "communication_result" in escalation.columns else 0

# -- FM09: Clinician capacity exceeded --
capacity_queued = safe_count(escalation["capacity_status"], "QUEUED") \
    if "capacity_status" in escalation.columns else 0
within_cap      = safe_count(escalation["capacity_status"], "WITHIN_CAPACITY") \
    if "capacity_status" in escalation.columns else 0

# -- FM10: Recommendation cannot be trusted --
safe_fallback = safe_count(escalation["escalation_path"], "SAFE_FALLBACK") \
    if "escalation_path" in escalation.columns else 0


# ---------------------------------------------------------------------------
# DEFINE FAILURE MODES
# Each failure mode has:
#   id, scenario, possible_cause, detection_method,
#   system_response, safety_action, remaining_risk,
#   count (measured from data), status
# ---------------------------------------------------------------------------

failure_modes = [
    {
        "failure_id":       "FM01",
        "scenario":         "Missing sensor readings",
        "possible_cause":   "Sensor disconnection, device fault, or patient not wearing device",
        "detection_method": "Data cleaning flags records as Incomplete when any sensor value is NaN",
        "system_response":  "Record marked Incomplete; risk cannot be reliably assessed; "
                            "escalation path set to SAFE_FALLBACK",
        "safety_action":    "Prompt repeat measurement; do NOT classify as LOW risk; "
                            "route to SAFE_FALLBACK",
        "remaining_risk":   "Patient may be missed during the gap in sensor data",
        "count":            rows_with_any_missing,
        "count_label":      "Records with >= 1 missing sensor value",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM02",
        "scenario":         "Invalid or noisy sensor readings",
        "possible_cause":   "Sensor calibration error, motion artefact, or data transmission error",
        "detection_method": "Data cleaning checks for values outside physiological prototype ranges "
                            "(e.g. systolic BP < 50 or > 250) and flags records as Invalid",
        "system_response":  "Record marked Invalid; excluded from reliable risk assessment; "
                            "prompted for repeat measurement",
        "safety_action":    "Repeat measurement requested; clinician notified if high priority",
        "remaining_risk":   "Threshold-based validation cannot catch all realistic edge cases",
        "count":            invalid_records,
        "count_label":      "Invalid records (out-of-range sensor values)",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM03",
        "scenario":         "High sensor risk but no concerning symptoms reported",
        "possible_cause":   "Patient has not reported symptoms yet; early-stage condition; "
                            "patient under-reporting",
        "detection_method": "Conflict detection identifies SENSOR-ONLY CONCERN when risk level "
                            "is HIGH/CRITICAL but no concerning symptoms are present",
        "system_response":  "Case escalated to CLINICIAN_REVIEW despite absence of symptoms; "
                            "sensor finding is NOT dismissed",
        "safety_action":    "Clinician review requested; repeat measurement recommended",
        "remaining_risk":   "Patient may delay reporting symptoms; sensor reading could be spurious",
        "count":            sensor_only_count,
        "count_label":      "Sensor-only concern cases",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM04",
        "scenario":         "Low sensor risk but concerning symptoms reported",
        "possible_cause":   "Early-stage condition not yet reflected in sensor readings; "
                            "intermittent symptoms; sensor measurement timing",
        "detection_method": "Conflict detection identifies SENSOR-SYMPTOM CONFLICT when "
                            "sensor shows LOW/MEDIUM but patient reports headache, blurred "
                            "vision, or bleeding",
        "system_response":  "Priority upgraded to HIGH; routed to CLINICIAN_REVIEW; "
                            "symptoms take precedence over sensor reading",
        "safety_action":    "Clinician review required; sensor result alone is not sufficient "
                            "to reassure",
        "remaining_risk":   "Symptom self-reporting relies on patient honesty and awareness",
        "count":            sensor_symptom_conflict,
        "count_label":      "Sensor-symptom conflict cases",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM05",
        "scenario":         "Sensor and patient-reported symptoms both concerning",
        "possible_cause":   "Genuine high-risk clinical situation; severe or rapidly progressing condition",
        "detection_method": "Both risk_level is HIGH/CRITICAL AND patient reports concerning symptoms; "
                            "conflict module identifies agreement between both signals",
        "system_response":  "Priority set to CRITICAL; routed to URGENT_CLINICIAN_REVIEW immediately",
        "safety_action":    "Urgent clinician review required; communication attempt initiated",
        "remaining_risk":   "Communication may fail or clinician capacity may be exceeded",
        "count":            both_concerning,
        "count_label":      "Cases with both sensor + symptoms concerning",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM06",
        "scenario":         "Insufficient data to make a reliable decision",
        "possible_cause":   "Multiple sensor values missing; record quality too poor "
                            "for safe assessment",
        "detection_method": "Conflict detection marks record as INSUFFICIENT DATA when "
                            "data quality is Incomplete/Invalid and key sensor values are absent",
        "system_response":  "Priority set to UNTRUSTED; routed to SAFE_FALLBACK; "
                            "recommendation explicitly marked as unreliable",
        "safety_action":    "Repeat measurement and clinician review requested; "
                            "case is never silently classified as LOW risk",
        "remaining_risk":   "Patient could be harmed if repeat measurement is not performed promptly",
        "count":            insuff_data,
        "count_label":      "Insufficient data / UNTRUSTED cases",
        "status":           "Handled",
    },
    {
        "failure_id":       "FM07",
        "scenario":         "Internet or network connectivity offline",
        "possible_cause":   "Remote area with no signal; network outage; device connectivity fault",
        "detection_method": "internet_status column checked at time of escalation attempt; "
                            "Offline detected before communication is attempted",
        "system_response":  "Case stored locally using store-and-forward mechanism; "
                            "record is NOT discarded and NOT classified as LOW risk",
        "safety_action":    "Case stored locally; forwarded automatically when connectivity returns",
        "remaining_risk":   "Delay in clinician receiving urgent case during offline period",
        "count":            offline_count,
        "count_label":      "Offline cases detected",
        "status":           "Partially Handled",
    },
    {
        "failure_id":       "FM08",
        "scenario":         "Communication to clinician fails",
        "possible_cause":   "Network error after first attempt; clinician device unreachable; "
                            "message delivery failure",
        "detection_method": "communication_result column records the outcome of each attempt; "
                            "FAILED status is logged",
        "system_response":  "Failure is logged in communication_result; offline cases "
                            "are stored for forward; no silent failure",
        "safety_action":    "Communication failure is recorded; case remains in the escalation "
                            "queue; retry on next cycle is a future improvement",
        "remaining_risk":   "Clinician may not be aware of urgent case if all retry attempts fail",
        "count":            comm_failed,
        "count_label":      "Communication failed cases",
        "status":           "Partially Handled",
    },
    {
        "failure_id":       "FM09",
        "scenario":         "Clinician capacity exceeded (too many urgent cases)",
        "possible_cause":   "High volume of simultaneous HIGH/CRITICAL cases; limited clinician "
                            "availability in remote setting",
        "detection_method": "Capacity rule applied after escalation: first 10 HIGH/CRITICAL "
                            "cases = WITHIN_CAPACITY; remaining = QUEUED",
        "system_response":  "Cases beyond capacity are marked QUEUED and assigned to the next "
                            "available review slot; they are NOT discarded",
        "safety_action":    "Queued cases scheduled for the next review cycle; priority is preserved",
        "remaining_risk":   "Queued CRITICAL cases may experience a dangerous review delay",
        "count":            capacity_queued,
        "count_label":      "Cases queued due to capacity limit",
        "status":           "Partially Handled",
    },
    {
        "failure_id":       "FM10",
        "scenario":         "Recommendation cannot be trusted (safe fallback triggered)",
        "possible_cause":   "Data quality is Incomplete or Invalid; key measurements are absent; "
                            "conflicting signals with no reliable resolution",
        "detection_method": "Priority set to UNTRUSTED when data quality flags prevent reliable "
                            "risk classification",
        "system_response":  "Escalation path set to SAFE_FALLBACK; recommendation explicitly "
                            "flagged as unreliable; clinician and repeat measurement requested",
        "safety_action":    "System never silently classifies an unreliable record as LOW risk; "
                            "safe fallback always raises awareness",
        "remaining_risk":   "Relies on clinician or health worker acting on the safe fallback alert",
        "count":            safe_fallback,
        "count_label":      "Safe fallback cases triggered",
        "status":           "Handled",
    },
]


# ---------------------------------------------------------------------------
# PRINT TERMINAL REPORT
# ---------------------------------------------------------------------------

section("PHASE 10 - FAILURE MODE ANALYSIS")
print(f"  Dataset: {total_records} simulated anonymous records")
print(f"  Failure modes analysed: {len(failure_modes)}")
print()
print("  DISCLAIMER: This is an educational prototype using simulated")
print("  anonymous data. Not for real clinical use.")

# ------------------------------------------------------------------
section("FAILURE MODE DETAILS")

for fm in failure_modes:
    print()
    print(f"  [{fm['failure_id']}]  {fm['scenario']}")
    print(f"    Count          : {fm['count']} {fm['count_label']}")
    print(f"    Possible Cause : {fm['possible_cause']}")
    print(f"    Detection      : {fm['detection_method']}")
    print(f"    System Response: {fm['system_response']}")
    print(f"    Safety Action  : {fm['safety_action']}")
    print(f"    Remaining Risk : {fm['remaining_risk']}")
    print(f"    Status         : {fm['status']}")

# ------------------------------------------------------------------
section("SUMMARY")

status_counts = {}
for fm in failure_modes:
    s = fm["status"]
    status_counts[s] = status_counts.get(s, 0) + 1

row_print("Total failure modes analysed:", len(failure_modes))
row_print("Handled:",           status_counts.get("Handled", 0))
row_print("Partially Handled:", status_counts.get("Partially Handled", 0))
row_print("Future Improvement:",status_counts.get("Future Improvement", 0))
print()
print("    Important case counts (from existing data):")
row_print("Rows with missing sensor data:",    rows_with_any_missing)
row_print("Invalid records:",                  invalid_records)
row_print("Incomplete records:",               incomplete_records)
row_print("Sensor-only concerns:",             sensor_only_count)
row_print("Sensor-symptom conflicts:",         sensor_symptom_conflict)
row_print("Both signals concerning:",          both_concerning)
row_print("Insufficient data / UNTRUSTED:",    insuff_data)
row_print("Offline cases:",                    offline_count)
row_print("Store-and-forward (stored):",       stored_count)
row_print("Communication failures:",           comm_failed)
row_print("Capacity queued cases:",            capacity_queued)
row_print("Safe fallback cases:",              safe_fallback)

print()
divider()


# ---------------------------------------------------------------------------
# SAVE FAILURE MODE RESULTS TO CSV
# ---------------------------------------------------------------------------

# Build a clean DataFrame — drop the nested count_label, keep what's useful
save_records = []
for fm in failure_modes:
    save_records.append({
        "failure_id":       fm["failure_id"],
        "scenario":         fm["scenario"],
        "possible_cause":   fm["possible_cause"],
        "detection_method": fm["detection_method"],
        "system_response":  fm["system_response"],
        "safety_action":    fm["safety_action"],
        "remaining_risk":   fm["remaining_risk"],
        "measured_count":   fm["count"],
        "count_label":      fm["count_label"],
        "status":           fm["status"],
    })

fm_df = pd.DataFrame(save_records)
fm_df.to_csv(OUTPUT_CSV, index=False)
print()
print(f"  Failure mode results saved to: {OUTPUT_CSV}")

# Also save a flat summary row alongside the failure mode table
summary_csv = os.path.join(OUTPUT_DIR, "failure_mode_summary.csv")
summary = {
    "total_failure_modes":          len(failure_modes),
    "status_handled":               status_counts.get("Handled", 0),
    "status_partially_handled":     status_counts.get("Partially Handled", 0),
    "status_future_improvement":    status_counts.get("Future Improvement", 0),
    "total_records":                total_records,
    "missing_sensor_rows":          rows_with_any_missing,
    "invalid_records":              invalid_records,
    "incomplete_records":           incomplete_records,
    "sensor_only_concerns":         sensor_only_count,
    "sensor_symptom_conflicts":     sensor_symptom_conflict,
    "both_signals_concerning":      both_concerning,
    "insufficient_data_cases":      insuff_data,
    "offline_cases":                offline_count,
    "store_forward_stored":         stored_count,
    "communication_failed":         comm_failed,
    "capacity_queued":              capacity_queued,
    "safe_fallback_cases":          safe_fallback,
}
pd.DataFrame([summary]).to_csv(summary_csv, index=False)
print(f"  Summary stats saved to:        {summary_csv}")

print()
print("=" * 54)
print("  PHASE 10 COMPLETE")
print("=" * 54)
print(f"  Failure modes analysed : {len(failure_modes)}")
print(f"  Handled                : {status_counts.get('Handled', 0)}")
print(f"  Partially Handled      : {status_counts.get('Partially Handled', 0)}")
print(f"  Future Improvement     : {status_counts.get('Future Improvement', 0)}")
print()
print("  This analysis used only existing CSV files.")
print("  No machine learning or complex algorithms were used.")
print()
print("  DISCLAIMER: Educational prototype using simulated")
print("  anonymous data. Not for real clinical use.")
print()
