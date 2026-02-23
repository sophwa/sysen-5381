# 2025 Tech Stocks Shiny App

> This Shiny for Python app (`[app.py](app.py)`) queries the Marketstack API for major tech stocks and visualizes their quarterly returns for 2025.

---

## Overview

This app demonstrates how to build a small, API‑backed dashboard using [Shiny for Python](https://shiny.rstudio.com/py/).  
It lets you:

- **Select a quarter in 2025** (Q1–Q4).
- **Choose one or more tech companies** (Apple, Microsoft, Google, Amazon, etc.).
- **Fetch end‑of‑day price data from Marketstack** on demand.
- **Compute simple buy‑and‑hold returns** over the selected quarter.
- **Compare performance** across companies using a bar chart and a summary table.
- **Generate an AI‑written executive summary** of the quarterly performance using an Ollama cloud model.

The app is structured to match best practices for Shiny:

- `app.py` – main entry point and Shiny `App` object.
- `ui_components.py` – UI layout and inputs/outputs.
- `server.py` – reactive server logic and rendering (including AI summary output).
- `utils.py` – API helpers and data transformation functions.
- `ai_reporting.py` – helper that calls an Ollama cloud model to generate the AI summary.

---

## Data Summary

The core API data comes from the **Marketstack** `/v1/eod` endpoint and is transformed into a tidy table of quarterly returns. Key columns:

```markdown
| Column Name | Type    | Description                                                     |
|------------|---------|-----------------------------------------------------------------|
| symbol     | string  | Stock ticker symbol (e.g., `AAPL`, `MSFT`, `GOOGL`).            |
| date       | date    | Trading date for each end‑of‑day (EOD) price from Marketstack.  |
| adj_close  | float   | Adjusted closing price for the symbol on `date`.                |
| start_date | date    | First trading date in the selected quarter for each `symbol`.   |
| end_date   | date    | Last trading date in the selected quarter for each `symbol`.    |
| return_pct | float   | Buy‑and‑hold return over the quarter (0.10 = 10% gain).         |
| quarter    | string  | Human‑readable label, e.g., `Q4 2025 (Oct–Dec)`.                |
```

The Shiny app uses `symbol`, `start_date`, `end_date`, `return_pct`, and `quarter` for visualization, and passes the same summary data into `ai_reporting.py` to construct an AI‑friendly prompt.

---

## Installation

**Prerequisites:**

- Python 3.10+ recommended.
- A working internet connection (for API calls).

From the project root, install the required packages:

```bash
pip install -r 02_productivity/shiny_app/requirements.txt
```

This installs:

- `shiny` – Shiny for Python.
- `pandas` – data wrangling and summarization.
- `requests` – HTTP requests to the API.
- `python-dotenv` – loading environment variables from `.env`.
- `matplotlib` – plotting quarterly returns.

---

## API Requirements

This app uses the **Marketstack** end‑of‑day endpoint:

- **Endpoint:** `http://api.marketstack.com/v1/eod`
- **Method:** `GET`
- **Key parameters:**
  - `access_key` – your Marketstack API key (required).
  - `symbols` – comma‑separated stock symbols (e.g., `AAPL,MSFT,GOOGL`).
  - `date_from` / `date_to` – ISO‑formatted dates for the selected quarter.
  - `limit` – maximum number of returned records.

**API key setup (Marketstack):**

1. Create a Marketstack account and obtain an API key.
2. In the `dsai` project root (same level as `01_query_api` and `02_productivity`), create a `.env` file.
3. Add a line with your key:

```text
access_key=YOUR_MARKETSTACK_KEY_HERE
```

4. Save the file; do not commit `.env` to version control.

The app uses `python-dotenv` to load this key in `[utils.py](utils.py)` before making requests.

**AI API key setup (Ollama cloud):**

The AI executive summary uses an Ollama cloud model via HTTPS:

- **Endpoint:** `https://ollama.com/api/chat`  
- **Model:** `gpt-oss:20b-cloud` (configured in `ai_reporting.py`)

To enable AI reporting:

1. Obtain an Ollama cloud API key.
2. In the same `.env` file in the project root, add:

   ```text
   OLLAMA_API_KEY=YOUR_OLLAMA_KEY_HERE
   ```

3. Save the file (do **not** commit `.env`).

If `OLLAMA_API_KEY` is missing or invalid, the Shiny app will still run, but the AI summary pane will show a friendly error message instead of a report.

---

## How to Run the App

From the `dsai` project root, run the Shiny app with:

```bash
shiny run 02_productivity/shiny_app/app.py
```

Alternatively, you can run it as a module:

```bash
python3 02_productivity/shiny_app/app.py
```

Then open the URL printed in the terminal (typically `http://localhost:8000`) in your browser.

---

## Usage Instructions

1. **Choose a quarter**
   - Use the **“Select quarter (2025)”** dropdown to pick `Q1`, `Q2`, `Q3`, or `Q4`.
   - Internally, the app maps each quarter to the correct `date_from` and `date_to` range.

2. **Select tech companies**
   - Use the **checkbox group** to choose one or more companies (e.g., Apple, Microsoft, NVIDIA).
   - The app sends their ticker symbols (e.g., `AAPL`, `MSFT`, `NVDA`) to the API.

3. **Run the query**
   - Click **“Run API Query”**.
   - The app:
     - Calls the Marketstack `/v1/eod` endpoint for the selected symbols and dates.
     - Converts the JSON records to a tidy `pandas` DataFrame.
     - Computes a simple quarterly return for each symbol:
       - \(\text{return} = (\text{last\_price} - \text{first\_price}) / \text{first\_price}\).

4. **Interpret the outputs**
   - **Status text:** Shows whether data loaded successfully or describes any error (e.g., missing API key).
   - **Quarterly Returns (Bar Chart):**
     - **x‑axis:** Stock symbol (e.g., `AAPL`, `MSFT`).
     - **y‑axis:** Return over the selected quarter (percent).
     - A horizontal zero line helps distinguish gains from losses.
   - **Quarterly Returns – Table:**
     - Lists `symbol`, `start_date`, `end_date`, `return_pct` (in %), and `quarter`.
     - Useful for checking exact values behind the chart.
   - **AI‑Generated Executive Summary:**
     - Uses the same quarterly returns data to produce a short narrative report.
     - Helpful for quickly explaining which companies out‑ or under‑performed.
     - Always verify the narrative against the chart and table.

5. **Common errors**
   - **Missing API key:** Ensure `.env` exists in the project root and includes `access_key=...`.
   - **No data returned:** Check that your key is valid and that the selected symbols/quarter are supported by your Marketstack plan.
   - **AI summary error:** Ensure `.env` includes `OLLAMA_API_KEY=...` and that your Ollama key is valid. If the AI call fails, the status text will explain why.

---

## Related Files and References

- App entry point: `[app.py](app.py)`
- UI layout: `[ui_components.py](ui_components.py)`
- Server logic: `[server.py](server.py)`
- Helpers and API code: `[utils.py](utils.py)`
- Course lab: `[LAB: Develop a Meaningful API Query](../../01_query_api/LAB_your_good_api_query.md)`
- Shiny for Python documentation: [Shiny for Python – Get Started](https://shiny.rstudio.com/py/)

