# Board Questions Intake Concept (4+1)

Working process for the WSDC analytics committee when Board members submit data or analysis asks.

**Tone:** soft partner. Classify by *data layer and dependencies*, not by blaming the registry.

**Related:** [Analytics brief · 1 Sep 2026](../2026-09-01/README.md) (Gaps A–D, three populations). Published example of C1 work: [Faster Division Transitions](https://wsdc-analytics.github.io/article_division_transition_time_en.html).

---

## Why this exists

Board asks arrive mixed: some are answerable from the public Points Registry today; some need Score Report hygiene already sitting in WSDC’s contour; some need new collection design; some are community landscape outside the registry; some are governance/scope (how the committee should work), not datasets.

Without a shared frame, every ask looks like “more analysis” and scope expands. Kay’s constraint stands: **use this committee to make current work better, not to bite off new product fronts.**

---

## Three populations (do not mix)

Same frame as the Sep brief. Every atomic answer must name which population it uses.

| Population | Meaning | Typical source |
|------------|---------|----------------|
| **Community** | Broader WCS social/learning world | Outside registry (C4) or proxy estimates |
| **Entry** | Everyone registered in WSDC J&J at an event | Score Report Competitors List (§2.3 already requires it) |
| **Scored** | People with awarded registry points / Competitor ID after a point | Public Points Registry |

Competitor ID only after a point — Registry Event Rules 2026.1B §3.2.2c. Public analytics default to **Scored** unless Entry lists are usable.

---

## Category model (4+1)

| ID | Name | Meaning | Typical sources |
|----|------|---------|-----------------|
| **C1** | Answerable now | Deliver from cleaned/public layer with clear disclaimers | Points Registry results, event catalog/calendar, published analytics |
| **C2** | After source hygiene | Data already exists in WSDC contour in raw/private form; need aliases, join, retention, schema | Score Report archive (Info Summary, Competitors List, Dual Roles), Drive sheets, Event Update free-text cleanup |
| **C3** | Needs WSDC collection design | Inside WSDC is the right place, but no usable stream yet (or policy/format undecided) | Durable list retention + ID policy, voluntary home city, certified-judge feeds for AJP %, New Event Application analytics fields, calendar pre-event confirmation |
| **C4** | Outside WSDC | Community / non-registry landscape | Workshops, local socials, non-WSDC weekends, local attendance, polls |
| **C5** | Governance / scope | Strategy, priorities, product/ops ownership — not “another dataset” | Committee mandate, website feature calls, merge/delete policy, listing fee models |

### Link to Gaps A–D (Sep brief)

| Gap | Rough map |
|-----|-----------|
| A · Identity | C2–C3 (ID before first point; join lists) |
| B · Coverage | C2–C3 (Entry lists retained and joinable) |
| C · Data quality / geo | C2 (free-text Event Update / Score Report location drift) |
| D · Landscape / calendar | C2–C3 (forward calendar signal); C4 for non-registry events |

---

## Migration

Categories are **not permanent labels on topics**. They move when enablements land.

```
C3 ──schema / retention / policy──► C2 ──pipeline join / aliases──► C1
C4 stays C4 until a durable community-collection program exists
C5 is escalated to Board/ops; data work does not “solve” it
```

**Example:** Competitors List today → mostly C3 (usable stream unclear) or C2 (archive exists, not joined). After schema + central retention + aliases → C2. After join into analytics pipeline → C1 for Entry-based asks.

Reclassify atomic rows in [MATRIX.md](MATRIX.md) when an enablement ships. Do not leave stale “blocked forever” labels.

---

## Workflow

1. **Intake** — asker, raw text, must-have vs nice-to-have, date.
2. **Quote** — keep the Board wording (full ask or the exact bullet/clause). Do not replace the ask with a paraphrase in the matrix.
3. **Decompose** — one Board message often becomes several *atomic* rows (different categories), **same quote** when layers differ.
4. **Classify** each atomic → C1–C5 + population (Community / Entry / Scored) + **Depth** (`full` / `partial` / `blocked` / `scope`).
5. **Respond**
   - **C1 `full`:** analyze and deliver; take into work first.
   - **C1 `partial`:** deliver only the named scope (usually Scored) against the **same quote**; point to the C2/C3 twin for the full ask.
   - **C2:** do not stop at “need data” — name the **concrete enabling work** that unlocks a full answer (e.g. Competitors List join, Score Report prelims field, aliases).
   - **C3:** design the collection/policy stream inside WSDC.
   - **C4:** community collection + verification design; not registry-grade.
   - **C5:** return to Board with scope recommendation (Kay filter).
6. **Track** — status, blocker, next enabling step.
7. **Reclassify** after enablement (C2→C1 when unlock ships).

**C1 review order:** list `full` atoms first, then `partial`.

### Decision shortcuts

| Signal | Prefer |
|--------|--------|
| Answerable from points + event dates alone, ask matches that layer | C1 `full` |
| Ask is broader (Entry/community/attendance) but scored slice is useful now | C1 `partial` + C2 twin with concrete Enabling |
| Answer needs full starting lists, home city, judges panel, or unjoined Score Report fields | C2 if files/sheets exist; else C3 |
| Workshops / local socials / non-WSDC weekends / polls | C4 |
| “Should the website…?”, “Should the committee build…?”, fee models, merge policy without contestant request | C5 |
| Forecast / prediction | C1 `partial` (scored scenario) unless Entry series exists |

---

## Scope rule (Kay)

The committee **supports current Board mission, strategy, and infrastructure work**. Default when an ask expands product surface (new public hubs, coding verification systems, revenue experiments): classify **C5**, propose *data support* to an owning Board/ops track, and avoid taking delivery ownership unless Board mandates it.

---

## Artifacts in this folder

| File | Audience |
|------|----------|
| [CONCEPT.md](CONCEPT.md) | Committee — taxonomy + workflow |
| [MATRIX.md](MATRIX.md) | Committee — Board source numbering + atomic splits (`a`/`-E`); full classification |
| [slides_en.html](slides_en.html) | Board-facing brief (unlisted) |
| [README.md](README.md) | Share notes, noindex |

Do not commit PII or Score Report workbooks. Refer to *source types* only.
