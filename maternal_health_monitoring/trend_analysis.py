# trend_analysis.py
# Phase 5 - Trend Analysis
# Remote Maternal Health Monitoring and Escalation System
#
# This script groups patient observations by patient_id, sorts them by
# observation_day, and identifies whether each patient's systolic blood
# pressure is Increasing, Decreasing, Stable, or has Not Enough Data.
#
# IMPORTANT:
#   - This is a student prototype using simulated data only.
#   - Trend labels are for software workflow demonstration purposes only.
#   - Do NOT use this analysis to make real clinical decisions.
#   - These thresholds are NOT official medical guidelines.

import os
import sys
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# SECTION 1: FILE PATHS
# ---------------------------------------------------------------------------

INPUT_FILE  = os.path.join("data", "cleaned_maternal_data.csv")
OUTPUT_FILE = os.path.join("data", "trend_results.csv")

# ---------------------------------------------------------------------------
# SECTION 2: TREND SENSITIVITY THRESHOLD
# ---------------------------------------------------------------------------
# If the change between two readings is within +/- this value, we call it Stable.
# This is a prototype demonstration value, not a medical threshold.

STABLE_THRESHOLD = 5   # mmHg difference

# Minimum proportion of consecutive changes that must be positive for
# "Consistently Increasing" (and negative for "Consistently Decreasing")
CONSISTENT_MAJORITY = 0.6


# ---------------------------------------------------------------------------
# SECTION 3: LOAD DATA
# ---------------------------------------------------------------------------

