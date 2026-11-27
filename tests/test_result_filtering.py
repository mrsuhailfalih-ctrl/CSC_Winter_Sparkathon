import unittest
from datetime import date

from utils.result_filtering import extract_event_dates, filter_event_candidates


class ResultFilteringTests(unittest.TestCase):
    def test_extracts_abbreviated_month_and_date_range(self):
        self.assertEqual(extract_event_dates("Nov 14–15, 2026"), [date(2026, 11, 14), date(2026, 11, 15)])

    def test_excludes_known_stale_event(self):
        candidate = {"name": "Veritas AI International High School Hackathon", "snippet": "Nov 14, 2026. Free virtual AI hackathon."}
        confirmed, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed, [])
        self.assertEqual(possible, [])
        self.assertEqual(diagnostics["outside_date_range"], 1)

    def test_keeps_specific_unknown_date_event_as_unverified(self):
        candidate = {"name": "Meta Global AI Developer Hackathon", "snippet": "Virtual AI hackathon. Apply now."}
        confirmed, possible, _ = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed, [])
        self.assertEqual(possible, [candidate])

    def test_rejects_directory_or_bootcamp_pages(self):
        candidates = [
            {"name": "Hack4Hack (Hack 4 Hack) — Online Hackathons, AI Challenges", "url": "https://hack4hack.com/", "snippet": "Find upcoming events"},
            {"name": "Register For AI BootCamp", "url": "https://example.com/bootcamp", "snippet": "Pre-register for a hackathon"},
            {"name": "Online Python hackathons 2026 / 2027 - dev.events", "url": "https://dev.events/", "snippet": "Hackathons and online challenges"},
        ]
        confirmed, possible, diagnostics = filter_event_candidates(candidates, "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(confirmed + possible, [])
        self.assertEqual(diagnostics["not_individual_event"], 3)

    def test_accepts_specific_event_url_when_title_omits_hackathon(self):
        candidate = {"name": "Global AI Build Challenge", "url": "https://example.org/events/global-ai-build", "snippet": "Join our hackathon for AI developers. Applications open."}
        _, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(possible, [candidate])
        self.assertEqual(diagnostics["not_individual_event"], 0)

    def test_does_not_reject_specific_hackathon_for_good_title(self):
        candidate = {"name": "AI Hackathon for Good", "url": "https://example.org/events/ai-for-good", "snippet": "Apply now for the event."}
        _, possible, diagnostics = filter_event_candidates([candidate], "AI", date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(possible, [candidate])
        self.assertEqual(diagnostics["not_individual_event"], 0)


if __name__ == "__main__":
    unittest.main()
