# clean_data.py
# Phase 3 - Data Cleaning and Validation
# Remote Maternal Health Monitoring and Escalation System
#
# This script loads the simulated dataset, checks for problems,
# marks each record with a data quality status, and saves a
# cleaned version ready for the next phase.
#
# NOTE: This script does NOT make clinical decisions.
#       It only checks whether the simulated data values are
#       within reasonable ranges for a prototype system.

import os
import sys
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# SECTION 1: FILE PATHS
# ---------------------------------------------------------------------------

INPUT_FILE  = os.path.join("data", "simulated_maternal_data.csv")
OUTPUT_FILE = os.path.join("data", "cleaned_maternal_data.csv")

# ---------------------------------------------------------------------------
# SECTION 2: VALIDATION RANGES
# ---------------------------------------------------------------------------
# These are simple data-quality boundary checks for the simulated prototype.
# They are NOT official medical diagnostic thresholds.

VALID_RANGES = {
    "systolic_bp":  (50, 250),   # values outside this range are impossible
    "diastolic_bp": (30, 160),
    "heart_rate":   (30, 200),
    "temperature":  (33.0, 43.0),
    "spo2":         (50, 100),
    "pregnancy_week": (4, 45),
}

# Valid categorical values for each column
VALID_SYMPTOMS = {"Yes", "No"}

VALID_INTERNET_STATUS = {"Online", "Offline"}

VALID_COMMUNICATION_STATUS = {"Not Required", "Pending", "Completed", "Failed"}

VALID_CLINICIAN_DECISION = {
    "Continue Monitoring",
    "Schedule Follow-up",
    "Clinician Review",
    "Immediate Referral",
}

# These are the sensor columns we consider "important" for quality flagging
IMPORTANT_SENSOR_COLS = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "spo2"]

SYMPTOM_COLS = [
    "headache", "blurred_vision", "bleeding",
    "abdominal_pain", "swelling", "reduced_fetal_movement",
]


# ---------------------------------------------------------------------------
# SECTION 3: LOAD DATA
# ---------------------------------------------------------------------------

