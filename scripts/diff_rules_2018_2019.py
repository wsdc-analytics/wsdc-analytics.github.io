#!/usr/bin/env python3
"""Extract text from 2018 PDFs and compare with 2019 to identify key changes."""
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "projects" / "tableau" / "My-Tableau-Projects" / "WSDC" / "WSDC Rules Analysis" / "rules_extracted" / "Правила WSDC"
RULES_TEXT = Path(__file__).resolve().parent.parent.parent / "projects" / "tableau" / "My-Tableau-Projects" / "WSDC" / "WSDC Rules Analysis" / "rules_text"


def extract_pdf_text(pdf_path: Path) -> str:
    from pypdf import PdfReader
    reader = PdfReader(str(pdf_path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def main():
    # Extract 2018 to local temp
    out_dir = Path(__file__).resolve().parent.parent / "temp_rules_extract"
    out_dir.mkdir(exist_ok=True)
    for name in ["2018.1A-Registry-Event-Rules-and-Requirements.pdf", "2018.1B-WSDC-Points-Registry-Rules-v2018.1B.pdf"]:
        p = SOURCE_DIR / name
        if p.exists():
            text = extract_pdf_text(p)
            out = out_dir / name.replace(".pdf", ".txt")
            out.write_text(text, encoding="utf-8")
            print(f"Extracted: {name} -> {len(text)} chars")

    # Read 2019
    p19_er = RULES_TEXT / "2019" / "2019.1A-Registry-Event-Rules_Final.txt"
    p19_pr = RULES_TEXT / "2019" / "2019.1A-WSDC-Points-Registry-Rules_Final.txt"
    if p19_er.exists():
        t = p19_er.read_text(encoding="utf-8")
        print(f"2019 Event Rules: {len(t)} chars")
    if p19_pr.exists():
        t = p19_pr.read_text(encoding="utf-8")
        # Key phrase to find
        if "Effective July 1, 2019" in t:
            print("FOUND: 'Effective July 1, 2019, the number of rounds for tiers will be mandatory.'")
        if "mandatory" in t:
            idx = t.find("mandatory")
            print(f"Context: ...{t[max(0,idx-80):idx+80]}...")


if __name__ == "__main__":
    main()
