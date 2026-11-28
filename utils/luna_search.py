from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.parse import urlsplit, urlunsplit

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


def _citation_urls(payload: dict[str, Any]) -> set[str]:
    """Collect source URLs attached as web-search citation annotations by the API."""
    found: set[str] = set()
    for block in payload.get("output", []):
        if not isinstance(block, dict):
            continue
        for content in block.get("content", []):
            if not isinstance(content, dict):
                continue
            for annotation in content.get("annotations", []):
                if isinstance(annotation, dict) and annotation.get("type") in {"url_citation", "web_search_result"}:
                    url = annotation.get("url")
                    if isinstance(url, str):
                        normalized = _normalize_url(url)
                        if normalized:
                            found.add(normalized)
    return found


def _normalize_url(url: str) -> str:
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return ""
        return urlunsplit(("https", parsed.netloc.lower(), parsed.path.rstrip("/"), parsed.query, ""))
    except ValueError:
        return ""


def _parse_json(text: str) -> Any:
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", text.strip(), flags=re.I)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Tolerate a short preamble while still requiring valid JSON for the payload.
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start:end + 1])
        raise


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
    """Search with a Responses-API-compatible model and require its web-search citations."""
    key = _setting("LUNA_API_KEY").strip()
    if not key:
        return {"results": [], "error": "LUNA_API_KEY is not configured."}

    base_url = _setting("LUNA_API_BASE", "https://api.openai.com/v1").strip().rstrip("/")
    model = _setting("LUNA_MODEL", "gpt-6-luna").strip()
    web_tool = _setting("LUNA_WEB_SEARCH_TOOL", "web_search").strip()
    prompt = (
        "You are finding real hackathon events. You MUST use the enabled web search tool; do not answer from memory. "
        "Search for individual events and prefer official organizer or event-platform pages. Cross-check dates and eligibility "
        "against the source page/search evidence. Use the actual event schedule, not publication dates or registration deadlines. "
        "Do not invent an event, URL, date, location, eligibility rule, or format. Every returned event URL must be a URL you "
        "actually opened or cited in web search. Include the event if its timing is unclear but leave date fields empty. "
        "Exclude broad directories, calendars, roundups, guides, and events confirmed to be finished. Return JSON only in this shape: "
        "{\"events\":[{\"title\":\"...\",\"url\":\"https://...\",\"snippet\":\"short source-grounded description\","
        "\"event_start_date\":\"YYYY-MM-DD or empty\",\"event_end_date\":\"YYYY-MM-DD or empty\","
        "\"location\":\"...\",\"age_eligibility\":\"...\",\"format\":\"Online, In-person, or Unknown\"}]}\n"
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
                "tools": [{"type": web_tool}],
                "tool_choice": "required",
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
        citations = _citation_urls(payload)
        if not citations:
            return {
                "results": [],
                "error": "The AI response contained no web-search source citations. Check that the provider supports the configured web-search tool and returns citation annotations.",
            }

        results = []
        for item in candidate_events:
            if not isinstance(item, dict):
                continue
            url = item.get("url")
            title = item.get("title")
            if not isinstance(url, str) or not isinstance(title, str) or not title.strip():
                continue
            normalized_url = _normalize_url(url)
            # Do not present model-generated URLs unless the API attached the same URL
            # as a web-search citation. This reduces fabricated or unsupported results.
            if not normalized_url or normalized_url not in citations:
                continue
            start_date_value = item.get("event_start_date")
            end_date_value = item.get("event_end_date")
            def valid_date(value: Any) -> str:
                if not isinstance(value, str) or not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", value):
                    return ""
                try:
                    from datetime import date
                    date.fromisoformat(value)
                except ValueError:
                    return ""
                return value

            results.append({
                "title": title.strip()[:240],
                "link": url,
                "snippet": str(item.get("snippet", ""))[:1200],
                "event_start_date": valid_date(start_date_value),
                "event_end_date": valid_date(end_date_value),
                "location": str(item.get("location", ""))[:200],
                "age_eligibility": str(item.get("age_eligibility", ""))[:200],
                "format": str(item.get("format", "Unknown"))[:40],
                "source": "GPT web-search citation; verify with organizer",
            })
        return {"results": results, "error": None, "query": prompt, "provider": model}
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        # Do not expose response bodies or credentials in the UI/logs.
        return {
            "results": [],
            "error": f"GPT web search failed ({type(exc).__name__}). Check that the provider supports the Responses API and the configured web-search tool, and verify LUNA_API_BASE, LUNA_MODEL, and the key.",
        }
