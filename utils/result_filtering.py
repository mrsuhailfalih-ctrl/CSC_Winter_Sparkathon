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
DATE_RE = re.compile(rf"\b({MONTH_PATTERN})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:\s*(?:-|–|to)\s*(\d{{1,2}})(?:st|nd|rd|th)?)?[,]?\s+(20\d{{2}})\b", re.I)
ISO_DATE_RE = re.compile(r"\b(20\d{2})-(0?[1-9]|1[0-2])-(0?[1-9]|[12]\d|3[01])\b")
YEAR_MONTH_RE = re.compile(rf"\b({MONTH_PATTERN})\.?\s+(20\d{{2}})\b", re.I)
GENERIC_TITLES = re.compile(r"\b(directory|browse events|hackathon guide|upcoming hackathons?|hackathons? list|boot\s?camp|tutorial|how to build)\b", re.I)
EVENT_WORDS = re.compile(r"\b(hack(?:-a-)?thon|buildathon|coding challenge|innovation challenge|competition|sprint|jam|makeathon)\b", re.I)
EVENT_EVIDENCE = re.compile(r"\b(register|registration|apply|applications?|prizes?|teams?|submit|join|deadline|build|challenge|competition)\b", re.I)
ONLINE_WORDS = re.compile(r"\b(online|virtual|remote|remote-first|anywhere|worldwide)\b", re.I)
IN_PERSON_WORDS = re.compile(r"\b(in[ -]?person|onsite|on[ -]site|physical venue|at the venue|held in|located in)\b", re.I)


def extract_event_dates(text: str) -> list[date]:
    """Extract explicit dates from a title/snippet, tolerating common formats."""
    found: set[date] = set()
    covered_spans: list[tuple[int, int]] = []
    for match in DATE_RE.finditer(text):
        month, first_day, last_day, year = match.groups()
        try:
            month_number = MONTHS[month.lower().rstrip(".")]
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
        if any(begin <= match.start() < finish for begin, finish in covered_spans):
            continue
        try:
            found.add(date(int(match.group(2)), MONTHS[match.group(1).lower().rstrip(".")], 1))
        except ValueError:
            continue
    return sorted(found)


def _topic_words(text: str) -> set[str]:
    ignored = {"and", "the", "for", "with", "from", "that", "this", "any", "are", "you", "your", "want", "looking", "hackathon", "hackathons", "event", "events"}
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if (len(word) >= 3 or word == "ai") and word not in ignored}


def _is_individual_hackathon(item: dict[str, Any]) -> bool:
    """Reject obvious guides/directories, but keep plausible event pages generously."""
    title = str(item.get("name", "")).strip()
    snippet = str(item.get("snippet", ""))
    if not title or GENERIC_TITLES.search(title):
        return False
    try:
        parsed = urlsplit(str(item.get("url", "")))
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            return False
        path_parts = [part for part in parsed.path.lower().split("/") if part]
    except ValueError:
        return False

    title_and_snippet = f"{title} {snippet}"
    # Serper's query already asks for hackathons; accept event synonyms and specific
    # event-looking routes even when the snippet itself omits the word hackathon.
    has_event_language = bool(EVENT_WORDS.search(title_and_snippet))
    has_event_action = bool(EVENT_EVIDENCE.search(title_and_snippet))
    has_specific_page = bool(path_parts and path_parts[-1] not in {"hackathons", "events", "search", "browse", "upcoming", "all"})
    if not path_parts and not has_event_language:
        return False
    return has_event_language or (has_specific_page and has_event_action)


def _topic_match(item: dict[str, Any], interests: str) -> bool:
    requested = _topic_words(interests)
    if not requested:
        return True
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    available = _topic_words(evidence)
    if "ai" in requested and ("artificial" in available or "intelligence" in available):
        available.add("ai")
    # Partial term matches are sufficient. If the result has no topic evidence,
    # retain it as an unconfirmed candidate instead of silently filtering it out.
    return not available or bool(requested & available)


