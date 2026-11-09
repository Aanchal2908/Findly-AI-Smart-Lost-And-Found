import unittest
from unittest.mock import patch

from evaluation import EVALUATION_PAIRS
from semantic_matcher import (
    SemanticBackendUnavailable,
    rank_matches_with_mode,
    rank_semantic_matches,
)


class FakeSentenceEncoder:
    def encode(self, texts, **kwargs):
        vectors = []
        for text in texts:
            lowered = text.lower()
            if "rain shield" in lowered or "umbrella" in lowered or "parasol" in lowered:
                vectors.append([1.0, 0.0])
            else:
                vectors.append([0.0, 1.0])
        return vectors


class SemanticMatcherTests(unittest.TestCase):
    def test_semantic_ranker_can_match_a_synonym_pair_with_injected_encoder(self):
        pair = EVALUATION_PAIRS[3]
        results = rank_semantic_matches(
            pair["lost"],
            [pair["found"]],
            model=FakeSentenceEncoder(),
        )

        self.assertEqual([result["item"]["id"] for result in results], [pair["found"]["id"]])
        self.assertEqual(results[0]["semantic_similarity"], 100.0)
        self.assertTrue(any("MiniLM semantic similarity" in reason for reason in results[0]["reasons"]))
        self.assertTrue(any("No exact descriptive terms" in difference for difference in results[0]["differences"]))

    def test_semantic_ranker_still_compares_only_found_reports(self):
        pair = EVALUATION_PAIRS[0]
        same_type = {**pair["found"], "id": "OTHER-LOST", "type": "Lost"}
        results = rank_semantic_matches(
            pair["lost"],
            [same_type, pair["found"]],
            model=FakeSentenceEncoder(),
        )

        self.assertEqual([result["item"]["id"] for result in results], [pair["found"]["id"]])

    def test_missing_semantic_backend_falls_back_to_lexical_baseline(self):
        pair = EVALUATION_PAIRS[0]
        with patch(
            "semantic_matcher._load_model",
            side_effect=SemanticBackendUnavailable("test: model unavailable"),
        ):
            results, active_mode, warning = rank_matches_with_mode(
                pair["lost"], [pair["found"]], mode="semantic"
            )

        self.assertEqual(active_mode, "lexical_fallback")
        self.assertIn("test: model unavailable", warning)
        self.assertEqual([result["item"]["id"] for result in results], [pair["found"]["id"]])
        self.assertEqual(results[0]["matching_mode"], "lexical_fallback")

    def test_default_mode_keeps_the_existing_baseline(self):
        pair = EVALUATION_PAIRS[0]
        results, active_mode, warning = rank_matches_with_mode(pair["lost"], [pair["found"]])

        self.assertEqual(active_mode, "lexical")
        self.assertIsNone(warning)
        self.assertEqual(results[0]["matching_mode"] if "matching_mode" in results[0] else None, None)


if __name__ == "__main__":
    unittest.main()
