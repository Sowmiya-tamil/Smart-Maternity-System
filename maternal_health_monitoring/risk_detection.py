# risk_detection.py
# Phase 4 - Baseline Risk Detection
# Remote Maternal Health Monitoring and Escalation System
#
# This script applies simple rule-based logic to assign a risk level
# to each cleaned observation record.
#
# IMPORTANT:
#   - This is a student prototype using simulated data only.
#   - The thresholds used here are SIMPLIFIED rules for demonstrating
#     software workflow. They are NOT official medical guidelines.
#   - Do NOT use this system to make real clinical decisions.

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# SECTION 1: FILE PATHS
# ---------------------------------------------------------------------------

INPUT_FILE  = os.path.join("data", "cleaned_maternal_data.csv")
OUTPUT_FILE = os.path.join("data", "baseline_risk_results.csv")

# ---------------------------------------------------------------------------
# SECTION 2: PROTOTYPE THRESHOLD VALUES
# ---------------------------------------------------------------------------
# These are simplified ranges used only for this educational prototype.
# They are NOT official medical diagnostic thresholds.

# Blood pressure thresholds (prototype only)
SYSTOLIC_MODERATE  = 130   # >= this value → moderate BP concern
SYSTOLIC_HIGH      = 140   # >= this value → high BP concern

DIASTOLIC_MODERATE = 85    # >= this value → moderate BP concern
DIASTOLIC_HIGH     = 90    # >= this value → high BP concern

# Supporting vital sign boundaries (prototype only)
HEART_RATE_LOW  = 60
HEART_RATE_HIGH = 100

TEMP_LOW  = 36.0
TEMP_HIGH = 38.0

SPO2_LOW  = 95   # below this → supporting abnormality

# ---------------------------------------------------------------------------
# SECTION 3: LOAD DATA
# ---------------------------------------------------------------------------

