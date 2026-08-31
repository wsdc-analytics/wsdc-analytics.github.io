#!/usr/bin/env python3
"""Build homepage KPI totals + period increments from WSDC pipeline CSVs.

Metrics
-------
- events (totals): count of occurred WSDC editions in event_editions.csv
  (rows with result_rows > 0, or event_occurred). One row = one event
  year/month that awarded points — not the stale events_wsdc registry dump.
- points (totals): sum of event_points across all nominations in results
- dancers (totals): count of unique dancer_id in results

Period increments (growth counters)
-----------------------------------
Uses event_editions.csv precise calendar dates:
  start_date, end_date, calendar_status, event_occurred
(edition_date stays YYYY-MM-01 for Tableau.)

Week/month buckets use start_date (event start; avoids double-counting
cross-month weekends).

- week: editions bucketed by ISO week of start_date; latest non-empty week
  at/before as_of (do not advance into a week with no occurred events yet)
- month: occurred editions with start_date in the current month (through as_of)
- year: WSDC results year (event_year), not calendar end_date year — so
  New Year events that start in late December still count toward the new year

Within each window:
- events / points: activity in the window (year = all results with that event_year)
- dancers: NEW dancers — unique dancer_id whose first WSDC points fall in
  the window (week/month: by first edition end_date; year: by first event_year)

Optional reference: edition_calendar_dates.csv (planned calendar incl. future/hiatus).

Usage
-----
  python scripts/build_homepage_kpis.py
  python scripts/build_homepage_kpis.py --as-of 2026-07-16
"""

from __future__ import annotations

import argparse
import csv
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = Path(
    os.environ.get(
        "WSDC_PIPELINE_DATA",
        str(Path.home() / ".cursor/projects/python/wsdc-data-pipeline/data"),
    )
)
DEFAULT_OUTPUT = REPO_ROOT / "static" / "data" / "homepage_kpis.json"


@dataclass(frozen=True)
class Edition:
    event_name: str
    event_year: int
    start_date: date
    end_date: date
    occurred: bool
    result_rows: int
    unique_dancers: int


@dataclass
class ResultAgg:
    points: float = 0.0
    dancers: set[str] = field(default_factory=set)

    def add(self, dancer_id: str, points: float) -> None:
        if dancer_id:
            self.dancers.add(dancer_id)
        self.points += points


@dataclass
class Bucket:
    events: set[str]
    points: float = 0.0

    def snapshot(self, *, new_dancers: int) -> dict[str, int | float]:
        return {
            "events": len(self.events),
            "points": round(self.points, 1),
            "dancers": int(new_dancers),
        }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build homepage_kpis.json from pipeline data.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--as-of",
        default="",
        help="Anchor date YYYY-MM-DD (default: today). Used for period windows.",
    )
    return parser.parse_args()


def parse_iso_date(value: str) -> date | None:
    s = (value or "").strip()
    if not s or len(s) < 10:
        return None
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def truthy(value: str) -> bool:
    return (value or "").strip().lower() in {"1", "t", "true", "yes", "y"}


def month_start(year: int, month: int) -> date:
    return date(year, month, 1)


def month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    idx = year * 12 + (month - 1) + delta
    return idx // 12, idx % 12 + 1


def count_occurred_editions(source: Path) -> int | None:
    """Count WSDC editions that awarded points (not events_wsdc registry rows).

    Includes editions even when start_date is missing — totals must move when
    new results land, unlike the stale events_wsdc dump.
    """
    path = source / "event_editions.csv"
    if not path.exists():
        return None
    count = 0
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("event_name") or "").strip()
            if not name:
                continue
            try:
                result_rows = int(float(row.get("result_rows") or 0))
            except ValueError:
                result_rows = 0
            if truthy(row.get("event_occurred") or "") or result_rows > 0:
                count += 1
    return count


def count_catalog_events(source: Path) -> int | None:
    """Deprecated alias kept for callers; prefer count_occurred_editions."""
    return count_occurred_editions(source)


