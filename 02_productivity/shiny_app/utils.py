#!/usr/bin/env python
# utils.py
# Helper functions for Marketstack API and data processing
# Pairs with my_good_query.py and LAB_your_good_api_query.md
# Tim Fraser (course materials) / Shiny app helpers
#
# This module shows how to:
# - Load an API key from a .env file
# - Make reusable API requests to Marketstack
# - Transform raw JSON into a pandas DataFrame
# - Compute simple quarterly returns for comparison plots

# 0. Setup #################################

## 0.1 Load Packages ############################

import os  # for reading environment variables
from dataclasses import dataclass  # for lightweight configuration objects
from datetime import date  # for basic date handling
from pathlib import Path  # for robust file paths
from typing import Dict, List, Tuple

import pandas as pd  # for data manipulation
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from .env


## 0.2 Load Environment Variables ################

# Load environment variables from the .env file in the project root.
# We resolve the path relative to this file so the app works even when
# launched from different working directories (e.g., via `shiny run`).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# First, try loading the .env from the calculated project root.
load_dotenv(ENV_PATH)

# Second, also try the default search starting from the current working
# directory. This mirrors the simple pattern used in my_good_query.py
# and increases the chance of picking up your .env in teaching setups.
load_dotenv()

ACCESS_KEY = os.getenv("access_key")


@dataclass
class QuarterConfig:
    """Simple container for quarter date ranges."""

    label: str
    start: date
    end: date


def get_quarter_configs(year: int) -> Dict[str, QuarterConfig]:
    """Return a dictionary of quarter codes to QuarterConfig objects.

    Parameters
    ----------
    year:
        Calendar year for which to build quarter ranges.
    """

    return {
        "Q1": QuarterConfig("Q1 2025 (Jan–Mar)", date(year, 1, 1), date(year, 3, 31)),
        "Q2": QuarterConfig("Q2 2025 (Apr–Jun)", date(year, 4, 1), date(year, 6, 30)),
        "Q3": QuarterConfig("Q3 2025 (Jul–Sep)", date(year, 7, 1), date(year, 9, 30)),
        "Q4": QuarterConfig("Q4 2025 (Oct–Dec)", date(year, 10, 1), date(year, 12, 31)),
    }


def get_tech_symbols() -> Dict[str, str]:
    """Return a dictionary mapping labels to tech stock symbols.

    This matches the example in my_good_query.py and keeps symbols
    in one place so UI and server code can share them.
    """

    return {
        "Apple (AAPL)": "AAPL",
        "Microsoft (MSFT)": "MSFT",
        "Alphabet / Google (GOOGL)": "GOOGL",
        "Amazon (AMZN)": "AMZN",
        "Meta Platforms (META)": "META",
        "NVIDIA (NVDA)": "NVDA",
        "Tencent (TCEHY)": "TCEHY",
        "Alibaba (BABA)": "BABA",
        "IBM (IBM)": "IBM",
        "Oracle (ORCL)": "ORCL",
    }


def fetch_marketstack_eod(
    symbols: List[str],
    start_date: date,
    end_date: date,
    limit: int = 500,
) -> pd.DataFrame:
    """Fetch end‑of‑day data from the Marketstack API.

    Parameters
    ----------
    symbols:
        List of stock symbols (e.g., ["AAPL", "MSFT"]).
    start_date:
        Start of date range.
    end_date:
        End of date range.
    limit:
        Maximum number of records to request.

    Returns
    -------
    pandas.DataFrame
        A tidy DataFrame with at least the columns:
        - symbol
        - date (as datetime)
        - adj_close

    Raises
    ------
    RuntimeError
        If the API key is missing or the request fails.
    """

    if ACCESS_KEY is None:
        raise RuntimeError(
            "API key 'access_key' not found in environment. "
            "Make sure your .env file exists in the dsai project root "
            "and contains a line like access_key=YOUR_KEY_HERE. "
            f"Looked for .env at: {ENV_PATH} and from working dir: {Path.cwd()}."
        )

    if not symbols:
        raise RuntimeError("You must select at least one symbol.")

    # Build the parameter dictionary for the API
    symbols_param = ",".join(symbols)
    params = {
        "access_key": ACCESS_KEY,
        "symbols": symbols_param,
        "date_from": start_date.isoformat(),
        "date_to": end_date.isoformat(),
        "limit": limit,
    }

    try:
        response = requests.get("http://api.marketstack.com/v1/eod", params=params)
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Request error occurred: {exc}") from exc

    if response.status_code != 200:
        # Show helpful details for debugging and teaching.
        raise RuntimeError(
            f"Request failed with status code {response.status_code}. "
            f"Symbols sent: {symbols_param!r}. "
            f"Raw response: {response.text[:400]}"
        )

    data_json = response.json()

    # Marketstack returns data under the "data" key.
    records = data_json.get("data", [])

    if not records:
        return pd.DataFrame(columns=["symbol", "date", "adj_close"])

    # Convert JSON records to a DataFrame and keep key fields.
    df = pd.DataFrame.from_records(records)

    # Keep only the fields we need for returns.
    df = df[["symbol", "date", "adj_close"]].copy()

    # Convert date column to datetime for proper sorting and grouping.
    df["date"] = pd.to_datetime(df["date"])

    return df


def compute_quarter_returns(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """Compute simple buy‑and‑hold returns for each symbol over the quarter.

    For each symbol, we:
    - sort by date
    - take the first and last adjusted close
    - compute return = (last - first) / first
    """

    if df.empty:
        return pd.DataFrame(columns=["symbol", "start_date", "end_date", "return_pct"])

    # Sort so first/last are well defined
    df_sorted = df.sort_values(["symbol", "date"])

    grouped = df_sorted.groupby("symbol", as_index=False)

    summary = grouped.agg(
        start_date=("date", "first"),
        end_date=("date", "last"),
        start_price=("adj_close", "first"),
        end_price=("adj_close", "last"),
    )

    # Avoid division‑by‑zero
    summary = summary[summary["start_price"] != 0].copy()
    summary["return_pct"] = (summary["end_price"] - summary["start_price"]) / summary[
        "start_price"
    ]

    # For display, keep just the most interpretable fields.
    summary = summary[["symbol", "start_date", "end_date", "return_pct"]]

    return summary


def get_quarter_and_dates(year: int, quarter_code: str) -> Tuple[str, date, date]:
    """Helper to map a quarter code like 'Q1' to a label and dates."""

    quarters = get_quarter_configs(year)

    if quarter_code not in quarters:
        raise ValueError(f"Unknown quarter code: {quarter_code}")

    cfg = quarters[quarter_code]
    return cfg.label, cfg.start, cfg.end

