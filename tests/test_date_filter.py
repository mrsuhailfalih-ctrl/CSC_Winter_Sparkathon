import unittest
from datetime import date

from utils.search_filter import extract_explicit_dates, filter_search_results


class DateRangeFilterTests(unittest.TestCase):
    def test_extracts_explicit_month_date_range(self):
        dates = extract_explicit_dates("The event runs March 1-3, 2027.")
        self.assertEqual(dates, [date(2027, 3, 1), date(2027, 3, 3)])

    def test_extracts_iso_dates(self):
        dates = extract_explicit_dates("Dates: 2027-03-15 to 2027-03-16")
        self.assertIn(date(2027, 3, 15), dates)
        self.assertIn(date(2027, 3, 16), dates)

    def test_does_not_treat_publication_date_as_event_date(self):
        text = "Published Sep 28, 2026. View the 2027 competition details."
        self.assertEqual(extract_explicit_dates(text), [date(2026, 9, 28)])


if __name__ == "__main__":
    unittest.main()
