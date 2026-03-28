# server.py
# Stateless MCP Server — FastAPI (Python)
# Pairs with mcp_plumber/plumber.R
# Tim Fraser

# What this file is:
#   A FastAPI app that speaks the Model Context Protocol (MCP) over HTTP.
#   It mirrors plumber.R: same tools, same JSON-RPC methods, Streamable HTTP behavior.
#   Stateless: each POST /mcp is one JSON-RPC request → one JSON response (or 202 for notifications).
#
# How to run locally:
#   uvicorn server:app --port 8000 --reload
#   or: python runme.py
#
# How to deploy:
#   See deployme.py
#
# Packages:
#   pip install fastapi uvicorn pandas
#   (requests only needed if you use testme.py for Ollama)

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
import pandas as pd
import json

app = FastAPI()

# ── Tool definitions (what the LLM sees) ────────────────────

TOOLS = [
    {
        "name": "summarize_dataset",
        "description": "Returns mean, sd, min, and max for each numeric column in a dataset.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "Dataset to summarize. Options: 'mtcars' or 'iris'.",
                }
            },
            "required": ["dataset_name"],
        },
    },
    {
        "name": "filter_dataset",
        "description": "Filter rows from a dataset where a numeric column meets a condition. Returns matching rows as JSON.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "dataset_name": {
                    "type": "string",
                    "description": "Dataset to filter. Options: 'mtcars' or 'iris'.",
                },
                "column": {
                    "type": "string",
                    "description": "Name of the numeric column to filter on (e.g. 'mpg', 'Sepal.Length').",
                },
                "operator": {
                    "type": "string",
                    "description": "Comparison operator: '>', '<', '>=', '<=', or '=='.",
                },
                "value": {
                    "type": "number",
                    "description": "Numeric threshold to compare against.",
                },
            },
            "required": ["dataset_name", "column", "operator", "value"],
        },
    },
]

# ── Tool logic (same datasets as R: mtcars, iris via Rdatasets CSV) ──

_DATASET_URLS = {
    "mtcars": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/mtcars.csv",
    "iris": "https://vincentarelbundock.github.io/Rdatasets/csv/datasets/iris.csv",
}
DATASETS = {name: pd.read_csv(url) for name, url in _DATASET_URLS.items()}


def run_tool(name: str, args: dict) -> str:
    if name == "summarize_dataset":
        nm = args.get("dataset_name")
        if nm not in DATASETS:
            raise ValueError(f"Unknown dataset: '{nm}' — choose 'mtcars' or 'iris'")

        df = DATASETS[nm].select_dtypes(include="number")
        summary = df.agg(["mean", "std", "min", "max"]).round(2).T
        summary.index.name = "variable"
        summary.columns = ["mean", "sd", "min", "max"]
        return summary.reset_index().to_json(orient="records", indent=2)

    if name == "filter_dataset":
        nm = args.get("dataset_name")
        if nm not in DATASETS:
            raise ValueError(f"Unknown dataset: '{nm}' — choose 'mtcars' or 'iris'")

        col = args.get("column")
        op  = args.get("operator")
        val = args.get("value")

        df = DATASETS[nm]
        if col not in df.columns:
            raise ValueError(f"Column '{col}' not found. Available: {list(df.columns)}")

        ops = {">": "__gt__", "<": "__lt__", ">=": "__ge__", "<=": "__le__", "==": "__eq__"}
        if op not in ops:
            raise ValueError(f"Operator '{op}' not supported. Use one of: {list(ops)}")

        filtered = df[getattr(df[col], ops[op])(val)]
        return filtered.to_json(orient="records", indent=2)

    raise ValueError(f"Unknown tool: {name}")


# ── MCP JSON-RPC router ──────────────────────────────────────


@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()

    method = body.get("method")
    id_ = body.get("id")

    if isinstance(method, str) and method.startswith("notifications/"):
        return Response(status_code=202)

    try:
        if method == "initialize":
            result = {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "py-summarizer", "version": "0.1.0"},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": TOOLS}
        elif method == "tools/call":
            tool_result = run_tool(
                body["params"]["name"],
                body["params"]["arguments"],
            )
            result = {
                "content": [{"type": "text", "text": tool_result}],
                "isError": False,
            }
        else:
            raise ValueError(f"Method not found: {method}")

    except Exception as e:
        return JSONResponse(
            {"jsonrpc": "2.0", "id": id_, "error": {"code": -32601, "message": str(e)}}
        )

    return JSONResponse({"jsonrpc": "2.0", "id": id_, "result": result})


@app.options("/mcp")
async def mcp_options():
    return Response(
        status_code=204,
        headers={"Allow": "GET, POST, OPTIONS"},
    )


@app.get("/mcp")
async def mcp_get():
    return Response(
        content=json.dumps(
            {"error": "This MCP server uses stateless HTTP. Use POST."}
        ),
        status_code=405,
        headers={"Allow": "GET, POST, OPTIONS"},
        media_type="application/json",
    )
