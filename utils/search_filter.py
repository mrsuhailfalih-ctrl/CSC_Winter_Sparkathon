from __future__ import annotations

import re
from typing import Any

# Titles that strongly indicate a collection, directory, calendar, or broad
# search category rather than an individual event.
COLLECTION_TITLE = re.compile(
    r"\b(?:list\s+of\s+\d|\d+\s*\+?\s+(?:open\s+)?(?:online\s+)?hackathons?|"
    r"every\s+hackathon(?:s)?\s+in\s+20\d{2}|"
    r"(?:online|virtual|remote|free|global|upcoming)\s+hackathons?\b|"
    r"hackathons?\s*[—–-]\s*(?:virtual|online|remote)|"
    r"(?:free\s+)?online\s+hackathon\s+events|"
    r"(?:discover|explore|browse)\s+hackathons?\b|"
    r"upcoming\s+.*hackathons?.*\b\d+\s+cities\b|"
    r"hackathons?\s+in\s+\d+\s+cities|"
    r"global\s+hackathons?\s+20\d{4}|"
    r"all\s+hackathons?\b|hackathons?\s+made\s+easy|"
    r"hackathons?\s+and\s+challenges)\b",
    re.IGNORECASE,
)

# Explicit roundup/list cues are not overridden just because the roundup
# mentions deadlines, prizes, or event formats.
STRONG_ROUNDUP = re.compile(
    r"\b(?:list\s+of\s+\d|\d{2,}\s+(?:open\s+)?hackathons?|"
    r"every\s+hackathon(?:s)?\s+in\s+20\d{2}|"
    r"every\s+hackathon\s+happening|"
    r"filterable\s+by|filter\s+by\s+(?:deadline|format|region)|"
    r"\d+\s+online\s+and\s+virtual\s+hackathons?|"
    r"hackathons?\s+in\s+\d+\s+cities|"
    r"(?:bond's|our|my)\s+picks|"
    r"including\s+online\s+and\s+virtual\s+events|"
    r"discover\s+hackathons?\s+on\s+[\w.-]+)",
    re.IGNORECASE,
)

EVENT_DETAIL_PATTERNS = (
    re.compile(r"\b\d{1,3}\s*[- ]?hour\b", re.I),
    re.compile(r"\b(?:teams?\s+of\s+\d|teams?\s+(?:will|can|build)|build(?:ers)?\s+(?:will|can)\s+make)\b", re.I),
    re.compile(r"\b(?:participants?|builders?)\s+aged?\s+\d{1,2}\s*[-–to]+\s*\d{1,2}\b", re.I),
    re.compile(r"\b(?:deadline|finals?|kickoff|starts?\s+on|takes?\s+place)\s*:?\s*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|\d{4}-\d{2}-\d{2})", re.I),
    re.compile(r"\$\s?\d[\d,]*(?:\.\d{2})?\s*(?:in\s+)?(?:prizes?|prize\s+pool)?", re.I),
    re.compile(r"\b(?:register|registration|apply|applications?\s+open)\b", re.I),
    re.compile(r"\b(?:finals?|final\s+round)\s+(?:in|at)\s+[A-Z]", re.I),
)


def is_unnecessary_search_result(item: dict[str, Any]) -> bool:
    """Return True for broad directories/roundups, but retain individual events."""
    title = str(item.get("title", ""))
    snippet = str(item.get("snippet", item.get("description", "")))
    combined = f"{title}. {snippet}"

    if STRONG_ROUNDUP.search(combined):
        return True
    if not COLLECTION_TITLE.search(title):
        return False

    # Some real events use generic platform titles (for example, "All Hackathons").
    # Keep those only when the snippet contains multiple concrete event details.
    specific_details = sum(bool(pattern.search(snippet)) for pattern in EVENT_DETAIL_PATTERNS)
    return specific_details < 2


def filter_search_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove obvious directory/listicle results while preserving Serper fields."""
    return [item for item in results if isinstance(item, dict) and not is_unnecessary_search_result(item)]
