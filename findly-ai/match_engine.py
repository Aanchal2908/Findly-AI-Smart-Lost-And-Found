"""Explainable, local text-and-context ranking for lost/found reports."""

from collections import Counter
from datetime import date, datetime
import math
import re


MATCH_THRESHOLD = 22.0
MIN_TEXT_SIMILARITY = 0.06
DATE_RELEVANCE_DAYS = 30

_STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "been", "by", "for", "from",
    "has", "have", "in", "is", "it", "its", "of", "on", "or", "the", "this",
    "to", "was", "were", "with", "near", "left", "lost", "found", "item",
}
_LOCATION_NOISE = {"building", "campus", "floor", "hall", "level", "room"}


def _tokens(value):
    words = re.findall(r"[a-z0-9]+", str(value or "").lower())
    normalized = []
    for word in words:
        if word.endswith("ies") and len(word) > 4:
            word = word[:-3] + "y"
        elif word.endswith("s") and len(word) > 4 and not word.endswith("ss"):
            word = word[:-1]
        if word not in _STOP_WORDS:
            normalized.append(word)
    return normalized


def _report_text(report):
    return " ".join(
        str(report.get(field, "") or "")
        for field in ("name", "description", "characteristics", "identifying_features")
    )


def _report_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raw = str(value or "").split(" · ", 1)[0].strip()
    for date_format in ("%b %d, %Y", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(raw, date_format).date()
        except ValueError:
            continue
    return None


def _idf_weights(documents):
    document_frequency = Counter()
    for document in documents:
        document_frequency.update(set(document))
    count = len(documents)
    return {
        token: math.log((count + 1) / (frequency + 1)) + 1
        for token, frequency in document_frequency.items()
    }


def _tfidf_vector(tokens, idf):
    frequencies = Counter(tokens)
    return {token: (frequency * idf.get(token, 1.0)) for token, frequency in frequencies.items()}


def _cosine_similarity(left_tokens, right_tokens, idf):
    left = _tfidf_vector(left_tokens, idf)
    right = _tfidf_vector(right_tokens, idf)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    shared = left.keys() & right.keys()
    return sum(left[token] * right[token] for token in shared) / (left_norm * right_norm)


def _location_similarity(left, right):
    left_tokens = set(_tokens(left)) - _LOCATION_NOISE
    right_tokens = set(_tokens(right)) - _LOCATION_NOISE
    if not left_tokens or not right_tokens:
        return 0.0, []
    shared = sorted(left_tokens & right_tokens)
    return len(shared) / len(left_tokens | right_tokens), shared


def rank_matches(lost_report, reports, threshold=MATCH_THRESHOLD):
    """Return suitable Found candidates ranked against one Lost report.

    Scores are weighted similarities, not probabilities or identity claims. Only
    reports with a Lost status are accepted as the query; only Found reports are
    considered as candidates.
    """
    if not isinstance(lost_report, dict) or str(lost_report.get("type", "")).lower() != "lost":
        return []

    lost_tokens = _tokens(_report_text(lost_report))
    if not lost_tokens:
        return []

    found_reports = [
        report for report in reports
        if isinstance(report, dict) and str(report.get("type", "")).lower() == "found"
    ]
    if not found_reports:
        return []

    found_tokens = [_tokens(_report_text(report)) for report in found_reports]
    idf = _idf_weights([lost_tokens, *found_tokens])
    lost_category = str(lost_report.get("category", "")).strip().casefold()
    lost_location = str(lost_report.get("location", ""))
    lost_date = _report_date(lost_report.get("date"))
    ranked = []

    for report, candidate_tokens in zip(found_reports, found_tokens):
        text_similarity = _cosine_similarity(lost_tokens, candidate_tokens, idf)
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
            0.65 * text_similarity
            + 0.20 * float(category_agrees)
            + 0.10 * location_similarity
            + 0.05 * date_similarity
        )
        shared_terms = sorted(
            set(lost_tokens) & set(candidate_tokens),
            key=lambda token: (-idf.get(token, 1.0), token),
        )
        reasons = []
        differences = []
        if shared_terms:
            reasons.append("Shared terms: " + ", ".join(shared_terms[:8]))
        else:
            differences.append("No descriptive terms overlap")
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

        if score < threshold or text_similarity < MIN_TEXT_SIMILARITY:
            continue
        ranked.append({
            "item": report,
            "score": round(score, 1),
            "text_similarity": round(text_similarity * 100, 1),
            "category_agrees": category_agrees,
            "location_similarity": round(location_similarity * 100, 1),
            "location_terms": location_terms,
            "days_apart": days_apart,
            "date_similarity": round(date_similarity * 100, 1),
            "shared_terms": shared_terms[:8],
            "reasons": reasons,
            "differences": differences,
        })

    return sorted(ranked, key=lambda match: (-match["score"], match["item"].get("id", "")))
