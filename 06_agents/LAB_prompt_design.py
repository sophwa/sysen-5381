# LAB_prompt_design.py
# Design Effective Prompts for Multi-Agent Systems
# SYSEN 5381 Lab - Multi-Agent Orchestration

# Workflow: Neurology Drug Shortage Triage & Procurement Advisory
#
#   [FDA API: Neurology] --> raw DataFrame
#         |
#   [Agent 1: Data Analyst]    --> filtered markdown table of shortages
#         |
#   [Agent 2: Risk Assessor]   --> risk-classified table (CRITICAL / MODERATE / WATCH)
#         |
#   [Agent 3: Procurement Advisor] --> numbered action checklist for hospital supply teams

# 0. SETUP ###################################

from functions import agent_run, get_shortages, df_as_text
import os
import sys
import pandas as pd

# Set working directory so relative imports work
os.chdir(os.path.dirname(os.path.abspath(__file__)))


MODEL = "smollm2:1.7b"   # Iteration 2: upgraded from 135m — better instruction following

# 1. FETCH RAW DATA (function, not an agent) ###################################

# Category chosen: Neurology — different from existing examples (Psychiatry, Oncology)
category = "Neurology"
print(f"Fetching FDA drug shortage data for category: {category}...\n")

data = get_shortages(category=category, limit=200)

# Keep only the most recent record per drug to avoid duplicates
if data.empty:
    print("No data returned from FDA API. Exiting.")
    sys.exit(1)

stat = (
    data
    .groupby("generic_name", group_keys=False)
    .apply(lambda x: x.loc[x["update_date"].idxmax()])
    .reset_index(drop=True)
)

# Iteration 2: pre-slim to 3 columns in Python before feeding to Agent 1.
# This reduces noise in the input — small models struggle when given wide tables
# with irrelevant columns (update_type, related_info).
slim = (
    stat[["generic_name", "availability", "update_date"]]
    .rename(columns={"generic_name": "drug_name", "update_date": "last_updated"})
    .sort_values("last_updated", ascending=False)
    .head(15)
)
raw_text = df_as_text(slim)
print(f"Fetched {len(stat)} unique drug shortage records.\n")

# 2. AGENT 1 — DATA ANALYST ###################################
# Role:   Receive raw FDA shortage table; return a clean filtered markdown table.
# Input:  raw_text  (markdown table from FDA API)
# Output: analysis  (filtered markdown table, sorted by date, max 15 rows)
#
# Prompt design choice:
#   - Specify exact output columns so Agent 2 can parse reliably.
#   - Cap at 15 rows to keep the context manageable for small models.
#   - Sort descending by date so the most urgent items appear first.

# Iteration 2: lead with "Return ONLY" (imperative) rather than a persona statement.
# Small models are more likely to follow a direct command than to stay in character.
# Iteration 3: added "copy values exactly" — model was hallucinating availability
# values in iteration 2.  Also added "include every row" to prevent row dropping.
role1 = (
    "Return ONLY a markdown table. Do not write any other text before or after the table. "
    "The table must have exactly three columns: drug_name | availability | last_updated. "
    "Copy every value exactly as it appears in the user's table — do not change, infer, or omit any values. "
    "Include every row from the user's table. Sort rows by last_updated descending."
)

print("Running Agent 1 (Data Analyst)...")
analysis = agent_run(role=role1, task=raw_text, model=MODEL, output="text")

print("\n--- Agent 1 Output (Filtered Shortage Table) ---")
print(analysis)

# 3. AGENT 2 — RISK ASSESSOR ###################################
# Role:   Receive Agent 1's filtered table; classify each drug by risk level.
# Input:  analysis  (output from Agent 1)
# Output: risk_table  (markdown table with added risk_level column)
#
# Prompt design choice:
#   - Define explicit classification criteria so the agent is deterministic:
#       CRITICAL  = unavailable
#       MODERATE  = limited supply / limited availability
#       WATCH     = anything else currently active
#   - Require the same markdown table format so Agent 3 can parse it cleanly.

# Iteration 2: explicit keyword matching moved to rules block; clarified that
# "Limited Availability" → MODERATE (not CRITICAL).  Added example row so the
# model can see exactly what each classification looks like.
# Iteration 3: added second example row for WATCH and a third for CRITICAL to
# make the three classes unambiguous.  Also reinforced "include ALL rows".
role2 = (
    "Return ONLY a markdown table. Do not write any other text before or after the table. "
    "The table must have exactly four columns: drug_name | availability | last_updated | risk_level. "
    "Copy drug_name, availability, and last_updated exactly from the user's table. "
    "Include ALL rows — do not drop any. "
    "Assign risk_level using ONLY these rules:\n"
    "  - CRITICAL : availability is exactly 'Unavailable'\n"
    "  - MODERATE : availability contains the word 'Limited'\n"
    "  - WATCH    : availability is 'Available' or any other status\n"
    "Example rows:\n"
    "  | Midazolam Injection | Unavailable | 2026-03-13 | CRITICAL |\n"
    "  | Lorazepam Injection | Limited Availability | 2026-03-13 | MODERATE |\n"
    "  | Atropine Sulfate Injection | Available | 2026-03-13 | WATCH |\n"
    "Sort so CRITICAL rows appear first, then MODERATE, then WATCH."
)

