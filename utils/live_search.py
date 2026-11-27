from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

PLATFORMS = (
    {"name": "Devpost", "hosts": ("devpost.com",), "browse_url": "https://devpost.com/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "Devfolio", "hosts": ("devfolio.co",), "browse_url": "https://devfolio.co/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "MLH", "hosts": ("mlh.io", "events.mlh.io"), "browse_url": "https://mlh.io/seasons", "paths": (r"^/events/[^/]+/?$", r"^/seasons/\d{4}/events/[^/]+/?$",)},
    {"name": "Unstop", "hosts": ("unstop.com",), "browse_url": "https://unstop.com/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "Eventbrite", "hosts": ("eventbrite.com",), "browse_url": "https://www.eventbrite.com/d/online/hackathon/", "paths": (r"^/e/[^/]+/?$",)},
    {"name": "Luma", "hosts": ("lu.ma", "luma.com"), "browse_url": "https://lu.ma/discover", "paths": (r"^/[^/]+/?$",)},
)
MAX_EVENT_PAGES_PER_PLATFORM = 20
MAX_PAGE_BYTES = 2_000_000
REQUEST_TIMEOUT = (3, 8)
MONTHS = {name.lower(): number for number, names in enumerate((
    ("January", "Jan"), ("February", "Feb"), ("March", "Mar"), ("April", "Apr"),
    ("May",), ("June", "Jun"), ("July", "Jul"), ("August", "Aug"),
    ("September", "Sep"), ("October", "Oct"), ("November", "Nov"), ("December", "Dec"),
), 1) for name in names}


class _PageParser(HTMLParser):
    """Collect only public page metadata, links, visible text, and Event JSON-LD."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[dict[str, str]] = []
        self.jsonld: list[str] = []
        self.meta: dict[str, str] = {}
        self.title = ""
        self.text: list[str] = []
        self._in_jsonld = False
        self._script_parts: list[str] = []
        self._in_title = False
        self._anchor: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value for key, value in attrs}
        tag = tag.lower()
        if tag == "a" and attributes.get("href"):
            self._anchor = {"href": str(attributes["href"]), "text": ""}
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name") or attributes.get("itemprop")
            content = attributes.get("content")
            if key and content:
                self.meta[str(key).lower()] = str(content)
        if tag == "title":
            self._in_title = True
        if tag == "script" and "ld+json" in str(attributes.get("type", "")).lower():
            self._in_jsonld = True
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        self.text.append(text)
        if self._in_title:
            self.title += text + " "
        if self._anchor is not None:
            self._anchor["text"] += text + " "
        if self._in_jsonld:
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "a" and self._anchor is not None:
            self._anchor["text"] = re.sub(r"\s+", " ", self._anchor["text"]).strip()
            self.links.append(self._anchor)
            self._anchor = None
        if tag == "title":
            self._in_title = False
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._script_parts))
            self._in_jsonld = False
            self._script_parts = []


def _platform_for_url(url: str) -> dict[str, Any] | None:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().removeprefix("www.")
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return None
    for platform in PLATFORMS:
        if any(host == domain or host.endswith("." + domain) for domain in platform["hosts"]):
            return platform
    return None


def _is_event_url(url: str, platform: dict[str, Any]) -> bool:
    try:
        parsed = urlsplit(url)
    except ValueError:
        return False
    return _platform_for_url(url) == platform and any(re.search(pattern, parsed.path, re.I) for pattern in platform["paths"])


def _fetch_page(url: str, platform: dict[str, Any]) -> tuple[str | None, str | None]:
    if _platform_for_url(url) != platform:
        return None, "outside_platform_allowlist"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "HackathonFinder/1.0 (public event discovery; contact repository owner)"},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
        if response.is_redirect:
            return None, "redirect_not_followed"
        response.raise_for_status()
        return response.content[:MAX_PAGE_BYTES].decode(response.encoding or "utf-8", errors="replace"), None
    except requests.RequestException as exc:
        return None, type(exc).__name__


def _event_objects(value: Any):
    if isinstance(value, list):
        for entry in value:
            yield from _event_objects(entry)
    elif isinstance(value, dict):
        types = value.get("@type", [])
        if isinstance(types, str):
            types = [types]
        if any(str(kind).lower() in {"event", "socialevent", "educationalevent", "hackathonevent"} for kind in types):
            yield value
        for key in ("@graph", "itemListElement", "mainEntity", "subEvent"):
            if key in value:
                yield from _event_objects(value[key])


def _parse_jsonld(parser: _PageParser) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for block in parser.jsonld:
        try:
            payload = json.loads(block)
        except (json.JSONDecodeError, TypeError):
            continue
        for event in _event_objects(payload):
            if isinstance(event.get("item"), dict):
                events.extend(_event_objects(event["item"]))
            else:
                events.append(event)
    return events


def _as_date(value: Any) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00")).date()
    except ValueError:
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None


def _text_dates(text: str) -> tuple[date | None, date | None]:
    iso = re.findall(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    dates = []
    for raw in iso:
        parsed = _as_date(raw)
        if parsed:
            dates.append(parsed)
    month_pattern = "|".join(sorted((re.escape(name) for name in MONTHS), key=len, reverse=True))
    for match in re.finditer(rf"\b({month_pattern})\.?\s+(\d{{1,2}})(?:\s*[-–]\s*(\d{{1,2}}))?[,]?\s+(20\d{{2}})\b", text, re.I):
        month, day, last_day, year = match.groups()
        month_num = MONTHS[month.lower().rstrip(".")]
        try:
            dates.append(date(int(year), month_num, int(day)))
            if last_day:
                dates.append(date(int(year), month_num, int(last_day)))
        except ValueError:
            pass
    return (min(dates), max(dates)) if dates else (None, None)


def _event_row(event: dict[str, Any], page_url: str, platform: dict[str, Any]) -> dict[str, Any] | None:
    title = event.get("name")
    url = event.get("url") or page_url
    if isinstance(url, dict):
        url = url.get("url")
    url = urljoin(page_url, str(url)) if url else page_url
    if not isinstance(title, str) or not title.strip():
        return None
    if not _is_event_url(url, platform):
        url = page_url
    start, end = _as_date(event.get("startDate")), _as_date(event.get("endDate"))
    description = re.sub(r"\s+", " ", str(event.get("description", ""))).strip()
    if not start:
        start, parsed_end = _text_dates(f"{title} {description}")
        end = end or parsed_end
    location = event.get("location", {})
    if isinstance(location, dict):
        place = location.get("name", "")
        address = location.get("address", {})
        if isinstance(address, dict):
            place = ", ".join(str(part) for part in (place, address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")) if part)
    else:
        place = str(location)
    return {"name": title.strip()[:240], "url": url, "snippet": description[:900], "source_platform": platform["name"], "start_date": start, "end_date": end, "location": str(place)[:180]}


def _fallback_event_row(parser: _PageParser, page_url: str, platform: dict[str, Any], anchor_title: str = "") -> dict[str, Any] | None:
    title = (parser.meta.get("og:title") or parser.meta.get("twitter:title") or parser.title or anchor_title).strip()
    description = (parser.meta.get("og:description") or parser.meta.get("description") or parser.meta.get("twitter:description") or "").strip()
    # Remove common platform suffixes, but do not infer missing dates or details.
    title = re.sub(r"\s*[|–-]\s*(Devpost|Devfolio|Unstop|Eventbrite|Luma|MLH).*$", "", title, flags=re.I).strip()
    if not title or title.lower() in {"devpost", "devfolio", "unstop", "eventbrite", "luma", "major league hacking"}:
        title = anchor_title.strip()
    if not title:
        return None
    start, end = _text_dates(" ".join((title, description, " ".join(parser.text[:100]))))
    return {"name": title[:240], "url": page_url, "snippet": description[:900], "source_platform": platform["name"], "start_date": start, "end_date": end, "location": ""}


def _matches_topic(event: dict[str, Any], interests: str) -> bool:
    terms = [term.lower() for term in re.findall(r"[a-z0-9]+", interests) if len(term) > 1]
    if not terms:
        return True
    evidence = f"{event['name']} {event['snippet']}".lower()
    return any(term in evidence for term in terms)


def _within_period(event: dict[str, Any], start: date, end: date) -> bool:
    event_start, event_end = event.get("start_date"), event.get("end_date")
    if event_start is None:
        return True  # Show as date-unverified rather than silently dropping the event.
    event_end = event_end or event_start
    return event_start <= end and event_end >= start


def _discover_platform(platform: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    listing_html, error = _fetch_page(platform["browse_url"], platform)
    if error or listing_html is None:
        return [], error or "empty_listing_page"
    listing = _PageParser()
    listing.feed(listing_html)
    candidates: list[tuple[str, str]] = []
    for link in listing.links:
        absolute = urljoin(platform["browse_url"], link["href"])
        if _is_event_url(absolute, platform) and absolute not in [url for url, _ in candidates]:
            candidates.append((absolute, link["text"]))
    found = []
    for raw_event in _parse_jsonld(listing):
        row = _event_row(raw_event, platform["browse_url"], platform)
        if row:
            found.append(row)
    # Fetch more than JSON-LD: use page metadata as an explicitly unverified
    # fallback for sites that publish event details in Open Graph/meta tags.
    candidates = candidates[:MAX_EVENT_PAGES_PER_PLATFORM]
    page_jobs = {}
    with ThreadPoolExecutor(max_workers=min(5, max(1, len(candidates)))) as pool:
        for event_url, anchor_title in candidates:
            page_jobs[pool.submit(_fetch_page, event_url, platform)] = (event_url, anchor_title)
        for future in as_completed(page_jobs):
            event_url, anchor_title = page_jobs[future]
            html, fetch_error = future.result()
            if not html:
                continue
            page = _PageParser()
            page.feed(html)
            page_events = [_event_row(raw_event, event_url, platform) for raw_event in _parse_jsonld(page)]
            page_events = [event for event in page_events if event]
            if not page_events:
                fallback = _fallback_event_row(page, event_url, platform, anchor_title)
                if fallback:
                    page_events = [fallback]
            found.extend(page_events)
    unique = {}
    for event in found:
        unique[event["url"]] = event
    if unique:
        return list(unique.values()), None
    if not candidates and not _parse_jsonld(listing):
        return [], "No public event links or structured event data in listing page (possibly JavaScript-rendered)"
    return [], "Event pages had no readable event metadata or structured data"


def search_official_events(interests: str, details: str, start: date, end: date) -> dict[str, Any]:
    """Discover events from allowlisted public hosting-platform pages only."""
    if start > end:
        raise ValueError("The start date must be on or before the latest date.")
    results: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {}
    with ThreadPoolExecutor(max_workers=len(PLATFORMS)) as pool:
        jobs = {pool.submit(_discover_platform, platform): platform for platform in PLATFORMS}
        for future in as_completed(jobs):
            platform = jobs[future]
            try:
                events, error = future.result()
            except Exception as exc:
                events, error = [], type(exc).__name__
            diagnostics[platform["name"]] = {"events_found": len(events), "issue": error}
            for event in events:
                if _matches_topic(event, interests) and _within_period(event, start, end):
                    event["date_verified"] = event["start_date"] is not None
                    results.append(event)
    results = list({event["url"]: event for event in results}.values())
    results.sort(key=lambda event: (event["start_date"] is None, event["start_date"] or date.max, event["name"].lower()))
    return {"results": results, "diagnostics": diagnostics, "message": "Events are collected only from official hosting-platform pages. Dates parsed from page metadata are unverified until checked on the organizer's page; results may be incomplete."}


def get_official_sources(interests: str, details: str, start: date, end: date) -> list[dict[str, Any]]:
    phrase = " ".join(part.strip() for part in (interests, details) if part and part.strip())
    return [{"name": p["name"], "url": p["browse_url"], "search_phrase": f"{phrase} {start.isoformat()} to {end.isoformat()}".strip()} for p in PLATFORMS]


def find_hackathons(interests: str, details: str, start_date: date, end_date: date, **_: Any) -> dict[str, Any]:
    result = search_official_events(interests, details, start_date, end_date)
    return {"error": False, "results": result["results"], "search_available": True, "search_diagnostics": result["diagnostics"], "message": result["message"]}
