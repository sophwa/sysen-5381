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

### System Architecture

Three pipelines, all using the same `agent_run()` helper in `functions.py`:

**Lab 1 — Multi-agent triage (`LAB_prompt_design.py`)**
- Agent 1 (Data Analyst): takes raw FDA shortage data → outputs a filtered markdown table
- Agent 2 (Risk Assessor): takes that table → adds a `risk_level` column (CRITICAL / MODERATE / WATCH)
- Agent 3 (Procurement Advisor): takes the risk table → writes a numbered action checklist

**Lab 2 — RAG query (`energy_burden_rag.py`)**
- Single agent: gets matching paragraphs from `energy_burden.txt` → responds as an energy policy analyst

**Lab 3 — Tool calling (`LAB_multi_agent_with_tools.py`)**
- Agent 1 (Data Fetcher): calls `get_earthquakes()` → returns a USGS DataFrame
- Agent 2 (Report Writer): gets that DataFrame → writes a short newsletter paragraph

---

### RAG Data Source

**File:** `07_rag/data/energy_burden.txt`

A reference document on energy burden — covers definitions, WAP/LIHEAP eligibility, renter burden, and housing stock. The search function splits it on double newlines and returns any paragraphs containing the query term (case-insensitive). Results go to the LLM as a JSON dict with keys: `query`, `document`, `matching_content`, and `num_matches`.

---

### Tool Functions

| Tool | Purpose | Parameters | Returns |
|---|---|---|---|
| `get_earthquakes` | Fetch recent USGS earthquake events | `min_magnitude` (float), `days_back` (int) | DataFrame: magnitude, place, time, depth_km, lat, lon |
| `get_shortages` | Fetch FDA drug shortage records | `category` (str), `limit` (int) | DataFrame: generic_name, update_type, update_date, availability |
| `search_text` | Keyword search over a text file | `query` (str), `document_path` (str) | Dict: query, document, matching_content, num_matches |

---

### Technical Details

| Item | Detail |
|---|---|
| Model | `smollm2:1.7b` (local via Ollama, port 11434) |
| Python packages | `requests`, `pandas`, `json`, `ast`, `tabulate` |
| External APIs | FDA Drug Shortages API (open.fda.gov), USGS Earthquake API (earthquake.usgs.gov) — both free, no key needed |
| Key helper | `functions.py` — added `func_map` param to `agent_run()` to fix external function resolution |
| RAG data | `07_rag/data/energy_burden.txt` — plain text, paragraph-delimited |

---

### Usage

Prerequisites:
```bash
ollama pull smollm2:1.7b
pip install requests pandas tabulate
```

Run each script from its own folder:
```bash
# Lab 1
cd 06_agents && python3 LAB_prompt_design.py

# Lab 2
cd 07_rag && python3 energy_burden_rag.py

# Lab 3
cd 08_function_calling && python3 LAB_multi_agent_with_tools.py
```

No API keys needed — both external APIs are open and free.

---

![Footer Image](../docs/images/icons.png)

---

← 🏠 [Back to Top](#Table-of-Contents)
