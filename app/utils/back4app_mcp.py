import os
import json
import requests
from typing import Dict, Any

"""
Helper to save evaluation results to Back4App using the REST API.

Configuration via environment variables:
- BACK4APP_APP_ID : application id
- BACK4APP_REST_KEY : REST API key
- BACK4APP_MCP_URL : optional custom MCP endpoint (will be used instead of Back4App REST API)

The module exposes `save_evaluation(payload)` which returns the parsed JSON response from Back4App.
"""

BACK4APP_APP_ID = os.getenv("BACK4APP_APP_ID")
BACK4APP_REST_KEY = os.getenv("BACK4APP_REST_KEY")
BACK4APP_MCP_URL = os.getenv("BACK4APP_MCP_URL")


def save_evaluation(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Save the evaluation payload to Back4App (class `Evaluation`).

    payload keys should be JSON-serializable. Returns the response JSON.
    """
    if BACK4APP_MCP_URL:
        # If an MCP server URL is provided, POST there. Expect the MCP to proxy to Back4App.
        url = BACK4APP_MCP_URL.rstrip("/") + "/evaluation"
        r = requests.post(url, json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    # Fallback to Back4App REST API
    if not BACK4APP_APP_ID or not BACK4APP_REST_KEY:
        raise RuntimeError("Please set BACK4APP_APP_ID and BACK4APP_REST_KEY environment variables to save evaluations.")

    url = "https://parseapi.back4app.com/classes/Evaluation"
    headers = {
        "X-Parse-Application-Id": BACK4APP_APP_ID,
        "X-Parse-REST-API-Key": BACK4APP_REST_KEY,
        "Content-Type": "application/json",
    }
    r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=15)
    r.raise_for_status()
    return r.json()
