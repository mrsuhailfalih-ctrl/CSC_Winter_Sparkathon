import unittest
from datetime import date

from utils.result_filtering import extract_event_dates, filter_event_candidates


class ResultFilteringTests(unittest.TestCase):
    def test_extracts_abbreviated_month_and_date_range(self):
        self.assertEqual(extract_event_dates("Nov 14–15, 2026"), [date(2026, 11, 14), date(2026, 11, 15)])

    def test_keeps_unknown_date_event_as_unverified(self):
        candidate = {"name": "Meta Global AI Developer Hackathon", "url": "https://example.org/events/meta-ai", "snippet": "Virtual AI hackathon. Apply now."}
        confirmed, possible, _ = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed, [])
        self.assertEqual(len(possible), 1)
        self.assertIn("No event date", possible[0]["date_match"])

    def test_keeps_out_of_range_snippet_as_possible_to_avoid_false_drop(self):
        candidate = {"name": "AI Hackathon", "url": "https://example.org/events/ai-hack", "snippet": "Registration opens Nov 14, 2026."}
        confirmed, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed, [])
        self.assertEqual(len(possible), 1)
        self.assertEqual(diagnostics["outside_date_range"], 1)

    def test_excludes_obvious_directory_and_bootcamp_pages(self):
        candidates = [
            {"name": "Hackathons Directory", "url": "https://example.com/hackathons", "snippet": "Browse events"},
            {"name": "Register for AI BootCamp", "url": "https://example.com/bootcamp", "snippet": "Pre-register for a bootcamp"},
        ]
        confirmed, possible, diagnostics = filter_event_candidates(candidates, "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed + possible, [])
        self.assertEqual(diagnostics["not_individual_event"], 2)

    def test_keeps_specific_event_page_when_title_omits_hackathon(self):
        candidate = {"name": "Global AI Build Challenge", "url": "https://example.org/events/global-ai-build", "snippet": "Join our event and register now."}
        _, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(possible), 1)
        self.assertEqual(diagnostics["not_individual_event"], 0)

    def test_unknown_age_and_mode_are_retained(self):
        candidate = {"name": "Student Hackathon", "url": "https://example.org/events/student-hack", "snippet": "Build with a team."}
        _, possible, _ = filter_event_candidates([candidate], "", date(2027, 3, 1), date(2027, 3, 31), age=14, event_format="Online")
        self.assertEqual(len(possible), 1)
        self.assertIn("Not confirmed", possible[0]["age_status"])
        self.assertIn("not stated", possible[0]["format_status"])

    def test_filters_explicit_age_conflict(self):
        candidate = {"name": "18+ AI Hackathon", "url": "https://example.org/events/ai-hack", "snippet": "Minimum age 18. In-person hackathon."}
        _, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31), age=14)
        self.assertEqual(possible, [])
        self.assertEqual(diagnostics["age_conflict"], 1)

    def test_unknown_format_is_kept_for_online_preference(self):
        candidate = {"name": "AI Hackathon", "url": "https://example.org/events/ai-hack", "snippet": "Register to build a project."}
        _, possible, _ = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31), event_format="Online")
        self.assertEqual(len(possible), 1)
        self.assertIn("kept as a possible", possible[0]["format_status"])


if __name__ == "__main__":
    unittest.main()
