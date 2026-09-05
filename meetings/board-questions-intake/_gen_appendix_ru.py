#!/usr/bin/env python3
"""Generate fully Russian appendix_ru.html from MATRIX.md + RU translations."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

BASE = Path(__file__).resolve().parent

# id -> (quote_ru, comment_ru)
RU: dict[str, tuple[str, str]] = {
    "JT-1": (
        "Длительность для каждого конкурента от момента, когда он впервые получает поинт в дивизионе, до момента, когда он «закончен» в этом дивизионе",
        "Tigges №1. Перешедшие + цензурированные отдельно; переиспользовать статью / dwell.",
    ),
    "JT-2": (
        "Длительность для каждого конкурента от последнего поинта в нижнем дивизионе до первого поинта в более высоком",
        "Tigges №2. Метрика last_to_first; переиспользовать.",
    ),
    "JT-3": (
        "Длительность от достижения порога «may» move up до «must» move up — и сколько оставались, пока не набрали 25%, 50% и 75% дополнительных поинтов до must",
        "Tigges №3. Время до allowed / required; переиспользовать.",
    ),
    "JT-4": (
        "Сколько ивентов в каждом году у каждого конкурента дали поинт на любом уровне (+ корзины 12+ / 6–12 / 3–6 / 0–1)",
        "Tigges №4. Только ивенты с поинтом — формулировка уже исключает attendance.",
    ),
    "JT-6": (
        "Сколько людей могли бы «спуститься», ЕСЛИ разрешить «дисконтировать» поинты старше 10 лет (или 8 / 5 лет)",
        "Tigges №6 — аналитика. Политическое решение = JT-6b (C5).",
    ),
    "JT-8": (
        "У нас есть xx лет результатов ивентов: перечень по каждому ивенту и году — растут, сжимаются, стабильны… а если сжимаются — есть ли рядом новые ивенты в регионе",
        "Tigges №8. Scored-размер YOY + соседние новые ивенты; причинность — интерпретация.",
    ),
    "JN-1b": (
        "Общее число людей, которые за 10+ лет дошли до квалификации, чтобы выступать в дивизионе All-Star",
        "Jen №1. Уточнить метрику: допуск в Advanced vs первый поинт All-Star. Переиспользовать путь из статьи.",
    ),
    "JN-1c": (
        "Статистика по текущим чемпионам с 10+ поинтами: сколько они уже чемпионы, сколько шли до дивизиона, среднее число ивентов и выходов в финал в год",
        "Jen №1. Финалы — где в результатах есть место.",
    ),
    "JN-1d": (
        "…а также число чемпионов, которые не получили ни одного поинта после ковида",
        "Jen №1. Фильтр inactivity по Champions.",
    ),
    "JN-2b": (
        "Сколько людей не соревновались (или не получили поинт, если нет регистрационных данных) после ковида — в каких штатах / странах сильнее спад",
        "Jen №2. Цитата допускает прокси по поинтам; отдаём scored inactivity по geo ивента. Entry no-shows = JN-2b-E.",
    ),
    "PL-1a": (
        "Сколько ивентов проводили Champion и/или Invitational (окна 3 / 6 / 9 лет)",
        "Paul №1. Имена номинаций в результатах.",
    ),
    "PL-1c": (
        "Указать, где поинты начислялись людям с менее чем 11 champion-поинтами",
        "Paul №1. Join размещений к карьерным итогам Champion.",
    ),
    "KY-1": (
        "Ближе посмотреть на текущую структуру поинтов и тиров и влияние возможных изменений, особенно на прогрессию большинства танцоров (многие поинты забирает одно и то же небольшое меньшинство)",
        "Kay №1. Упаковать division-transition + концентрацию для инициативы Board. Entry «majority on the floor» = KY-1-E.",
    ),
    "JC-5b": (
        "Есть ли у комитета идеи другой аналитики, полезной для заявок на новые ивенты (New Event Applications)?",
        "Coakley №5. Scored-пакет для поддержки решений (соседние registry-ивенты, scored-размер, региональный YOY). Не Entry attendance (JC-5c).",
    ),
    "YV-1": (
        "Сколько конкурентов в каждом skill level с 2021 по 2026?",
        "Сейчас отвечаем только по Scored (роль×дивизион). Полные «competitors» = Entry → YV-1-E.",
    ),
    "YV-3": (
        "Исходя из данных, какой прогноз числа конкурентов в каждой роли на 2027, 2028, 2029, 2030 и 2031?",
        "Только scored-сценарий / прогноз; 2026 YTD неполный. Entry-прогноз → YV-3-E.",
    ),
    "JN-1a": (
        "Средняя траектория человека, начавшего WCS после ковида, от Novice до All-Star по среднему числу ивентов, которые он посещает (growth-регионы vs Европа vs США) — нужно знать разницу в числе предлагаемых ивентов YOY",
        "Scored-траектория + ивенты-с-поинтом как прокси «посещает»; срез по регионам. Реальный attendance → JN-1a-E. Переиспользовать статью.",
    ),
    "JN-2a": (
        "В каких штатах / странах больше всего зарегистрированных WCS-конкурентов и как рос этот показатель за последние 10 лет",
        "Scored unique по geo ивента (или танцора) — явно подписать, не «registered Entry». Полный Entry → JN-2a-E.",
    ),
    "JN-3a": (
        "Число добавленных ивентов YOY по странам с количеством конкурентов на каждом ивенте",
        "Ивенты YOY = C1; конкуренты = scored unique ID. Entry headcount → JN-3a-E.",
    ),
    "JT-5": (
        "Сколько ивентов каждый год проводят разные дивизионы WSDC и сколько на каждом уровне (за каждую роль) приходится на разные Tiers (например, половина и больше Novice — Tier 3+? Сколько ивентов с Tier 1 All-Star? и т.д.)",
        "Наличие дивизиона + полосы тиров по размеру scored finals. Точные Entry tier headcounts → JT-5-E.",
    ),
    "JT-7": (
        "Карта ивентов… и число конкурентов (например, во Франции 12 ивентов — в среднем 200 или 400 конкурентов?)",
        "Карта + scored unique на edition. Entry-размер ивента → JT-7-E.",
    ),
    "KY-2": (
        "Что можно понять из текущих данных о ландшафте ивентов и capacity — особенно когда речь о лимите новых ивентов при миссии про growth?",
        "Сейчас: ландшафт + scored-нагрузка YOY. Capacity / customer base → KY-2-E; «где нужны» → KY-2c.",
    ),
    "JC-3a": (
        "Проанализировать данные по routine-дивизионам за 15 лет. Показать, на каких ивентах были Classic, Showcase, Sophisticated, Masters и Juniors. … Routines на спаде?",
        "Только age J&J (Sophisticated / Masters / Juniors) и только там, где начислялись поинты — не полная история «проводили» и не гарантированно 15 лет. Classic/Showcase → JC-3b. Уточнить у Jim.",
    ),
    "YV-1-E": (
        "Сколько конкурентов в каждом skill level с 2021 по 2026?",
        "Что сделать: сохранять Competitors List из Score Report; схема + join dancer ID в пайплайн; skill/role в entry-листе. Тогда полные Entry-счёты по skill.",
    ),
    "YV-2a": (
        "Общий размер community и, если возможно, регион?",
        "Что сделать: согласовать с Board определение «community» (только Entry или шире); retention + join Competitors List (как YV-1-E). Регион без списков всё ещё заблокирован.",
    ),
    "YV-2b": (
        "Общий размер community и, если возможно, регион?",
        "Что сделать (scored-регион): Gap C — алиасы event/location; зафиксировать country/state ивента; развести geo ивента vs home танцора. После алиасов возможен частичный scored-by-event-country.",
    ),
    "YV-2b-E": (
        "Общий размер community и, если возможно, регион?",
        "Что сделать: join списков как в YV-1-E плюс чистая Entry-geo (поля списка или verified home).",
    ),
    "YV-3-E": (
        "Исходя из данных, какой прогноз числа конкурентов в каждой роли на 2027, 2028, 2029, 2030 и 2031?",
        "Что сделать: сначала многолетний Entry time series из YV-1-E; только потом сценарий прогноза по Entry.",
    ),
    "KY-1-E": (
        "Ближе посмотреть на текущую структуру поинтов и тиров и влияние возможных изменений, особенно на прогрессию большинства танцоров (многие поинты забирает одно и то же небольшое меньшинство)",
        "Что сделать: join Competitors List, чтобы «majority on the floor» ≠ только scored point-winners.",
    ),
    "KY-2-E": (
        "Что можно понять из текущих данных о ландшафте ивентов и capacity — особенно когда речь о лимите новых ивентов при миссии про growth?",
        "Что сделать: Entry headcount на ивент/год из Competitors List (join + retention) как сигнал capacity.",
    ),
    "JC-6a": (
        "Аудиты базы: были люди без поинтов. Мы это поправили?",
        "Что сделать: ops-экспорт реестра от Paul; чеклист «zero-point record»; ежегодный повтор.",
    ),
    "JN-1a-E": (
        "Средняя траектория человека, начавшего WCS после ковида, от Novice до All-Star по среднему числу ивентов, которые он посещает (growth-регионы vs Европа vs США) — нужно знать разницу в числе предлагаемых ивентов YOY",
        "Что сделать: Competitors List / слой attendance, сджойненный с ID, чтобы «events attended» ≠ ивенты-с-поинтом.",
    ),
    "JN-2a-E": (
        "В каких штатах / странах больше всего зарегистрированных WCS-конкурентов и как рос этот показатель за последние 10 лет",
        "Что сделать: Entry-списки + geo-поля (или home) с retention и join; алиасы Gap C.",
    ),
    "JN-2b-E": (
        "Сколько людей не соревновались (или не получили поинт, если нет регистрационных данных) после ковида — в каких штатах / странах сильнее спад",
        "Что сделать: Entry-списки по ивентам + identity, чтобы no-shows ≠ «нет поинтов».",
    ),
    "JN-3a-E": (
        "Число добавленных ивентов YOY по странам с количеством конкурентов на каждом ивенте",
        "Что сделать: Competitors List на edition, сджойненный с каталогом ивентов (Gap B).",
    ),
    "JN-3b": (
        "По соревнованиям: топ 5–10 крупнейших ивентов в каждой стране/регионе с долей «локальных» конкурентов (напр. French Open: 50% французов в 2023…)",
        "Что сделать: гигиена nationality / home country танцора (Score Report / verification); одной страны ивента недостаточно.",
    ),
    "PL-1b": (
        "Указать те, где были prelims, и те, где shelf judges",
        "Что сделать: вытащить поля prelims / shelf-judge из Score Report (или протоколов) в joinable-таблицу event×year.",
    ),
    "PL-2": (
        "По данным Yvonne и Jennifer, что ~25% ивентов — «problem child»: детальнее влияние этих ~25 на календарь registry, правило 6/15, time-distance и другие метрики управления ивентами",
        "Что сделать: зафиксированный Board-список «problem child» + полные official dates / distance (см. JC-5a).",
    ),
    "JT-5-E": (
        "Сколько ивентов каждый год проводят разные дивизионы WSDC и сколько на каждом уровне (за каждую роль) приходится на разные Tiers (например, половина и больше Novice — Tier 3+? Сколько ивентов с Tier 1 All-Star? и т.д.)",
        "Что сделать: размеры Entry starting-list по division×role (Competitors List) для настоящих WSDC tiers.",
    ),
    "JT-7-E": (
        "Карта ивентов… и число конкурентов (например, во Франции 12 ивентов — в среднем 200 или 400 конкурентов?)",
        "Что сделать: Entry headcount на edition из Competitors List + join к geo.",
    ),
    "KY-2c": (
        "Есть ли способ понять, где нужны ивенты относительно customer base?",
        "Дизайн: поток residence / customer base (добровольный home или политика Entry-geo), пока «где нужны» не отвечаемо.",
    ),
    "JC-3b": (
        "Проанализировать данные по routine-дивизионам за 15 лет. Показать, на каких ивентах были Classic, Showcase, Sophisticated, Masters и Juniors. … Routines на спаде?",
        "Дизайн / поиск источника: Classic и Showcase нет в публичном Points Registry — Score Report contests, программы или другой intake WSDC; иначе C4 web-сбор.",
    ),
    "JC-5a": (
        "Paul уже работает над Excel-экспортом 6/15. Нужно довести кусок official dates.",
        "Дизайн/ops: полнота поля official dates в NEA / экспорте 6/15; комитет может задать validation checks.",
    ),
    "JC-5d": (
        "Какие data points комитет считает нужными для исключений? Запрос Jen: число танцоров в радиусе 100 миль…",
        "Дизайн: захват home city/state (verification или поля списка) + метод радиуса.",
    ),
    "JN-3c": (
        "Популяция WCS в радиусе 100 миль вокруг каждого ивента",
        "Дизайн: поток home coordinates/city; если city из Score Report собирается — после join может уйти в C2.",
    ),
    "PL-3": (
        "Продолжить сбор данных по интеграции сертификации судей WSDC / AJP с марта 2027… смогут ли ивенты набрать 25% по списку судей pre-registration… прогноз на 40% и 50%",
        "Дизайн: поток roster сертифицированных судей + назначенные судьи J&J на ивент.",
    ),
    "JC-1": (
        "Собрать список workshop weekends и specialty day intensive по миру и категоризировать по state/country/region",
        "Программа community-сбора + верификация (владелец TBD).",
    ),
    "JC-2": (
        "Собрать локальные dance events по миру и категоризировать по state/country/region",
        "Та же программа, что JC-1.",
    ),
    "JC-2b": (
        "Нужен процесс верификации раз в месяц или неделю… Нельзя, чтобы люди ехали на ивент, которого уже нет или который сменил место/даты",
        "Советовать схему/каденс; не брать тихо ownership сборки (фильтр Kay).",
    ),
    "JC-3d": (
        "Также можно опросить community: где есть интерес к большим routine-дивизионам и какие стопперы",
        "Дизайн опроса вне реестра.",
    ),
    "JC-4": (
        "Также включить NON-WSDC weekend events или social events",
        "Та же listings-программа, что JC-1/2.",
    ),
    "JC-5c": (
        "…собрать данные о local dance attendance, чтобы понять размер community…",
        "Сбор attendance вне реестра.",
    ),
    "KY-S": (
        "Хочу, чтобы комитет поддерживал текущую работу, миссию и стратегию. … Нужно осторожно не использовать комитет для расширения scope",
        "Постоянное правило для всего intake.",
    ),
    "KY-3": (
        "Где комитет может облегчить или поддержать текущую работу — особенно вокруг points database, коммуникации и инфраструктуры?",
        "Kay №3. Advisory; без ownership новых задач без мандата.",
    ),
    "JC-2c": (
        "Стать хабом информации о WCS поможет образовательным инициативам…",
        "Расширение product/mission; фильтр Kay.",
    ),
    "JC-3c": (
        "Можно фильтры на календаре показывать ивенты с этими номинациями… Комитет может дать feedback по другим фильтрам на сайте",
        "Website product; список фильтров можно опереть на инвентарь JC-3a.",
    ),
    "JC-4b": (
        "Для этих страниц листинги лучше бесплатные. … Может, 3 года бесплатно, потом $20 в год…",
        "Board / finance.",
    ),
    "JC-6b": (
        "А люди, танцевавшие не в том дивизионе? Аудит и снятие поинтов? … дубликаты… мержить записи? … записи, которые выглядят на удаление",
        "Политика аудита — Board/ops; правила детекции можно предложить позже.",
    ),
    "JC-7": (
        "История point ranking по ивенту и по человеку. Хотим ли добавить это на сайт?",
        "Product-решение.",
    ),
    "JT-6b": (
        "…ЕСЛИ разрешить «дисконтировать» поинты… (политика разрешения move-down)",
        "Решение Board по правилам; аналитическая поддержка = JT-6.",
    ),
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def strip_md(s: str) -> str:
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", s)


def main() -> None:
    text = (BASE / "MATRIX.md").read_text()
    m = re.search(r"## Matrix\n\n\| ID \|.*?\n\|----.*?\n(.*?)(?:\n---\n)", text, re.S)
    assert m
    rows = []
    for line in m.group(1).strip().splitlines():
        parts = [p.strip() for p in line.strip("|").split("|")]
        if parts[0] == "ID":
            continue
        rid = parts[0]
        assert rid in RU, f"missing RU for {rid}"
        q_ru, n_ru = RU[rid]
        rows.append(
            {
                "id": rid,
                "asker": parts[1],
                "cat": parts[3],
                "depth": parts[4],
                "q": q_ru,
                "notes": n_ru,
            }
        )
    missing = set(RU) - {r["id"] for r in rows}
    assert not missing, missing
    cats = Counter(r["cat"] for r in rows)
    n_full = sum(1 for r in rows if r["cat"] == "C1" and r["depth"] == "full")
    n_part = sum(1 for r in rows if r["cat"] == "C1" and r["depth"] == "partial")

    css = (BASE / "appendix_en.html").read_text()
    head = css[: css.index("<body>")]
    head = head.replace('lang="en"', 'lang="ru"')
    head = head.replace(
        "Appendix: Board questions classified C1–C5 for review.",
        "Приложение: вопросы Board по категориям C1–C5 — полный русский перевод.",
    )
    head = head.replace(
        "Board Questions Intake · Appendix by category (EN)",
        "Приём вопросов Board · Приложение по категориям (RU)",
    )
    if ".tag.full" not in head:
        head = head.replace(
            ".tag.reuse { border-color: #bfdbfe; background: #e8f0fe; color: #1e3a5f; }",
            """.tag.reuse { border-color: #bfdbfe; background: #e8f0fe; color: #1e3a5f; }
    .tag.full { border-color: #bbf7d0; background: #ecfdf5; color: #14532d; }
    .tag.partial { border-color: #fde68a; background: #fffbeb; color: #92400e; }
    .quote {
      margin: 0 0 6px;
      color: var(--ink);
      font-size: 0.95rem;
      font-style: italic;
    }
    .quote::before { content: "«"; }
    .quote::after { content: "»"; }""",
        )
    else:
        # RU guillemets for quotes
        head = head.replace('content: "“";', 'content: "«";').replace(
            'content: "”";', 'content: "»";'
        )

    blurbs = {
        "C1": (
            "Можно ответить сейчас",
            "Сначала <strong>полный</strong> ответ (брать в работу), затем <strong>частичный</strong> (та же цитата Board, только Scored / ограниченный слой).",
        ),
        "C2": (
            "После гигиены источников",
            "Та же цитата Board; в каждом ряду — <strong>что конкретно сделать</strong>, чтобы ответить полностью.",
        ),
        "C3": (
            "Нужен дизайн сбора внутри WSDC",
            "Внутри WSDC логично, но usable stream ещё нет.",
        ),
        "C4": ("Вне WSDC", "Community / non-registry ландшафт."),
        "C5": (
            "Governance / scope",
            "Стратегия, продукт или ops — не ещё один датасет.",
        ),
    }
    depth_ru = {"full": "полный", "partial": "частичный"}
    depth_rank = {"full": 0, "partial": 1, "blocked": 2, "scope": 3}
    reuse_ids = {"JT-1", "JT-2", "JT-3", "JN-1a", "JN-1b", "KY-1"}

    def item_html(r: dict) -> str:
        tags = ""
        if r["depth"] in depth_ru:
            tags += f' <span class="tag {r["depth"]}">{depth_ru[r["depth"]]}</span>'
        if r["id"] in reuse_ids:
            tags += ' <span class="tag reuse">reuse</span>'
        label = "Что сделать" if r["cat"] == "C2" else "Комментарий"
        if r["cat"] == "C3":
            label = "Дизайн"
        elif r["cat"] in ("C4", "C5"):
            label = "Комментарий"
        return f"""      <div class="item">
        <div class="who"><span class="id">{esc(r['id'])}</span> {esc(r['asker'])}{tags}</div>
        <p class="quote">{esc(r['q'])}</p>
        <p class="why"><strong>{label}:</strong> {esc(r['notes'])}</p>
      </div>
"""

    order = ["C1", "C2", "C3", "C4", "C5"]
    n = {c: cats[c] for c in order}
    top = f"""  <div class="top">
    <div>
      <strong>Приложение</strong> · классификация по категориям
      · <a href="slides_ru.html">← основная презентация</a>
      · <a href="appendix_en.html">EN</a>
    </div>
    <nav class="toc" aria-label="Категории">
      <a href="#c1">C1 · {n['C1']}</a>
      <a href="#c2">C2 · {n['C2']}</a>
      <a href="#c3">C3 · {n['C3']}</a>
      <a href="#c4">C4 · {n['C4']}</a>
      <a href="#c5">C5 · {n['C5']}</a>
    </nav>
  </div>
  <div class="wrap">
    <h1>Вопросы Board по категориям</h1>
    <p class="lead">В каждом ряду — <strong>цитата Board на русском</strong> (при дроблении — полный вопрос). C1: сначала полные ({n_full}), затем частичные ({n_part}). C2: конкретные шаги для полного ответа.</p>
    <p class="meta">Источник: MATRIX.md · {len(rows)} атомов · C1 {n['C1']} (полных {n_full} · частичных {n_part}) · C2 {n['C2']} · C3 {n['C3']} · C4 {n['C4']} · C5 {n['C5']}</p>
"""
    sections = []
    for c in order:
        title, blurb = blurbs[c]
        group = [r for r in rows if r["cat"] == c]
        if c == "C1":
            group = sorted(group, key=lambda r: depth_rank.get(r["depth"], 9))
        items = "".join(item_html(r) for r in group)
        sections.append(
            f"""    <section class="cat" id="{c.lower()}">
      <h2>{c} — {title} ({n[c]})</h2>
      <p class="blurb">{blurb}</p>
{items}    </section>
"""
        )
    out = head + "<body>\n" + top + "\n".join(sections) + "  </div>\n</body>\n</html>\n"
    (BASE / "appendix_ru.html").write_text(out)
    print(f"wrote appendix_ru.html ({len(rows)} atoms)")


if __name__ == "__main__":
    main()
