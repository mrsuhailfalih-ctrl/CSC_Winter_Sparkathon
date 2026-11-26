import unittest
from datetime import date
from unittest.mock import patch

from utils.live_search import _merge_and_dedupe, _normalize_url, search_hackathons


class LiveSearchQualityTests(unittest.TestCase):
    def test_removes_tracking_and_fragments(self):
        self.assertEqual(
            _normalize_url("https://www.example.com/event/?utm_source=x#rules"),
            "https://example.com/event",
        )

    def test_filters_editorial_and_deduplicates_event_pages(self):
        raw = [
            {"title": "AI Hackathons for High School Students: 2026–2027 Guide", "href": "https://example.com/guide", "body": "Top events"},
            {"title": "Register Free | Veritas AI International High School Hackathon", "href": "https://veritas.example/register?utm_source=x", "body": "Nov 14, 2026. Open worldwide to high schoolers."},
            {"title": "Veritas AI International High School Hackathon Registration", "href": "https://veritas.example/register", "body": "Teams of 1–3."},
            {"title": "Official Resources for USAII Global AI Hackathon 2026", "href": "https://usaii.example/resources", "body": "Qualifier guide"},
        ]
        results = _merge_and_dedupe(raw)
        self.assertEqual(len(results), 1)
        self.assertIn("Veritas", results[0]["name"])

    @patch("utils.live_search.DDGS")
    def test_date_window_orders_explicit_match_first(self, ddgs_class):
        search = ddgs_class.return_value.__enter__.return_value
        search.text.side_effect = [
            [{"title": "Out of range Hackathon", "href": "https://event.example/out", "body": "March 2, 2027"}],
            [{"title": "Summer Code Hackathon registration", "href": "https://event.example/in", "body": "June 16, 2026"}],
        ]
        results = search_hackathons("AI", "student", date(2026, 6, 1), date(2026, 8, 31))
        self.assertEqual(results[0]["name"], "Summer Code Hackathon registration")
        self.assertTrue(results[0]["date_fit"])
        self.assertFalse(results[1]["date_fit"])


if __name__ == "__main__":
    unittest.main()
