# LAB_prompt_design.py
# Design Effective Prompts for Multi-Agent Systems
# SYSEN 5381 Lab - Multi-Agent Orchestration

# Workflow: Earthquake Risk Triage & Emergency Response Advisory
#
#   [USGS API] --> raw DataFrame of recent earthquakes
#         |
#   [Agent 1: Data Analyst]      --> clean markdown table (magnitude, place, time, depth_km)
#         |
#   [Agent 2: Risk Assessor]     --> risk-classified table (HIGH / MODERATE / LOW)
#         |
#   [Agent 3: Emergency Advisor] --> numbered emergency response checklist

# 0. SETUP ###################################

from functions import agent_run, df_as_text
import os
import sys
import requests
import pandas as pd
from datetime import datetime, timedelta

# Set working directory so relative imports work
os.chdir(os.path.dirname(os.path.abspath(__file__)))

MODEL = "smollm2:1.7b"   # Iteration 2: upgraded from 135m — better instruction following

# 1. FETCH RAW DATA (function, not an agent) ###################################

def get_earthquakes(min_magnitude=5.0, days_back=7):
    """
    Fetch recent earthquake events from the USGS Earthquake Hazards API.

    Parameters
    ----------
    min_magnitude : float
        Minimum magnitude to include (default: 5.0)
    days_back : int
        How many days back to query (default: 7)

    Returns
    -------
    pandas.DataFrame
        Columns: magnitude, place, time, depth_km
    """
    end   = datetime.utcnow()
    start = end - timedelta(days=days_back)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format":       "geojson",
        "starttime":    start.strftime("%Y-%m-%d"),
        "endtime":      end.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "orderby":      "magnitude",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    features = response.json().get("features", [])

    rows = []
    for f in features:
        props  = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None, None])
        rows.append({
            "magnitude": props.get("mag"),
            "place":     props.get("place"),
            "time":      datetime.utcfromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                         if props.get("time") else None,
            "depth_km":  coords[2],
        })

    return pd.DataFrame(rows)

print("Fetching USGS earthquake data (mag >= 5.0, last 7 days)...\n")
data = get_earthquakes(min_magnitude=5.0, days_back=7)

if data.empty:
    print("No earthquake data returned from USGS API. Exiting.")
    sys.exit(1)

# Pre-slim to top 15 strongest events to keep context manageable for small models
slim = data.head(15).reset_index(drop=True)
raw_text = df_as_text(slim)
print(f"Fetched {len(data)} earthquakes. Passing top {len(slim)} to Agent 1.\n")

# 2. AGENT 1 — DATA ANALYST ###################################
# Role:   Receive raw USGS earthquake table; return a clean formatted markdown table.
# Input:  raw_text  (markdown table from USGS API)
# Output: analysis  (clean markdown table, 4 columns, sorted by magnitude descending)
#
# Prompt design choice:
#   - Specify exact output columns so Agent 2 can parse reliably.
#   - Cap at 15 rows to keep context manageable for small models.
#   - "Return ONLY" imperative opener — more effective than persona framing.
#   - "copy values exactly" prevents hallucination of magnitude or place values.

# Iteration 2: lead with "Return ONLY" rather than persona statement.
# Iteration 3: added "copy values exactly" — model was hallucinating place names.
role1 = (
    "Return ONLY a markdown table. Do not write any other text before or after the table. "
    "The table must have exactly four columns: magnitude | place | time | depth_km. "
    "Copy every value exactly as it appears in the user's table — do not change, infer, or omit any values. "
    "Include every row from the user's table. Sort rows by magnitude descending."
)

print("Running Agent 1 (Data Analyst)...")
analysis = agent_run(role=role1, task=raw_text, model=MODEL, output="text")

print("\n--- Agent 1 Output (Cleaned Earthquake Table) ---")
print(analysis)

# 3. AGENT 2 — RISK ASSESSOR ###################################
# Role:   Receive Agent 1's table; classify each earthquake by risk level.
# Input:  analysis  (output from Agent 1)
# Output: risk_table  (markdown table with added risk_level column)
#
# Prompt design choice:
#   - Explicit magnitude thresholds so classification is deterministic:
#       HIGH      = magnitude >= 6.5
#       MODERATE  = magnitude 5.0 – 6.4
#       LOW       = magnitude < 5.0
#   - Example rows anchor exact format for each class.
#   - "include ALL rows" prevents the model from silently dropping entries.

