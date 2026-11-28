import unittest
from unittest.mock import Mock, patch

from utils.serper_search import search_with_serper


class SerperSearchTests(unittest.TestCase):
    @patch("utils.serper_search._setting", return_value="test-key")
    @patch("utils.serper_search.requests.post")
    def test_returns_all_organic_results_without_filtering(self, post, _setting):
        organic = [
            {"title": "Potential event", "link": "https://example.com/event", "snippet": "Unrelated wording"},
            {"title": "Another result", "link": "https://another.example/page", "date": "2025"},
        ]
        response = Mock()
        response.json.return_value = {"organic": organic}
        post.return_value = response

        result = search_with_serper("AI", "student", "2026-01-01", "2026-12-31")

        self.assertIsNone(result["error"])
        self.assertEqual(result["results"], organic)
        self.assertEqual(post.call_args.kwargs["headers"]["X-API-KEY"], "test-key")
        self.assertIn("upcoming individual hackathon event", post.call_args.kwargs["json"]["q"])

    @patch("utils.serper_search._setting", return_value="test-key")
    @patch("utils.serper_search.requests.post")
    def test_query_includes_age_format_location_and_date_window(self, post, _setting):
        response = Mock()
        response.json.return_value = {"organic": []}
        post.return_value = response

        result = search_with_serper(
            "AI", "student", "2027-03-01", "2027-03-31",
            age=17, event_format="In-person", location="Toronto, Ontario",
        )

        query = result["query"]
        self.assertIn("eligibility for age 17", query)
        self.assertIn("in-person onsite", query)
        self.assertIn("near Toronto, Ontario", query)
        self.assertIn("event dates between 2027-03-01 and 2027-03-31", query)

    @patch("utils.serper_search._setting", return_value="")
    def test_reports_missing_api_key(self, _setting):
        result = search_with_serper("AI", "", None, None)
        self.assertEqual(result["results"], [])
        self.assertIn("SERPER_API_KEY", result["error"])


if __name__ == "__main__":
    unittest.main()
