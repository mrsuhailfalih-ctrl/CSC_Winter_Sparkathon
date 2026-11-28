from __future__ import annotations

import re
from datetime import date
from typing import Any

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}
MONTH_PATTERN = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
MONTH_DATE = re.compile(
    rf"\b({MONTH_PATTERN})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?"
    rf"(?:\s*(?:-|–|to)\s*(\d{{1,2}})(?:st|nd|rd|th)?)?[,]?\s+(20\d{{2}})\b",
    re.I,
)
ISO_DATE = re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b")

COLLECTION_TITLE = re.compile(
    r"\b(?:list\s+of\s+\d|\d+\s*\+?\s+(?:open\s+)?(?:online\s+)?hackathons?|"
    r"every\s+hackathon(?:s)?\s+in\s+20\d{2}|(?:online|virtual|remote|free|global|upcoming)\s+hackathons?\b|"
    r"hackathons?\s*[—–-]\s*(?:virtual|online|remote)|(?:free\s+)?online\s+hackathon\s+events|"
    r"(?:discover|explore|browse)\s+hackathons?\b|hackathons?\s+in\s+\d+\s+cities|"
    r"global\s+hackathons?\s+20\d{2}|all\s+hackathons?\b|hackathons?\s+made\s+easy)", re.I,
)
STRONG_ROUNDUP = re.compile(
    r"\b(?:list\s+of\s+\d|\d{2,}\s+(?:open\s+)?hackathons?|every\s+hackathon(?:s)?\s+(?:in|happening)|"
    r"filterable\s+by|filter\s+by\s+(?:deadline|format|region)|\d+\s+online\s+and\s+virtual\s+hackathons?|"
    r"hackathons?\s+in\s+\d+\s+cities|(?:bond's|our|my)\s+picks|discover\s+hackathons?\s+on\s+[\w.-]+)", re.I,
)

# Search-engine dates commonly describe publication or registration deadlines,
# not when the event itself takes place. Do not use them to satisfy the date filter.
NON_EVENT_DATE_CONTEXT = re.compile(
    r"\b(?:published|posted|updated|modified|last\s+crawled|registration\s+deadline|"
    r"application\s+deadline|applications?\s+close|register\s+by|apply\s+by|deadline)\b", re.I,
)
EVENT_DATE_CONTEXT = re.compile(
    r"\b(?:hackathon|event|competition|event\s+dates?|hackathon\s+dates?|hackathon\s+period|"
    r"event\s+period|competition\s+period|runs?|takes?\s+place|held|kickoff|starts?|will\s+be)\b", re.I,
)


def _nearby_context(text: str, start: int, end: int, radius: int = 100) -> str:
    return text[max(0, start - radius):min(len(text), end + radius)]


def _event_date_ranges(text: str) -> list[tuple[date, date]]:
    """Extract year-qualified dates only when nearby text links them to an event schedule."""
    candidates: list[tuple[date, date]] = []
    occupied: list[tuple[int, int]] = []
    for match in MONTH_DATE.finditer(text):
        context = _nearby_context(text, *match.span())
        if NON_EVENT_DATE_CONTEXT.search(context) or not EVENT_DATE_CONTEXT.search(context):
            continue
        month_name, first_day, last_day, year = match.groups()
        try:
            first = date(int(year), MONTHS[month_name.lower().rstrip(".")], int(first_day))
            last = date(int(year), MONTHS[month_name.lower().rstrip(".")], int(last_day or first_day))
        except (KeyError, ValueError):
            continue
        candidates.append((first, last))
        occupied.append(match.span())

    for match in ISO_DATE.finditer(text):
        if any(a <= match.start() < b for a, b in occupied):
            continue
        context = _nearby_context(text, *match.span())
        if NON_EVENT_DATE_CONTEXT.search(context) or not EVENT_DATE_CONTEXT.search(context):
            continue
        try:
            value = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            continue
        candidates.append((value, value))
    return candidates


def extract_explicit_dates(text: str) -> list[date]:
    """Compatibility helper: return dates with explicit years, irrespective of context."""
    found: set[date] = set()
    for match in MONTH_DATE.finditer(text):
        month, day, last_day, year = match.groups()
        try:
            found.add(date(int(year), MONTHS[month.lower().rstrip(".")], int(day)))
            if last_day:
                found.add(date(int(year), MONTHS[month.lower().rstrip(".")], int(last_day)))
        except (KeyError, ValueError):
            pass
    for match in ISO_DATE.finditer(text):
        try:
            found.add(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
        except ValueError:
            pass
    return sorted(found)


def is_unnecessary_search_result(item: dict[str, Any]) -> bool:
    title = str(item.get("title", ""))
    snippet = str(item.get("snippet", item.get("description", "")))
    combined = f"{title}. {snippet}"
    if STRONG_ROUNDUP.search(combined):
        return True
    if not COLLECTION_TITLE.search(title):
        return False
    return not bool(re.search(r"\b(?:teams?\s+of|event\s+period|hackathon\s+period|finals?|register|registration|prize|participants?|aged?\s+\d)\b", snippet, re.I))


def filter_search_results(
    results: list[dict[str, Any]], start: date | None = None, end: date | None = None,
) -> list[dict[str, Any]]:
    """Filter collections and (strictly) keep only date-evidenced events in range.

    Only the result title/snippet are inspected: result URLs are never fetched. Dates
    from Serper's `date` field are ignored because those are indexing/publication dates.
    Results with no unambiguous event-schedule date are omitted when a range is selected.
    """
    output: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict) or is_unnecessary_search_result(item):
            continue
        row = dict(item)
        if start is not None and end is not None:
            if start > end:
                raise ValueError("The start date must be on or before the latest date.")
            snippet = str(row.get("snippet", row.get("description", "")))
            ranges = _event_date_ranges(snippet)
            if not ranges:
                continue
            # Fail closed when snippets contain conflicting schedule dates. This avoids
            # admitting stale editions just because another unrelated date matches.
            if any(last < start or first > end for first, last in ranges):
                continue
            row["date_verification"] = {
                "status": "snippet_match",
                "dates": sorted({value.isoformat() for first, last in ranges for value in (first, last)}),
                "note": "An event-related date in the search snippet overlaps the selected range; verify on organizer page.",
            }
        output.append(row)
    return output
