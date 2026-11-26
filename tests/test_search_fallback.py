import unittest
from datetime import date
from unittest.mock import patch

from utils.live_search import _merge_and_dedupe, _normalize_url, analyze_with_ollama, find_hackathons


class SearchAndOllamaFallbackTests(unittest.TestCase):
    def test_normalizes_tracking_url(self):
        self.assertEqual(_normalize_url("https://www.example.com/event/?utm_source=x#rules"), "https://example.com/event")

    def test_editorial_results_filtered_and_duplicate_links_collapsed(self):
        raw = [
            {"title": "AI Hackathons for High School Students: 2026–2027 Guide", "href": "https://example.com/guide", "body": "Top events"},
            {"title": "Register Free | Veritas AI International High School Hackathon", "href": "https://veritas.example/register?utm_source=x", "body": "Nov 14, 2026. Open worldwide to high schoolers."},
            {"title": "Veritas AI International High School Hackathon Registration", "href": "https://veritas.example/register", "body": "Teams of 1–3."},
        ]
        self.assertEqual(len(_merge_and_dedupe(raw)), 1)

    @patch("utils.live_search.requests.get", side_effect=__import__("requests").ConnectionError)
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
        self.assertIn("free local ranker", result["ai_message"])


if __name__ == "__main__":
    unittest.main()
