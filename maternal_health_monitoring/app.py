# app.py
# Phase 8 - Functional Streamlit Application
# Remote Maternal Health Monitoring and Escalation System
#
# This application demonstrates the complete simulated monitoring workflow
# built across Phases 2-7.
#
# IMPORTANT:
#   - This is a student prototype using simulated data only.
#   - All patient IDs are anonymous (P001-P100, DEMO001-DEMO006).
#   - This application is NOT a medical diagnostic system.
#   - Do NOT use this output to make real clinical decisions.

import os
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# IMPORT WORKFLOW FUNCTIONS FROM PREVIOUS PHASES
#
# These imports are safe because each script uses:
#   if __name__ == "__main__": main()
# so their pipeline code does not run when they are imported.
# ---------------------------------------------------------------------------

from risk_detection import calculate_risk
from conflict_detection import detect_conflict
from escalation_workflow import (
    assign_priority,
    assign_escalation_path,
    handle_communication,
    handle_store_forward,
    create_final_action,
    create_escalation_reason,
    apply_escalation,
    handle_capacity,
)

# ---------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Maternal Health Monitoring System",
    page_icon="health_worker",
    layout="wide",
)

# ---------------------------------------------------------------------------
# FILE PATHS
# ---------------------------------------------------------------------------

ESCALATION_FILE = os.path.join("data", "escalation_results.csv")
CLEANED_FILE    = os.path.join("data", "cleaned_maternal_data.csv")
DEMO_FILE       = os.path.join("data", "demo_conflict_cases.csv")

# Sort order for displaying priorities (most urgent first)
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "UNTRUSTED": 2, "MEDIUM": 3, "LOW": 4}

# Short explanation for each demo case shown on the Conflict Demo page
DEMO_EXPLANATIONS = {
    "DEMO001": (
        "**Scenario:** LOW sensor risk + headache and blurred vision reported.\n\n"
        "**Expected result:** SENSOR-SYMPTOM CONFLICT → Clinician Review.\n\n"
        "Demonstrates that normal-looking sensor readings do NOT override "
        "concerning patient-reported symptoms."
    ),
    "DEMO002": (
        "**Scenario:** HIGH sensor risk + no concerning symptoms.\n\n"
        "**Expected result:** SENSOR-ONLY CONCERN → Repeat Measurement / Clinician Review.\n\n"
        "Demonstrates that an abnormal sensor reading is not dismissed just "
        "because the patient has not reported symptoms."
    ),
    "DEMO003": (
        "**Scenario:** HIGH sensor risk + headache and blurred vision — both signals agree.\n\n"
        "**Expected result:** Both signals concerning → CRITICAL → Urgent Clinician Review.\n\n"
        "Demonstrates agreement between sensor concern and reported symptoms."
    ),
    "DEMO004": (
        "**Scenario:** UNCERTAIN risk + Incomplete data + Offline connection.\n\n"
        "**Expected result:** INSUFFICIENT DATA → UNTRUSTED → Safe Fallback.\n\n"
        "Demonstrates that the system NEVER classifies incomplete data as LOW risk."
    ),
    "DEMO005": (
        "**Scenario:** LOW sensor risk + no concerning symptoms + Good data quality.\n\n"
        "**Expected result:** NO CONFLICT → LOW → Continue Monitoring.\n\n"
        "Demonstrates a fully reassuring case where no escalation is needed."
    ),
    "DEMO006": (
        "**Scenario:** HIGH sensor risk + concerning symptoms + OFFLINE connection.\n\n"
        "**Expected result:** CRITICAL → Urgent Clinician Review + Store-and-Forward.\n\n"
        "Demonstrates that an offline critical case is stored locally "
        "and NOT discarded."
    ),
}


# ---------------------------------------------------------------------------
# HELPER FUNCTION: LOAD CSV SAFELY
# ---------------------------------------------------------------------------

def load_csv(filepath):
    """
    Load a CSV file. Display a Streamlit error and return None if file is missing.
    """
    if not os.path.exists(filepath):
        st.error(
            f"**Required data file not found:** `{filepath}`\n\n"
            "Please run the previous project phases first in this order:\n\n"
            "`python generate_data.py` → `python clean_data.py` → "
            "`python risk_detection.py` → `python trend_analysis.py` → "
            "`python conflict_detection.py` → `python escalation_workflow.py`"
        )
        return None
    return pd.read_csv(filepath)


