# validation/run_validation.py
# Phase 11 – User / Stakeholder Validation
# Remote Maternal Health Monitoring and Escalation System
#
# PURPOSE:
#   Load the simulated stakeholder feedback CSV, calculate average scores,
#   identify strongest and weakest areas, and print a clear validation summary.
#
# HOW TO RUN:
#   python validation/run_validation.py
#   (Run from the maternal_health_monitoring/ project folder)
#
# IMPORTANT DISCLAIMER:
#   This validation uses simulated prototype stakeholder-style feedback
#   created for academic evaluation purposes only.
#   It is NOT clinical validation and does NOT represent feedback from
#   real patients or healthcare professionals.
#
# USES: pandas and simple Python only. No machine learning.

import os
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# PATH SETUP
# ---------------------------------------------------------------------------

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALIDATION_DIR = os.path.dirname(os.path.abspath(__file__))
FEEDBACK_CSV   = os.path.join(VALIDATION_DIR, "user_feedback.csv")
OUTPUT_CSV     = os.path.join(VALIDATION_DIR, "validation_results.csv")

# ---------------------------------------------------------------------------
# SCORE COLUMNS AND THEIR DISPLAY NAMES
# ---------------------------------------------------------------------------

SCORE_COLUMNS = {
    "workflow_clarity_score":   "Workflow Clarity",
    "escalation_clarity_score": "Escalation Clarity",
    "usability_score":          "Usability",
    "safety_fallback_score":    "Safety Fallback",
    "overall_score":            "Overall Score",
}

# ---------------------------------------------------------------------------
# HELPER: DIVIDER AND ROW PRINT
# ---------------------------------------------------------------------------

def divider(char="=", width=52):
    print(char * width)


def section(title):
    print()
    divider()
    print(f"  {title}")
    divider()


def row_print(label, value, indent=4):
    spaces = " " * indent
    print(f"{spaces}{label:<36} {value}")


# ---------------------------------------------------------------------------
# LOAD FEEDBACK DATA
# ---------------------------------------------------------------------------

print()
print("Loading feedback data...")

if not os.path.exists(FEEDBACK_CSV):
    print(f"\n[ERROR] Feedback file not found: {FEEDBACK_CSV}")
    print("        Please make sure validation/user_feedback.csv exists.")
    sys.exit(1)

try:
    df = pd.read_csv(FEEDBACK_CSV)
except Exception as e:
    print(f"\n[ERROR] Could not read feedback CSV: {e}")
    sys.exit(1)

print(f"  Loaded {len(df)} feedback responses from {FEEDBACK_CSV}")

# Validate expected columns
required_cols = list(SCORE_COLUMNS.keys()) + [
    "feedback_id", "stakeholder_role",
    "positive_feedback", "improvement_suggestion",
]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    print(f"\n[ERROR] Missing columns in feedback CSV: {missing_cols}")
    sys.exit(1)


# ---------------------------------------------------------------------------
# CALCULATE AVERAGE SCORES
# ---------------------------------------------------------------------------

averages = {}
for col, label in SCORE_COLUMNS.items():
    avg = round(float(df[col].mean()), 2)
    averages[col] = {"label": label, "average": avg}

# Identify strongest and weakest area (excluding overall_score)
area_scores = {
    col: data["average"]
    for col, data in averages.items()
    if col != "overall_score"
}

strongest_col  = max(area_scores, key=area_scores.get)
weakest_col    = min(area_scores, key=area_scores.get)
strongest_name = averages[strongest_col]["label"]
weakest_name   = averages[weakest_col]["label"]
strongest_val  = averages[strongest_col]["average"]
weakest_val    = averages[weakest_col]["average"]


# ---------------------------------------------------------------------------
# ROLE BREAKDOWN
# ---------------------------------------------------------------------------

role_counts = df["stakeholder_role"].value_counts().to_dict()

role_avg = df.groupby("stakeholder_role")["overall_score"].mean().round(2).to_dict()


# ---------------------------------------------------------------------------
# SCORE BAND COUNTS
# ---------------------------------------------------------------------------
# Count how many responses scored <= 3 vs >= 4 per column

def score_band(series):
    """Return count of scores 4-5 (positive) and 1-3 (needs improvement)."""
    positive   = int((series >= 4).sum())
    needs_work = int((series <= 3).sum())
    return positive, needs_work

band_results = {}
for col, label in SCORE_COLUMNS.items():
    pos, neg = score_band(df[col])
    band_results[col] = {
        "label":       label,
        "positive":    pos,
        "needs_work":  neg,
    }