def load_editions(source: Path) -> list[Edition]:
    sched_path = source / "scheduled_events.csv"
    schedule_starts: dict[tuple[str, int, int], date] = {}
    schedule_ends: dict[tuple[str, int, int], date] = {}
    if sched_path.exists():
        with sched_path.open("r", encoding="utf-8-sig", newline="") as sf:
            for srow in csv.DictReader(sf):
                name = (srow.get("canonical_name") or srow.get("event_name") or "").strip()
                if not name:
                    continue
                try:
                    sy = int(float((srow.get("results_year") or "").strip()))
                    sm = int(float((srow.get("results_month") or "").strip()))
                except ValueError:
                    continue
                s_start = parse_iso_date(srow.get("start_date") or "")
                s_end = parse_iso_date(srow.get("end_date") or "") or s_start
                if s_start is None:
                    continue
                key = (name, sy, sm)
                # Keep earliest known start for the month bucket.
                if key not in schedule_starts or s_start < schedule_starts[key]:
                    schedule_starts[key] = s_start
                    schedule_ends[key] = s_end or s_start

    path = source / "event_editions.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing editions CSV: {path}")
    editions: list[Edition] = []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("event_name") or "").strip()
            start = parse_iso_date(row.get("start_date") or "")
            end = parse_iso_date(row.get("end_date") or "") or start
            if not name:
                continue
            try:
                year = int(float((row.get("event_year") or start.year)))
            except ValueError:
                if start is None:
                    continue
                year = start.year
            try:
                month = int(float((row.get("event_month") or "").strip() or 1))
            except ValueError:
                month = start.month if start is not None else 1
            if start is None:
                # Fallback for month-level editions (e.g., Infinite Swing 2026-07):
                # use schedule day dates so week KPI doesn't drop valid events.
                key = (name, year, month)
                start = schedule_starts.get(key)
                end = schedule_ends.get(key, start)
            if start is None:
                continue
            try:
                result_rows = int(float(row.get("result_rows") or 0))
            except ValueError:
                result_rows = 0
            try:
                unique_dancers = int(float(row.get("unique_dancers") or 0))
            except ValueError:
                unique_dancers = 0
            occurred = truthy(row.get("event_occurred") or "") or result_rows > 0
            editions.append(
                Edition(
                    event_name=name,
                    event_year=year,
                    start_date=start,
                    end_date=end or start,
                    occurred=occurred,
                    result_rows=result_rows,
                    unique_dancers=unique_dancers,
                )
            )
    return editions


def edition_end_index(editions: list[Edition]) -> dict[tuple[str, int], date]:
    """(event_name, event_year) -> earliest end_date for that edition key."""
    index: dict[tuple[str, int], date] = {}
    for ed in editions:
        key = (ed.event_name, ed.event_year)
        prev = index.get(key)
        if prev is None or ed.end_date < prev:
            index[key] = ed.end_date
    return index


def load_result_aggs(
    source: Path,
    edition_ends: dict[tuple[str, int], date],
) -> tuple[
    dict[tuple[str, int], ResultAgg],
    dict[str, int | float],
    dict[str, date],
    dict[str, int],
    date,
]:
    """Aggregate results by (event_name, year); totals; first-points date/year per dancer."""
    path = source / "dancers_results_info.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing results CSV: {path}")

    by_event: dict[tuple[str, int], ResultAgg] = defaultdict(ResultAgg)
    all_dancers: set[str] = set()
    first_points: dict[str, date] = {}
    first_wsdc_year: dict[str, int] = {}
    total_points = 0.0
    latest_ym: tuple[int, int] | None = None

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            name = (row.get("event_name") or "").strip()
            year_raw = (row.get("event_year") or "").strip()
            if not name or not year_raw:
                continue
            try:
                year = int(float(year_raw))
                month = int(float((row.get("event_month") or "1").strip() or 1))
            except ValueError:
                continue
            dancer_id = (row.get("dancer_id") or "").strip()
            try:
                points = float(row.get("event_points") or 0)
            except ValueError:
                points = 0.0
            by_event[(name, year)].add(dancer_id, points)
            if dancer_id:
                all_dancers.add(dancer_id)
                # Align first-points day with WSDC month attribution (event end).
                event_day = edition_ends.get((name, year))
                if event_day is None:
                    event_day = date(year, max(1, min(12, month)), 1)
                prev = first_points.get(dancer_id)
                if prev is None or event_day < prev:
                    first_points[dancer_id] = event_day
                    first_wsdc_year[dancer_id] = year
            total_points += points
            ym = (year, month)
            if latest_ym is None or ym > latest_ym:
                latest_ym = ym

    if latest_ym is None:
        raise RuntimeError("No dated rows found in dancers_results_info.csv")

    totals = {
        "points": round(total_points, 1),
        "dancers": len(all_dancers),
    }
    return by_event, totals, first_points, first_wsdc_year, month_end(*latest_ym)


