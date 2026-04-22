# LAB_multi_agent_with_tools.py
# Multi-Agent Earthquake System with Function Calling
# Sophie Wang

# Agent 1 calls get_earthquake() to fetch live USGS data at runtime,
# then hands the result to Agent 2 to write a newsletter summary.

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

# 1. DEFINE GET_EARTHQUAKE TOOL ###################################

def get_earthquake(min_magnitude=5.0, days=21, limit=34):
    """
    Fetch recent earthquake data from the USGS Earthquake Hazards API.

    Parameters:
    -----------
    min_magnitude : float
        Minimum magnitude to include (default: 5.0)
    days : int
        Number of past days to query (default: 21)
    limit : int
        Maximum number of results to return (default: 34)

    Returns:
    --------
    pandas.DataFrame
        DataFrame with columns: magnitude, place, time, depth_km, latitude, longitude
    """

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    end   = datetime.utcnow()
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
            "latitude":  round(coords[1], 3),
            "longitude": round(coords[0], 3),
        })

    return pd.DataFrame(rows)

# 2. DEFINE TOOL METADATA ###################################

tool_get_earthquake = {
    "type": "function",
    "function": {
        "name": "get_earthquake",
        "description": "Fetch recent earthquake data from the USGS Earthquake Hazards API",
        "parameters": {
            "type": "object",
            "required": ["min_magnitude", "days", "limit"],
            "properties": {
                "min_magnitude": {
                    "type":        "number",
                    "description": "Minimum earthquake magnitude (default: 5.0)",
                },
                "days": {
                    "type":        "number",
                    "description": "Number of past days to fetch (default: 21)",
                },
                "limit": {
                    "type":        "number",
                    "description": "Maximum number of results to return (default: 34)",
                },
            },
        },
    },
}

# 3. MULTI-AGENT WORKFLOW ###################################

# Agent 1: Earthquake Data Fetcher (with tools) -------------------------
# Uses get_earthquake() to pull fresh data from the USGS API at runtime.
print("Agent 1: Earthquake Data Fetcher (with tools)")

task1 = "Fetch recent earthquake data with minimum magnitude 5.0 from the past 21 days, limit 34."
role1 = "Fetch recent earthquake data from the USGS API using the get_earthquake tool."

result1_calls = agent_run(
    role=role1,
    task=task1,
    model=MODEL,
    output="tools",
    tools=[tool_get_earthquake],
    func_map={"get_earthquake": get_earthquake},   # explicit map so the function resolves correctly
)

# Extract the DataFrame returned by the tool call
result1_df = (
    result1_calls[0].get("output")
    if isinstance(result1_calls, list) and len(result1_calls) > 0
    else get_earthquake()   # fallback: run directly if LLM didn't trigger the tool
)

print(f"Retrieved {len(result1_df)} earthquakes (showing top 15):")
print(df_as_text(result1_df.head(15)))

# Agent 2: Newsletter Writer (no tools) -------------------------
# Receives the earthquake table and writes a public-facing summary.
result1_text = df_as_text(result1_df.head(15))

role2 = (
    "You are a science journalist. "
    "Write a short 2–3 paragraph newsletter summary of the recent earthquake data. "
    "Include notable patterns, the most significant events, and any regional trends. "
    "Be informative and accessible to a general audience."
)

print("\nAgent 2: Newsletter Writer")
result2 = agent_run(role=role2, task=result1_text, model=MODEL)
print(result2)
