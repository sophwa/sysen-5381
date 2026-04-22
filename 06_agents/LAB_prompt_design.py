# LAB_prompt_design.py
# Multi-Agent Earthquake Triage Workflow
# Sophie Wang

# Three-agent pipeline: raw USGS data -> classify -> advise
# Agent 1: Data Analyst  - cleans and formats earthquake data
# Agent 2: Risk Assessor - adds risk level (HIGH/MODERATE/LOW)
# Agent 3: Emergency Advisor - produces a response checklist

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import requests     # for HTTP requests
import json         # for working with JSON
import pandas as pd # for data manipulation
import os, sys      # for path handling
from datetime import datetime, timedelta

# If you haven't already, install these packages...
# pip install requests pandas tabulate

## 0.2 Working Directory #################################

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

## 0.3 Load Functions #################################

from functions import agent_run, df_as_text

## 0.4 Configuration #################################

MODEL = "smollm2:1.7b"

# 1. FETCH USGS DATA ###################################

def get_earthquakes(min_magnitude=5.0, days=21, limit=500):
    """
    Fetch recent earthquake data from the USGS Earthquake Hazards API.

    Parameters:
    -----------
    min_magnitude : float
        Minimum earthquake magnitude to fetch (default: 5.0)
    days : int
        Number of past days to query (default: 21)
    limit : int
        Maximum number of results (default: 500)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns: magnitude, place, time, depth_km
    """

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    end = datetime.utcnow()
    start = end - timedelta(days=days)

    params = {
        "format":       "geojson",
        "starttime":    start.strftime("%Y-%m-%d"),
        "endtime":      end.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "orderby":      "time",
        "limit":        limit,
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    features = response.json().get("features", [])

    rows = []
    for f in features:
        props  = f["properties"]
        coords = f["geometry"]["coordinates"]
        rows.append({
            "magnitude": props.get("mag"),
            "place":     props.get("place"),
            "time":      datetime.utcfromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M"),
            "depth_km":  round(coords[2], 3),
        })

    return pd.DataFrame(rows)

# 2. WORKFLOW EXECUTION ###################################

print("Fetching USGS data...")
data = get_earthquakes(min_magnitude=5.0, days=21)
top15 = data.head(15)
print(f"Fetched {len(data)} earthquakes. Passing top 15 to Agent 1...\n")

task1 = df_as_text(top15)

# Agent 1: Data Analyst -------------------------
role1 = (
    "You are a seismic data analyst. "
    "Clean the earthquake data below and return it as a markdown table. "
    "Output ONLY the table with columns: magnitude, place, time, depth_km. No extra text.\n"
    "Example:\n"
    "| magnitude | place | time | depth_km |\n"
    "|---|---|---|---|\n"
    "| 7.5 | 166 km W of Neiafu, Tonga | 2026-03-24 04:37 | 229.453 |"
)

print("Running Agent 1 (Data Analyst)...")
result1 = agent_run(role=role1, task=task1, model=MODEL)
print("\n— Agent 1 Output (Cleaned Earthquake Table) —")
print(result1)

# Agent 2: Risk Assessor -------------------------
role2 = (
    "You are a seismic risk assessor. "
    "Classify each earthquake row as HIGH (magnitude >= 6.5), MODERATE (magnitude 5.5–6.4), or LOW (magnitude < 5.5). "
    "Return ONLY a markdown table with columns: magnitude, place, time, depth_km, risk_level. No extra text.\n"
    "Example:\n"
    "| magnitude | place | time | depth_km | risk_level |\n"
    "|---|---|---|---|---|\n"
    "| 7.5 | 166 km W of Neiafu, Tonga | 2026-03-24 04:37 | 229.453 | HIGH |"
)

print("\nRunning Agent 2 (Risk Assessor)...")
result2 = agent_run(role=role2, task=result1, model=MODEL)
print("\n— Agent 2 Output (Risk-Classified Table) —")
print(result2)

# Agent 3: Emergency Advisor -------------------------
role3 = (
    "You are an emergency response advisor. "
    "For each earthquake in the table, write one action item for local authorities. "
    "Lead each line with ==location== (RISK, mag X.X): action. Output a numbered checklist. Be concise.\n"
    "Example:\n"
    "1. ==166 km W of Neiafu, Tonga== (HIGH, mag 7.5): Activate regional tsunami warning system and deploy rapid assessment teams."
)

print("\nRunning Agent 3 (Emergency Advisor)...")
result3 = agent_run(role=role3, task=result2, model=MODEL)
print("\n— Agent 3 Output (Emergency Response Checklist) —")
print(result3)

# 3. FULL WORKFLOW SUMMARY ###################################

print("\n" + "=" * 60)
print("FULL WORKFLOW SUMMARY")
print("\n[Agent 1] Cleaned earthquake table:")
print(result1)
print("\n[Agent 2] Risk-classified table:")
print(result2)
print("\n[Agent 3] Emergency response checklist:")
print(result3)
