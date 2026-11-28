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
    *,
    age: int | None = None,
    event_format: str = "Any",
    location: str = "",
) -> dict[str, Any]:
    """Search Serper with event-focused constraints, without treating snippet dates as verified."""
    api_key = _setting("SERPER_API_KEY").strip()
    if not api_key:
        return {
            "results": [],
            "error": "Serper is not configured. Add SERPER_API_KEY to your environment or Streamlit secrets.",
        }

    parts = ["upcoming individual hackathon event", interests.strip(), details.strip()]
    if start_date and end_date:
        parts.append(f"event dates between {start_date} and {end_date}")
    if age is not None:
        parts.append(f"eligibility for age {age}")
    if event_format == "Online":
        parts.append("online virtual remote")
    elif event_format == "In-person":
        parts.append("in-person onsite")
    if location.strip() and event_format != "Online":
        parts.append(f"near {location.strip()}")
    parts.extend(("official event registration deadline", "exclude past events and hackathon lists"))
    query = " ".join(part for part in parts if part)

    try:
        response = requests.post(
            SERPER_SEARCH_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query, "num": 20},
            timeout=(5, 30),
        )
        response.raise_for_status()
        payload = response.json()
        organic = payload.get("organic", [])
        if not isinstance(organic, list):
            return {"results": [], "error": "Serper returned an unexpected organic results format."}
        return {"results": organic, "error": None, "query": query}
    except requests.RequestException:
        return {
            "results": [],
            "error": "Could not reach Serper. Check your API key, account quota, and network connection.",
        }
    except ValueError:
        return {"results": [], "error": "Serper returned invalid JSON."}
