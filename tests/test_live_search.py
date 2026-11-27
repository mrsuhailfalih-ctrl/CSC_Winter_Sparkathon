import unittest
from datetime import date
from unittest.mock import patch

from utils.live_search import PLATFORMS, _event_objects, _is_event_url, _PageParser, search_official_events


class OfficialPlatformSearchTests(unittest.TestCase):
    def test_only_allowlisted_event_routes_are_accepted(self):
        devpost = next(platform for platform in PLATFORMS if platform["name"] == "Devpost")
        self.assertTrue(_is_event_url("https://devpost.com/hackathons/sample-event", devpost))
        self.assertFalse(_is_event_url("https://example.com/hackathons/sample-event", devpost))
        self.assertFalse(_is_event_url("https://devpost.com/hackathons", devpost))

    def test_extracts_event_type_from_jsonld_graph(self):
        parser = _PageParser()
        parser.jsonld = ['{"@context":"https://schema.org","@graph":[{"@type":"Event","name":"AI Build","startDate":"2027-03-12"}]}']
        events = list(_event_objects(__import__("json").loads(parser.jsonld[0])))
        self.assertEqual(events[0]["name"], "AI Build")

    @patch("utils.live_search._discover_platform")
    def test_results_are_only_from_platform_events_and_date_filtered(self, discover):
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
        self.assertEqual(result["results"][0]["source_platform"], "Devpost")

    def test_all_sources_are_official_platform_domains(self):
        for platform in PLATFORMS:
            self.assertTrue(platform["browse_url"].startswith("https://"))
            self.assertTrue(_is_event_url(platform["browse_url"], platform) is False)


if __name__ == "__main__":
    unittest.main()
