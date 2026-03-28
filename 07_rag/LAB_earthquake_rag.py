# earthquake_rag.py
# Custom RAG Workflow: Earthquake Preparedness Advisor
# Based on 02_txt.py template

# This script demonstrates a RAG workflow using a text file of earthquake
# preparedness and hazard reference content. It retrieves relevant paragraphs
# based on a search query and passes them to an LLM to generate an
# emergency-management-focused explanation.

# 0. SETUP ###################################

## 0.1 Load Packages
import os
import runpy
import requests
import json

## 0.2 Working Directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

## 0.3 Start Ollama Server (source 01_ollama.py)
ollama_script_path = os.path.join(os.getcwd(), "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.4 Load Functions
from functions import agent_run

## 0.5 Configuration
MODEL    = "smollm2:1.7b"
PORT     = 11434
DOCUMENT = "data/earthquake_preparedness.txt"

# 1. SEARCH FUNCTION ###################################

def search_text(query, document_path):
    """
    Search a text file for paragraphs containing the query term.

    The document is split into paragraphs (separated by blank lines).
    Any paragraph containing the query (case-insensitive) is returned.

    Parameters
    ----------
    query : str
        The search term to look for
    document_path : str
        Path to the text file to search

    Returns
    -------
    dict
        Dictionary with query, document name, matching content, and match count
    """
    with open(document_path, 'r', encoding='utf-8') as f:
        text_content = f.read()

    # Split into paragraphs by double newlines, dropping empty chunks
    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]

    # Find paragraphs containing the query (case-insensitive)
    matching_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]

    result_text = "\n\n".join(matching_paragraphs)

    return {
        "query":            query,
        "document":         os.path.basename(document_path),
        "matching_content": result_text,
        "num_matches":      len(matching_paragraphs)
    }

# 2. TEST SEARCH FUNCTION ###################################

print("Testing search function...")
test_result = search_text("magnitude", DOCUMENT)
print(f"Found {test_result['num_matches']} matching paragraphs for 'magnitude'")

# 3. RAG WORKFLOW ###################################

# Query topic: building safety and structural damage after a major earthquake
input_data = {"topic": "building damage retrofit"}

# Task 1: Retrieve relevant paragraphs from the earthquake preparedness document
result1 = search_text(input_data["topic"], DOCUMENT)

# Convert results to JSON to pass to the LLM
result1_json = json.dumps(result1, indent=2)

print(f"\nRetrieved {result1['num_matches']} matching paragraphs for '{input_data['topic']}'")

# Task 2: Generate an emergency-management-focused explanation from retrieved content
role = (
    "You are an emergency management advisor specializing in seismic hazard. "
    "Given retrieved reference content about earthquake preparedness and structural safety, "
    "explain the key findings and their implications clearly and concisely. "
    "Focus on what the information means for building owners, emergency managers, and local governments. "
    "Format your response as markdown with a title and well-structured paragraphs. "
    "If the retrieved content is incomplete or does not fully address the query, note that."
)

result2 = agent_run(
    role=role,
    task=result1_json,
    model=MODEL,
    output="text"
)

print("\n📝 Earthquake Preparedness Analysis:")
print(result2)
