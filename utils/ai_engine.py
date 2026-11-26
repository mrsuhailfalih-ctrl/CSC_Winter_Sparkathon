import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BACKBOARD_API_URL = "https://app.backboard.io/api/v1/chat"


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


def query_backboard_ai(user_prompt: str):
    """Recommend real hackathons relevant to the user's request."""
    api_key = _get_setting("BACKBOARD_API_KEY")
    if not api_key:
        return {
            "error": True,
            "message": "Backboard AI is not configured. Add BACKBOARD_API_KEY to your .env file.",
        }

    api_url = _get_setting("BACKBOARD_API_URL", DEFAULT_BACKBOARD_API_URL)
    prompt = (
        "You are an assistant whose only task is recommending hackathons based on "
        "the user's request. Recommend current, real events that fit. Use web search "
        "when available and prioritize official organizer pages. Never invent event "
        "names, dates, eligibility, costs, or links. For each recommendation, give "
        "the event name, why it fits, dates or registration deadline when verifiable, "
        "and its official link. If you cannot verify a detail, say so. If you cannot "
        "find suitable events, say that instead of suggesting unrelated ones.\n\n"
        f"User request: {user_prompt}"
    )

    try:
        response = requests.post(
            api_url,
            json={"message": prompt, "memory": "Auto", "web_search": "Auto"},
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"Backboard AI error: {exc}")
        return {
            "error": True,
            "message": "Hackathon recommendations are temporarily unavailable. Please try again later.",
        }
    except ValueError as exc:
        print(f"Backboard response parsing error: {exc}")
        return {
            "error": True,
            "message": "The AI service returned an unreadable response. Please try again later.",
        }
