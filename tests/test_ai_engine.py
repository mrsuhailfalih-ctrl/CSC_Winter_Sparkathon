import unittest

from utils.ai_engine import filter_by_age, rank_locally, recommend_hackathons


class RecommendationTests(unittest.TestCase):
    def test_age_too_low_is_filtered(self):
        events = [{"name": "Adult event", "minimum_age": 18}]
        self.assertEqual(filter_by_age(events, 16), [])

    def test_age_within_range_is_kept(self):
        events = [{"name": "Teen event", "minimum_age": 13, "maximum_age": 18}]
        self.assertEqual(filter_by_age(events, 16), events)

    def test_unknown_age_rule_is_not_rejected(self):
        events = [{"name": "Unknown event", "minimum_age": None, "maximum_age": None}]
        self.assertEqual(filter_by_age(events, 16), events)

    def test_invalid_age_is_rejected(self):
        result = recommend_hackathons("AI", 12)
        self.assertTrue(result["error"])

    def test_local_ranking_returns_sorted_list(self):
        events = [
            {"name": "AI event", "tags": "AI, Python", "location": "Online", "level": "Beginner"},
            {"name": "Art event", "tags": "art", "location": "Online", "level": "All Levels"},
        ]
        result = rank_locally("AI Python beginner", 16, events)
        self.assertFalse(result["error"])
        self.assertEqual(result["answer"][0]["name"], "AI event")


if __name__ == "__main__":
    unittest.main()
