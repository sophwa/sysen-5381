![Banner Image](../docs/images/icons.png)

# README `08_function_calling`

> Learn how to use function calling with LLMs to enable agents to interact with external tools and APIs. Build multi-agent systems where agents can call functions to fetch data, perform calculations, and process information.

---

## Table of Contents

- [README `08_function_calling`](#readme-08_function_calling)
  - [Table of Contents](#table-of-contents)
  - [Activities](#activities)
  - [Readings](#readings)

---

## Activities

Complete these activities in order:

1. [ACTIVITY: Function Calling Basics](ACTIVITY_function_calling.md)
   - [`02_function_calling.py`](02_function_calling.py) — Basic function calling (Python)
   - [`02_function_calling.R`](02_function_calling.R) — Basic function calling (R)
2. [ACTIVITY: Agents with Tools](ACTIVITY_agents_with_tools.md)
   - [`03_agents_with_function_calling.py`](03_agents_with_function_calling.py) — Agents with tools (Python)
   - [`03_agents_with_function_calling.R`](03_agents_with_function_calling.R) — Agents with tools (R)
   - [`functions.py`](functions.py) — Helper functions (Python)
   - [`functions.R`](functions.R) — Helper functions (R)
3. [LAB: Multi-Agent System with Tools](LAB_multi_agent_with_tools.md)
   - [`04_multiple_agents_with_function_calling.py`](04_multiple_agents_with_function_calling.py) — Multi-agent workflow (Python)
   - [`04_multiple_agents_with_function_calling.R`](04_multiple_agents_with_function_calling.R) — Multi-agent workflow (R)
4. [ACTIVITY: Build and Deploy an MCP Server](ACTIVITY_mcp_server.md)
   - [`mcp_plumber/`](mcp_plumber/) — MCP over HTTP with **Plumber** (R); see [mcp_plumber/README.md](mcp_plumber/README.md)
   - [`mcp_fastapi/`](mcp_fastapi/) — same protocol with **FastAPI** (Python); see [mcp_fastapi/README.md](mcp_fastapi/README.md)

---

## Readings

- None.

---

## Student Documentation (sophwa)

### System Overview

This is an earthquake intelligence and preparedness system built across three labs. Each lab adds a new capability on top of the last — Lab 1 handles multi-agent triage of live seismic data, Lab 2 adds a retrieval layer over a preparedness reference document, and Lab 3 wires in a real-time tool call to the USGS API. Together they form a pipeline that can fetch, classify, and communicate earthquake hazard information.

---

### System Architecture

Three pipelines, all using the same `agent_run()` helper in `functions.py`:

**Lab 1 — Earthquake risk triage (`06_agents/LAB_prompt_design.py`)**
- Fetches live USGS earthquake data (mag ≥ 5.0, last 7 days) directly in Python
- Agent 1 (Data Analyst): receives raw table → outputs clean 4-column markdown table
- Agent 2 (Risk Assessor): receives Agent 1 table → classifies each event as HIGH / MODERATE / LOW based on magnitude
- Agent 3 (Emergency Advisor): receives risk table → writes a numbered emergency response checklist

**Lab 2 — Earthquake preparedness RAG (`07_rag/earthquake_rag.py`)**
- Single agent: searches `earthquake_preparedness.txt` for relevant paragraphs → responds as an emergency management advisor

**Lab 3 — Live tool calling (`08_function_calling/LAB_multi_agent_with_tools.py`)**
- Agent 1 (Data Fetcher): calls `get_earthquakes()` tool against the USGS API → returns a live DataFrame
- Agent 2 (Report Writer): receives that DataFrame → writes a plain-English newsletter briefing

---

### RAG Data Source

**File:** `07_rag/data/earthquake_preparedness.txt`

A reference document covering earthquake hazard and preparedness — includes the magnitude/intensity scale, US seismic hazard zones, building codes and retrofitting, individual and community preparedness, post-earthquake damage assessment, tsunami hazards, early warning systems, and economic impacts. The `search_text()` function splits the document on double newlines into paragraphs and returns any that contain the query term (case-insensitive). Results are passed to the LLM as a JSON dict with keys: `query`, `document`, `matching_content`, and `num_matches`.

---

### Tool Functions

| Tool | Purpose | Parameters | Returns |
|---|---|---|---|
| `get_earthquakes` | Fetch recent USGS earthquake events | `min_magnitude` (float), `days_back` (int) | DataFrame: magnitude, place, time, depth_km |
| `search_text` | Keyword search over a text file (RAG retrieval) | `query` (str), `document_path` (str) | Dict: query, document, matching_content, num_matches |

---

### Technical Details

| Item | Detail |
|---|---|
| Model | `smollm2:1.7b` (local via Ollama, port 11434) |
| Python packages | `requests`, `pandas`, `json`, `ast`, `tabulate` |
| External APIs | USGS Earthquake Hazards API (earthquake.usgs.gov) — free, no key needed |
| Key helper | `functions.py` — `func_map` param added to `agent_run()` to resolve caller-defined tool functions |
| RAG data | `07_rag/data/earthquake_preparedness.txt` — plain text, paragraph-delimited |

---

### Usage

Prerequisites:
```bash
ollama pull smollm2:1.7b
pip install requests pandas tabulate
```

Run each script from its own folder:
```bash
# Lab 1 — multi-agent earthquake triage
cd 06_agents && python3 LAB_prompt_design.py

# Lab 2 — earthquake preparedness RAG
cd 07_rag && python3 earthquake_rag.py

# Lab 3 — live tool calling + newsletter
cd 08_function_calling && python3 LAB_multi_agent_with_tools.py
```

No API keys needed — the USGS API is open and free.

---

![Footer Image](../docs/images/icons.png)

---

← 🏠 [Back to Top](#Table-of-Contents)
