# Homework 2: AI Agent System with RAG and Tools
**SYSEN 5381 | sophwa**

---

## Table of Contents
- [System Overview](#system-overview)
- [Repository Links](#repository-links)
- [System Architecture](#system-architecture)
- [RAG Data Source](#rag-data-source)
- [Tool Functions](#tool-functions)
- [Technical Details](#technical-details)
- [Usage Instructions](#usage-instructions)

---

## System Overview

This is an earthquake intelligence and preparedness system built across three labs. Each lab adds a new capability on top of the last — Lab 1 handles multi-agent triage of live seismic data, Lab 2 adds a retrieval layer over a preparedness reference document, and Lab 3 wires in a real-time tool call to the USGS API. Together they form a pipeline that can fetch, classify, and communicate earthquake hazard information.

---

## Repository Links

| File | Description |
|---|---|
| [`06_agents/LAB_prompt_design.py`](../06_agents/LAB_prompt_design.py) | Multi-agent earthquake risk triage |
| [`07_rag/LAB_earthquake_rag.py`](../07_rag/LAB_earthquake_rag.py) | Earthquake preparedness RAG query |
| [`08_function_calling/LAB_multi_agent_with_tools.py`](LAB_multi_agent_with_tools.py) | Live tool calling + newsletter agent |
| [`08_function_calling/functions.py`](functions.py) | Shared agent helper functions |

---

## System Architecture

All three labs use the same `agent_run()` helper from `functions.py` and work on the same domain — earthquake data and preparedness.

**Lab 1 — Multi-agent triage (`06_agents/LAB_prompt_design.py`)**
- Pulls USGS earthquake data (mag ≥ 5.0, last 7 days) directly in Python
- Agent 1 (Data Analyst): receives raw data → outputs a clean 4-column markdown table
- Agent 2 (Risk Assessor): receives Agent 1 table → classifies each event HIGH / MODERATE / LOW by magnitude
- Agent 3 (Emergency Advisor): receives risk table → writes a numbered response checklist

**Lab 2 — Preparedness RAG (`07_rag/LAB_earthquake_rag.py`)**
- Single agent: keyword-searches `earthquake_preparedness.txt` → responds as an emergency management advisor using only retrieved context

**Lab 3 — Live tool calling (`08_function_calling/LAB_multi_agent_with_tools.py`)**
- Agent 1 (Data Fetcher): calls `get_earthquakes()` against the USGS API → returns a live DataFrame
- Agent 2 (Report Writer): receives the DataFrame → writes a plain-English newsletter briefing

---

## RAG Data Source

**File:** `07_rag/data/earthquake_preparedness.txt`

A reference document covering earthquake hazard and preparedness — includes the magnitude/intensity scale, US seismic hazard zones, building codes and retrofitting, individual and community preparedness, post-earthquake damage assessment, tsunami hazards, early warning systems, and economic impacts. The `search_text()` function splits it on double newlines into paragraphs and returns any that contain the query term (case-insensitive). Results are passed to the LLM as a JSON dict with keys: `query`, `document`, `matching_content`, and `num_matches`.

---

## Tool Functions

| Tool | Purpose | Parameters | Returns |
|---|---|---|---|
| `get_earthquakes` | Fetch recent USGS earthquake events | `min_magnitude` (float), `days_back` (int) | DataFrame: magnitude, place, time, depth_km |
| `search_text` | Keyword search over a text file (RAG retrieval) | `query` (str), `document_path` (str) | Dict: query, document, matching_content, num_matches |

---

## Technical Details

| Item | Detail |
|---|---|
| Model | `smollm2:1.7b` (local via Ollama, port 11434) |
| Python packages | `requests`, `pandas`, `json`, `ast`, `tabulate` |
| External API | USGS Earthquake Hazards API (earthquake.usgs.gov) — free, no key needed |
| Key fix | `func_map` param added to `agent_run()` in `functions.py` so caller-defined tools resolve correctly |
| RAG data | `07_rag/data/earthquake_preparedness.txt` — plain text, paragraph-delimited |

---

## Usage Instructions

Prerequisites:
```bash
ollama pull smollm2:1.7b
pip install requests pandas tabulate
```

Run from the repo root:
```bash
# Lab 1 — multi-agent earthquake triage
cd 06_agents && python3 LAB_prompt_design.py

# Lab 2 — earthquake preparedness RAG
cd 07_rag && python3 LAB_earthquake_rag.py

# Lab 3 — live tool calling + newsletter
cd 08_function_calling && python3 LAB_multi_agent_with_tools.py
```

No API keys needed — the USGS API is open and free.
