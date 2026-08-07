#!/usr/bin/env python3
"""Reconstruct the Part 2 benchmark dataset as a validated SQLite database.

Only the Python standard library is required. The loader preserves every source
JSON object in audit tables while exposing normalized tables for analysis.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile


SCHEMA_VERSION = 1
NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"


DDL = r"""
PRAGMA foreign_keys = ON;

CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
) STRICT;

CREATE TABLE ingestion_manifest (
    file_name TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL CHECK(length(sha256) = 64),
    logical_row_count INTEGER NOT NULL CHECK(logical_row_count >= 0)
) STRICT;

CREATE TABLE data_dictionary_fields (
    entity TEXT NOT NULL CHECK(entity IN ('branch', 'review')),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    source_field TEXT NOT NULL,
    declared_type TEXT NOT NULL,
    description TEXT NOT NULL,
    example TEXT,
    provenance TEXT NOT NULL,
    PRIMARY KEY (entity, ordinal),
    UNIQUE (entity, source_field)
) STRICT;

CREATE TABLE data_dictionary_files (
    ordinal INTEGER PRIMARY KEY CHECK(ordinal >= 0),
    file_name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    declared_size TEXT NOT NULL
) STRICT;

CREATE TABLE brands (
    brand_name TEXT PRIMARY KEY
) STRICT;

CREATE TABLE branches (
    branch_id TEXT PRIMARY KEY,
    brand_name TEXT NOT NULL REFERENCES brands(brand_name),
    title TEXT NOT NULL,
    subtitle TEXT,
    city TEXT NOT NULL,
    neighbourhood TEXT NOT NULL,
    branch_label TEXT NOT NULL,
    category_name TEXT,
    total_score REAL CHECK(total_score BETWEEN 0 AND 5),
    reviews_count INTEGER CHECK(reviews_count >= 0),
    images_count INTEGER CHECK(images_count >= 0),
    popular_times_live_text TEXT,
    popular_times_live_percent INTEGER CHECK(
        popular_times_live_percent IS NULL OR
        popular_times_live_percent BETWEEN 0 AND 100
    ),
    scraped_at TEXT NOT NULL,
    language TEXT
) STRICT;

CREATE TABLE source_branch_records (
    source_file TEXT NOT NULL,
    source_ordinal INTEGER NOT NULL CHECK(source_ordinal >= 0),
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256) = 64),
    raw_json TEXT NOT NULL CHECK(json_valid(raw_json)),
    PRIMARY KEY (source_file, source_ordinal)
) STRICT;

CREATE TABLE branch_categories (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    category TEXT NOT NULL,
    PRIMARY KEY (branch_id, ordinal)
) STRICT;

CREATE TABLE branch_review_distribution (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
    review_count INTEGER NOT NULL CHECK(review_count >= 0),
    PRIMARY KEY (branch_id, stars)
) STRICT;

CREATE TABLE branch_opening_hours (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    day TEXT NOT NULL,
    hours TEXT NOT NULL,
    PRIMARY KEY (branch_id, ordinal)
) STRICT;

CREATE TABLE branch_popular_times (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    weekday TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    hour INTEGER NOT NULL CHECK(hour BETWEEN 0 AND 23),
    occupancy_percent INTEGER NOT NULL CHECK(occupancy_percent BETWEEN 0 AND 100),
    PRIMARY KEY (branch_id, weekday, ordinal)
) STRICT;

CREATE TABLE branch_attributes (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    attribute_group TEXT NOT NULL,
    item_ordinal INTEGER NOT NULL CHECK(item_ordinal >= 0),
    attribute_name TEXT NOT NULL,
    enabled INTEGER NOT NULL CHECK(enabled IN (0, 1)),
    PRIMARY KEY (branch_id, attribute_group, item_ordinal, attribute_name)
) STRICT;

CREATE TABLE branch_place_tags (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    title TEXT NOT NULL,
    tag_count INTEGER CHECK(tag_count >= 0),
    PRIMARY KEY (branch_id, ordinal)
) STRICT;

