# experiments/run_experiment.py
# Phase 9 – Experiment and Evaluation
# Remote Maternal Health Monitoring and Escalation System
#
# PURPOSE:
#   Evaluate the full Phase 2-7 workflow using existing simulated data.
#   Produces a clear terminal report and saves results to experiment_results.csv.
#
# HOW TO RUN:
#   python experiments/run_experiment.py
#
# REQUIREMENTS:
#   - Run from the maternal_health_monitoring/ project folder
#   - All Phase 2-7 CSV files must already exist in data/
#
# NOTE:
#   - Uses only pandas and simple Python logic
#   - No machine learning, no complex algorithms
#   - All patient data is simulated and anonymous

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------
# Make sure we can import project modules from the parent folder
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

DATA_DIR    = os.path.join(PROJECT_ROOT, "data")
OUTPUT_DIR  = os.path.dirname(os.path.abspath(__file__))  # experiments/
OUTPUT_CSV  = os.path.join(OUTPUT_DIR, "experiment_results.csv")

# ---------------------------------------------------------------------------
# HELPER: LOAD CSV SAFELY
# ---------------------------------------------------------------------------

def load_csv(filename):
    """Load a CSV from the data/ folder. Exit with a clear message if missing."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        print(f"\n[ERROR] Required file not found: {path}")
        print("        Please run the Phase 2-7 pipeline first.")
        print("        python generate_data.py -> clean_data.py -> risk_detection.py")
        print("        -> trend_analysis.py -> conflict_detection.py -> escalation_workflow.py")
        sys.exit(1)
    return pd.read_csv(path)


def safe_count(series, key):
    """Return count of a key in a value_counts Series, or 0 if missing."""
    counts = series.value_counts()
    return int(counts.get(key, 0))


def section(title):
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def row(label, value, indent=4):
    """Print a labelled metric row."""
    spaces = " " * indent
    print(f"{spaces}{label:<40} {value}")


# ---------------------------------------------------------------------------
# LOAD ALL DATA FILES
# ---------------------------------------------------------------------------

print()
print("Loading data files...")

baseline   = load_csv("baseline_risk_results.csv")
conflict   = load_csv("conflict_results.csv")
escalation = load_csv("escalation_results.csv")
trend      = load_csv("trend_results.csv")
demo_cases = load_csv("demo_conflict_cases.csv")

print(f"  baseline_risk_results.csv  : {len(baseline)} rows")
print(f"  conflict_results.csv       : {len(conflict)} rows")
print(f"  escalation_results.csv     : {len(escalation)} rows")
print(f"  trend_results.csv          : {len(trend)} rows")
print(f"  demo_conflict_cases.csv    : {len(demo_cases)} rows")


# ---------------------------------------------------------------------------
# SECTION 1 – EXPERIMENT SUMMARY (overview of the dataset)
# ---------------------------------------------------------------------------

section("EXPERIMENT SUMMARY")

total_records   = len(escalation)
unique_patients = escalation["patient_id"].nunique() \
    if "patient_id" in escalation.columns else 0

# Data quality breakdown
if "data_quality" in escalation.columns:
    dq = escalation["data_quality"].value_counts()
    good       = safe_count(escalation["data_quality"], "Good")
    incomplete = safe_count(escalation["data_quality"], "Incomplete")
    invalid    = safe_count(escalation["data_quality"], "Invalid")
else:
    good = incomplete = invalid = 0

# Missing sensor values
sensor_cols = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "spo2"]
existing    = [c for c in sensor_cols if c in escalation.columns]
missing_values = int(escalation[existing].isna().sum().sum())

row("Total observations processed:", total_records)
row("Unique anonymous patients:",    unique_patients)
row("Good quality records:",         good)
row("Incomplete records:",           incomplete)
row("Invalid records:",              invalid)
row("Total missing sensor values:",  missing_values)
row("Trend-analysed patients:",      len(trend))


# ---------------------------------------------------------------------------
# SECTION 2 – BASELINE RESULTS (Phase 4 risk detection only)
# ---------------------------------------------------------------------------

section("BASELINE RESULTS  (Phase 4 Risk Detection Only)")
print("    The baseline uses sensor readings + data quality only.")
print("    It does NOT consider symptoms, trends, or conflicts.")
print()

if "risk_level" in baseline.columns:
    row("LOW risk (sensor only):",      safe_count(baseline["risk_level"], "LOW"))
    row("MEDIUM risk (sensor only):",   safe_count(baseline["risk_level"], "MEDIUM"))
    row("HIGH risk (sensor only):",     safe_count(baseline["risk_level"], "HIGH"))
    row("CRITICAL risk (sensor only):", safe_count(baseline["risk_level"], "CRITICAL"))
    row("UNCERTAIN risk (sensor only):", safe_count(baseline["risk_level"], "UNCERTAIN"))

if "recommended_action" in baseline.columns:
    print()
    print("    Baseline recommended actions:")
    for action, count in baseline["recommended_action"].value_counts().items():
        row(str(action) + ":", count, indent=6)

# Map baseline recommended_action to a decision category for comparison
def map_baseline_action(action):
    """Map raw baseline action text to a decision category."""
    a = str(action).lower()
    if "continue" in a:
        return "CONTINUE_MONITORING"
    elif "immediate" in a:
        return "URGENT_CLINICIAN_REVIEW"
    elif "clinician" in a:
        return "CLINICIAN_REVIEW"
    elif "schedule" in a or "follow" in a:
        return "SCHEDULE_FOLLOW_UP"
    elif "repeat" in a or "missing" in a:
        return "SAFE_FALLBACK"
    else:
        return "OTHER"

baseline["baseline_decision"] = baseline["recommended_action"].apply(map_baseline_action)

baseline_decision_counts = baseline["baseline_decision"].value_counts().to_dict()


# ---------------------------------------------------------------------------
# SECTION 3 – FINAL WORKFLOW RESULTS (after Phases 5, 6, 7)
# ---------------------------------------------------------------------------

section("FINAL WORKFLOW RESULTS  (After Phases 5-7)")
print("    The full workflow adds: symptom reconciliation, trend analysis,")
print("    conflict detection, escalation routing, and capacity management.")
print()

if "priority" in escalation.columns:
    low      = safe_count(escalation["priority"], "LOW")
    medium   = safe_count(escalation["priority"], "MEDIUM")
    high     = safe_count(escalation["priority"], "HIGH")
    critical = safe_count(escalation["priority"], "CRITICAL")
    untrust  = safe_count(escalation["priority"], "UNTRUSTED")

    row("LOW priority:",       low)
    row("MEDIUM priority:",    medium)
    row("HIGH priority:",      high)
    row("CRITICAL priority:",  critical)
    row("UNTRUSTED priority:", untrust)
    print()

if "escalation_path" in escalation.columns:
    print("    Escalation pathway distribution:")
    for path, count in escalation["escalation_path"].value_counts().items():
        row(str(path) + ":", count, indent=6)


# ---------------------------------------------------------------------------
# SECTION 4 – BASELINE vs FINAL WORKFLOW COMPARISON
# ---------------------------------------------------------------------------

section("BASELINE vs FINAL WORKFLOW COMPARISON")
print("    Comparing the decision category before and after the full workflow.")
print()

# Merge baseline decisions with final escalation paths
merged = baseline[["patient_id", "observation_day", "baseline_decision"]].merge(
    escalation[["patient_id", "observation_day", "escalation_path", "priority"]],
    on=["patient_id", "observation_day"],
    how="inner",
)

merged["decision_changed"] = merged["baseline_decision"] != merged["escalation_path"]
same    = int((~merged["decision_changed"]).sum())
changed = int(merged["decision_changed"].sum())

row("Decisions unchanged after full workflow:", same)
row("Decisions changed by full workflow:",      changed)
print()

# Count specific types of changes
# Cases upgraded (escalated higher) by conflict/trend detection
upgraded = merged[
    (merged["baseline_decision"] == "CLINICIAN_REVIEW") &
    (merged["escalation_path"]   == "URGENT_CLINICIAN_REVIEW")
]

# Cases that became SAFE_FALLBACK (data quality flagged as untrusted)
became_safe_fallback = merged[
    (merged["baseline_decision"] != "SAFE_FALLBACK") &
    (merged["escalation_path"]   == "SAFE_FALLBACK")
]

row("Cases escalated to URGENT_CLINICIAN_REVIEW:", len(upgraded))
row("Cases routed to SAFE_FALLBACK (untrusted):",  len(became_safe_fallback))
print()
print("    Note: The full workflow adds symptom reconciliation, trend detection,")
print("    conflict detection, and capacity management – giving a more complete")
print("    clinical picture than sensor data alone.")


# ---------------------------------------------------------------------------
# SECTION 5 – EDGE CASE RESULTS (6 Demonstration Cases)
# ---------------------------------------------------------------------------

section("EDGE CASE RESULTS  (Demonstration Cases)")
print("    The 6 demonstration cases are hand-crafted to cover every scenario.")
print("    Each case has an expected escalation pathway defined in the design.")
print()

# Import workflow modules to run demo cases through the pipeline
try:
    from conflict_detection import detect_conflict
    from escalation_workflow import assign_priority, assign_escalation_path
    modules_available = True
except ImportError:
    modules_available = False
    print("    [WARNING] Could not import project modules.")
    print("    Run this script from the maternal_health_monitoring/ folder.")

# Expected pathways for each demo case
# Based on system design (Phase 6-7 rules)
expected_pathways = {
    "DEMO001": "CLINICIAN_REVIEW",           # Sensor-symptom conflict -> Clinician Review
    "DEMO002": "CLINICIAN_REVIEW",           # Sensor-only concern -> Clinician Review
    "DEMO003": "URGENT_CLINICIAN_REVIEW",    # Both signals concerning -> Urgent
    "DEMO004": "SAFE_FALLBACK",              # Incomplete data -> Safe Fallback
    "DEMO005": "CONTINUE_MONITORING",        # No conflict, low risk -> Continue
    "DEMO006": "URGENT_CLINICIAN_REVIEW",    # Critical + offline -> Urgent + Store-Forward
}

demo_results = []
correct = 0
total_demo = len(demo_cases)

if modules_available:
    for _, demo_row in demo_cases.iterrows():
        r = demo_row.to_dict()
        pid = str(r.get("patient_id", ""))

        # Run conflict detection
        conflict_result = detect_conflict(r)
        r.update(conflict_result)

        # Run escalation
        priority        = assign_priority(r)
        escalation_path = assign_escalation_path(priority)

        expected = expected_pathways.get(pid, "UNKNOWN")
        matched  = (escalation_path == expected)
        if matched:
            correct += 1
        status = "PASS" if matched else "FAIL"

        print(f"    {pid}:")
        print(f"      Risk Level    : {r.get('risk_level', 'N/A')}")
        print(f"      Conflict      : {r.get('conflict_status', 'N/A')}")
        print(f"      Priority      : {priority}")
        print(f"      Actual path   : {escalation_path}")
        print(f"      Expected path : {expected}")
        print(f"      Result        : [{status}]")
        print()

        demo_results.append({
            "patient_id":       pid,
            "risk_level":       r.get("risk_level", "N/A"),
            "conflict_status":  r.get("conflict_status", "N/A"),
            "priority":         priority,
            "actual_path":      escalation_path,
            "expected_path":    expected,
            "result":           status,
        })

    accuracy = (correct / total_demo) * 100
    row("Demonstration cases tested:", total_demo)
    row("Correctly routed:",           correct)
    row("Incorrectly routed:",         total_demo - correct)
    row("Edge Case Routing Accuracy:", f"{accuracy:.1f}%")

else:
    # Fallback: just show demo cases without running through modules
    for _, demo_row in demo_cases.iterrows():
        pid = str(demo_row.get("patient_id", ""))
        expected = expected_pathways.get(pid, "UNKNOWN")
        print(f"    {pid}: Expected -> {expected}")
        demo_results.append({
            "patient_id":      pid,
            "risk_level":      demo_row.get("risk_level", "N/A"),
            "conflict_status": "NOT_RUN",
            "priority":        "NOT_RUN",
            "actual_path":     "NOT_RUN",
            "expected_path":   expected,
            "result":          "NOT_RUN",
        })
    accuracy = 0.0

demo_df = pd.DataFrame(demo_results)


# ---------------------------------------------------------------------------
# SECTION 6 – CONFLICT DETECTION RESULTS
# ---------------------------------------------------------------------------

section("CONFLICT DETECTION RESULTS")
print("    Conflict detection checks whether sensor readings and reported")
print("    symptoms agree. Mismatches are flagged for clinician attention.")
print()

if "conflict_status" in conflict.columns:
    no_conflict    = safe_count(conflict["conflict_status"], "NO CONFLICT")
    sensor_symptom = safe_count(conflict["conflict_status"], "SENSOR-SYMPTOM CONFLICT")
    sensor_only    = safe_count(conflict["conflict_status"], "SENSOR-ONLY CONCERN")
    symptom_only   = safe_count(conflict["conflict_status"], "SYMPTOM-ONLY CONCERN")
    insuff_data    = safe_count(conflict["conflict_status"], "INSUFFICIENT DATA")

    row("No conflict detected:",        no_conflict)
    row("Sensor-symptom conflicts:",    sensor_symptom)
    row("Sensor-only concerns:",        sensor_only)
    row("Symptom-only concerns:",       symptom_only)
    row("Insufficient data cases:",     insuff_data)
    total_flagged = sensor_symptom + sensor_only + symptom_only + insuff_data
    row("Total flagged (non-routine):", total_flagged)


# ---------------------------------------------------------------------------
# SECTION 7 – CAPACITY RESULTS
# ---------------------------------------------------------------------------

section("CAPACITY RESULTS")
print("    Clinician capacity rule: only 10 HIGH/CRITICAL cases can be")
print("    reviewed immediately per review cycle. Remaining cases are queued.")
print()

if "capacity_status" in escalation.columns:
    within_cap = safe_count(escalation["capacity_status"], "WITHIN_CAPACITY")
    queued     = safe_count(escalation["capacity_status"], "QUEUED")
    not_appl   = safe_count(escalation["capacity_status"], "NOT_APPLICABLE")

    row("Capacity limit (design rule):", 10)
    row("Cases within capacity:",        within_cap)
    row("Cases queued (next slot):",     queued)
    row("Cases not applicable:",         not_appl)

if "schedule_status" in escalation.columns:
    print()
    print("    Schedule status breakdown:")
    for status, count in escalation["schedule_status"].value_counts().items():
        row(str(status) + ":", count, indent=6)


# ---------------------------------------------------------------------------
# SECTION 8 – COMMUNICATION RESULTS
# ---------------------------------------------------------------------------

section("COMMUNICATION RESULTS")
print("    Communication is attempted for HIGH and CRITICAL cases.")
print("    Offline cases are saved using the store-and-forward mechanism.")
print()

if "communication_result" in escalation.columns:
    comm = escalation["communication_result"].value_counts()
    completed = safe_count(escalation["communication_result"], "Clinician contact completed.")
    pending   = safe_count(escalation["communication_result"], "Clinician contact pending.")
    failed    = safe_count(escalation["communication_result"], "First communication attempt failed.")
    stored    = safe_count(escalation["communication_result"],
                           "Case stored locally for later transmission when connectivity returns.")

    row("Communication completed:",    completed)
    row("Communication pending:",      pending)
    row("Communication failed:",       failed)
    row("Stored for forward (offline):", stored)

if "store_forward_status" in escalation.columns:
    stored_count     = safe_count(escalation["store_forward_status"], "STORED")
    not_req_sf_count = safe_count(escalation["store_forward_status"], "NOT_REQUIRED")
    print()
    row("Store-and-forward STORED:",       stored_count)
    row("Store-and-forward NOT_REQUIRED:", not_req_sf_count)


# ---------------------------------------------------------------------------
# SECTION 9 – ERROR ANALYSIS (risk categories for review)
# ---------------------------------------------------------------------------

section("ERROR ANALYSIS")
print("    This section identifies categories of cases that may carry")
print("    clinical risk in a real deployment (for research and review).")
print()

# 1. False reassurance risk:
#    Cases where baseline said LOW/Continue but they have concerning symptoms
if "risk_level" in escalation.columns and "concerning_symptoms" in escalation.columns:
    false_reassurance_risk = escalation[
        (escalation["risk_level"] == "LOW") &
        (escalation["concerning_symptoms"].notna()) &
        (escalation["concerning_symptoms"] != "") &
        (escalation["concerning_symptoms"].str.strip() != "")
    ]
    row("False reassurance risk (LOW risk + symptoms):", len(false_reassurance_risk))
else:
    row("False reassurance risk:", "N/A (columns missing)")

# 2. Sensor-only concern (abnormal sensors, no symptoms reported)
sensor_only_count = safe_count(escalation["conflict_status"], "SENSOR-ONLY CONCERN") \
    if "conflict_status" in escalation.columns else 0
row("Sensor-only concern cases:", sensor_only_count)

# 3. Symptom-only concern
symptom_only_count = safe_count(escalation["conflict_status"], "SYMPTOM-ONLY CONCERN") \
    if "conflict_status" in escalation.columns else 0
row("Symptom-only concern cases:", symptom_only_count)

# 4. Insufficient data (could not assess reliably)
insuff_data_count = safe_count(escalation["conflict_status"], "INSUFFICIENT DATA") \
    if "conflict_status" in escalation.columns else 0
row("Insufficient data cases:", insuff_data_count)

# 5. Communication failure (clinician may not have been reached)
comm_failed_count = safe_count(
    escalation["communication_result"], "First communication attempt failed."
) if "communication_result" in escalation.columns else 0
row("Communication failed cases:", comm_failed_count)

# 6. Capacity queue (delayed review)
capacity_queued_count = safe_count(escalation["capacity_status"], "QUEUED") \
    if "capacity_status" in escalation.columns else 0
row("Capacity-queued (delayed review):", capacity_queued_count)

print()
print("    IMPORTANT: In a real system, each of the above categories would")
print("    require a specific mitigation strategy. This prototype demonstrates")
print("    that the system identifies and flags these cases rather than ignoring them.")


# ---------------------------------------------------------------------------
# SAVE RESULTS TO CSV
# ---------------------------------------------------------------------------

section("SAVING EXPERIMENT RESULTS")

# Build a flat summary record for the CSV
summary_record = {
    # General
    "total_records":              total_records,
    "unique_patients":            unique_patients,
    "good_records":               good,
    "incomplete_records":         incomplete,
    "invalid_records":            invalid,
    "missing_sensor_values":      missing_values,
    "trend_analysed_patients":    len(trend),

    # Priority (final workflow)
    "priority_LOW":               safe_count(escalation["priority"], "LOW")        if "priority" in escalation.columns else 0,
    "priority_MEDIUM":            safe_count(escalation["priority"], "MEDIUM")     if "priority" in escalation.columns else 0,
    "priority_HIGH":              safe_count(escalation["priority"], "HIGH")       if "priority" in escalation.columns else 0,
    "priority_CRITICAL":          safe_count(escalation["priority"], "CRITICAL")   if "priority" in escalation.columns else 0,
    "priority_UNTRUSTED":         safe_count(escalation["priority"], "UNTRUSTED")  if "priority" in escalation.columns else 0,

    # Conflict
    "conflict_no_conflict":       safe_count(conflict["conflict_status"], "NO CONFLICT")           if "conflict_status" in conflict.columns else 0,
    "conflict_sensor_symptom":    safe_count(conflict["conflict_status"], "SENSOR-SYMPTOM CONFLICT") if "conflict_status" in conflict.columns else 0,
    "conflict_sensor_only":       safe_count(conflict["conflict_status"], "SENSOR-ONLY CONCERN")   if "conflict_status" in conflict.columns else 0,
    "conflict_symptom_only":      safe_count(conflict["conflict_status"], "SYMPTOM-ONLY CONCERN")  if "conflict_status" in conflict.columns else 0,
    "conflict_insufficient_data": safe_count(conflict["conflict_status"], "INSUFFICIENT DATA")     if "conflict_status" in conflict.columns else 0,

    # Escalation pathways
    "path_continue_monitoring":   safe_count(escalation["escalation_path"], "CONTINUE_MONITORING")     if "escalation_path" in escalation.columns else 0,
    "path_schedule_followup":     safe_count(escalation["escalation_path"], "SCHEDULE_FOLLOW_UP")      if "escalation_path" in escalation.columns else 0,
    "path_clinician_review":      safe_count(escalation["escalation_path"], "CLINICIAN_REVIEW")        if "escalation_path" in escalation.columns else 0,
    "path_urgent_review":         safe_count(escalation["escalation_path"], "URGENT_CLINICIAN_REVIEW") if "escalation_path" in escalation.columns else 0,
    "path_safe_fallback":         safe_count(escalation["escalation_path"], "SAFE_FALLBACK")           if "escalation_path" in escalation.columns else 0,

    # Communication
    "comm_completed":             safe_count(escalation["communication_result"], "Clinician contact completed.") if "communication_result" in escalation.columns else 0,
    "comm_pending":               safe_count(escalation["communication_result"], "Clinician contact pending.")  if "communication_result" in escalation.columns else 0,
    "comm_failed":                safe_count(escalation["communication_result"], "First communication attempt failed.") if "communication_result" in escalation.columns else 0,
    "store_forward_count":        safe_count(escalation["store_forward_status"], "STORED") if "store_forward_status" in escalation.columns else 0,

    # Capacity
    "capacity_within":            safe_count(escalation["capacity_status"], "WITHIN_CAPACITY") if "capacity_status" in escalation.columns else 0,
    "capacity_queued":            safe_count(escalation["capacity_status"], "QUEUED")          if "capacity_status" in escalation.columns else 0,

    # Baseline comparison
    "baseline_decisions_same":    same,
    "baseline_decisions_changed": changed,
    "escalated_to_urgent":        len(upgraded),
    "routed_to_safe_fallback":    len(became_safe_fallback),

    # Edge case accuracy
    "demo_cases_total":           total_demo,
    "demo_cases_correct":         correct,
    "demo_routing_accuracy_pct":  round(accuracy, 1),
}

summary_df = pd.DataFrame([summary_record])
summary_df.to_csv(OUTPUT_CSV, index=False)
print(f"  Experiment summary saved to: {OUTPUT_CSV}")

# Also save the demo case details
demo_output_csv = os.path.join(OUTPUT_DIR, "demo_case_results.csv")
demo_df.to_csv(demo_output_csv, index=False)
print(f"  Demo case details saved to:  {demo_output_csv}")


# ---------------------------------------------------------------------------
# FINAL PRINT SUMMARY
# ---------------------------------------------------------------------------

print()
print("=" * 60)
print("  PHASE 9 EXPERIMENT COMPLETE")
print("=" * 60)
print(f"  Total records processed  : {total_records}")
print(f"  Edge case routing acc.   : {accuracy:.1f}%")
print(f"  Decisions changed        : {changed} / {total_records}")
print(f"  Results saved to         : experiments/experiment_results.csv")
print()
print("  This experiment used only existing CSV files and simple")
print("  pandas logic. No machine learning was used.")
print()
print("  DISCLAIMER: This is an educational prototype using")
print("  simulated anonymous data. Not for clinical use.")
print()
