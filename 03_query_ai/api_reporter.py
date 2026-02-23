# Marketstack API Example
# - API Name: Marketstack
# - Endpoint: /v1/eod
# - Expected Data: One record per stock per trading day. Data returned in JSON format.
# - Number of Records: 100, 10 records per 10 companies
# - Key Fields: symbol, date, adj_close, adj_volume
# - Data Structure: dataframe

import pandas as pd
import requests            # for making HTTP requests
import os                  # for reading environment variables
import os  # for reading environment variables
import requests  # for making HTTP requests
from dotenv import load_dotenv  # for loading variables from .env

load_dotenv(".env")
access_key = os.getenv("access_key")
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")

try:
    response = requests.get(
        "http://api.marketstack.com/v1/eod",
        params={"access_key": access_key,
                "symbols": "AAPL,MSFT,GOOGL,AMZN,META,NVDA,TCEHY,BABA,IBM,ORCL",
                "date_from": "2025-10-01", "date_to": "2025-12-31"},
    )

    if response.status_code != 200:
        print(f"Request failed with status code {response.status_code}")
        print("Raw response:", response.text)
        response.raise_for_status()
except requests.exceptions.RequestException as e:
    print("Request error occurred:", e)
else:
    data = response.json()["data"]
    df = pd.DataFrame(data)
    df = df[["symbol", "date", "adj_close", "adj_volume"]]
    df["date"] = pd.to_datetime(df["date"])
    df = df.dropna()

    summary = df.groupby("symbol").agg(
        avg_close=("adj_close", "mean"),
        total_volume=("adj_volume", "sum"),
        max_close=("adj_close", "max"),
        min_close=("adj_close", "min")
    ).reset_index()

    summary = summary.round(2)

    ai_ready_data = summary.to_dict(orient="records")

    print(response.status_code)

    prompt = f"""
    You are a financial data analyst.

    Below is summarized Q4 2025 stock performance data.
    Each company includes:
    - avg_close (average adjusted closing price)
    - total_volume (total trading volume)
    - max_close (highest closing price)
    - min_close (lowest closing price)

    Stock Data:
    {ai_ready_data}

    Tasks:
    1. Write a 3-sentence executive summary of overall performance.
    2. Identify the top 3 companies by average closing price.
    3. Highlight any notable volume trends.
    4. Use bullet points for the insights section.
    5. Keep response under 150 words.
    6. Base analysis ONLY on the provided data.

    Format exactly as:

    Executive Summary:
    [3 sentences]

    Top Insights:
    - Insight 1
    - Insight 2
    - Insight 3
    """

    url = "https://ollama.com/api/chat"

    body = {
        "model": "gpt-oss:20b-cloud",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False
    }

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json"
    }

    ai_response = requests.post(url, headers=headers, json=body)
    ai_response.raise_for_status()

    result = ai_response.json()
    output = result["message"]["content"]

    print(output)

globals().clear()
