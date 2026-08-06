"""Deterministic evidence for the six Part 2 PM example claims."""

from __future__ import annotations

import math
import re
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import fmean, stdev
from typing import Any, Iterable


ARABIC_DIACRITICS = re.compile(r"[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06edـ]")
WHITESPACE = re.compile(r"\s+")


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    value = unicodedata.normalize("NFKC", value).lower()
    value = ARABIC_DIACRITICS.sub("", value)
    value = value.translate(str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ى": "ي", "ة": "ه"}))
    return WHITESPACE.sub(" ", value).strip()


THEME_DEFINITIONS: dict[str, dict[str, Any]] = {
    "wait_time_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing an Arabic/English wait, delay, queue, or crowding term",
        "terms": (
            "انتظار", "انتظر", "ننتظر", "تاخير", "تاخر", "متاخر", "بطيء", "بطيئ", "بطء",
            "طابور", "ازدحام", "زحمه", "slow", "wait", "delay", "queue", "crowd",
        ),
    },
    "packaging_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a packaging, cup, lid, leak, spill, container, or bag term",
        "terms": (
            "تغليف", "علبه", "علب", "كوب", "اكواب", "غطاء", "تسريب", "يسرب", "انسكب",
            "كيس", "packag", "container", "cup", "lid", "leak", "spill", "bag",
        ),
    },
    "delivery_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a delivery, driver, or pickup term",
        "terms": ("توصيل", "مندوب", "سائق", "استلام", "delivery", "driver", "pickup"),
    },
    "product_quality_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a taste, drink, coffee, dessert, freshness, or temperature term",
        "terms": (
            "طعم", "مذاق", "قهوه", "مشروب", "حلا", "كيك", "كرواسون", "بارد", "حار",
            "جوده", "طازج", "taste", "coffee", "drink", "dessert", "fresh", "cold", "hot",
        ),
    },
    "service_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a service, staff, employee, or attitude term",
        "terms": ("خدمه", "موظف", "عامل", "كاشير", "تعامل", "service", "staff", "employee", "cashier", "attitude"),
    },
    "value_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a price, value, expensive, offer, or discount term",
        "terms": ("سعر", "اسعار", "غالي", "قيمه", "عرض", "خصم", "price", "value", "expensive", "offer", "discount"),
    },
    "cleanliness_complaint": {
        "requires_low_rating": True,
        "description": "1-3 star review containing a cleanliness, dirty, restroom, or hygiene term",
        "terms": ("نظافه", "وسخ", "دوره مياه", "حمام", "clean", "dirty", "restroom", "hygiene"),
    },
    "repeat_visit_language": {
        "requires_low_rating": False,
        "description": "Review containing a defined prior/repeated-visit phrase; a language proxy, not a customer-status label",
        "terms": (
            "كالعاده", "دائما", "دايما", "دايم", "كل مره", "من زمان", "من سنوات", "زبون دائم",
            "عميل دائم", "مره ثانيه", "رجعت", "نرجع", "اجيهم", "اعتدت", "معتاد", "usual",
            "always", "again", "regular", "every time", "long-time",
        ),
    },
    "loyalty_program_mention": {
        "requires_low_rating": False,
        "description": "Review containing a loyalty-program, points, rewards, or membership term",
        "terms": ("برنامج الولاء", "ولاء", "نقاط", "مكافات", "عضويه", "loyalty", "rewards", "membership", "points"),
    },
}

COMPLAINT_THEMES = (
    "wait_time_complaint",
    "packaging_complaint",
    "delivery_complaint",
    "product_quality_complaint",
    "service_complaint",
    "value_complaint",
    "cleanliness_complaint",
)

