#!/usr/bin/env python3
"""Merge Points Registry Rules + Event Rules into combined PDFs for 2015, 2018, 2019, 2020.

For 2020: splits addendum pages into separate 2020-May-Addendum.pdf;
main combined PDF contains only base rules (no addendum).

Requires: Place Points Registry PDFs in static/rules/ (WSDC removed them from their site):
  - 2018.1A-WSDC-Points-Registry-Rules-v2018.1A.pdf
  - 2019.1A-WSDC-Points-Registry-Rules_Final.pdf
  - 2020.1B-WSDC-Points-Registry-Rules_with-addendum-5-14-2021.pdf

Run: .venv-pdf/bin/python scripts/merge_rules_pdfs.py
"""
from pathlib import Path

from pypdf import PdfReader, PdfWriter

RULES_DIR = Path(__file__).resolve().parent.parent / "static" / "rules"

# Pages for 2020 addendum split:
# Points: 6 pages total, addendum on pages 5-6 (0-indexed: 4-5)
# Event: 10 pages total, addendum on pages 9-10 (0-indexed: 8-9)
POINTS_ADDENDUM_PAGES = (4, 5)  # 0-indexed, inclusive
EVENT_ADDENDUM_PAGES = (8, 9)

PAIRS = [
    {
        "year": "2015",
        "points_local": "WSDC-Points-Registry-Document-7-1-2015.pdf",
        "event_local": "WSDC_Registry_Event_Requirements.pdf",
        "output": "2015-WSDC-Registry-Event-Rules-Combined.pdf",
    },
    {
        "year": "2018",
        "points_local": "2018.1B-WSDC-Points-Registry-Rules-v2018.1B.pdf",  # also accept 2018.1A
        "points_fallback": "2018.1A-WSDC-Points-Registry-Rules-v2018.1A.pdf",
        "event_local": "2018.1A-Registry-Event-Rules-and-Requirements.pdf",
        "output": "2018-WSDC-Registry-Event-Rules-Combined.pdf",
    },
    {
        "year": "2019",
        "points_local": "2019.1A-WSDC-Points-Registry-Rules_Final.pdf",
        "event_local": "2019.1A-Registry-Event-Rules_Final.pdf",
        "output": "2019-WSDC-Registry-Event-Rules-Combined.pdf",
    },
    {
        "year": "2020",
        "points_local": "2020.1B-WSDC-Points-Registry-Rules_with-addendum-5-14-2021.pdf",
        "event_local": "2020.1B-Registry-Event-Rules_with-addendum-5-14-2021.pdf",
        "output": "2020-WSDC-Registry-Event-Rules-Combined.pdf",
        "addendum_output": "2020-May-Addendum.pdf",
    },
]

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "projects" / "tableau" / "My-Tableau-Projects" / "WSDC" / "WSDC Rules Analysis" / "rules_extracted" / "Правила WSDC"


def process_2020_with_addendum_split(points_path: Path, event_path: Path) -> None:
    """Split 2020: base rules → combined PDF, addendum pages → separate PDF."""
    points_reader = PdfReader(str(points_path))
    event_reader = PdfReader(str(event_path))

    # Base: Points pages 0..3, Event pages 0..7 (exclude addendum)
    base_writer = PdfWriter()
    for i in range(POINTS_ADDENDUM_PAGES[0]):
        base_writer.add_page(points_reader.pages[i])
    for i in range(EVENT_ADDENDUM_PAGES[0]):
        base_writer.add_page(event_reader.pages[i])
    base_path = RULES_DIR / "2020-WSDC-Registry-Event-Rules-Combined.pdf"
    with open(base_path, "wb") as f:
        base_writer.write(f)
    base_writer.close()
    print(f"  -> {base_path.name} (base only, no addendum)")

    # Addendum: только одна копия (Points и Event содержат одинаковый addendum)
    add_writer = PdfWriter()
    for i in range(EVENT_ADDENDUM_PAGES[0], EVENT_ADDENDUM_PAGES[1] + 1):
        add_writer.add_page(event_reader.pages[i])
    add_path = RULES_DIR / "2020-May-Addendum.pdf"
    with open(add_path, "wb") as f:
        add_writer.write(f)
    add_writer.close()
    print(f"  -> {add_path.name} (addendum pages)")


def main():
    for p in PAIRS:
        print(f"Processing {p['year']}...")
        points_path = RULES_DIR / p["points_local"]
        if not points_path.exists() and p.get("points_fallback"):
            points_path = RULES_DIR / p["points_fallback"]
        if not points_path.exists() and SOURCE_DIR.exists():
            # Use source from WSDC Rules Analysis rules_extracted (no copy needed)
            src = SOURCE_DIR / p["points_local"]
            if src.exists():
                points_path = src
                print(f"  Using {p['points_local']} from rules_extracted")
            elif p.get("points_fallback") and (SOURCE_DIR / p["points_fallback"]).exists():
                points_path = SOURCE_DIR / p["points_fallback"]
                print(f"  Using {p['points_fallback']} from rules_extracted")
        if not points_path.exists():
            print(f"  SKIP: Points Registry not found in static/rules/ or rules_extracted.")
            continue
        event_path = RULES_DIR / p["event_local"]
        if not event_path.exists():
            raise FileNotFoundError(f"Event rules not found: {event_path}")

        if p["year"] == "2020" and p.get("addendum_output"):
            process_2020_with_addendum_split(points_path, event_path)
            continue

        writer = PdfWriter()
        writer.append(str(points_path))  # Points Registry first (for competitors)
        writer.append(str(event_path))   # Event Rules second (for organizers)
        out_path = RULES_DIR / p["output"]
        with open(out_path, "wb") as f:
            writer.write(f)
        writer.close()
        print(f"  -> {out_path.name}")


if __name__ == "__main__":
    main()
