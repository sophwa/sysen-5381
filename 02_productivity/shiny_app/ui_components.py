#!/usr/bin/env python
# ui_components.py
# Shiny UI layout for the 2025 Tech Stocks Quarterly Returns app
# Pairs with app.py and server.py
# Tim Fraser (course materials) / Shiny app UI
#
# This file shows how to:
# - Build a clean, modern Shiny for Python layout
# - Expose input controls for API query parameters
# - Display text, plots, and tables in a dashboard‑style page

# 0. Setup #################################

## 0.1 Load Packages ############################

from shiny import ui  # core Shiny UI components

from .utils import get_tech_symbols, get_quarter_configs  # shared helpers


## 1. Define UI ###############################

def create_app_ui() -> ui.Tag:
    """Create the top‑level Shiny UI.

    We use cards and a fluid layout to create a modern, dashboard‑like
    appearance that is still simple and easy to understand for learners.
    """

    # get_tech_symbols() returns a mapping of human‑readable labels to symbols.
    # Shiny for Python expects dictionary *keys* to be the values returned to
    # the server, and dictionary *values* to be the labels shown in the UI.
    # So we reverse the mapping here so that the server receives symbols like
    # "AAPL" and "MSFT", while users see friendly labels.
    label_to_symbol = get_tech_symbols()
    symbol_to_label = {symbol: label for label, symbol in label_to_symbol.items()}
    quarter_configs = get_quarter_configs(2025)

    # Build choices for the quarter dropdown using the config labels.
    quarter_labels = {code: cfg.label for code, cfg in quarter_configs.items()}

    return ui.page_fluid(
        ui.tags.style(
            """
            body { background-color: #f5f7fb; }
            .app-title { margin-bottom: 0.2rem; }
            .app-subtitle { color: #555; margin-bottom: 1.5rem; }
            """
        ),
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("2025 Tech Stocks – Quarterly Returns"),
                ui.markdown(
                    """
                    This app queries the **Marketstack** API for major tech companies
                    and computes simple buy‑and‑hold returns over a selected quarter in 2025.

                    - Pick a **quarter** in 2025  
                    - Choose one or more **tech companies**  
                    - Click **Run API Query** to fetch data and update the chart
                    """
                ),
                ui.layout_columns(
                    ui.input_select(
                        "quarter",
                        "Select quarter (2025):",
                        choices=quarter_labels,
                        selected="Q4",
                    ),
                    ui.input_checkbox_group(
                        "symbols",
                        "Select tech companies:",
                        choices=symbol_to_label,
                        selected=list(symbol_to_label.keys()),
                    ),
                ),
                ui.input_action_button(
                    "run_query",
                    "Run API Query",
                    class_="btn-primary",
                ),
                ui.div(
                    ui.output_text("status_text"),
                    class_="mt-2 text-muted",
                ),
            ),
            width=1,
        ),
        ui.layout_column_wrap(
            ui.card(
                ui.card_header("Quarterly Returns (Bar Chart)"),
                ui.output_plot("returns_plot"),
            ),
            ui.card(
                ui.card_header("Quarterly Returns – Table"),
                ui.output_table("returns_table"),
            ),
            width="200px",
        ),
    )


# Expose a module‑level variable for convenient import from app.py
app_ui = create_app_ui()
