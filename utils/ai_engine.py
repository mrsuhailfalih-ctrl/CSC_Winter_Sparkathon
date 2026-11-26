from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import requests


MAX_USER_PROMPT_CHARS = 3000
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "hackathons.json"


def _get_setting(name: str, default: str = "") -> str:
    """Read configuration from environment variables or Streamlit secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


def load_hackathons() -> list[dict[str, Any]]:
    with DATA_PATH.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data if isinstance(data, list) else []


def filter_by_age(hackathons: list[dict[str, Any]], age: int) -> list[dict[str, Any]]:
    """Filter only against explicit minimum/maximum values in the dataset."""
    eligible = []
    for event in hackathons:
        minimum = event.get("minimum_age")
        maximum = event.get("maximum_age")
        if minimum is not None and age < int(minimum):
            continue
        if maximum is not None and age > int(maximum):
            continue
        eligible.append(event)
    return eligible


def rank_locally(
    user_preferences: str,
    age: int,
    hackathons: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic fallback that requires no paid API or Ollama server."""
    query = user_preferences.lower()
    terms = {term.strip().lower() for term in query.replace("/", " ").replace(",", " ").split() if term.strip()}
    ranked = []

    for event in hackathons:
        searchable = " ".join(str(event.get(key, "")) for key in ("name", "theme", "tags", "format", "level", "location")).lower()
        score = sum(1 for term in terms if len(term) > 2 and term in searchable) * 15
        if "beginner" in query and str(event.get("level", "")).lower() == "beginner":
            score += 25
        if "online" in query and str(event.get("location", "")).lower() == "online":
            score += 20
        if str(event.get("location", "")).lower() == "online":
            score += 5

        age_label = event.get("age_label", "Eligibility not provided")
        ranked.append({
            **event,
            "score": min(score + 50, 100),
            "reason": f"Matches visible interests and is eligible for age {age}.",
            "eligibility": age_label,
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return {
        "error": False,
        "answer": ranked[:5],
        "sources": [event.get("url") for event in ranked[:5] if event.get("url")],
    }


def query_ollama(user_prompt: str) -> dict[str, Any]:
    base_url = _get_setting("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = _get_setting("OLLAMA_MODEL", "qwen2.5:7b")
    try:
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": (
                    "You are helping a student find hackathons. Only use the supplied event data. "
                    "Never invent events, URLs, dates, or eligibility rules. "
                    "Return a concise ranked Markdown list.\n\n" + user_prompt[:MAX_USER_PROMPT_CHARS]
                ),
                "stream": False,
            },
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response")
        if not isinstance(answer, str) or not answer.strip():
            raise ValueError("Empty Ollama response")
        return {"error": False, "answer": answer, "sources": []}
    except requests.RequestException:
        return {"error": True, "message": "Ollama is unavailable. The app will use the local offline ranking fallback."}
    except ValueError:
        return {"error": True, "message": "Ollama returned an unreadable response."}


def query_backboard_ai(user_prompt: str) -> dict[str, Any]:
    """Use Backboard when configured; otherwise return a transparent local fallback."""
    api_key = _get_setting("BACKBOARD_API_KEY")
    provider = _get_setting("BACKBOARD_LLM_PROVIDER")
    model = _get_setting("BACKBOARD_MODEL_NAME")

    if not api_key:
        return {"error": True, "message": "Backboard is not configured."}
    if not provider or not model:
        return {"error": True, "message": "Set both BACKBOARD_LLM_PROVIDER and BACKBOARD_MODEL_NAME."}

    prompt = (
        "Help the user find hackathons matching their preferences. You do not have live "
        "web browsing, so do not claim event details are current or verified. Do not invent "
        "event names, dates, deadlines, eligibility, costs, or URLs. "
        "Keep the response concise and include source-verification warnings.\n\n"
        f"User request: {user_prompt[:MAX_USER_PROMPT_CHARS]}"
    )

    try:
        response = requests.post(
            "https://app.backboard.io/api/threads/messages",
            headers={"X-API-Key": api_key, "Content-Type": "application/json"},
            json={"content": prompt, "llm_provider": provider, "model_name": model},
            timeout=45,
        )
        if not response.ok:
            print(f"Backboard API returned HTTP {response.status_code}.")
            return {"error": True, "message": f"Backboard request failed (HTTP {response.status_code})."}
        data = response.json()
    except requests.RequestException:
        return {"error": True, "message": "Could not reach Backboard."}
    except ValueError:
        return {"error": True, "message": "Backboard returned an unreadable response."}

    answer = None
    if isinstance(data, dict):
        for key in ("content", "response", "answer", "message", "text"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                answer = value
                break
            if isinstance(value, dict):
                nested = value.get("content") or value.get("text")
                if isinstance(nested, str) and nested.strip():
                    answer = nested
                    break
    if not answer:
        return {"error": True, "message": "Backboard returned an unexpected response."}
    return {"error": False, "answer": answer, "sources": []}


def recommend_hackathons(
    preferences: str,
    age: int,
    provider: str = "local",
) -> dict[str, Any]:
    """Apply deterministic age filtering, then rank matching cached events."""
    if not 13 <= age <= 99:
        return {"error": True, "message": "Enter an age between 13 and 99."}

    all_events = load_hackathons()
    eligible = filter_by_age(all_events, age)
    if not eligible:
        return {
            "error": False,
            "answer": [],
            "sources": [],
            "message": "No verified events in the local dataset match this age.",
        }

    if provider == "backboard":
        compact_events = json.dumps(eligible[:20], ensure_ascii=False)
        prompt = (
            f"Age: {age}\nPreferences: {preferences[:MAX_USER_PROMPT_CHARS]}\n"
            f"Eligible cached events: {compact_events}\n"
            "Rank only events from that list and explain each match in one sentence. "
            "For unknown eligibility or missing official URLs, say verification is required."
        )
        return query_backboard_ai(prompt)

    if provider == "ollama":
        compact_events = json.dumps(eligible[:20], ensure_ascii=False)
        prompt = (
            f"Age: {age}\nPreferences: {preferences[:MAX_USER_PROMPT_CHARS]}\n"
            f"Eligible cached events: {compact_events}\n"
            "Rank no more than five events by the preferences and explain each match. "
            "Only use entries from the supplied data."
        )
        ollama_result = query_ollama(prompt)
        if not ollama_result.get("error"):
            return ollama_result

    return rank_locally(preferences, age, eligible)