# ---------------------------------------------------------------------------
# PAGE 1: DASHBOARD
# ---------------------------------------------------------------------------

def show_dashboard():
    """
    Display summary metrics and two charts from the escalation results dataset.
    """
    st.title("Dashboard")
    st.caption(
        "Overview of all simulated patient observations processed through "
        "the Phase 2-7 workflow."
    )

    df = load_csv(ESCALATION_FILE)
    if df is None:
        return

    total = len(df)

    # Count each priority level
    p = df["priority"].value_counts() if "priority" in df.columns else pd.Series()

    # Count offline and capacity metrics
    offline_count = int((df["internet_status"] == "Offline").sum()) \
        if "internet_status" in df.columns else 0
    stored_count  = int((df["store_forward_status"] == "STORED").sum()) \
        if "store_forward_status" in df.columns else 0
    queued_count  = int((df["capacity_status"] == "QUEUED").sum()) \
        if "capacity_status" in df.columns else 0

    # --- Row 1: Priority counts ---
    st.subheader("Priority Overview")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Observations", total)
    c2.metric("LOW",                int(p.get("LOW",       0)))
    c3.metric("MEDIUM",             int(p.get("MEDIUM",    0)))
    c4.metric("HIGH",               int(p.get("HIGH",      0)))
    c5.metric("CRITICAL",           int(p.get("CRITICAL",  0)))
    c6.metric("UNTRUSTED",          int(p.get("UNTRUSTED", 0)))

    # --- Row 2: Workflow status ---
    st.subheader("Workflow Status")
    w1, w2, w3 = st.columns(3)
    w1.metric("Offline Cases",           offline_count)
    w2.metric("Stored for Forward",      stored_count,
              help="Offline cases saved locally for later forwarding.")
    w3.metric("Queued (Over Capacity)",  queued_count,
              help="High-priority cases that exceed the immediate clinician limit.")

    st.divider()

    # --- Charts ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Priority Distribution")
        if "priority" in df.columns:
            priority_counts = df["priority"].value_counts().reindex(
                ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNTRUSTED"],
                fill_value=0,
            )
            st.bar_chart(priority_counts)

    with col_right:
        st.subheader("Escalation Pathway Distribution")
        if "escalation_path" in df.columns:
            path_counts = df["escalation_path"].value_counts()
            st.bar_chart(path_counts)


# ---------------------------------------------------------------------------
# PAGE 2: PATIENT ASSESSMENT
# ---------------------------------------------------------------------------

def show_patient_assessment():
    """
    Simple form for entering a simulated observation and running the complete
    Phase 3-7 workflow to produce an assessment result.
    """
    st.title("Patient Assessment")
    st.info(
        "Enter a simulated patient observation below. The system will apply "
        "the risk, conflict, and escalation rules from Phases 3-7.\n\n"
        "**All IDs are anonymous. No real patient data is entered or stored.**"
    )

    with st.form("assessment_form"):

        # Patient information
        col_id, col_week = st.columns(2)
        with col_id:
            patient_id = st.text_input("Patient ID (e.g. P101)", value="P101")
        with col_week:
            pregnancy_week = st.number_input(
                "Pregnancy Week", min_value=4, max_value=45, value=28
            )

        # Sensor readings
        st.subheader("Sensor Readings")
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            systolic   = st.number_input("Systolic BP (mmHg)",  50,  250, 120)
            heart_rate = st.number_input("Heart Rate (bpm)",     30,  200,  75)
        with sc2:
            diastolic  = st.number_input("Diastolic BP (mmHg)", 30,  160,  78)
            spo2       = st.number_input("SpO2 (%)",            50,  100,  98)
        with sc3:
            temperature = st.number_input(
                "Temperature (C)", 33.0, 43.0, 36.6, step=0.1
            )

        mark_incomplete = st.checkbox(
            "Simulate unavailable sensor data  "
            "(marks this record as Incomplete — triggers Safe Fallback)"
        )

        # Symptoms
        st.subheader("Patient-Reported Symptoms")
        sy1, sy2, sy3 = st.columns(3)
        with sy1:
            headache  = st.checkbox("Headache")
            bleeding  = st.checkbox("Bleeding")
        with sy2:
            blurred_vision = st.checkbox("Blurred Vision")
            abdominal_pain = st.checkbox("Abdominal Pain")
        with sy3:
            swelling = st.checkbox("Swelling")
            rfm      = st.checkbox("Reduced Fetal Movement")

        # Internet status
        internet_status = st.selectbox(
            "Internet Status",
            ["Online", "Offline"],
            help="Choose Offline to see store-and-forward behaviour.",
        )

        submitted = st.form_submit_button(
            "Analyze Case", use_container_width=True
        )

    if submitted:
        _run_assessment(
            patient_id,
            float(systolic),  float(diastolic), float(heart_rate),
            float(temperature), float(spo2),
            mark_incomplete,
            headache, blurred_vision, bleeding, abdominal_pain, swelling, rfm,
            internet_status,
        )


