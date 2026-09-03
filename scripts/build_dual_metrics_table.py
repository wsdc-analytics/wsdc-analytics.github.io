#!/usr/bin/env python3
"""Build dual-metric median table: threshold vs first-to-first by year and era."""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from pathlib import Path

SOURCE = Path("/Users/ania/.cursor/projects/python/wsdc-data-pipeline/data")
RULES_PATH = Path(__file__).resolve().parents[1] / "static/data/rules_advancement_thresholds.json"
MIN_N = 30

TRANSITIONS = [
    ("Novice", "Intermediate"),
    ("Intermediate", "Advanced"),
    ("Advanced", "All-Stars"),
    ("All-Stars", "Champions"),
]

PRE_COVID = frozenset(range(2015, 2020))
POST_COVID = frozenset(range(2024, 2026))
YEARS = list(range(2015, 2026))


def norm_div(value: str) -> str | None:
    v = (value or "").strip()
    if v in {"All Star", "All-Star", "All Stars", "All-Stars"}:
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
    return sum(e["pts"] for e in events if e["div"] == div and lo <= ym_ord(*e["ym"]) <= at)


def threshold_for_year(rules: dict, year: int, division: str) -> dict:
    for epoch in rules.get("epochs", []):
        vf = epoch.get("valid_from")
        vt = epoch.get("valid_to")
        if vf is not None and year < vf:
            continue
        if vt is not None and year > vt:
            continue
        model = epoch.get("model")
        if model in ("allowed_required_36mo", "allowed_required"):
            d = epoch.get("divisions", {}).get(division)
            if d and "allowed" in d:
                return {"allowed": d["allowed"], "required": d.get("required"), "epoch": epoch["id"]}
            if division == "All-Stars" and d and "champions_allowed" in d:
                return {
                    "champions_allowed": d["champions_allowed"],
                    "epoch": epoch["id"],
                }
        if model == "cumulative":
            trans = epoch.get("transitions", {})
            if division in trans:
                p = trans[division]["points"]
                return {"allowed": p, "epoch": epoch["id"], "cumulative": True}
    return {}


def months_to_allowed(
    first_pts: dict,
    events: list[dict],
    from_div: str,
    ref_year: int,
    rules: dict,
) -> int | None:
    if from_div not in first_pts:
        return None
    t0 = first_pts[from_div]
    th = threshold_for_year(rules, ref_year, from_div)

    if from_div == "All-Stars":
        ca = (th or {}).get("champions_allowed") or {}
        as_target = float(ca.get("or_all_star_points", 150))
        ch_target = float(ca.get("champions_points", 1))
        as_tot = ch_tot = 0.0
        for e in events:
            if e["ym"] < t0:
                continue
            if e["div"] == "All-Stars":
                as_tot += e["pts"]
                if as_tot >= as_target:
                    return months_between(t0, e["ym"])
            if e["div"] == "Champions":
                ch_tot += e["pts"]
                if ch_tot >= ch_target:
                    return months_between(t0, e["ym"])
        return None

    if not th or th.get("allowed") is None:
        return None
    target = float(th["allowed"])
    epoch = th.get("epoch", "")
    use_rolling = from_div == "Advanced" and epoch in ("2018_2020", "2021_2022")
    total = 0.0
    for e in events:
        if e["div"] != from_div or e["ym"] < t0:
            continue
        if use_rolling:
            if rolling_sum(events, from_div, e["ym"], 36) >= target:
                return months_between(t0, e["ym"])
        else:
            total += e["pts"]
            if total >= target:
                return months_between(t0, e["ym"])
    return None


def dist_stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "min": None, "median": None, "max": None}
    return {
        "n": len(values),
        "min": float(min(values)),
        "median": float(statistics.median(values)),
        "max": float(max(values)),
    }


def fmt_dist(stats: dict) -> str:
    """median [min–max]; * if 10 <= n < MIN_N."""
    if stats["n"] == 0 or stats["median"] is None:
        return "—"
    med, lo, hi = stats["median"], stats["min"], stats["max"]
    text = f"{med:.1f} [{lo:.0f}–{hi:.0f}]"
    if stats["n"] < MIN_N:
        return f"{text}*" if stats["n"] >= 10 else "—"
    return text


def fmt_val(stats: dict, field: str) -> str:
    if stats["n"] == 0 or stats.get(field) is None:
        return "—"
    v = stats[field]
    text = f"{v:.1f}"
    if stats["n"] < MIN_N:
        return f"{text}*" if stats["n"] >= 10 else "—"
    return text


TABLE_HEADER = (
    "| Год / период | n₁ | M1 min | M1 med | M1 max | n₂ | M2 min | M2 med | M2 max |\n"
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|"
)


def format_table_row(label: str, b: dict) -> str:
    thr, ff = dist_stats(b["thr"]), dist_stats(b["ff"])
    return (
        f"| {label} | {thr['n']} | {fmt_val(thr, 'min')} | {fmt_val(thr, 'median')} | "
        f"{fmt_val(thr, 'max')} | {ff['n']} | {fmt_val(ff, 'min')} | {fmt_val(ff, 'median')} | "
        f"{fmt_val(ff, 'max')} |"
    )