def load_data(filepath):
    """
    Load the cleaned CSV into a Pandas DataFrame.
    If the file is missing, print a clear message and stop.
    """
    if not os.path.exists(filepath):
        print(f"\n[ERROR] Cleaned dataset not found: {filepath}")
        print("  Please run clean_data.py first.\n")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"[OK] Loaded cleaned dataset: {filepath}")
    print(f"     Rows: {len(df)}, Columns: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# SECTION 4: DATA QUALITY CHECK
# ---------------------------------------------------------------------------

def check_data_quality(row):
    """
    If the record has a data quality problem, return UNCERTAIN immediately.
    We must not make a risk prediction on unreliable data.

    Returns (risk_level, risk_reason, recommended_action) or None if OK.
    """
    quality = row.get("data_quality", "Good")

    if quality == "Invalid":
        return (
            "UNCERTAIN",
            "Invalid or unreliable observation. Sensor reading was outside the "
            "possible range and has been replaced.",
            "Repeat measurement and clinician review."
        )

    if quality == "Incomplete":
        return (
            "UNCERTAIN",
            "Important observation is missing. Risk cannot be reliably assessed "
            "without complete sensor readings.",
            "Repeat missing measurement and review symptoms."
        )

    # Good quality — proceed with normal risk rules
    return None


# ---------------------------------------------------------------------------
# SECTION 5: VITAL SIGN FLAGS
# ---------------------------------------------------------------------------

def get_bp_flag(systolic, diastolic):
    """
    Check blood pressure and return a flag string.
    Returns: 'high', 'moderate', or 'normal'

    NOTE: Prototype thresholds only, not clinical guidelines.
    """
    # Missing BP cannot be assessed
    if pd.isna(systolic) or pd.isna(diastolic):
        return "missing"

    # High concern: either value clearly elevated
    if systolic >= SYSTOLIC_HIGH or diastolic >= DIASTOLIC_HIGH:
        return "high"

    # Moderate concern: either value moderately elevated
    if systolic >= SYSTOLIC_MODERATE or diastolic >= DIASTOLIC_MODERATE:
        return "moderate"

    return "normal"


def count_supporting_abnormalities(row):
    """
    Count how many of the supporting vital signs (heart rate, temperature,
    SpO2) fall outside the prototype normal range.

    Returns an integer count (0, 1, 2, or 3).
    """
    count = 0

    # Heart rate outside normal range
    hr = row.get("heart_rate")
    if pd.notna(hr) and (hr < HEART_RATE_LOW or hr > HEART_RATE_HIGH):
        count += 1

    # Temperature outside normal range
    temp = row.get("temperature")
    if pd.notna(temp) and (temp < TEMP_LOW or temp > TEMP_HIGH):
        count += 1

    # SpO2 below threshold
    spo2 = row.get("spo2")
    if pd.notna(spo2) and spo2 < SPO2_LOW:
        count += 1

    return count


# ---------------------------------------------------------------------------
# SECTION 6: SYMPTOM FLAGS
# ---------------------------------------------------------------------------

def get_high_priority_symptoms(row):
    """
    Check for high-priority symptom combinations.

    High-priority conditions (for this prototype):
    1. bleeding = Yes
    2. reduced_fetal_movement = Yes
    3. headache = Yes AND blurred_vision = Yes

    Returns a list of the high-priority concerns found (empty if none).
    """
    concerns = []

    if row.get("bleeding") == "Yes":
        concerns.append("bleeding reported")

    if row.get("reduced_fetal_movement") == "Yes":
        concerns.append("reduced fetal movement reported")

    if row.get("headache") == "Yes" and row.get("blurred_vision") == "Yes":
        concerns.append("headache and blurred vision reported together")

    return concerns


def count_supporting_symptoms(row):
    """
    Count supporting (non-critical) symptoms that are present.
    Used to add weight to a MEDIUM classification.
    """
    count = 0
    for symptom in ["abdominal_pain", "swelling"]:
        if row.get(symptom) == "Yes":
            count += 1
    return count


# ---------------------------------------------------------------------------
# SECTION 7: CORE RISK CALCULATION
# ---------------------------------------------------------------------------

def calculate_risk(row):
    """
    Apply the risk detection rules to a single row.

    Priority order:
    1. UNCERTAIN  → data quality is Invalid or Incomplete
    2. CRITICAL   → high-priority symptom + concerning sensor reading
    3. HIGH       → clearly high BP, or multiple abnormal observations
    4. MEDIUM     → moderate BP, or one supporting abnormality, or symptoms
    5. LOW        → everything within prototype normal ranges

    Returns (risk_level, risk_reason, recommended_action).
    """

    # --- Step 1: Check data quality first ---
    quality_result = check_data_quality(row)
    if quality_result is not None:
        return quality_result

    # --- Step 2: Gather observation flags ---
    bp_flag              = get_bp_flag(row.get("systolic_bp"), row.get("diastolic_bp"))
    supporting_abnormal  = count_supporting_abnormalities(row)
    high_priority_syms   = get_high_priority_symptoms(row)
    supporting_syms      = count_supporting_symptoms(row)

    # --- Step 3: Apply risk rules ---

    # CRITICAL: high-priority symptom present AND a concerning sensor reading
    if high_priority_syms and (bp_flag in ("high", "moderate") or supporting_abnormal >= 1):
        reason = (
            f"Concerning symptom(s) reported ({'; '.join(high_priority_syms)}) "
            f"together with an abnormal sensor reading."
        )
        return ("CRITICAL", reason, "Immediate Clinician Review")

    # HIGH: clearly high BP alone, or multiple abnormal observations, or multiple
    #       high-priority symptoms without a corresponding sensor flag
    if bp_flag == "high":
        reason = (
            "Blood pressure is clearly elevated according to prototype thresholds. "
            "Clinician review is required."
        )
        return ("HIGH", reason, "Clinician Review")

    if supporting_abnormal >= 2:
        reason = (
            "Multiple supporting vital signs (heart rate, temperature, or SpO2) "
            "are outside the prototype normal range."
        )
        return ("HIGH", reason, "Clinician Review")

    if len(high_priority_syms) >= 1:
        # High-priority symptom present but no concerning sensor reading → HIGH
        reason = (
            f"High-priority symptom reported: {'; '.join(high_priority_syms)}. "
            f"Sensor readings are within normal range, but clinician review is needed."
        )
        return ("HIGH", reason, "Clinician Review")

    # MEDIUM: moderate BP, or one supporting abnormality, or supporting symptoms
    if bp_flag == "moderate":
        reason = (
            "Blood pressure is moderately elevated according to prototype thresholds. "
            "A follow-up observation is recommended."
        )
        return ("MEDIUM", reason, "Schedule Follow-up")

    if supporting_abnormal == 1:
        reason = (
            "One supporting vital sign (heart rate, temperature, or SpO2) is "
            "outside the prototype normal range."
        )
        return ("MEDIUM", reason, "Schedule Follow-up")

    if supporting_syms >= 1:
        reason = (
            "Supporting symptoms (abdominal pain or swelling) were reported. "
            "A follow-up observation is recommended."
        )
        return ("MEDIUM", reason, "Schedule Follow-up")

    # LOW: everything is within prototype normal ranges
    reason = (
        "Blood pressure is within the prototype normal range and no concerning "
        "symptoms were reported. Continue routine monitoring."
    )
    return ("LOW", reason, "Continue Monitoring")


# ---------------------------------------------------------------------------
# SECTION 8: APPLY RISK TO THE FULL DATASET
# ---------------------------------------------------------------------------

def apply_risk_to_dataset(df):
    """
    Run calculate_risk() on every row and add three new columns:
    risk_level, risk_reason, recommended_action.
    """
    results = df.apply(calculate_risk, axis=1, result_type="expand")
    results.columns = ["risk_level", "risk_reason", "recommended_action"]

    df = pd.concat([df, results], axis=1)
    return df


# ---------------------------------------------------------------------------
# SECTION 9: SAVE OUTPUT
# ---------------------------------------------------------------------------

def save_results(df, output_path):
    """
    Save the dataset with risk columns to a new CSV.
    The cleaned_maternal_data.csv is NOT overwritten.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Risk results saved to: {output_path}")


# ---------------------------------------------------------------------------
# SECTION 10: SUMMARY AND DISPLAY
# ---------------------------------------------------------------------------

def show_summary(df):
    """
    Print a risk-level summary and the first 10 records in a readable format.
    """
    counts = df["risk_level"].value_counts()

    total = len(df)

    # Ensure all levels appear even if count is 0
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "UNCERTAIN"]:
        if level not in counts:
            counts[level] = 0

    print("\n" + "=" * 50)
    print("  PHASE 4 - BASELINE RISK DETECTION")
    print("=" * 50)
    print(f"\n  Total records: {total}")
    print("\n  Risk Summary:")
    print(f"    LOW       -> {counts.get('LOW', 0)}")
    print(f"    MEDIUM    -> {counts.get('MEDIUM', 0)}")
    print(f"    HIGH      -> {counts.get('HIGH', 0)}")
    print(f"    CRITICAL  -> {counts.get('CRITICAL', 0)}")
    print(f"    UNCERTAIN -> {counts.get('UNCERTAIN', 0)}")
    print("\n" + "=" * 50)

    # Print first 10 records with key columns
    display_cols = ["patient_id", "risk_level", "risk_reason", "recommended_action"]
    print("\nFirst 10 records (risk columns only):\n")
    print(df[display_cols].head(10).to_string(index=False))
    print()


# ---------------------------------------------------------------------------
# SECTION 11: VERIFY SPECIFIC TEST CASES
# ---------------------------------------------------------------------------

def verify_test_cases(df):
    """
    Search the generated dataset for examples of each expected risk category
    and print one representative row for each.

    This confirms that the rule logic is working correctly for all risk levels.
    """
    print("-" * 50)
    print("  TEST CASE VERIFICATION")
    print("-" * 50)

    test_targets = {
        "LOW":       "data_quality=='Good' and risk_level=='LOW'",
        "MEDIUM":    "data_quality=='Good' and risk_level=='MEDIUM'",
        "HIGH":      "data_quality=='Good' and risk_level=='HIGH'",
        "CRITICAL":  "data_quality=='Good' and risk_level=='CRITICAL'",
        "UNCERTAIN (Incomplete)": "data_quality=='Incomplete'",
        "UNCERTAIN (Invalid)":    "data_quality=='Invalid'",
    }

    cols = ["patient_id", "data_quality", "risk_level", "risk_reason", "recommended_action"]

    for label, query in test_targets.items():
        try:
            sample = df.query(query)
            if len(sample) > 0:
                row = sample.iloc[0]
                print(f"\n  [{label}]")
                print(f"    patient_id        : {row['patient_id']}")
                print(f"    data_quality      : {row['data_quality']}")
                print(f"    risk_level        : {row['risk_level']}")
                print(f"    risk_reason       : {row['risk_reason']}")
                print(f"    recommended_action: {row['recommended_action']}")
            else:
                print(f"\n  [{label}] -- No matching record found in dataset.")
        except Exception:
            print(f"\n  [{label}] -- Could not query dataset.")

    print()


# ---------------------------------------------------------------------------
# SECTION 12: MAIN FUNCTION
# ---------------------------------------------------------------------------

def main():
    """
    Orchestrate all Phase 4 steps in order.
    """
    print("=" * 55)
    print("  Phase 4 - Baseline Risk Detection")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)

    # Step 1: Load the cleaned dataset
    df = load_data(INPUT_FILE)

    # Step 2: Apply risk detection rules to every row
    print("\nApplying risk detection rules ...")
    df = apply_risk_to_dataset(df)

    # Step 3: Save results to a new CSV
    save_results(df, OUTPUT_FILE)

    # Step 4: Print risk summary and first 10 rows
    show_summary(df)

    # Step 5: Verify that key test cases exist in the output
    verify_test_cases(df)

    print("[DONE] Phase 4 complete.")
    print("  Input  : data/cleaned_maternal_data.csv  (unchanged)")
    print("  Output : data/baseline_risk_results.csv")
    print("\n  Do NOT start Phase 5 yet.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
