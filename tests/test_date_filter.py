import unittest
from datetime import date

from utils.search_filter import extract_explicit_dates, filter_search_results


class DateRangeFilterTests(unittest.TestCase):
    def test_extracts_explicit_month_date_range(self):
        self.assertEqual(extract_explicit_dates("The event runs March 1-3, 2027."), [date(2027, 3, 1), date(2027, 3, 3)])

    def test_extracts_iso_dates(self):
        self.assertEqual(extract_explicit_dates("Dates: 2027-03-15 to 2027-03-16"), [date(2027, 3, 15), date(2027, 3, 16)])

    def test_strict_filter_keeps_matching_event_period(self):
        rows = [{"title": "AI Hackathon", "snippet": "Hackathon dates: March 15-16, 2027.", "date": "2026-09-28", "link": "https://example.test/event"}]
        filtered = filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["date_verification"]["status"], "snippet_match")

    def test_removes_confirmed_out_of_range_schedule(self):
        rows = [{"title": "AI Hackathon", "snippet": "Hackathon period: February 10-March 15, 2026."}]
        self.assertEqual(filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31)), [])

    def test_ignores_publication_and_registration_deadline_dates(self):
        rows = [{"title": "AI Hackathon", "snippet": "Published Sep 28, 2026. Registration deadline: March 15, 2027."}]
        filtered = filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["date_verification"]["status"], "unverified")

    def test_keeps_unknown_date_as_unverified(self):
        rows = [{"title": "USAII Global AI Hackathon 2026", "snippet": "Virtual student competition. Registration is open."}]
        filtered = filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["date_verification"]["status"], "unverified")

    def test_model_dates_outside_range_are_removed(self):
        rows = [{"title": "Past Event", "event_start_date": "2026-02-10", "event_end_date": "2026-03-15"}]
        self.assertEqual(filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31)), [])

    def test_model_dates_matching_range_are_kept(self):
        rows = [{"title": "Event", "event_start_date": "2027-03-15", "event_end_date": "2027-03-16"}]
        filtered = filter_search_results(rows, date(2027, 3, 1), date(2027, 3, 31))
        self.assertEqual(filtered[0]["date_verification"]["status"], "model_date_match")


if __name__ == "__main__":
    unittest.main()