def count_new_dancers(first_points: dict[str, date], start: date, end: date) -> int:
    """Dancers whose first WSDC points fall in [start, end] inclusive."""
    return sum(1 for day in first_points.values() if start <= day <= end)


def count_new_dancers_for_wsdc_year(first_wsdc_year: dict[str, int], year: int) -> int:
    """Dancers whose first WSDC points were earned at an event_year == year."""
    return sum(1 for y in first_wsdc_year.values() if y == year)


def aggregate_editions(
    editions: list[Edition],
    by_event: dict[tuple[str, int], ResultAgg],
) -> Bucket:
    bucket = Bucket(events=set(), points=0.0)
    for ed in editions:
        bucket.events.add(ed.event_name)
        agg = by_event.get((ed.event_name, ed.event_year))
        if agg:
            bucket.points += agg.points
    return bucket


def increment_block(
    *,
    label: str,
    start: date,
    end: date,
    snap: dict[str, int | float],
    since: date,
    extra: dict | None = None,
) -> dict:
    period: dict[str, str] = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "since_previous_ended": since.isoformat(),
    }
    if extra:
        period.update({k: str(v) for k, v in extra.items()})
    return {
        "label": label,
        "period": period,
        "increment": {
            "events": int(snap["events"]),
            "points": float(snap["points"]),
            "dancers": int(snap["dancers"]),
        },
    }


def build_week_increment(
    editions: list[Edition],
    by_event: dict[tuple[str, int], ResultAgg],
    first_points: dict[str, date],
    as_of: date,
) -> dict:
    """Latest non-empty ISO week by edition start_date (occurred events only)."""
    by_week: dict[tuple[int, int], list[Edition]] = defaultdict(list)
    for ed in editions:
        if not ed.occurred or ed.start_date > as_of:
            continue
        iso = ed.start_date.isocalendar()
        by_week[(int(iso.year), int(iso.week))].append(ed)

    as_of_week = as_of.isocalendar()
    cutoff = (int(as_of_week.year), int(as_of_week.week))
    keys = sorted(k for k in by_week if k <= cutoff and by_week[k])
    if not keys:
        # empty fallback: last completed calendar week
        if as_of.isoweekday() == 7:
            last_sunday = as_of
        else:
            last_sunday = as_of - timedelta(days=as_of.isoweekday())
        iso = last_sunday.isocalendar()
        cur = (int(iso.year), int(iso.week))
        week_editions: list[Edition] = []
    else:
        cur = keys[-1]
        week_editions = by_week[cur]

    cur_start = date.fromisocalendar(cur[0], cur[1], 1)
    cur_end = date.fromisocalendar(cur[0], cur[1], 7)
    since = month_end(*add_months(cur_end.year, cur_end.month, -1))
    new_dancers = count_new_dancers(first_points, cur_start, cur_end)
    snap = aggregate_editions(week_editions, by_event).snapshot(new_dancers=new_dancers)
    return increment_block(
        label="Week",
        start=cur_start,
        end=cur_end,
        snap=snap,
        since=since,
        extra={
            "iso_week": f"{cur[0]}-W{cur[1]:02d}",
            "bucket": "edition_start_date",
            "event_names": ", ".join(sorted({e.event_name for e in week_editions})),
        },
    )


def build_month_increment(
    editions: list[Edition],
    by_event: dict[tuple[str, int], ResultAgg],
    first_points: dict[str, date],
    as_of: date,
) -> dict:
    cur = (as_of.year, as_of.month)
    prev = add_months(cur[0], cur[1], -1)
    month_editions = [
        ed
        for ed in editions
        if ed.occurred
        and ed.start_date.year == as_of.year
        and ed.start_date.month == as_of.month
        and ed.start_date <= as_of
    ]
    period_start = month_start(*cur)
    new_dancers = count_new_dancers(first_points, period_start, as_of)
    snap = aggregate_editions(month_editions, by_event).snapshot(new_dancers=new_dancers)
    return increment_block(
        label="Month",
        start=period_start,
        end=as_of,
        snap=snap,
        since=month_end(*prev),
        extra={
            "bucket": "edition_start_date",
            "event_names": ", ".join(sorted({e.event_name for e in month_editions})),
        },
    )


