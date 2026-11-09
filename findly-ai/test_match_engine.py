import unittest
from datetime import date

from match_engine import rank_matches


LOST_HEADPHONES = {
    "id": "L-TEST-1",
    "type": "Lost",
    "name": "Wireless headphones",
    "category": "Electronics",
    "description": "Black over-ear wireless headphones lost near the engineering lecture room. Foldable with a scratched headband.",
    "characteristics": "Matte black, small yellow star sticker",
    "location": "Engineering Building",
    "date": "Oct 17, 2026",
}

FOUND_HEADPHONES = {
    "id": "F-TEST-1",
    "type": "Found",
    "name": "Black wireless headset",
    "category": "Electronics",
    "description": "Over-ear headphones found outside the engineering lecture room. Foldable with a scratch on the headband.",
    "characteristics": "Matte black, tiny yellow star sticker",
    "location": "Engineering Building, Room 104",
    "date": "Oct 17, 2026",
}

FOUND_ID_CARD = {
    "id": "F-TEST-2",
    "type": "Found",
    "name": "Student ID card",
    "category": "ID Cards",
    "description": "Clear campus card holder with a blue lanyard found at the sports center.",
    "characteristics": "Clear sleeve, blue cord",
    "location": "Sports Center",
    "date": "Oct 1, 2026",
}

SAME_TYPE_HEADPHONES = {
    **FOUND_HEADPHONES,
    "id": "L-TEST-2",
    "type": "Lost",
}


class MatchEngineTests(unittest.TestCase):
    def test_ranks_expected_found_match_and_explains_it(self):
        results = rank_matches(
            LOST_HEADPHONES,
            [FOUND_ID_CARD, SAME_TYPE_HEADPHONES, FOUND_HEADPHONES],
        )

        self.assertEqual([result["item"]["id"] for result in results], ["F-TEST-1"])
        match = results[0]
        self.assertGreater(match["score"], 0)
        self.assertIn("headphone", match["shared_terms"])
        self.assertTrue(match["category_agrees"])
        self.assertEqual(match["days_apart"], 0)
        self.assertTrue(any("Category agrees" in reason for reason in match["reasons"]))
        self.assertTrue(any("engineering" in reason.lower() for reason in match["reasons"]))

    def test_excludes_nonmatching_found_report(self):
        self.assertEqual(rank_matches(LOST_HEADPHONES, [FOUND_ID_CARD]), [])

    def test_only_lost_query_and_found_candidates_are_compared(self):
        self.assertEqual(rank_matches(FOUND_HEADPHONES, [LOST_HEADPHONES]), [])
        self.assertEqual(rank_matches(LOST_HEADPHONES, [SAME_TYPE_HEADPHONES]), [])

    def test_empty_or_unreadable_report_text_returns_no_matches(self):
        empty_lost = {"type": "Lost", "name": "", "description": "", "characteristics": ""}
        self.assertEqual(rank_matches(empty_lost, [FOUND_HEADPHONES]), [])
        self.assertEqual(rank_matches(LOST_HEADPHONES, []), [])

    def test_accepts_date_objects(self):
        lost = {**LOST_HEADPHONES, "date": date(2026, 10, 17)}
        found = {**FOUND_HEADPHONES, "date": date(2026, 10, 17)}
        results = rank_matches(lost, [found])
        self.assertEqual(results[0]["days_apart"], 0)


if __name__ == "__main__":
    unittest.main()
