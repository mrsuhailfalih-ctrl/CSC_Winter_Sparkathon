import unittest
from datetime import date

from utils.live_search import OFFICIAL_EVENT_SOURCES, find_hackathons, get_official_sources


class OfficialSourceSearchTests(unittest.TestCase):
    def test_only_official_platform_destinations_are_returned(self):
        sources = get_official_sources("AI, Python", "online, free", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(sources), 6)
        self.assertEqual({source["name"] for source in sources}, {source["name"] for source in OFFICIAL_EVENT_SOURCES})
        self.assertTrue(all(source["url"].startswith("https://") for source in sources))

    def test_search_phrase_includes_preferences_and_period(self):
        sources = get_official_sources("AI", "online", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(sources[0]["search_phrase"], "AI online hackathon 2027-03-01 to 2027-03-31")

    def test_compatibility_entry_point_does_not_claim_scraped_results(self):
        result = find_hackathons("AI", "", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(result["results"], [])
        self.assertFalse(result["search_diagnostics"]["third_party_search_used"])
        self.assertEqual(len(result["sources"]), 6)

    def test_rejects_reversed_date_range(self):
        with self.assertRaises(ValueError):
            find_hackathons("AI", "", date(2027, 3, 31), date(2027, 3, 1))


if __name__ == "__main__":
    unittest.main()
