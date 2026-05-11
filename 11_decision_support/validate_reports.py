# validate_reports.py
# AI Report Validation System — Homework 3
# Sophie Wang
#
# Custom validation system for AI-generated PM10 emissions policy reports.
# Evaluates five domain-specific quality dimensions, then uses ANOVA + t-tests
# to compare three generation prompts (A, B, C).
#
# Usage:
#   pip install openai python-dotenv pandas scipy pingouin matplotlib
#   python3 11_decision_support/validate_reports.py
#
# Requires OPENAI_API_KEY in .env (project root).

# ── 0. Setup ──────────────────────────────────────────────────────────────────

import os
import json
import re
import time
import requests
import pandas as pd
import matplotlib
matplotlib.use("Agg")          # headless — no display needed
import matplotlib.pyplot as plt
from scipy.stats import bartlett
import pingouin as pg

# Ollama local configuration (no API key required)
OLLAMA_HOST  = "http://localhost:11434"
OLLAMA_MODEL = "llama3.2:latest"

# Source data the reports are supposed to summarise
SOURCE_DATA = """\
White County, IL | 2015 | PM10 | Time Driven | hours

Vehicle Type  | VMT (hours)  | Share
Light Truck   | 2,700,000    | 51.8%
Car/Bike      | 1,900,000    | 36.1%
Combo Truck   |   381,300    |  7.3%
Heavy Truck   |   220,700    |  4.2%
Bus           |    30,600    |  0.6%
TOTAL         | 5,232,600    | 100.0%\
"""

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── 1. Generation Prompts ─────────────────────────────────────────────────────
#
# Three prompts that vary in instruction specificity and style.
# Prompt A: comprehensive + formal (most specific)
# Prompt B: concise + technical (moderately specific)
# Prompt C: open-ended narrative (least specific)
#
# Hypothesis: A > B > C on overall validation score.

GENERATION_PROMPTS = {
    "A": (
        "You are an environmental policy analyst authoring a formal technical report. "
        "Using the provided PM10 emissions data, write a precise 4–5 sentence paragraph that:\n"
        "  1. Names every vehicle category and cites its exact share from the data.\n"
        "  2. Explicitly justifies why certain categories are prioritised for intervention.\n"
        "  3. Proposes at least two targeted, mechanism-specific policy actions.\n"
        "Use formal government-report language. Do not add or invent statistics."
    ),
    "B": (
        "Summarise the PM10 emissions data in 2–3 concise, technically accurate sentences. "
        "Include the most important percentages and conclude with one specific policy recommendation."
    ),
    "C": (
        "Write a short paragraph about the PM10 emissions situation. "
        "Mention the vehicle types and suggest what could be done about it."
    ),
}

def _ollama_chat(messages: list, use_json: bool = False) -> str:
    body = {
        "model":    OLLAMA_MODEL,
        "messages": messages,
        "stream":   False,
    }
    if use_json:
        body["format"] = "json"
    resp = requests.post(f"{OLLAMA_HOST}/api/chat", json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]

def generate_report(prompt_text: str) -> str:
    messages = [
        {"role": "system", "content": prompt_text},
        {"role": "user",   "content": f"Source Data:\n{SOURCE_DATA}\n\nWrite the paragraph now."},
    ]
    return _ollama_chat(messages).strip()

# ── 2. Custom Validation Criteria ─────────────────────────────────────────────
#
# Five domain-specific dimensions designed for PM10 policy-report evaluation.
# These differ from the LAB's generic Likert scales (accuracy, formality,
# faithfulness, clarity, succinctness, relevance) in three ways:
#   • All use a 0–10 continuous scale instead of 1–5 Likert.
#   • Each dimension targets a policy-reporting concern, not general writing quality.
#   • A boolean `data_accurate` flag guards against factual fabrication.
#
# Dimensions:
#   numeric_fidelity     — Are cited percentages/counts identical to source data?
#   completeness         — Are all five vehicle categories addressed?
#   policy_specificity   — Are recommendations specific (mechanism, target vehicle)?
#   scientific_hedging   — Is epistemic tone appropriate (no overstatement)?
#   prioritization_logic — Is vehicle prioritisation explicitly data-justified?

