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
    """Use Gemini to suggest hackathons without requiring web-search support."""
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
        "You are an assistant that helps users find hackathons matching their request. "
        "You do not have live web browsing, so do not claim you searched the web or that "
        "event details are current or verified. Do not invent event names, dates, deadlines, "
        "eligibility, costs, or URLs. If you are not confident a particular event and its "
        "details are real, say you cannot verify current listings and give useful search "
        "terms or official event platforms to check instead. If the user provides event "
        "links or details, help compare them against the user's preferences and clearly "
        "identify anything that still needs checking. Be concise and explain why suggestions fit.\n\n"
        f"User request: {user_prompt}"
    )
    url = f"{GEMINI_API_BASE_URL}/{model}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=60,
        )
        if not response.ok:
            # Do not log the request URL: it contains the API key query parameter.
            print(f"Gemini API returned HTTP {response.status_code}.")
            return {
                "error": True,
                "message": (
                    f"Gemini request failed (HTTP {response.status_code}). Check your model ID, "
                    "API key, and AI Studio quota."
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

    parts = candidates[0].get("content", {}).get("parts", [])
    answer = "\n".join(part["text"] for part in parts if part.get("text"))
    if not answer.strip():
        return {
            "error": True,
            "message": "Gemini returned no text recommendation. Please try again.",
        }

    return {"error": False, "answer": answer, "sources": []}
