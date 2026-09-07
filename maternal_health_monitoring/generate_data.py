# generate_data.py
# Phase 2 - Simulated Dataset Generation
# Remote Maternal Health Monitoring and Escalation System
#
# This dataset contains simulated data only and must not be used for real clinical decisions.
#
# Purpose:
#   Generate a realistic-looking but completely fake dataset of maternal health observations.
#   No real patient data is used. All patient IDs are anonymous (P001, P002, ..., P100).

import os
import random
import numpy as np
import pandas as pd

# Fix the random seed so the same dataset is produced each time we run this script.
random.seed(42)
np.random.seed(42)

# ---------------------------------------------------------------------------
# SECTION 1: CONFIGURATION
# ---------------------------------------------------------------------------

# Total number of patient IDs to simulate
NUM_PATIENTS = 100

# Total number of observation records to generate (approximately 1000)
TARGET_TOTAL_RECORDS = 1000

# Folder and filename where the CSV will be saved
OUTPUT_FOLDER = "data"
OUTPUT_FILE = "simulated_maternal_data.csv"


# ---------------------------------------------------------------------------
# SECTION 2: HELPER FUNCTIONS FOR GENERATING INDIVIDUAL COLUMNS
# ---------------------------------------------------------------------------

def generate_patient_ids(num_patients):
    """Return a list of anonymous patient IDs like P001, P002, ..., P100."""
    return [f"P{str(i).zfill(3)}" for i in range(1, num_patients + 1)]


def assign_observation_days(patient_ids, target_total):
    """
    Assign multiple observation days to patients so some have many visits
    and others have fewer. This lets later phases demonstrate trends.
    Returns a flat list of (patient_id, observation_day) pairs.
    """
    pairs = []

    for pid in patient_ids:
        # Each patient gets between 5 and 15 observation days
        num_days = random.randint(5, 15)
        # Space observations roughly 3-5 days apart
        day = 1
        for _ in range(num_days):
            pairs.append((pid, day))
            day += random.randint(3, 5)

    # If we generated more than needed, trim; if fewer, we accept it.
    # Shuffle so patients are not all grouped together.
    random.shuffle(pairs)

    # Trim to target if over
    if len(pairs) > target_total:
        pairs = pairs[:target_total]

    return pairs


def generate_pregnancy_week(patient_id):
    """
    Simulate a realistic gestational age in weeks (12 to 40 weeks).
    Each patient has a fixed starting pregnancy week so it is consistent
    across their observation days.
    """
    # Use patient number to produce a consistent starting week
    patient_num = int(patient_id[1:])
    return 12 + (patient_num % 28)


def generate_bp(base_systolic, base_diastolic, add_noise=False, make_high=False):
    """
    Generate a blood pressure reading.
    - base values represent the patient's typical BP
    - add_noise: add a large random error to simulate a bad sensor reading
    - make_high: shift values up to simulate a dangerous reading
    Returns (systolic, diastolic) as integers.
    """
    systolic = base_systolic + random.randint(-5, 5)
    diastolic = base_diastolic + random.randint(-3, 3)

    if make_high:
        systolic += random.randint(30, 60)
        diastolic += random.randint(15, 30)

    if add_noise:
        # Simulate an impossible or very noisy sensor reading
        systolic = random.choice([999, 0, -10, 300])
        diastolic = random.choice([999, 0, -5, 200])

    return systolic, diastolic


def generate_heart_rate(add_noise=False):
    """
    Simulate a heart rate in beats per minute.
    Normal range: 60-100.
    add_noise: return an impossible value.
    """
    if add_noise:
        return random.choice([0, 300, -5, 999])
    return random.randint(60, 100)


def generate_temperature(add_noise=False):
    """
    Simulate a body temperature in degrees Celsius.
    Normal range: 36.1 to 37.5.
    add_noise: return an impossible value.
    """
    if add_noise:
        return random.choice([0.0, 55.0, -1.0, 100.0])
    return round(random.uniform(36.1, 37.5), 1)


def generate_spo2(add_noise=False):
    """
    Simulate blood oxygen saturation (SpO2) as a percentage.
    Normal range: 95 to 100.
    add_noise: return an impossible value.
    """
    if add_noise:
        return random.choice([0, 200, -5, 999])
    return random.randint(95, 100)


