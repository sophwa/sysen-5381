# 05_multi_agent_chain.py
# Simple 2-Agent Chain Workflow
# Tim Fraser

# This script demonstrates a minimal 2-agent chain.
# Each agent's output becomes the next agent's input.
#
# Workflow:
#   [FDA API] --> raw data
#       |
#   [Agent 1: Summarizer]  --> bullet-point summary
#       |
#   [Agent 2: Report Writer] --> formatted markdown report

# 0. SETUP ###################################

import os
import pandas as pd
from functions import agent_run, get_shortages, df_as_text

# Set working directory to this script's folder (update path as needed)
# os.chdir("/path/to/06_agents")

# Select a model available in your local Ollama install
MODEL = "smollm2:135m"

# 1. FETCH RAW DATA (function, not an agent) ###################################

# Use a category with reliable current shortage data
category = "Oncology"
data = get_shortages(category=category, limit=100)

# Keep only the most recent record per drug to avoid duplicates
stat = (
    data
    .groupby("generic_name", group_keys=False)
    .apply(lambda x: x.loc[x["update_date"].idxmax()])
    .reset_index(drop=True)
)

# Convert the dataframe to a plain-text markdown table for Agent 1
raw_text = df_as_text(stat)

print(f"Fetched {len(stat)} drug shortage records for category: {category}\n")

# 2. AGENT 1 — SUMMARIZER ###################################
# Role:  Read the raw data table and produce a concise bullet-point summary.
# Input: raw_text  (markdown table from FDA API)
# Output: summary  (bullet-point text)

role1 = (
    "I am a data analyst specializing in pharmaceutical supply chains. "
    "I read a markdown table of FDA drug shortage records and produce a concise "
    "bullet-point summary that lists each drug name and its current availability status. "
    "I keep my summary short and factual."
)

print("Running Agent 1 (Summarizer)...")
summary = agent_run(role=role1, task=raw_text, model=MODEL, output="text")

print("\n--- Agent 1 Output (Bullet-Point Summary) ---")
print(summary)

# 3. AGENT 2 — REPORT WRITER ###################################
# Role:  Take the bullet-point summary and write a structured markdown report.
# Input: summary  (output from Agent 1)
# Output: report  (formatted markdown report)

role2 = (
    "I am a healthcare communications specialist. "
    "I receive a bullet-point summary of current drug shortages and write a "
    "structured, professional markdown report for hospital administrators. "
    "My report includes: a brief headline, a section listing the affected drugs, "
    "and a short recommended action for procurement teams."
)

print("\nRunning Agent 2 (Report Writer)...")
report = agent_run(role=role2, task=summary, model=MODEL, output="text")

print("\n--- Agent 2 Output (Formatted Report) ---")
print(report)

# 4. HOW THE CHAIN WORKS ###################################
#
# The key to a multi-agent chain is simply passing one agent's return value
# as the 'task' argument of the next agent_run() call:
#
#   summary = agent_run(role=role1, task=raw_text,  ...)   # Agent 1
#   report  = agent_run(role=role2, task=summary,   ...)   # Agent 2
#                                        ^^^^^^^
#                                 Agent 1's output becomes
#                                 Agent 2's input
