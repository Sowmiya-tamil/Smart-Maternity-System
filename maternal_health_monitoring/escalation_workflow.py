# escalation_workflow.py
# Phase 7 - Escalation Workflow, Capacity Limits and Safe Fallback
# Remote Maternal Health Monitoring and Escalation System
#
# This script reads the conflict detection results and decides:
#   - What priority each case gets
#   - Which escalation pathway to follow
#   - How to simulate communication attempts
#   - How to store offline cases for later forwarding
#   - How to handle clinician capacity limits
#
# IMPORTANT:
#   - This is a student prototype using simulated data only.
#   - These workflow rules are for software demonstration purposes only.
#   - No real SMS, phone, or API calls are made.
#   - Do NOT use this output to make real clinical decisions.

import os
import sys
import pandas as pd

# Import conflict detection logic so we can apply it to demo cases.
# This import is safe because conflict_detection.py only defines functions
# at module level — no file loading happens when it is imported.
from conflict_detection import detect_conflict

# ---------------------------------------------------------------------------
# SECTION 1: FILE PATHS AND CONFIGURATION
# ---------------------------------------------------------------------------

CONFLICT_FILE = os.path.join("data", "conflict_results.csv")
DEMO_FILE     = os.path.join("data", "demo_conflict_cases.csv")
OUTPUT_FILE   = os.path.join("data", "escalation_results.csv")

# Simulated clinician capacity:
# Only this many HIGH/CRITICAL cases can be handled immediately in one cycle.
MAX_HIGH_PRIORITY_CASES = 10


# ---------------------------------------------------------------------------
# SECTION 2: LOAD DATA
# ---------------------------------------------------------------------------

def load_data(filepath):
    """
    Load a CSV file. Show a clear message and stop if the file is missing.
    """
    if not os.path.exists(filepath):
        print(f"\n[ERROR] File not found: {filepath}")
        print("  Please run conflict_detection.py first.\n")
        sys.exit(1)

    df = pd.read_csv(filepath)
    print(f"[OK] Loaded: {filepath} ({len(df)} rows)")
    return df


# ---------------------------------------------------------------------------
# SECTION 3: ASSIGN PRIORITY
# ---------------------------------------------------------------------------

def assign_priority(row):
    """
    Assign a priority level to one observation record.

    Rules (checked in this exact order):
    1. UNTRUSTED: data cannot be trusted — never classify as LOW.
    2. CRITICAL : sensor and symptoms are both strongly concerning.
    3. HIGH     : sensor risk is high, or a sensor-symptom conflict exists.
    4. MEDIUM   : moderate sensor-based concern.
    5. LOW      : everything within normal prototype ranges.
    """
    risk_level      = str(row.get("risk_level",      "UNCERTAIN"))
    data_quality    = str(row.get("data_quality",    "Good"))
    conflict_status = str(row.get("conflict_status", "NO CONFLICT"))
    signal_agreement = str(row.get("signal_agreement", ""))

    # --- Rule 1: UNTRUSTED ---
    # Any missing, invalid, or conflicting data prevents a safe assessment.
    if (data_quality in ("Incomplete", "Invalid")
            or risk_level == "UNCERTAIN"
            or conflict_status == "INSUFFICIENT DATA"):
        return "UNTRUSTED"

    # --- Rule 2: CRITICAL ---
    # The baseline risk is CRITICAL.
    if risk_level == "CRITICAL":
        return "CRITICAL"

    # HIGH sensor risk AND symptoms are also concerning → CRITICAL escalation.
    if risk_level == "HIGH" and "both concerning" in signal_agreement:
        return "CRITICAL"

    # --- Rule 3: HIGH ---
    # Sensor risk is HIGH (but symptoms are absent or partially absent).
    if risk_level == "HIGH":
        return "HIGH"

    # A sensor-symptom conflict means sensors look okay but symptoms are alarming.
    # Safety rule: never downgrade this case to LOW.
    if conflict_status == "SENSOR-SYMPTOM CONFLICT":
        return "HIGH"

    # --- Rule 4: MEDIUM ---
    if risk_level == "MEDIUM":
        return "MEDIUM"

    # --- Rule 5: LOW ---
    return "LOW"