CLAIM_CLASSIFICATIONS = (
    {
        "claim": "(a) Wait-time complaints doubled this quarter, from 37 to 75.",
        "classification": "Minable with careful definitions",
        "as_written": "Not reproducible from this snapshot",
        "reason": "Wait-time complaints require a validated aspect rule, and the export contains only one trailing 90-day window rather than current and prior quarters.",
        "strongest_supported_version": "Within two predeclared equal-duration halves of this snapshot, report the count and rate of reviews matching a validated wait-time-complaint definition, with n and review IDs.",
    },
    {
        "claim": "(b) 61 customers reviewed both brands; taste is 4.4 vs 4.0.",
        "classification": "Split: overlap directly computable; taste minable with careful definitions",
        "as_written": "Partly reproducible, but not as one atomic fact",
        "reason": "Stable reviewer IDs make overlap exact. Stars are overall ratings; the structured food sub-rating is not a pure taste rating, and text-based taste needs a validated extractor.",
        "strongest_supported_version": "State exact unique-reviewer overlap, then separately report customer-balanced overall stars and the closest structured food sub-rating with coverage; do not rename food as taste.",
    },
    {
        "claim": "(c) Your regulars are going quiet; repeat-customer language is down 38%.",
        "classification": "Inference that must be hedged",
        "as_written": "The behavioral conclusion is unsupported",
        "reason": "Repeat-visit phrases are observable, but they neither identify all regulars nor measure visit frequency or silence outside public reviews.",
        "strongest_supported_version": "The share of reviews containing a defined repeat-visit-language proxy changed by X within the snapshot; this is not evidence that regular customers visited less.",
    },
    {
        "claim": "(d) Competitor A fixed wait time; reviews prove it worked and gained 0.4 stars.",
        "classification": "Inference that must be hedged",
        "as_written": "The intervention and causal effect are unobservable",
        "reason": "The review export can show temporal association only; it has no intervention date, operational wait measurements, or causal control.",
        "strongest_supported_version": "The wait-time-complaint proxy and mean review stars moved by X over two defined periods; the data does not identify a fix or attribute the change to one.",
    },
    {
        "claim": "(e) A loyalty program is why customers forgive mistakes.",
        "classification": "Judgment beyond what the data supports",
        "as_written": "Not reproducible",
        "reason": "Program exposure, membership, redemption, mistakes, and counterfactual behavior are absent. Text co-occurrence cannot establish motive or causality.",
        "strongest_supported_version": "Report how often loyalty-program terms appear and, if sufficiently supported, their co-occurrence with issue reviews; do not infer forgiveness or why it occurred.",
    },
    {
        "claim": "(f) First move: fix delivery packaging; it protects the product lead.",
        "classification": "Judgment beyond what the data supports",
        "as_written": "Not defensible from reviews alone",
        "reason": "Theme growth can be estimated, but priority, root cause, feasible intervention, and protection of an undefined lead require business and operational context.",
        "strongest_supported_version": "Flag an eligible, fastest-rising packaging-complaint proxy as an observation and propose a bounded validation test; assign priority only after client context confirms impact, controllability, cost, and ownership.",
    },
)