def load_data(filepath):
    """
    Load the CSV file into a Pandas DataFrame.
    If the file does not exist, show a clear error and stop.
    """
    if not os.path.exists(filepath):
        print(f"\n[ERROR] File not found: {filepath}")
        print("  Please run generate_data.py first to create the dataset.\n")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"[OK] Loaded dataset: {filepath}")
    print(f"     Rows: {len(df)}, Columns: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# SECTION 4: REMOVE DUPLICATES
# ---------------------------------------------------------------------------

def remove_duplicates(df):
    """
    Remove exact duplicate rows from the DataFrame.
    A duplicate means every column has the same value.
    Different observation days for the same patient are NOT duplicates.
    """
    before = len(df)
    df = df.drop_duplicates()
    after  = len(df)
    removed = before - after

    print(f"\n[Duplicates]")
    print(f"  Duplicate rows found  : {removed}")
    print(f"  Rows after removal    : {after}")

    return df, removed


# ---------------------------------------------------------------------------
# SECTION 5: VALIDATE SENSOR VALUES
# ---------------------------------------------------------------------------

def validate_sensor_data(df):
    """
    Check each important sensor column for values that fall outside the
    valid range defined in VALID_RANGES.
    When an invalid value is found:
      - Replace it with NaN (so it is treated as missing, not wrong)
      - Record which rows were affected so we can mark them later.

    Returns the modified DataFrame and a boolean Series where True means
    this row had at least one invalid sensor reading.
    """
    # Track which rows have invalid sensors (one True/False per row)
    invalid_sensor_mask = pd.Series(False, index=df.index)

    print(f"\n[Sensor Validation]")

    for col in IMPORTANT_SENSOR_COLS:
        if col not in df.columns:
            continue   # skip if column is missing from the file

        low, high = VALID_RANGES[col]

        # Find rows where the value is not NaN AND outside the valid range
        out_of_range = df[col].notna() & ((df[col] < low) | (df[col] > high))
        count = out_of_range.sum()

        if count > 0:
            print(f"  {col}: {count} invalid value(s) replaced with NaN"
                  f"  (valid range: {low} to {high})")
            # Replace the invalid values with NaN
            df.loc[out_of_range, col] = np.nan
            # Mark those rows as having had an invalid reading
            invalid_sensor_mask = invalid_sensor_mask | out_of_range
        else:
            print(f"  {col}: OK (no out-of-range values)")

    return df, invalid_sensor_mask


# ---------------------------------------------------------------------------
# SECTION 6: VALIDATE SYMPTOM COLUMNS
# ---------------------------------------------------------------------------

def validate_symptoms(df):
    """
    Check that every symptom column contains only 'Yes' or 'No'.
    If an unexpected value is found:
      - Report it clearly.
      - Mark that row as having an invalid entry.

    Returns the DataFrame and a boolean Series of rows with bad symptom values.
    """
    invalid_symptom_mask = pd.Series(False, index=df.index)

    print(f"\n[Symptom Validation]")

    for col in SYMPTOM_COLS:
        if col not in df.columns:
            continue

        # Find rows with values other than Yes/No (ignore NaN)
        bad = df[col].notna() & ~df[col].isin(VALID_SYMPTOMS)
        count = bad.sum()

        if count > 0:
            bad_values = df.loc[bad, col].unique().tolist()
            print(f"  {col}: {count} unexpected value(s) found -> {bad_values}")
            invalid_symptom_mask = invalid_symptom_mask | bad
        else:
            print(f"  {col}: OK")

    return df, invalid_symptom_mask


# ---------------------------------------------------------------------------
# SECTION 7: VALIDATE PREGNANCY WEEK
# ---------------------------------------------------------------------------

def validate_pregnancy_week(df):
    """
    Check that pregnancy_week is within the valid range.
    Flag rows where the value is missing or clearly impossible.

    Returns a boolean Series of rows with an invalid pregnancy_week.
    """
    invalid_preg_mask = pd.Series(False, index=df.index)

    print(f"\n[Pregnancy Week Validation]")

    col = "pregnancy_week"
    if col not in df.columns:
        print(f"  Column '{col}' not found. Skipping.")
        return invalid_preg_mask

    low, high = VALID_RANGES[col]

    # Missing pregnancy week
    missing = df[col].isna()
    missing_count = missing.sum()

    # Out-of-range pregnancy week
    out_of_range = df[col].notna() & ((df[col] < low) | (df[col] > high))
    out_count = out_of_range.sum()

    if missing_count > 0:
        print(f"  {col}: {missing_count} missing value(s)")
        invalid_preg_mask = invalid_preg_mask | missing

    if out_count > 0:
        print(f"  {col}: {out_count} out-of-range value(s) (valid: {low}-{high})")
        df.loc[out_of_range, col] = np.nan
        invalid_preg_mask = invalid_preg_mask | out_of_range

    if missing_count == 0 and out_count == 0:
        print(f"  {col}: OK")

    return invalid_preg_mask


# ---------------------------------------------------------------------------
# SECTION 8: VALIDATE CATEGORICAL STATUS COLUMNS
# ---------------------------------------------------------------------------

def validate_status_columns(df):
    """
    Check internet_status, communication_status, and clinician_decision
    for unexpected values.
    Returns a boolean Series of rows with bad status values.
    """
    invalid_status_mask = pd.Series(False, index=df.index)

    checks = {
        "internet_status":      VALID_INTERNET_STATUS,
        "communication_status": VALID_COMMUNICATION_STATUS,
        "clinician_decision":   VALID_CLINICIAN_DECISION,
    }

    print(f"\n[Status Column Validation]")

    for col, valid_set in checks.items():
        if col not in df.columns:
            continue

        bad = df[col].notna() & ~df[col].isin(valid_set)
        count = bad.sum()

        if count > 0:
            bad_values = df.loc[bad, col].unique().tolist()
            print(f"  {col}: {count} unexpected value(s) -> {bad_values}")
            invalid_status_mask = invalid_status_mask | bad
        else:
            print(f"  {col}: OK")

    return invalid_status_mask


# ---------------------------------------------------------------------------
# SECTION 9: CHECK MISSING VALUES IN IMPORTANT COLUMNS
# ---------------------------------------------------------------------------

def check_missing_values(df):
    """
    Print the number of missing values in each important sensor column.
    Returns a boolean Series where True means at least one important
    sensor reading is missing for that row.
    """
    print(f"\n[Missing Value Check]")

    missing_any_mask = pd.Series(False, index=df.index)

    for col in IMPORTANT_SENSOR_COLS:
        if col not in df.columns:
            continue
        missing = df[col].isna()
        count = missing.sum()
        print(f"  {col}: {count} missing")
        missing_any_mask = missing_any_mask | missing

    total_missing = df[IMPORTANT_SENSOR_COLS].isna().sum().sum()
    print(f"  Total missing sensor values: {total_missing}")

    return missing_any_mask


# ---------------------------------------------------------------------------
# SECTION 10: ASSIGN DATA QUALITY STATUS
# ---------------------------------------------------------------------------

def create_quality_status(df, invalid_sensor_mask, invalid_symptom_mask,
                           invalid_preg_mask, invalid_status_mask,
                           missing_sensor_mask):
    """
    Add a new column called 'data_quality' to each row.

    Rules (applied in order of priority):
    1. If a sensor value was replaced because it was impossible -> "Invalid"
    2. If a symptom or status column has an unexpected value   -> "Invalid"
    3. If a pregnancy week was invalid or missing              -> "Invalid"
    4. If any important sensor reading is still NaN            -> "Incomplete"
    5. Otherwise                                               -> "Good"

    Note: A record can be both missing AND invalid; we give "Invalid" priority.
    """

    # Start every row as "Good"
    df["data_quality"] = "Good"

    # Mark incomplete rows (missing sensor values)
    df.loc[missing_sensor_mask, "data_quality"] = "Incomplete"

    # Mark invalid rows (bad sensor values, symptoms, or status columns)
    # Invalid overrides Incomplete
    any_invalid = (invalid_sensor_mask | invalid_symptom_mask |
                   invalid_preg_mask   | invalid_status_mask)
    df.loc[any_invalid, "data_quality"] = "Invalid"

    print(f"\n[Data Quality Status assigned]")

    return df


# ---------------------------------------------------------------------------
# SECTION 11: SAVE CLEANED DATASET
# ---------------------------------------------------------------------------

def save_cleaned_data(df, output_path):
    """
    Save the cleaned DataFrame to a new CSV file.
    The original simulated file is NOT overwritten.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Cleaned dataset saved to: {output_path}")


# ---------------------------------------------------------------------------
# SECTION 12: PRINT CLEANING REPORT
# ---------------------------------------------------------------------------

def print_cleaning_report(original_rows, removed_duplicates, df):
    """
    Print a simple, readable cleaning report to the terminal.
    """
    final_rows = len(df)

    total_missing = df[IMPORTANT_SENSOR_COLS].isna().sum().sum()

    quality_counts = df["data_quality"].value_counts()
    good_count       = quality_counts.get("Good",       0)
    incomplete_count = quality_counts.get("Incomplete", 0)
    invalid_count    = quality_counts.get("Invalid",    0)

    print("\n" + "-" * 40)
    print("  DATA CLEANING REPORT")
    print("-" * 40)
    print(f"  Original rows         : {original_rows}")
    print(f"  Duplicate rows removed: {removed_duplicates}")
    print(f"  Final rows            : {final_rows}")
    print()
    print(f"  Missing sensor values : {total_missing}")
    print()
    print(f"  Good records          : {good_count}")
    print(f"  Incomplete records    : {incomplete_count}")
    print(f"  Invalid records       : {invalid_count}")
    print("-" * 40)

    print("\nFirst 5 rows of cleaned dataset:")
    print(df.head(5).to_string())

    print("\n" + "-" * 40)
    print("  DATA QUALITY SUMMARY")
    print("-" * 40)
    print(f"  Good       -> {good_count} records")
    print(f"  Incomplete -> {incomplete_count} records")
    print(f"  Invalid    -> {invalid_count} records")
    print("-" * 40)


# ---------------------------------------------------------------------------
# SECTION 13: MAIN FUNCTION
# ---------------------------------------------------------------------------

def main():
    """
    Run all cleaning steps in order and save the cleaned dataset.
    This is the only function that calls all the other functions.
    """

    print("=" * 55)
    print("  Phase 3 - Data Cleaning and Validation")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)

    # Step 1: Load the raw simulated data
    df = load_data(INPUT_FILE)
    original_rows = len(df)

    # Step 2: Remove exact duplicate rows
    df, removed_duplicates = remove_duplicates(df)

    # Step 3: Validate sensor values (replace impossible values with NaN)
    df, invalid_sensor_mask = validate_sensor_data(df)

    # Step 4: Validate symptom columns (check for unexpected Yes/No values)
    df, invalid_symptom_mask = validate_symptoms(df)

    # Step 5: Validate pregnancy_week
    invalid_preg_mask = validate_pregnancy_week(df)

    # Step 6: Validate status columns
    invalid_status_mask = validate_status_columns(df)

    # Step 7: Check for remaining missing sensor values (after replacing invalid ones)
    missing_sensor_mask = check_missing_values(df)

    # Step 8: Assign data_quality label to every row
    df = create_quality_status(
        df,
        invalid_sensor_mask,
        invalid_symptom_mask,
        invalid_preg_mask,
        invalid_status_mask,
        missing_sensor_mask,
    )

    # Step 9: Save the cleaned dataset (original file is NOT changed)
    save_cleaned_data(df, OUTPUT_FILE)

    # Step 10: Print the final report
    print_cleaning_report(original_rows, removed_duplicates, df)

    print("\n[DONE] Phase 3 complete.")
    print("  Original data : data/simulated_maternal_data.csv  (unchanged)")
    print("  Cleaned data  : data/cleaned_maternal_data.csv")
    print("\n  Do NOT start Phase 4 yet.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
