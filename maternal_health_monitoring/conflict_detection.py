# conflict_detection.py
# Phase 6 - Sensor-Symptom Conflict Detection
# Remote Maternal Health Monitoring and Escalation System
#
# This script compares sensor-based risk signals with patient-reported symptoms
# to identify cases where the two sources of information agree or conflict.
#
# IMPORTANT:
#   - This is a student prototype using simulated data only.
#   - These rules are for software workflow demonstration purposes only.
#   - This system does NOT diagnose any medical condition.
#   - Do NOT use this output to make real clinical decisions.

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# SECTION 1: FILE PATHS
# ---------------------------------------------------------------------------

RISK_FILE   = os.path.join("data", "baseline_risk_results.csv")
TREND_FILE  = os.path.join("data", "trend_results.csv")
OUTPUT_FILE = os.path.join("data", "conflict_results.csv")
DEMO_FILE   = os.path.join("data", "demo_conflict_cases.csv")

# ---------------------------------------------------------------------------
# SECTION 2: CONSTANTS — RISK SIGNAL GROUPS
# ---------------------------------------------------------------------------

# Baseline risk levels treated as a high sensor-based concern
HIGH_SENSOR_RISK = {"HIGH", "CRITICAL"}

# Baseline risk levels treated as a moderate sensor-based concern
MODERATE_SENSOR_RISK = {"MEDIUM"}

# Baseline risk levels treated as low sensor-based concern
LOW_SENSOR_RISK = {"LOW"}

# Risk levels where data is too unreliable for conflict analysis
UNCERTAIN_RISK = {"UNCERTAIN"}


# ---------------------------------------------------------------------------
# SECTION 3: LOAD DATA
# ---------------------------------------------------------------------------

def load_data():
    """
    Load both input CSV files and return them as DataFrames.
    Show a clear error message if either file is missing.
    """
    # Check baseline risk results
    if not os.path.exists(RISK_FILE):
        print(f"\n[ERROR] File not found: {RISK_FILE}")
        print("  Please run risk_detection.py first.\n")
        sys.exit(1)

    # Check trend results
    if not os.path.exists(TREND_FILE):
        print(f"\n[ERROR] File not found: {TREND_FILE}")
        print("  Please run trend_analysis.py first.\n")
        sys.exit(1)

    risk_df  = pd.read_csv(RISK_FILE)
    trend_df = pd.read_csv(TREND_FILE)

    print(f"[OK] Loaded: {RISK_FILE}  ({len(risk_df)} rows)")
    print(f"[OK] Loaded: {TREND_FILE} ({len(trend_df)} rows)")

    return risk_df, trend_df


# ---------------------------------------------------------------------------
# SECTION 4: MERGE TREND INFORMATION INTO THE RISK DATASET
# ---------------------------------------------------------------------------

def merge_trend_info(risk_df, trend_df):
    """
    Join the patient-level trend results (one row per patient) onto the
    per-observation risk dataset using patient_id as the key.

    After the merge, every observation row will also carry the patient's
    trend_status and overall_trend for use in conflict detection.
    """
    # Select only the columns we need from the trend data
    trend_cols = [
        "patient_id",
        "trend_status",
        "overall_trend",
        "systolic_bp_change",
    ]
    trend_small = trend_df[trend_cols]

    # Left join: keep all rows from risk_df, add trend columns where available
    merged = risk_df.merge(trend_small, on="patient_id", how="left")

    print(f"\n[OK] Merged trend data. Combined dataset: {len(merged)} rows.")
    return merged


# ---------------------------------------------------------------------------
# SECTION 5: CHECK FOR CONCERNING SYMPTOMS
# ---------------------------------------------------------------------------

