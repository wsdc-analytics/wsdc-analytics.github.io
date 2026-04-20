#!/usr/bin/env python3
"""
Сравнение данных между русской и английской версиями статей
для поиска противоречий в цифрах для одинаковых ивентов
"""

import re
from collections import defaultdict

def extract_event_data(html_content, lang):
    """Извлекает данные об ивентах из HTML"""
    events = defaultdict(dict)
    
    # Паттерны для поиска
    # Формат: <span class="event-name">... Event Name</span> ... <span class="metric-val">N</span> ... <span class="growth-cell">...</span>
    
    # Ищем все строки таблиц с ивентами
    # Паттерн для строки таблицы с ивентом
    table_row_pattern = r'<tr>.*?<td class="rank-col[^"]*">(\d+)</td>.*?<span class="event-name">.*?<span class="event-flag">([🇦-🇿\s]+)</span>\s*([^<]+)</span>.*?<span class="event-comment">([^<]*)</span>.*?<span class="metric-val">(\d+)</span>.*?<span class="growth-cell">.*?<span class="growth-[^"]*">([^<]+)</span>'
    
    # Более простой подход: ищем блоки с event-name
    event_blocks = re.findall(r'<span class="event-name">.*?<span class="event-flag">([🇦-🇿\s]+)</span>\s*([^<]+)</span>', html_content, re.DOTALL)
    
    # Находим метрики для каждого ивента
    lines = html_content.split('\n')
    
    current_section = None
    for i, line in enumerate(lines):
        # Определяем текущий раздел
        if 'Global Top (Points)' in line or 'Глобальный топ (Points)' in line:
            current_section = 'global_points'
        elif 'Global New Dancers' in line or 'Новые участники (New)' in line:
            current_section = 'global_new'
        elif 'European Top (Points)' in line or 'Европейский топ (Points)' in line:
            current_section = 'europe_points'
        elif 'European New Dancers' in line or 'Новые участники в Европе' in line:
            current_section = 'europe_new'
        elif 'US Top (Points)' in line or 'Топ США (Points)' in line:
            current_section = 'us_points'
        elif 'US New Dancers' in line or 'Новые участники в США' in line:
            current_section = 'us_new'
        elif 'Российские ивенты' in line or 'Russian Events' in line:
            current_section = 'russia_points'
        
        # Ищем строки с ивентами
        if '<span class="event-name">' in line:
            # Извлекаем название ивента
            event_match = re.search(r'<span class="event-name">.*?<span class="event-flag">([🇦-🇿\s]+)</span>\s*([^<]+)</span>', line)
            if event_match:
                flag = event_match.group(1).strip()
                event_name = event_match.group(2).strip()
                
                # Ищем метрики в следующих строках
                for j in range(i, min(i+10, len(lines))):
                    metric_match = re.search(r'<span class="metric-val">(\d+)</span>', lines[j])
                    growth_match = re.search(r'<span class="growth-cell">.*?<span class="growth-[^"]*">([^<]+)</span>', lines[j])
                    rank_match = re.search(r'<td class="rank-col[^"]*">(\d+)</td>', lines[i-5:i+5])
                    
                    if metric_match:
                        metric_val = int(metric_match.group(1))
                        growth_val = growth_match.group(1) if growth_match else None
                        rank_val = int(rank_match.group(1)) if rank_match else None
                        
                        key = f"{current_section}_{event_name}"
                        events[key] = {
                            'name': event_name,
                            'flag': flag,
                            'section': current_section,
                            'rank': rank_val,
                            'metric': metric_val,
                            'growth': growth_val,
                            'lang': lang,
                            'line': i
                        }
                        break
    
    return events

