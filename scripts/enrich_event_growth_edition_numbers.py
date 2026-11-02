#!/usr/bin/env python3
"""Bake full-history edition ordinals into event_growth.json.

Growth JSON is truncated at year_floor (2018), but WSDC history in
event_editions.csv starts in 1991. Each retained edition gets an `edition`
field = 1-based ordinal among scored editions of that series up to
(and including) that edition's start date.

By default the series key is event_id. Year-split rebrands with
`reset_edition_ordinal: True` in pipeline EVENT_NAME_YEAR_SPLITS split one
event_id into early/late eras (e.g. Paris Westie Fest ≤2022 vs Paris Swing
Classic ≥2023). The first late-era edition is forced to status=new with no
prev/delta so tips do not compare across brands.

Usage:
  python3 scripts/enrich_event_growth_edition_numbers.py
  python3 scripts/enrich_event_growth_edition_numbers.py \\
    --editions ~/…/wsdc-data-pipeline/data/event_editions.csv
"""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, DefaultDict, Dict, List, Optional

REPO = Path(__file__).resolve().parents[1]
DEFAULT_GROWTH = REPO / "static" / "data" / "event_growth.json"

# Used only if pipeline event_aliases.py cannot be parsed.
_FALLBACK_EDITION_SERIES_SPLITS: List[Dict[str, int]] = [
    {"event_id": 272, "early_year_max": 2022, "late_year_min": 2023},
]


