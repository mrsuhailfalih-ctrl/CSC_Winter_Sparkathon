import unittest
from datetime import date
from unittest.mock import patch

import requests

from utils.live_search import _clean_result, _merge_and_dedupe, _normalize_url, _tokens, analyze_with_ollama, find_hackathons, search_hackathons


class SearchQualityTests(unittest.TestCase):
    def test_tokens(self):
        self.assertEqual(_tokens("AI hackathon Python"), {"python"})

    def test_rejects_directory_and_guide(self):
        self.assertIsNone(_clean_result({"title": "Hackathons | AI WhatsOn", "href": "https://aiwhatson.com/hackathons", "body": "Browse events"}))
        self.assertIsNone(_clean_result({"title": "AI hackathon guide", "href": "https://example.org/hackathon-guide", "body": "Guide"}))

    def test_accepts_specific_devpost_event(self):
        item = _clean_result({"title": "AI for Good Hackathon", "href": "https://devpost.com/hackathons/ai-for-good", "body": "Register for this hackathon"})
        self.assertIsNotNone(item)

    def test_deduplicates_tracking_links(self):
        raw = [
            {"title": "Veritas AI Hackathon Registration", "href": "https://veritas.example/register?utm_source=x", "body": "Nov 14, 2026. Registration open."},
            {"title": "Veritas AI Hackathon Register", "href": "https://veritas.example/register", "body": "Teams of 1–3."},
        ]
        self.assertEqual(len(_merge_and_dedupe(raw)), 1)

    @patch("utils.live_search.DDGS")
    def test_uses_targeted_queries_and_returns_individual_event_pages(self, ddgs_class):
        search = ddgs_class.return_value.__enter__.return_value
        search.text.side_effect = [
            [{"title": "AI Hackathons for Students Guide", "href": "https://aiwhatson.com/hackathons", "body": "Top events"},
             {"title": "AI for Good Hackathon", "href": "https://devpost.com/hackathons/ai-for-good", "body": "June 16, 2026. Register now."}],
            [], [], [], [],
        ]
        result = search_hackathons("AI", "student", date(2026, 6, 1), date(2026, 8, 31))
        self.assertEqual(len(result), 1)
        self.assertIn("devpost.com/hackathons/ai-for-good", result[0]["url"])

    @patch("utils.live_search.requests.get")
    @patch("utils.live_search.requests.post")
    def test_ollama_chat_success(self, post, get):
        get.return_value.raise_for_status.return_value = None
        get.return_value.json.return_value = {"models": [{"name": "qwen2.5:3b"}]}
        post.return_value.raise_for_status.return_value = None
        post.return_value.json.return_value = {"message": {"content": '{"results":[{"id":"abc","reason":"Good fit"}]}'}}
        result = analyze_with_ollama([{"id": "abc", "name": "Event", "url": "https://example.org/event", "snippet": "Hackathon", "date_match": "unknown"}], "AI", date(2026, 1, 1), date(2026, 12, 31))
        self.assertTrue(result["available"])
        self.assertEqual(result["annotations"]["abc"]["reason"], "Good fit")

    @patch("utils.live_search.requests.get", side_effect=requests.ConnectionError)
    def test_ollama_missing_server_falls_back(self, _):
        result = analyze_with_ollama([{"id": "abc", "name": "Event", "url": "https://example.org", "snippet": "Hackathon", "date_match": "unknown"}], "AI", date(2026, 1, 1), date(2026, 12, 31))
        self.assertFalse(result["available"])
        self.assertIn("Ollama is not reachable", result["message"])


if __name__ == "__main__":
    unittest.main()
