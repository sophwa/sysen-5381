# Homework 3: AI Report Validation System

**SYSEN 5381 | Sophie Wang | May 2026**

---

## Overview

This project implements a custom AI-powered validation system for PM10 traffic-emissions policy reports. It compares three generation prompts (A, B, C) by running each 31 times, validating every report with a domain-specific rubric, and using ANOVA and t-tests to determine which prompt produces significantly better output.

---

## File Structure

```
11_decision_support/
├── validate_reports.py       # Main script: generates reports, validates, runs statistics
├── build_homework3.js        # Builds the .docx submission file
├── HOMEWORK3_Wang.docx       # Submission deliverable
├── HOMEWORK3_README.md       # This file
└── data/
    ├── validation_scores.csv      # Raw scores for all 93 reports (31 per prompt)
    ├── score_comparison.png       # Boxplot + dimension bar chart
    ├── ss1_system_in_action.png   # Screenshot: script running
    ├── ss2_one_report_result.png  # Screenshot: one report + validator JSON
    ├── ss3_rubric_table.png       # Screenshot: validation criteria table
    ├── ss4_statistical_results.png # Screenshot: t-test & ANOVA output
    └── ss5_score_comparison.png   # Screenshot: boxplot + summary stats
```

---

## Setup

**Requirements:** Ollama running locally with `llama3.2:latest` pulled.

```bash
# 1. Install Ollama (https://ollama.com) and pull the model
ollama pull llama3.2:latest

# 2. Install Python dependencies
pip install requests pandas scipy pingouin matplotlib python-dotenv

# 3. Run the full experiment from the repo root
python3 11_decision_support/validate_reports.py
```

No API key required — everything runs against local Ollama.

---

## Validation Criteria

The validator uses five domain-specific dimensions on a **0–10 scale**, plus a boolean gate. These differ from the Module 9 LAB's generic 1–5 Likert scales (accuracy, formality, faithfulness, clarity, succinctness, relevance) in that each dimension targets a specific failure mode for PM10 policy reporting.

| Dimension | Scale | Description | 10 = … | 0 = … |
|---|---|---|---|---|
| `numeric_fidelity` | 0–10 | Cited percentages/counts match source data exactly | All exact | Wrong or invented |
| `completeness` | 0–10 | All five vehicle categories addressed with data | All 5 covered | None mentioned |
| `policy_specificity` | 0–10 | Recommendations name a mechanism and target vehicle type | ≥2 targeted actions | No recommendations |
| `scientific_hedging` | 0–10 | Epistemic tone is appropriate — no overstatement or alarm | Appropriately hedged | Alarmist or certain |
| `prioritization_logic` | 0–10 | Vehicle prioritization explicitly grounded in data | Data-cited logic | Arbitrary or none |
| `data_accurate` | bool | Hard gate: zero fabricated statistics | `true` | `false` → flagged |

`overall_score` is the mean of the five numeric dimensions.

---

## Prompts Compared

**Prompt A — Comprehensive/Formal**
> You are an environmental policy analyst authoring a formal technical report. Using the provided PM10 emissions data, write a precise 4–5 sentence paragraph that: (1) names every vehicle category and cites its exact share from the data, (2) explicitly justifies why certain categories are prioritized for intervention, (3) proposes at least two targeted, mechanism-specific policy actions. Use formal government-report language. Do not add or invent statistics.

**Prompt B — Concise/Technical**
> Summarize the PM10 emissions data in 2–3 concise, technically accurate sentences. Include the most important percentages and conclude with one specific policy recommendation.

**Prompt C — Open-Ended**
> Write a short paragraph about the PM10 emissions situation. Mention the vehicle types and suggest what could be done about it.

---

## Results

### Descriptive Statistics

| Prompt | n | Mean | SD | Min | Max |
|--------|---|------|----|-----|-----|
| A | 31 | 7.34 | 0.73 | 5.80 | 8.80 |
| B | 31 | 6.95 | 0.62 | 6.00 | 8.00 |
| C | 31 | 6.76 | 0.95 | 3.60 | 8.20 |

### Statistical Tests

| Test | Statistic | df | p-value | Effect Size |
|------|-----------|-----|---------|-------------|
| Bartlett's (equal variance check) | stat = 5.57 | — | 0.062 | — |
| One-way ANOVA | F = 4.59 | 2, 90 | **0.013** | η² = 0.092 |
| T-test: A vs B | T = 2.25 | 60 | **0.028** | d = 0.572 |
| T-test: A vs C | T = 2.73 | 60 | **0.008** | d = 0.695 |
| Tukey: A vs C | — | — | **0.010** | g = 0.686 |
| Tukey: A vs B | — | — | 0.127 | g = 0.565 |

**Conclusion:** Prompt A significantly outperforms Prompt C (Tukey p = 0.010, medium-large effect). The ANOVA is significant at p = 0.013. The largest gaps are on `policy_specificity` (5.73 vs 4.27) and `prioritization_logic` (5.40 vs 4.33), confirming that open-ended prompts fail most on actionability and data-grounding.

---

## How It Works

```
Source Data (PM10 table)
        │
        ├──► Generator (llama3.2, temp=0.8)
        │         Prompt A / B / C
        │         → report paragraph
        │
        └──► Validator (llama3.2, temp=0.2, JSON mode)
                  Rubric system prompt + report
                  → JSON scores
                  → overall_score = mean of 5 dimensions
```

The validator only receives the report text and the source data — not the generation prompt — so it cannot inadvertently reward prompt complexity.

---

## Reproducing the Statistical Output

```bash
python3 - << 'EOF'
import pandas as pd, pingouin as pg
from scipy.stats import bartlett

df = pd.read_csv("11_decision_support/data/validation_scores.csv")
a = df.query('prompt_id == "A"')["overall_score"]
b = df.query('prompt_id == "B"')["overall_score"]
c = df.query('prompt_id == "C"')["overall_score"]

print(df.groupby("prompt_id")["overall_score"].agg(["mean","std","count"]).round(3))

bstat, bp = bartlett(a, b, c)
print(f"\nBartlett: stat={bstat:.4f}, p={bp:.4f}")

print("\nANOVA:")
print(pg.anova(dv="overall_score", between="prompt_id", data=df)[["Source","F","p_unc","np2"]])

print("\nTukey post-hoc:")
print(pg.pairwise_tukey(dv="overall_score", between="prompt_id", data=df))
EOF
```
