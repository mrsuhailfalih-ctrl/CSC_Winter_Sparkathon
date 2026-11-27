import unittest
from datetime import date
from unittest.mock import patch

import requests

from utils.openrouter_ai import DEFAULT_MODEL, analyze_with_openrouter


CANDIDATES = [{
    "id": "evt-1", "name": "AI for Good Hackathon", "url": "https://events.example/ai",
    "snippet": "A student AI hackathon in June.", "date_match": "June 2026",
}]


class OpenRouterTests(unittest.TestCase):
    @patch("utils.openrouter_ai.requests.post")
    def test_sends_configured_model_and_parses_scores(self, post):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": '{"results":[{"id":"evt-1","score":91,"reason":"Matches AI and student preferences."}]}'}}]
        }
        result = analyze_with_openrouter(CANDIDATES, "AI student", date(2026, 6, 1), date(2026, 6, 30), api_key="test-key")
        self.assertTrue(result["available"])
        self.assertEqual(result["annotations"]["evt-1"]["score"], 91)
        self.assertEqual(post.call_args.kwargs["json"]["model"], DEFAULT_MODEL)
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer test-key")

    @patch("utils.openrouter_ai.requests.post")
    def test_ignores_unknown_ids_and_caps_scores(self, post):
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {
            "choices": [{"message": {"content": '{"results":[{"id":"not-real","score":10,"reason":"ignore"},{"id":"evt-1","score":999,"reason":"Good."}]}'}}]
        }
        result = analyze_with_openrouter(CANDIDATES, "AI", date(2026, 6, 1), date(2026, 6, 30), api_key="test-key")
        self.assertEqual(result["annotations"], {"evt-1": {"score": 100, "reason": "Good."}})

    def test_missing_key_gracefully_falls_back(self):
        with patch("utils.openrouter_ai._get_api_key", return_value=""):
            result = analyze_with_openrouter(CANDIDATES, "AI", date(2026, 6, 1), date(2026, 6, 30))
        self.assertFalse(result["available"])
        self.assertIn("OPENROUTER_API_KEY", result["message"])

    @patch("utils.openrouter_ai.requests.post", side_effect=requests.Timeout)
    def test_timeout_keeps_local_fallback(self, _):
        result = analyze_with_openrouter(CANDIDATES, "AI", date(2026, 6, 1), date(2026, 6, 30), api_key="test-key")
        self.assertFalse(result["available"])
        self.assertIn("timed out", result["message"])


if __name__ == "__main__":
    unittest.main()