CREATE TABLE branch_review_tags (
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    title TEXT NOT NULL,
    tag_count INTEGER CHECK(tag_count >= 0),
    PRIMARY KEY (branch_id, ordinal)
) STRICT;

CREATE TABLE reviewers (
    reviewer_id TEXT PRIMARY KEY
) STRICT;

CREATE TABLE reviews (
    review_id TEXT PRIMARY KEY,
    brand_name TEXT NOT NULL REFERENCES brands(brand_name),
    branch_id TEXT NOT NULL REFERENCES branches(branch_id),
    source_branch_label TEXT NOT NULL,
    source_city TEXT NOT NULL,
    reviewer_id TEXT NOT NULL REFERENCES reviewers(reviewer_id),
    reviewer_number_of_reviews INTEGER CHECK(reviewer_number_of_reviews >= 0),
    is_local_guide INTEGER NOT NULL CHECK(is_local_guide IN (0, 1)),
    review_text TEXT,
    translated_text TEXT,
    owner_response_text TEXT,
    owner_response_date TEXT,
    stars INTEGER NOT NULL CHECK(stars BETWEEN 1 AND 5),
    alternate_rating INTEGER CHECK(alternate_rating IS NULL OR alternate_rating BETWEEN 1 AND 5),
    likes_count INTEGER NOT NULL CHECK(likes_count >= 0),
    relative_publish_text TEXT,
    published_at TEXT NOT NULL,
    visited_in TEXT,
    original_language TEXT,
    translated_language TEXT,
    is_advertisement INTEGER NOT NULL CHECK(is_advertisement IN (0, 1)),
    category_name TEXT,
    source_total_score REAL CHECK(source_total_score BETWEEN 0 AND 5),
    source_reviews_count INTEGER CHECK(source_reviews_count >= 0),
    scraped_at TEXT NOT NULL,
    record_language TEXT
) STRICT;

CREATE TABLE source_review_records (
    source_file TEXT NOT NULL,
    source_ordinal INTEGER NOT NULL CHECK(source_ordinal >= 0),
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    payload_sha256 TEXT NOT NULL CHECK(length(payload_sha256) = 64),
    is_exact_duplicate INTEGER NOT NULL CHECK(is_exact_duplicate IN (0, 1)),
    raw_json TEXT NOT NULL CHECK(json_valid(raw_json)),
    PRIMARY KEY (source_file, source_ordinal)
) STRICT;

CREATE TABLE review_categories (
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    ordinal INTEGER NOT NULL CHECK(ordinal >= 0),
    category TEXT NOT NULL,
    PRIMARY KEY (review_id, ordinal)
) STRICT;

CREATE TABLE review_context (
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    context_key TEXT NOT NULL,
    value_type TEXT NOT NULL,
    json_value TEXT NOT NULL CHECK(json_valid(json_value)),
    PRIMARY KEY (review_id, context_key)
) STRICT;

CREATE TABLE review_detailed_ratings (
    review_id TEXT NOT NULL REFERENCES reviews(review_id),
    aspect TEXT NOT NULL,
    score REAL NOT NULL CHECK(score BETWEEN 1 AND 5),
    PRIMARY KEY (review_id, aspect)
) STRICT;

CREATE TABLE menu_items (
    brand_name TEXT NOT NULL REFERENCES brands(brand_name),
    section_ordinal INTEGER NOT NULL CHECK(section_ordinal >= 0),
    section_name TEXT NOT NULL,
    item_ordinal INTEGER NOT NULL CHECK(item_ordinal >= 0),
    item_name TEXT NOT NULL,
    price REAL CHECK(price IS NULL OR price >= 0),
    PRIMARY KEY (brand_name, section_ordinal, item_ordinal)
) STRICT;

CREATE INDEX idx_reviews_brand_date ON reviews(brand_name, published_at);
CREATE INDEX idx_reviews_branch_date ON reviews(branch_id, published_at);
CREATE INDEX idx_reviews_reviewer_brand ON reviews(reviewer_id, brand_name);
CREATE INDEX idx_source_reviews_duplicate ON source_review_records(is_exact_duplicate);
CREATE INDEX idx_detailed_ratings_aspect ON review_detailed_ratings(aspect, score);