# ---------------------------------------------------------------------------
# SECTION 4: ASSIGN ESCALATION PATHWAY
# ---------------------------------------------------------------------------

def assign_escalation_path(priority):
    """
    Map a priority level to the appropriate escalation pathway.
    """
    mapping = {
        "LOW":       "CONTINUE_MONITORING",
        "MEDIUM":    "SCHEDULE_FOLLOW_UP",
        "HIGH":      "CLINICIAN_REVIEW",
        "CRITICAL":  "URGENT_CLINICIAN_REVIEW",
        "UNTRUSTED": "SAFE_FALLBACK",
    }
    return mapping.get(priority, "SAFE_FALLBACK")


# ---------------------------------------------------------------------------
# SECTION 5: SIMULATE COMMUNICATION
# ---------------------------------------------------------------------------

def handle_communication(row, escalation_path):
    """
    Simulate a communication attempt based on internet status.
    No real APIs are used — this is workflow simulation only.

    Returns (communication_attempt, communication_result).
    """
    internet     = str(row.get("internet_status",      "Online"))
    comm_status  = str(row.get("communication_status", "Not Required"))

    # Routine monitoring cases do not require active communication.
    if escalation_path == "CONTINUE_MONITORING":
        return ("NOT_REQUIRED",
                "No communication required for routine monitoring.")

    # Offline: store the case locally and forward when connectivity returns.
    if internet == "Offline":
        return ("STORED_FOR_FORWARD",
                "Case stored locally for later transmission when connectivity returns.")

    # Online: simulate a first communication attempt.
    if comm_status == "Completed":
        return ("FIRST_ATTEMPT", "Clinician contact completed.")
    elif comm_status == "Pending":
        return ("FIRST_ATTEMPT", "Clinician contact pending.")
    elif comm_status == "Failed":
        return ("FIRST_ATTEMPT", "First communication attempt failed.")
    else:
        return ("NOT_REQUIRED", "Communication not required for this case.")


# ---------------------------------------------------------------------------
# SECTION 6: HANDLE STORE-AND-FORWARD
# ---------------------------------------------------------------------------

def handle_store_forward(row, escalation_path):
    """
    Decide whether an offline case should be stored for later forwarding.

    Important: offline cases requiring escalation are STORED, not discarded.
    """
    internet = str(row.get("internet_status", "Online"))

    if internet == "Offline" and escalation_path != "CONTINUE_MONITORING":
        return "STORED"

    return "NOT_REQUIRED"


# ---------------------------------------------------------------------------
# SECTION 7: CREATE FINAL ACTION
# ---------------------------------------------------------------------------

def create_final_action(priority, conflict_status):
    """
    Return a short, plain-English description of what should happen next.
    """
    if priority == "CRITICAL":
        return "Urgent clinician review required."

    if priority == "HIGH":
        if conflict_status == "SENSOR-SYMPTOM CONFLICT":
            return "Clinician review required because sensor and symptoms disagree."
        if conflict_status == "SENSOR-ONLY CONCERN":
            return "Repeat measurement and clinician review."
        return "Clinician review required."

    if priority == "MEDIUM":
        return "Schedule clinician follow-up."

    if priority == "LOW":
        return "Continue routine monitoring."

    # UNTRUSTED
    return "Repeat measurement and clinician review."


# ---------------------------------------------------------------------------
# SECTION 8: CREATE ESCALATION REASON
# ---------------------------------------------------------------------------

def create_escalation_reason(row, priority, conflict_status):
    """
    Return a plain-English explanation of why this escalation decision was made.
    """
    internet = str(row.get("internet_status", "Online"))

    if priority == "UNTRUSTED":
        return ("Data quality is insufficient; recommendation cannot be trusted. "
                "Repeat measurement and route to clinician review.")

    if conflict_status == "SENSOR-SYMPTOM CONFLICT":
        return ("Sensor readings and patient-reported symptoms disagree; "
                "human review is required.")

    if conflict_status == "SENSOR-ONLY CONCERN":
        reason = ("Sensor-based concern is present without matching reported "
                  "symptoms. ")
        if internet == "Offline":
            reason += "Case is offline and has been stored for forwarding."
        return reason

    if priority == "CRITICAL":
        reason = ("High sensor-based concern with matching symptoms; "
                  "urgent referral required.")
        if internet == "Offline":
            reason += " Case is offline and has been stored for forwarding."
        return reason

    if priority == "HIGH":
        return "High sensor-based concern requires clinician review."

    if priority == "MEDIUM":
        return "Moderate risk requires scheduled follow-up."

    return "Low-risk observation with no concerning symptoms."


