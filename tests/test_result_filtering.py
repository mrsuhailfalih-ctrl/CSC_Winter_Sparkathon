import unittest
from datetime import date

from utils.result_filtering import extract_event_dates, filter_event_candidates


class ResultFilteringTests(unittest.TestCase):
    def test_extracts_abbreviated_month_and_date_range(self):
        self.assertEqual(
            extract_event_dates("Nov 14–15, 2026"),
            [date(2026, 11, 14), date(2026, 11, 15)],
        )

    def test_excludes_known_stale_event(self):
        candidate = {
            "name": "Veritas AI International High School Hackathon",
            "snippet": "Nov 14, 2026. Free virtual AI hackathon.",
        }
        confirmed, possible, diagnostics = filter_event_candidates(
            [candidate], "AI", date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(confirmed, [])
        self.assertEqual(possible, [])
        self.assertEqual(diagnostics["outside_date_range"], 1)

    def test_keeps_specific_unknown_date_event_as_unverified(self):
        candidate = {"name": "Meta Global AI Developer Hackathon", "snippet": "Virtual AI hackathon. Apply now."}
        confirmed, possible, _ = filter_event_candidates(
            [candidate], "AI", date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(confirmed, [])
        self.assertEqual(possible, [candidate])

    def test_rejects_directory_or_bootcamp_pages(self):
        candidates = [
            {"name": "Hack4Hack — Online Hackathons, AI Challenges", "snippet": "Find upcoming events"},
            {"name": "Register For AI BootCamp", "snippet": "Pre-register for a hackathon"},
        ]
        confirmed, possible, diagnostics = filter_event_candidates(
            candidates, "AI", date(2027, 3, 1), date(2027, 3, 31)
        )
        self.assertEqual(confirmed + possible, [])
        self.assertEqual(diagnostics["not_individual_event"], 2)


if __name__ == "__main__":
    unittest.main()
