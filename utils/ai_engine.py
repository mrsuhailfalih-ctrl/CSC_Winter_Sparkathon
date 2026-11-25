import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKBOARD_API_KEY = os.getenv("BACKBOARD_API_KEY")
BACKBOARD_API_URL = os.getenv(
    "BACKBOARD_API_URL",
    "https://app.backboard.io/api/v1/chat",
)


def query_backboard_ai(user_prompt: str, user_profile: dict, thread_id: str = None):
    """Call Backboard AI or return a local fallback when unavailable."""
    if not BACKBOARD_API_KEY:
        return {
            "error": True,
            "message": (
                "Backboard AI is not configured. Using the local offline "
                "hackathon and teammate database."
            ),
        }

    headers = {
        "Authorization": f"Bearer {BACKBOARD_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "message": (
            f"Student profile: {user_profile}. "
            f"Request: {user_prompt}. "
            "Return concise recommendations, an idea, and suggested next steps."
        ),
        "memory": "Auto",
        "web_search": "Auto",
    }
    if thread_id:
        payload["thread_id"] = thread_id

    try:
        response = requests.post(
            BACKBOARD_API_URL,
            json=payload,
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        print(f"AI Error: {exc}")
        return {
            "error": True,
            "message": (
                "The AI service is temporarily unavailable. "
                "Using the local offline hackathon database."
            ),
        }