def generate_symptom(probability_yes=0.10):
    """
    Return 'Yes' or 'No' for a symptom.
    probability_yes: how likely this symptom is to appear.
    """
    return "Yes" if random.random() < probability_yes else "No"


def generate_internet_status():
    """Return 'Online' or 'Offline'. Mostly online, some offline."""
    return "Offline" if random.random() < 0.15 else "Online"


def generate_communication_status():
    """
    Return a simulated communication status.
    Most records do not require communication.
    """
    return random.choice(["Not Required", "Not Required", "Not Required",
                          "Pending", "Completed", "Failed"])


def generate_clinician_decision(systolic, diastolic, symptoms):
    """
    Assign a simulated clinician decision based on rough thresholds.
    These are NOT real clinical guidelines — they are for prototype testing only.
    """
    # Count how many concerning symptoms the patient reported
    concerning = sum(1 for s in symptoms if s == "Yes")

    if systolic >= 160 or diastolic >= 110 or concerning >= 3:
        return "Immediate Referral"
    elif systolic >= 140 or diastolic >= 90 or concerning == 2:
        return "Clinician Review"
    elif systolic >= 130 or diastolic >= 85 or concerning == 1:
        return "Schedule Follow-up"
    else:
        return "Continue Monitoring"


# ---------------------------------------------------------------------------
# SECTION 3: PATIENT PROFILE ASSIGNMENT
# ---------------------------------------------------------------------------

def assign_patient_profile(patient_id):
    """
    Give each patient a profile that determines their base health readings
    and whether their readings trend upward, downward, or stay stable.

    Profiles:
    - 'normal'   : healthy-looking patient
    - 'rising_bp': BP increases over observations (for trend demo)
    - 'high_bp'  : already-elevated BP throughout
    - 'mixed'    : some abnormal readings mixed in

    Returns a dictionary with profile details.
    """
    patient_num = int(patient_id[1:])

    # Assign profile based on patient number for reproducibility
    if patient_num % 5 == 0:
        # 20% of patients: rising BP trend
        return {
            "profile": "rising_bp",
            "base_systolic": 115,
            "base_diastolic": 75,
            "systolic_increase_per_day": 0.8,  # BP rises over time
        }
    elif patient_num % 7 == 0:
        # ~14% of patients: already high BP
        return {
            "profile": "high_bp",
            "base_systolic": 145,
            "base_diastolic": 95,
            "systolic_increase_per_day": 0.1,
        }
    elif patient_num % 3 == 0:
        # ~33% of patients: mixed readings
        return {
            "profile": "mixed",
            "base_systolic": 125,
            "base_diastolic": 80,
            "systolic_increase_per_day": 0.0,
        }
    else:
        # remaining patients: normal
        return {
            "profile": "normal",
            "base_systolic": 115,
            "base_diastolic": 75,
            "systolic_increase_per_day": 0.0,
        }


# ---------------------------------------------------------------------------
# SECTION 4: CONFLICT CASE GENERATION
# ---------------------------------------------------------------------------

def should_be_conflict_case(patient_id, obs_index):
    """
    Decide if this observation should be a deliberate conflict case.
    A conflict means sensor readings and symptoms disagree intentionally.
    Returns: 'normal_bp_bad_symptoms', 'high_bp_no_symptoms', or None.
    """
    patient_num = int(patient_id[1:])

    # About 5% of records: normal BP but bad symptoms
    if (patient_num + obs_index) % 20 == 0:
        return "normal_bp_bad_symptoms"

    # About 5% of records: high BP but no symptoms reported
    if (patient_num + obs_index) % 19 == 0:
        return "high_bp_no_symptoms"

    return None


# ---------------------------------------------------------------------------
# SECTION 5: MISSING AND NOISY DATA
# ---------------------------------------------------------------------------

def maybe_make_missing(value, probability=0.04):
    """
    Replace a value with NaN with the given probability.
    This simulates sensor drop-outs or missing readings.
    """
    if random.random() < probability:
        return np.nan
    return value


