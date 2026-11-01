# WSDC Registry Event — Competitor List export (draft)

**Status:** draft for analytics committee / ops discussion. Not an official WSDC form until adopted.

**File:** [WSDC_Registry_Event_Competitor_List_v0.1.xlsx](WSDC_Registry_Event_Competitor_List_v0.1.xlsx)

## Intent

Propose a **machine-export schema** that scoring companies can produce instead of (or as the successor to) the current Score Report «Competitors List» sheet.

- Target filler: **scoring systems**, not organizers typing hundreds of names.
- Goal: retain Entry population centrally and join to C1 (Points Registry) where `wsdc_competitor_id` exists.
- Open in Excel, or **File → Import** into Google Sheets (dropdowns may need re-binding to the `Lookups` sheet after import).

## Sheets

| Sheet | Role |
|-------|------|
| `README` | How to use + identity rules |
| `Event_Header` | One row per event edition (catalog id / name / year / dates / country) |
| `Competitors` | One row = person × role × division × contest_type |
| `Lookups` | Controlled lists for dropdowns |
| `Vendor_Mapping` | Typical scoring-system field → column map |

## Rebuild

```bash
/tmp/.venv-xlsx/bin/python meetings/board-questions-intake/competitor-list-export/_build_template.py
```

(or any env with `openpyxl`)

## Related

- Intake concept: [../CONCEPT.md](../CONCEPT.md) (Entry / C2 → C1)
- Matrix enabling: Competitors List retain + schema + ID join ([../MATRIX.md](../MATRIX.md))
- Sep 1 brief: Score Report §2.3 already asks for the full registered list
