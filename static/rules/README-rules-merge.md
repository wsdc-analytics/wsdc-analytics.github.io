# Объединённые правила 2018–2020

С 2018 по 2020 год WSDC публиковал правила в двух документах:
- **Points Registry Rules** — для участников
- **Registry Event Rules** — для организаторов

Для удобства мы объединяем их в один PDF.

## Источник PDF

Points Registry берётся из проекта WSDC Rules Analysis:
`rules_extracted/Правила WSDC/` — там есть все нужные документы (2018.1B, 2019.1A, 2020.1B).

Event Rules уже есть в `static/rules/`.

## Как создать объединённые PDF

```bash
.venv-pdf/bin/python scripts/merge_rules_pdfs.py
```

Скрипт автоматически находит Points Registry в `rules_extracted/Правила WSDC/` (если репозиторий WSDC Rules Analysis находится рядом) и создаёт:
- `2018-WSDC-Registry-Event-Rules-Combined.pdf`
- `2019-WSDC-Registry-Event-Rules-Combined.pdf`
- `2020-WSDC-Registry-Event-Rules-Combined.pdf` — только базовая редакция (без addendum)
- `2020-May-Addendum.pdf` — отдельный документ со страницами addendum