def should_be_noisy(patient_id, obs_index, probability=0.02):
    """Return True if this observation should have a noisy/invalid sensor reading."""
    return random.random() < probability


# ---------------------------------------------------------------------------
# SECTION 6: MAIN DATA GENERATION FUNCTION
# ---------------------------------------------------------------------------

def generate_dataset():
    """
    Build the full simulated dataset and return it as a Pandas DataFrame.
    This is the main function that puts all parts together.
    """

    patient_ids = generate_patient_ids(NUM_PATIENTS)
    observation_pairs = assign_observation_days(patient_ids, TARGET_TOTAL_RECORDS)

    # Store all rows here
    rows = []

    # Keep track of how many observations each patient has had
    obs_count_per_patient = {}

    for patient_id, observation_day in observation_pairs:

        # Track observation index for this patient
        if patient_id not in obs_count_per_patient:
            obs_count_per_patient[patient_id] = 0
        obs_index = obs_count_per_patient[patient_id]
        obs_count_per_patient[patient_id] += 1

        # --- Patient profile ---
        profile = assign_patient_profile(patient_id)

        # Calculate BP for this observation day (may increase if rising_bp profile)
        systolic_offset = int(profile["systolic_increase_per_day"] * observation_day)
        base_sys = profile["base_systolic"] + systolic_offset
        base_dia = profile["base_diastolic"]

        # Pregnancy week
        preg_week = generate_pregnancy_week(patient_id)

        # --- Decide observation type ---
        conflict_type = should_be_conflict_case(patient_id, obs_index)
        noisy = should_be_noisy(patient_id, obs_index)

        # --- Generate vital signs ---
        if conflict_type == "high_bp_no_symptoms":
            # CASE B: High BP but no symptoms reported
            systolic, diastolic = generate_bp(base_sys, base_dia, make_high=True)
        elif noisy:
            # Noisy/invalid sensor reading
            systolic, diastolic = generate_bp(base_sys, base_dia, add_noise=True)
        else:
            systolic, diastolic = generate_bp(base_sys, base_dia)

        heart_rate = generate_heart_rate(add_noise=noisy)
        temperature = generate_temperature(add_noise=noisy)
        spo2 = generate_spo2(add_noise=noisy)

        # --- Generate symptoms ---
        if conflict_type == "normal_bp_bad_symptoms":
            # CASE A: Normal-looking BP but concerning symptoms
            # Use normal BP values regardless of profile
            systolic = base_sys + random.randint(-5, 5)
            diastolic = base_dia + random.randint(-3, 3)
            headache = "Yes"
            blurred_vision = "Yes"
            bleeding = generate_symptom(0.10)
            abdominal_pain = generate_symptom(0.20)
            swelling = "Yes"
            reduced_fetal_movement = generate_symptom(0.20)

        elif conflict_type == "high_bp_no_symptoms":
            # CASE B: High BP but all major symptoms are No
            headache = "No"
            blurred_vision = "No"
            bleeding = generate_symptom(0.05)  # CASE C can overlap: some bleeding
            abdominal_pain = "No"
            swelling = "No"
            reduced_fetal_movement = "No"

        elif profile["profile"] == "high_bp":
            # High BP patients: more likely to have symptoms
            headache = generate_symptom(0.50)
            blurred_vision = generate_symptom(0.40)
            bleeding = generate_symptom(0.10)
            abdominal_pain = generate_symptom(0.30)
            swelling = generate_symptom(0.40)
            reduced_fetal_movement = generate_symptom(0.20)

        else:
            # Normal / mixed: low symptom probability
            headache = generate_symptom(0.08)
            blurred_vision = generate_symptom(0.05)
            bleeding = generate_symptom(0.03)
            abdominal_pain = generate_symptom(0.07)
            swelling = generate_symptom(0.10)
            reduced_fetal_movement = generate_symptom(0.04)

        # CASE C: Normal-looking sensors but bleeding=Yes (can happen in any case)
        # Already handled above by keeping bleeding independent with low probability

        # --- Previous systolic BP (for trend comparison in Phase 5) ---
        # Simulate what the BP was roughly 3-5 days before this reading
        if obs_index == 0:
            previous_systolic_bp = np.nan  # No previous reading on first visit
        else:
            previous_systolic_bp = systolic - random.randint(-8, 8)

        # --- Internet and communication status ---
        internet_status = generate_internet_status()
        communication_status = generate_communication_status()

        # --- Clinician decision ---
        symptoms = [headache, blurred_vision, bleeding, abdominal_pain,
                    swelling, reduced_fetal_movement]
        clinician_decision = generate_clinician_decision(systolic, diastolic, symptoms)

        # --- Apply missing values to selected vital fields ---
        systolic = maybe_make_missing(systolic, probability=0.04)
        diastolic = maybe_make_missing(diastolic, probability=0.04)
        heart_rate = maybe_make_missing(heart_rate, probability=0.03)
        temperature = maybe_make_missing(temperature, probability=0.03)
        spo2 = maybe_make_missing(spo2, probability=0.03)

        # --- Build the row dictionary ---
        row = {
            "patient_id": patient_id,
            "observation_day": observation_day,
            "pregnancy_week": preg_week,
            "systolic_bp": systolic,
            "diastolic_bp": diastolic,
            "heart_rate": heart_rate,
            "temperature": temperature,
            "spo2": spo2,
            "headache": headache,
            "blurred_vision": blurred_vision,
            "bleeding": bleeding,
            "abdominal_pain": abdominal_pain,
            "swelling": swelling,
            "reduced_fetal_movement": reduced_fetal_movement,
            "previous_systolic_bp": previous_systolic_bp,
            "internet_status": internet_status,
            "communication_status": communication_status,
            "clinician_decision": clinician_decision,
        }

        rows.append(row)

    # Build the DataFrame from all rows
    df = pd.DataFrame(rows)

    return df


