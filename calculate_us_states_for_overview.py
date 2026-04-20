#!/usr/bin/env python3
"""
Скрипт для расчета данных по американским штатам за 2024 и 2025 годы
для статьи overview - использует location_info.csv для правильного маппинга
"""

import csv
import os
import sys
from collections import defaultdict
from datetime import datetime

def load_csv_data():
    """Загружает данные из CSV файлов"""
    filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'
    filename_location = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/location_info.csv'
    
    if not os.path.exists(filename_points):
        print(f"❌ Файл не найден: {filename_points}")
        return None, None, None
    
    if not os.path.exists(filename_events):
        print(f"❌ Файл не найден: {filename_events}")
        return None, None, None
    
    if not os.path.exists(filename_location):
        print(f"❌ Файл не найден: {filename_location}")
        return None, None, None
    
    return filename_points, filename_events, filename_location

# Manual overrides
MANUAL_LOCATIONS = {
    'Scandinavian Open': 'Stockholm, Sweden',
    'Scandinavian Open WCS': 'Stockholm, Sweden',
    'Scandinavian Open WCS 2022': 'Stockholm, Sweden',
    'Scandinavian Open WCS "SNOW"': 'Stockholm, Sweden',
}

# Маппинг альтернативных названий событий
EVENT_NAME_MAPPING = {
    'Worlds UCWDC': 'UCWDC Country Dance World Championship',
}

# Специальные случаи для событий с неоднозначными локациями
# События, которые должны быть приписаны к определенному штату
SPECIAL_EVENT_STATES = {
    "Swingin' Into Spring": 'Massachusetts',  # Событие в Springfield, MA, но в location_info записано как CT
    "Swingin' Into Spring 2025": 'Massachusetts',
}

# Маппинг полных названий штатов на сокращения для отображения
STATE_NAMES = {
    'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
    'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'Florida': 'FL', 'Georgia': 'GA',
    'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL', 'Indiana': 'IN', 'Iowa': 'IA',
    'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA', 'Maine': 'ME', 'Maryland': 'MD',
    'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN', 'Mississippi': 'MS', 'Missouri': 'MO',
    'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV', 'New Hampshire': 'NH', 'New Jersey': 'NJ',
    'New Mexico': 'NM', 'New York': 'NY', 'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH',
    'Oklahoma': 'OK', 'Oregon': 'OR', 'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC',
    'South Dakota': 'SD', 'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT',
    'Virginia': 'VA', 'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY',
    'District of Columbia': 'DC'
}

def normalize_state_name(state):
    """Нормализует название штата к сокращению"""
    if not state:
        return state
    # Если уже сокращение (2 символа), возвращаем как есть
    if len(state) == 2:
        return state.upper()
    # Иначе ищем в маппинге
    return STATE_NAMES.get(state, state)

