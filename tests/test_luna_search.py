import unittest
from unittest.mock import Mock, patch

from utils.luna_search import search_with_luna


class LunaSearchTests(unittest.TestCase):
    @patch("utils.luna_search._setting")
    @patch("utils.luna_search.requests.post")
    def test_requires_web_search_and_citation_for_results(self, post, setting):
        setting.side_effect = lambda name, default="": {
            "LUNA_API_KEY": "secret-test", "LUNA_API_BASE": "https://example.test/v1",
            "LUNA_MODEL": "gpt-6-luna", "LUNA_WEB_SEARCH_TOOL": "web_search",
        }.get(name, default)
        response = Mock()
        response.json.return_value = {
            "output": [{"content": [{
                "type": "output_text",
                "text": '{"events":[{"title":"AI Hackathon","url":"https://events.example/hack","snippet":"Hackathon dates: March 15-16, 2027.","event_start_date":"2027-03-15","event_end_date":"not-a-date"}]}',
                "annotations": [{"type": "url_citation", "url": "https://events.example/hack"}],
            }]}]
        }
        post.return_value = response

        result = search_with_luna("AI", "student", "2027-03-01", "2027-03-31", age=17)

        self.assertIsNone(result["error"])
        self.assertEqual(result["results"][0]["title"], "AI Hackathon")
        self.assertEqual(result["results"][0]["event_end_date"], "")
        self.assertEqual(post.call_args.args[0], "https://example.test/v1/responses")
        self.assertEqual(post.call_args.kwargs["json"]["tools"], [{"type": "web_search"}])
        self.assertEqual(post.call_args.kwargs["json"]["tool_choice"], "required")
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer secret-test")

    @patch("utils.luna_search._setting")
    @patch("utils.luna_search.requests.post")
    def test_drops_uncited_model_generated_urls(self, post, setting):
        setting.side_effect = lambda name, default="": {
            "LUNA_API_KEY": "secret-test", "LUNA_API_BASE": "https://example.test/v1", "LUNA_MODEL": "gpt-6-luna"
        }.get(name, default)
        response = Mock()
        response.json.return_value = {
            "output_text": '{"events":[{"title":"Invented","url":"https://fake.example/event"}]}'
        }
        post.return_value = response

        result = search_with_luna("AI", "", "2027-03-01", "2027-03-31")

        self.assertEqual(result["results"], [])
        self.assertIn("no web-search source citations", result["error"])


if __name__ == "__main__":
    unittest.main()
