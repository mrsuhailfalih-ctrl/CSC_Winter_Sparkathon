from __future__ import annotations

import ipaddress
import re
import socket
from html.parser import HTMLParser
from urllib.parse import urlparse

import requests


MAX_PAGE_BYTES = 1_000_000
AGE_TERMS = re.compile(r"\b(age|ages|under\s+\d+|over\s+\d+|minimum age|at least|18\+|13\+|high school|minor|parental consent|guardian)\b", re.I)


class _TextExtractor(HTMLParser):
    """Small standard-library HTML text extractor that ignores scripts/styles."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1
        elif tag.lower() in {"p", "li", "div", "section", "br", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1
        elif tag.lower() in {"p", "li", "div", "section", "br", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth and data.strip():
            self.parts.append(data.strip())


def _public_https_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    try:
        addresses = socket.getaddrinfo(parsed.hostname, 443, type=socket.SOCK_STREAM)
    except (OSError, socket.gaierror):
        return False
    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            return False
    return True


def _age_evidence(text: str) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    evidence = []
    for sentence in sentences:
        cleaned = " ".join(sentence.split())
        if AGE_TERMS.search(cleaned):
            evidence.append(cleaned[:500])
    return list(dict.fromkeys(evidence))[:20]


def verify_age_rule(url: str) -> dict:
    """Fetch an HTTPS event page and return age-related evidence for human review.

    This is evidence gathering, not an automatic eligibility decision. Page text may
    be incomplete, stale, or misleading; the user must confirm the rule themselves.
    """
    if not _public_https_url(url):
        return {"error": True, "message": "Only public HTTPS event pages can be checked."}

    original_host = urlparse(url).hostname.lower()
    try:
        with requests.get(
            url,
            headers={"User-Agent": "HackathonFinder/1.0 (eligibility evidence checker)"},
            timeout=(5, 12),
            stream=True,
            allow_redirects=True,
        ) as response:
            if urlparse(response.url).hostname.lower() != original_host:
                return {"error": True, "message": "The page redirected to another host; open and verify the destination manually."}
            response.raise_for_status()
            content_type = response.headers.get("Content-Type", "").lower()
            if "html" not in content_type:
                return {"error": True, "message": "The official page did not return HTML that can be checked."}
            chunks = []
            size = 0
            for chunk in response.iter_content(chunk_size=8192):
                size += len(chunk)
                if size > MAX_PAGE_BYTES:
                    return {"error": True, "message": "The page is too large to inspect safely."}
                chunks.append(chunk)
            raw = b"".join(chunks)
            encoding = response.encoding or "utf-8"
            html = raw.decode(encoding, errors="replace")
    except requests.RequestException:
        return {"error": True, "message": "Could not fetch this page. Open the official rules in your browser and check manually."}
    except (LookupError, UnicodeError):
        return {"error": True, "message": "Could not decode the page; please check the official rules manually."}

    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        return {"error": True, "message": "Could not read the page content. Check it manually."}

    evidence = _age_evidence(" ".join(parser.parts))
    return {
        "error": False,
        "url": url,
        "checked_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(timespec="seconds"),
        "evidence": evidence,
        "message": "Age-related text found. Review the official rules yourself; this tool does not verify eligibility automatically."
        if evidence else "No age-related text was extracted. This does not mean there is no age restriction.",
    }


def parse_age_bounds(minimum: str, maximum: str) -> tuple[int | None, int | None]:
    """Parse optional human-reviewed age bounds, rejecting malformed ranges."""
    min_age = int(minimum) if minimum.strip() else None
    max_age = int(maximum) if maximum.strip() else None
    if min_age is not None and not 0 <= min_age <= 120:
        raise ValueError("Minimum age must be between 0 and 120.")
    if max_age is not None and not 0 <= max_age <= 120:
        raise ValueError("Maximum age must be between 0 and 120.")
    if min_age is not None and max_age is not None and min_age > max_age:
        raise ValueError("Minimum age cannot be greater than maximum age.")
    return min_age, max_age