def calculate_us_states_stats():
    """Рассчитывает статистику по штатам США за 2024 и 2025 годы"""
    dancers_file, events_file, location_file = load_csv_data()
    
    if not dancers_file or not events_file or not location_file:
        return
    
    # 1. Загружаем location_info.csv для маппинга локаций к штатам
    location_info_map = {}
    try:
        with open(location_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                loc_str = row.get('event_location', '').strip()
                if loc_str:
                    location_info_map[loc_str.lower()] = {
                        'city': row.get('event_city', '').strip(),
                        'state': row.get('event_state', '').strip(),
                        'country': row.get('event_country', '').strip(),
                    }
                    # Добавить очищенную версию
                    loc_clean = ' '.join(loc_str.split()).lower()
                    if loc_clean != loc_str.lower():
                        location_info_map[loc_clean] = location_info_map[loc_str.lower()]
    except Exception as e:
        print(f"❌ Ошибка при чтении location_info.csv: {e}")
        return
    
    print(f"✅ Загружено {len(location_info_map)} локаций из location_info.csv")
    
    # 2. Build Event Location Map из events_wsdc.csv
    event_geo_map = {}
    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row['name'].strip()
                loc = row.get('location', '').strip()
                date_str = row.get('date', '').strip()
                
                if name and loc:
                    # Ищем локацию в location_info_map
                    loc_lower = loc.lower().strip()
                    loc_clean = ' '.join(loc.split()).lower()
                    
                    location_info = None
                    if loc_lower in location_info_map:
                        location_info = location_info_map[loc_lower]
                    elif loc_clean in location_info_map:
                        location_info = location_info_map[loc_clean]
                    else:
                        # Пробуем заменить полные названия штатов на сокращения
                        # Например: "Redmond, Oregon" -> "Redmond, OR"
                        loc_parts = [p.strip() for p in loc.split(',')]
                        if len(loc_parts) >= 2:
                            city = loc_parts[0]
                            state_or_country = loc_parts[1]
                            # Проверяем, является ли это полным названием штата
                            # STATE_NAMES: {'Alabama': 'AL', ...} -> обратный маппинг
                            state_full_to_abbr = {v: k for k, v in STATE_NAMES.items()}
                            # Но нам нужен маппинг полного названия -> сокращение
                            state_full_to_abbr_correct = STATE_NAMES  # {'Alabama': 'AL', 'Oregon': 'OR', ...}
                            if state_or_country in state_full_to_abbr_correct:
                                state_abbr = state_full_to_abbr_correct[state_or_country]
                                loc_with_abbr = f"{city}, {state_abbr}"
                                if len(loc_parts) >= 3:
                                    country = loc_parts[2]
                                    loc_with_abbr = f"{city}, {state_abbr}, {country}"
                                loc_with_abbr_lower = loc_with_abbr.lower()
                                if loc_with_abbr_lower in location_info_map:
                                    location_info = location_info_map[loc_with_abbr_lower]
                                else:
                                    loc_with_abbr_clean = ' '.join(loc_with_abbr.split()).lower()
                                    if loc_with_abbr_clean in location_info_map:
                                        location_info = location_info_map[loc_with_abbr_clean]
                    
                    if location_info and location_info['country']:
                        # Парсим дату для выбора самой поздней локации
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
                        
                        if name not in event_geo_map:
                            event_geo_map[name] = {
                                'city': location_info['city'],
                                'state': location_info['state'],
                                'country': location_info['country'],
                                'raw_loc': loc,
                                'date': event_date
                            }
                        else:
                            existing_date = event_geo_map[name].get('date')
                            if event_date and (not existing_date or event_date > existing_date):
                                event_geo_map[name] = {
                                    'city': location_info['city'],
                                    'state': location_info['state'],
                                    'country': location_info['country'],
                                    'raw_loc': loc,
                                    'date': event_date
                                }
    except Exception as e:
        print(f"❌ Ошибка при чтении events_wsdc.csv: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Добавляем manual overrides (используем простой парсинг для них)
    for name, loc_str in MANUAL_LOCATIONS.items():
        # Простой парсинг для manual overrides
        parts = [p.strip() for p in loc_str.split(',')]
        if len(parts) >= 2:
            city = parts[0]
            country = parts[-1]
            state = parts[1] if len(parts) > 2 else None
            if country:
                event_geo_map[name] = {
                    'city': city,
                    'state': state,
                    'country': country,
                    'raw_loc': loc_str
                }
    
    print(f"✅ Загружено {len(event_geo_map)} событий с локациями")
    
    # 3. Статистика по штатам за оба года
    stats_by_year = {
        '2024': defaultdict(lambda: {'points': 0, 'events': set()}),
        '2025': defaultdict(lambda: {'points': 0, 'events': set()})
    }
    
    # 4. Обрабатываем данные
    print("📊 Обрабатываем данные за 2024 и 2025 годы...")
    try:
        with open(dancers_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                year = row.get('event_year', '').strip()
                if year not in ['2024', '2025']:
                    continue
                
                if row.get('event_competition', '') not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
                    continue
                
                event_name = row['event_name']
                
                try:
                    points = int(float(row.get('event_points', '0') or '0'))
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
                if geo['country'] != 'United States':
                    continue
                
                # Проверяем специальные случаи
                if event_name in SPECIAL_EVENT_STATES:
                    state = normalize_state_name(SPECIAL_EVENT_STATES[event_name])
                elif geo['state']:
                    state = normalize_state_name(geo['state'])
                else:
                    continue
                
                # Обновляем статистику
                stats_by_year[year][state]['points'] += points
                stats_by_year[year][state]['events'].add(event_name)
    
    except Exception as e:
        print(f"❌ Ошибка при чтении dancers_results_info.csv: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Конвертируем sets в числа
    for year in ['2024', '2025']:
        for state in stats_by_year[year]:
            stats_by_year[year][state]['events'] = len(stats_by_year[year][state]['events'])
    
    # Сортируем по поинтам за 2025
    sorted_2025 = sorted(stats_by_year['2025'].items(), key=lambda x: x[1]['points'], reverse=True)
    
    # Выводим результаты
    print("\n" + "="*90)
    print("🏆 ТОП ШТАТОВ США ПО ПОИНТАМ (2025 vs 2024)")
    print("="*90)
    print(f"{'#':<4} {'Штат':<8} {'Поинты 2025':<15} {'Поинты 2024':<15} {'Изменение':<12} {'Рост':<10}")
    print("-"*90)
    
    results = []
    for rank, (state, stats_2025) in enumerate(sorted_2025[:10], 1):  # Топ-10 для статьи
        points_2025 = stats_2025['points']
        points_2024 = stats_by_year['2024'][state]['points']
        
        change = points_2025 - points_2024
        if points_2024 > 0:
            growth_pct = ((points_2025 - points_2024) / points_2024) * 100
            growth_str = f"{growth_pct:+.1f}%"
        else:
            growth_pct = 0
            growth_str = "N/A"
        
        print(f"{rank:<4} {state:<8} {points_2025:>12,.0f}  {points_2024:>12,.0f}  {change:>+10,.0f}  {growth_str:>10}")
        
        results.append({
            'state': state,
            'points_2025': points_2025,
            'points_2024': points_2024,
            'change': change,
            'growth_pct': growth_pct
        })
    
    print("="*90)
    
    # Находим максимальное значение для расчета процентов ширины баров
    max_points_2025 = max([r['points_2025'] for r in results]) if results else 1
    
    print("\n📊 Данные для HTML статьи:")
    print(f"Max points 2025: {max_points_2025}")
    print("\nHTML для bar chart:")
    for r in results:
        width_pct = (r['points_2025'] / max_points_2025) * 100
        growth_class = "negative" if r['growth_pct'] < 0 else ""
        growth_display = f"({r['growth_pct']:+.1f}%)" if r['growth_pct'] != 0 else "(N/A)"
        
        print(f"""                        <div class="bar-row">
                            <div class="bar-label">{r['state']}</div>
                            <div class="bar-container">
                                <div class="bar-fill-2025" style="width: {width_pct:.1f}%"></div>
                            </div>
                            <div class="bar-value"><span class="bar-value-primary">{r['points_2025']:,}</span> <span class="bar-value-secondary">/ {r['points_2024']:,}</span> <span class="bar-value-percent {growth_class}">{growth_display}</span></div>
                        </div>""")
    
    return results, max_points_2025

if __name__ == '__main__':
    calculate_us_states_stats()