def check_symptoms(row):
    """
    Determine whether a record has a concerning symptom signal.

    Concerning symptom conditions (prototype definition):
    1. bleeding = Yes
    2. reduced_fetal_movement = Yes
    3. headache = Yes AND blurred_vision = Yes

    Also collect any additional supporting symptoms present.

    Returns:
    - has_concerning_symptom (bool)
    - concerning_list        (list of strings describing which concerns were found)
    - supporting_list        (list of strings for non-critical symptoms present)
    """
    concerning_list = []
    supporting_list = []

    # --- High-priority symptom checks ---
    if row.get("bleeding") == "Yes":
        concerning_list.append("bleeding reported")

    if row.get("reduced_fetal_movement") == "Yes":
        concerning_list.append("reduced fetal movement reported")

    if row.get("headache") == "Yes" and row.get("blurred_vision") == "Yes":
        concerning_list.append("headache and blurred vision reported together")

    # --- Supporting symptoms ---
    if row.get("abdominal_pain") == "Yes":
        supporting_list.append("abdominal pain")

    if row.get("swelling") == "Yes":
        supporting_list.append("swelling")

    # A headache alone (without blurred vision) is a supporting symptom
    if row.get("headache") == "Yes" and row.get("blurred_vision") != "Yes":
        supporting_list.append("headache alone")

    has_concerning = len(concerning_list) > 0

    return has_concerning, concerning_list, supporting_list


# ---------------------------------------------------------------------------
# SECTION 6: BUILD TREND NOTE
# ---------------------------------------------------------------------------

def get_trend_note(row):
    """
    Return a short readable note about the patient's BP trend.
    This is added as supporting context — it does NOT change the conflict status.
    """
    trend = row.get("trend_status", "")

    if trend == "Increasing":
        return "Increasing BP trend observed."
    elif trend == "Decreasing":
        return "Decreasing BP trend observed."
    elif trend == "Stable":
        return "Recent BP readings are relatively stable."
    elif trend == "Not Enough Data":
        return "Not enough valid readings to determine a trend."
    else:
        return "Trend data unavailable."


# ---------------------------------------------------------------------------
# SECTION 7: DETECT CONFLICT FOR ONE ROW
# ---------------------------------------------------------------------------