# ---------------------------------------------------------------------------
# SECTION 9: APPLY ALL ESCALATION LOGIC ROW BY ROW
# ---------------------------------------------------------------------------

def apply_escalation(df):
    """
    Loop through every row and compute all escalation columns.
    Returns the DataFrame with new columns appended.
    """
    priorities          = []
    escalation_paths    = []
    comm_attempts       = []
    comm_results        = []
    store_forward_list  = []
    final_actions       = []
    escalation_reasons  = []

    for _, row in df.iterrows():

        priority        = assign_priority(row)
        escalation_path = assign_escalation_path(priority)
        conflict_status = str(row.get("conflict_status", "NO CONFLICT"))

        comm_attempt, comm_result = handle_communication(row, escalation_path)
        store_forward  = handle_store_forward(row, escalation_path)
        final_action   = create_final_action(priority, conflict_status)
        esc_reason     = create_escalation_reason(row, priority, conflict_status)

        priorities.append(priority)
        escalation_paths.append(escalation_path)
        comm_attempts.append(comm_attempt)
        comm_results.append(comm_result)
        store_forward_list.append(store_forward)
        final_actions.append(final_action)
        escalation_reasons.append(esc_reason)

    result = df.copy()
    result["priority"]              = priorities
    result["escalation_path"]       = escalation_paths
    result["communication_attempt"] = comm_attempts
    result["communication_result"]  = comm_results
    result["store_forward_status"]  = store_forward_list
    result["final_action"]          = final_actions
    result["escalation_reason"]     = escalation_reasons

    return result


# ---------------------------------------------------------------------------
# SECTION 10: HANDLE CLINICIAN CAPACITY
# ---------------------------------------------------------------------------

def handle_capacity(df):
    """
    Apply the clinician capacity limit (MAX_HIGH_PRIORITY_CASES).

    - CRITICAL cases are sorted first, then HIGH.
    - The first MAX_HIGH_PRIORITY_CASES combined HIGH/CRITICAL cases
      get capacity_status = 'WITHIN_CAPACITY'.
    - Remaining HIGH/CRITICAL cases get 'QUEUED' and 'QUEUED_NEXT_SLOT'.
    - All other priorities get 'NOT_APPLICABLE'.

    Schedule status is also assigned here.
    """
    result = df.copy()

    # Default values
    result["capacity_status"] = "NOT_APPLICABLE"
    result["schedule_status"] = "NOT_REQUIRED"

    # Assign schedule_status for each row (independent of capacity)
    for idx, row in result.iterrows():
        p = row["priority"]
        if p == "MEDIUM":
            result.at[idx, "schedule_status"] = "SCHEDULED"
        elif p in ("HIGH", "CRITICAL"):
            result.at[idx, "schedule_status"] = "IMMEDIATE_REVIEW"
        elif p == "UNTRUSTED":
            result.at[idx, "schedule_status"] = "SAFE_FALLBACK_REVIEW"
        # LOW stays NOT_REQUIRED

    # Find all HIGH/CRITICAL rows and sort CRITICAL before HIGH
    high_crit_mask    = result["priority"].isin(["CRITICAL", "HIGH"])
    sorted_hc_indices = result[high_crit_mask].sort_values(
        by="priority",
        key=lambda s: s.map({"CRITICAL": 0, "HIGH": 1})
    ).index.tolist()

    # Apply capacity limit
    for rank, idx in enumerate(sorted_hc_indices):
        if rank < MAX_HIGH_PRIORITY_CASES:
            result.at[idx, "capacity_status"] = "WITHIN_CAPACITY"
        else:
            result.at[idx, "capacity_status"] = "QUEUED"
            result.at[idx, "schedule_status"] = "QUEUED_NEXT_SLOT"

    return result


