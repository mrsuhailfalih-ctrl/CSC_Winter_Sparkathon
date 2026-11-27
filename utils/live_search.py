from __future__ import annotations

from datetime import date
from typing import Any
from urllib.parse import quote_plus

# These are official platform browse pages, not third-party search-result URLs.
# We deliberately do not scrape the pages: the platforms do not share one public,
# unauthenticated event-search API, and their page structures/search rules differ.
OFFICIAL_EVENT_SOURCES = (
    {"name": "Devpost", "url": "https://devpost.com/hackathons", "note": "Hackathon listings and project challenges"},
    {"name": "Devfolio", "url": "https://devfolio.co/hackathons", "note": "Hackathon listings"},
    {"name": "Major League Hacking (MLH)", "url": "https://mlh.io/seasons", "note": "MLH seasons and events"},
    {"name": "Unstop", "url": "https://unstop.com/hackathons", "note": "Hackathons and student competitions"},
    {"name": "Eventbrite", "url": "https://www.eventbrite.com/d/online/hackathon/", "note": "Event listings; check organizer and event details"},
    {"name": "Luma", "url": "https://lu.ma/discover", "note": "Community events; search for hackathons"},
)


def get_official_sources(interests: str, details: str, start: date, end: date) -> list[dict[str, Any]]:
    """Return official event-platform destinations and a reusable search phrase.

    This is intentionally a source directory rather than fabricated live results:
    the listed platforms do not expose a common public search API for app use.
    """
    topic = " ".join(part.strip() for part in (interests, details) if part and part.strip())
    phrase = f"{topic} hackathon {start.isoformat()} to {end.isoformat()}".strip()
    return [
        {**source, "search_phrase": phrase, "search_phrase_encoded": quote_plus(phrase)}
        for source in OFFICIAL_EVENT_SOURCES
    ]


def find_hackathons(interests: str, details: str, start_date: date, end_date: date, **_: Any) -> dict[str, Any]:
    """Compatibility entry point. Returns source links, never third-party SERP results."""
    if start_date > end_date:
        raise ValueError("The start date must be on or before the latest date.")
    return {
        "error": False,
        "results": [],
        "sources": get_official_sources(interests, details, start_date, end_date),
        "search_available": True,
        "message": "Search these official event-platform pages directly. Dates and eligibility must be checked on each event's organizer page.",
        "search_diagnostics": {"search_method": "official_platform_links_only", "third_party_search_used": False},
        "ai_available": False,
        "ai_message": "AI ranking is not used for source browsing.",
    }
