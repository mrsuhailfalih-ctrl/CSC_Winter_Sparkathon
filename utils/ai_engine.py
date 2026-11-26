import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKBOARD_MESSAGE_URL = "https://app.backboard.io/api/threads/messages"
MAX_USER_PROMPT_CHARS = 2000


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


def query_backboard_ai(user_prompt: str) -> dict:
    """Use Backboard to suggest hackathons, with an explicitly selected model."""
    api_key = _get_setting("BACKBOARD_API_KEY")
    provider = _get_setting("BACKBOARD_LLM_PROVIDER")
    model = _get_setting("BACKBOARD_MODEL_NAME")

    if not api_key:
        return {
            "error": True,
            "message": "Backboard is not configured. Add BACKBOARD_API_KEY to your local .env file.",
        }
    if not provider or not model:
        return {
            "error": True,
            "message": (
                "Choose a model in your Backboard dashboard and set both "
                "BACKBOARD_LLM_PROVIDER and BACKBOARD_MODEL_NAME in .env."
            ),
        }

    prompt = (
        "Help the user find hackathons matching their preferences. You do not have live "
        "web browsing, so do not claim event details are current or verified. Do not invent "
        "event names, dates, deadlines, eligibility, costs, or URLs. If you cannot confidently "
        "verify a specific event, say so and provide useful search terms or official platforms. "
        "Keep the response concise.\n\n"
        f"User request: {user_prompt[:MAX_USER_PROMPT_CHARS]}"
    )

    try:
        response = requests.post(
            BACKBOARD_MESSAGE_URL,
            headers={
                "X-API-Key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "content": prompt,
                "llm_provider": provider,
                "model_name": model,
            },
            timeout=45,
        )
        if not response.ok:
            # Avoid logging response bodies or request details that may contain sensitive data.
            print(f"Backboard API returned HTTP {response.status_code}.")
            return {
                "error": True,
                "message": (
                    f"Backboard request failed (HTTP {response.status_code}). Check your API key, "
                    "provider/model selection, and account credits."
                ),
            }
        data = response.json()
    except requests.RequestException:
        return {
            "error": True,
            "message": "Could not reach Backboard. Check your internet connection and try again.",
        }
    except ValueError:
        return {
            "error": True,
            "message": "Backboard returned an unreadable response. Please try again.",
        }

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
    elif isinstance(data, str) and data.strip():
        answer = data

    if not answer:
        return {
            "error": True,
            "message": "Backboard returned an unexpected response. Please check the API setup and try again.",
        }

    return {"error": False, "answer": answer, "sources": []}
