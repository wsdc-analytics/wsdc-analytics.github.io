#!/usr/bin/env python3
"""Build division transition time metrics for wsdc-analytics article."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from datetime import date
from pathlib import Path

SKILL_DIVISIONS = ["Novice", "Intermediate", "Advanced", "All-Stars", "Champions"]
ARTICLE_TRANSITIONS = [
    ("Novice", "Intermediate"),
    ("Intermediate", "Advanced"),
    ("Advanced", "All-Stars"),
    ("All-Stars", "Champions"),
]
MIN_N_DISPLAY = 30
BASELINE_YEARS = {2021, 2022}
CURRENT_YEARS = {2024, 2025}
COHORT_PERIODS = {
    "2010-2018": frozenset(range(2010, 2019)),
    "2023-2024": frozenset({2023, 2024}),
}
COHORT_WINDOW_MONTHS = 12
ROLES = ("Leader", "Follower", "All")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update division transition metrics JSON.")
    parser.add_argument(
        "--source-dir",
        default="/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points",
    )
    parser.add_argument(
        "--output",
        default="/Users/ania/.cursor/wsdc-analytics-repo/static/data/division_transition_metrics.json",
    )
    parser.add_argument(
        "--rules",
        default="/Users/ania/.cursor/wsdc-analytics-repo/static/data/rules_advancement_thresholds.json",
    )
    parser.add_argument("--raw-csv", default="")
    return parser.parse_args()


def norm_div(value: str) -> str | None:
    v = (value or "").strip()
    if v in {"All Star", "All Stars", "All-Stars"}:
        return "All-Stars"
    if v in {"Champion", "Champions"}:
        return "Champions"
    if v in SKILL_DIVISIONS:
        return v
    return None


def parse_date(ym: str, year: str = "", month: str = "") -> tuple[int, int] | None:
    if not ym and year and month:
        try:
            return (int(float(year)), int(float(month)))
        except ValueError:
            return None
    if not ym:
        return None
    s = str(ym).strip()
    if "-" in s:
        parts = s.split("-")
        try:
            return (int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            return None
    if len(s) >= 6:
        try:
            return (int(s[:4]), int(s[4:6]))
        except ValueError:
            return None
    return None


def ym_ord(y: int, m: int) -> int:
    return y * 12 + m


def months_between(a: tuple[int, int], b: tuple[int, int]) -> int:
    return (b[0] - a[0]) * 12 + (b[1] - a[1])


def median_safe(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def cohort_conversion_stats(
    first_pts: dict,
    dominate: dict,
    from_div: str,
    to_div: str,
    cohort_years: frozenset[int],
    role: str,
    window_months: int = COHORT_WINDOW_MONTHS,
) -> dict:
    starters = converted = 0
    for did, fp in first_pts.items():
        if from_div not in fp:
            continue
        if fp[from_div][0] not in cohort_years:
            continue
        dancer_role = dominate[did]
        if role != "All" and dancer_role != role:
            continue
        starters += 1
        if to_div not in fp:
            continue
        if months_between(fp[from_div], fp[to_div]) <= window_months:
            converted += 1
    rate = round(100 * converted / starters, 1) if starters else None
    return {
        "starters": starters,
        "converted": converted,
        "rate_pct": rate,
    }


def aggregate_stats(months_list: list[float]) -> dict:
    if not months_list:
        return {"n": 0, "median_months": None, "mean_months": None, "p25": None, "p75": None}
    qs = statistics.quantiles(months_list, n=4) if len(months_list) >= 2 else [months_list[0], months_list[0], months_list[0]]
    return {
        "n": len(months_list),
        "median_months": round(median_safe(months_list) or 0, 2),
        "mean_months": round(sum(months_list) / len(months_list), 2),
        "p25": round(qs[0], 2),
        "p75": round(qs[2], 2),
    }


def threshold_for_year(rules: dict, year: int, division: str) -> dict:
    for epoch in rules.get("epochs", []):
        vf = epoch.get("valid_from")
        vt = epoch.get("valid_to")
        if vf is not None and year < vf:
            continue
        if vt is not None and year > vt:
            continue
        model = epoch.get("model")
        if model == "allowed_required_36mo":
            d = epoch.get("divisions", {}).get(division)
            if d and "allowed" in d:
                return {
                    "allowed": d["allowed"],
                    "required": d["required"],
                    "epoch": epoch["id"],
                }
        if model == "cumulative":
            trans = epoch.get("transitions", {})
            if division in trans:
                p = trans[division]["points"]
                return {"allowed": p, "required": p, "epoch": epoch["id"], "cumulative": True}
    return {}


def rolling_sum(events: list[dict], div: str, at_ym: tuple[int, int], window: int = 36) -> float:
    at = ym_ord(*at_ym)
    lo = at - window + 1
    return sum(e["pts"] for e in events if e["div"] == div and lo <= ym_ord(*e["ym"]) <= at)


def main() -> None:
    args = parse_args()
    source = Path(args.source_dir)
    output = Path(args.output)
    rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))

    dominate: dict[str, str] = {}
    with (source / "dancer_role_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            role = (row.get("dominate_role") or "").strip().title()
            if did and role in ("Leader", "Follower"):
                dominate[did] = role

    events_by_dancer: dict[str, list[dict]] = defaultdict(list)
    first_pts: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    last_pts: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    ecosystem: dict[int, dict] = defaultdict(
        lambda: {"events": set(), "dancers": set(), "total_points": 0.0}
    )
    excluded = {
        "invalid_date": 0,
        "non_skill_division": 0,
        "no_dominate_role": 0,
        "non_positive_points": 0,
        "transition_non_positive_months": 0,
        "transition_to_not_after_from": 0,
        "last_first_overlap": 0,
    }

    with (source / "dancers_results_info.csv").open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if did not in dominate:
                excluded["no_dominate_role"] += 1
                continue
            div = norm_div(row.get("event_competition") or "")
            if div is None:
                excluded["non_skill_division"] += 1
                continue
            role = (row.get("event_role") or "").strip().title()
            if role != dominate[did]:
                continue
            try:
                pts = float(row.get("event_points") or 0)
            except ValueError:
                pts = 0
            if pts <= 0:
                excluded["non_positive_points"] += 1
                continue
            dt = parse_date(
                row.get("event_year_and_month") or "",
                row.get("event_year") or "",
                row.get("event_month") or "",
            )
            if dt is None:
                excluded["invalid_date"] += 1
                continue
            y, m = dt
            eid = (row.get("event_name_id") or row.get("event_name") or "").strip()
            ecosystem[y]["events"].add(eid or f"{row.get('event_name')}_{y}")
            ecosystem[y]["dancers"].add(did)
            ecosystem[y]["total_points"] += pts

            events_by_dancer[did].append({"div": div, "pts": pts, "ym": dt, "year": y})
            if div not in first_pts[did] or dt < first_pts[did][div]:
                first_pts[did][div] = dt
            if div not in last_pts[did] or dt > last_pts[did][div]:
                last_pts[did][div] = dt

    for did in events_by_dancer:
        events_by_dancer[did].sort(key=lambda e: ym_ord(*e["ym"]))

    raw_rows: list[dict] = []
    m1_buckets: dict[tuple, list[float]] = defaultdict(list)
    m1b_buckets: dict[tuple, list[float]] = defaultdict(list)
    transition_counts: dict[tuple, int] = defaultdict(int)

    for from_div, to_div in ARTICLE_TRANSITIONS:
        for did in first_pts:
            if from_div not in first_pts[did] or to_div not in first_pts[did]:
                continue
            t_from = first_pts[did][from_div]
            t_to = first_pts[did][to_div]
            if t_to <= t_from:
                excluded["transition_to_not_after_from"] += 1
                continue
            months_ff = months_between(t_from, t_to)
            if months_ff < 0:
                excluded["transition_non_positive_months"] += 1
                continue
            role = dominate[did]
            ty = t_to[0]
            m1_buckets[(ty, role, from_div, to_div, "first_to_first")].append(float(months_ff))

            t_last = last_pts[did].get(from_div)
            months_lf = None
            if t_last:
                if t_to > t_last:
                    months_lf = months_between(t_last, t_to)
                else:
                    excluded["last_first_overlap"] += 1
            if months_lf is not None and months_lf >= 0:
                m1b_buckets[(ty, role, from_div, to_div, "last_to_first")].append(float(months_lf))

            raw_rows.append(
                {
                    "dancer_id": did,
                    "dominate_role": role,
                    "from_division": from_div,
                    "to_division": to_div,
                    "transition_year": ty,
                    "months_first_first": months_ff,
                    "months_last_first": months_lf if months_lf is not None else "",
                }
            )
            transition_counts[(ty, role, from_div, to_div)] += 1

    counts_all: dict[tuple, int] = defaultdict(int)
    for (ty, role, from_div, to_div), n in transition_counts.items():
        counts_all[(ty, from_div, to_div)] += n
    for key, n in counts_all.items():
        ty, from_div, to_div = key
        transition_counts[(ty, "All", from_div, to_div)] = n

    transition_series = []
    years_all = sorted({k[0] for k in m1_buckets} | {k[0] for k in m1b_buckets})
    for ty in years_all:
        for role in ROLES:
            for from_div, to_div in ARTICLE_TRANSITIONS:
                for variant, bucket in (
                    ("first_to_first", m1_buckets),
                    ("last_to_first", m1b_buckets),
                ):
                    if role == "All":
                        vals = []
                        for r in ("Leader", "Follower"):
                            vals.extend(bucket.get((ty, r, from_div, to_div, variant), []))
                    else:
                        vals = bucket.get((ty, role, from_div, to_div, variant), [])
                    stats = aggregate_stats(vals)
                    stats.update(
                        {
                            "transition_year": ty,
                            "role": role,
                            "from_division": from_div,
                            "to_division": to_div,
                            "metric_variant": variant,
                            "suppress": stats["n"] < MIN_N_DISPLAY,
                        }
                    )
                    transition_series.append(stats)

    # m2: first calendar year when rolling 36-mo sum in D reaches threshold
    m2_by_dancer: dict[tuple, float] = {}
    for did, evs in events_by_dancer.items():
        role = dominate[did]
        for div in ("Novice", "Intermediate"):
            if div not in first_pts[did]:
                continue
            t0 = first_pts[did][div]
            reached: dict[str, bool] = {}
            for e in evs:
                if e["div"] != div or e["ym"] < t0:
                    continue
                year = e["year"]
                th = threshold_for_year(rules, year, div)
                if not th:
                    continue
                roll = rolling_sum(evs, div, e["ym"], 36)
                months_from_start = months_between(t0, e["ym"])
                for kind in ("allowed", "required"):
                    if reached.get(kind):
                        continue
                    target = th.get(kind)
                    if target is not None and roll >= target:
                        reached[kind] = True
                        key = (did, div, kind)
                        if key not in m2_by_dancer:
                            m2_by_dancer[key] = (months_from_start, year, role, target)

    m2_buckets: dict[tuple, list[float]] = defaultdict(list)
    for (_did, div, kind), (months, cross_year, role, _target) in m2_by_dancer.items():
        m2_buckets[(cross_year, div, kind, role)].append(float(months))

    m2_all: dict[tuple, list[float]] = defaultdict(list)
    for (y, div, kind, role), vals in m2_buckets.items():
        m2_all[(y, div, kind)].extend(vals)
    for key, vals in m2_all.items():
        y, div, kind = key
        m2_buckets[(y, div, kind, "All")] = vals

    months_to_threshold = []
    for key, vals in sorted(m2_buckets.items()):
        y, div, ttype, role = key
        stats = aggregate_stats(vals)
        th = threshold_for_year(rules, y, div)
        stats.update(
            {
                "year": y,
                "division": div,
                "threshold_type": ttype,
                "role": role,
                "threshold_points": th.get(ttype),
                "suppress": stats["n"] < MIN_N_DISPLAY,
            }
        )
        months_to_threshold.append(stats)

    cohort_conversion = []
    for period_id, cohort_years in COHORT_PERIODS.items():
        for from_div, to_div in ARTICLE_TRANSITIONS[:3]:
            for role in ROLES:
                stats = cohort_conversion_stats(
                    first_pts, dominate, from_div, to_div, cohort_years, role
                )
                cohort_conversion.append(
                    {
                        "cohort_period": period_id,
                        "window_months": COHORT_WINDOW_MONTHS,
                        "role": role,
                        "from_division": from_div,
                        "to_division": to_div,
                        **stats,
                    }
                )

    implied_thresholds = []
    for div in ("Novice", "Intermediate"):
        for ttype in ("allowed", "required"):
            for role in ("All",):
                base_meds, cur_meds = [], []
                th_base = threshold_for_year(rules, 2021, div).get(ttype)
                for (y, d, tt, r), vals in m2_buckets.items():
                    if d != div or tt != ttype or r != role:
                        continue
                    med = median_safe(vals)
                    if med is None:
                        continue
                    if y in BASELINE_YEARS:
                        base_meds.append(med)
                    if y in CURRENT_YEARS:
                        cur_meds.append(med)
                med_base = median_safe(base_meds)
                med_cur = median_safe(cur_meds)
                if not th_base or not med_base or not med_cur or med_cur <= 0:
                    continue
                ratio = med_base / med_cur
                implied_thresholds.append(
                    {
                        "division": div,
                        "threshold_type": ttype,
                        "role": role,
                        "baseline_years": sorted(BASELINE_YEARS),
                        "current_years": sorted(CURRENT_YEARS),
                        "actual_threshold": th_base,
                        "median_months_baseline": round(med_base, 2),
                        "median_months_current": round(med_cur, 2),
                        "implied_threshold": round(th_base * ratio, 1),
                        "ratio_baseline_over_current": round(ratio, 3),
                    }
                )

    velocity: dict[tuple, list[float]] = defaultdict(list)
    pts_acc: dict[tuple, float] = defaultdict(float)
    for did, evs in events_by_dancer.items():
        for e in evs:
            if e["div"] not in SKILL_DIVISIONS:
                continue
            pts_acc[(e["year"], e["div"], dominate[did], did)] += e["pts"]
    for (y, div, role, _did), total in pts_acc.items():
        velocity[(y, div, role)].append(total)

    points_velocity = []
    for key, vals in sorted(velocity.items()):
        y, div, role = key
        stats = aggregate_stats(vals)
        stats.update({"year": y, "division": div, "role": role})
        points_velocity.append(stats)

    payload = {
        "data_as_of": date.today().isoformat(),
        "source_dir": str(source),
        "min_n_display": MIN_N_DISPLAY,
        "article_transitions": [{"from": a, "to": b} for a, b in ARTICLE_TRANSITIONS],
        "baseline_years": sorted(BASELINE_YEARS),
        "current_years": sorted(CURRENT_YEARS),
        "excluded_counts": excluded,
        "transition_series": transition_series,
        "cohort_conversion": cohort_conversion,
        "transitions_count_by_year": [
            {
                "transition_year": ty,
                "role": role,
                "from_division": fd,
                "to_division": td,
                "n": n,
            }
            for (ty, role, fd, td), n in sorted(transition_counts.items())
        ],
        "ecosystem_by_year": [
            {
                "year": y,
                "unique_events": len(eco["events"]),
                "unique_dancers": len(eco["dancers"]),
                "total_points": round(eco["total_points"], 1),
            }
            for y, eco in sorted(ecosystem.items())
        ],
        "months_to_threshold": months_to_threshold,
        "implied_thresholds": implied_thresholds,
        "points_velocity": points_velocity,
        "rules_epochs_ref": "rules_advancement_thresholds.json",
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {output}")

    if args.raw_csv:
        p = Path(args.raw_csv)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(raw_rows[0].keys()))
            w.writeheader()
            w.writerows(raw_rows)
        print(f"Wrote {p}")


if __name__ == "__main__":
    main()
