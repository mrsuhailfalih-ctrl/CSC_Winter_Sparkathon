from __future__ import annotations

import re
from datetime import date
from typing import Any
from urllib.parse import urlsplit

MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}
MONTH_PATTERN = "jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?"
DATE_RE = re.compile(
    rf"\b({MONTH_PATTERN})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?"
    rf"(?:\s*(?:-|–|to)\s*(\d{{1,2}})(?:st|nd|rd|th)?)?[,]?\s+(20\d{{2}})\b",
    re.I,
)
ISO_DATE_RE = re.compile(r"\b(20\d{2})-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])\b")
YEAR_MONTH_RE = re.compile(rf"\b({MONTH_PATTERN})\.?\s+(20\d{{2}})\b", re.I)
GENERIC_TITLES = re.compile(
    r"\b(directory|find upcoming|upcoming hackathons?|browse events|boot\s?camp|"
    r"pre-?register|registration page|hackathons? and challenges|competitions, quizzes, hackathons)\b",
    re.I,
)
GENERIC_SLUGS = {"", "hackathons", "events", "search", "browse", "upcoming", "all", "competitions"}
KNOWN_DIRECTORY_HOSTS = {"dev.events", "hack4hack.com", "aiwhatson.com", "mlh.io"}
EVENT_ACTIONS = re.compile(r"\b(register|registration|apply|applications?|prizes?|teams?|submit|challenge)\b", re.I)


def extract_event_dates(text: str) -> list[date]:
    """Extract explicit event dates, including abbreviated months and date ranges."""
    found: set[date] = set()
    covered_spans: list[tuple[int, int]] = []
    for match in DATE_RE.finditer(text):
        month, first_day, last_day, year = match.groups()
        month_number = MONTHS[month.lower().rstrip(".")]
        try:
            found.add(date(int(year), month_number, int(first_day)))
            if last_day:
                found.add(date(int(year), month_number, int(last_day)))
            covered_spans.append(match.span())
        except ValueError:
            continue
    for match in ISO_DATE_RE.finditer(text):
        try:
            found.add(date(int(match.group(1)), int(match.group(2)), int(match.group(3))))
            covered_spans.append(match.span())
        except ValueError:
            continue
    for match in YEAR_MONTH_RE.finditer(text):
        if any(start <= match.start() < end for start, end in covered_spans):
            continue
        month_number = MONTHS[match.group(1).lower().rstrip(".")]
        found.add(date(int(match.group(2)), month_number, 1))
    return sorted(found)


def _topic_words(text: str) -> set[str]:
    ignored = {"and", "the", "for", "with", "from", "that", "this", "any", "are", "you", "your", "want", "looking", "hackathon", "hackathons", "event", "events"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if (len(word) >= 3 or word == "ai") and word not in ignored}


def _is_individual_hackathon(item: dict[str, Any]) -> bool:
    title = str(item.get("name", "")).strip()
    snippet = str(item.get("snippet", ""))
    title_lower = title.lower()
    if GENERIC_TITLES.search(title):
        return False

    try:
        parsed = urlsplit(str(item.get("url", "")))
        host = (parsed.hostname or "").lower().removeprefix("www.")
        path_parts = [part for part in parsed.path.lower().split("/") if part]
    except ValueError:
        host, path_parts = "", []
    slug = path_parts[-1] if path_parts else ""

    # Reject known search directories at their root/category routes, but don't
    # classify an individual event as generic just because its title says
    # "hackathon for ..." or the provider omitted that word from its title.
    if host in KNOWN_DIRECTORY_HOSTS and (not path_parts or slug in GENERIC_SLUGS):
        return False
    if slug in GENERIC_SLUGS and not re.search(r"\bhackathon\b", title_lower):
        return False

    has_event_title = bool(re.search(r"\bhack(?:-a-)?thon\b", title_lower))
    has_event_evidence = bool(re.search(r"\bhack(?:-a-)?thon\b", snippet, re.I) or EVENT_ACTIONS.search(snippet))
    has_specific_route = bool(path_parts and slug not in GENERIC_SLUGS)
    # The upstream search cleaner has already checked that results are event-like.
    # Here we only discard obvious directory/course pages and allow specific
    # event routes whose search title omitted the word "hackathon".
    return has_event_title or (has_specific_route and has_event_evidence)


def _topic_match(item: dict[str, Any], interests: str) -> bool:
    requested = _topic_words(interests)
    if not requested:
        return True
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    available = _topic_words(evidence)
    if "ai" in requested and ("artificial" in available or "intelligence" in available):
        available.add("ai")
    return bool(requested & available)


def filter_event_candidates(
    candidates: list[dict[str, Any]], interests: str, start: date, end: date,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Return dated-in-range and date-unknown individual events; exclude known stale dates."""
    confirmed: list[dict[str, Any]] = []
    possible: list[dict[str, Any]] = []
    rejected_titles: list[str] = []
    diagnostics: dict[str, Any] = {
        "input": len(candidates), "not_individual_event": 0,
        "topic_mismatch": 0, "outside_date_range": 0, "rejected_title_samples": rejected_titles,
    }
    for item in candidates:
        if not _is_individual_hackathon(item):
            diagnostics["not_individual_event"] += 1
            if len(rejected_titles) < 10:
                rejected_titles.append(str(item.get("name", "(untitled)"))[:160])
            continue
        if not _topic_match(item, interests):
            diagnostics["topic_mismatch"] += 1
            continue
        text = f"{item.get('name', '')}. {item.get('snippet', '')}"
        dates = extract_event_dates(text)
        in_range = [event_date for event_date in dates if start <= event_date <= end]
        if in_range:
            item["date_fit"] = True
            item["date_match"] = "Date evidence in search result: " + ", ".join(d.isoformat() for d in in_range)
            confirmed.append(item)
        elif dates or item.get("date_fit") is False:
            diagnostics["outside_date_range"] += 1
        elif item.get("date_fit") is True:
            confirmed.append(item)
        else:
            item["date_fit"] = None
            item["date_match"] = "Event date not found in search snippet—verify on official page"
            possible.append(item)
    return confirmed, possible, diagnostics


def preference_evidence(item: dict[str, Any], details: str) -> list[str]:
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    requested = _topic_words(details)
    status = []
    if requested & {"online", "virtual", "remote"}:
        status.append("Online/virtual: mentioned" if re.search(r"\b(online|virtual|remote|remote-first|anywhere|worldwide)\b", evidence) else "Online/virtual: not confirmed")
    if "free" in requested:
        status.append("Free: mentioned" if re.search(r"\b(free|no cost|without charge|free to enter|free entry)\b", evidence) else "Free: not confirmed")
    return status
