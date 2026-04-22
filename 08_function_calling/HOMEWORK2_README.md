# Homework 2: AI Agent Systems with RAG and Tools

## About

For this homework, I built an **earthquake intelligence pipeline** that ties together the last three weeks of labs into one cohesive system. The idea is that all three components — multi-agent orchestration, RAG, and function calling — are working on the same problem: pulling live seismic data, cross-referencing it against a preparedness knowledge base, and turning it into something useful for emergency managers or the public.

Lab 1 sets up a three-agent triage chain that takes raw USGS earthquake data and runs it through a classify-then-advise workflow. Lab 2 adds a retrieval layer over an earthquake preparedness document so the system can answer specific questions by pulling relevant context rather than relying on the model's built-in knowledge alone. Lab 3 brings in a live `get_earthquake()` tool call to the USGS API, so Agent 1 can fetch fresh data at runtime and pass it straight to Agent 2 to write a newsletter summary.

Most of the technical work came down to prompt design and getting function resolution to work correctly across files. With a 1.7B model, I had to be pretty explicit. Vague instructions consistently produced inaccurate output, so I ended up leading every system prompt with a direct imperative and including a concrete example of what the output should look like. On the code side, the main issue was that tool functions defined outside `functions.py` weren't visible when `agent_run()` tried to look them up, so I added a `func_map` parameter to let callers pass their function in explicitly.

---

## Git Repo

| Component | File |
|---|---|
| Multi-agent workflow | [`06_agents/LAB_prompt_design.py`](../06_agents/LAB_prompt_design.py) |
| RAG implementation | [`07_rag/LAB_earthquake_rag.py`](../07_rag/LAB_earthquake_rag.py) |
| Function calling / tools | [`08_function_calling/LAB_multi_agent_with_tools.py`](LAB_multi_agent_with_tools.py) |
| Agent helper functions | [`08_function_calling/functions.py`](functions.py) |
| Documentation | [`08_function_calling/HOMEWORK2_README.md`](HOMEWORK2_README.md) |

---

## System Architecture

### Lab 1 — Multi-Agent Triage Chain (`LAB_prompt_design.py`)

Three agents running in sequence over live USGS earthquake data:

```
USGS API → raw DataFrame
    ↓
Agent 1 (Data Analyst)
  role: clean and format data as a markdown table
  input: raw DataFrame (as markdown)
  output: cleaned table (magnitude, place, time, depth_km)
    ↓
Agent 2 (Risk Assessor)
  role: classify each earthquake HIGH / MODERATE / LOW
  input: Agent 1 table
  output: risk-classified table (adds risk_level column)
    ↓
Agent 3 (Emergency Advisor)
  role: generate one action item per earthquake for local authorities
  input: Agent 2 table
  output: numbered emergency response checklist
```

**Risk classification thresholds:**
- HIGH: magnitude ≥ 6.5
- MODERATE: magnitude 5.5 – 6.4
- LOW: magnitude < 5.5

### Lab 2 — RAG over Preparedness Knowledge Base (`LAB_earthquake_rag.py`)

```
User query
    ↓
search_text(query, "data/earthquake_preparedness.txt")
  → paragraph-level keyword search (case-insensitive)
  → returns matching paragraphs + metadata as JSON
    ↓
agent_run(role=analyst_prompt, task=json_result)
  → LLM synthesises retrieved content into structured analysis
```

**Data source:** `07_rag/data/earthquake_preparedness.txt`  
A custom knowledge base covering what to do before/during/after earthquakes, structural safety, community emergency planning, tsunami awareness, and recovery.

### Lab 3 — Multi-Agent System with Function Calling (`LAB_multi_agent_with_tools.py`)

```
Agent 1 (Data Fetcher) — uses get_earthquake() tool
  input: natural-language task ("fetch recent M5.0+ earthquakes, past 21 days")
  tool call: get_earthquake(min_magnitude=5.0, days=21, limit=34) → USGS API
  output: DataFrame of recent earthquakes
    ↓
Agent 2 (Newsletter Writer) — no tools
  input: Agent 1 DataFrame (as markdown table, top 15 rows)
  output: 2–3 paragraph public newsletter summary
```

---

## RAG Data Source

**File:** `07_rag/data/earthquake_preparedness.txt`  
**Format:** Plain text, paragraphs separated by blank lines  
**Search method:** Paragraph-level substring match (`query.lower() in paragraph.lower()`)  
**Topics covered:** Before/during/after earthquake actions, structural retrofitting, community response planning, tsunami awareness, psychological recovery

The search function splits the document on double newlines and returns any paragraph containing the query string. When 0 paragraphs match, the LLM still generates a response using its built-in knowledge.

---

## Tool Functions

| Name | Purpose | Parameters | Returns |
|---|---|---|---|
| `get_earthquake` | Fetch recent earthquakes from USGS API | `min_magnitude` (float), `days` (int), `limit` (int) | `pandas.DataFrame` with columns: magnitude, place, time, depth_km, latitude, longitude |
| `search_text` | Paragraph search over a text document | `query` (str), `document_path` (str) | dict: query, document, matching_content, num_paragraphs |

---

## Technical Details

| Item | Value |
|---|---|
| Model | `smollm2:1.7b` (via Ollama) |
| Ollama port | `11434` |
| USGS API endpoint | `https://earthquake.usgs.gov/fdsnws/event/1/query` |
| RAG document | `07_rag/data/earthquake_preparedness.txt` |
| Key packages | `requests`, `pandas`, `tabulate` |

**Key change to `functions.py`:** Added `func_map` parameter to `agent()` and `agent_run()`. This lets callers pass a `{"function_name": callable}` dict so that tool functions defined outside `functions.py` resolve correctly without relying solely on stack-frame inspection.

---

## Usage Instructions

### 1. Install dependencies

```bash
pip install requests pandas tabulate
```

### 2. Start Ollama and pull the model

```bash
ollama serve          # start Ollama server (keep running)
ollama pull smollm2:1.7b
```

### 3. Run Lab 1 — Multi-Agent Triage

```bash
cd 06_agents
python3 LAB_prompt_design.py
```

### 4. Run Lab 2 — RAG Query

```bash
cd 07_rag
python3 LAB_earthquake_rag.py
```

### 5. Run Lab 3 — Function Calling

```bash
cd 08_function_calling
python3 LAB_multi_agent_with_tools.py
```

No API keys are required. The USGS Earthquake Hazards API is free and open. Ollama runs entirely locally.