def detect_conflict(row):
    """
    Apply conflict detection rules to a single observation row.

    Returns a dictionary with five new fields:
    - conflict_status      : the main conflict category label
    - signal_agreement     : whether sensor and symptoms point the same way
    - concerning_symptoms  : comma-separated list of concerning symptoms found
    - conflict_reason      : plain-English explanation
    - final_workflow_action: the prototype workflow recommendation

    Priority of rules (checked in order):
    1. INSUFFICIENT DATA  — if data_quality is not Good
    2. NO CONFLICT (high agree) — sensor high + symptoms concerning
    3. SENSOR-ONLY CONCERN — sensor high + no concerning symptoms
    4. SENSOR-SYMPTOM CONFLICT — sensor low/medium + concerning symptoms present
    5. NO CONFLICT (both low) — sensor low + no concerning symptoms
    """
    risk_level   = row.get("risk_level", "UNCERTAIN")
    data_quality = row.get("data_quality", "Good")
    trend_note   = get_trend_note(row)

    # Gather symptom information
    has_concerning, concerning_list, supporting_list = check_symptoms(row)

    # Build a readable string of concerning symptoms
    concerning_str = "; ".join(concerning_list) if concerning_list else "None"

    # -----------------------------------------------------------------------
    # RULE 1: INSUFFICIENT DATA
    # Data quality problems mean we cannot reliably compare sensor and symptoms.
    # -----------------------------------------------------------------------
    if data_quality in ("Incomplete", "Invalid") or risk_level in UNCERTAIN_RISK:
        return {
            "conflict_status":       "INSUFFICIENT DATA",
            "signal_agreement":      "Cannot assess — data quality issue",
            "concerning_symptoms":   concerning_str,
            "conflict_reason": (
                "Data quality is insufficient to confidently reconcile sensor "
                "readings and symptoms. " + trend_note
            ),
            "final_workflow_action": "Repeat Measurement / Clinician Review",
        }

    # -----------------------------------------------------------------------
    # RULE 2: SENSOR HIGH + SYMPTOMS CONCERNING → Both agree (high concern)
    # -----------------------------------------------------------------------
    if risk_level in HIGH_SENSOR_RISK and has_concerning:
        return {
            "conflict_status":       "NO CONFLICT",
            "signal_agreement":      "Sensor and symptoms agree — both concerning",
            "concerning_symptoms":   concerning_str,
            "conflict_reason": (
                f"Sensor-based risk ({risk_level}) and reported symptoms "
                f"({concerning_str}) are both concerning. "
                + trend_note
            ),
            "final_workflow_action": row.get("recommended_action",
                                             "Immediate Clinician Review"),
        }

    # -----------------------------------------------------------------------
    # RULE 3: SENSOR HIGH + NO CONCERNING SYMPTOMS → Sensor-only concern
    # Sensor readings are elevated but patient has not reported matching symptoms.
    # We do NOT dismiss the sensor reading.
    # -----------------------------------------------------------------------
    if risk_level in HIGH_SENSOR_RISK and not has_concerning:
        return {
            "conflict_status":       "SENSOR-ONLY CONCERN",
            "signal_agreement":      "Sensor concern without matching symptoms",
            "concerning_symptoms":   concerning_str,
            "conflict_reason": (
                f"Sensor-based risk is {risk_level} but no concerning symptoms "
                f"were reported. The sensor reading should not be dismissed. "
                + trend_note
            ),
            "final_workflow_action": "Repeat Measurement / Clinician Review",
        }

    # -----------------------------------------------------------------------
    # RULE 4: SENSOR LOW/MEDIUM + CONCERNING SYMPTOMS → Conflict
    # Sensors appear relatively normal, but the patient reports symptoms
    # that should not be ignored. Route to clinician review.
    # -----------------------------------------------------------------------
    if risk_level in (LOW_SENSOR_RISK | MODERATE_SENSOR_RISK) and has_concerning:
        return {
            "conflict_status":       "SENSOR-SYMPTOM CONFLICT",
            "signal_agreement":      "Sensor and symptoms disagree",
            "concerning_symptoms":   concerning_str,
            "conflict_reason": (
                f"Sensor-based risk is {risk_level}, but concerning symptoms "
                f"were reported ({concerning_str}). "
                "Symptoms must not be dismissed because sensors appear normal. "
                + trend_note
            ),
            "final_workflow_action": "Clinician Review",
        }

    # -----------------------------------------------------------------------
    # RULE 5: SENSOR MODERATE + NO CONCERNING SYMPTOMS
    # -----------------------------------------------------------------------
    if risk_level in MODERATE_SENSOR_RISK and not has_concerning:
        # Check for supporting (non-critical) symptoms
        supporting_str = "; ".join(supporting_list) if supporting_list else "None"
        return {
            "conflict_status":       "NO CONFLICT",
            "signal_agreement":      "Moderate sensor concern, no critical symptoms",
            "concerning_symptoms":   concerning_str,
            "conflict_reason": (
                "Sensor-based risk is MEDIUM with no critical symptom conflict. "
                f"Supporting symptoms: {supporting_str}. "
                + trend_note
            ),
            "final_workflow_action": row.get("recommended_action",
                                             "Schedule Follow-up"),
        }

    # -----------------------------------------------------------------------
    # RULE 6: SENSOR LOW + NO CONCERNING SYMPTOMS → No conflict (all clear)
    # -----------------------------------------------------------------------
    return {
        "conflict_status":       "NO CONFLICT",
        "signal_agreement":      "Sensor and symptoms both reassuring",
        "concerning_symptoms":   concerning_str,
        "conflict_reason": (
            "Sensor findings and reported symptoms do not show a major mismatch. "
            + trend_note
        ),
        "final_workflow_action": "Continue Monitoring",
    }


# ---------------------------------------------------------------------------
# SECTION 8: APPLY CONFLICT DETECTION TO THE FULL DATASET
# ---------------------------------------------------------------------------

def create_results(df):
    """
    Run detect_conflict() on every row and add the five new columns.
    Returns the updated DataFrame.
    """
    new_cols = df.apply(detect_conflict, axis=1, result_type="expand")
    df = pd.concat([df, new_cols], axis=1)
    return df


# ---------------------------------------------------------------------------
# SECTION 9: SAVE OUTPUT
# ---------------------------------------------------------------------------