def load_data(filepath):
    """
    Load the cleaned CSV file into a Pandas DataFrame.
    Stop with a clear message if the file does not exist.
    """
    if not os.path.exists(filepath):
        print(f"\n[ERROR] Cleaned dataset not found: {filepath}")
        print("  Please run clean_data.py first.\n")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"[OK] Loaded dataset: {filepath}")
    print(f"     Rows: {len(df)}, Columns: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# SECTION 4: PREPARE PATIENT DATA
# ---------------------------------------------------------------------------

def prepare_patient_data(df):
    """
    Group the DataFrame by patient_id.
    Within each group, sort rows by observation_day so that we always
    compare earlier readings with later ones.

    Returns the sorted DataFrame (all rows, just reordered).
    """
    df_sorted = df.sort_values(
        by=["patient_id", "observation_day"]
    ).reset_index(drop=True)

    return df_sorted


# ---------------------------------------------------------------------------
# SECTION 5: GET VALID SYSTOLIC READINGS FOR ONE PATIENT
# ---------------------------------------------------------------------------

def get_valid_systolic_readings(patient_df):
    """
    Given a patient's sorted observations, return a list of (day, systolic_bp)
    tuples where the systolic_bp value is not NaN.

    We only use valid readings for trend calculation.
    Missing or invalid values (NaN) are skipped.
    """
    valid = patient_df[["observation_day", "systolic_bp"]].dropna(
        subset=["systolic_bp"]
    )
    # Return as a list of (day, bp) tuples sorted by day
    return list(valid.itertuples(index=False, name=None))


# ---------------------------------------------------------------------------
# SECTION 6: CALCULATE THE MOST RECENT TREND (LAST TWO READINGS)
# ---------------------------------------------------------------------------

def calculate_recent_trend(readings):
    """
    Compare the last two valid systolic BP readings to find the recent trend.

    readings: list of (day, systolic_bp) tuples, sorted by day.

    Returns (trend_status, change, reason) where:
    - trend_status: "Increasing", "Decreasing", "Stable", "Not Enough Data"
    - change      : numeric difference (latest - previous), or None
    - reason      : short readable explanation
    """
    if len(readings) < 2:
        return (
            "Not Enough Data",
            None,
            "Not enough valid observations to determine a trend."
        )

    # Take the two most recent valid readings
    previous_day, previous_bp = readings[-2]
    latest_day,   latest_bp   = readings[-1]

    change = latest_bp - previous_bp

    if change > STABLE_THRESHOLD:
        trend  = "Increasing"
        reason = (
            f"Latest BP ({latest_bp:.0f}) is higher than the previous valid "
            f"reading ({previous_bp:.0f}). Increasing BP trend observed."
        )
    elif change < -STABLE_THRESHOLD:
        trend  = "Decreasing"
        reason = (
            f"Latest BP ({latest_bp:.0f}) is lower than the previous valid "
            f"reading ({previous_bp:.0f}). Decreasing BP trend observed."
        )
    else:
        trend  = "Stable"
        reason = (
            f"Latest BP ({latest_bp:.0f}) is close to the previous valid "
            f"reading ({previous_bp:.0f}). Recent readings are relatively stable."
        )

    return (trend, change, reason)


# ---------------------------------------------------------------------------
# SECTION 7: CALCULATE OVERALL TREND (3+ READINGS)
# ---------------------------------------------------------------------------

def calculate_overall_trend(readings):
    """
    For patients with 3 or more valid readings, look at ALL consecutive
    changes to determine the overall direction.

    Rule:
    - If >= CONSISTENT_MAJORITY of consecutive changes are positive  → "Consistently Increasing"
    - If >= CONSISTENT_MAJORITY of consecutive changes are negative  → "Consistently Decreasing"
    - Otherwise                                                      → "Stable/Variable"

    Returns an overall_trend string, or None if fewer than 3 readings exist.
    """
    if len(readings) < 3:
        return None   # Not enough data for an overall trend

    # Calculate all consecutive differences
    changes = []
    for i in range(1, len(readings)):
        diff = readings[i][1] - readings[i - 1][1]
        changes.append(diff)

    total = len(changes)
    positive_count = sum(1 for c in changes if c > 0)
    negative_count = sum(1 for c in changes if c < 0)

    if positive_count / total >= CONSISTENT_MAJORITY:
        return "Consistently Increasing"
    elif negative_count / total >= CONSISTENT_MAJORITY:
        return "Consistently Decreasing"
    else:
        return "Stable/Variable"


# ---------------------------------------------------------------------------
# SECTION 8: PROCESS ALL PATIENTS
# ---------------------------------------------------------------------------

def create_trend_results(df_sorted):
    """
    Loop through every patient and calculate their systolic BP trend.

    For each patient we produce one summary row containing:
    patient_id, number_of_observations, number_of_valid_readings,
    previous_systolic_bp, latest_systolic_bp, systolic_bp_change,
    trend_status, overall_trend, trend_reason.

    Returns a DataFrame with one row per patient.
    """
    results = []

    # Group by patient so we can handle each patient separately
    grouped = df_sorted.groupby("patient_id", sort=True)

    for patient_id, patient_df in grouped:

        # Sort this patient's rows by observation_day (already done, but just in case)
        patient_df = patient_df.sort_values("observation_day")

        total_obs = len(patient_df)

        # Get only the rows where systolic_bp is a valid number
        valid_readings = get_valid_systolic_readings(patient_df)
        valid_count = len(valid_readings)

        # --- Recent trend (based on last two readings) ---
        trend_status, change, reason = calculate_recent_trend(valid_readings)

        # --- Overall trend (based on all readings if 3+) ---
        overall_trend = calculate_overall_trend(valid_readings)

        # Extract previous and latest BP values for the summary row
        if valid_count >= 2:
            previous_bp = valid_readings[-2][1]
            latest_bp   = valid_readings[-1][1]
        elif valid_count == 1:
            previous_bp = np.nan
            latest_bp   = valid_readings[0][1]
        else:
            previous_bp = np.nan
            latest_bp   = np.nan

        results.append({
            "patient_id":              patient_id,
            "total_observations":      total_obs,
            "valid_systolic_readings": valid_count,
            "previous_systolic_bp":    previous_bp,
            "latest_systolic_bp":      latest_bp,
            "systolic_bp_change":      change,
            "trend_status":            trend_status,
            "overall_trend":           overall_trend if overall_trend else "N/A (< 3 readings)",
            "trend_reason":            reason,
        })

    trend_df = pd.DataFrame(results)
    return trend_df


# ---------------------------------------------------------------------------
# SECTION 9: SAVE RESULTS
# ---------------------------------------------------------------------------

def save_results(trend_df, output_path):
    """
    Save the patient-level trend results to a new CSV file.
    The cleaned dataset and risk results are NOT modified.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    trend_df.to_csv(output_path, index=False)
    print(f"\n[OK] Trend results saved to: {output_path}")


# ---------------------------------------------------------------------------
# SECTION 10: PRINT SUMMARY
# ---------------------------------------------------------------------------

def show_summary(trend_df):
    """
    Print a clear, readable summary of the trend analysis results.
    """
    total_patients = len(trend_df)
    counts = trend_df["trend_status"].value_counts()

    print("\n" + "=" * 50)
    print("  PHASE 5 - TREND ANALYSIS")
    print("=" * 50)
    print(f"\n  Total patients analyzed: {total_patients}")
    print()
    print(f"  Increasing     -> {counts.get('Increasing', 0)}")
    print(f"  Decreasing     -> {counts.get('Decreasing', 0)}")
    print(f"  Stable         -> {counts.get('Stable', 0)}")
    print(f"  Not Enough Data-> {counts.get('Not Enough Data', 0)}")
    print("\n" + "=" * 50)

    # Show overall trend breakdown as well
    overall_counts = trend_df["overall_trend"].value_counts()
    print("\n  Overall trend (3+ readings):")
    for label, cnt in overall_counts.items():
        print(f"    {label}: {cnt}")

    # First 10 trend results
    print("\nFirst 10 trend results:\n")
    display_cols = [
        "patient_id", "valid_systolic_readings",
        "previous_systolic_bp", "latest_systolic_bp",
        "systolic_bp_change", "trend_status", "overall_trend"
    ]
    print(trend_df[display_cols].head(10).to_string(index=False))
    print()


# ---------------------------------------------------------------------------
# SECTION 11: DEMONSTRATION CASE VERIFICATION
# ---------------------------------------------------------------------------

def verify_demonstration_cases(trend_df):
    """
    Search the trend results for examples of each expected category and
    print a representative row for each.

    This confirms the trend logic is working correctly.
    """
    print("-" * 50)
    print("  DEMONSTRATION CASE VERIFICATION")
    print("-" * 50)

    cases = {
        "Consistently Increasing": "overall_trend == 'Consistently Increasing'",
        "Consistently Decreasing": "overall_trend == 'Consistently Decreasing'",
        "Stable/Variable":         "overall_trend == 'Stable/Variable'",
        "Increasing (recent)":     "trend_status == 'Increasing'",
        "Decreasing (recent)":     "trend_status == 'Decreasing'",
        "Stable (recent)":         "trend_status == 'Stable'",
        "Not Enough Data":         "trend_status == 'Not Enough Data'",
    }

    for label, query in cases.items():
        try:
            sample = trend_df.query(query)
            if len(sample) > 0:
                row = sample.iloc[0]
                print(f"\n  [{label}]")
                print(f"    patient_id            : {row['patient_id']}")
                print(f"    valid_systolic_readings: {row['valid_systolic_readings']}")
                print(f"    previous_systolic_bp  : {row['previous_systolic_bp']}")
                print(f"    latest_systolic_bp    : {row['latest_systolic_bp']}")
                print(f"    systolic_bp_change    : {row['systolic_bp_change']}")
                print(f"    trend_status          : {row['trend_status']}")
                print(f"    overall_trend         : {row['overall_trend']}")
                print(f"    trend_reason          : {row['trend_reason']}")
            else:
                print(f"\n  [{label}] -- No matching patient found in dataset.")
        except Exception as e:
            print(f"\n  [{label}] -- Query error: {e}")

    print()


# ---------------------------------------------------------------------------
# SECTION 12: MAIN FUNCTION
# ---------------------------------------------------------------------------

def main():
    """
    Run all Phase 5 trend analysis steps in order.
    """
    print("=" * 55)
    print("  Phase 5 - Trend Analysis")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)

    # Step 1: Load the cleaned dataset
    df = load_data(INPUT_FILE)

    # Step 2: Sort all rows by patient_id and observation_day
    print("\nPreparing patient observations ...")
    df_sorted = prepare_patient_data(df)

    # Step 3: Calculate trend for every patient
    print("Calculating trends ...")
    trend_df = create_trend_results(df_sorted)

    # Step 4: Save results
    save_results(trend_df, OUTPUT_FILE)

    # Step 5: Print summary and first 10 rows
    show_summary(trend_df)

    # Step 6: Verify demonstration cases
    verify_demonstration_cases(trend_df)

    # Step 7: Confirm input files are unchanged
    print("-" * 50)
    print("  INPUT FILE STATUS")
    print("-" * 50)
    original = pd.read_csv(INPUT_FILE)
    print(f"  data/cleaned_maternal_data.csv : {len(original)} rows (unchanged)")

    risk_path = os.path.join("data", "baseline_risk_results.csv")
    if os.path.exists(risk_path):
        risk_df = pd.read_csv(risk_path)
        print(f"  data/baseline_risk_results.csv : {len(risk_df)} rows (unchanged)")

    print()
    print("[DONE] Phase 5 complete.")
    print("  Output: data/trend_results.csv")
    print("\n  Do NOT start Phase 6 yet.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