# ---------------------------------------------------------------------------
# SECTION 7: SAVE THE DATASET
# ---------------------------------------------------------------------------

def save_dataset(df):
    """Save the DataFrame to a CSV file inside the data/ folder."""

    # Create the output folder if it does not already exist
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    output_path = os.path.join(OUTPUT_FOLDER, OUTPUT_FILE)
    df.to_csv(output_path, index=False)

    print(f"\n[OK] Dataset saved to: {output_path}")
    return output_path


# ---------------------------------------------------------------------------
# SECTION 8: DATA QUALITY SUMMARY
# ---------------------------------------------------------------------------

def print_data_summary(df):
    """Print a simple summary of the generated dataset for quick inspection."""

    print("\n" + "=" * 55)
    print("  DATA QUALITY SUMMARY")
    print("=" * 55)

    print(f"\nTotal rows (records)   : {len(df)}")
    print(f"Total columns          : {len(df.columns)}")

    print("\nColumn names:")
    for col in df.columns:
        print(f"  - {col}")

    print("\nMissing values per column:")
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            print(f"  {col}: {count} missing")

    print(f"\nTotal missing values   : {df.isnull().sum().sum()}")
    print(f"Number of patients     : {df['patient_id'].nunique()}")

    online_count = (df["internet_status"] == "Online").sum()
    offline_count = (df["internet_status"] == "Offline").sum()
    print(f"Online observations    : {online_count}")
    print(f"Offline observations   : {offline_count}")

    print(f"\nClinician decision distribution:")
    for decision, count in df["clinician_decision"].value_counts().items():
        print(f"  {decision}: {count}")

    print("\nFirst 5 rows:")
    print(df.head(5).to_string())

    print("\n" + "=" * 55)


# ---------------------------------------------------------------------------
# SECTION 9: RUN THE GENERATOR
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    print("=" * 55)
    print("  Phase 2 - Simulated Dataset Generation")
    print("  Remote Maternal Health Monitoring System")
    print("=" * 55)
    print("\nGenerating simulated dataset ...")

    # Step 1: Generate the dataset
    df = generate_dataset()

    # Step 2: Save it to CSV
    save_dataset(df)

    # Step 3: Print a simple summary
    print_data_summary(df)

    print("\n[DONE] Phase 2 complete. Do NOT start Phase 3 yet.")
    print("   Next: Run generate_data.py and inspect the CSV before proceeding.\n")
