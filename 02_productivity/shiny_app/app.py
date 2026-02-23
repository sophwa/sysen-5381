#!/usr/bin/env python
# app.py
# 2025 Tech Stocks Quarterly Returns – Shiny for Python App
# Pairs with my_good_query.py and LAB_your_good_api_query.md
# Tim Fraser (course materials) / Shiny app entry point
#
# This script shows how to:
# - Structure a Shiny for Python app into UI, server, and helpers
# - Implement an API‑backed data app with clear, educational code
# - Compare quarterly returns for major tech companies in 2025

# 0. Setup #################################

## 0.1 Load Packages ############################

from shiny import App  # main Shiny application object

# Note on imports:
# This app is typically launched using:
#   shiny run 02_productivity/shiny_app/app.py
# In that mode, Shiny imports this file in a way that does not always support
# package-style relative imports (like `from .server import server`).
# We therefore use same-folder imports.
from server import server  # server logic
from ui_components import app_ui  # UI layout


## 1. Create App ###############################

app = App(app_ui, server)


if __name__ == "__main__":
    # Allow running with: python app.py
    # In many setups, you can also use:
    #   shiny run --reload app.py
    app.run()

