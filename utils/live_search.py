from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests

# We read only public listing/event pages on these platforms. Their own search
# APIs are not assumed to be available. Parsers rely on standard Event JSON-LD;
# platforms that render events only in client-side JavaScript may return no data.
PLATFORMS = (
    {"name": "Devpost", "hosts": ("devpost.com",), "browse_url": "https://devpost.com/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "Devfolio", "hosts": ("devfolio.co",), "browse_url": "https://devfolio.co/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "MLH", "hosts": ("mlh.io", "events.mlh.io"), "browse_url": "https://mlh.io/seasons", "paths": (r"^/events/[^/]+/?$", r"^/seasons/\d{4}/events/[^/]+/?$",)},
    {"name": "Unstop", "hosts": ("unstop.com",), "browse_url": "https://unstop.com/hackathons", "paths": (r"^/hackathons/[^/]+/?$",)},
    {"name": "Eventbrite", "hosts": ("eventbrite.com",), "browse_url": "https://www.eventbrite.com/d/online/hackathon/", "paths": (r"^/e/[^/]+/?$",)},
    {"name": "Luma", "hosts": ("lu.ma", "luma.com"), "browse_url": "https://lu.ma/discover", "paths": (r"^/[^/]+/?$",)},
)
MAX_EVENT_PAGES_PER_PLATFORM = 5
MAX_PAGE_BYTES = 2_000_000
REQUEST_TIMEOUT = (3, 7)


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[str] = []
        self.jsonld: list[str] = []
        self._in_jsonld = False
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag.lower() == "a" and attributes.get("href"):
            self.links.append(str(attributes["href"]))
        if tag.lower() == "script" and "ld+json" in str(attributes.get("type", "")).lower():
            self._in_jsonld = True
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        if self._in_jsonld:
            self._script_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._in_jsonld:
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
    if _platform_for_url(url) != platform:
        return False
    return any(re.search(pattern, parsed.path, re.I) for pattern in platform["paths"])


def _fetch_page(url: str, platform: dict[str, Any]) -> tuple[str | None, str | None]:
    """Fetch one public page without following redirects outside the allowlist."""
    if _platform_for_url(url) != platform:
        return None, "outside_platform_allowlist"
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "HackathonFinder/1.0 (public event discovery; contact: project repository)"},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
        if response.is_redirect:
            return None, "redirect_not_followed"
        response.raise_for_status()
        content = response.content[:MAX_PAGE_BYTES]
        return content.decode(response.encoding or "utf-8", errors="replace"), None
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
            # ItemList entries sometimes wrap the actual event in `item`.
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


def _event_row(event: dict[str, Any], page_url: str, platform: dict[str, Any]) -> dict[str, Any] | None:
    title = event.get("name")
    url = event.get("url") or page_url
    if isinstance(url, dict):
        url = url.get("url")
    url = urljoin(page_url, str(url)) if url else page_url
    if not isinstance(title, str) or not title.strip() or not _is_event_url(url, platform):
        url = page_url
        if not isinstance(title, str) or not title.strip():
            return None
    start = _as_date(event.get("startDate"))
    end = _as_date(event.get("endDate"))
    description = re.sub(r"\s+", " ", str(event.get("description", ""))).strip()
    location = event.get("location", {})
    if isinstance(location, dict):
        place = location.get("name", "")
        address = location.get("address", {})
        if isinstance(address, dict):
            place = ", ".join(str(part) for part in (place, address.get("addressLocality"), address.get("addressRegion"), address.get("addressCountry")) if part)
    else:
        place = str(location)
    return {
        "name": title.strip()[:240], "url": url, "snippet": description[:900],
        "source_platform": platform["name"], "start_date": start,
        "end_date": end, "location": str(place)[:180],
    }


def _matches_topic(event: dict[str, Any], interests: str) -> bool:
    terms = [term.lower() for term in re.findall(r"[a-z0-9]+", interests) if len(term) > 1]
    if not terms:
        return True
    evidence = f"{event['name']} {event['snippet']}".lower()
    return any(term in evidence for term in terms)


def _within_period(event: dict[str, Any], start: date, end: date) -> bool:
    event_start, event_end = event.get("start_date"), event.get("end_date")
    if event_start is None:
        return True  # Retain as a possible match, visibly marked as date-unverified.
    event_end = event_end or event_start
    return event_start <= end and event_end >= start


def _discover_platform(platform: dict[str, Any]) -> tuple[list[dict[str, Any]], str | None]:
    listing_html, error = _fetch_page(platform["browse_url"], platform)
    if error or listing_html is None:
        return [], error or "empty_listing_page"
    listing = _PageParser()
    listing.feed(listing_html)
    candidates: list[str] = []
    for href in listing.links:
        absolute = urljoin(platform["browse_url"], href)
        if _is_event_url(absolute, platform) and absolute not in candidates:
            candidates.append(absolute)
    # Some platforms expose structured Event data directly on browse pages.
    found = []
    for raw_event in _parse_jsonld(listing):
        row = _event_row(raw_event, platform["browse_url"], platform)
        if row:
            found.append(row)
    candidates = candidates[:MAX_EVENT_PAGES_PER_PLATFORM]
    page_jobs = {}
    with ThreadPoolExecutor(max_workers=min(5, max(1, len(candidates)))) as pool:
        for event_url in candidates:
            page_jobs[pool.submit(_fetch_page, event_url, platform)] = event_url
        for future in as_completed(page_jobs):
            event_url = page_jobs[future]
            html, fetch_error = future.result()
            if not html:
                continue
            page = _PageParser()
            page.feed(html)
            for raw_event in _parse_jsonld(page):
                row = _event_row(raw_event, event_url, platform)
                if row:
                    found.append(row)
    # Remove duplicate URLs, preserving one authoritative platform page.
    unique = {}
    for event in found:
        unique[event["url"]] = event
    return list(unique.values()), None


def search_official_events(interests: str, details: str, start: date, end: date) -> dict[str, Any]:
    """Discover structured events from official platform pages only.

    This is best-effort: JS-only listings, blocked pages, or missing Event JSON-LD
    are reported as source limitations rather than replaced with general search.
    """
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
    # Any-platform dedupe by canonical event URL; dates remain sourced from JSON-LD.
    deduped = {event["url"]: event for event in results}
    results = list(deduped.values())
    results.sort(key=lambda event: (event["start_date"] is None, event["start_date"] or date.max, event["name"].lower()))
    return {
        "results": results,
        "diagnostics": diagnostics,
        "message": "Events are extracted from public official-platform pages when those pages expose structured Event data. Verify each listing with its organizer; coverage is not exhaustive.",
    }


def get_official_sources(interests: str, details: str, start: date, end: date) -> list[dict[str, Any]]:
    """Compatibility helper for platform browse destinations."""
    phrase = " ".join(part.strip() for part in (interests, details) if part and part.strip())
    return [{"name": p["name"], "url": p["browse_url"], "search_phrase": f"{phrase} {start.isoformat()} to {end.isoformat()}".strip()} for p in PLATFORMS]


def find_hackathons(interests: str, details: str, start_date: date, end_date: date, **_: Any) -> dict[str, Any]:
    """Compatibility wrapper used by older app code."""
    result = search_official_events(interests, details, start_date, end_date)
    return {"error": False, "results": result["results"], "search_available": True, "search_diagnostics": result["diagnostics"], "message": result["message"]}