# ---------------------------------------------------------------------------
# SECTION 11: SAVE RESULTS
# ---------------------------------------------------------------------------

def save_results(df, output_path):
    """
    Save the escalation-annotated DataFrame to a new CSV.
    None of the existing input files are modified.
    """
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\n[OK] Escalation results saved to: {output_path}")


# ---------------------------------------------------------------------------
# SECTION 12: PRINT SUMMARY
# ---------------------------------------------------------------------------

def show_summary(df):
    """
    Print a clear, readable summary of the full escalation workflow results.
    """
    total = len(df)

    priority_counts = df["priority"].value_counts()
    path_counts     = df["escalation_path"].value_counts()

    # Communication breakdowns
    completed = df["communication_result"].str.contains(
        "completed", case=False, na=False).sum()
    pending   = df["communication_result"].str.contains(
        "pending", case=False, na=False).sum()
    failed    = df["communication_result"].str.contains(
        "failed", case=False, na=False).sum()
    stored    = (df["communication_attempt"] == "STORED_FOR_FORWARD").sum()

    within_cap = (df["capacity_status"] == "WITHIN_CAPACITY").sum()
    queued     = (df["capacity_status"] == "QUEUED").sum()

    print("\n" + "=" * 50)
    print("  PHASE 7 - ESCALATION WORKFLOW")
    print("=" * 50)

    print(f"\n  Total cases processed: {total}")

    print("\n  Priority:")
    print(f"    LOW       -> {priority_counts.get('LOW',       0)}")
    print(f"    MEDIUM    -> {priority_counts.get('MEDIUM',    0)}")
    print(f"    HIGH      -> {priority_counts.get('HIGH',      0)}")
    print(f"    CRITICAL  -> {priority_counts.get('CRITICAL',  0)}")
    print(f"    UNTRUSTED -> {priority_counts.get('UNTRUSTED', 0)}")

    print("\n  Escalation Pathways:")
    print(f"    CONTINUE_MONITORING      -> {path_counts.get('CONTINUE_MONITORING',     0)}")
    print(f"    SCHEDULE_FOLLOW_UP       -> {path_counts.get('SCHEDULE_FOLLOW_UP',      0)}")
    print(f"    CLINICIAN_REVIEW         -> {path_counts.get('CLINICIAN_REVIEW',        0)}")
    print(f"    URGENT_CLINICIAN_REVIEW  -> {path_counts.get('URGENT_CLINICIAN_REVIEW', 0)}")
    print(f"    SAFE_FALLBACK            -> {path_counts.get('SAFE_FALLBACK',           0)}")

    print("\n  Communication:")
    print(f"    Completed          : {completed}")
    print(f"    Pending            : {pending}")
    print(f"    Failed             : {failed}")
    print(f"    Stored for Forward : {stored}")

    print(f"\n  Capacity (limit = {MAX_HIGH_PRIORITY_CASES} HIGH/CRITICAL cases):")
    print(f"    Within Capacity : {within_cap}")
    print(f"    Queued          : {queued}")

    print("\n" + "=" * 50)


# ---------------------------------------------------------------------------
# SECTION 13: PROCESS AND DISPLAY DEMONSTRATION CASES
# ---------------------------------------------------------------------------