# ---------------------------------------------------------------------------
# KEY FEEDBACK QUOTES (top 3 positive, top 3 improvement)
# ---------------------------------------------------------------------------

positive_quotes = df["positive_feedback"].dropna().tolist()
improvement_quotes = df["improvement_suggestion"].dropna().tolist()


# ---------------------------------------------------------------------------
# PRINT TERMINAL REPORT
# ---------------------------------------------------------------------------

section("PHASE 11 - USER / STAKEHOLDER VALIDATION")

print()
print("  DISCLAIMER:")
print("  This validation uses simulated prototype stakeholder-style")
print("  feedback created for academic evaluation purposes only.")
print("  It is NOT clinical validation and does NOT represent")
print("  feedback from real patients or healthcare professionals.")

print()
divider("-", 52)
print(f"  Total feedback responses: {len(df)}")
divider("-", 52)

# -- Average scores --
print()
print("  Average Scores (scale 1-5):")
print()
for col, data in averages.items():
    bar_filled = int(round(data["average"]))
    bar = "*" * bar_filled + "." * (5 - bar_filled)
    row_print(
        data["label"] + ":",
        f"{data['average']:.2f} / 5.00  [{bar}]"
    )

# -- Strongest / weakest --
print()
divider("-", 52)
row_print("Strongest Area:",         f"{strongest_name}  ({strongest_val:.2f}/5.00)")
row_print("Area for Improvement:",   f"{weakest_name}  ({weakest_val:.2f}/5.00)")
divider("-", 52)

# -- Role breakdown --
print()
print("  Responses by Stakeholder Role:")
print()
for role, count in role_counts.items():
    avg_overall = role_avg.get(role, 0)
    row_print(role + ":", f"{count} response(s)  |  Avg overall: {avg_overall:.2f}")

# -- Score band summary --
print()
print("  Score Distribution (scores 4-5 = Positive, 1-3 = Needs Work):")
print()
for col, data in band_results.items():
    if col == "overall_score":
        continue
    row_print(
        data["label"] + ":",
        f"Positive={data['positive']}  Needs Work={data['needs_work']}"
    )

# -- Key positive feedback --
print()
print("  Key Positive Feedback:")
print()
for i, quote in enumerate(positive_quotes[:3], start=1):
    # Wrap at ~60 chars for readability
    words   = quote.split()
    lines   = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > 60:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    print(f"    {i}. {lines[0]}")
    for line in lines[1:]:
        print(f"       {line}")
    print()

# -- Key improvement suggestions --
print()
print("  Key Improvement Suggestions:")
print()
for i, quote in enumerate(improvement_quotes[:3], start=1):
    words   = quote.split()
    lines   = []
    current = ""
    for word in words:
        if len(current) + len(word) + 1 > 60:
            lines.append(current)
            current = word
        else:
            current = (current + " " + word).strip()
    if current:
        lines.append(current)
    print(f"    {i}. {lines[0]}")
    for line in lines[1:]:
        print(f"       {line}")
    print()

divider()


# ---------------------------------------------------------------------------
# SAVE VALIDATION RESULTS TO CSV
# ---------------------------------------------------------------------------

results_records = []
for col, data in averages.items():
    band = band_results.get(col, {})
    results_records.append({
        "metric":          col,
        "display_name":    data["label"],
        "average_score":   data["average"],
        "positive_count":  band.get("positive",   "N/A"),
        "needs_work_count":band.get("needs_work",  "N/A"),
        "is_strongest":    (col == strongest_col),
        "is_weakest":      (col == weakest_col and col != "overall_score"),
    })

results_df = pd.DataFrame(results_records)
results_df.to_csv(OUTPUT_CSV, index=False)
print()
print(f"  Validation results saved to: {OUTPUT_CSV}")

# Also save the raw feedback with computed average per row
df["row_average"] = df[list(SCORE_COLUMNS.keys())].mean(axis=1).round(2)
detailed_csv = os.path.join(VALIDATION_DIR, "validation_detailed.csv")
df.to_csv(detailed_csv, index=False)
print(f"  Detailed feedback saved to:  {detailed_csv}")


# ---------------------------------------------------------------------------
# FINAL SUMMARY
# ---------------------------------------------------------------------------

print()
divider()
print("  PHASE 11 COMPLETE")
divider()
print(f"  Total responses      : {len(df)}")
print(f"  Overall average      : {averages['overall_score']['average']:.2f} / 5.00")
print(f"  Strongest area       : {strongest_name}")
print(f"  Area for improvement : {weakest_name}")
print()
print("  Script completed successfully.")
print()
print("  DISCLAIMER: Simulated prototype stakeholder feedback")
print("  for academic evaluation only. Not clinical validation.")
print()
