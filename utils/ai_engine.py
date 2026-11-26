import os

import requests
from dotenv import load_dotenv

load_dotenv()

DEFAULT_BACKBOARD_API_URL = "https://app.backboard.io/api/v1/chat"


def _get_setting(name: str, default: str = "") -> str:
    """Read local environment values or Streamlit-hosted secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st

        return str(st.secrets.get(name, default))
    except Exception:
        return default


def query_backboard_ai(user_prompt: str, preferences: dict, thread_id: str = None):
    """Ask Backboard to find and summarize hackathons matching the request."""
    api_key = _get_setting("BACKBOARD_API_KEY")
    if not api_key:
        return {
            "error": True,
            "message": (
                "Backboard AI is not configured. You can still browse and filter "
                "the illustrative sample listings below."
            ),
        }

    api_url = _get_setting("BACKBOARD_API_URL", DEFAULT_BACKBOARD_API_URL)
    prompt = (
        "Act as a hackathon discovery assistant. Find current, real hackathons "
        "that fit the request. Prefer official organizer pages and use web search "
        "when available. Do not invent events, dates, eligibility, prices, or URLs. "
        "For each result, provide the event name, official source link, dates and "
        "registration deadline (or say if not listed), location/format, eligibility, "
        "cost, relevant themes, and a short explanation of fit. Clearly state when "
        "a detail cannot be verified. Keep the answer concise.\n\n"
        f"Preferences: {preferences}\n"
        f"Request: {user_prompt}"
    )
    payload = {
        "message": prompt,
        "memory": "Auto",
        "web_search": "Auto",
    }
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        response = requests.post(
            api_url,
            json=payload,
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
            "message": (
                "Backboard could not complete the search. Check your API settings "
                "and try again; the sample listings remain available."
            ),
        }
