import json
import unittest
from unittest.mock import Mock, patch

from utils.momen_ai import _replace_prompt, rank_events_with_momen


class MomenIntegrationTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    def test_missing_settings_falls_back_without_request(self):
        result = rank_events_with_momen([{"name": "Event", "url": "https://devpost.com/hackathons/event"}])
        self.assertFalse(result["available"])
        self.assertEqual(result["rankings"], {})

    def test_prompt_substitution_supports_nested_variables(self):
        result = _replace_prompt({"input": {"message": "{{PROMPT}}"}}, "hello")
        self.assertEqual(result, {"input": {"message": "hello"}})

    @patch.dict("os.environ", {
        "MOMEN_GRAPHQL_URL": "https://example.momen.app/api/graphql",
        "MOMEN_JWT": "test-token",
        "MOMEN_AI_MUTATION": "mutation Rank($prompt: String!) { rank(prompt: $prompt) }",
        "MOMEN_AI_VARIABLES_JSON": '{"prompt":"{{PROMPT}}"}',
    }, clear=True)
    @patch("utils.momen_ai.requests.post")
    def test_accepts_only_rankings_for_supplied_urls(self, post):
        event_url = "https://devpost.com/hackathons/ai-event"
        output = {"rankings": [{"url": event_url, "score": 88, "reason": "AI topic matches"}, {"url": "https://bad.example/x", "score": 100}]}
        post.return_value = Mock(status_code=200)
        post.return_value.json.return_value = {"data": {"rank": json.dumps(output)}}
        post.return_value.raise_for_status.return_value = None
        result = rank_events_with_momen([{"name": "AI Event", "url": event_url}])
        self.assertTrue(result["available"])
        self.assertEqual(result["rankings"], {event_url: {"score": 88, "reason": "AI topic matches"}})


if __name__ == "__main__":
    unittest.main()
