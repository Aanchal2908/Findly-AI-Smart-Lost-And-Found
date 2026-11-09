"""Optional, cache-only pretrained sentence-embedding matcher."""

from functools import lru_cache
import math

from match_engine import (
    DATE_RELEVANCE_DAYS,
    MATCH_THRESHOLD,
    _location_similarity,
    _report_date,
    _report_text,
    _tokens,
    rank_matches,
)


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MIN_SEMANTIC_SIMILARITY = 0.20


class SemanticBackendUnavailable(RuntimeError):
    """Raised when the optional package or locally cached model is unavailable."""


@lru_cache(maxsize=1)
def _load_model():
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as error:
        raise SemanticBackendUnavailable(
            "Optional sentence-transformers is not installed. Use the TF-IDF baseline "
            "or install the optional semantic requirements."
        ) from error

    try:
        return SentenceTransformer(
            MODEL_NAME,
            device="cpu",
            local_files_only=True,
        )
    except Exception as error:
        raise SemanticBackendUnavailable(
            f"Pretrained model {MODEL_NAME} is not available in the local cache. "
            "The semantic mode never downloads model files automatically; use the "
            "TF-IDF baseline or follow the documented model setup command."
        ) from error


def _cosine_similarity(left, right):
    left = [float(value) for value in left]
    right = [float(value) for value in right]
    if len(left) != len(right):
        raise SemanticBackendUnavailable("The embedding model returned inconsistent vector sizes.")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if not left_norm or not right_norm:
        return 0.0
    return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)


def rank_semantic_matches(lost_report, reports, threshold=MATCH_THRESHOLD, model=None):
    """Rank Found candidates using cached MiniLM embeddings and existing context signals."""
    if not isinstance(lost_report, dict) or str(lost_report.get("type", "")).lower() != "lost":
        return []

    found_reports = [
        report for report in reports
        if isinstance(report, dict) and str(report.get("type", "")).lower() == "found"
    ]
    if not found_reports:
        return []

    report_texts = [_report_text(lost_report)] + [_report_text(report) for report in found_reports]
    if not _tokens(report_texts[0]):
        return []

    encoder = model or _load_model()
    try:
        vectors = encoder.encode(
            report_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    except Exception as error:
        raise SemanticBackendUnavailable("The local MiniLM model could not encode these reports.") from error

    if len(vectors) != len(report_texts):
        raise SemanticBackendUnavailable("The embedding model returned an unexpected number of vectors.")

    lost_vector = vectors[0]
    lost_category = str(lost_report.get("category", "")).strip().casefold()
    lost_location = str(lost_report.get("location", ""))
    lost_date = _report_date(lost_report.get("date"))
    ranked = []

    lost_tokens = _tokens(report_texts[0])
    for index, (report, vector) in enumerate(zip(found_reports, vectors[1:]), start=1):
        semantic_similarity = max(0.0, min(1.0, _cosine_similarity(lost_vector, vector)))
        category = str(report.get("category", "")).strip().casefold()
        category_agrees = bool(lost_category and category and lost_category == category)
        location_similarity, location_terms = _location_similarity(
            lost_location, str(report.get("location", ""))
        )
        found_date = _report_date(report.get("date"))
        days_apart = abs((lost_date - found_date).days) if lost_date and found_date else None
        date_similarity = (
            max(0.0, 1.0 - days_apart / DATE_RELEVANCE_DAYS)
            if days_apart is not None
            else 0.0
        )
        score = 100 * (
            0.65 * semantic_similarity
            + 0.20 * float(category_agrees)
            + 0.10 * location_similarity
            + 0.05 * date_similarity
        )
        shared_terms = sorted(set(lost_tokens) & set(_tokens(report_texts[index])))
        reasons = [f"Pretrained MiniLM semantic similarity: {semantic_similarity:.1%}"]
        differences = []
        if shared_terms:
            reasons.append("Shared wording: " + ", ".join(shared_terms[:8]))
        else:
            differences.append("No exact descriptive terms overlap; semantic similarity carries the text signal")
        if category_agrees:
            reasons.append(f"Category agrees: {report.get('category')}")
        elif lost_category or category:
            differences.append(
                f"Category differs: {lost_report.get('category') or 'not provided'} vs "
                f"{report.get('category') or 'not provided'}"
            )
        if location_terms:
            reasons.append("Location terms overlap: " + ", ".join(location_terms))
        elif lost_location or report.get("location"):
            differences.append("No meaningful location terms overlap")
        if days_apart is None:
            differences.append("Date is missing or could not be read")
        elif days_apart == 0:
            reasons.append("Reported on the same date")
        else:
            reasons.append(f"Reported {days_apart} days apart")
            if days_apart > 7:
                differences.append(f"Reports are {days_apart} days apart")

        if score < threshold or semantic_similarity < MIN_SEMANTIC_SIMILARITY:
            continue
        ranked.append({
            "item": report,
            "score": round(score, 1),
            "text_similarity": round(semantic_similarity * 100, 1),
            "semantic_similarity": round(semantic_similarity * 100, 1),
            "category_agrees": category_agrees,
            "location_similarity": round(location_similarity * 100, 1),
            "location_terms": location_terms,
            "days_apart": days_apart,
            "date_similarity": round(date_similarity * 100, 1),
            "shared_terms": shared_terms[:8],
            "reasons": reasons,
            "differences": differences,
            "matching_mode": "minilm",
        })

    return sorted(ranked, key=lambda match: (-match["score"], match["item"].get("id", "")))


def rank_matches_with_mode(lost_report, reports, mode="lexical", threshold=MATCH_THRESHOLD, model=None):
    """Use semantic ranking when requested; safely fall back to the lexical baseline."""
    if mode != "semantic":
        matches = rank_matches(lost_report, reports, threshold=threshold)
        return matches, "lexical", None

    try:
        matches = rank_semantic_matches(lost_report, reports, threshold=threshold, model=model)
        return matches, "semantic", None
    except SemanticBackendUnavailable as error:
        fallback = [dict(match, matching_mode="lexical_fallback") for match in rank_matches(
            lost_report, reports, threshold=threshold
        )]
        return fallback, "lexical_fallback", str(error)
