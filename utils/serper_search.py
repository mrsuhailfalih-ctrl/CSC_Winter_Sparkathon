from __future__ import annotations

import os
from typing import Any

import requests

SERPER_SEARCH_URL = "https://google.serper.dev/search"


def _setting(name: str, default: str = "") -> str:
    """Read configuration from environment variables or Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


def serper_is_configured() -> bool:
    return bool(_setting("SERPER_API_KEY").strip())


def search_with_serper(
    interests: str,
    details: str,
    start_date: Any,
    end_date: Any,
) -> dict[str, Any]:
    """Return Serper's organic results as-is; do not post-filter search results."""
    api_key = _setting("SERPER_API_KEY").strip()
    if not api_key:
        return {
            "results": [],
            "error": "Serper is not configured. Add SERPER_API_KEY to your environment or Streamlit secrets.",
        }

    parts = ["hackathons", interests.strip(), details.strip()]
    query = " ".join(part for part in parts if part)
    if start_date and end_date:
        query += f" {start_date} through {end_date}"

    try:
        response = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query},
            timeout=(5, 30),
        )
        response.raise_for_status()
        payload = response.json()
        organic = payload.get("organic", [])
        if not isinstance(organic, list):
            return {"results": [], "error": "Serper returned an unexpected organic results format."}
        # Preserve every organic result and its original fields. There is deliberately
        # no relevance, date, event-type, or domain filtering after the API response.
        return {"results": organic, "error": None, "query": query}
    except requests.RequestException:
        return {
            "results": [],
            "error": "Could not reach Serper. Check your API key, account quota, and network connection.",
        }
    except ValueError:
        return {"results": [], "error": "Serper returned invalid JSON."}