def _run_assessment(
    patient_id,
    systolic, diastolic, heart_rate, temperature, spo2,
    mark_incomplete,
    headache, blurred_vision, bleeding, abdominal_pain, swelling, rfm,
    internet_status,
):
    """
    Apply the complete workflow (Phases 4-7) to one observation row and
    display the results using Streamlit components.
    """
    st.divider()
    st.subheader(f"Assessment Results — {patient_id}")

    # Build an observation row dict for the workflow functions
    data_quality = "Incomplete" if mark_incomplete else "Good"
    row = {
        "data_quality":            data_quality,
        "systolic_bp":             np.nan if mark_incomplete else systolic,
        "diastolic_bp":            np.nan if mark_incomplete else diastolic,
        "heart_rate":              heart_rate,
        "temperature":             temperature,
        "spo2":                    spo2,
        "headache":                "Yes" if headache        else "No",
        "blurred_vision":          "Yes" if blurred_vision  else "No",
        "bleeding":                "Yes" if bleeding        else "No",
        "abdominal_pain":          "Yes" if abdominal_pain  else "No",
        "swelling":                "Yes" if swelling        else "No",
        "reduced_fetal_movement":  "Yes" if rfm             else "No",
        # No observation history available for a new form entry
        "trend_status":            "Stable",
        "internet_status":         internet_status,
        "communication_status":    "Not Required",
    }

    # --- Step 1: Risk detection (Phase 4 rules) ---
    risk_level, risk_reason, recommended_action = calculate_risk(row)
    row["risk_level"]         = risk_level
    row["recommended_action"] = recommended_action

    # --- Step 2: Conflict detection (Phase 6 rules) ---
    conflict_result  = detect_conflict(row)
    conflict_status  = conflict_result["conflict_status"]
    signal_agreement = conflict_result["signal_agreement"]
    conflict_reason  = conflict_result["conflict_reason"]
    row["conflict_status"]  = conflict_status
    row["signal_agreement"] = signal_agreement

    # --- Step 3: Escalation (Phase 7 rules) ---
    priority        = assign_priority(row)
    escalation_path = assign_escalation_path(priority)
    comm_attempt, comm_result = handle_communication(row, escalation_path)
    store_forward   = handle_store_forward(row, escalation_path)
    final_action    = create_final_action(priority, conflict_status)
    esc_reason      = create_escalation_reason(row, priority, conflict_status)

    # --- Metrics row ---
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk Level",      risk_level)
    m2.metric("Data Quality",    data_quality)
    m3.metric("Priority",        priority)
    m4.metric("Escalation Path", escalation_path)

    st.divider()

    # --- Risk / priority message ---
    if priority == "UNTRUSTED":
        st.warning(
            "**Safe Fallback Triggered**\n\n"
            "Recommendation cannot be trusted because important data is "
            "missing or invalid.\n\n"
            f"**Action:** {final_action}"
        )
    elif priority == "CRITICAL":
        st.error(
            f"**CRITICAL PRIORITY**\n\n"
            f"{risk_reason}\n\n"
            f"**Action:** {final_action}"
        )
    elif priority == "HIGH":
        st.error(
            f"**HIGH PRIORITY**\n\n"
            f"{risk_reason}\n\n"
            f"**Action:** {final_action}"
        )
    elif priority == "MEDIUM":
        st.warning(
            f"**MEDIUM PRIORITY**\n\n"
            f"{risk_reason}\n\n"
            f"**Action:** {final_action}"
        )
    else:
        st.success(
            f"**LOW PRIORITY**\n\n"
            f"{risk_reason}\n\n"
            f"**Action:** {final_action}"
        )

    # --- Sensor-symptom conflict display (the core project feature) ---
    st.subheader("Sensor-Symptom Analysis")
    if conflict_status == "SENSOR-SYMPTOM CONFLICT":
        st.error(
            "**Sensor-Symptom Conflict Detected**\n\n"
            "Patient-reported symptoms require clinician review even though "
            "the sensor risk appears normal.\n\n"
            f"{conflict_reason}"
        )
    elif conflict_status == "SENSOR-ONLY CONCERN":
        st.warning(
            "**Sensor-Only Concern**\n\n"
            "Sensor readings indicate concern, but no critical symptoms were "
            "reported. The sensor reading must not be ignored.\n\n"
            f"{conflict_reason}"
        )
    elif conflict_status == "INSUFFICIENT DATA":
        st.warning(
            f"**Insufficient Data**\n\n{conflict_reason}"
        )
    elif "both concerning" in signal_agreement:
        st.error(
            "**Sensor and symptoms both indicate concern.**\n\n"
            f"Signal agreement: {signal_agreement}\n\n"
            f"{conflict_reason}"
        )
    else:
        st.success(
            f"**{conflict_status}**\n\n"
            f"Signal agreement: {signal_agreement}"
        )

    # --- Offline store-and-forward message ---
    if store_forward == "STORED":
        st.info(
            "**Offline Mode — Store-and-Forward**\n\n"
            "Internet is not available. This case has been stored locally "
            "for forwarding when connectivity returns.\n\n"
            f"Store-and-Forward Status: **{store_forward}**\n\n"
            f"Communication: {comm_result}"
        )
    elif comm_attempt == "FIRST_ATTEMPT":
        st.info(
            f"Communication attempt: **{comm_attempt}**\n\n{comm_result}"
        )

    # --- Escalation reason ---
    st.subheader("Escalation Reason")
    st.write(esc_reason)


