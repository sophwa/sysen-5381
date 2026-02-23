#!/usr/bin/env python
# server.py
# Shiny server logic for the 2025 Tech Stocks Quarterly Returns app
# Pairs with app.py and ui_components.py
# Tim Fraser (course materials) / Shiny app server
#
# This file shows how to:
# - React to user input and button clicks
# - Call a reusable API helper function
# - Handle errors gracefully and display clear messages
# - Render a bar chart and table of quarterly returns

# 0. Setup #################################

## 0.1 Load Packages ############################

from typing import Optional

import matplotlib.pyplot as plt  # for plotting in Shiny
import pandas as pd  # for type hints and clarity
from shiny import render, reactive  # Shiny server tools

from .ai_reporting import generate_ai_report  # AI reporting helper
from .utils import (  # reusable helper functions
    compute_quarter_returns,
    fetch_marketstack_eod,
    get_quarter_and_dates,
)


## 1. Server Function ###############################

def server(input, output, session):
    """Define the Shiny server function.

    This follows the standard Shiny pattern:
    - reactive calculations for data
    - render functions for outputs (text, plots, tables)
    """

    # Store the latest error message (if any) in a reactive value
    last_error: reactive.Value[Optional[str]] = reactive.Value(None)
    # Store the latest AI report (if any) and AI-specific error
    ai_report_text: reactive.Value[Optional[str]] = reactive.Value(None)
    ai_error: reactive.Value[Optional[str]] = reactive.Value(None)

    @reactive.event(input.run_query)
    def _fetch_and_compute() -> pd.DataFrame:
        """Event‑driven reactive that runs when the user clicks the button."""

        last_error.set(None)  # clear previous errors
        ai_error.set(None)
        ai_report_text.set(None)

        try:
            quarter_code = input.quarter()
            quarter_label, start_date, end_date = get_quarter_and_dates(
                2025, quarter_code)

            symbols = list(input.symbols())

            raw_df = fetch_marketstack_eod(
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
            )

            returns_df = compute_quarter_returns(raw_df)

            # Add a friendly label column for display
            returns_df = returns_df.copy()
            returns_df["quarter"] = quarter_label

            # Try to generate an AI summary using the same returns data.
            # If the AI request fails, we keep the main app working and
            # surface a friendly message instead of an exception.
            try:
                report_text = generate_ai_report(returns_df)
                ai_report_text.set(report_text)
            except Exception as exc:  # broad for teaching; log-friendly message
                ai_error.set(str(exc))

            return returns_df

        except Exception as exc:  # broad for teaching; in production, be more specific
            last_error.set(str(exc))
            ai_error.set(None)
            ai_report_text.set(None)
            # Return an empty DataFrame so downstream render functions
            # can still run and show a friendly message.
            return pd.DataFrame(columns=["symbol", "start_date", "end_date", "return_pct", "quarter"])

    @reactive.calc
    def returns_data() -> pd.DataFrame:
        """Expose the latest returns data to outputs.

        This reactive depends on the event‑based calculation above,
        so it updates only when the user clicks the button.
        """

        return _fetch_and_compute()

    @output
    @render.text
    def status_text() -> str:
        """Show human‑readable status or error text."""

        error_msg = last_error()
        if error_msg:
            return f"⚠️ Error: {error_msg}"

        df = returns_data()
        if df.empty:
            return "Click 'Run API Query' to fetch data for the selected quarter."

        symbols = ", ".join(sorted(df["symbol"].unique()))
        quarter_label = df["quarter"].iloc[0]

        return f"Showing quarterly returns for {symbols} in {quarter_label}."

    @output
    @render.text
    def ai_summary() -> str:
        """AI‑generated executive summary based on the quarterly returns."""

        # Ensure we react to the same data updates as the other outputs.
        df = returns_data()

        # If the main query has not run yet, show guidance text.
        if df.empty and last_error() is None:
            return "Run the API query first. An AI summary will appear here once data is available."

        # If there was a main error, do not show an AI summary.
        if last_error():
            return "AI summary unavailable because the main API query did not succeed."

        # Prefer AI-specific error messages when the AI call failed.
        if ai_error():
            return f"⚠️ AI summary error: {ai_error()}"

        report_text = ai_report_text()
        if not report_text:
            return "AI summary will appear here after a successful query."

        return report_text

    @output
    @render.plot
    def returns_plot():
        """Bar chart of quarterly returns by company."""

        df = returns_data()

        fig, ax = plt.subplots(figsize=(8, 4))

        if df.empty:
            ax.text(
                0.5,
                0.5,
                "No data to display.\nCheck your API key and try again.",
                ha="center",
                va="center",
                fontsize=11,
                transform=ax.transAxes,
            )
            ax.set_axis_off()
            return fig

        # Sort symbols for a clean x‑axis
        plot_df = df.sort_values("symbol")
        x_labels = plot_df["symbol"]
        y_values = plot_df["return_pct"] * 100  # convert to percent

        ax.bar(x_labels, y_values, color="#3b82f6")

        quarter_label = plot_df["quarter"].iloc[0]
        ax.set_title(f"Tech Company Returns – {quarter_label}")
        ax.set_xlabel("Company (symbol)")
        ax.set_ylabel("Return (%) over quarter")
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_xticklabels(x_labels, rotation=45, ha="right")

        fig.tight_layout()
        return fig

    @output
    @render.table
    def returns_table():
        """Tabular view of returns for transparency."""

        df = returns_data()

        if df.empty:
            # Show an empty, but well‑labeled, table.
            return pd.DataFrame(
                {
                    "symbol": [],
                    "start_date": [],
                    "end_date": [],
                    "return_pct": [],
                    "quarter": [],
                }
            )

        display_df = df.copy()
        # Format return as percent with 1 decimal place for the table.
        display_df["return_pct"] = (display_df["return_pct"] * 100).round(1)

        return display_df