def _age_status(item: dict[str, Any], age: int | None) -> tuple[str, bool]:
    if age is None:
        return "Not checked — check official rules", True
    text = f"{item.get('name', '')} {item.get('snippet', '')}"
    lower = text.lower()
    min_match = re.search(r"(?:minimum age(?: is)?|ages?\s*|must be at least\s*|18\+|21\+)\s*(\d{1,2})", lower)
    max_match = re.search(r"under\s*(\d{1,2})|ages?\s*(\d{1,2})\s*(?:and under|or younger)", lower)
    minimum = int(min_match.group(1)) if min_match else None
    maximum = int(max_match.group(1)) if max_match else None
    if minimum is not None and age < minimum:
        return f"May not meet stated minimum age ({minimum}+); verify with organizer", False
    if maximum is not None and age > maximum:
        return f"May exceed stated age limit (under {maximum}); verify with organizer", False
    if minimum is not None or maximum is not None:
        return "Age rule appears compatible in snippet; confirm official rules", True
    return "Not confirmed — check official age rules and parental-consent requirements", True


def _format_status(item: dict[str, Any], requested: str) -> tuple[str, bool]:
    text = f"{item.get('name', '')} {item.get('snippet', '')}"
    online = bool(ONLINE_WORDS.search(text))
    in_person = bool(IN_PERSON_WORDS.search(text))
    if requested == "Any":
        if online and in_person:
            return "Hybrid / multiple formats mentioned", True
        if online:
            return "Online/virtual mentioned", True
        if in_person:
            return "In-person mentioned", True
        return "Not confirmed — check official page", True
    if requested == "Online" and in_person and not online:
        return "Snippet suggests in-person; verify before applying", False
    if requested == "In-person" and online and not in_person:
        return "Snippet suggests online; verify before applying", False
    if requested == "Online" and online:
        return "Online/virtual mentioned", True
    if requested == "In-person" and in_person:
        return "In-person mentioned", True
    return "Format not stated — kept as a possible match", True


def filter_event_candidates(
    candidates: list[dict[str, Any]],
    interests: str,
    start: date,
    end: date,
    age: int | None = None,
    event_format: str = "Any",
    details: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Keep plausible/unknown candidates; discard only clear mismatches."""
    confirmed: list[dict[str, Any]] = []
    possible: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {
        "input": len(candidates), "not_individual_event": 0,
        "topic_mismatch": 0, "outside_date_range": 0,
        "age_conflict": 0, "format_conflict": 0,
    }
    for original in candidates:
        item = dict(original)
        if not _is_individual_hackathon(item):
            diagnostics["not_individual_event"] += 1
            continue
        if not _topic_match(item, f"{interests} {details}"):
            diagnostics["topic_mismatch"] += 1
            continue

        age_status, age_compatible = _age_status(item, age)
        item["age_status"] = age_status
        if not age_compatible:
            diagnostics["age_conflict"] += 1
            continue

        format_status, format_compatible = _format_status(item, event_format)
        item["format_status"] = format_status
        if not format_compatible:
            diagnostics["format_conflict"] += 1
            continue

        dates = extract_event_dates(f"{item.get('name', '')}. {item.get('snippet', '')}")
        in_range = [event_date for event_date in dates if start <= event_date <= end]
        if in_range:
            item["date_fit"] = True
            item["date_match"] = "Date evidence in range: " + ", ".join(value.isoformat() for value in in_range) + " (verify on official page)"
            confirmed.append(item)
        elif dates:
            diagnostics["outside_date_range"] += 1
            # Search snippets can show registration/deadline dates rather than event
            # dates. Preserve as a lower-confidence possibility rather than dropping.
            item["date_fit"] = False
            item["date_match"] = "Snippet date appears outside requested range; confirm actual event dates"
            possible.append(item)
        else:
            item["date_fit"] = None
            item["date_match"] = "No event date found in snippet — verify requested dates on official page"
            possible.append(item)
    return confirmed, possible, diagnostics


def preference_evidence(item: dict[str, Any], details: str) -> list[str]:
    evidence = f"{item.get('name', '')} {item.get('snippet', '')}".lower()
    requested = _topic_words(details)
    status = []
    if requested & {"online", "virtual", "remote"}:
        status.append("Online/virtual: mentioned" if ONLINE_WORDS.search(evidence) else "Online/virtual: not confirmed")
    if "free" in requested:
        status.append("Free: mentioned" if re.search(r"\b(free|no cost|without charge|free to enter|free entry)\b", evidence) else "Free: not confirmed")
    return status
