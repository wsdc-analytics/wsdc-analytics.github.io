#!/usr/bin/env python3
"""Validate core website JSON data contracts."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "static" / "data"


def fail(message: str) -> None:
    print(f"[FAIL] {message}")
    raise SystemExit(1)


def load_json(path: Path):
    if not path.exists():
        fail(f"Missing file: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def validate_articles() -> None:
    path = DATA_DIR / "articles.json"
    data = load_json(path)
    if not isinstance(data, dict):
        fail("articles.json must be an object with language keys")
    required_langs = {"ru", "en", "es"}
    missing_langs = required_langs - set(data.keys())
    if missing_langs:
        fail(f"articles.json missing languages: {sorted(missing_langs)}")

    required_fields = {"title", "description", "url", "keywords", "datePublished", "category"}
    for lang in required_langs:
        items = data.get(lang)
        if not isinstance(items, list):
            fail(f"articles.json[{lang}] must be a list")
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                fail(f"articles.json[{lang}][{idx}] must be an object")
            missing = required_fields - set(item.keys())
            if missing:
                fail(f"articles.json[{lang}][{idx}] missing fields: {sorted(missing)}")
            if not str(item.get("url", "")).endswith(".html"):
                fail(f"articles.json[{lang}][{idx}] has non-html url: {item.get('url')}")

    print("[OK] articles.json")


def validate_points_summaries() -> None:
    path = DATA_DIR / "points_summaries.json"
    data = load_json(path)
    if not isinstance(data, dict):
        fail("points_summaries.json must be an object")
    summaries = data.get("summaries")
    if not isinstance(summaries, list):
        fail("points_summaries.json must contain list field 'summaries'")

    for idx, summary in enumerate(summaries):
        if not isinstance(summary, dict):
            fail(f"summaries[{idx}] must be an object")
        if "post_date" not in summary:
            fail(f"summaries[{idx}] missing post_date")
        events = summary.get("events", [])
        if not isinstance(events, list):
            fail(f"summaries[{idx}].events must be a list")

    print("[OK] points_summaries.json")


def main() -> None:
    validate_articles()
    validate_points_summaries()
    print("[OK] Data validation passed.")


if __name__ == "__main__":
    main()
