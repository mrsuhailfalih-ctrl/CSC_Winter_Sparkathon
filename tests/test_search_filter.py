import unittest

from utils.search_filter import filter_search_results, is_unnecessary_search_result


class SearchFilterTests(unittest.TestCase):
    def test_hides_broad_collections_and_roundups(self):
        examples = [
            {"title": "Free list of 700+ open AI hackathons, filterable by deadline", "snippet": "Browse open events and filter by prize."},
            {"title": "Every hackathon in 2027", "snippet": "Every hackathon happening in 2027, with dates and city."},
            {"title": "Online Hackathons — Virtual & Remote", "snippet": "Explore 262 online and virtual hackathons."},
            {"title": "Free Online Hackathon Events", "snippet": "Category Business Science & Tech."},
            {"title": "Global Hackathons 2026: Online, Free & Open Worldwide", "snippet": "Global hackathons open for registration now."},
            {"title": "Upcoming AI hackathons in 7 cities, Bond's picks", "snippet": "Every upcoming in-person AI hackathon in seven cities."},
            {"title": "Hackathons", "snippet": "Discover Hackathons on Digitomize and stay in the loop."},
        ]
        self.assertEqual(filter_search_results(examples), [])

    def test_keeps_specific_events_even_when_title_is_generic(self):
        event = {
            "title": "All Hackathons. Hackathons Made Easy: Your Pathway to Innovation",
            "snippet": "A December-holiday AI project: teams of 1–4 build their own AI project online, with finals in Singapore on Sunday 31 January 2027.",
        }
        self.assertFalse(is_unnecessary_search_result(event))
        self.assertEqual(filter_search_results([event]), [event])

    def test_keeps_specific_event_pages(self):
        results = [
            {"title": "The home for AI hackathons", "snippet": "A free 48-hour AI-native online hackathon for builders aged 13–18. $15,560 in prizes. Deadline: Jan 10."},
            {"title": "Climate Code Jam", "snippet": "Teams will build climate tools. Registration deadline: March 15. Prizes total $5,000."},
        ]
        self.assertEqual(filter_search_results(results), results)

    def test_does_not_mutate_or_reformat_items(self):
        item = {"title": "Specific Event", "snippet": "Register by June 1.", "link": "https://example.com"}
        self.assertEqual(filter_search_results([item]), [item])


if __name__ == "__main__":
    unittest.main()