# ---------------------------------------------------------------------------
# PAGE 3: ESCALATION QUEUE
# ---------------------------------------------------------------------------

def show_escalation_queue():
    """
    Show all processed observations sorted by priority, with a capacity summary.
    """
    st.title("Escalation Queue")
    st.caption(
        "All processed observations sorted by priority (most urgent first). "
        "Only a limited number of high-priority cases can be reviewed immediately; "
        "additional cases are queued for the next available slot."
    )

    df = load_csv(ESCALATION_FILE)
    if df is None:
        return

    # Capacity summary
    within_cap = int((df["capacity_status"] == "WITHIN_CAPACITY").sum()) \
        if "capacity_status" in df.columns else 0
    queued     = int((df["capacity_status"] == "QUEUED").sum()) \
        if "capacity_status" in df.columns else 0

    st.subheader("Clinician Capacity Status")
    cap1, cap2, cap3 = st.columns(3)
    cap1.metric("Immediate Capacity Limit", 10)
    cap2.metric("Within Capacity",          within_cap)
    cap3.metric("Queued (Next Slot)",       queued)

    st.divider()

    # Priority filter
    st.subheader("Filter by Priority")
    selected_priorities = st.multiselect(
        "Show priorities:",
        options=["CRITICAL", "HIGH", "UNTRUSTED", "MEDIUM", "LOW"],
        default=["CRITICAL", "HIGH", "UNTRUSTED"],
    )

    # Select and sort columns
    display_cols = [
        "patient_id", "priority", "risk_level", "conflict_status",
        "escalation_path", "schedule_status",
        "internet_status", "store_forward_status",
        "final_action",
    ]
    display_cols = [c for c in display_cols if c in df.columns]

    sorted_df = df.copy()
    if "priority" in df.columns:
        sorted_df["_sort_key"] = sorted_df["priority"].map(
            lambda p: PRIORITY_ORDER.get(str(p), 99)
        )
        sorted_df = sorted_df.sort_values("_sort_key").drop(columns=["_sort_key"])

    # Apply filter
    if selected_priorities and "priority" in sorted_df.columns:
        filtered = sorted_df[sorted_df["priority"].isin(selected_priorities)]
    else:
        filtered = sorted_df

    st.write(f"Showing **{len(filtered)}** of **{len(df)}** records.")
    st.dataframe(filtered[display_cols], use_container_width=True)


