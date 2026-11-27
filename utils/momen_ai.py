from __future__ import annotations

import json
import os
import re
from datetime import date
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


def momen_is_configured() -> bool:
    return all(_setting(name) for name in ("MOMEN_GRAPHQL_URL", "MOMEN_JWT", "MOMEN_AI_MUTATION"))


def _replace_prompt(value: Any, prompt: str) -> Any:
    if isinstance(value, str):
        return value.replace("{{PROMPT}}", prompt)
    if isinstance(value, list):
        return [_replace_prompt(item, prompt) for item in value]
    if isinstance(value, dict):
        return {key: _replace_prompt(item, prompt) for key, item in value.items()}
    return value


def _extract_text(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("text", "content", "response", "message", "output", "result"):
            if key in value:
                found = _extract_text(value[key])
                if found:
                    return found
        for item in value.values():
            found = _extract_text(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = _extract_text(item)
            if found:
                return found
    return None


def _invoke_momen(prompt: str) -> tuple[str | None, str | None]:
    endpoint = _setting("MOMEN_GRAPHQL_URL").strip()
    token = _setting("MOMEN_JWT").strip()
    mutation = _setting("MOMEN_AI_MUTATION").strip()
    if not endpoint or not token or not mutation:
        return None, "Momen AI is not configured. Add the GraphQL URL, server-side JWT, generated agent mutation, and variables template to host secrets."
    try:
        variables_template = json.loads(_setting("MOMEN_AI_VARIABLES_JSON", '{"prompt":"{{PROMPT}}"}'))
        body = {"query": mutation, "variables": _replace_prompt(variables_template, prompt)}
        response = requests.post(
            endpoint,
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=(4, 45),
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            return None, "Momen returned a GraphQL error. Verify the generated mutation and variables against this project's GraphiQL schema."
        return _extract_text(payload.get("data")), None
    except (requests.RequestException, ValueError, TypeError, KeyError):
        return None, "Could not reach Momen. Check server-side settings and the generated GraphQL operation."


def _decode_json(text: str) -> Any:
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    return json.loads(cleaned)


def _event_url_platform(url: str):
    # Import lazily to avoid coupling Momen support to the scraper during startup.
    from utils.live_search import PLATFORMS, _is_event_url
    try:
        parsed = urlsplit(url)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return None
    return next((p for p in PLATFORMS if _is_event_url(url, p)), None)


def _verify_candidate(candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Fetch only allowlisted event URLs and use page metadata, not AI claims."""
    from utils.live_search import _PageParser, _event_row, _fallback_event_row, _fetch_page, _parse_jsonld
    url = candidate.get("url")
    if not isinstance(url, str):
        return None
    platform = _event_url_platform(url)
    if not platform:
        return None
    html, error = _fetch_page(url, platform)
    if not html:
        return None
    parser = _PageParser()
    parser.feed(html)
    events = [_event_row(raw, url, platform) for raw in _parse_jsonld(parser)]
    events = [event for event in events if event]
    if events:
        event = events[0]
    else:
        event = _fallback_event_row(parser, url, platform)
    if not event:
        return None
    # Require the fetched page itself to look event-specific. Do not rely on an
    # AI-invented title/description when the page provides no corroborating info.
    page_evidence = f"{event['name']} {event['snippet']}".lower()
    if not any(term in page_evidence for term in ("hackathon", "hack-a-thon", "hack day", "buildathon", "coding challenge")):
        return None
    event["date_verified"] = event.get("start_date") is not None
    event["source_platform"] = platform["name"]
    return event


def search_events_with_momen(
    interests: str, details: str, start: date, end: date,
) -> dict[str, Any]:
    """Use a Momen agent's configured web-search tool to discover platform events.

    Returned candidate URLs are strictly allowlisted and fetched before display.
    The agent must be configured in Momen with web-search/browsing capability;
    the GraphQL call alone does not grant the model internet access.
    """
    if start > end:
        raise ValueError("The start date must be on or before the latest date.")
    from utils.live_search import PLATFORMS, _matches_topic, _within_period
    platform_names = ", ".join(p["name"] for p in PLATFORMS)
    prompt = (
        "Use your configured web search/browsing tool now. Find current, individual hackathon event pages "
        f"on these official hosting platforms only: {platform_names}. Do not use aggregators or generic articles. "
        "Return JSON only as {\"events\":[{\"url\":\"exact https event URL\"}]}. "
        "Do not invent URLs, event details, dates, eligibility, or descriptions. Only include URLs you opened or directly verified with web search. "
        "The app will fetch each URL and independently validate the platform page.\n"
        f"Interests: {interests[:300]}\nPreferences: {details[:500]}\n"
        f"Requested event period: {start.isoformat()} through {end.isoformat()}"
    )
    text, error = _invoke_momen(prompt)
    if error:
        return {"results": [], "error": error, "diagnostics": {"method": "momen_web_search", "candidate_count": 0, "verified_count": 0}}
    if not text:
        return {"results": [], "error": "Momen returned no text. Confirm the configured agent invokes a web-search tool and returns JSON.", "diagnostics": {"method": "momen_web_search", "candidate_count": 0, "verified_count": 0}}
    try:
        payload = _decode_json(text)
        candidates = payload.get("events", []) if isinstance(payload, dict) else []
    except (json.JSONDecodeError, AttributeError):
        return {"results": [], "error": "Momen's response was not valid JSON. Configure the agent to return {\"events\":[{\"url\":\"...\"}]} only.", "diagnostics": {"method": "momen_web_search", "candidate_count": 0, "verified_count": 0}}

    unique_urls = []
    for item in candidates[:40]:
        if isinstance(item, dict) and isinstance(item.get("url"), str) and item["url"] not in unique_urls:
            if _event_url_platform(item["url"]):
                unique_urls.append(item["url"])
    results = []
    for url in unique_urls[:20]:
        event = _verify_candidate({"url": url})
        if event and _matches_topic(event, interests) and _within_period(event, start, end):
            results.append(event)
    results.sort(key=lambda event: (event.get("start_date") is None, event.get("start_date") or date.max, event["name"].lower()))
    return {
        "results": results,
        "error": None,
        "message": "Momen searched the web; displayed results were fetched from allowlisted event-platform pages. Dates and eligibility still need organizer verification.",
        "diagnostics": {"method": "momen_web_search", "candidate_count": len(unique_urls), "verified_count": len(results), "platform_url_filter": True},
    }


def rank_events_with_momen(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Legacy ranking helper retained for compatibility; the app now uses search."""
    if not events:
        return {"available": True, "rankings": {}, "message": ""}
    rows = [{"name": event.get("name", ""), "url": event.get("url", ""), "platform": event.get("source_platform", ""), "start_date": str(event.get("start_date") or ""), "description": event.get("snippet", "")[:500]} for event in events[:30]]
    prompt = "Rank these supplied events for relevance. Do not invent details. Return JSON {\"rankings\":[{\"url\":\"exact URL\",\"score\":0,\"reason\":\"...\"}]}: " + json.dumps(rows)
    text, error = _invoke_momen(prompt)
    if error or not text:
        return {"available": False, "rankings": {}, "message": error or "Momen returned no text."}
    try:
        data = _decode_json(text)
        allowed = {str(event.get("url")) for event in events}
        rankings = {}
        for row in data.get("rankings", []):
            if isinstance(row, dict) and row.get("url") in allowed:
                try:
                    rankings[row["url"]] = {"score": max(0, min(100, int(row.get("score", 0)))), "reason": str(row.get("reason", ""))[:240]}
                except (TypeError, ValueError):
                    continue
        return {"available": bool(rankings), "rankings": rankings, "message": "Momen rankings are advisory only." if rankings else "No usable rankings returned."}
    except (json.JSONDecodeError, AttributeError, TypeError):
        return {"available": False, "rankings": {}, "message": "Momen response was not valid ranking JSON."}
