#!/usr/bin/env python3
"""
Проверка согласованности данных между русской и английской версиями статей
"""

import re
from collections import defaultdict

def extract_table_data(html_content):
    """Извлекает данные из всех таблиц"""
    events = defaultdict(list)
    
    # Ищем все таблицы с классом rank-table
    table_pattern = r'<table class="rank-table">.*?</table>'
    tables = re.findall(table_pattern, html_content, re.DOTALL)
    
    for table in tables:
        # Определяем раздел по заголовку перед таблицей
        section = None
        # Ищем заголовок перед таблицей
        table_start = html_content.find(table)
        prev_text = html_content[max(0, table_start-500):table_start]
        
        if 'Global Top (Points)' in prev_text or 'Глобальный топ (Points)' in prev_text:
            section = 'global_points'
        elif 'Global New Dancers' in prev_text or 'Новые участники (New)' in prev_text or 'Новые участники \(New\)' in prev_text:
            section = 'global_new'
        elif 'European Top (Points)' in prev_text or 'Европейский топ (Points)' in prev_text:
            section = 'europe_points'
        elif 'European New Dancers' in prev_text or 'Новые участники в Европе' in prev_text:
            section = 'europe_new'
        elif 'US Top (Points)' in prev_text or 'Топ США (Points)' in prev_text:
            section = 'us_points'
        elif 'US New Dancers' in prev_text or 'Новые участники в США' in prev_text:
            section = 'us_new'
        elif 'Российские ивенты' in prev_text:
            section = 'russia_points'
        
        if not section:
            continue
        
        # Извлекаем строки таблицы
        rows = re.findall(r'<tr>.*?</tr>', table, re.DOTALL)
        
        for row in rows:
            # Ищем название ивента
            event_match = re.search(r'<span class="event-name">.*?<span class="event-flag">([🇦-🇿\s]+)</span>\s*([^<]+)</span>', row, re.DOTALL)
            if not event_match:
                continue
            
            flag = event_match.group(1).strip()
            event_name = event_match.group(2).strip()
            
            # Ищем ранг
            rank_match = re.search(r'<td class="rank-col[^"]*">(\d+)</td>', row)
            rank = int(rank_match.group(1)) if rank_match else None
            
            # Ищем метрику
            metric_match = re.search(r'<span class="metric-val">(\d+)</span>', row)
            if not metric_match:
                continue
            metric = int(metric_match.group(1))
            
            # Ищем рост
            growth_match = re.search(r'<span class="growth-cell">.*?<span class="growth-[^"]*">([^<]+)</span>', row, re.DOTALL)
            growth = growth_match.group(1).strip() if growth_match else None
            
            events[event_name].append({
                'section': section,
                'rank': rank,
                'metric': metric,
                'growth': growth,
                'flag': flag
            })
    
    return events

def normalize_event_name(name):
    """Нормализует название ивента для сравнения"""
    # Убираем лишние пробелы
    name = ' '.join(name.split())
    
    # Приводим к нижнему регистру для сравнения
    name_lower = name.lower()
    
    # Синонимы - нормализуем к одному варианту
    if 'liberty swing' in name_lower:
        return 'liberty swing'
    
    return name_lower