CREATE VIEW review_enriched AS
SELECT
    r.review_id,
    r.brand_name,
    r.branch_id,
    b.branch_label,
    b.city,
    b.neighbourhood,
    r.reviewer_id,
    r.review_text,
    r.stars,
    r.published_at,
    r.original_language,
    CASE WHEN r.owner_response_text IS NULL THEN 0 ELSE 1 END AS has_owner_response
FROM reviews AS r
JOIN branches AS b ON b.branch_id = r.branch_id;

CREATE VIEW reviewer_brand_activity AS
SELECT reviewer_id, brand_name, COUNT(*) AS review_count,
       MIN(published_at) AS first_review_at, MAX(published_at) AS last_review_at
FROM reviews
GROUP BY reviewer_id, brand_name;
"""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def validate_iso8601(value: str | None, field: str, nullable: bool = False) -> None:
    if value is None and nullable:
        return
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 string")
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def _cell_column(reference: str) -> int:
    letters = "".join(ch for ch in reference if ch.isalpha())
    value = 0
    for ch in letters:
        value = value * 26 + ord(ch.upper()) - 64
    return value - 1


def read_xlsx_sheets(path: Path) -> dict[str, list[list[str]]]:
    """Read cell values from the simple data-dictionary workbook using OOXML."""
    main = {"m": NS_MAIN, "r": NS_REL, "pr": NS_PACKAGE_REL}
    with ZipFile(path) as archive:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("m:si", main):
                shared.append("".join(node.text or "" for node in item.iter(f"{{{NS_MAIN}}}t")))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {node.attrib["Id"]: node.attrib["Target"] for node in relationships}
        result: dict[str, list[list[str]]] = {}
        sheets_node = workbook.find("m:sheets", main)
        if sheets_node is None:
            raise ValueError("Workbook has no sheets")
        for sheet in sheets_node:
            name = sheet.attrib["name"]
            relationship_id = sheet.attrib[f"{{{NS_REL}}}id"]
            target = targets[relationship_id]
            sheet_path = target.lstrip("/") if target.startswith("/") else str(PurePosixPath("xl") / target)
            root = ET.fromstring(archive.read(sheet_path))
            rows: list[list[str]] = []
            for row_node in root.findall(".//m:sheetData/m:row", main):
                values: dict[int, str] = {}
                for cell in row_node.findall("m:c", main):
                    column = _cell_column(cell.attrib["r"])
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("m:v", main)
                    inline = cell.find("m:is", main)
                    if cell_type == "s" and value_node is not None:
                        value = shared[int(value_node.text or 0)]
                    elif cell_type == "inlineStr" and inline is not None:
                        value = "".join(node.text or "" for node in inline.iter(f"{{{NS_MAIN}}}t"))
                    else:
                        value = value_node.text if value_node is not None and value_node.text is not None else ""
                    values[column] = value
                if values:
                    rows.append([values.get(index, "") for index in range(max(values) + 1)])
            result[name] = rows
        return result


def insert_dictionary(connection: sqlite3.Connection, workbook_path: Path) -> None:
    sheets = read_xlsx_sheets(workbook_path)
    for entity, sheet_name in (("branch", "Branch fields"), ("review", "Review fields")):
        rows = sheets[sheet_name]
        field_rows = [row for row in rows if row and row[0] not in ("", "Field")][1:]
        for ordinal, row in enumerate(field_rows):
            padded = row + [""] * (5 - len(row))
            connection.execute(
                "INSERT INTO data_dictionary_fields VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entity, ordinal, *padded[:5]),
            )
    file_rows = [row for row in sheets["Files"] if row and row[0] not in ("", "File", "Files")]
    for ordinal, row in enumerate(file_rows):
        padded = row + [""] * (3 - len(row))
        connection.execute("INSERT INTO data_dictionary_files VALUES (?, ?, ?, ?)", (ordinal, *padded[:3]))


def require_keys(record: dict[str, Any], keys: Iterable[str], source: str) -> None:
    missing = [key for key in keys if key not in record]
    if missing:
        raise ValueError(f"{source} is missing required fields: {missing}")


def insert_branch(connection: sqlite3.Connection, record: dict[str, Any], source_file: str, ordinal: int) -> None:
    require_keys(
        record,
        ("brand", "branch_id", "title", "city", "neighbourhood", "branch_label", "scrapedAt"),
        f"{source_file}[{ordinal}]",
    )
    validate_iso8601(record["scrapedAt"], "branch.scrapedAt")
    connection.execute("INSERT OR IGNORE INTO brands VALUES (?)", (record["brand"],))
    connection.execute(
        """INSERT INTO branches VALUES (
           ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )""",
        (
            record["branch_id"], record["brand"], record["title"], record.get("subTitle"),
            record["city"], record["neighbourhood"], record["branch_label"], record.get("categoryName"),
            record.get("totalScore"), record.get("reviewsCount"), record.get("imagesCount"),
            record.get("popularTimesLiveText"), record.get("popularTimesLivePercent"),
            record["scrapedAt"], record.get("language"),
        ),
    )
    raw = canonical_json(record)
    connection.execute(
        "INSERT INTO source_branch_records VALUES (?, ?, ?, ?, ?)",
        (source_file, ordinal, record["branch_id"], sha256_bytes(raw.encode()), raw),
    )
    for index, category in enumerate(record.get("categories") or []):
        connection.execute("INSERT INTO branch_categories VALUES (?, ?, ?)", (record["branch_id"], index, category))
    distribution = record.get("reviewsDistribution") or {}
    for stars, label in enumerate(("oneStar", "twoStar", "threeStar", "fourStar", "fiveStar"), start=1):
        if label in distribution:
            connection.execute(
                "INSERT INTO branch_review_distribution VALUES (?, ?, ?)",
                (record["branch_id"], stars, distribution[label]),
            )
    for index, item in enumerate(record.get("openingHours") or []):
        connection.execute(
            "INSERT INTO branch_opening_hours VALUES (?, ?, ?, ?)",
            (record["branch_id"], index, item["day"], item["hours"]),
        )
    for weekday, values in (record.get("popularTimesHistogram") or {}).items():
        for index, item in enumerate(values):
            connection.execute(
                "INSERT INTO branch_popular_times VALUES (?, ?, ?, ?, ?)",
                (record["branch_id"], weekday, index, item["hour"], item["occupancyPercent"]),
            )
    for group_name, items in (record.get("additionalInfo") or {}).items():
        for item_index, item in enumerate(items):
            for attribute_name, enabled in item.items():
                connection.execute(
                    "INSERT INTO branch_attributes VALUES (?, ?, ?, ?, ?)",
                    (record["branch_id"], group_name, item_index, attribute_name, int(bool(enabled))),
                )
    for table, key in (("branch_place_tags", "placesTags"), ("branch_review_tags", "reviewsTags")):
        for index, tag in enumerate(record.get(key) or []):
            connection.execute(
                f"INSERT INTO {table} VALUES (?, ?, ?, ?)",
                (record["branch_id"], index, tag["title"], tag.get("count")),
            )


def insert_review(
    connection: sqlite3.Connection,
    record: dict[str, Any],
    source_file: str,
    ordinal: int,
    canonical_payloads: dict[str, str],
) -> bool:
    require_keys(
        record,
        ("brand", "branch_id", "branch_label", "city", "review_id", "reviewer_id", "stars", "publishedAtDate", "scrapedAt"),
        f"{source_file}[{ordinal}]",
    )
    validate_iso8601(record["publishedAtDate"], "review.publishedAtDate")
    validate_iso8601(record["scrapedAt"], "review.scrapedAt")
    validate_iso8601(record.get("responseFromOwnerDate"), "review.responseFromOwnerDate", nullable=True)
    raw = canonical_json(record)
    payload_hash = sha256_bytes(raw.encode())
    existing_hash = canonical_payloads.get(record["review_id"])
    is_duplicate = existing_hash is not None
    if is_duplicate and existing_hash != payload_hash:
        raise ValueError(f"Conflicting payloads share review_id {record['review_id']}")
    if not is_duplicate:
        branch = connection.execute(
            "SELECT brand_name, branch_label, city FROM branches WHERE branch_id = ?", (record["branch_id"],)
        ).fetchone()
        if branch is None:
            raise ValueError(f"Orphan review {record['review_id']}: unknown branch {record['branch_id']}")
        if (record["brand"], record["branch_label"], record["city"]) != tuple(branch):
            raise ValueError(f"Review {record['review_id']} disagrees with its branch identity")
        connection.execute("INSERT OR IGNORE INTO reviewers VALUES (?)", (record["reviewer_id"],))
        connection.execute(
            """INSERT INTO reviews VALUES (
               ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )""",
            (
                record["review_id"], record["brand"], record["branch_id"], record["branch_label"], record["city"],
                record["reviewer_id"], record.get("reviewerNumberOfReviews"), int(bool(record.get("isLocalGuide"))),
                record.get("text"), record.get("textTranslated"), record.get("responseFromOwnerText"),
                record.get("responseFromOwnerDate"), record["stars"], record.get("rating"),
                record.get("likesCount", 0), record.get("publishAt"), record["publishedAtDate"],
                record.get("visitedIn"), record.get("originalLanguage"), record.get("translatedLanguage"),
                int(bool(record.get("isAdvertisement"))), record.get("categoryName"), record.get("totalScore"),
                record.get("reviewsCount"), record["scrapedAt"], record.get("language"),
            ),
        )
        for index, category in enumerate(record.get("categories") or []):
            connection.execute("INSERT INTO review_categories VALUES (?, ?, ?)", (record["review_id"], index, category))
        for key, value in (record.get("reviewContext") or {}).items():
            connection.execute(
                "INSERT INTO review_context VALUES (?, ?, ?, ?)",
                (record["review_id"], key, type(value).__name__, canonical_json(value)),
            )
        for aspect, score in (record.get("reviewDetailedRating") or {}).items():
            connection.execute(
                "INSERT INTO review_detailed_ratings VALUES (?, ?, ?)",
                (record["review_id"], aspect, score),
            )
        canonical_payloads[record["review_id"]] = payload_hash
    connection.execute(
        "INSERT INTO source_review_records VALUES (?, ?, ?, ?, ?, ?)",
        (source_file, ordinal, record["review_id"], payload_hash, int(is_duplicate), raw),
    )
    return is_duplicate


def validate_database(connection: sqlite3.Connection, expected: dict[str, int]) -> dict[str, int]:
    foreign_key_errors = connection.execute("PRAGMA foreign_key_check").fetchall()
    if foreign_key_errors:
        raise ValueError(f"Foreign-key validation failed: {foreign_key_errors[:5]}")
    counts = {
        "brands": connection.execute("SELECT COUNT(*) FROM brands").fetchone()[0],
        "branches": connection.execute("SELECT COUNT(*) FROM branches").fetchone()[0],
        "source_reviews": connection.execute("SELECT COUNT(*) FROM source_review_records").fetchone()[0],
        "unique_reviews": connection.execute("SELECT COUNT(*) FROM reviews").fetchone()[0],
        "exact_duplicate_reviews": connection.execute(
            "SELECT COUNT(*) FROM source_review_records WHERE is_exact_duplicate = 1"
        ).fetchone()[0],
        "menu_items": connection.execute("SELECT COUNT(*) FROM menu_items").fetchone()[0],
    }
    for key, value in expected.items():
        if counts[key] != value:
            raise ValueError(f"Expected {key}={value}, found {counts[key]}")
    invalid_stars = connection.execute("SELECT COUNT(*) FROM reviews WHERE stars NOT BETWEEN 1 AND 5").fetchone()[0]
    if invalid_stars:
        raise ValueError(f"Found {invalid_stars} reviews with invalid stars")
    return counts


def build_database(source_dir: Path, dictionary_path: Path, output_path: Path) -> dict[str, Any]:
    branch_paths = sorted(source_dir.glob("*_branches.json"))
    review_paths = sorted(source_dir.glob("*_reviews.json"))
    menu_path = source_dir / "menus.json"
    if len(branch_paths) != 3 or len(review_paths) != 3 or not menu_path.exists():
        raise FileNotFoundError("Expected three branch files, three review files, and menus.json")
    if not dictionary_path.exists():
        raise FileNotFoundError(dictionary_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(prefix=f".{output_path.name}.", suffix=".tmp", dir=output_path.parent)
    os.close(handle)
    temporary_path = Path(temporary_name)
    try:
        connection = sqlite3.connect(temporary_path)
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(DDL)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        connection.executemany(
            "INSERT INTO schema_metadata VALUES (?, ?)",
            (("schema_version", str(SCHEMA_VERSION)), ("analysis_window", "source-defined trailing 90 days")),
        )
        insert_dictionary(connection, dictionary_path)
        dictionary_bytes = dictionary_path.read_bytes()
        connection.execute(
            "INSERT INTO ingestion_manifest VALUES (?, ?, ?)",
            (dictionary_path.name, sha256_bytes(dictionary_bytes), len(read_xlsx_sheets(dictionary_path))),
        )

        branch_count = 0
        for path in branch_paths:
            records = load_json(path)
            if not isinstance(records, list):
                raise ValueError(f"{path.name} must contain a JSON array")
            connection.execute(
                "INSERT INTO ingestion_manifest VALUES (?, ?, ?)",
                (path.name, sha256_bytes(path.read_bytes()), len(records)),
            )
            for ordinal, record in enumerate(records):
                insert_branch(connection, record, path.name, ordinal)
            branch_count += len(records)

        source_review_count = 0
        duplicate_count = 0
        canonical_payloads: dict[str, str] = {}
        for path in review_paths:
            records = load_json(path)
            if not isinstance(records, list):
                raise ValueError(f"{path.name} must contain a JSON array")
            connection.execute(
                "INSERT INTO ingestion_manifest VALUES (?, ?, ?)",
                (path.name, sha256_bytes(path.read_bytes()), len(records)),
            )
            for ordinal, record in enumerate(records):
                duplicate_count += int(insert_review(connection, record, path.name, ordinal, canonical_payloads))
            source_review_count += len(records)

        menus = load_json(menu_path)
        if not isinstance(menus, dict):
            raise ValueError("menus.json must contain a brand-keyed object")
        menu_count = 0
        for brand_name, sections in menus.items():
            if connection.execute("SELECT 1 FROM brands WHERE brand_name = ?", (brand_name,)).fetchone() is None:
                raise ValueError(f"Menu references unknown brand {brand_name}")
            for section_index, (section_name, items) in enumerate(sections.items()):
                for item_index, (item_name, price) in enumerate(items.items()):
                    connection.execute(
                        "INSERT INTO menu_items VALUES (?, ?, ?, ?, ?, ?)",
                        (brand_name, section_index, section_name, item_index, item_name, price),
                    )
                    menu_count += 1
        connection.execute(
            "INSERT INTO ingestion_manifest VALUES (?, ?, ?)",
            (menu_path.name, sha256_bytes(menu_path.read_bytes()), menu_count),
        )

        counts = validate_database(
            connection,
            {
                "brands": 3,
                "branches": branch_count,
                "source_reviews": source_review_count,
                "unique_reviews": source_review_count - duplicate_count,
                "exact_duplicate_reviews": duplicate_count,
                "menu_items": menu_count,
            },
        )
        connection.execute("INSERT INTO schema_metadata VALUES (?, ?)", ("validation_status", "passed"))
        connection.commit()
        connection.execute("PRAGMA optimize")
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise ValueError(f"SQLite integrity check failed: {integrity}")
        connection.close()
        os.replace(temporary_path, output_path)
        output_path.chmod(0o644)
    except Exception:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise

    return {
        "database": str(output_path),
        "schema_version": SCHEMA_VERSION,
        "counts": counts,
        "source_files": [path.name for path in branch_paths + review_paths] + [menu_path.name, dictionary_path.name],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=Path("Files"))
    parser.add_argument("--dictionary", type=Path, default=Path("DATA_DICTIONARY.xlsx"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("analysis/generated/competitive_benchmarking.sqlite"),
    )
    arguments = parser.parse_args()
    result = build_database(arguments.source_dir, arguments.dictionary, arguments.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