def build_year_increment(
    by_event: dict[tuple[str, int], ResultAgg],
    first_wsdc_year: dict[str, int],
    as_of: date,
) -> dict:
    """WSDC results year (event_year), including late-December New Year editions."""
    year = as_of.year
    names = {name for (name, y) in by_event if y == year}
    points = 0.0
    for name in names:
        agg = by_event.get((name, year))
        if agg:
            points += agg.points
    snap = {
        "events": len(names),
        "points": round(points, 1),
        "dancers": count_new_dancers_for_wsdc_year(first_wsdc_year, year),
    }
    return increment_block(
        label="Year",
        start=date(year, 1, 1),
        end=as_of,
        snap=snap,
        since=date(year - 1, 12, 31),
        extra={"bucket": "event_year"},
    )


def main() -> None:
    args = parse_args()
    source = args.source_dir.expanduser().resolve()
    output = args.output.expanduser().resolve()
    as_of_arg = date.fromisoformat(args.as_of) if args.as_of else None

    editions = load_editions(source)
    edition_ends = edition_end_index(editions)
    by_event, result_totals, first_points, first_wsdc_year, data_through = load_result_aggs(
        source, edition_ends
    )
    occurred_editions = count_occurred_editions(source)

    as_of = as_of_arg or date.today()
    if as_of > data_through:
        # allow as_of up to today even if results month-end is later via editions
        pass
    # Cap only if beyond latest edition end we know about
    latest_end = max((ed.end_date for ed in editions if ed.occurred), default=data_through)
    if as_of > max(data_through, latest_end) and as_of > date.today():
        as_of = date.today()

    totals = {
        "events": (
            occurred_editions
            if occurred_editions is not None
            else len({(ed.event_name, ed.event_year) for ed in editions if ed.occurred})
        ),
        "points": result_totals["points"],
        "dancers": result_totals["dancers"],
    }

    comparisons = {
        "week": build_week_increment(editions, by_event, first_points, as_of),
        "month": build_month_increment(editions, by_event, first_points, as_of),
        "year": build_year_increment(by_event, first_wsdc_year, as_of),
    }

    calendar_path = source / "edition_calendar_dates.csv"
    payload = {
        "generated_at": date.today().isoformat(),
        "as_of": as_of.isoformat(),
        "data_through": data_through.isoformat(),
        "source_dir": str(source),
        "methodology": {
            "events_total": (
                "count of occurred WSDC editions in event_editions.csv "
                "(result_rows > 0 or event_occurred); one row per event year/month that awarded points"
            ),
            "points_total": "sum of event_points across all nominations in dancers_results_info.csv",
            "dancers_total": "count of unique dancer_id in dancers_results_info.csv",
            "dancers_increment": (
                "new dancers = unique dancer_id whose first WSDC points fall in the window "
                "(week/month: earliest edition end_date; year: event_year of that first event)"
            ),
            "edition_dates": "event_editions.csv start_date/end_date (edition_date remains YYYY-MM-01 for Tableau)",
            "calendar_archive": str(calendar_path) if calendar_path.exists() else None,
            "as_of_note": "as_of defaults to today.",
            "increment_note": (
                "Events/points increments count activity in the window. "
                "Dancers increment counts new dancers (first WSDC points), not unique participants. "
                "Week/month windows use edition start_date so cross-month events count once."
            ),
            "week_note": (
                "Week uses ISO week of edition start_date for occurred events. Never advances to a week "
                "with no occurred events (e.g. Jul 13-19 empty → keep Jul 6-12). Baseline "
                "since_previous_ended is end of previous calendar month."
            ),
            "month_note": (
                "Month increment = occurred editions with start_date in the current month through as_of; "
                "new dancers with first points in that window."
            ),
            "year_note": (
                "Year increment uses WSDC event_year (not calendar end_date year), so late-December "
                "New Year events count toward the new year. Events = distinct event_name in results "
                "for that event_year; points = sum for those events; dancers = new dancers whose "
                "first points were at an event_year in this year."
            ),
        },
        "totals": totals,
        "comparisons": comparisons,
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")
    print(
        f"as_of={payload['as_of']} totals="
        f"events={totals['events']} points={totals['points']} dancers={totals['dancers']}"
    )
    for scale in ("week", "month", "year"):
        block = comparisons[scale]
        inc = block["increment"]
        print(
            f"{block['label']}: {block['period']['start']}→{block['period']['end']} "
            f"+events={inc['events']} +points={inc['points']} +new_dancers={inc['dancers']}"
        )


if __name__ == "__main__":
    main()
