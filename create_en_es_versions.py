#!/usr/bin/env python3
"""
Создание английской и испанской версий статьи с переводами
"""

import re
from pathlib import Path

HTML_FILE = Path('dancers_2025.html')

# Читаем исходный файл
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Переводы основных элементов
translations_en = {
    'ru': {
        'lang': 'en',
        'title': 'WSDC 2025: Top Dancers',
        'subtitle': 'Most successful WCS dancers in 2025',
        'description': 'WSDC 2025 Top Dancers: leaders by points, wins, and events with points in skill-level divisions.',
        'intro': '''In this article, we examine which WCS dancers had the most successful 2025 year in Skill Level divisions across three metrics:<br>
            - number of points earned,<br>
            - number of wins (first places) in divisions,<br>
            - number of events with points (unique events where the dancer earned points).<br>
            <br>
            Each section consists of a top-10 table and short summaries of the most notable dancers whose achievements in 2025 seemed most interesting.''',
        'back_link': 'Back to home',
        'global_title': 'Global Top',
        'european_title': 'Top-10 Dancers by European Events Results',
        'sophisticated_title': 'Top-10 Dancers by Sophisticated Divisions',
        'use_switchers': 'Use the switchers to select a metric.',
        'name': 'Name',
        'geography': 'Geography:',
        'most_successful_event': 'Most successful event:',
        'most_successful_events': 'Most successful events:',
    },
    'es': {
        'lang': 'es',
        'title': 'WSDC 2025: Top Bailarines',
        'subtitle': 'Los bailarines de WCS más exitosos en 2025',
        'description': 'Top Bailarines WSDC 2025: líderes por puntos, victorias y eventos con puntos en divisiones de nivel de habilidad.',
        'intro': '''En este artículo, examinamos qué bailarines de WCS tuvieron el año 2025 más exitoso en divisiones de Nivel de Habilidad según tres métricas:<br>
            - número de puntos obtenidos,<br>
            - número de victorias (primeros lugares) en divisiones,<br>
            - número de eventos con puntos (eventos únicos donde el bailarín obtuvo puntos).<br>
            <br>
            Cada sección consiste en una tabla top-10 y resúmenes breves de los bailarines más destacados cuyos logros en 2025 parecieron más interesantes.''',
        'back_link': 'Volver al inicio',
        'global_title': 'Top Global',
        'european_title': 'Top-10 Bailarines por Resultados de Eventos Europeos',
        'spanish_title': 'Top-10 Bailarines Españoles',
        'use_switchers': 'Use los interruptores para seleccionar una métrica.',
        'name': 'Nombre',
        'geography': 'Geografía:',
        'most_successful_event': 'Evento más exitoso:',
        'most_successful_events': 'Eventos más exitosos:',
    }
}

def find_section(content, start_marker, end_marker=None):
    """Находит секцию между маркерами"""
    start_pos = content.find(start_marker)
    if start_pos == -1:
        return None
    
    if end_marker:
        end_pos = content.find(end_marker, start_pos)
        if end_pos == -1:
            end_pos = content.find('<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>', start_pos)
            if end_pos == -1:
                end_pos = content.find('</section>', start_pos)
            if end_pos != -1:
                end_pos += len('</section>')
        else:
            end_pos += len(end_marker)
    else:
        end_pos = len(content)
    
    return content[start_pos:end_pos] if start_pos != -1 else None

# Извлекаем секции
header_end = content.find('<article class="article-content">')
header = content[:header_end] if header_end != -1 else content[:1000]

intro_start = content.find('<div class="intro">')
intro_end = content.find('</div>', intro_start) + len('</div>')
intro = content[intro_start:intro_end] if intro_start != -1 else ""

global_section = find_section(content, '<!-- Section 1: Global Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')
european_section = find_section(content, '<!-- Section 4: European Events Top', '</section>')
sophisticated_section = find_section(content, '<!-- Section 3: Sophisticated Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')

spanish_start = content.find('<section class="section">\n<h2 class="section-title">Топ-10 испанских танцоров</h2>')
spanish_section = None
if spanish_start != -1:
    spanish_end = content.find('</section>', spanish_start)
    if spanish_end != -1:
        spanish_end += len('</section>')
        spanish_section = content[spanish_start:spanish_end]

