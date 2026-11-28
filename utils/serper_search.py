from __future__ import annotations

import os
import re
from datetime import date
from typing import Any
from urllib.parse import urlsplit

import requests

from utils.result_filtering import filter_event_candidates

SERPER_ENDPOINT = "https://google.serper.dev/search"
MAX_RESULTS = 20
TIMEOUT = (5, 25)


def _get_serper_key() -> str:
    key = os.getenv("SERPER_API_KEY", "").strip()
    if key:
        return key
    try:
        import streamlit as st

        return str(st.secrets.get("SERPER_API_KEY", "")).strip()
    except Exception:
        return ""


def _safe_https_url(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlsplit(url)
        return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username and not parsed.password
    except ValueError:
        return False


def _query(interests: str, details: str, start: date, end: date, age: int, event_format: str) -> str:
    pieces = ["hackathon OR buildathon OR coding challenge"]
    if interests.strip():
        pieces.append(interests.strip()[:160])
    if details.strip():
        pieces.append(details.strip()[:160])
    pieces.extend((f'after:{start.isoformat()}', f'before:{end.isoformat()}', "registration event"))
    if event_format == "Online":
        pieces.append("online OR virtual")
    elif event_format == "In-person":
        pieces.append('"in person" OR onsite OR location')
    # Search hints only: age/format eligibility is determined from evidence, never assumed.
    pieces.append(f"student age {age} eligibility")
    return " ".join(pieces)


def _candidate_from_organic(item: dict[str, Any]) -> dict[str, Any] | None:
    url = item.get("link")
    title = item.get("title")
    if not _safe_https_url(url) or not isinstance(title, str) or not title.strip():
        return None
    snippet = item.get("snippet") or ""
    if not isinstance(snippet, str):
        snippet = str(snippet)
    return {
        "name": title.strip()[:240],
        "url": url,
        "snippet": snippet.strip()[:1000],
        "source_platform": urlsplit(url).hostname or "Web search",
    }


def search_hackathons(
    interests: str,
    details: str,
    start: date,
    end: date,
    age: int,
    event_format: str = "Any",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Search with Serper and apply permissive, evidence-based event filters."""
    if start > end:
        raise ValueError("The start date must be on or before the latest date.")
    key = (api_key or _get_serper_key()).strip()
    if not key:
        return {"error": "Serper is not configured. Add SERPER_API_KEY to Streamlit Secrets or the server environment.", "results": []}
    query = _query(interests, details, start, end, age, event_format)
    try:
        response = requests.post(
            SERPER_ENDPOINT,
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": MAX_RESULTS},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
        organic = payload.get("organic", []) if isinstance(payload, dict) else []
        if not isinstance(organic, list):
            organic = []
    except requests.Timeout:
        return {"error": "Serper search timed out. Please try again.", "results": []}
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "unknown"
        if status in (401, 403):
            message = "Serper rejected the API key. Check SERPER_API_KEY in your server secrets."
        elif status == 429:
            message = "Serper rate limit reached. Wait a little and try again."
        else:
            message = f"Serper returned HTTP {status}. Please try again later."
        return {"error": message, "results": []}
    except (requests.RequestException, ValueError, TypeError):
        return {"error": "Could not reach Serper or read its response. Check the server connection and try again.", "results": []}

    candidates = []
    seen = set()
    for item in organic:
        if not isinstance(item, dict):
            continue
        candidate = _candidate_from_organic(item)
        if candidate and candidate["url"] not in seen:
            candidates.append(candidate)
            seen.add(candidate["url"])

    confirmed, possible, diagnostics = filter_event_candidates(
        candidates,
        interests=interests,
        start=start,
        end=end,
        age=age,
        event_format=event_format,
        details=details,
    )
    events = confirmed + possible
    events.sort(key=lambda item: (item.get("date_fit") is not True, item.get("name", "").lower()))
    return {
        "error": None,
        "results": events,
        "message": "Results come from Serper web search snippets. Unknown details remain included for you to verify on the organizer page.",
        "diagnostics": {"query": query, "serper_results": len(candidates), **diagnostics},
    }