VALIDATOR_SYSTEM = """\
You are a domain expert reviewing AI-generated PM10 traffic-emissions policy reports.
Evaluate the report strictly against the source data provided.

Return ONLY valid JSON with exactly these keys:
{
  "numeric_fidelity":     <integer 0-10>,
  "completeness":         <integer 0-10>,
  "policy_specificity":   <integer 0-10>,
  "scientific_hedging":   <integer 0-10>,
  "prioritization_logic": <integer 0-10>,
  "data_accurate":        <true|false>,
  "rationale":            "<20-40 word explanation>"
}

Rubric:
  numeric_fidelity (0–10):
    10 = every cited percentage/count exactly matches the source data
     5 = minor rounding errors but no misrepresentations
     0 = statistics are wrong or invented
  completeness (0–10):
    10 = all five vehicle categories (Light Truck, Car/Bike, Combo Truck, Heavy Truck, Bus) mentioned with data
     6 = top two mentioned; others omitted
     0 = no vehicle categories addressed
  policy_specificity (0–10):
    10 = ≥2 interventions, each tied to a specific vehicle category with a described mechanism
     5 = one vague recommendation (e.g., "stricter standards")
     0 = no policy recommendations
  scientific_hedging (0–10):
    10 = appropriate epistemic language; no unjustified certainty or alarm
     5 = mostly appropriate but one overstatement
     0 = alarmist, hyperbolic, or unfounded certainty throughout
  prioritization_logic (0–10):
    10 = prioritisation explicitly grounded in share percentages from the data
     5 = prioritises correctly but without data justification
     0 = arbitrary or no prioritisation
  data_accurate (boolean):
    true  = no statistic in the report misrepresents the source data
    false = at least one incorrect statistic\
"""

def validate_report(report_text: str) -> dict:
    prompt = f"Source Data:\n{SOURCE_DATA}\n\nReport to Evaluate:\n{report_text}"
    messages = [
        {"role": "system", "content": VALIDATOR_SYSTEM},
        {"role": "user",   "content": prompt},
    ]
    raw = _ollama_chat(messages, use_json=True)
    # extract JSON if model wraps it in text
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(m.group(0) if m else raw)
    dims = ["numeric_fidelity", "completeness", "policy_specificity",
            "scientific_hedging", "prioritization_logic"]
    data["overall_score"] = round(sum(data[d] for d in dims) / len(dims), 2)
    return data

# ── 3. Experiment ─────────────────────────────────────────────────────────────

N_PER_PROMPT = 15   # 15 reports × 3 prompts = 45 total observations
records = []

for pid, prompt_text in GENERATION_PROMPTS.items():
    print(f"\n{'─'*40}\nPrompt {pid}  ({N_PER_PROMPT} runs)\n{'─'*40}")
    for i in range(1, N_PER_PROMPT + 1):
        print(f"  [{i:02d}/{N_PER_PROMPT}] generating ...", end=" ", flush=True)
        try:
            report  = generate_report(prompt_text)
            scores  = validate_report(report)
            records.append({"prompt_id": pid, "report_id": i, "report_text": report, **scores})
            print(f"overall={scores['overall_score']:.2f}")
        except Exception as exc:
            print(f"ERROR — {exc}")
        time.sleep(0.4)

df = pd.DataFrame(records)
scores_path = os.path.join(OUTPUT_DIR, "validation_scores.csv")
df.to_csv(scores_path, index=False)
print(f"\n✅  Scores saved → {scores_path}")

# ── 4. Descriptive Statistics ─────────────────────────────────────────────────

print("\n\n══════════════════════════════════════════")
print("  DESCRIPTIVE STATISTICS")
print("══════════════════════════════════════════")

DIMS = ["numeric_fidelity", "completeness", "policy_specificity",
        "scientific_hedging", "prioritization_logic", "overall_score"]

summary = df.groupby("prompt_id")[DIMS].agg(["mean", "std"]).round(3)
print(summary.to_string())

print("\nPer-prompt overall_score (mean ± SD):")
for pid in ["A", "B", "C"]:
    sub = df.query(f'prompt_id == "{pid}"')["overall_score"]
    print(f"  Prompt {pid}: {sub.mean():.2f} ± {sub.std():.2f}")

# ── 5. Statistical Analysis ───────────────────────────────────────────────────

print("\n\n══════════════════════════════════════════")
print("  STATISTICAL ANALYSIS")
print("══════════════════════════════════════════")

a = df.query('prompt_id == "A"')["overall_score"]
b = df.query('prompt_id == "B"')["overall_score"]
c = df.query('prompt_id == "C"')["overall_score"]

