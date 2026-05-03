import re
from pathlib import Path


FILE = Path("/Users/ania/.cursor/wsdc-analytics-repo/article_3year_rule.html")
text = FILE.read_text(encoding="utf-8")


def transform_block(content: str, summary: str, table_class: str) -> str:
    pattern = (
        r'(<details class="risk-disclosure">\s*<summary>'
        + re.escape(summary)
        + r'</summary>\s*<div class="table-scroll">\s*<table class="risk-table)'
        + r'(">\s*<thead>\s*<tr>)'
        + r'(.*?)'
        + r'(</tr>\s*</thead>\s*<tbody>)'
        + r'(.*?)'
        + r'(</tbody>\s*</table>\s*</div>\s*</details>)'
    )
    m = re.search(pattern, content, flags=re.S)
    if not m:
        return content

    open_a, open_b, header_row, mid, rows_block, end = m.groups()

    # Force class on the target table
    new_open_a = f'{open_a} {table_class}'

    # Header: keep #, Dancer, Last Year
    header_cells = re.findall(r"<th>.*?</th>", header_row, flags=re.S)
    if len(header_cells) >= 5:
        new_header = "".join([header_cells[0], header_cells[1], header_cells[4]])
    else:
        new_header = header_row

    # Rows: keep td 1,2,5
    new_rows = []
    for row in re.findall(r"<tr>.*?</tr>", rows_block, flags=re.S):
        tds = re.findall(r"<td>.*?</td>", row, flags=re.S)
        if len(tds) >= 5:
            new_rows.append(f"<tr>{tds[0]}{tds[1]}{tds[4]}</tr>")
        else:
            new_rows.append(row)
    new_rows_block = "\n".join(new_rows)

    replacement = f"{new_open_a}{open_b}{new_header}{mid}{new_rows_block}{end}"
    return content[: m.start()] + replacement + content[m.end() :]


text = transform_block(text, "Список: 98 человек", "year-only-table")
text = transform_block(text, "Список: 146 человек", "year-only-table")

# Ensure the 29-people status table has explicit class
text = re.sub(
    r'(<summary>Список: 29 человек</summary>\s*<div class="table-scroll">\s*<table class="risk-table)(?=">)',
    r"\1 status-only-table",
    text,
    flags=re.S,
)

FILE.write_text(text, encoding="utf-8")

