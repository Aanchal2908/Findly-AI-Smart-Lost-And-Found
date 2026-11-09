import unittest
from unittest.mock import patch

from evaluation import EVALUATION_PAIRS, _safe_ratio, evaluate_comparison, evaluate_pairs
from semantic_matcher import SemanticBackendUnavailable


class EvaluationTests(unittest.TestCase):
    def test_measured_pairwise_metrics_match_dataset_predictions(self):
        evaluation = evaluate_pairs()

        self.assertEqual(evaluation["evaluated_pairs"], 4)
        self.assertEqual(
            evaluation["counts"],
            {
                "true_positive": 2,
                "false_positive": 0,
                "true_negative": 1,
                "false_negative": 1,
            },
        )
        self.assertEqual(evaluation["metrics"]["precision"], 1.0)
        self.assertAlmostEqual(evaluation["metrics"]["recall"], 2 / 3)
        self.assertAlmostEqual(evaluation["metrics"]["f1"], 0.8)

    def test_dataset_covers_required_language_scenarios(self):
        scenarios = {pair["scenario"] for pair in EVALUATION_PAIRS}
        self.assertEqual(
            scenarios,
            {
                "Exact wording",
                "Partially overlapping wording",
                "Unrelated items",
                "Synonyms without shared wording",
            },
        )

    def test_synonym_pair_is_measured_as_a_false_negative(self):
        evaluation = evaluate_pairs()
        synonym_result = next(
            result for result in evaluation["results"]
            if result["pair_id"] == "synonym-only"
        )
        self.assertTrue(synonym_result["expected_match"])
        self.assertFalse(synonym_result["predicted_match"])
        self.assertEqual(synonym_result["outcome"], "False negative")

    def test_zero_denominators_return_zero(self):
        self.assertEqual(_safe_ratio(0, 0), 0.0)
        self.assertEqual(_safe_ratio(3, 0), 0.0)

    def test_no_positive_labels_has_zero_precision_recall_and_f1(self):
        negative_pair = next(
            pair for pair in EVALUATION_PAIRS if not pair["expected_match"]
        )
        evaluation = evaluate_pairs([negative_pair])
        self.assertEqual(
            evaluation["metrics"],
            {"precision": 0.0, "recall": 0.0, "f1": 0.0},
        )

    def test_comparison_preserves_baseline_and_marks_semantic_unavailable(self):
        with patch(
            "evaluation.rank_semantic_matches",
            side_effect=SemanticBackendUnavailable("model not installed for test"),
        ):
            comparison = evaluate_comparison()

        self.assertEqual(comparison["baseline"]["metrics"]["precision"], 1.0)
        self.assertEqual(comparison["baseline"]["evaluated_pairs"], 4)
        self.assertFalse(comparison["semantic"]["available"])
        self.assertIn("model not installed", comparison["semantic"]["error"])


if __name__ == "__main__":
    unittest.main()