# Iteration 2: moved classification rules into a clear block with magnitude ranges.
# Iteration 3: added three example rows so each class is unambiguously demonstrated.
role2 = (
    "Return ONLY a markdown table. Do not write any other text before or after the table. "
    "The table must have exactly five columns: magnitude | place | time | depth_km | risk_level. "
    "Copy magnitude, place, time, and depth_km exactly from the user's table. "
    "Include ALL rows — do not drop any. "
    "Assign risk_level using ONLY these rules:\n"
    "  - HIGH     : magnitude >= 6.5\n"
    "  - MODERATE : magnitude >= 5.0 and < 6.5\n"
    "  - LOW      : magnitude < 5.0\n"
    "Example rows:\n"
    "  | 7.1 | 150 km NE of Tokyo, Japan | 2026-03-20 14:22 | 35.0 | HIGH |\n"
    "  | 5.8 | 80 km SW of Lima, Peru | 2026-03-19 09:10 | 12.0 | MODERATE |\n"
    "  | 4.2 | 20 km SE of Los Angeles, CA | 2026-03-18 07:45 | 8.0 | LOW |\n"
    "Sort so HIGH rows appear first, then MODERATE, then LOW."
)

print("\nRunning Agent 2 (Risk Assessor)...")
risk_table = agent_run(role=role2, task=analysis, model=MODEL, output="text")

print("\n--- Agent 2 Output (Risk-Classified Table) ---")
print(risk_table)

# 4. AGENT 3 — EMERGENCY ADVISOR ###################################
# Role:   Receive Agent 2's risk table; write an emergency response checklist.
# Input:  risk_table  (output from Agent 2)
# Output: checklist   (numbered action list for emergency managers)
#
# Prompt design choice:
#   - One bullet per earthquake so output is scannable.
#   - HIGH-risk items first (Agent 2 already sorted them).
#   - Cap at 10 items to keep output focused.
#   - Concrete action per line — avoids vague "monitor the situation" responses.

# Iteration 2: dropped "group by risk level" headers — too complex for small model.
# Relied on Agent 2's sort order instead so HIGH items implicitly appear first.
role3 = (
    "Return ONLY a numbered list. Do not write any other text before or after the list. "
    "For each earthquake in the table provided by the user, write one line in this exact format:\n"
    "  N. **place** (risk_level, mag magnitude): one concrete emergency response action.\n"
    "Example: 1. **150 km NE of Tokyo, Japan** (HIGH, mag 7.1): Activate regional tsunami warning system and deploy rapid assessment teams.\n"
    "Include at most 10 items. List HIGH items first, then MODERATE, then LOW."
)

print("\nRunning Agent 3 (Emergency Advisor)...")
checklist = agent_run(role=role3, task=risk_table, model=MODEL, output="text")

print("\n--- Agent 3 Output (Emergency Response Checklist) ---")
print(checklist)

# 5. FULL WORKFLOW SUMMARY ###################################

print("\n" + "="*60)
print("FULL WORKFLOW SUMMARY")
print("="*60)
print(f"\nEarthquakes fetched: {len(data)}  (showing top {len(slim)})")
print("\n[Agent 1] Cleaned earthquake table:")
print(analysis)
print("\n[Agent 2] Risk-classified table:")
print(risk_table)
print("\n[Agent 3] Emergency response checklist:")
print(checklist)

# 6. PROMPT DESIGN DOCUMENTATION ###################################
#
# Agent roles and workflow:
#   Agent 1 (Data Analyst): Receives a pre-slimmed 4-column DataFrame (magnitude,
#     place, time, depth_km) from the USGS API and returns a sorted markdown table.
#     Pre-slimming in Python (not the agent) reduces noise in the model's context.
#
#   Agent 2 (Risk Assessor): Receives Agent 1's table and adds a risk_level column
#     using explicit magnitude thresholds (>=6.5 → HIGH, 5.0-6.4 → MODERATE,
#     <5.0 → LOW). Example rows in the prompt anchor each class unambiguously.
#
#   Agent 3 (Emergency Advisor): Converts the risk table into a numbered emergency
#     response checklist, one line per earthquake with a concrete recommended action.
#
# What worked well:
#   - Pre-filtering to 4 columns before Agent 1 removed irrelevant context.
#   - "Return ONLY a markdown table" imperative was more reliable than persona framing.
#   - Providing three example rows in Agent 2's prompt anchored the exact format.
#   - smollm2:1.7b followed multi-constraint prompts far better than 135m.
#
# What was iterated:
#   Iteration 1 → 2:
#     - Model: 135m → 1.7b (small model couldn't follow multi-constraint prompts).
#     - Agent 1 prompt: changed to "Return ONLY" imperative; removed persona framing.
#     - Data pre-processing: slimmed to 4 columns before Agent 1 to reduce noise.
#     - Agent 2 prompt: clarified magnitude thresholds; added example row per class.
#     - Agent 3 prompt: dropped grouped section headers (too complex for small model).
#   Iteration 2 → 3:
#     - Agent 1: added "copy values exactly" — model was hallucinating place names.
#     - Agent 2: added three concrete example rows to anchor all three classes.
#   Remaining limitation:
#     - smollm2:1.7b occasionally misclassifies one row on long contexts.
#     - A post-processing Python step enforcing magnitude thresholds would fix this
#       for production use.
