# test_requests.py
# POST Request with JSON Data

# Demonstrates making a POST request with JSON payload using the requests library.
# httpbin.org/post echoes back the request, useful for testing.

# 0. SETUP ###################################

## 0.1 Load Packages #################################

import requests  # for HTTP requests

# 1. MAKE POST REQUEST ###################################

# JSON data to send in the request body
data = {"name": "test"}

# Send POST request - json= automatically sets Content-Type and serializes the dict
response = requests.post("https://httpbin.org/post", json=data)

# 2. INSPECT RESPONSE ###################################

# Check status (200 = success)
print(response.status_code)

# Parse and display the JSON response
# httpbin echoes back our data in the "json" field
print(response.json())