def compare_events(ru_events, en_events):
    """Сравнивает события между версиями"""
    contradictions = []
    
    # Нормализуем названия
    ru_normalized = {}
    for name, data_list in ru_events.items():
        norm_name = normalize_event_name(name)
        if norm_name not in ru_normalized:
            ru_normalized[norm_name] = []
        ru_normalized[norm_name].extend(data_list)
    
    en_normalized = {}
    for name, data_list in en_events.items():
        norm_name = normalize_event_name(name)
        if norm_name not in en_normalized:
            en_normalized[norm_name] = []
        en_normalized[norm_name].extend(data_list)
    
    # Находим общие ивенты
    common_events = set(ru_normalized.keys()) & set(en_normalized.keys())
    
    print(f"📊 Найдено общих ивентов: {len(common_events)}\n")
    
    for event_name in sorted(common_events):
        ru_data_list = ru_normalized[event_name]
        en_data_list = en_normalized[event_name]
        
        # Группируем по разделам
        ru_by_section = defaultdict(list)
        en_by_section = defaultdict(list)
        
        for data in ru_data_list:
            ru_by_section[data['section']].append(data)
        for data in en_data_list:
            en_by_section[data['section']].append(data)
        
        # Проверяем совпадения метрик в одинаковых разделах
        common_sections = set(ru_by_section.keys()) & set(en_by_section.keys())
        
        for section in common_sections:
            ru_entries = ru_by_section[section]
            en_entries = en_by_section[section]
            
            # Сравниваем каждую пару
            for ru_entry in ru_entries:
                for en_entry in en_entries:
                    if ru_entry['metric'] != en_entry['metric']:
                        contradictions.append({
                            'event': event_name,
                            'section': section,
                            'ru_metric': ru_entry['metric'],
                            'en_metric': en_entry['metric'],
                            'ru_rank': ru_entry['rank'],
                            'en_rank': en_entry['rank'],
                            'ru_growth': ru_entry['growth'],
                            'en_growth': en_entry['growth']
                        })
        
        # Также проверяем пересекающиеся разделы (global vs regional)
        # Например, если ивент есть в global_points и us_points, метрика должна совпадать
        for ru_section, ru_entries in ru_by_section.items():
            for en_section, en_entries in en_by_section.items():
                # Если это один тип метрики (points или new)
                if ('points' in ru_section and 'points' in en_section) or \
                   ('new' in ru_section and 'new' in en_section):
                    # И это не один и тот же раздел
                    if ru_section != en_section:
                        # Сравниваем метрики (они должны совпадать, если это один и тот же ивент)
                        for ru_entry in ru_entries:
                            for en_entry in en_entries:
                                if ru_entry['metric'] != en_entry['metric']:
                                    contradictions.append({
                                        'event': event_name,
                                        'section': f"{ru_section} (RU) vs {en_section} (EN)",
                                        'ru_metric': ru_entry['metric'],
                                        'en_metric': en_entry['metric'],
                                        'ru_rank': ru_entry['rank'],
                                        'en_rank': en_entry['rank'],
                                        'ru_growth': ru_entry['growth'],
                                        'en_growth': en_entry['growth']
                                    })
    
    return contradictions, ru_normalized, en_normalized

def print_detailed_comparison(ru_normalized, en_normalized, contradictions):
    """Выводит детальное сравнение ивентов"""
    common_events = set(ru_normalized.keys()) & set(en_normalized.keys())
    
    print("📋 Детальное сравнение общих ивентов:\n")
    
    for event_name in sorted(common_events):
        ru_data_list = ru_normalized[event_name]
        en_data_list = en_normalized[event_name]
        
        print(f"🎯 {event_name}")
        print(f"   RU ({len(ru_data_list)} записей):")
        for data in ru_data_list:
            print(f"      - {data['section']}: метрика={data['metric']}, ранг={data['rank']}, рост={data['growth']}")
        print(f"   EN ({len(en_data_list)} записей):")
        for data in en_data_list:
            print(f"      - {data['section']}: метрика={data['metric']}, ранг={data['rank']}, рост={data['growth']}")
        print()
    
    if contradictions:
        print(f"\n⚠️  Найдено {len(contradictions)} противоречий:\n")
        for i, cont in enumerate(contradictions, 1):
            print(f"{i}. {cont['event']}")
            print(f"   Раздел: {cont['section']}")
            print(f"   RU: метрика={cont['ru_metric']}, ранг={cont['ru_rank']}, рост={cont['ru_growth']}")
            print(f"   EN: метрика={cont['en_metric']}, ранг={cont['en_rank']}, рост={cont['en_growth']}")
            print()
    else:
        print("\n✅ Противоречий не найдено!")

# Читаем файлы
print("📖 Чтение файлов...\n")

with open('/Users/ania/.cursor/wsdc-analytics-repo/events_2025.html', 'r', encoding='utf-8') as f:
    ru_html = f.read()

with open('/Users/ania/.cursor/wsdc-analytics-repo/events_2025_en.html', 'r', encoding='utf-8') as f:
    en_html = f.read()

print("🔍 Извлечение данных...\n")

ru_events = extract_table_data(ru_html)
en_events = extract_table_data(en_html)

print(f"Русская версия: {sum(len(v) for v in ru_events.values())} записей, {len(ru_events)} уникальных ивентов")
print(f"Английская версия: {sum(len(v) for v in en_events.values())} записей, {len(en_events)} уникальных ивентов\n")

print("🔎 Поиск противоречий...\n")

contradictions, ru_normalized, en_normalized = compare_events(ru_events, en_events)

print_detailed_comparison(ru_normalized, en_normalized, contradictions)

