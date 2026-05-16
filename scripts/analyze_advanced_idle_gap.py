#!/usr/bin/env python3
"""Advanced eligibility vs first All-Stars points — idle gap analysis."""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from pathlib import Path

SOURCE = Path("/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points")


def norm_div(value: str) -> str | None:
    v = (value or "").strip()
    if v in {"All Star", "All Stars", "All-Stars"}:
        return "All-Stars"
    if v in {"Champion", "Champions"}:
        return "Champions"
    if v in {"Novice", "Intermediate", "Advanced", "All-Stars", "Champions"}:
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


def rolling_sum(events: list[dict], div: str, at_ym: tuple[int, int], window: int = 36) -> float:
    at = ym_ord(*at_ym)
    lo = at - window + 1
    return sum(
        e["pts"] for e in events if e["div"] == div and lo <= ym_ord(*e["ym"]) <= at
    )


def load_data():
    dominate: dict[str, str] = {}
    with (SOURCE / "dancer_role_info.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            role = (row.get("dominate_role") or "").strip().title()
            if did and role in ("Leader", "Follower"):
                dominate[did] = role

    first_pts: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    events_by_dancer: dict[str, list[dict]] = defaultdict(list)

    with (SOURCE / "dancers_results_info.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if did not in dominate:
                continue
            div = norm_div(row.get("event_competition") or "")
            if div is None:
                continue
            if (row.get("event_role") or "").strip().title() != dominate[did]:
                continue
            try:
                pts = float(row.get("event_points") or 0)
            except ValueError:
                pts = 0.0
            if pts <= 0:
                continue
            dt = parse_date(
                row.get("event_year_and_month") or "",
                row.get("event_year") or "",
                row.get("event_month") or "",
            )
            if dt is None:
                continue
            events_by_dancer[did].append({"div": div, "pts": pts, "ym": dt})
            if div not in first_pts[did] or dt < first_pts[did][div]:
                first_pts[did][div] = dt

    for evs in events_by_dancer.values():
        evs.sort(key=lambda e: ym_ord(*e["ym"]))

    return dominate, first_pts, events_by_dancer


def months_to_threshold(
    first_pts: dict,
    events: list[dict],
    target: float,
    *,
    cumulative: bool,
    window: int = 36,
) -> int | None:
    if "Advanced" not in first_pts:
        return None
    t0 = first_pts["Advanced"]
    total = 0.0
    for e in events:
        if e["div"] != "Advanced" or e["ym"] < t0:
            continue
        if cumulative:
            total += e["pts"]
            if total >= target:
                return months_between(t0, e["ym"])
        elif rolling_sum(events, "Advanced", e["ym"], window) >= target:
            return months_between(t0, e["ym"])
    return None


def summarize(label: str, values: list[float]) -> None:
    if not values:
        print(f"  {label}: n=0")
        return
    qs = statistics.quantiles(values, n=4) if len(values) >= 4 else [values[0]] * 3
    print(
        f"  {label}: n={len(values)}, med={statistics.median(values):.1f}, "
        f"p25={qs[0]:.1f}, p75={qs[2]:.1f}"
    )


def main() -> None:
    _, first_pts, events_by_dancer = load_data()

    # Cohorts: dancers who reached All-Stars, by year of first AS points
    cohorts = {
        "2015-19": range(2015, 2020),
        "2021-22": (2021, 2022),
        "2023-25": range(2023, 2026),
    }

    print("=== 1. Время до порога в Advanced (от первых Adv-поинтов) ===")
    print("Сопоставимые когорты: только те, у кого есть All-Stars\n")

    for clabel, years in cohorts.items():
        to_45_roll, to_45_cum, to_60_cum, to_as, idle_45, idle_60 = [], [], [], [], [], []
        for did, fp in first_pts.items():
            if "Advanced" not in fp or "All-Stars" not in fp or fp["All-Stars"][0] not in years:
                continue
            if fp["All-Stars"] <= fp["Advanced"]:
                continue
            evs = events_by_dancer[did]
            m_as = months_between(fp["Advanced"], fp["All-Stars"])
            m45r = months_to_threshold(fp, evs, 45, cumulative=False)
            m45c = months_to_threshold(fp, evs, 45, cumulative=True)
            m60c = months_to_threshold(fp, evs, 60, cumulative=True)
            to_as.append(m_as)
            if m45r is not None:
                to_45_roll.append(m45r)
                idle_45.append(m_as - m45r)
            if m45c is not None:
                to_45_cum.append(m45c)
            if m60c is not None:
                to_60_cum.append(m60c)
                idle_60.append(m_as - m60c)

        print(f"[{clabel}]")
        summarize("first Adv → first AS", to_as)
        summarize("до 45 (36mo rolling)", to_45_roll)
        summarize("до 45 (cumulative)", to_45_cum)
        summarize("до 60 (cumulative)", to_60_cum)
        summarize("«холостой» ход после 45 roll (AS − 45)", idle_45)
        summarize("«холостой» ход после 60 cum (AS − 60)", idle_60)
        print()

    print("=== 2. Сравнение эпох (медианы, когорта с All-Stars) ===")
    era_specs = [
        ("2015-19 / порог ~45", range(2015, 2020), 45, "roll"),
        ("2015-19 / 45 cumulative", range(2015, 2020), 45, "cum"),
        ("2023-25 / 60 cumulative", range(2023, 2026), 60, "cum"),
    ]
    for label, years, target, mode in era_specs:
        vals = []
        idle = []
        for did, fp in first_pts.items():
            if "Advanced" not in fp or "All-Stars" not in fp or fp["All-Stars"][0] not in years:
                continue
            if fp["All-Stars"] <= fp["Advanced"]:
                continue
            evs = events_by_dancer[did]
            m_thr = months_to_threshold(
                fp, evs, target, cumulative=(mode == "cum"), window=36
            )
            if m_thr is None:
                continue
            m_as = months_between(fp["Advanced"], fp["All-Stars"])
            vals.append(m_thr)
            idle.append(m_as - m_thr)
        print(label)
        summarize("  до порога", vals)
        summarize("  холостой ход до AS", idle)


if __name__ == "__main__":
    main()
