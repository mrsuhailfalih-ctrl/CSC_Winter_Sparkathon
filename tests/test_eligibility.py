import unittest
from unittest.mock import patch

from utils.eligibility import _age_evidence, parse_age_bounds, verify_age_rule


class AgeEvidenceTests(unittest.TestCase):
    def test_extracts_age_related_sentence(self):
        evidence = _age_evidence("Welcome. Participants must be ages 13-18. Register today.")
        self.assertEqual(evidence, ["Participants must be ages 13-18."])

    def test_ignores_scripts_in_parser(self):
        from utils.eligibility import _TextExtractor
        parser = _TextExtractor()
        parser.feed("<p>Ages 13-18</p><script>hidden age 5</script>")
        self.assertNotIn("hidden", " ".join(parser.parts))

    def test_parse_age_bounds(self):
        self.assertEqual(parse_age_bounds("13", "18"), (13, 18))
        self.assertEqual(parse_age_bounds("", "18"), (None, 18))
        with self.assertRaises(ValueError):
            parse_age_bounds("19", "18")

    @patch("utils.eligibility._public_https_url", return_value=False)
    def test_blocks_non_public_or_unsecured_page(self, _):
        result = verify_age_rule("http://example.com/rules")
        self.assertTrue(result["error"])


if __name__ == "__main__":
    unittest.main()
