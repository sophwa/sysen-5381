# LAB_multi_agent_with_tools.py
# Multi-Agent System with Tools
# SYSEN 5381

# Build a 2-agent workflow:
#   Agent 1 — Data Fetcher: calls get_earthquakes() to pull recent USGS earthquake data
#   Agent 2 — Report Writer: reads the fetched data and writes a plain-English summary

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import requests   # for HTTP requests
import json       # for working with JSON
import pandas as pd  # for data manipulation
from datetime import datetime, timedelta

## 0.2 Load Functions #################################

from functions import agent_run, df_as_text

## 0.3 Configuration #################################

MODEL = "smollm2:1.7b"

# 1. CUSTOM TOOL FUNCTION ###################################

def get_earthquakes(min_magnitude=4.5, days_back=7):
    """
    Fetch recent earthquake events from the USGS Earthquake Hazards API.

    Parameters
    ----------
    min_magnitude : float
        Minimum Richter magnitude to include (default: 4.5)
    days_back : int
        How many days back to query (default: 7)

    Returns
    -------
    pandas.DataFrame
        Each row is one earthquake event with columns:
        magnitude, place, time, depth_km, latitude, longitude
    """
    end   = datetime.utcnow()
    start = end - timedelta(days=days_back)

    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format":     "geojson",
        "starttime":  start.strftime("%Y-%m-%d"),
        "endtime":    end.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "orderby":    "magnitude",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    features = response.json().get("features", [])

    rows = []
    for f in features:
        props = f.get("properties", {})
        coords = f.get("geometry", {}).get("coordinates", [None, None, None])
        rows.append({
            "magnitude":  props.get("mag"),
            "place":      props.get("place"),
            "time":       datetime.utcfromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M")
                          if props.get("time") else None,
            "depth_km":   coords[2],
            "latitude":   coords[1],
            "longitude":  coords[0],
        })

    return pd.DataFrame(rows)

# 2. TOOL METADATA ###################################

tool_get_earthquakes = {
    "type": "function",
    "function": {
        "name": "get_earthquakes",
        "description": (
            "Fetch recent earthquake events from the USGS Earthquake API. "
            "Returns a table with magnitude, location, time, and depth."
        ),
        "parameters": {
            "type": "object",
            "required": ["min_magnitude", "days_back"],
            "properties": {
                "min_magnitude": {
                    "type": "number",
                    "description": "Minimum earthquake magnitude to include (e.g. 4.5)."
                },
                "days_back": {
                    "type": "integer",
                    "description": "Number of past days to search (e.g. 7)."
                }
            }
        }
    }
}

# 3. MULTI-AGENT WORKFLOW ###################################

print("🌍 Agent 1 — fetching earthquake data...")

# Agent 1: Data Fetcher — calls get_earthquakes via tool
result1 = agent_run(
    role="You fetch recent earthquake data from the USGS API.",
    task="Get earthquakes with magnitude >= 5.0 from the past 7 days.",
    model=MODEL,
    tools=[tool_get_earthquakes],
    output="tools",
    func_map={"get_earthquakes": get_earthquakes}
)

# result1 is the tool_calls list; extract the DataFrame from the last call's output
df1 = result1[-1]["output"] if isinstance(result1, list) else result1
result1_text = df_as_text(df1)

print(f"✅ Retrieved {len(df1)} earthquakes")
print(df1.head())
print()

print("📝 Agent 2 — writing summary report...")

# Agent 2: Report Writer — reads the table and writes a plain-English briefing
result2 = agent_run(
    role=(
        "You are a geoscience communicator. "
        "Given a table of recent earthquakes, write a concise 1-paragraph briefing "
        "suitable for a public newsletter. Highlight the strongest event and any notable patterns."
    ),
    task=result1_text,
    model=MODEL,
    output="text",
    tools=None
)

print("📰 Earthquake Briefing:")
print(result2)
