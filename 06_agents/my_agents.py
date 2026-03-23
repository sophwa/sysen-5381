# 2-Agent Workflow: Data Summary → Formatted Report
# Agent 1 – Summarizer : receives raw tabular data  → produces a concise summary
# Agent 2 – Formatter  : receives the summary       → produces a formatted report

# ── 0. SETUP ──────────────────────────────────────────────────────────────────

import os
import pandas as pd
from functions import get_shortages
from ollama import Client

# Override agent_run to use ollama.com cloud instead of localhost
_client = Client(
    host="https://ollama.com",
    headers={
        "Authorization": f"Bearer {os.environ.get('OLLAMA_API_KEY', '')}"},
)


def agent_run(role: str, task: str, model: str = "smollm2:135m-cloud", **kwargs) -> str:
    response = _client.chat(
        model=model,
        messages=[
            {"role": "system", "content": role},
            {"role": "user",   "content": task},
        ],
    )
    return response["message"]["content"]

# Override df_as_text to avoid the tabulate dependency in functions.py


def df_as_text(df, max_rows=40):
    if df.empty:
        return "(No data available)"
    return df.head(max_rows).to_string(index=False)

# ── 1. CONFIGURATION ──────────────────────────────────────────────────────────


MODEL = "smollm2:135m-cloud"   # ollama cloud model (remote inference)
CATEGORY = "Psychiatry"           # FDA therapeutic category to query
LIMIT = 200                    # Max records to fetch

# ── 2. DATA FETCH (no agent) ──────────────────────────────────────────────────

print(f"\n📡  Fetching FDA drug shortage data  [category='{CATEGORY}'] …")

raw = get_shortages(category=CATEGORY, limit=LIMIT)

if raw.empty:
    raise SystemExit(
        "❌  No data returned from FDA API – check your network / category.")

print(f"    ✅  {len(raw)} records retrieved.\n")

# Keep only the most-recent entry per drug
latest = (
    raw
    .groupby("generic_name", group_keys=False)
    # ← fixed warning
    .apply(lambda g: g.loc[g["update_date"].idxmax()], include_groups=False)
    .reset_index(drop=True)
)

# Convert DataFrame → plain text for the LLM prompt
raw_table_text = df_as_text(latest)

# ── 3. AGENT 1 – SUMMARIZER ───────────────────────────────────────────────────
# Input  : raw tabular data (text)
# Output : a concise bullet-point summary of key findings

print("🤖  Agent 1 (Summarizer) is reading the raw data …")

role_agent1 = """
You are a clinical pharmacist analyst.
You receive a plain-text table of FDA drug shortage records and produce
a concise structured summary with:
  • Total number of drugs listed
  • How many are currently Unavailable vs. Available vs. other statuses
  • The 3–5 most notable shortages (drug name + reason if available)
  • Any common shortage reasons you notice across the dataset
Keep the summary under 300 words. Use bullet points.
"""

summary = agent_run(role=role_agent1, task=raw_table_text, model=MODEL)

print("    ✅  Summary produced.\n")
print("─" * 60)
print("AGENT 1 OUTPUT (summary passed to Agent 2):")
print("─" * 60)
print(summary)
print("─" * 60 + "\n")

# ── 4. AGENT 2 – FORMATTER ────────────────────────────────────────────────────
# Input  : the summary produced by Agent 1
# Output : a polished, stakeholder-ready Markdown report

print("📝  Agent 2 (Formatter) is drafting the report …")

role_agent2 = """
You are a public-health communications specialist.
You receive a bullet-point summary of current psychiatric drug shortages
and convert it into a one-page, stakeholder-ready Markdown report that includes:
  1. A short executive summary (2–3 sentences)
  2. A "Key Findings" section with a Markdown table listing notable drugs,
     their availability status, and shortage reason
  3. A "Recommendations" section with 2–3 actionable steps for healthcare
     providers or pharmacy teams
  4. A footer with a data-source citation: FDA Drug Shortages API
     (https://open.fda.gov/apis/drug/drugshortages/)
Use clear Markdown headings, bold text for drug names, and a professional tone.
"""

report = agent_run(role=role_agent2, task=summary, model=MODEL)

print("    ✅  Report produced.\n")

# ── 5. RESULTS ────────────────────────────────────────────────────────────────

print("=" * 60)
print("📰  FINAL REPORT (Agent 2 output)")
print("=" * 60)
print(report)

# Save both agent outputs to a file
output_path = "shortage_report.md"
with open(output_path, "w", encoding="utf-8") as f:
    f.write("# Psychiatric Drug Shortage Report\n\n")
    f.write(f"**Category queried:** {CATEGORY}  \n")
    f.write(f"**Records fetched:** {len(raw)}  \n\n")
    f.write("---\n\n")
    f.write("## Agent 1 Summary\n\n")
    f.write(summary)
    f.write("\n\n---\n\n")
    f.write("## Agent 2 Formatted Report\n\n")
    f.write(report)

print(f"\n💾  Report saved to: {output_path}")
