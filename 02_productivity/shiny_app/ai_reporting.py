#!/usr/bin/env python
# ai_reporting.py
# AI summary helper for the 2025 Tech Stocks Quarterly Returns app
# Pairs with server.py, ui_components.py, and api_reporter.py
# Tim Fraser (course materials) / Shiny app AI helper
#
# This module shows how to:
# - Load an AI API key from a .env file
# - Prepare a compact data structure for AI consumption
# - Call an Ollama cloud model to generate a short report
# - Return plain text that can be rendered inside a Shiny app

# 0. Setup #################################

## 0.1 Load Packages ############################

from __future__ import annotations

import os  # for reading environment variables
from pathlib import Path  # for robust file paths
from typing import List

import pandas as pd  # for data manipulation and typing
import requests  # for HTTP requests to the AI API
from dotenv import load_dotenv  # for loading variables from .env


## 0.2 Load Environment Variables ################

# Resolve the project root so we can load .env reliably when the app is
# launched from different working directories (e.g., via `shiny run`).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# First, try loading the .env from the calculated project root.
load_dotenv(ENV_PATH)

# Second, fall back to the default search from the current working dir.
load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

# Endpoint and model match the pattern used in 03_query_ai/api_reporter.py
OLLAMA_URL = "https://ollama.com/api/chat"
OLLAMA_MODEL = "gpt-oss:20b-cloud"


## 1. AI Reporting Helper ###############################

def _prepare_ai_data(returns_df: pd.DataFrame) -> List[dict]:
    """Convert returns data into a compact list of dicts for the AI model.

    The Shiny app computes buy-and-hold returns per symbol over a quarter.
    We keep only:
    - symbol
    - quarter (label)
    - return_pct (percentage, rounded for readability)
    """

    if returns_df.empty:
        return []

    display_df = returns_df.copy()
    if "return_pct" in display_df.columns:
        display_df["return_pct"] = (display_df["return_pct"] * 100).round(2)

    cols = [c for c in ["symbol", "quarter", "return_pct"] if c in display_df.columns]
    return display_df[cols].to_dict(orient="records")


def generate_ai_report(returns_df: pd.DataFrame) -> str:
    """Generate an AI-powered executive summary for quarterly returns.

    Parameters
    ----------
    returns_df:
        DataFrame produced by compute_quarter_returns(), with at least:
        - symbol
        - return_pct (0–1, not percent)
        - quarter (label added in server.py)

    Returns
    -------
    str
        Plain-text report suitable for display inside the Shiny app.

    Raises
    ------
    RuntimeError
        If the AI API key is missing or the request fails.
    """

    if OLLAMA_API_KEY is None:
        raise RuntimeError(
            "AI API key 'OLLAMA_API_KEY' not found in environment. "
            "Update your .env file in the project root (dsai) with a line like "
            "OLLAMA_API_KEY=YOUR_OLLAMA_KEY_HERE before using the AI summary."
        )

    if returns_df.empty:
        raise RuntimeError(
            "No returns data available for AI summary. "
            "Run the API query successfully before requesting an AI report."
        )

    ai_ready_data = _prepare_ai_data(returns_df)
    quarter_label = (
        returns_df["quarter"].iloc[0] if "quarter" in returns_df.columns else "the selected quarter"
    )

    prompt = f"""
You are a financial data analyst.

Below is a summary of buy-and-hold returns for major tech stocks in {quarter_label}.
Each item includes:
- symbol: stock ticker
- return_pct: percentage return over the quarter

Data:
{ai_ready_data}

Tasks:
1. Write a 2–3 sentence executive summary comparing performance across companies.
2. Identify the top 2–3 best-performing and the 1–2 worst-performing symbols by return_pct.
3. Comment briefly on overall market tone (for example, broadly positive, mixed, or negative).
4. Keep the response under 150 words.
5. Base your analysis only on the provided data.

Format exactly as:

Executive Summary:
[2–3 sentences]

Top Insights:
- [Insight 1]
- [Insight 2]
- [Insight 3]
"""

    body = {
        "model": OLLAMA_MODEL,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "stream": False,
    }

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(OLLAMA_URL, headers=headers, json=body, timeout=60)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Error contacting Ollama API: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"Ollama API request failed with status code {response.status_code}. "
            f"Raw response: {response.text[:400]}"
        )

    result = response.json()

    message = result.get("message", {})
    content = message.get("content")

    if not content:
        raise RuntimeError("Ollama API returned an unexpected response without content.")

    return str(content).strip()