def connect(database_path: Path | str) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def wilson_interval(matches: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return (0.0, 0.0)
    proportion = matches / total
    denominator = 1 + z * z / total
    center = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def mean_interval(values: list[float], z: float = 1.96) -> tuple[float | None, float | None]:
    if not values:
        return (None, None)
    mean = fmean(values)
    if len(values) == 1:
        return (mean, mean)
    margin = z * stdev(values) / math.sqrt(len(values))
    return (mean - margin, mean + margin)


def matches_theme(text: str | None, stars: int, theme: str) -> bool:
    definition = THEME_DEFINITIONS[theme]
    if definition["requires_low_rating"] and stars > 3:
        return False
    normalized = normalize_text(text)
    return bool(normalized) and any(normalize_text(term) in normalized for term in definition["terms"])


def database_profile(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    query = """
        SELECT brand_name, COUNT(*) AS unique_reviews, COUNT(DISTINCT reviewer_id) AS reviewers,
               COUNT(DISTINCT branch_id) AS reviewed_branches,
               MIN(substr(published_at, 1, 10)) AS first_date,
               MAX(substr(published_at, 1, 10)) AS last_date,
               ROUND(AVG(stars), 3) AS mean_stars,
               SUM(review_text IS NOT NULL AND trim(review_text) <> '') AS reviews_with_text,
               SUM(owner_response_text IS NOT NULL) AS owner_responses
        FROM reviews GROUP BY brand_name ORDER BY brand_name
    """
    return [dict(row) for row in connection.execute(query)]


def data_quality(connection: sqlite3.Connection) -> dict[str, Any]:
    scalar = lambda query: connection.execute(query).fetchone()[0]
    return {
        "source_review_rows": scalar("SELECT COUNT(*) FROM source_review_records"),
        "unique_review_ids": scalar("SELECT COUNT(*) FROM reviews"),
        "exact_duplicate_source_rows": scalar("SELECT COUNT(*) FROM source_review_records WHERE is_exact_duplicate = 1"),
        "branches": scalar("SELECT COUNT(*) FROM branches"),
        "orphan_reviews": scalar("SELECT COUNT(*) FROM reviews r LEFT JOIN branches b USING(branch_id) WHERE b.branch_id IS NULL"),
        "foreign_key_errors": len(connection.execute("PRAGMA foreign_key_check").fetchall()),
        "integrity_check": scalar("PRAGMA integrity_check"),
        "reviews_without_text": scalar("SELECT COUNT(*) FROM reviews WHERE review_text IS NULL OR trim(review_text) = ''"),
        "record_language_ar": scalar("SELECT COUNT(*) FROM reviews WHERE record_language = 'ar'"),
        "detected_arabic_text": scalar("SELECT COUNT(*) FROM reviews WHERE original_language = 'ar'"),
        "detected_english_text": scalar("SELECT COUNT(*) FROM reviews WHERE original_language IN ('en', 'en-GB', 'en-Arab')"),
        "unknown_original_language": scalar("SELECT COUNT(*) FROM reviews WHERE original_language IS NULL"),
    }


def analysis_window(connection: sqlite3.Connection) -> dict[str, Any]:
    minimum, maximum = connection.execute("SELECT MIN(published_at), MAX(published_at) FROM reviews").fetchone()
    start = datetime.fromisoformat(minimum.replace("Z", "+00:00"))
    end = datetime.fromisoformat(maximum.replace("Z", "+00:00"))
    midpoint = start + (end - start) / 2
    return {
        "start": start,
        "end": end,
        "midpoint": midpoint,
        "duration_days": (end - start).total_seconds() / 86400,
        "early_label": f"{start.date()} to {midpoint.date()} (before midpoint timestamp)",
        "recent_label": f"{midpoint.date()} to {end.date()} (from midpoint timestamp)",
    }


def _review_rows(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(
        "SELECT review_id, brand_name, branch_id, reviewer_id, review_text, stars, published_at FROM reviews"
    )]


def theme_trends(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    window = analysis_window(connection)
    midpoint = window["midpoint"]
    reviews = _review_rows(connection)
    text_totals: dict[tuple[str, str], int] = Counter()
    matches: dict[tuple[str, str, str], list[str]] = defaultdict(list)
    for review in reviews:
        timestamp = datetime.fromisoformat(review["published_at"].replace("Z", "+00:00"))
        period = "early" if timestamp < midpoint else "recent"
        if normalize_text(review["review_text"]):
            text_totals[(review["brand_name"], period)] += 1
        for theme in THEME_DEFINITIONS:
            if matches_theme(review["review_text"], review["stars"], theme):
                matches[(review["brand_name"], period, theme)].append(review["review_id"])
    results: list[dict[str, Any]] = []
    brands = sorted({review["brand_name"] for review in reviews})
    for brand in brands:
        for theme in THEME_DEFINITIONS:
            row: dict[str, Any] = {"brand": brand, "theme": theme}
            for period in ("early", "recent"):
                ids = matches[(brand, period, theme)]
                total = text_totals[(brand, period)]
                low, high = wilson_interval(len(ids), total)
                row[f"{period}_text_reviews"] = total
                row[f"{period}_matches"] = len(ids)
                row[f"{period}_per_1000"] = 1000 * len(ids) / total if total else 0.0
                row[f"{period}_ci_low_per_1000"] = 1000 * low
                row[f"{period}_ci_high_per_1000"] = 1000 * high
                row[f"{period}_evidence_ids"] = ids
            row["absolute_change_per_1000"] = row["recent_per_1000"] - row["early_per_1000"]
            row["relative_change_percent"] = (
                100 * (row["recent_per_1000"] / row["early_per_1000"] - 1)
                if row["early_per_1000"] > 0 else None
            )
            combined_matches = row["early_matches"] + row["recent_matches"]
            row["evidence_grade"] = (
                "eligible" if combined_matches >= 20 and min(row["early_matches"], row["recent_matches"]) >= 5
                else "directional" if combined_matches >= 10
                else "insufficient"
            )
            results.append(row)
    return results


def reviewer_overlap(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    brands = [row[0] for row in connection.execute("SELECT brand_name FROM brands ORDER BY brand_name")]
    reviewer_sets = {
        brand: {row[0] for row in connection.execute("SELECT DISTINCT reviewer_id FROM reviews WHERE brand_name = ?", (brand,))}
        for brand in brands
    }
    all_three = set.intersection(*(reviewer_sets[brand] for brand in brands))
    results = []
    for index, brand_a in enumerate(brands):
        for brand_b in brands[index + 1:]:
            shared = reviewer_sets[brand_a] & reviewer_sets[brand_b]
            results.append({
                "brand_a": brand_a,
                "brand_b": brand_b,
                "shared_reviewers": len(shared),
                "shared_reviewers_also_at_third_brand": len(shared & all_three),
                "pair_exclusive_reviewers": len(shared - all_three),
            })
    return results


def _customer_balanced_metric(
    connection: sqlite3.Connection,
    reviewers: set[str],
    brand: str,
    metric: str,
) -> tuple[float | None, int, tuple[float | None, float | None]]:
    if not reviewers:
        return (None, 0, (None, None))
    placeholders = ",".join("?" for _ in reviewers)
    if metric == "overall_stars":
        query = f"""
            SELECT reviewer_id, AVG(stars) value FROM reviews
            WHERE brand_name = ? AND reviewer_id IN ({placeholders}) GROUP BY reviewer_id
        """
    elif metric == "food_subrating":
        query = f"""
            SELECT r.reviewer_id, AVG(d.score) value
            FROM reviews r JOIN review_detailed_ratings d USING(review_id)
            WHERE r.brand_name = ? AND d.aspect = 'الطعام' AND r.reviewer_id IN ({placeholders})
            GROUP BY r.reviewer_id
        """
    else:
        raise ValueError(metric)
    values = [float(row[1]) for row in connection.execute(query, (brand, *sorted(reviewers)))]
    return (fmean(values) if values else None, len(values), mean_interval(values))


def overlap_ratings(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    brands = [row[0] for row in connection.execute("SELECT brand_name FROM brands ORDER BY brand_name")]
    reviewer_sets = {
        brand: {row[0] for row in connection.execute("SELECT DISTINCT reviewer_id FROM reviews WHERE brand_name = ?", (brand,))}
        for brand in brands
    }
    results = []
    for index, brand_a in enumerate(brands):
        for brand_b in brands[index + 1:]:
            shared = reviewer_sets[brand_a] & reviewer_sets[brand_b]
            row: dict[str, Any] = {"brand_a": brand_a, "brand_b": brand_b, "shared_reviewers": len(shared)}
            for label, brand in (("a", brand_a), ("b", brand_b)):
                for metric in ("overall_stars", "food_subrating"):
                    mean, coverage, interval = _customer_balanced_metric(connection, shared, brand, metric)
                    row[f"{label}_{metric}_mean"] = mean
                    row[f"{label}_{metric}_reviewers"] = coverage
                    row[f"{label}_{metric}_ci_low"] = interval[0]
                    row[f"{label}_{metric}_ci_high"] = interval[1]
            results.append(row)
    return results


def period_rating_trends(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    window = analysis_window(connection)
    midpoint = window["midpoint"]
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    for row in connection.execute("SELECT brand_name, stars, published_at FROM reviews"):
        timestamp = datetime.fromisoformat(row["published_at"].replace("Z", "+00:00"))
        grouped[(row["brand_name"], "early" if timestamp < midpoint else "recent")].append(float(row["stars"]))
    results = []
    for brand in sorted({key[0] for key in grouped}):
        row: dict[str, Any] = {"brand": brand}
        for period in ("early", "recent"):
            values = grouped[(brand, period)]
            low, high = mean_interval(values)
            row[f"{period}_n"] = len(values)
            row[f"{period}_mean_stars"] = fmean(values)
            row[f"{period}_ci_low"] = low
            row[f"{period}_ci_high"] = high
        row["change_stars"] = row["recent_mean_stars"] - row["early_mean_stars"]
        results.append(row)
    return results


def fastest_growing_complaints(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results = []
    brands = sorted({row["brand"] for row in trends})
    for brand in brands:
        eligible = [
            row for row in trends
            if row["brand"] == brand and row["theme"] in COMPLAINT_THEMES and row["evidence_grade"] == "eligible"
        ]
        if not eligible:
            results.append({"brand": brand, "theme": None, "status": "No eligible complaint theme"})
            continue
        winner = max(eligible, key=lambda row: row["absolute_change_per_1000"])
        results.append({
            "brand": brand,
            "theme": winner["theme"],
            "status": "eligible",
            "early_matches": winner["early_matches"],
            "recent_matches": winner["recent_matches"],
            "early_per_1000": winner["early_per_1000"],
            "recent_per_1000": winner["recent_per_1000"],
            "absolute_change_per_1000": winner["absolute_change_per_1000"],
        })
    return results


def loyalty_evidence(connection: sqlite3.Connection) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "low_rating_mentions": 0, "high_rating_mentions": 0, "evidence_ids": []}
    )
    for row in connection.execute("SELECT review_id, brand_name, review_text, stars FROM reviews"):
        if matches_theme(row["review_text"], row["stars"], "loyalty_program_mention"):
            item = grouped[row["brand_name"]]
            item["mentions"] += 1
            item["low_rating_mentions" if row["stars"] <= 3 else "high_rating_mentions"] += 1
            item["evidence_ids"].append(row["review_id"])
    return [
        {"brand": brand, **grouped[brand]}
        for brand in (row[0] for row in connection.execute("SELECT brand_name FROM brands ORDER BY brand_name"))
    ]


def evidence_sample(trends: list[dict[str, Any]], brand: str, theme: str, limit: int = 8) -> list[str]:
    row = next(item for item in trends if item["brand"] == brand and item["theme"] == theme)
    return (row["early_evidence_ids"] + row["recent_evidence_ids"])[:limit]


def select_trends(trends: list[dict[str, Any]], themes: Iterable[str]) -> list[dict[str, Any]]:
    wanted = set(themes)
    return [row for row in trends if row["theme"] in wanted]


def format_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]], digits: int = 2) -> str:
    if not rows:
        return "(no rows)"
    headers = [label for _, label in columns]
    rendered: list[list[str]] = []
    for row in rows:
        values = []
        for key, _ in columns:
            value = row.get(key)
            if isinstance(value, float):
                value = f"{value:.{digits}f}"
            elif value is None:
                value = "—"
            values.append(str(value))
        rendered.append(values)
    widths = [max(len(headers[index]), *(len(row[index]) for row in rendered)) for index in range(len(headers))]
    line = " | ".join(headers[index].ljust(widths[index]) for index in range(len(headers)))
    separator = "-+-".join("-" * width for width in widths)
    body = [" | ".join(row[index].ljust(widths[index]) for index in range(len(headers))) for row in rendered]
    return "\n".join((line, separator, *body))