def load():
    rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    dominate: dict[str, str] = {}
    with (SOURCE / "dancer_role_info.csv").open(encoding="utf-8-sig", newline="") as f:
        import csv

        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            role = (row.get("dominate_role") or "").strip().title()
            if did and role in ("Leader", "Follower"):
                dominate[did] = role

    first_pts: dict[str, dict[str, tuple[int, int]]] = defaultdict(dict)
    events_by_dancer: dict[str, list[dict]] = defaultdict(list)
    import csv

    with (SOURCE / "dancers_results_info.csv").open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            did = (row.get("dancer_id") or "").strip()
            if did not in dominate:
                continue
            div = norm_div(row.get("event_competition") or "")
            if not div:
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
            if not dt:
                continue
            events_by_dancer[did].append({"div": div, "pts": pts, "ym": dt})
            if div not in first_pts[did] or dt < first_pts[did][div]:
                first_pts[did][div] = dt

    for evs in events_by_dancer.values():
        evs.sort(key=lambda e: ym_ord(*e["ym"]))
    return rules, dominate, first_pts, events_by_dancer


def collect(rules, first_pts, events_by_dancer):
    by_year: dict[tuple, dict] = {}
    by_period: dict[tuple, dict] = {}

    def bucket(store, key, m_thr, m_ff):
        if key not in store:
            store[key] = {"thr": [], "ff": []}
        if m_thr is not None:
            store[key]["thr"].append(float(m_thr))
        store[key]["ff"].append(float(m_ff))

    for from_div, to_div in TRANSITIONS:
        for did, fp in first_pts.items():
            if from_div not in fp or to_div not in fp:
                continue
            if fp[to_div] <= fp[from_div]:
                continue
            ty = fp[to_div][0]
            if ty not in YEARS:
                continue
            evs = events_by_dancer[did]
            m_ff = months_between(fp[from_div], fp[to_div])
            m_thr = months_to_allowed(fp, evs, from_div, ty, rules)
            key = (from_div, to_div)
            bucket(by_year, (key, ty), m_thr, m_ff)
            if ty in PRE_COVID:
                bucket(by_period, (key, "2015–2019"), m_thr, m_ff)
            if ty in POST_COVID:
                bucket(by_period, (key, "2024–2025"), m_thr, m_ff)

    return by_year, by_period


def build_rows(by_year, by_period):
    rows = []
    for from_div, to_div in TRANSITIONS:
        for y in YEARS:
            b = by_year.get(((from_div, to_div), y), {"thr": [], "ff": []})
            thr = dist_stats(b["thr"])
            ff = dist_stats(b["ff"])
            rows.append(
                {
                    "from_division": from_div,
                    "to_division": to_div,
                    "period_type": "year",
                    "period": str(y),
                    "n_first_to_first": ff["n"],
                    "n_to_threshold": thr["n"],
                    "months_to_threshold": thr,
                    "months_first_to_first": ff,
                }
            )
        for period in ("2015–2019", "2024–2025"):
            b = by_period.get(((from_div, to_div), period), {"thr": [], "ff": []})
            thr = dist_stats(b["thr"])
            ff = dist_stats(b["ff"])
            rows.append(
                {
                    "from_division": from_div,
                    "to_division": to_div,
                    "period_type": "era",
                    "period": period,
                    "n_first_to_first": ff["n"],
                    "n_to_threshold": thr["n"],
                    "months_to_threshold": thr,
                    "months_first_to_first": ff,
                }
            )
    return rows


def main() -> None:
    rules, _, first_pts, events_by_dancer = load()
    by_year, by_period = collect(rules, first_pts, events_by_dancer)
    out_path = Path(__file__).resolve().parents[1] / "static/data/dual_metrics_by_year.json"
    payload = {
        "description": "Dual metrics (min/median/max months) by year/era; cohort = year of first points in D+1",
        "min_n_display": MIN_N,
        "pre_covid_years": sorted(PRE_COVID),
        "post_covid_years": sorted(POST_COVID),
        "rows": build_rows(by_year, by_period),
    }
    md_path = out_path.parent / "dual_metrics_tables.md"
    md_parts = [
        "# Две метрики по переходам (All, dominate role)\n",
        "Когорта: **год первых поинтов в D+1**. "
        "M1 — до allowed; M2 — до первых поинтов в D+1. "
        f"n₁ — до порога, n₂ — до D+1. «—» если n < 10; * если 10 ≤ n < {MIN_N}.\n",
    ]

    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Wrote {md_path}\n")

    for from_div, to_div in TRANSITIONS:
        transition = f"{from_div} → {to_div}"
        md_parts.append(f"\n## {transition}\n\n{TABLE_HEADER}\n")
        print(f"### {transition}\n")
        print(TABLE_HEADER)
        for y in YEARS:
            b = by_year.get(((from_div, to_div), y), {"thr": [], "ff": []})
            row = format_table_row(str(y), b)
            print(row)
            md_parts.append(row + "\n")
        for period in ("2015–2019", "2024–2025"):
            b = by_period.get(((from_div, to_div), period), {"thr": [], "ff": []})
            row = format_table_row(f"**{period}**", b)
            print(row)
            md_parts.append(row + "\n")
        print()

    md_path.write_text("".join(md_parts), encoding="utf-8")


if __name__ == "__main__":
    main()