# ---------------------------------------------------------------------------
# PAGE 4: CONFLICT DEMO
# ---------------------------------------------------------------------------

def show_conflict_demo():
    """
    Load the six hand-crafted demo cases, run conflict detection and escalation
    on each, and let the user browse them with a selectbox.
    """
    st.title("Conflict Detection Demo")
    st.info(
        "These six hand-crafted simulated cases demonstrate every conflict "
        "detection and escalation scenario.\n\n"
        "**These are NOT real patient records.** "
        "Anonymous IDs: DEMO001 to DEMO006."
    )

    demo_raw = load_csv(DEMO_FILE)
    if demo_raw is None:
        return

    # Run conflict detection on the demo rows
    conflict_cols = demo_raw.apply(detect_conflict, axis=1, result_type="expand")
    demo_df = pd.concat([demo_raw.reset_index(drop=True),
                         conflict_cols.reset_index(drop=True)], axis=1)

    # Run escalation logic
    demo_df = apply_escalation(demo_df)
    demo_df = handle_capacity(demo_df)

    # Select a demo case
    demo_ids = demo_df["patient_id"].tolist()
    selected_id = st.selectbox("Select a demo case to inspect:", demo_ids)

    row = demo_df[demo_df["patient_id"] == selected_id].iloc[0]

    st.divider()

    # Explanation
    explanation = DEMO_EXPLANATIONS.get(selected_id, "")
    st.info(explanation)

    # Key metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Risk Level",      str(row.get("risk_level",      "")))
    m2.metric("Conflict Status", str(row.get("conflict_status", "")))
    m3.metric("Priority",        str(row.get("priority",        "")))
    m4.metric("Escalation Path", str(row.get("escalation_path", "")))

    st.divider()

    # Detail columns
    d1, d2 = st.columns(2)

    with d1:
        st.markdown("**Sensor Readings**")
        st.write(f"Systolic BP  : {row.get('systolic_bp',  'N/A')}")
        st.write(f"Diastolic BP : {row.get('diastolic_bp', 'N/A')}")
        st.write(f"Heart Rate   : {row.get('heart_rate',   'N/A')}")
        st.write(f"Temperature  : {row.get('temperature',  'N/A')}")
        st.write(f"SpO2         : {row.get('spo2',         'N/A')}")
        st.write(f"Data Quality : {row.get('data_quality', 'N/A')}")
        st.write(f"Internet     : {row.get('internet_status', 'N/A')}")

    with d2:
        st.markdown("**Patient-Reported Symptoms**")
        for col in ["headache", "blurred_vision", "bleeding",
                    "abdominal_pain", "swelling", "reduced_fetal_movement"]:
            val   = row.get(col, "No")
            label = col.replace("_", " ").title()
            if val == "Yes":
                st.write(f":red_circle: {label}: **Yes**")
            else:
                st.write(f":green_circle: {label}: No")

    # Conflict analysis
    st.subheader("Conflict Analysis")
    conflict_status  = str(row.get("conflict_status",  ""))
    signal_agreement = str(row.get("signal_agreement", ""))
    conflict_reason  = str(row.get("conflict_reason",  ""))
    final_action     = str(row.get("final_action",     ""))

    if conflict_status == "SENSOR-SYMPTOM CONFLICT":
        st.error(
            f"**Sensor-Symptom Conflict Detected**\n\n"
            f"Signal agreement: {signal_agreement}\n\n"
            f"{conflict_reason}"
        )
    elif conflict_status == "SENSOR-ONLY CONCERN":
        st.warning(
            f"**Sensor-Only Concern**\n\n{conflict_reason}"
        )
    elif conflict_status == "INSUFFICIENT DATA":
        st.warning(
            f"**Insufficient Data**\n\n{conflict_reason}"
        )
    elif "both concerning" in signal_agreement:
        st.error(
            f"**Both sensor and symptoms are concerning.**\n\n"
            f"Signal agreement: {signal_agreement}\n\n"
            f"{conflict_reason}"
        )
    else:
        st.success(
            f"**{conflict_status}**\n\n"
            f"Signal agreement: {signal_agreement}"
        )

    # Offline / store-and-forward
    if str(row.get("store_forward_status", "")) == "STORED":
        st.info(
            "**Offline Mode — Store-and-Forward**\n\n"
            f"Internet Status: **{row.get('internet_status', 'Offline')}**\n\n"
            "This case has been stored locally for forwarding when connectivity "
            "returns. It has NOT been discarded.\n\n"
            f"Store-and-Forward Status: **{row.get('store_forward_status', '')}**\n\n"
            f"Communication: {row.get('communication_result', '')}"
        )

    # Final action
    st.subheader("Final Recommended Action")
    priority = str(row.get("priority", ""))
    if priority in ("CRITICAL", "HIGH"):
        st.error(f"**{final_action}**")
    elif priority == "UNTRUSTED":
        st.warning(f"**{final_action}**")
    elif priority == "MEDIUM":
        st.warning(f"**{final_action}**")
    else:
        st.success(f"**{final_action}**")


