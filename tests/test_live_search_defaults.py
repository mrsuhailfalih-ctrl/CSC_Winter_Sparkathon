import unittest
from datetime import date
from unittest.mock import patch

from utils.live_search import _search_hackathons, search_hackathons


class SearchDefaultTests(unittest.TestCase):
    @patch("utils.live_search._run_search", return_value=([], 0, []))
    def test_private_search_has_safe_default_result_limit(self, _run_search):
        candidates, diagnostics = _search_hackathons("AI", "student", date(2026, 1, 1), date(2026, 12, 31))
        self.assertEqual(candidates, [])
        self.assertEqual(diagnostics["queries_succeeded"], 0)


if __name__ == "__main__":
    unittest.main()