footer_start = content.find('<footer class="article-footer">')
footer_and_scripts = content[footer_start:] if footer_start != -1 else ""

# Создаем английскую версию
print("Создание английской версии...")
en_content = header

# Обновляем метаданные
t = translations_en['ru']  # Используем ключ 'ru' для английских переводов
en_content = re.sub(r'<html lang="ru">', f'<html lang="{t["lang"]}">', en_content)
en_content = re.sub(r'WSDC 2025: Топ-танцоры', t['title'], en_content)
en_content = re.sub(r'Топ-танцоры WSDC 2025: лидеры по поинтам', t['description'], en_content)
en_content = re.sub(r'Наиболее успешные танцоры WCS в 2025 году', t['subtitle'], en_content)
en_content = re.sub(r'Назад на главную', t['back_link'], en_content)
en_content = re.sub(r'dancers_2025\.html', 'dancers_2025_en.html', en_content)

# Добавляем контент
en_content += intro.replace('В этой статье мы рассмотрим', t['intro'].split('<br>')[0].replace('In this article, we examine', ''))
en_content = en_content.replace(intro, f'<div class="intro">\n            {t["intro"]}\n        </div>')

if global_section:
    en_section = global_section.replace('Общий топ', t['global_title'])
    en_section = en_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    en_section = en_section.replace('Имя', t['name'])
    en_content += en_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"

if european_section:
    en_section = european_section.replace('Топ-10 танцоров по результатам европейских ивентов', t['european_title'])
    en_section = en_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    en_section = en_section.replace('Имя', t['name'])
    en_content += en_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"

if sophisticated_section:
    en_section = sophisticated_section.replace('Топ-10 танцоров по Sophisticated номинациям', t['sophisticated_title'])
    en_section = en_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    en_section = en_section.replace('Имя', t['name'])
    en_content += en_section + "\n"

en_content += "\n</article>\n" + footer_and_scripts

with open('dancers_2025_en.html', 'w', encoding='utf-8') as f:
    f.write(en_content)
print("✅ Английская версия создана: dancers_2025_en.html")

# Создаем испанскую версию
print("\nСоздание испанской версии...")
es_content = header

t = translations_en['es']
es_content = re.sub(r'<html lang="ru">', f'<html lang="{t["lang"]}">', es_content)
es_content = re.sub(r'WSDC 2025: Топ-танцоры', t['title'], es_content)
es_content = re.sub(r'Топ-танцоры WSDC 2025: лидеры по поинтам', t['description'], es_content)
es_content = re.sub(r'Наиболее успешные танцоры WCS в 2025 году', t['subtitle'], es_content)
es_content = re.sub(r'Назад на главную', t['back_link'], es_content)
es_content = re.sub(r'dancers_2025\.html', 'dancers_2025_es.html', es_content)

es_content += f'<div class="intro">\n            {t["intro"]}\n        </div>'

if global_section:
    es_section = global_section.replace('Общий топ', t['global_title'])
    es_section = es_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    es_section = es_section.replace('Имя', t['name'])
    es_content += es_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"

if european_section:
    es_section = european_section.replace('Топ-10 танцоров по результатам европейских ивентов', t['european_title'])
    es_section = es_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    es_section = es_section.replace('Имя', t['name'])
    es_content += es_section + "\n<hr style=\"border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;\"/>\n"

if spanish_section:
    es_section = spanish_section.replace('Топ-10 испанских танцоров', t['spanish_title'])
    es_section = es_section.replace('Используйте переключатели чтобы выбрать метрику.', t['use_switchers'])
    es_section = es_section.replace('Имя', t['name'])
    es_content += es_section + "\n"

es_content += "\n</article>\n" + footer_and_scripts

with open('dancers_2025_es.html', 'w', encoding='utf-8') as f:
    f.write(es_content)
print("✅ Испанская версия создана: dancers_2025_es.html")

print("\n⚠️  ВАЖНО: Переводы highlight блоков и детальных описаний требуют ручной работы.")
print("   Создана базовая структура с переводами заголовков и основных элементов.")
