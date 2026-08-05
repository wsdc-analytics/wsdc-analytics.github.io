#!/usr/bin/env python3
"""Validate core website JSON data contracts."""

from __future__ import annotations

import json
import re
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

    post_date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    allowed_status = {"allowed", "required"}
    seen_slugs: set[str] = set()

    for idx, summary in enumerate(summaries):
        if not isinstance(summary, dict):
            fail(f"champion_news.summaries[{idx}] must be an object")
        post_date = summary.get("post_date")
        if not isinstance(post_date, str) or not post_date_re.match(post_date.strip()):
            fail(
                f"champion_news.summaries[{idx}] post_date must be YYYY-MM-DD, "
                f"got {post_date!r}"
            )
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
            status = str(event.get("status") or "").lower()
            if status not in allowed_status:
                fail(
                    f"champion_news.summaries[{idx}].events[{ei}] "
                    f"status must be allowed|required, got {event.get('status')!r}"
                )
            slug = str(event.get("slug") or "").strip()
            if not slug:
                fail(f"champion_news.summaries[{idx}].events[{ei}] slug is empty")
            if slug in seen_slugs:
                fail(f"champion_news duplicate slug: {slug}")
            seen_slugs.add(slug)
            if "path" in event and event["path"] is not None:
                if not isinstance(event["path"], dict):
                    fail(
                        f"champion_news.summaries[{idx}].events[{ei}].path "
                        "must be an object when present"
                    )

    print("[OK] champion_news.json")


def validate_events_year_calendar() -> None:
    path = DATA_DIR / "events_year_calendar.json"
    data = load_json(path)
    if not isinstance(data, dict):
        fail("events_year_calendar.json must be an object")
    for field in ("as_of", "years", "default_year", "events", "disclaimer"):
        if field not in data:
            fail(f"events_year_calendar.json missing field: {field}")
    if not isinstance(data["years"], list) or not data["years"]:
        fail("events_year_calendar.json.years must be a non-empty list")
    if not isinstance(data["events"], list):
        fail("events_year_calendar.json.events must be a list")
    disclaimer = data["disclaimer"]
    if not isinstance(disclaimer, dict):
        fail("events_year_calendar.json.disclaimer must be an object")
    for lang in ("en", "ru", "es"):
        if lang not in disclaimer:
            fail(f"events_year_calendar.json.disclaimer missing {lang}")
    allowed_status = {"confirmed", "expected", "hiatus"}
    allowed_kind = {"registry", "trial"}
    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for idx, event in enumerate(data["events"]):
        if not isinstance(event, dict):
            fail(f"events_year_calendar.events[{idx}] must be an object")
        for field in (
            "id",
            "name",
            "start_date",
            "weekend_key",
            "status",
            "kind",
            "year",
        ):
            if field not in event:
                fail(f"events_year_calendar.events[{idx}] missing {field}")
        if str(event.get("status")) not in allowed_status:
            fail(
                f"events_year_calendar.events[{idx}] bad status: {event.get('status')!r}"
            )
        if str(event.get("kind")) not in allowed_kind:
            fail(f"events_year_calendar.events[{idx}] bad kind: {event.get('kind')!r}")
        if not date_re.match(str(event.get("start_date") or "")):
            fail(f"events_year_calendar.events[{idx}] start_date must be YYYY-MM-DD")
        if not date_re.match(str(event.get("weekend_key") or "")):
            fail(f"events_year_calendar.events[{idx}] weekend_key must be YYYY-MM-DD")
    print("[OK] events_year_calendar.json")


def validate_event_l2_cards() -> None:
    path = DATA_DIR / "event_l2_cards.json"
    if not path.exists():
        print("[SKIP] event_l2_cards.json (optional)")
        return
    data = load_json(path)
    if not isinstance(data, dict):
        fail("event_l2_cards.json must be an object")
    for field in ("as_of", "generated_at", "tier_tip", "cards"):
        if field not in data:
            fail(f"event_l2_cards.json missing field: {field}")
    tip = data["tier_tip"]
    if not isinstance(tip, dict):
        fail("event_l2_cards.json.tier_tip must be an object")
    for lang in ("en", "ru", "es"):
        if lang not in tip or not str(tip[lang]).strip():
            fail(f"event_l2_cards.json.tier_tip missing {lang}")
    cards = data["cards"]
    if not isinstance(cards, dict) or not cards:
        fail("event_l2_cards.json.cards must be a non-empty object")
    sample_key = next(iter(cards))
    sample = cards[sample_key]
    if not isinstance(sample, dict):
        fail(f"event_l2_cards.json.cards[{sample_key}] must be an object")
    if "series" not in sample:
        fail(f"event_l2_cards.json.cards[{sample_key}] missing series")
    print(f"[OK] event_l2_cards.json ({len(cards)} cards)")


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
    validate_events_year_calendar()
    validate_event_l2_cards()
    print("[OK] Data validation passed.")

if __name__ == "__main__":
    main()
