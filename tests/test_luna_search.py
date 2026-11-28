import unittest
from unittest.mock import Mock, patch

from utils.luna_search import search_with_luna


class LunaSearchTests(unittest.TestCase):
    @patch("utils.luna_search._setting")
    @patch("utils.luna_search.requests.post")
    def test_uses_web_search_and_parses_events(self, post, setting):
        setting.side_effect = lambda name, default="": {
            "LUNA_API_KEY": "secret-test", "LUNA_API_BASE": "https://example.test/v1", "LUNA_MODEL": "gpt-6-luna"
        }.get(name, default)
        response = Mock()
        response.json.return_value = {
            "output_text": '{"events":[{"title":"AI Hackathon","url":"https://events.example/hack","snippet":"Hackathon dates: March 15-16, 2027.","event_start_date":"2027-03-15","event_end_date":"2027-03-16"}]}'
        }
        post.return_value = response

        result = search_with_luna("AI", "student", "2027-03-01", "2027-03-31", age=17)

        self.assertIsNone(result["error"])
        self.assertEqual(result["results"][0]["title"], "AI Hackathon")
        self.assertEqual(post.call_args.args[0], "https://example.test/v1/responses")
        self.assertEqual(post.call_args.kwargs["json"]["tools"], [{"type": "web_search"}])
        self.assertEqual(post.call_args.kwargs["headers"]["Authorization"], "Bearer secret-test")


if __name__ == "__main__":
    unittest.main()
