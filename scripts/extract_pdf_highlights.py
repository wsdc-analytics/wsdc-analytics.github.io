#!/usr/bin/env python3
"""Extract highlight annotations from WSDC rules PDFs to identify key changes."""
from pathlib import Path

SOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "projects" / "tableau" / "My-Tableau-Projects" / "WSDC" / "WSDC Rules Analysis" / "rules_extracted" / "Правила WSDC"
RULES_DIR = Path(__file__).resolve().parent.parent / "static" / "rules"


def inspect_pdf_annotations(pdf_path: Path) -> None:
    """List all annotations in PDF."""
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    print(f"\n=== {pdf_path.name} ({len(reader.pages)} pages) ===\n")

    for i, page in enumerate(reader.pages):
        if "/Annots" not in page:
            continue
        annots = page["/Annots"]
        if isinstance(annots, list):
            for a in annots:
                try:
                    obj = a.get_object()
                    subtype = obj.get("/Subtype", "?")
                    rect = obj.get("/Rect", [])
                    if subtype == "/Highlight":
                        quad = obj.get("/QuadPoints", [])
                        contents = obj.get("/Contents", "")
                        print(f"  Page {i+1}: {subtype} rect={rect[:4] if rect else 'N/A'} contents={contents[:80] if contents else 'N/A'}")
                    else:
                        print(f"  Page {i+1}: {subtype}")
                except Exception as e:
                    print(f"  Page {i+1}: Error {e}")


if __name__ == "__main__":
    # Check 2019 Event Rules (where WSDC typically marks changes)
    for name in [
        "2019.1A-Registry-Event-Rules_Final.pdf",
        "2019.1A-WSDC-Points-Registry-Rules_Final.pdf",
    ]:
        p = SOURCE_DIR / name
        if p.exists():
            inspect_pdf_annotations(p)
        else:
            p2 = RULES_DIR / name
            if p2.exists():
                inspect_pdf_annotations(p2)
