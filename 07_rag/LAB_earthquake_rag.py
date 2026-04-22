# LAB_earthquake_rag.py
# RAG Workflow over Earthquake Preparedness Document
# Sophie Wang

# Retrieval layer over a local earthquake preparedness knowledge base.
# Answers questions by pulling relevant paragraphs rather than relying
# on the model's built-in knowledge alone.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import os       # for file path operations
import json     # for working with JSON
import sys      # for path handling

# If you haven't already, install these packages...
# pip install requests

## 0.2 Working Directory #################################

os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

## 0.3 Load Functions #################################

from functions import agent_run

## 0.4 Configuration #################################

MODEL    = "smollm2:1.7b"
PORT     = 11434
DOCUMENT = "data/earthquake_preparedness.txt"

# 1. SEARCH FUNCTION ###################################

def search_text(query, document_path):
    """
    Search an earthquake preparedness text file for paragraphs
    containing the query string (case-insensitive).

    Parameters:
    -----------
    query : str
        The search term to look for
    document_path : str
        Path to the text file to search

    Returns:
    --------
    dict
        Dictionary with query, document name, matching content, and paragraph count
    """

    with open(document_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split into paragraphs on blank lines
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

    # Case-insensitive substring search
    matching = [p for p in paragraphs if query.lower() in p.lower()]

    return {
        "query":            query,
        "document":         os.path.basename(document_path),
        "matching_content": "\n\n".join(matching),
        "num_paragraphs":   len(matching),
    }

# 2. TEST SEARCH FUNCTION ###################################

print("Testing search function...")
test_result = search_text("building damage retrofit", DOCUMENT)
print(f"Retrieved {test_result['num_paragraphs']} matching paragraphs for 'building damage retrofit'")

# 3. RAG WORKFLOW ###################################

# Topic to query
input_data = {"topic": "earthquake preparedness"}

# Task 1: Retrieve relevant paragraphs from the knowledge base
result1     = search_text(input_data["topic"], DOCUMENT)
result1_json = json.dumps(result1, indent=2)

# Task 2: Augment the LLM with retrieved context
role = (
    "You are an earthquake preparedness analyst. "
    "Based on the retrieved content below, provide a detailed analysis with key findings. "
    "Format your response as:\n\n"
    "## Earthquake Preparedness Analysis: Key Findings\n"
    "[3-4 paragraphs summarising key findings]\n\n"
    "## Implications for Building Owners\n"
    "[numbered list]\n\n"
    "## Implications for Emergency Managers and Local Governments\n"
    "[numbered list]\n\n"
    "## Conclusion\n"
    "[1 paragraph]"
)

result2 = agent_run(role=role, task=result1_json, model=MODEL, output="text")

# 4. VIEW RESULTS ###################################

print("\n" + result2)
