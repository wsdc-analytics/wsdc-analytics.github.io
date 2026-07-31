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


def validate_champion_news() -> None:
    path = DATA_DIR / "champion_news.json"
    data = load_json(path)
    if not isinstance(data, dict):
        fail("champion_news.json must be an object")
    summaries = data.get("summaries")
    if not isinstance(summaries, list):
        fail("champion_news.json must contain list field 'summaries'")

    for idx, summary in enumerate(summaries):
        if not isinstance(summary, dict):
            fail(f"champion_news.summaries[{idx}] must be an object")
        if "post_date" not in summary:
            fail(f"champion_news.summaries[{idx}] missing post_date")
        events = summary.get("events", [])
        if not isinstance(events, list):
            fail(f"champion_news.summaries[{idx}].events must be a list")
        for ei, event in enumerate(events):
            if not isinstance(event, dict):
                fail(f"champion_news.summaries[{idx}].events[{ei}] must be an object")
            for field in ("slug", "dancer_id", "role", "status"):
                if field not in event:
                    fail(
                        f"champion_news.summaries[{idx}].events[{ei}] missing {field}"
                    )

    print("[OK] champion_news.json")


def validate_homepage_kpis() -> None:
    path = DATA_DIR / "homepage_kpis.json"
    data = load_json(path)
    if not isinstance(data, dict):
        fail("homepage_kpis.json must be an object")
    for field in ("as_of", "totals", "comparisons"):
        if field not in data:
            fail(f"homepage_kpis.json missing field: {field}")
    totals = data["totals"]
    if not isinstance(totals, dict):
        fail("homepage_kpis.json.totals must be an object")
    for metric in ("events", "points", "dancers"):
        if metric not in totals:
            fail(f"homepage_kpis.json.totals missing: {metric}")
    comparisons = data["comparisons"]
    if not isinstance(comparisons, dict):
        fail("homepage_kpis.json.comparisons must be an object")
    for scale in ("week", "month", "year"):
        block = comparisons.get(scale)
        if not isinstance(block, dict):
            fail(f"homepage_kpis.json.comparisons.{scale} must be an object")
        for field in ("label", "period", "increment"):
            if field not in block:
                fail(f"homepage_kpis.json.comparisons.{scale} missing: {field}")
        period = block["period"]
        if not isinstance(period, dict) or "start" not in period or "end" not in period:
            fail(f"homepage_kpis.json.comparisons.{scale}.period must include start/end")
        increment = block["increment"]
        if not isinstance(increment, dict):
            fail(f"homepage_kpis.json.comparisons.{scale}.increment must be an object")
        for metric in ("events", "points", "dancers"):
            if metric not in increment:
                fail(f"homepage_kpis.json.comparisons.{scale}.increment missing: {metric}")
    print("[OK] homepage_kpis.json")


def main() -> None:
    validate_articles()
    validate_points_summaries()
    validate_champion_news()
    validate_homepage_kpis()
    print("[OK] Data validation passed.")

if __name__ == "__main__":
    main()
