#!/usr/bin/env python3
"""Extract yellow-highlighted text from WSDC rules PDF using PyMuPDF."""
import fitz
from pathlib import Path

PDF_PATH = Path(__file__).resolve().parent.parent / "static" / "rules" / "2019-WSDC-Registry-Event-Rules-Combined.pdf"


def is_yellow(color):
    """Check if color is yellow (RGB ~1,1,0 or similar)."""
    if color is None:
        return False
    if isinstance(color, (int, float)):
        return False
    # fitz colors: (r, g, b) each 0-1, or single value for gray
    if hasattr(color, "__len__") and len(color) >= 3:
        r, g, b = float(color[0]), float(color[1]), float(color[2])
        # Yellow: high R and G, low B
        return r > 0.8 and g > 0.8 and b < 0.3
    return False


def main():
    doc = fitz.open(str(PDF_PATH))
    print(f"=== {PDF_PATH.name} ({len(doc)} pages) ===\n")

    for page_num in range(len(doc)):
        page = doc[page_num]
        highlights = []

        # 1. Check annotations
        for annot in page.annots():
            if annot.type[0] == 8:  # Highlight
                rects = annot.vertices
                if rects:
                    quad = fitz.Quad(rects[:4])
                    rect = quad.rect
                    text = page.get_text(clip=rect)
                    if text.strip():
                        color = annot.colors.get("stroke") or annot.colors.get("fill")
                        highlights.append(("annotation", text.strip(), color))

        # 2. Check drawings for yellow filled rectangles
        try:
            drawings = page.get_drawings()
            for d in drawings:
                fill = d.get("fill")
                if fill and is_yellow(fill):
                    rect = fitz.Rect(d["rect"])
                    text = page.get_text(clip=rect)
                    if text.strip() and len(text.strip()) > 3:
                        highlights.append(("drawing", text.strip(), fill))
        except Exception as e:
            pass

        # 3. Try get_text("dict") and look for span colors
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line.get("spans", []):
                    color = span.get("color")
                    if color is not None:
                        # color is int 0xRRGGBB
                        r = ((color >> 16) & 0xFF) / 255
                        g = ((color >> 8) & 0xFF) / 255
                        b = (color & 0xFF) / 255
                        if is_yellow((r, g, b)):
                            highlights.append(("span_color", span.get("text", ""), (r, g, b)))
                    # Check for background in font
                    if "flags" in span:
                        pass

        if highlights:
            print(f"--- Page {page_num + 1} ---")
            for src, text, color in highlights:
                # Dedupe and clean
                t = " ".join(text.split())[:200]
                if t:
                    print(f"  [{src}] {t}...")
            print()

    doc.close()


if __name__ == "__main__":
    main()