def process_demo_cases():
    """
    Load demo_conflict_cases.csv, run conflict detection and escalation on
    each row, and display clearly formatted results.

    The demo cases are deliberately constructed to show every scenario.
    They are NOT real patient records.
    """
    if not os.path.exists(DEMO_FILE):
        print(f"\n[WARN] Demo file not found: {DEMO_FILE}")
        return

    demo_df = pd.read_csv(DEMO_FILE)
    print(f"\n[OK] Loaded demo cases: {DEMO_FILE} ({len(demo_df)} rows)")

    # Step 1: Apply conflict detection (same function used in Phase 6)
    conflict_cols = demo_df.apply(detect_conflict, axis=1, result_type="expand")
    demo_df = pd.concat([demo_df, conflict_cols], axis=1)

    # Step 2: Apply escalation logic
    demo_df = apply_escalation(demo_df)

    # Step 3: Apply capacity (demo cases are few; all will be within capacity)
    demo_df = handle_capacity(demo_df)

    # Step 4: Print results
    print("\n" + "-" * 55)
    print("  DEMONSTRATION CASES (Simulated — Not Real Patients)")
    print("-" * 55)

    for _, row in demo_df.iterrows():
        pid = row["patient_id"]
        rl  = row.get("risk_level",          "")
        dq  = row.get("data_quality",        "")
        cs  = row.get("conflict_status",     "")
        sa  = row.get("signal_agreement",    "")
        pri = row["priority"]
        ep  = row["escalation_path"]
        ca  = row["communication_attempt"]
        cr  = row["communication_result"]
        sf  = row["store_forward_status"]
        ss  = row["schedule_status"]
        fa  = row["final_action"]
        er  = row["escalation_reason"]
        net = row.get("internet_status", "Online")

        # Build a short symptom summary
        syms = ", ".join(
            col for col in [
                "headache", "blurred_vision", "bleeding",
                "abdominal_pain", "swelling", "reduced_fetal_movement"
            ]
            if row.get(col) == "Yes"
        ) or "None"

        print(f"\n  {pid}")
        print(f"    risk_level            : {rl}")
        print(f"    data_quality          : {dq}")
        print(f"    internet_status       : {net}")
        print(f"    symptoms present      : {syms}")
        print(f"    conflict_status       : {cs}")
        print(f"    signal_agreement      : {sa}")
        print(f"    priority          --> : {pri}")
        print(f"    escalation_path       : {ep}")
        print(f"    communication_attempt : {ca}")
        print(f"    communication_result  : {cr}")
        print(f"    store_forward_status  : {sf}")
        print(f"    schedule_status       : {ss}")
        print(f"    final_action          : {fa}")
        print(f"    escalation_reason     : {er}")

    print()
    print("-" * 55)


# ---------------------------------------------------------------------------
# SECTION 14: VERIFY INPUT FILES ARE UNCHANGED
# ---------------------------------------------------------------------------

def verify_inputs_unchanged():
    """
    Confirm all upstream input files still exist and print their row counts.
    """
    print("-" * 50)
    print("  INPUT FILE STATUS")
    print("-" * 50)

    files_to_check = [
        os.path.join("data", "simulated_maternal_data.csv"),
        os.path.join("data", "cleaned_maternal_data.csv"),
        os.path.join("data", "baseline_risk_results.csv"),
        os.path.join("data", "trend_results.csv"),
        os.path.join("data", "conflict_results.csv"),
    ]

    for filepath in files_to_check:
        if os.path.exists(filepath):
            tmp = pd.read_csv(filepath)
            print(f"  {filepath}: {len(tmp)} rows (unchanged)")
        else:
            print(f"  {filepath}: NOT FOUND")

    print()


# ---------------------------------------------------------------------------
# SECTION 15: MAIN FUNCTION
# ---------------------------------------------------------------------------

def main():
    """
    Run all Phase 7 escalation steps in order.
    """
    print("=" * 55)
    print("  Phase 7 - Escalation Workflow")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)

    # Step 1: Load the conflict detection results (994 real records)
    df = load_data(CONFLICT_FILE)

    # Step 2: Assign priority and escalation pathway to every row
    print("\nAssigning priorities and escalation pathways ...")
    df = apply_escalation(df)

    # Step 3: Apply clinician capacity limits
    print("Applying clinician capacity limits ...")
    df = handle_capacity(df)

    # Step 4: Save the escalation results to a new CSV
    save_results(df, OUTPUT_FILE)

    # Step 5: Print the escalation summary
    show_summary(df)

    # Step 6: Process and display the demo cases
    process_demo_cases()

    # Step 7: Confirm all upstream files are unchanged
    verify_inputs_unchanged()

    print("[DONE] Phase 7 complete.")
    print("  Output : data/escalation_results.csv")
    print("\n  Do NOT start Phase 8 yet.\n")


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