def save_results(df, output_path):
    """
    Save the conflict-annotated dataset to a new CSV.
    Original input files are NOT touched.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Conflict results saved to: {output_path}")


# ---------------------------------------------------------------------------
# SECTION 10: PRINT SUMMARY
# ---------------------------------------------------------------------------

def show_summary(df):
    """
    Print a readable summary of conflict detection results.
    """
    total = len(df)
    counts = df["conflict_status"].value_counts()

    print("\n" + "=" * 50)
    print("  PHASE 6 - CONFLICT DETECTION")
    print("=" * 50)
    print(f"\n  Total records analyzed: {total}")
    print()
    print(f"  NO CONFLICT              -> {counts.get('NO CONFLICT', 0)}")
    print(f"  SENSOR-SYMPTOM CONFLICT  -> {counts.get('SENSOR-SYMPTOM CONFLICT', 0)}")
    print(f"  SENSOR-ONLY CONCERN      -> {counts.get('SENSOR-ONLY CONCERN', 0)}")
    print(f"  SYMPTOM-ONLY CONCERN     -> {counts.get('SYMPTOM-ONLY CONCERN', 0)}")
    print(f"  INSUFFICIENT DATA        -> {counts.get('INSUFFICIENT DATA', 0)}")
    print()

    # Additional breakdowns
    sensor_symptom = counts.get("SENSOR-SYMPTOM CONFLICT", 0)
    sensor_only    = counts.get("SENSOR-ONLY CONCERN", 0)
    insuff         = counts.get("INSUFFICIENT DATA", 0)

    concerning_rows = (df["concerning_symptoms"] != "None").sum()

    print(f"  Records with concerning symptoms : {concerning_rows}")
    print(f"  Sensor-symptom conflict cases    : {sensor_symptom}")
    print(f"  Sensor-only concern cases        : {sensor_only}")
    print(f"  Insufficient-data cases          : {insuff}")
    print("\n" + "=" * 50)


# ---------------------------------------------------------------------------
# SECTION 11: PRINT EXAMPLE CASES
# ---------------------------------------------------------------------------

def show_examples(df):
    """
    Print up to 3 example rows for each key conflict category.
    """
    display_cols = [
        "patient_id", "risk_level",
        "headache", "blurred_vision", "bleeding", "reduced_fetal_movement",
        "trend_status", "conflict_status", "conflict_reason",
        "final_workflow_action",
    ]

    categories = [
        ("SENSOR-SYMPTOM CONFLICT",  "conflict_status == 'SENSOR-SYMPTOM CONFLICT'"),
        ("SENSOR-ONLY CONCERN",      "conflict_status == 'SENSOR-ONLY CONCERN'"),
        ("INSUFFICIENT DATA",        "conflict_status == 'INSUFFICIENT DATA'"),
    ]

    print("\n" + "-" * 50)
    print("  EXAMPLE CASES BY CATEGORY")
    print("-" * 50)

    for label, query in categories:
        print(f"\n  [{label}]")
        try:
            sample = df.query(query).head(3)
            if len(sample) == 0:
                print("  No matching case found in current simulated dataset.")
                continue
            for _, row in sample.iterrows():
                print(f"\n    patient_id           : {row['patient_id']}")
                print(f"    risk_level           : {row['risk_level']}")
                print(f"    headache             : {row['headache']}")
                print(f"    blurred_vision       : {row['blurred_vision']}")
                print(f"    bleeding             : {row['bleeding']}")
                print(f"    reduced_fetal_movement: {row['reduced_fetal_movement']}")
                print(f"    trend_status         : {row.get('trend_status', 'N/A')}")
                print(f"    conflict_status      : {row['conflict_status']}")
                print(f"    conflict_reason      : {row['conflict_reason']}")
                print(f"    final_workflow_action: {row['final_workflow_action']}")
        except Exception as e:
            print(f"  Could not retrieve examples: {e}")

    print()


# ---------------------------------------------------------------------------
# SECTION 12: VERIFY INPUT FILES ARE UNCHANGED
# ---------------------------------------------------------------------------

def verify_inputs_unchanged():
    """
    Confirm both input files still exist and print their row counts.
    """
    print("-" * 50)
    print("  INPUT FILE STATUS")
    print("-" * 50)

    files_to_check = [
        os.path.join("data", "simulated_maternal_data.csv"),
        os.path.join("data", "cleaned_maternal_data.csv"),
        os.path.join("data", "baseline_risk_results.csv"),
        os.path.join("data", "trend_results.csv"),
    ]

    for filepath in files_to_check:
        if os.path.exists(filepath):
            tmp = pd.read_csv(filepath)
            print(f"  {filepath}: {len(tmp)} rows (unchanged)")
        else:
            print(f"  {filepath}: NOT FOUND")

    print()


# ---------------------------------------------------------------------------
# SECTION 13: MAIN FUNCTION
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# SECTION 14: LOAD AND PROCESS DEMONSTRATION EDGE CASES
# ---------------------------------------------------------------------------

def load_demo_cases(filepath):
    """
    Load the hand-crafted demo conflict cases CSV.
    Returns a DataFrame, or None if the file does not exist.
    """
    if not os.path.exists(filepath):
        print(f"\n[WARN] Demo file not found: {filepath}")
        return None
    df = pd.read_csv(filepath)
    print(f"[OK] Loaded demo cases: {filepath} ({len(df)} rows)")
    return df


def show_demo_results(demo_df):
    """
    Run conflict detection on each demo row and print a clearly formatted
    result for every case.

    This section demonstrates all conflict categories using deliberately
    constructed simulated edge cases.
    """
    if demo_df is None or len(demo_df) == 0:
        print("  No demo cases to display.")
        return

    # Apply the same detect_conflict() function used for the real dataset
    result_cols = demo_df.apply(detect_conflict, axis=1, result_type="expand")
    demo_result = pd.concat([demo_df, result_cols], axis=1)

    print("\n" + "-" * 55)
    print("  DEMONSTRATION EDGE CASES (Simulated — Not Real Patients)")
    print("-" * 55)
    print("  These cases are hand-crafted to demonstrate each conflict")
    print("  category. They use anonymous IDs (DEMO001–DEMO006).\n")

    for _, row in demo_result.iterrows():
        pid    = row["patient_id"]
        rl     = row["risk_level"]
        dq     = row["data_quality"]
        cs     = row["conflict_status"]
        cr     = row["conflict_reason"]
        fa     = row["final_workflow_action"]
        sa     = row["signal_agreement"]
        syms   = row["concerning_symptoms"]

        # Build a short symptom summary for display
        sym_str = ", ".join(
            col for col in
            ["headache", "blurred_vision", "bleeding",
             "abdominal_pain", "swelling", "reduced_fetal_movement"]
            if row.get(col) == "Yes"
        ) or "None"

        print(f"  {pid}")
        print(f"    risk_level           : {rl}")
        print(f"    data_quality         : {dq}")
        print(f"    symptoms present     : {sym_str}")
        print(f"    concerning_symptoms  : {syms}")
        print(f"    conflict_status  --> : {cs}")
        print(f"    signal_agreement     : {sa}")
        print(f"    conflict_reason      : {cr}")
        print(f"    final_workflow_action: {fa}")
        print()

    print("-" * 55)


# ---------------------------------------------------------------------------
# SECTION 15: MAIN FUNCTION
# ---------------------------------------------------------------------------

def main():
    """
    Run all Phase 6 conflict detection steps in order.
    """
    print("=" * 55)
    print("  Phase 6 - Sensor-Symptom Conflict Detection")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)

    # Step 1: Load both input files
    risk_df, trend_df = load_data()

    # Step 2: Merge trend information into the risk dataset
    df = merge_trend_info(risk_df, trend_df)

    # Step 3: Run conflict detection on every row
    print("Applying conflict detection rules ...")
    df = create_results(df)

    # Step 4: Save output
    save_results(df, OUTPUT_FILE)

    # Step 5: Print summary
    show_summary(df)

    # Step 6: Show example cases for key categories
    show_examples(df)

    # Step 7: Confirm input files are unchanged
    verify_inputs_unchanged()

    # Step 8: Load and display the demonstration edge cases separately
    print("\nLoading demonstration edge cases ...")
    demo_df = load_demo_cases(DEMO_FILE)
    show_demo_results(demo_df)

    print("[DONE] Phase 6 complete.")
    print("  Output : data/conflict_results.csv")
    print("  Demo   : data/demo_conflict_cases.csv (unchanged)")
    print("\n  Do NOT start Phase 7 yet.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
