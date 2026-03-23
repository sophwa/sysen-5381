# LAB_energy_burden_rag.py
# Custom RAG Workflow: Energy Burden Mapper
# Based on 02_txt.py template

# This script demonstrates a RAG workflow using a text file of energy burden
# reference content. It retrieves relevant paragraphs based on a search query
# and passes them to an LLM to generate a policy-focused explanation.

# 0. SETUP ###################################

## 0.1 Load Packages
import os
import runpy
import requests
import json

## 0.2 Working Directory
script_dir = os.path.dirname(os.path.abspath(__name__))
os.chdir(script_dir)

## 0.3 Start Ollama Server (source 01_ollama.py)
ollama_script_path = os.path.join(os.getcwd(), "01_ollama.py")
_ = runpy.run_path(ollama_script_path)

## 0.4 Load Functions
from functions import agent_run

## 0.5 Configuration
MODEL = "smollm2:1.7b"           # small local model via Ollama
PORT = 11434                      # default Ollama port
OLLAMA_HOST = f"http://localhost:{PORT}"
DOCUMENT = "data/energy_burden.txt"  # energy burden reference text file

# 1. SEARCH FUNCTION ###################################

def search_text(query, document_path):
    """
    Search a text file for paragraphs containing the query term.

    The document is split into paragraphs (separated by blank lines).
    Any paragraph containing the query (case-insensitive) is returned.

    Parameters:
    -----------
    query : str
        The search term to look for
    document_path : str
        Path to the text file to search

    Returns:
    --------
    dict
        Dictionary with query, document name, matching content, and match count
    """

    # Read the text file
    with open(document_path, 'r', encoding='utf-8') as f:
        text_content = f.read()

    # Split into paragraphs by double newlines, dropping empty chunks
    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]

    # Find paragraphs containing the query (case-insensitive)
    matching_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]

    # Combine matching paragraphs into a single text block
    result_text = "\n\n".join(matching_paragraphs)

    # Return as a dictionary (easily converted to JSON for the LLM)
    result = {
        "query": query,
        "document": os.path.basename(document_path),
        "matching_content": result_text,
        "num_matches": len(matching_paragraphs)
    }

    return result

# 2. TEST SEARCH FUNCTION ###################################

print("Testing search function...")
test_result = search_text("weatherization", DOCUMENT)
print(f"Found {test_result['num_matches']} matching paragraphs")
print(test_result)

# 3. RAG WORKFLOW ###################################

# Query topic: renter households facing high energy burden
input_data = {"topic": "renter burden high energy"}

# Task 1: Retrieve relevant paragraphs from the energy burden reference document
result1 = search_text(input_data["topic"], DOCUMENT)

# Convert results to JSON to pass to the LLM
result1_json = json.dumps(result1, indent=2)

# Task 2: Generate a policy-focused explanation from the retrieved content
role = (
    "You are an energy policy analyst assistant supporting the Energy Burden Mapper tool. "
    "Given retrieved reference content about energy burden, explain the key patterns "
    "and policy implications clearly and concisely. Focus on what the findings mean for "
    "low-income renters, older housing stock, and eligibility for programs like WAP and LIHEAP. "
    "Format your response as markdown with a title and well-structured paragraphs. "
    "If the retrieved content is incomplete or does not fully address the query, note that."
)

result2 = agent_run(
    role=role,
    task=result1_json,
    model=MODEL,
    output="text"
)

print("\n📝 Energy Burden Policy Analysis:")
print(result2)
