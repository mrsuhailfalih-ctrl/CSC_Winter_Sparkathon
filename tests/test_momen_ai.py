import json
import unittest
from datetime import date
from unittest.mock import Mock, patch

from utils.momen_ai import search_events_with_momen


class MomenWebSearchTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_configuration_returns_no_events(self):
        result = search_events_with_momen("AI", "", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(result["results"], [])
        self.assertTrue(result["error"])

    @patch.dict("os.environ", {
        "MOMEN_GRAPHQL_URL": "https://example.momen.app/api/graphql",
        "MOMEN_JWT": "test-token",
        "MOMEN_AI_MUTATION": "mutation Search($prompt: String!) { search(prompt: $prompt) }",
        "MOMEN_AI_VARIABLES_JSON": '{"prompt":"{{PROMPT}}"}',
    }, clear=True)
    @patch("utils.momen_ai.requests.post")
    @patch("utils.momen_ai._verify_candidate")
    def test_only_allowlisted_urls_are_queried_and_verified(self, verify, post):
        allowed = "https://devpost.com/hackathons/ai-robotics-2027"
        reply = {"events": [{"url": allowed}, {"url": "https://random-blog.example/hackathon"}]}
        response = Mock()
        response.json.return_value = {"data": {"search": json.dumps(reply)}}
        response.raise_for_status.return_value = None
        post.return_value = response
        verify.return_value = {
            "name": "AI Robotics Hackathon", "url": allowed, "source_platform": "Devpost",
            "snippet": "AI and robotics", "start_date": date(2027, 3, 10), "end_date": None,
            "location": "", "date_verified": True,
        }
        result = search_events_with_momen("AI", "", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["url"], allowed)
        verify.assert_called_once_with({"url": allowed})

    @patch.dict("os.environ", {
        "MOMEN_GRAPHQL_URL": "https://example.momen.app/api/graphql",
        "MOMEN_JWT": "test-token",
        "MOMEN_AI_MUTATION": "mutation Search($prompt: String!) { search(prompt: $prompt) }",
        "MOMEN_AI_VARIABLES_JSON": '{"prompt":"{{PROMPT}}"}',
    }, clear=True)
    @patch("utils.momen_ai.requests.post")
    def test_invalid_agent_output_is_handled(self, post):
        response = Mock()
        response.json.return_value = {"data": {"search": "not-json"}}
        response.raise_for_status.return_value = None
        post.return_value = response
        result = search_events_with_momen("AI", "", date(2027, 3, 1), date(2027, 3, 31))
        self.assertTrue(result["error"])
        self.assertEqual(result["results"], [])


if __name__ == "__main__":
    unittest.main()
