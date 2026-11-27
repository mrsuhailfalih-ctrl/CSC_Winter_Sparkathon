import unittest
from datetime import date
from unittest.mock import Mock, patch

from utils.live_search import PLATFORMS, _PageParser, _fallback_event_row, _is_event_url, _text_dates, search_official_events


class OfficialPlatformSearchTests(unittest.TestCase):
    def test_only_allowlisted_event_routes_are_accepted(self):
        devpost = next(platform for platform in PLATFORMS if platform["name"] == "Devpost")
        self.assertTrue(_is_event_url("https://devpost.com/hackathons/sample-event", devpost))
        self.assertFalse(_is_event_url("https://example.com/hackathons/sample-event", devpost))
        self.assertFalse(_is_event_url("https://devpost.com/hackathons", devpost))

    def test_parses_dates_from_text_metadata(self):
        self.assertEqual(_text_dates("AI build event March 12-14, 2027"), (date(2027, 3, 12), date(2027, 3, 14)))
        self.assertEqual(_text_dates("Starts 2027-03-20"), (date(2027, 3, 20), date(2027, 3, 20)))

    def test_uses_open_graph_metadata_when_jsonld_is_missing(self):
        platform = next(item for item in PLATFORMS if item["name"] == "Devpost")
        parser = _PageParser()
        parser.meta = {"og:title": "AI Python Buildathon", "og:description": "Online event March 12-14, 2027; free registration."}
        row = _fallback_event_row(parser, "https://devpost.com/hackathons/ai-build", platform)
        self.assertEqual(row["name"], "AI Python Buildathon")
        self.assertEqual(row["start_date"], date(2027, 3, 12))
        self.assertEqual(row["end_date"], date(2027, 3, 14))

    @patch("utils.live_search._discover_platform")
    def test_keeps_only_matching_and_in_period_platform_results(self, discover):
        def fake(platform):
            if platform["name"] == "Devpost":
                return ([
                    {"name": "AI Python Build", "url": "https://devpost.com/hackathons/ai-build", "snippet": "online free", "source_platform": "Devpost", "start_date": date(2027, 3, 12), "end_date": None, "location": ""},
                    {"name": "Old AI event", "url": "https://devpost.com/hackathons/old", "snippet": "", "source_platform": "Devpost", "start_date": date(2026, 3, 12), "end_date": None, "location": ""},
                ], None)
            return [], None
        discover.side_effect = fake
        result = search_official_events("AI", "", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual([event["name"] for event in result["results"]], ["AI Python Build"])

    def test_unknown_dates_are_not_dropped(self):
        from utils.live_search import _within_period
        self.assertTrue(_within_period({"start_date": None, "end_date": None}, date(2027, 3, 1), date(2027, 3, 31)))

    def test_all_sources_are_https_official_platform_destinations(self):
        for platform in PLATFORMS:
            self.assertTrue(platform["browse_url"].startswith("https://"))
            self.assertFalse(_is_event_url(platform["browse_url"], platform))


if __name__ == "__main__":
    unittest.main()
