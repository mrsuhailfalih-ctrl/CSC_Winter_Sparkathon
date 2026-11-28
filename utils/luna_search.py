from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urlsplit

import requests


def _setting(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return str(st.secrets.get(name, default))
    except Exception:
        return default


def luna_is_configured() -> bool:
    return bool(_setting("LUNA_API_KEY").strip())


def _response_text(payload: dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]
    parts = []
    for block in payload.get("output", []):
        if not isinstance(block, dict):
            continue
        for content in block.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "\n".join(parts)


def _parse_json(text: str) -> Any:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    return json.loads(cleaned)


def search_with_luna(
    interests: str,
    details: str,
    start_date: Any,
    end_date: Any,
    *,
    age: int | None = None,
    event_format: str = "Any",
    location: str = "",
) -> dict[str, Any]:
    """Use a Responses-API-compatible model with its web_search tool enabled."""
    key = _setting("LUNA_API_KEY").strip()
    if not key:
        return {"results": [], "error": "LUNA_API_KEY is not configured."}

    base_url = _setting("LUNA_API_BASE", "https://api.openai.com/v1").strip().rstrip("/")
    model = _setting("LUNA_MODEL", "gpt-6-luna").strip()
    prompt = (
        "Search the web now using your web_search tool. Find individual, currently relevant hackathons. "
        "Use the event schedule dates, not search publication dates or registration deadlines, to check the requested range. "
        "Prefer official event/organizer pages. Do not invent events, URLs, dates, locations, age limits, or details. "
        "Return only events for which you found a source URL; if dates are unclear, include the event with empty dates. "
        "Exclude broad directories, calendars, roundups, guides, and already-finished events when the source confirms they are past. "
        "Return JSON only with this shape: {\"events\":[{\"title\":\"...\",\"url\":\"https://...\","
        "\"snippet\":\"short source-grounded description\",\"event_start_date\":\"YYYY-MM-DD or empty\","
        "\"event_end_date\":\"YYYY-MM-DD or empty\",\"location\":\"...\",\"age_eligibility\":\"...\","
        "\"format\":\"Online, In-person, or Unknown\"}]}\n"
        f"Interests: {interests[:300]}\nPreferences: {details[:500]}\nAge: {age if age is not None else 'unspecified'}\n"
        f"Format: {event_format}\nLocation: {location[:160] or 'unspecified'}\n"
        f"Event date range: {start_date} through {end_date}"
    )
    try:
        response = requests.post(
            f"{base_url}/responses",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "tools": [{"type": "web_search"}],
                "tool_choice": "auto",
                "input": prompt,
                "max_output_tokens": 3000,
            },
            timeout=(8, 90),
        )
        response.raise_for_status()
        payload = response.json()
        text = _response_text(payload)
        decoded = _parse_json(text)
        candidate_events = decoded.get("events", []) if isinstance(decoded, dict) else []
        results = []
        for item in candidate_events:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            title = item.get("title")
            if not isinstance(url, str) or not isinstance(title, str) or not title.strip():
                continue
            try:
                parsed = urlsplit(url)
            except ValueError:
                continue
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
                continue
            results.append({
                "title": title.strip()[:240],
                "link": url,
                "snippet": str(item.get("snippet", ""))[:1200],
                "event_start_date": str(item.get("event_start_date", ""))[:32],
                "event_end_date": str(item.get("event_end_date", ""))[:32],
                "location": str(item.get("location", ""))[:200],
                "age_eligibility": str(item.get("age_eligibility", ""))[:200],
                "format": str(item.get("format", "Unknown"))[:40],
                "source": "GPT web search; verify with organizer",
            })
        return {"results": results, "error": None, "query": prompt, "provider": model}
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        # Do not expose response bodies or credentials in the UI/logs.
        return {
            "results": [],
            "error": f"GPT web search failed ({type(exc).__name__}). Check that the provider supports the Responses API and the web_search tool, and verify LUNA_API_BASE, LUNA_MODEL, and the key.",
        }
