# Marketstack API Example
# - API Name: Marketstack
# - Endpoint: /v1/eod
# - Expected Data: One record per stock per trading day. Data returned in JSON format.
# - Number of Records: 100, 10 records per 10 companies
# - Key Fields: symbol, date, adj_close, adj_volume
# - Data Structure: dataframe

import requests            # for making HTTP requests
import os                  # for reading environment variables
from dotenv import load_dotenv  # for loading variables from .env

load_dotenv(".env")
access_key = os.getenv("access_key")

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
    print(response.status_code)
    print(response.json())

globals().clear()
