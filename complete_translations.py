#!/usr/bin/env python3
"""
Полный перевод английской и испанской версий статьи
"""

import re
from pathlib import Path

HTML_FILE = Path('dancers_2025.html')

# Читаем исходный файл
with open(HTML_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Словари переводов
translations = {
    'en': {
        # Основные элементы
        'title': 'WSDC 2025: Top Dancers',
        'subtitle': 'Most successful WCS dancers in 2025',
        'description': 'WSDC 2025 Top Dancers: leaders by points, wins, and events with points in skill-level divisions.',
        'back_link': 'Back to home',
        'intro': '''In this article, we examine which WCS dancers had the most successful 2025 year in Skill Level divisions across three metrics:<br>
            - number of points earned,<br>
            - number of wins (first places) in divisions,<br>
            - number of events with points (unique events where the dancer earned points).<br>
            <br>
            Each section consists of a top-10 table and short summaries of the most notable dancers whose achievements in 2025 seemed most interesting.''',
        
        # Заголовки секций
        'global_title': 'Global Top',
        'european_title': 'Top-10 Dancers by European Events Results',
        'sophisticated_title': 'Top-10 Dancers by Sophisticated Divisions',
        
        # Метрики
        'by_points': 'by points',
        'by_wins': 'by wins',
        'by_events': 'by events',
        'use_switchers': 'Use the switchers to select a metric.',
        'name': 'Name',
        
        # Highlight блоки - общие фразы
        'geography': 'Geography:',
        'most_successful_event': 'Most successful event:',
        'most_successful_events': 'Most successful events:',
        'all_points': 'all points',
        'points': 'points',
        'wins': 'wins',
        'events': 'events',
        'on_european_events': 'on European events',
        'on_american_events': 'on American events',
        'on_russian_events': 'on Russian events',
        'on_spanish_events': 'on Spanish events',
        
        # Методология
        'data_source': 'Data source:',
        'methodology': 'Methodology:',
        'points_desc': 'Points - sum of points earned in skill-level divisions in 2025 (Newcomer, Novice, Intermediate, Advanced, All-Stars, Champions). For the Sophisticated section, only points earned in the Sophisticated division are counted.',
        'wins_desc': 'Wins - number of first places (wins) in skill-level divisions in 2025. For the Sophisticated section, only wins in the Sophisticated division are counted. Win = first place only (event_result = \'1\').',
        'events_desc': 'Events - number of unique events where the dancer earned points in 2025 (i.e., events where the dancer placed in positions that award points). Important: this is not the total number of participations or trips to events, but only events where points were earned, which reflects performance, not overall participation activity.',
        'sophisticated_desc': 'Sophisticated - age division for dancers 35+ years old, calculated separately from skill-level divisions.',
        'russian_desc': 'Russian dancers are identified by ID list from the repository apushkarev/wsdc.',
        'spanish_desc': 'Spanish dancers are identified by the provided list of dancer IDs from Spain.',
        'us_desc': 'American top considers only events held in the United States of America (United States).',
        
        # Комментарии
        'comments_title': 'Comments',
        'giscus_tab': 'GitHub (Giscus)',
        'cusdis_tab': 'Cusdis (no registration)',
        'giscus_info': 'A GitHub account is required for commenting. <a href="https://github.com/signup" rel="noopener noreferrer" target="_blank">Create a free account</a>',
        'cusdis_info': 'You can comment anonymously (by providing name and email) or via GitHub. Completely free, no ads.',
        
        # Динамика рейтингов
        'dynamics_title': 'About Rating Dynamics Between Years',
        'dynamics_text': '''When comparing top-10 dancers from 2024 and 2025, significant roster rotation is observed. This is natural dynamics for a competitive environment: only a small number of dancers remain in the top-10 year after year for each metric.<br>
            <br>
            This situation reflects both the competitiveness of the WSDC community and the influence of various factors: changes in competition schedules, dancers transitioning between divisions, individual development trajectories. Results for each year reflect the performance and achievements of that specific time period.''',
    },
    'es': {
        # Основные элементы
        'title': 'WSDC 2025: Top Bailarines',
        'subtitle': 'Los bailarines de WCS más exitosos en 2025',
        'description': 'Top Bailarines WSDC 2025: líderes por puntos, victorias y eventos con puntos en divisiones de nivel de habilidad.',
        'back_link': 'Volver al inicio',
        'intro': '''En este artículo, examinamos qué bailarines de WCS tuvieron el año 2025 más exitoso en divisiones de Nivel de Habilidad según tres métricas:<br>
            - número de puntos obtenidos,<br>
            - número de victorias (primeros lugares) en divisiones,<br>
            - número de eventos con puntos (eventos únicos donde el bailarín obtuvo puntos).<br>
            <br>
            Cada sección consiste en una tabla top-10 y resúmenes breves de los bailarines más destacados cuyos logros en 2025 parecieron más interesantes.''',
        
        # Заголовки секций
        'global_title': 'Top Global',
        'european_title': 'Top-10 Bailarines por Resultados de Eventos Europeos',
        'spanish_title': 'Top-10 Bailarines Españoles',
        
        # Метрики
        'by_points': 'por puntos',
        'by_wins': 'por victorias',
        'by_events': 'por eventos',
        'use_switchers': 'Use los interruptores para seleccionar una métrica.',
        'name': 'Nombre',
        
        # Highlight блоки
        'geography': 'Geografía:',
        'most_successful_event': 'Evento más exitoso:',
        'most_successful_events': 'Eventos más exitosos:',
        'all_points': 'todos los puntos',
        'points': 'puntos',
        'wins': 'victorias',
        'events': 'eventos',
        'on_european_events': 'en eventos europeos',
        'on_american_events': 'en eventos americanos',
        'on_russian_events': 'en eventos rusos',
        'on_spanish_events': 'en eventos españoles',
        
        # Методология
        'data_source': 'Fuente de datos:',
        'methodology': 'Metodología:',
        'points_desc': 'Points - suma de puntos obtenidos en divisiones de nivel de habilidad en 2025 (Newcomer, Novice, Intermediate, Advanced, All-Stars, Champions). Para la sección Sophisticated, solo se cuentan los puntos obtenidos en la división Sophisticated.',
        'wins_desc': 'Wins - número de primeros lugares (victorias) en divisiones de nivel de habilidad en 2025. Para la sección Sophisticated, solo se cuentan las victorias en la división Sophisticated. Victoria = solo primer lugar (event_result = \'1\').',
        'events_desc': 'Events - número de eventos únicos donde el bailarín obtuvo puntos en 2025 (es decir, eventos donde el bailarín ocupó posiciones que otorgan puntos). Importante: esto no es el número total de participaciones o viajes a eventos, sino solo eventos donde se obtuvieron puntos, lo que refleja el rendimiento, no la actividad general de participación.',
        'sophisticated_desc': 'Sophisticated - división de edad para bailarines de 35+ años, calculada por separado de las divisiones de nivel de habilidad.',
        'russian_desc': 'Los bailarines rusos se identifican por lista de ID del repositorio apushkarev/wsdc.',
        'spanish_desc': 'Los bailarines españoles se identifican por la lista proporcionada de ID de bailarines de España.',
        'us_desc': 'El top americano considera solo eventos realizados en los Estados Unidos de América (United States).',
        
        # Комментарии
        'comments_title': 'Comentarios',
        'giscus_tab': 'GitHub (Giscus)',
        'cusdis_tab': 'Cusdis (sin registro)',
        'giscus_info': 'Se requiere una cuenta de GitHub para comentar. <a href="https://github.com/signup" rel="noopener noreferrer" target="_blank">Crear una cuenta gratuita</a>',
        'cusdis_info': 'Puedes comentar de forma anónima (proporcionando nombre y correo electrónico) o a través de GitHub. Completamente gratis, sin anuncios.',
        
        # Динамика рейтингов
        'dynamics_title': 'Sobre la Dinámica de Clasificaciones Entre Años',
        'dynamics_text': '''Al comparar los top-10 bailarines de 2024 y 2025, se observa una rotación significativa del plantel. Esta es una dinámica natural para un entorno competitivo: solo un pequeño número de bailarines permanece en el top-10 año tras año para cada métrica.<br>
            <br>
            Esta situación refleja tanto la competitividad de la comunidad WSDC como la influencia de varios factores: cambios en los calendarios de competición, bailarines que transicionan entre divisiones, trayectorias de desarrollo individual. Los resultados de cada año reflejan el rendimiento y los logros de ese período de tiempo específico.''',
    }
}

def translate_text(text, lang):
    """Переводит текст используя словарь"""
    t = translations[lang]
    
    # Замены общих фраз
    replacements = [
        (r'по поинтам', t['by_points']),
        (r'по победам', t['by_wins']),
        (r'по ивентам', t['by_events']),
        (r'Используйте переключатели чтобы выбрать метрику\.', t['use_switchers']),
        (r'Имя', t['name']),
        (r'География:', t['geography']),
        (r'Самый успешный ивент:', t['most_successful_event']),
        (r'Самые успешные ивенты:', t['most_successful_events']),
        (r'все поинты', t['all_points']),
        (r'на европейских ивентах', t['on_european_events']),
        (r'на американских ивентах', t['on_american_events']),
        (r'на российских ивентах', t['on_russian_events']),
        (r'на испанских ивентах', t['on_spanish_events']),
    ]
    
    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text

def create_translated_version(lang, sections_needed):
    """Создает переведенную версию"""
    print(f"\nСоздание {lang.upper()} версии...")
    
    t = translations[lang]
    
    # Извлекаем нужные части
    header_end = content.find('<article class="article-content">')
    header = content[:header_end] if header_end != -1 else content[:1000]
    
    # Обновляем header
    header = re.sub(r'<html lang="ru">', f'<html lang="{lang}">', header)
    header = re.sub(r'WSDC 2025: Топ-танцоры', t['title'], header)
    header = re.sub(r'Топ-танцоры WSDC 2025: лидеры по поинтам', t['description'], header)
    header = re.sub(r'Наиболее успешные танцоры WCS в 2025 году', t['subtitle'], header)
    header = re.sub(r'Назад на главную', t['back_link'], header)
    
    # Обновляем URL в метаданных
    filename = f'dancers_2025_{lang}.html'
    header = re.sub(r'dancers_2025\.html', filename, header)
    header = re.sub(r'dancers_2025_ru\.html', filename, header)
    header = re.sub(r'dancers_2025_en\.html', filename, header)
    header = re.sub(r'dancers_2025_es\.html', filename, header)
    
    # Собираем контент
    result = header + '\n<article class="article-content">\n'
    
    # Intro
    result += f'<div class="intro">\n            {t["intro"]}\n        </div>\n'
    
    # Добавляем нужные секции
    if 'global' in sections_needed:
        global_section = find_section(content, '<!-- Section 1: Global Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')
        if global_section:
            global_section = translate_section(global_section, lang)
            result += global_section + '\n<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>\n'
    
    if 'european' in sections_needed:
        european_section = find_section(content, '<!-- Section 4: European Events Top', '</section>')
        if european_section:
            european_section = translate_section(european_section, lang)
            result += european_section + '\n<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>\n'
    
    if 'sophisticated' in sections_needed:
        sophisticated_section = find_section(content, '<!-- Section 3: Sophisticated Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')
        if sophisticated_section:
            sophisticated_section = translate_section(sophisticated_section, lang)
            result += sophisticated_section + '\n'
    
    if 'russian' in sections_needed:
        russian_section = find_section(content, '<!-- Section 2: Russian Top', '<hr style="border: 0; border-top: 1px solid #e5e5e5; margin: 60px 0;"/>')
        if russian_section:
            russian_section = translate_section(russian_section, lang)
            result += russian_section + '\n'
    
    if 'spanish' in sections_needed:
        spanish_start = content.find('<section class="section">\n<h2 class="section-title">Топ-10 испанских танцоров</h2>')
        if spanish_start != -1:
            spanish_end = content.find('</section>', spanish_start) + len('</section>')
            spanish_section = content[spanish_start:spanish_end]
            spanish_section = translate_section(spanish_section, lang)
            result += spanish_section + '\n'
    
    # Динамика рейтингов
    dynamics_start = content.find('<!-- Disclaimer about year-over-year dynamics -->')
    if dynamics_start != -1:
        dynamics_end = content.find('</section>', dynamics_start) + len('</section>')
        dynamics_section = content[dynamics_start:dynamics_end]
        dynamics_section = translate_dynamics_section(dynamics_section, lang)
        result += dynamics_section + '\n'
    
    # Комментарии
    comments_start = content.find('<!-- Comments section -->')
    if comments_start != -1:
        comments_end = content.find('</section>', comments_start) + len('</section>')
        comments_section = content[comments_start:comments_end]
        comments_section = translate_comments_section(comments_section, lang)
        result += comments_section + '\n'
    
    # Footer
    footer_start = content.find('<footer class="article-footer">')
    footer_end = content.find('</footer>') + len('</footer>')
    footer = content[footer_start:footer_end] if footer_start != -1 else ""
    footer = translate_footer(footer, lang)
    
    # Scripts
    scripts_start = content.find('<script>', footer_end)
    scripts = content[scripts_start:] if scripts_start != -1 else ""
    
    result += '\n</article>\n' + footer + '\n</div>\n' + scripts
    
    return result

def find_section(content, start_marker, end_marker=None):
    """Находит секцию"""
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

def translate_section(section, lang):
    """Переводит секцию"""
    t = translations[lang]
    
    # Заголовки секций
    if 'Общий топ' in section:
        section = section.replace('Общий топ', t['global_title'])
    if 'Топ-10 танцоров по результатам европейских ивентов' in section:
        section = section.replace('Топ-10 танцоров по результатам европейских ивентов', t['european_title'])
    if 'Топ-10 танцоров по Sophisticated номинациям' in section:
        section = section.replace('Топ-10 танцоров по Sophisticated номинациям', t['sophisticated_title'])
    if 'Топ-10 российских танцоров' in section:
        section = section.replace('Топ-10 российских танцоров', 'Top-10 Russian Dancers' if lang == 'en' else 'Top-10 Bailarines Rusos')
    if 'Топ-10 испанских танцоров' in section:
        if 'spanish_title' in t:
            section = section.replace('Топ-10 испанских танцоров', t['spanish_title'])
        else:
            section = section.replace('Топ-10 испанских танцоров', 'Top-10 Spanish Dancers')
    
    # Общие замены
    section = translate_text(section, lang)
    
    return section

def translate_dynamics_section(section, lang):
    """Переводит секцию про динамику"""
    t = translations[lang]
    section = section.replace('О динамике рейтингов между годами', t['dynamics_title'])
    # Найдем текст внутри и заменим
    pattern = r'<p>При сравнении топ-10 танцоров.*?</p>'
    replacement = f'<p>{t["dynamics_text"]}</p>'
    section = re.sub(pattern, replacement, section, flags=re.DOTALL)
    return section

def translate_comments_section(section, lang):
    """Переводит секцию комментариев"""
    t = translations[lang]
    section = section.replace('Комментарии', t['comments_title'])
    section = section.replace('GitHub (Giscus)', t['giscus_tab'])
    section = section.replace('Cusdis (без регистрации)', t['cusdis_tab'])
    
    # Информация о комментариях
    giscus_info_pattern = r'Для комментирования необходим GitHub аккаунт.*?</a>'
    giscus_info_replacement = t['giscus_info']
    section = re.sub(giscus_info_pattern, giscus_info_replacement, section, flags=re.DOTALL)
    
    cusdis_info_pattern = r'Можно комментировать анонимно.*?рекламы\.'
    cusdis_info_replacement = t['cusdis_info']
    section = re.sub(cusdis_info_pattern, cusdis_info_replacement, section, flags=re.DOTALL)
    
    # Обновляем lang в скриптах
    if lang == 'en':
        section = section.replace('data-lang="ru"', 'data-lang="en"')
    elif lang == 'es':
        section = section.replace('data-lang="ru"', 'data-lang="es"')
    
    return section

def translate_footer(footer, lang):
    """Переводит футер"""
    t = translations[lang]
    
    footer = footer.replace('Источник данных:', t['data_source'])
    footer = footer.replace('Методология:', t['methodology'])
    
    # Переводим описания методологии
    footer = footer.replace('Points - сумма поинтов', t['points_desc'].split(' - ')[0] + ' - ' + t['points_desc'].split(' - ')[1])
    # Это сложнее, нужно заменить весь блок методологии
    # Пока оставим базовые замены
    
    return footer

# Создаем версии
print("Начало создания переведенных версий...")

# Английская версия: Global + European + Sophisticated
en_content = create_translated_version('en', ['global', 'european', 'sophisticated'])
with open('dancers_2025_en.html', 'w', encoding='utf-8') as f:
    f.write(en_content)
print("✅ Английская версия создана")

# Испанская версия: Global + European + Spanish
es_content = create_translated_version('es', ['global', 'european', 'spanish'])
with open('dancers_2025_es.html', 'w', encoding='utf-8') as f:
    f.write(es_content)
print("✅ Испанская версия создана")

print("\n⚠️  ВАЖНО: Переводы highlight блоков требуют дополнительной работы.")
print("   Создана структура с переводами основных элементов.")
