#!/usr/bin/env python3
"""
Скрипт для расчета топ-20 американских штатов по поинтам в 2025 году
Использует ту же логику, что и get_geo_stats.py для статьи
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

# Добавляем путь к normalize_geo_data
sys.path.insert(0, '/Users/ania/.cursor')
try:
    from normalize_geo_data import normalize_location
except ImportError:
    print("❌ Не удалось импортировать normalize_location")
    sys.exit(1)

def load_csv_data():
    """Загружает данные из CSV файлов - использует тот же путь, что и get_geo_stats.py"""
    filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'
    
    if not os.path.exists(filename_points):
        print(f"❌ Файл не найден: {filename_points}")
        return None, None
    
    if not os.path.exists(filename_events):
        print(f"❌ Файл не найден: {filename_events}")
        return None, None
    
    print(f"✅ Найдены файлы:")
    print(f"   - {filename_points}")
    print(f"   - {filename_events}")
    
    return filename_points, filename_events

# Manual overrides (как в get_geo_stats.py)
MANUAL_LOCATIONS = {
    'Scandinavian Open': 'Stockholm, Sweden',
    'Scandinavian Open WCS': 'Stockholm, Sweden',
    'Scandinavian Open WCS 2022': 'Stockholm, Sweden',
    'Scandinavian Open WCS "SNOW"': 'Stockholm, Sweden',
}

# События, которые нужно исключить из расчета (не чисто WCS события)
EXCLUDED_EVENTS = {
    # Убрано - Worlds UCWDC чистое WCS событие, просто была неправильная локация
}

# Маппинг альтернативных названий событий (когда название в dancers_results_info отличается от events_wsdc)
EVENT_NAME_MAPPING = {
    'Worlds UCWDC': 'UCWDC Country Dance World Championship',  # Для 2025 года в events_wsdc называется иначе
}

def calculate_top20_states():
    """Рассчитывает топ-20 американских штатов - использует ту же логику, что и get_geo_stats.py"""
    dancers_file, events_file = load_csv_data()
    
    if not dancers_file or not events_file:
        return
    
    # 1. Build Event Location Map (как в get_geo_stats.py, но с учетом дат для одинаковых названий)
    event_geo_map = {}
    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['name'].strip()
                loc = row.get('location', '').strip()
                date_str = row.get('date', '').strip()
                
                if name and loc:
                    city, state, country = normalize_location(loc)
                    if country:
                        # Парсим дату для выбора самой поздней локации для одинаковых названий
                        event_date = None
                        try:
                            for fmt in ['%B %Y', '%b %Y', '%Y-%m-%d', '%Y/%m/%d']:
                                try:
                                    event_date = datetime.strptime(date_str.strip(), fmt)
                                    break
                                except:
                                    continue
                        except:
                            pass
                        
                        # Если событие с таким названием уже есть, выбираем более позднее
                        if name not in event_geo_map:
                            event_geo_map[name] = {
                                'city': city,
                                'state': state,
                                'country': country,
                                'raw_loc': loc,
                                'date': event_date
                            }
                        else:
                            existing_date = event_geo_map[name].get('date')
                            # Если новое событие более позднее, обновляем
                            if event_date and (not existing_date or event_date > existing_date):
                                event_geo_map[name] = {
                                    'city': city,
                                    'state': state,
                                    'country': country,
                                    'raw_loc': loc,
                                    'date': event_date
                                }
    except Exception as e:
        print(f"❌ Ошибка при чтении events_wsdc.csv: {e}")
        return
    
    # Добавляем manual overrides
    for name, loc_str in MANUAL_LOCATIONS.items():
        city, state, country = normalize_location(loc_str)
        event_geo_map[name] = {
            'city': city,
            'state': state,
            'country': country,
            'raw_loc': loc_str
        }
    
    print(f"✅ Загружено {len(event_geo_map)} событий с локациями")
    
    # 2. Загружаем статистику штатов США (как в get_geo_stats.py)
    stats_state = defaultdict(lambda: {
        'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
    })
    
    # 3. История для определения новых танцоров (локальная логика - первые поинты в штате в 2025)
    dancer_first_state_year = {}  # dancer_id -> {state -> year}
    
    # Сначала сканируем всю историю для определения первых поинтов в штате
    print("📊 Сканируем историю для определения новых танцоров...")
    with open(dancers_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
                continue
            
            event_name = row['event_name']
            dancer_id = row['dancer_id']
            year = int(row['event_year'])
            
            # Проверяем маппинг названий (когда название в dancers_results_info отличается)
            mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
            geo = event_geo_map.get(mapped_name)
            
            if not geo:
                geo = event_geo_map.get(event_name)
            
            if not geo:
                clean_name = event_name.split(' 20')[0].strip()
                geo = event_geo_map.get(clean_name)
            
            if geo and geo['country'] == 'United States' and geo['state']:
                state = geo['state']
                if dancer_id not in dancer_first_state_year:
                    dancer_first_state_year[dancer_id] = {}
                if state not in dancer_first_state_year[dancer_id] or year < dancer_first_state_year[dancer_id][state]:
                    dancer_first_state_year[dancer_id][state] = year
    
    # 4. Обрабатываем данные за 2025 год
    print("📊 Обрабатываем данные за 2025 год...")
    try:
        with open(dancers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['event_year'] != '2025':
                    continue
                
                if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
                    continue
                
                event_name = row['event_name']
                
                # Исключаем определенные события
                if event_name in EXCLUDED_EVENTS:
                    continue
                
                dancer_id = row['dancer_id']
                try:
                    points = int(row['event_points'])
                except:
                    points = 0
                
                if points <= 0:
                    continue
                
                # Проверяем маппинг названий
                mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
                geo = event_geo_map.get(mapped_name)
                
                if not geo:
                    geo = event_geo_map.get(event_name)
                
                if not geo:
                    clean_name = event_name.split(' 20')[0].strip()
                    geo = event_geo_map.get(clean_name)
                
                if not geo:
                    continue
                
                # Только штаты США
                if geo['country'] != 'United States' or not geo['state']:
                    continue
                
                state = geo['state']
                
                # Обновляем статистику
                stats_state[state]['points'] += points
                stats_state[state]['events_set'].add(event_name)
                stats_state[state]['dancers_set'].add(dancer_id)
                
                # Проверяем, новый ли танцор в этом штате (первые поинты в штате в 2025)
                if dancer_id in dancer_first_state_year and state in dancer_first_state_year[dancer_id]:
                    if dancer_first_state_year[dancer_id][state] == 2025:
                        stats_state[state]['new_dancers_set'].add(dancer_id)
    
    except Exception as e:
        print(f"❌ Ошибка при чтении dancers_results_info.csv: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Сортируем по поинтам
    sorted_states = sorted(stats_state.items(), key=lambda x: x[1]['points'], reverse=True)
    
    # Выводим топ-20
    print("\n" + "="*80)
    print("🏆 ТОП-20 АМЕРИКАНСКИХ ШТАТОВ (2025)")
    print("="*80)
    print(f"{'#':<4} {'Штат':<25} {'Поинты':<12} {'Ивенты':<10} {'Unique':<10} {'New':<10}")
    print("-"*80)
    
    for rank, (state, stats) in enumerate(sorted_states[:20], 1):
        points = stats['points']
        events_count = len(stats['events_set'])
        unique = len(stats['dancers_set'])
        new = len(stats['new_dancers_set'])
        
        print(f"{rank:<4} {state:<25} {points:>10,.0f}  {events_count:>8}  {unique:>8}  {new:>8}")
    
    print("="*80)
    print(f"Всего штатов с активностью: {len(sorted_states)}")

if __name__ == '__main__':
    calculate_top20_states()

