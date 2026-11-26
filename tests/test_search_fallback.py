import unittest
from datetime import date
from unittest.mock import patch

import requests

from utils.live_search import (
    _clean_result,
    _merge_and_dedupe,
    _normalize_url,
    _tokens,
    analyze_with_ollama,
    find_hackathons,
    search_hackathons,
)


class SearchQualityTests(unittest.TestCase):
    def test_tokens_subtracts_stop_words_from_set(self):
        self.assertEqual(_tokens("AI hackathon Python"), {"python"})

    def test_normalizes_tracking_url(self):
        self.assertEqual(_normalize_url("https://www.example.com/event/?utm_source=x#rules"), "https://example.com/event")

    def test_rejects_guide_and_blog_results(self):
        self.assertIsNone(_clean_result({"title": "AI Hackathons for High School Students: 2026 Guide", "href": "https://example.com/guide", "body": "Top events"}))
        self.assertIsNone(_clean_result({"title": "Future Hackathon Registration", "href": "https://example.com/blog/future", "body": "Register for the event"}))

    def test_deduplicates_same_event_tracking_links(self):
        results = _merge_and_dedupe([
            {"title": "Veritas AI High School Hackathon Registration", "href": "https://veritas.example/register?utm_source=x", "body": "Nov 14, 2026. Registration open."},
            {"title": "Veritas AI High School Hackathon Register", "href": "https://veritas.example/register", "body": "Teams of 1–3."},
        ])
        self.assertEqual(len(results), 1)

    @patch("utils.live_search.DDGS")
    def test_filters_past_edition_and_prioritizes_requested_dates(self, ddgs_class):
        search = ddgs_class.return_value.__enter__.return_value
        search.text.side_effect = [[
            {"title": "2024 AI Hackathon Registration", "href": "https://event.example/2024", "body": "The hackathon was held on June 2, 2024."},
            {"title": "Future AI Hackathon Registration 2026", "href": "https://event.example/2026", "body": "June 16, 2026. Register now."},
        ], []]
        results = search_hackathons("AI", "student", date(2026, 6, 1), date(2026, 8, 31))
        self.assertEqual(len(results), 1)
        self.assertIn("2026", results[0]["name"])
        self.assertTrue(results[0]["date_fit"])

    @patch("utils.live_search.requests.get", side_effect=requests.ConnectionError)
    def test_ollama_not_running_is_graceful(self, _):
        result = analyze_with_ollama(
            [{"id": "abc", "name": "Test Hackathon", "url": "https://example.org", "snippet": "Hackathon"}],
            "AI", date(2026, 1, 1), date(2026, 12, 31),
        )
        self.assertFalse(result["available"])
        self.assertIn("not running", result["message"])

    @patch("utils.live_search.search_hackathons", return_value=[
        {"id": "abc", "name": "AI Hackathon", "url": "https://example.org", "snippet": "AI hackathon registration", "date_fit": None, "date_match": "unknown", "reason": ""}
    ])
    def test_search_does_not_depend_on_ollama(self, _):
        result = find_hackathons("AI", "student", date(2026, 1, 1), date(2026, 12, 31))
        self.assertFalse(result["error"])
        self.assertEqual(len(result["results"]), 1)


if __name__ == "__main__":
    unittest.main()
