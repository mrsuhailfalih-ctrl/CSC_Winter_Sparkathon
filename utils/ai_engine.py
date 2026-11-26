import os

import requests
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


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


def query_gemini_ai(user_prompt: str) -> dict:
    """Use Gemini, with Google Search grounding, to recommend hackathons."""
    api_key = _get_setting("GEMINI_API_KEY")
    model = _get_setting("GEMINI_MODEL")

    if not api_key:
        return {
            "error": True,
            "message": "Gemini is not configured. Add GEMINI_API_KEY to your local .env file.",
        }
    if not model:
        return {
            "error": True,
            "message": (
                "Gemini model is not configured. Add GEMINI_MODEL using a model ID "
                "available to your Google AI Studio API key."
            ),
        }

    prompt = (
        "You are an assistant whose only task is recommending hackathons based on "
        "the user's request. Use Google Search to find current, real events. Prefer "
        "official organizer pages. Never invent event names, dates, eligibility, costs, "
        "or links. Recommend only events that fit. For each, include the event name, "
        "why it fits, dates or registration deadline when verifiable, and official link. "
        "Say when a detail cannot be verified. If you cannot find suitable events, say so.\n\n"
        f"User request: {user_prompt}"
    )
    url = f"{GEMINI_API_BASE_URL}/{model}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "tools": [{"google_search": {}}],
            },
            timeout=60,
        )
        if not response.ok:
            # Do not log the request URL: it contains the API key query parameter.
            print(f"Gemini API returned HTTP {response.status_code}.")
            return {
                "error": True,
                "message": (
                    f"Gemini request failed (HTTP {response.status_code}). Check that "
                    "the model ID is available to your key and that Google Search grounding "
                    "is supported for it."
                ),
            }
        data = response.json()
    except requests.RequestException:
        return {
            "error": True,
            "message": "Could not reach Gemini. Check your internet connection and try again.",
        }
    except ValueError:
        return {
            "error": True,
            "message": "Gemini returned an unreadable response. Please try again.",
        }

    candidates = data.get("candidates", [])
    if not candidates:
        return {
            "error": True,
            "message": "Gemini did not return a recommendation. Try rephrasing your request.",
        }

    candidate = candidates[0]
    parts = candidate.get("content", {}).get("parts", [])
    answer = "\n".join(part["text"] for part in parts if part.get("text"))
    if not answer.strip():
        return {
            "error": True,
            "message": "Gemini returned no text recommendation. Please try again.",
        }

    sources = []
    metadata = candidate.get("groundingMetadata", {})
    for chunk in metadata.get("groundingChunks", []):
        web = chunk.get("web", {})
        source_url = web.get("uri")
        if source_url and not any(item["url"] == source_url for item in sources):
            sources.append({"title": web.get("title") or source_url, "url": source_url})

    return {"error": False, "answer": answer, "sources": sources}