# ---------------------------------------------------------------------------
# PAGE 5: DATA QUALITY
# ---------------------------------------------------------------------------

def show_data_quality():
    """
    Show a data quality summary from the cleaned simulated dataset.
    """
    st.title("Data Quality Report")
    st.caption(
        "Summary of record quality in the cleaned simulated dataset "
        "(data/cleaned_maternal_data.csv)."
    )

    df = load_csv(CLEANED_FILE)
    if df is None:
        return

    total = len(df)

    # Quality distribution
    if "data_quality" in df.columns:
        q          = df["data_quality"].value_counts()
        good       = int(q.get("Good",       0))
        incomplete = int(q.get("Incomplete", 0))
        invalid    = int(q.get("Invalid",    0))
    else:
        good = incomplete = invalid = 0
        st.warning(
            "Column 'data_quality' not found. Please re-run clean_data.py."
        )

    st.subheader("Record Quality Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Records", total)
    c2.metric("Good",          good)
    c3.metric("Incomplete",    incomplete)
    c4.metric("Invalid",       invalid)

    if "data_quality" in df.columns:
        st.bar_chart(df["data_quality"].value_counts())

    st.divider()

    # Missing sensor value counts
    st.subheader("Missing Sensor Readings")
    sensor_cols = ["systolic_bp", "diastolic_bp", "heart_rate", "temperature", "spo2"]
    existing    = [c for c in sensor_cols if c in df.columns]

    if existing:
        missing_counts = {col: int(df[col].isna().sum()) for col in existing}
        missing_df = pd.DataFrame.from_dict(
            missing_counts, orient="index", columns=["Missing Values"]
        )
        missing_df.index.name = "Sensor Column"

        mc_left, mc_right = st.columns(2)
        with mc_left:
            st.dataframe(missing_df, use_container_width=True)
        with mc_right:
            st.bar_chart(missing_df)

    st.divider()

    # Sample of the cleaned data
    st.subheader("Sample Records (First 10 Rows)")
    sample_cols = [
        "patient_id", "observation_day", "pregnancy_week",
        "systolic_bp", "diastolic_bp", "heart_rate", "data_quality",
    ]
    sample_cols = [c for c in sample_cols if c in df.columns]
    st.dataframe(df[sample_cols].head(10), use_container_width=True)


# ---------------------------------------------------------------------------
# SIDEBAR AND NAVIGATION
# ---------------------------------------------------------------------------

def main():
    """
    Build the sidebar and route to the correct page.
    """
    # Sidebar
    st.sidebar.title("Maternal Health Monitor")
    st.sidebar.caption("Phase 8 — Streamlit Prototype")

    page = st.sidebar.radio(
        "Navigate to:",
        options=[
            "Dashboard",
            "Patient Assessment",
            "Escalation Queue",
            "Conflict Demo",
            "Data Quality",
        ],
    )

    st.sidebar.divider()

    # Privacy notice (always visible)
    st.sidebar.info(
        "**Privacy by Design**\n\n"
        "This prototype uses simulated records and anonymous patient IDs only. "
        "No names, phone numbers, addresses or real patient records are stored."
    )
    st.sidebar.caption(
        "Educational prototype only — not for real clinical decisions."
    )

    # Route to the selected page
    if page == "Dashboard":
        show_dashboard()
    elif page == "Patient Assessment":
        show_patient_assessment()
    elif page == "Escalation Queue":
        show_escalation_queue()
    elif page == "Conflict Demo":
        show_conflict_demo()
    elif page == "Data Quality":
        show_data_quality()


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    main()