def compare_events(ru_events, en_events):
    """Сравнивает ивенты между версиями и находит противоречия"""
    # Группируем по названиям ивентов
    ru_by_name = {}
    en_by_name = {}
    
    for key, data in ru_events.items():
        name = data['name']
        if name not in ru_by_name:
            ru_by_name[name] = []
        ru_by_name[name].append(data)
    
    for key, data in en_events.items():
        name = data['name']
        if name not in en_by_name:
            en_by_name[name] = []
        en_by_name[name].append(data)
    
    # Находим общие ивенты
    common_names = set(ru_by_name.keys()) & set(en_by_name.keys())
    
    print(f"📊 Найдено общих ивентов: {len(common_names)}\n")
    
    contradictions = []
    
    for name in sorted(common_names):
        ru_data_list = ru_by_name[name]
        en_data_list = en_by_name[name]
        
        # Сравниваем каждую комбинацию
        for ru_data in ru_data_list:
            for en_data in en_data_list:
                # Пропускаем, если это разные разделы, которые не должны совпадать
                # (например, global vs regional)
                if ru_data['section'] != en_data['section']:
                    # Но если это один тип метрики (points или new), проверяем
                    if ('points' in ru_data['section'] and 'points' in en_data['section']) or \
                       ('new' in ru_data['section'] and 'new' in en_data['section']):
                        # Сравниваем метрики
                        if ru_data['metric'] != en_data['metric']:
                            contradictions.append({
                                'name': name,
                                'ru': ru_data,
                                'en': en_data,
                                'issue': f"Метрика не совпадает: RU={ru_data['metric']}, EN={en_data['metric']}"
                            })
                        # Сравниваем рост (но учитываем, что форматы могут отличаться)
                        ru_growth = ru_data['growth'] or ''
                        en_growth = en_data['growth'] or ''
                        if ru_growth and en_growth and ru_growth != en_growth:
                            # Проверяем, не является ли это просто разным форматированием
                            ru_num = re.search(r'([+-]?\d+\.?\d*)', ru_growth)
                            en_num = re.search(r'([+-]?\d+\.?\d*)', en_growth)
                            if ru_num and en_num and ru_num.group(1) != en_num.group(1):
                                contradictions.append({
                                    'name': name,
                                    'ru': ru_data,
                                    'en': en_data,
                                    'issue': f"Рост не совпадает: RU={ru_growth}, EN={en_growth}"
                                })
                else:
                    # Одинаковые разделы - должны полностью совпадать
                    if ru_data['metric'] != en_data['metric']:
                        contradictions.append({
                            'name': name,
                            'ru': ru_data,
                            'en': en_data,
                            'issue': f"Метрика не совпадает в одинаковом разделе: RU={ru_data['metric']}, EN={en_data['metric']}"
                        })
    
    return contradictions

# Читаем файлы
print("📖 Чтение файлов...\n")

with open('/Users/ania/.cursor/wsdc-analytics-repo/events_2025.html', 'r', encoding='utf-8') as f:
    ru_html = f.read()

with open('/Users/ania/.cursor/wsdc-analytics-repo/events_2025_en.html', 'r', encoding='utf-8') as f:
    en_html = f.read()

print("🔍 Извлечение данных...\n")

ru_events = extract_event_data(ru_html, 'ru')
en_events = extract_event_data(en_html, 'en')

print(f"Русская версия: {len(ru_events)} записей")
print(f"Английская версия: {len(en_events)} записей\n")

print("🔎 Поиск противоречий...\n")

contradictions = compare_events(ru_events, en_events)

if contradictions:
    print(f"⚠️  Найдено {len(contradictions)} противоречий:\n")
    for i, cont in enumerate(contradictions, 1):
        print(f"{i}. {cont['name']}")
        print(f"   Проблема: {cont['issue']}")
        print(f"   RU: раздел={cont['ru']['section']}, метрика={cont['ru']['metric']}, рост={cont['ru']['growth']}")
        print(f"   EN: раздел={cont['en']['section']}, метрика={cont['en']['metric']}, рост={cont['en']['growth']}")
        print()
else:
    print("✅ Противоречий не найдено!")