def default_editions_csv() -> Path:
    """Resolve event_editions.csv via env, sibling pipeline checkout, or home path."""
    env = os.environ.get("EVENT_EDITIONS_CSV")
    if env:
        return Path(env)
    candidates = [
        REPO.parent / "projects/python/wsdc-data-pipeline/data/event_editions.csv",
        Path.home()
        / ".cursor/projects/python/wsdc-data-pipeline/data/event_editions.csv",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def default_event_aliases_py() -> Path:
    env = os.environ.get("EVENT_ALIASES_PY")
    if env:
        return Path(env)
    candidates = [
        REPO.parent
        / "projects/python/wsdc-data-pipeline/transform/knowledge/event_aliases.py",
        Path.home()
        / ".cursor/projects/python/wsdc-data-pipeline/transform/knowledge/event_aliases.py",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


DEFAULT_EDITIONS = default_editions_csv()
DEFAULT_ALIASES = default_event_aliases_py()


def edition_splits_from_year_split_rules(
    rules: List[Dict[str, Any]],
) -> List[Dict[str, int]]:
    """Keep only year-splits that opt into resetting #edition on rebrand."""
    out: List[Dict[str, int]] = []
    for rule in rules:
        if not rule.get("reset_edition_ordinal"):
            continue
        eid = rule.get("late_event_id", rule.get("early_event_id"))
        try:
            out.append(
                {
                    "event_id": int(eid),  # type: ignore[arg-type]
                    "early_year_max": int(rule["early_year_max"]),
                    "late_year_min": int(rule["late_year_min"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue
    return out


def load_edition_series_splits_from_aliases(
    path: Path,
) -> List[Dict[str, int]]:
    """Parse EVENT_NAME_YEAR_SPLITS via AST (no pandas / package import)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if not isinstance(node.target, ast.Name):
            continue
        if node.target.id != "EVENT_NAME_YEAR_SPLITS" or node.value is None:
            continue
        rules = ast.literal_eval(node.value)
        if not isinstance(rules, list):
            break
        return edition_splits_from_year_split_rules(rules)
    raise ValueError(f"EVENT_NAME_YEAR_SPLITS not found in {path}")


def resolve_edition_series_splits(
    aliases_path: Optional[Path] = None,
) -> List[Dict[str, int]]:
    path = aliases_path if aliases_path is not None else DEFAULT_ALIASES
    if path.is_file():
        try:
            return load_edition_series_splits_from_aliases(path)
        except (SyntaxError, ValueError, TypeError) as exc:
            print(
                f"WARN: could not load year-splits from {path}: {exc}; "
                "using fallback",
                file=sys.stderr,
            )
    return list(_FALLBACK_EDITION_SERIES_SPLITS)


# Resolved at import for callers/tests that expect a module-level list; refresh
# via resolve_edition_series_splits() when a custom aliases path is needed.
EDITION_SERIES_SPLITS: List[Dict[str, int]] = resolve_edition_series_splits()


def chrono_key(year: Any, month: Any = None, day: Any = None) -> Optional[int]:
    try:
        y = int(year)
    except (TypeError, ValueError):
        return None
    try:
        m = int(month) if month is not None and str(month) != "" else 0
    except (TypeError, ValueError):
        m = 0
    try:
        d = int(day) if day is not None and str(day) != "" else 0
    except (TypeError, ValueError):
        d = 0
    return y * 10000 + m * 100 + d


def chrono_from_row(row: Dict[str, str]) -> Optional[int]:
    start = (row.get("start_date") or row.get("edition_date") or "").strip()
    if len(start) >= 7:
        return chrono_key(
            start[0:4],
            start[5:7],
            start[8:10] if len(start) >= 10 else 1,
        )
    return chrono_key(row.get("event_year"), row.get("event_month"), 0)


def chrono_from_growth(ed: Dict[str, Any]) -> Optional[int]:
    start = ed.get("start")
    if start and len(str(start)) >= 7:
        s = str(start)
        return chrono_key(
            s[0:4],
            s[5:7],
            s[8:10] if len(s) >= 10 else 1,
        )
    return chrono_key(ed.get("year"), ed.get("month"), 0)


def year_from_chrono(key: int) -> int:
    return key // 10000


def series_bucket(
    event_id: int,
    year: int,
    splits: Optional[List[Dict[str, int]]] = None,
) -> str:
    """Stable key for edition counting; may split one event_id into eras."""
    for rule in splits if splits is not None else EDITION_SERIES_SPLITS:
        if int(rule["event_id"]) != int(event_id):
            continue
        early_max = int(rule["early_year_max"])
        late_min = int(rule["late_year_min"])
        if year <= early_max:
            return f"{event_id}:early:<={early_max}"
        # year > early_max (including gaps before late_min) → late era.
        return f"{event_id}:late:>={late_min}"
    return str(event_id)


def is_late_era_bucket(bucket: str) -> bool:
    return ":late:" in bucket


def clear_cross_brand_prev(ed: Dict[str, Any]) -> None:
    """First edition of a reset late-era brand is a debut, not a restart."""
    ed["status"] = "new"
    if "gap_flag" in ed:
        del ed["gap_flag"]
    if "prev" in ed:
        del ed["prev"]
    ed["delta"] = None
    ed["pct"] = None


def classify_growth(
    current: Optional[int],
    previous: Optional[int],
    year_gap: Optional[int],
    thr_pct: float = 0.10,
    thr_abs: int = 10,
) -> tuple[str, Optional[int], Optional[float], Optional[str]]:
    """Mirror pipeline event_growth.classify_growth for in-file prev restore."""
    if previous is None or current is None:
        return "new", None, None, None
    if year_gap is None or year_gap < 0:
        return "new", None, None, None
    if year_gap >= 3:
        return "restarted", None, None, "restarted"
    gap_flag = "after_1yr_break" if year_gap == 2 else None
    delta = int(current) - int(previous)
    if previous == 0:
        pct = None
        if abs(delta) >= thr_abs:
            status = "growing" if delta > 0 else "declining"
        else:
            status = "stable"
        return status, delta, pct, gap_flag
    pct = delta / float(previous)
    if abs(pct) >= thr_pct and abs(delta) >= thr_abs:
        status = "growing" if delta > 0 else "declining"
    else:
        status = "stable"
    return status, delta, pct, gap_flag


def restore_missing_prev_within_buckets(
    editions: List[Dict[str, Any]],
    splits: List[Dict[str, int]],
    thr_pct: float = 0.10,
    thr_abs: int = 10,
) -> int:
    """Relink prev when a continuous series lost it (e.g. after undoing a reset).

    Only fills empty prev when an earlier edition of the same series_bucket
    exists in the growth file. True debuts (first in bucket) stay untouched.
    """
    buckets: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    for ed in editions:
        try:
            eid = int(ed["event_id"])
            year = int(ed["year"])
        except (KeyError, TypeError, ValueError):
            continue
        buckets[series_bucket(eid, year, splits)].append(ed)

    restored = 0
    for rows in buckets.values():
        rows.sort(
            key=lambda e: (
                int(e.get("year") or 0),
                int(e.get("month") or 0),
                str(e.get("name") or ""),
            )
        )
        for i, ed in enumerate(rows):
            if i == 0 or ed.get("prev") is not None:
                continue
            prev = rows[i - 1]
            if prev.get("competitors") is None or ed.get("competitors") is None:
                continue
            try:
                year_gap = int(ed["year"]) - int(prev["year"])
            except (KeyError, TypeError, ValueError):
                continue
            status, delta, pct, gap_flag = classify_growth(
                int(ed["competitors"]),
                int(prev["competitors"]),
                year_gap,
                thr_pct=thr_pct,
                thr_abs=thr_abs,
            )
            ed["prev"] = {
                "year": int(prev["year"]),
                "month": prev.get("month"),
                "competitors": int(prev["competitors"]),
                "approx": prev.get("approx") or 0,
                "source": prev.get("source") or ("approx" if prev.get("approx") else "exact"),
            }
            ed["status"] = status
            ed["delta"] = delta
            ed["pct"] = pct
            if gap_flag:
                ed["gap_flag"] = gap_flag
            elif "gap_flag" in ed:
                del ed["gap_flag"]
            restored += 1
    return restored



def load_history(
    path: Path,
    splits: Optional[List[Dict[str, int]]] = None,
) -> DefaultDict[str, List[int]]:
    """series_bucket → sorted chrono keys for every historical edition."""
    by: DefaultDict[str, List[int]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            try:
                eid = int(row["event_id"])
            except (KeyError, TypeError, ValueError):
                continue
            key = chrono_from_row(row)
            if key is None:
                continue
            try:
                year = int(row.get("event_year") or year_from_chrono(key))
            except (TypeError, ValueError):
                year = year_from_chrono(key)
            bucket = series_bucket(eid, year, splits)
            by[bucket].append(key)
    for bucket in by:
        by[bucket] = sorted(set(by[bucket]))
    return by


def edition_ordinal(history_keys: List[int], self_key: int) -> int:
    return sum(1 for k in history_keys if k <= self_key)


def enrich(
    growth: Dict[str, Any],
    history: DefaultDict[str, List[int]],
    splits: Optional[List[Dict[str, int]]] = None,
) -> Dict[str, int]:
    stats = {
        "editions": 0,
        "with_history": 0,
        "missing_history": 0,
        "edition_gt_1_at_floor": 0,
        "split_buckets_used": 0,
        "cross_brand_prev_cleared": 0,
        "prev_restored": 0,
    }
    floor = growth.get("year_floor")
    split_rules = splits if splits is not None else EDITION_SERIES_SPLITS
    thr = growth.get("thresholds") or {}
    thr_pct = float(thr.get("pct", 0.10))
    thr_abs = int(thr.get("abs", 10))
    for ed in growth.get("editions") or []:
        stats["editions"] += 1
        try:
            eid = int(ed["event_id"])
        except (KeyError, TypeError, ValueError):
            ed.pop("edition", None)
            stats["missing_history"] += 1
            continue
        self_key = chrono_from_growth(ed)
        try:
            year = int(ed.get("year") or year_from_chrono(self_key or 0))
        except (TypeError, ValueError):
            year = year_from_chrono(self_key) if self_key else 0
        bucket = series_bucket(eid, year, split_rules)
        if ":" in bucket:
            stats["split_buckets_used"] += 1
        keys = history.get(bucket) or []
        if self_key is None or not keys:
            ed.pop("edition", None)
            stats["missing_history"] += 1
            continue
        n = edition_ordinal(keys, self_key)
        if n <= 0:
            ed.pop("edition", None)
            stats["missing_history"] += 1
            continue
        ed["edition"] = n
        stats["with_history"] += 1
        if floor is not None and ed.get("year") == floor and n > 1:
            stats["edition_gt_1_at_floor"] += 1
        # Debut of a reset late brand must not YoY-compare to the early brand.
        if is_late_era_bucket(bucket) and n == 1 and (
            ed.get("prev") is not None or ed.get("status") == "restarted"
        ):
            clear_cross_brand_prev(ed)
            stats["cross_brand_prev_cleared"] += 1
    # After clears: restore prev inside continuous buckets when it was wiped
    # (e.g. BTO → Calgary Town Open after turning reset_edition_ordinal off).
    stats["prev_restored"] = restore_missing_prev_within_buckets(
        list(growth.get("editions") or []),
        split_rules,
        thr_pct=thr_pct,
        thr_abs=thr_abs,
    )
    growth["edition_enrichment"] = {
        "source": "event_editions.csv",
        "enriched_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "series_splits": list(split_rules),
        "stats": stats,
    }
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--growth", type=Path, default=DEFAULT_GROWTH)
    ap.add_argument("--editions", type=Path, default=DEFAULT_EDITIONS)
    ap.add_argument(
        "--aliases",
        type=Path,
        default=DEFAULT_ALIASES,
        help="pipeline event_aliases.py (EVENT_NAME_YEAR_SPLITS source)",
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not args.growth.is_file():
        print(f"growth file not found: {args.growth}", file=sys.stderr)
        return 1
    if not args.editions.is_file():
        print(f"event_editions.csv not found: {args.editions}", file=sys.stderr)
        return 1

    splits = resolve_edition_series_splits(args.aliases)
    print(
        f"edition series splits ({len(splits)}): "
        + ", ".join(
            f"{s['event_id']}(≤{s['early_year_max']}/≥{s['late_year_min']})"
            for s in splits
        )
    )

    growth = json.loads(args.growth.read_text(encoding="utf-8"))
    history = load_history(args.editions, splits)
    stats = enrich(growth, history, splits)
    print(
        f"editions={stats['editions']} with_history={stats['with_history']} "
        f"missing={stats['missing_history']} "
        f"edition>1_at_floor={stats['edition_gt_1_at_floor']} "
        f"split_buckets={stats['split_buckets_used']} "
        f"cross_brand_cleared={stats['cross_brand_prev_cleared']} "
        f"history_buckets={len(history)}"
    )
    asia = [
        e
        for e in growth.get("editions") or []
        if e.get("event_id") == 218 and e.get("year") == 2023
    ]
    if asia:
        print(f"Asia Open 2023 edition=#{asia[0].get('edition')}")
    paris = [
        e for e in growth.get("editions") or [] if e.get("event_id") == 272
    ]
    paris.sort(key=lambda e: e.get("year") or 0)
    for e in paris:
        print(
            f"Paris {e.get('year')} {e.get('name')}: edition=#{e.get('edition')} "
            f"status={e.get('status')}"
        )

    if args.dry_run:
        print("dry-run: not writing")
        return 0

    args.growth.write_text(
        json.dumps(growth, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {args.growth}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
