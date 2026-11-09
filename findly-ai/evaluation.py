"""Pairwise evaluation for the current lexical Lost/Found ranker."""

from match_engine import MATCH_THRESHOLD, rank_matches
from semantic_matcher import SemanticBackendUnavailable, rank_semantic_matches


EVALUATION_PAIRS = (
    {
        "pair_id": "exact-wording",
        "scenario": "Exact wording",
        "expected_match": True,
        "lost": {
            "id": "E-L-001", "type": "Lost", "name": "Blue steel water bottle",
            "category": "Accessories",
            "description": "Insulated bottle lost near north library with mountain sticker.",
            "characteristics": "blue body, silver cap", "location": "North Library",
            "date": "Oct 18, 2026",
        },
        "found": {
            "id": "E-F-001", "type": "Found", "name": "Blue steel water bottle",
            "category": "Accessories",
            "description": "Insulated bottle found at north library with mountain sticker.",
            "characteristics": "blue body, silver cap", "location": "North Library, Level 2",
            "date": "Oct 18, 2026",
        },
    },
    {
        "pair_id": "partial-overlap",
        "scenario": "Partially overlapping wording",
        "expected_match": True,
        "lost": {
            "id": "E-L-002", "type": "Lost", "name": "Red canvas backpack",
            "category": "Bags",
            "description": "Canvas backpack with stitched initials, lost near student center.",
            "characteristics": "red fabric, brass zipper", "location": "Student Center",
            "date": "Oct 17, 2026",
        },
        "found": {
            "id": "E-F-002", "type": "Found", "name": "Red backpack",
            "category": "Bags",
            "description": "Canvas bag with initials and brass zipper, found by student centre.",
            "characteristics": "red fabric, brass zip", "location": "Student Centre",
            "date": "Oct 18, 2026",
        },
    },
    {
        "pair_id": "unrelated-items",
        "scenario": "Unrelated items",
        "expected_match": False,
        "lost": {
            "id": "E-L-003", "type": "Lost", "name": "Graphing calculator",
            "category": "Electronics",
            "description": "Black calculator with solar strip, lost in math lab.",
            "characteristics": "green display", "location": "Math Lab",
            "date": "Oct 17, 2026",
        },
        "found": {
            "id": "E-F-003", "type": "Found", "name": "Folding umbrella",
            "category": "Accessories",
            "description": "Green folding umbrella with wooden handle, found by cafe.",
            "characteristics": "curved wood grip", "location": "Cafe",
            "date": "Oct 17, 2026",
        },
    },
    {
        "pair_id": "synonym-only",
        "scenario": "Synonyms without shared wording",
        "expected_match": True,
        "lost": {
            "id": "E-L-004", "type": "Lost", "name": "Rain shield",
            "category": "Accessories",
            "description": "Waterproof canopy carried during a storm near the cafe.",
            "characteristics": "collapsible, dark textile, curved hardwood grip",
            "location": "Student Center", "date": "Oct 17, 2026",
        },
        "found": {
            "id": "E-F-004", "type": "Found", "name": "Umbrella",
            "category": "Accessories",
            "description": "Parasol recovered beside the student center entrance.",
            "characteristics": "folding, ebony cloth, bowed timber handle",
            "location": "Student Center", "date": "Oct 17, 2026",
        },
    },
)


def _safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def evaluate_pairs(pairs=EVALUATION_PAIRS, threshold=MATCH_THRESHOLD):
    """Predict labeled Lost/Found pairs and calculate pairwise metrics."""
    results = []
    true_positive = false_positive = true_negative = false_negative = 0

    for pair in pairs:
        lost = pair["lost"]
        found = pair["found"]
        matches = rank_matches(lost, [found], threshold=threshold)
        predicted = any(match["item"].get("id") == found.get("id") for match in matches)
        expected = bool(pair["expected_match"])
        score = next((match["score"] for match in matches if match["item"].get("id") == found.get("id")), None)

        if expected and predicted:
            true_positive += 1
            outcome = "True positive"
        elif not expected and predicted:
            false_positive += 1
            outcome = "False positive"
        elif not expected and not predicted:
            true_negative += 1
            outcome = "True negative"
        else:
            false_negative += 1
            outcome = "False negative"

        results.append({
            "pair_id": pair["pair_id"],
            "scenario": pair["scenario"],
            "lost_name": lost.get("name", ""),
            "found_name": found.get("name", ""),
            "expected_match": expected,
            "predicted_match": predicted,
            "score": score,
            "outcome": outcome,
        })

    precision = _safe_ratio(true_positive, true_positive + false_positive)
    recall = _safe_ratio(true_positive, true_positive + false_negative)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    total = len(results)

    return {
        "threshold": threshold,
        "evaluated_pairs": total,
        "counts": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
        "metrics": {"precision": precision, "recall": recall, "f1": f1},
        "results": results,
    }


def evaluate_semantic_pairs(pairs=EVALUATION_PAIRS, threshold=MATCH_THRESHOLD):
    """Evaluate the optional pretrained backend, without counting fallback as semantic."""
    results = []
    true_positive = false_positive = true_negative = false_negative = 0

    try:
        for pair in pairs:
            lost = pair["lost"]
            found = pair["found"]
            matches = rank_semantic_matches(lost, [found], threshold=threshold)
            predicted = any(match["item"].get("id") == found.get("id") for match in matches)
            expected = bool(pair["expected_match"])
            score = next(
                (match["score"] for match in matches if match["item"].get("id") == found.get("id")),
                None,
            )

            if expected and predicted:
                true_positive += 1
                outcome = "True positive"
            elif not expected and predicted:
                false_positive += 1
                outcome = "False positive"
            elif not expected and not predicted:
                true_negative += 1
                outcome = "True negative"
            else:
                false_negative += 1
                outcome = "False negative"

            results.append({
                "pair_id": pair["pair_id"],
                "scenario": pair["scenario"],
                "lost_name": lost.get("name", ""),
                "found_name": found.get("name", ""),
                "expected_match": expected,
                "predicted_match": predicted,
                "score": score,
                "outcome": outcome,
            })
    except SemanticBackendUnavailable as error:
        return {"available": False, "error": str(error), "results": []}

    precision = _safe_ratio(true_positive, true_positive + false_positive)
    recall = _safe_ratio(true_positive, true_positive + false_negative)
    f1 = _safe_ratio(2 * precision * recall, precision + recall)
    return {
        "available": True,
        "threshold": threshold,
        "evaluated_pairs": len(results),
        "counts": {
            "true_positive": true_positive,
            "false_positive": false_positive,
            "true_negative": true_negative,
            "false_negative": false_negative,
        },
        "metrics": {"precision": precision, "recall": recall, "f1": f1},
        "results": results,
    }


def evaluate_comparison(pairs=EVALUATION_PAIRS, threshold=MATCH_THRESHOLD):
    """Return baseline and semantic evaluation results for the same labeled pairs."""
    return {
        "baseline": evaluate_pairs(pairs, threshold),
        "semantic": evaluate_semantic_pairs(pairs, threshold),
    }
