import unittest
from datetime import date
from unittest.mock import patch

from utils.live_search import _merge_and_dedupe, _normalize_url, search_hackathons


class LiveSearchQualityTests(unittest.TestCase):
    def test_removes_tracking_and_fragments(self):
        self.assertEqual(_normalize_url("https://www.example.com/event/?utm_source=x#rules"), "https://example.com/event")

    def test_filters_editorial_and_deduplicates_event_pages(self):
        raw = [
            {"title": "AI Hackathons for High School Students: 2026–2027 Guide", "href": "https://example.com/guide", "body": "Top events"},
            {"title": "Register Free | Veritas AI International High School Hackathon", "href": "https://veritas.example/register?utm_source=x", "body": "Nov 14, 2026. Open worldwide to high school students."},
            {"title": "Veritas AI International High School Hackathon Registration", "href": "https://veritas.example/register", "body": "Teams of 1–3."},
            {"title": "Official Resources for USAII Global AI Hackathon 2026", "href": "https://usaii.example/resources", "body": "Qualifier guide"},
        ]
        results = _merge_and_dedupe(raw)
        self.assertEqual(len(results), 1)
        self.assertIn("Veritas", results[0]["name"])

    def test_official_platform_results_are_prioritized_and_labeled(self):
        raw = [
            {"title": "General AI Hackathon 2027", "href": "https://organizer.example/events/ai-2027", "body": "Register for the AI hackathon."},
            {"title": "AI Build Hackathon 2027", "href": "https://devpost.com/hackathons/ai-build-2027", "body": "Register and submit your project."},
        ]
        results = _merge_and_dedupe(raw)
        self.assertEqual(results[0]["source_platform"], "Devpost")
        self.assertEqual(results[0]["source_priority"], 0)

    def test_platform_searches_include_all_requested_sites(self):
        with patch("utils.live_search._run_search") as run_search:
            run_search.side_effect = [([], 6, []), ([], 2, [])]
            search_hackathons("AI", "student", date(2027, 3, 1), date(2027, 3, 31))
            queries = run_search.call_args_list[0].args[0]
            query_text = " ".join(queries)
            for domain in ("devpost.com", "devfolio.co", "mlh.io", "unstop.com", "eventbrite.com", "lu.ma"):
                self.assertIn(domain, query_text)

    def test_date_window_orders_explicit_match_first(self):
        with patch("utils.live_search._run_search") as run_search:
            run_search.side_effect = [
                ([{"title": "Summer Code Hackathon registration", "href": "https://event.example/events/in", "body": "June 16, 2026"}], 6, []),
                ([{"title": "Out of range Hackathon", "href": "https://event.example/events/out", "body": "March 2, 2027"}], 2, []),
            ]
            results = search_hackathons("AI", "student", date(2026, 6, 1), date(2026, 8, 31))
        self.assertEqual(results[0]["name"], "Summer Code Hackathon registration")
        self.assertTrue(results[0]["date_fit"])
        self.assertFalse(results[1]["date_fit"])


if __name__ == "__main__":
    unittest.main()