print("\nRunning Agent 2 (Risk Assessor)...")
risk_table = agent_run(role=role2, task=analysis, model=MODEL, output="text")

print("\n--- Agent 2 Output (Risk-Classified Table) ---")
print(risk_table)

# 4. AGENT 3 — PROCUREMENT ADVISOR ###################################
# Role:   Receive Agent 2's risk table; write an action checklist.
# Input:  risk_table  (output from Agent 2)
# Output: checklist   (numbered action list for procurement teams)
#
# Prompt design choice:
#   - Request numbered list (not prose) so items are scannable.
#   - Group by risk level so the reader can triage immediately.
#   - Cap at 10 items to keep the output focused and actionable.
#   - Specify audience (hospital procurement) to set the right tone.

# Iteration 2: simplified ask — one bullet per drug, no grouping headers.
# Grouping by risk level inside the checklist was too complex for the small model
# to maintain while also formatting correctly.  Instead, sort is already done by
# Agent 2, so the output order implicitly groups CRITICAL first.
role3 = (
    "Return ONLY a numbered list. Do not write any other text before or after the list. "
    "For each drug in the table provided by the user, write one line in this exact format:\n"
    "  N. **drug_name** (risk_level): one concrete procurement action.\n"
    "Example: 1. **Lorazepam Injection** (MODERATE): Contact alternate wholesalers and place a 30-day buffer order.\n"
    "Include at most 10 items. List CRITICAL items first, then MODERATE, then WATCH."
)

print("\nRunning Agent 3 (Procurement Advisor)...")
checklist = agent_run(role=role3, task=risk_table, model=MODEL, output="text")

print("\n--- Agent 3 Output (Procurement Action Checklist) ---")
print(checklist)

# 5. FULL WORKFLOW SUMMARY ###################################

print("\n" + "="*60)
print("FULL WORKFLOW SUMMARY")
print("="*60)
print(f"\nCategory:       {category}")
print(f"Records fetched: {len(stat)}")
print("\n[Agent 1] Filtered shortage table:")
print(analysis)
print("\n[Agent 2] Risk-classified table:")
print(risk_table)
print("\n[Agent 3] Procurement action checklist:")
print(checklist)

# 6. PROMPT DESIGN DOCUMENTATION ###################################
#
# Agent roles and workflow:
#   Agent 1 (Data Analyst): Receives a pre-slimmed 3-column DataFrame (drug_name,
#     availability, last_updated) and returns a sorted markdown table.
#     Pre-slimming in Python (not the agent) reduces noise in the model's context.
#
#   Agent 2 (Risk Assessor): Receives Agent 1's table and adds a risk_level column
#     using explicit keyword rules (Unavailable → CRITICAL, Limited → MODERATE,
#     else WATCH).  An example row in the prompt anchors the expected format.
#
#   Agent 3 (Procurement Advisor): Converts the risk table into a numbered action
#     checklist, one line per drug with a concrete recommendation.
#
# What worked well (across iterations):
#   - Pre-filtering the DataFrame to only 3 columns before Agent 1 removed
#     irrelevant context that confused the small model.
#   - Leading prompts with "Return ONLY a markdown table / numbered list" (direct
#     imperative) was more effective than persona framing ("I am a ...").
#   - Providing an example row in Agent 2's prompt anchored the exact format.
#   - Upgrading from smollm2:135m to smollm2:1.7b significantly improved format
#     compliance and classification accuracy.
#
# What was iterated:
#   Iteration 1 → 2:
#     - Model (135m → 1.7b): small model couldn't follow multi-constraint prompts.
#     - Agent 1 prompt: changed from persona + "no commentary" to "Return ONLY"
#       imperative opener; model was adding preamble like "Sure, I can help!".
#     - Data pre-processing: added Python step to slim DataFrame before Agent 1
#       so the model sees only the 3 relevant columns (not all 5).
#     - Agent 2 prompt: clarified "Limited Availability" → MODERATE with an
#       example row; original prompt caused model to mark all drugs CRITICAL.
#     - Agent 3 prompt: dropped "grouped by risk level" section headers
#       (too complex for small model); relied on Agent 2's sort order instead.
#   Iteration 2 → 3:
#     - Agent 1: added "copy every value exactly" and "include every row" —
#       model was still hallucinating some availability values and dropping rows.
#     - Agent 2: added three concrete example rows (CRITICAL, MODERATE, WATCH)
#       so each class is unambiguously anchored; also added "include ALL rows".
#     - Result: All 8 drugs now present in both tables; classification is
#       largely correct (one edge case remains: Dexamethasone "Unavailable"
#       classified as WATCH — model's attention limits on long example prompts).
#   Remaining limitation:
#     - smollm2:1.7b occasionally misclassifies one row when context is long.
#     - For production use, a larger model (e.g., llama3.2) or a post-processing
#       Python step to enforce the classification rules would eliminate this.