# Bartlett's test for homogeneity of variance
bstat, bp = bartlett(a, b, c)
var_equal  = bp >= 0.05
print(f"\nBartlett's test:  stat = {bstat:.4f},  p = {bp:.4f}")
print(f"Equal variances:  {'yes' if var_equal else 'no'}")

# T-test: Prompt A vs Prompt B (primary comparison)
print("\n── T-Test: Prompt A vs Prompt B ──")
t_res = pg.ttest(a, b, correction=not var_equal)
print(t_res[["T", "dof", "p_val", "cohen_d"]].to_string(index=False))
tp = t_res["p_val"].values[0]
better = "A" if a.mean() > b.mean() else "B"
if tp < 0.05:
    print(f"  ✅ Prompt {better} performs significantly better (p = {tp:.4f})")
else:
    print(f"  ✗  No significant difference (p = {tp:.4f})")

# One-way ANOVA / Welch ANOVA across all three prompts
print("\n── One-Way ANOVA: Prompts A, B, C ──")
if var_equal:
    anova = pg.anova(dv="overall_score", between="prompt_id", data=df)
    print("(standard ANOVA — equal variances)")
else:
    anova = pg.welch_anova(dv="overall_score", between="prompt_id", data=df)
    print("(Welch ANOVA — unequal variances)")

print(anova[["Source", "F", "p_unc", "np2"]].to_string(index=False))
fp = anova["p_unc"].values[0]
fstat = anova["F"].values[0]

if fp < 0.05:
    print(f"  ✅ Significant prompt effect  F = {fstat:.4f},  p = {fp:.4f}")
    posthoc = pg.pairwise_tukey(dv="overall_score", between="prompt_id", data=df)
    print("\n── Tukey Post-Hoc ──")
    print(posthoc.to_string(index=False))
else:
    print(f"  ✗  No significant prompt effect  F = {fstat:.4f},  p = {fp:.4f}")

# ── 6. Plots ──────────────────────────────────────────────────────────────────

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Box plot — overall score distribution
prompt_groups = [df.query(f'prompt_id == "{p}"')["overall_score"].values for p in ["A", "B", "C"]]
axes[0].boxplot(prompt_groups, labels=["Prompt A", "Prompt B", "Prompt C"], patch_artist=True,
                boxprops=dict(facecolor="#d4e6f1"), medianprops=dict(color="navy", linewidth=2))
axes[0].set_title("Overall Score by Prompt", fontsize=13, fontweight="bold")
axes[0].set_ylabel("Overall Score (0–10)")
axes[0].set_ylim(0, 10)
axes[0].grid(axis="y", linestyle="--", alpha=0.5)

# Bar chart — mean score per dimension per prompt
dim_labels = ["Numeric\nFidelity", "Completeness", "Policy\nSpecificity",
              "Scientific\nHedging", "Prioritization\nLogic"]
dim_cols   = ["numeric_fidelity", "completeness", "policy_specificity",
              "scientific_hedging", "prioritization_logic"]
dim_means  = df.groupby("prompt_id")[dim_cols].mean()

x = range(len(dim_cols))
width = 0.25
colors = ["#2e86c1", "#28b463", "#e67e22"]
for idx, (pid, color) in enumerate(zip(["A", "B", "C"], colors)):
    axes[1].bar([xi + idx * width for xi in x], dim_means.loc[pid], width,
                label=f"Prompt {pid}", color=color, alpha=0.85)
axes[1].set_xticks([xi + width for xi in x])
axes[1].set_xticklabels(dim_labels, fontsize=9)
axes[1].set_title("Mean Score by Dimension and Prompt", fontsize=13, fontweight="bold")
axes[1].set_ylabel("Mean Score (0–10)")
axes[1].set_ylim(0, 10)
axes[1].legend(title="Prompt")
axes[1].grid(axis="y", linestyle="--", alpha=0.5)

plt.suptitle("PM10 Report Validation — Prompt Comparison", fontsize=14, fontweight="bold", y=1.01)
plt.tight_layout()
plot_path = os.path.join(OUTPUT_DIR, "score_comparison.png")
plt.savefig(plot_path, dpi=150, bbox_inches="tight")
print(f"\n✅  Plot saved → {plot_path}")

print("\n✅  Validation experiment complete.")
