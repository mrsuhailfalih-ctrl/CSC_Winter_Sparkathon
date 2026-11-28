from __future__ import annotations

import re
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any

import requests

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

COLLECTION_TITLE = re.compile(
    r"\b(?:list\s+of\s+\d|\d+\s*\+?\s+(?:open\s+)?(?:online\s+)?hackathons?|"
    r"every\s+hackathon(?:s)?\s+in\s+20\d{2}|(?:online|virtual|remote|free|global|upcoming)\s+hackathons?\b|"
    r"hackathons?\s*[—–-]\s*(?:virtual|online|remote)|(?:free\s+)?online\s+hackathon\s+events|"
    r"(?:discover|explore|browse)\s+hackathons?\b|hackathons?\s+in\s+\d+\s+cities|"
    r"global\s+hackathons?\s+20\d{2}|all\s+hackathons?\b|hackathons?\s+made\s+easy)",
    re.I,
)

STRONG_ROUNDUP = re.compile(
    r"\b(?:list\s+of\s+\d|\d{2,}\s+(?:open\s+)?hackathons?|every\s+hackathon(?:s)?\s+(?:in|happening)|"
    r"filterable\s+by|filter\s+by\s+(?:deadline|format|region)|\d+\s+online\s+and\s+virtual\s+hackathons?|"
    r"hackathons?\s+in\s+\d+\s+cities|(?:bond's|our|my)\s+picks|discover\s+hackathons?\s+on\s+[\w.-]+)",
    re.I,
)

MONTH_DATE = re.compile(
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|"
    r"Aug(?:ust)?|Sep(?:tember)?|Sept(?:ember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\.?"
    r"\s+(\d{1,2})(?:st|nd|rd|th)?(?:\s*(?:-|–|to)\s*(\d{1,2})(?:st|nd|rd|th)?)?,?\s+(20\d{2})\b",
    re.I,
)
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b")


class _TextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []

    def handle_data(self, data: str) -> None:
        value = re.sub(r"\s+", " ", data).strip()
        if value:
            self.text.append(value)


def extract_explicit_dates(text: str) -> list[date]:
    """Extract only explicit, year-qualified dates; never interpret publication dates."""
    found: set[date] = set()
    for match in MONTH_DATE.finditer(text):
        month_name, start_day, end_day, year = match.groups()
        try:
            found.add(date(int(year), MONTHS[month_name.lower().rstrip(".")], int(start_day)))
            if end_day:
                found.add(date(int(year), MONTHS[month_name.lower().rstrip(".")], int(end_day)))
        except (KeyError, ValueError):
            pass
    for match in ISO_DATE.finditer(text):
        try:
            found.add(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            pass
    return sorted(found)


def verify_source_dates(url: str, start: date, end: date) -> dict[str, Any]:
    """Fetch a result's source page and look for explicit event dates in its HTML/JSON-LD."""
    if not isinstance(url, str) or not url.lower().startswith("https://"):
        return {"status": "unverified", "dates": [], "reason": "No HTTPS source URL"}
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "HackathonFinder/1.0 (date verification; contact repository owner)"},
            timeout=(4, 10),
            allow_redirects=True,
        )
        response.raise_for_status()
        parser = _TextParser()
        parser.feed(response.text[:2_000_000])
        dates = extract_explicit_dates(" ".join(parser.text) + " " + response.text)
        in_range = [value for value in dates if start <= value <= end]
        if in_range:
            return {"status": "verified", "dates": in_range, "reason": "Explicit dates found on source page"}
        if dates:
            return {"status": "outside_range", "dates": dates, "reason": "Source page dates are outside the requested range"}
        return {"status": "unverified", "dates": [], "reason": "No explicit year-qualified event dates found on source page"}
    except requests.RequestException:
        return {"status": "unverified", "dates": [], "reason": "Source page could not be fetched"}


def is_unnecessary_search_result(item: dict[str, Any]) -> bool:
    title = str(item.get("title", ""))
    snippet = str(item.get("snippet", item.get("description", "")))
    combined = f"{title}. {snippet}"
    if STRONG_ROUNDUP.search(combined):
        return True
    if not COLLECTION_TITLE.search(title):
        return False
    event_detail = re.search(r"\b(?:teams?\s+of|deadline|finals?|register|registration|prize|participants?|aged?\s+\d)", snippet, re.I)
    return not bool(event_detail)


def filter_search_results(results: list[dict[str, Any]], start: date | None = None, end: date | None = None) -> list[dict[str, Any]]:
    """Hide broad pages and, when a range is supplied, hide results outside it.

    Unknown dates are retained and clearly marked; snippets/search-index `date` fields
    are never used as proof of event timing. Confirmed source-page dates outside the
    range are removed. Source verification failures remain unverified rather than discarded.
    """
    filtered: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict) or is_unnecessary_search_result(item):
            continue
        row = dict(item)
        if start is not None and end is not None:
            verification = verify_source_dates(str(row.get("link", "")), start, end)
            row["date_verification"] = verification
            if verification["status"] == "outside_range":
                continue
        filtered.append(row)
    return filtered
