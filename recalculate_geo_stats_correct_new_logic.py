#!/usr/bin/env python3
"""
Пересчет статистики с правильной логикой для новых танцоров:
1. Танцор получил первые поинты ВООБЩЕ в 2025 (не было в базе ранее)
2. Определяем локацию (город/штат), где он получил ПЕРВЫЕ поинты в 2025
3. Он считается "новым" ТОЛЬКО для этой локации
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

MANUAL_LOCATIONS = {
    'Scandinavian Open': 'Stockholm, Sweden',
    'Scandinavian Open WCS': 'Stockholm, Sweden',
    'Scandinavian Open WCS 2022': 'Stockholm, Sweden',
    'Scandinavian Open WCS "SNOW"': 'Stockholm, Sweden',
}

EVENT_NAME_MAPPING = {
    'Worlds UCWDC': 'UCWDC Country Dance World Championship',
}

REGION_MAP = {
    'United States': 'North America',
    'Canada': 'North America',
    'Mexico': 'North America',
    'United Kingdom': 'Europe',
    'France': 'Europe',
    'Germany': 'Europe',
    'Russia': 'Europe',
    'Poland': 'Europe',
    'Hungary': 'Europe',
    'Sweden': 'Europe',
    'Finland': 'Europe',
    'Norway': 'Europe',
    'Austria': 'Europe',
    'Switzerland': 'Europe',
    'Netherlands': 'Europe',
    'Belgium': 'Europe',
    'Italy': 'Europe',
    'Spain': 'Europe',
    'Czech Republic': 'Europe',
    'Ukraine': 'Europe',
    'Estonia': 'Europe',
    'Latvia': 'Europe',
    'Lithuania': 'Europe',
    'Romania': 'Europe',
    'Ireland': 'Europe',
    'Portugal': 'Europe',
    'Bulgaria': 'Europe',
    'Slovenia': 'Europe',
    'Belarus': 'Europe',
    'Australia': 'Oceania',
    'New Zealand': 'Oceania',
    'Singapore': 'Asia',
    'South Korea': 'Asia',
    'Malaysia': 'Asia',
    'Japan': 'Asia',
    'China': 'Asia',
    'Taiwan': 'Asia',
    'Israel': 'Asia',
    'Turkey': 'Europe',
    'Brazil': 'South America',
    'Argentina': 'South America',
}

# 1. Build Event Location Map
event_geo_map = {}
try:
    with open(filename_events, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip()
            loc = row.get('location', '').strip()
            if name and loc:
                city, state, country = normalize_location(loc)
                if country:
                    event_geo_map[name] = {
                        'city': city,
                        'state': state,
                        'country': country,
                        'raw_loc': loc
                    }
except FileNotFoundError:
    print(f"Error: {filename_events} not found.")
    exit(1)

for name, loc_str in MANUAL_LOCATIONS.items():
    city, state, country = normalize_location(loc_str)
    event_geo_map[name] = {
        'city': city,
        'state': state,
        'country': country,
        'raw_loc': loc_str
    }

# 2. Data Structures
stats_country = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
})

stats_state = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
})

stats_city = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set(),
    'country': '', 'display_name': ''
})

stats_region = defaultdict(lambda: {
    'points': 0, 'events_set': set(), 'dancers_set': set(), 'new_dancers_set': set()
})

# 3. Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025
# (включая все номинации: skill level + Sophisticated + Masters)
print("📊 Шаг 1: Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025...")
dancer_first_year_ever = {}

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        # Включаем ВСЕ номинации
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        if dancer_id not in dancer_first_year_ever or year < dancer_first_year_ever[dancer_id]:
            dancer_first_year_ever[dancer_id] = year

new_dancers_2025_global = {d for d, y in dancer_first_year_ever.items() if y == 2025}
print(f"  Танцоров, которые получили первые поинты ВООБЩЕ в 2025: {len(new_dancers_2025_global)}")

# 4. Для каждого нового танцора определяем локацию ПЕРВЫХ поинтов в 2025
print("📊 Шаг 2: Определяем локацию ПЕРВЫХ поинтов для новых танцоров...")
dancer_first_city = {}  # dancer_id -> {'city_key': ..., 'month': ...}
dancer_first_state = {}  # dancer_id -> {'state': ..., 'month': ...}
dancer_first_country = {}  # dancer_id -> {'country': ..., 'month': ...}

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        # Включаем ВСЕ номинации
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        
        dancer_id = row['dancer_id']
        if dancer_id not in new_dancers_2025_global:
            continue
        
        try:
            points = int(row['event_points'])
        except:
            points = 0
        
        if points <= 0:
            continue
        
        event_name = row['event_name']
        month = int(row.get('event_month', 1))
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        city = geo['city']
        state = geo['state']
        country = geo['country']
        
        # Запоминаем локацию первых поинтов (по самому раннему месяцу)
        if dancer_id not in dancer_first_city:
            dancer_first_city[dancer_id] = {'city_key': None, 'month': 13}
        if dancer_id not in dancer_first_state:
            dancer_first_state[dancer_id] = {'state': None, 'month': 13}
        if dancer_id not in dancer_first_country:
            dancer_first_country[dancer_id] = {'country': None, 'month': 13}
        
        if month < dancer_first_city[dancer_id]['month']:
            if city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                dancer_first_city[dancer_id] = {'city_key': city_key, 'month': month}
        
        if month < dancer_first_state[dancer_id]['month']:
            if country == 'United States' and state:
                dancer_first_state[dancer_id] = {'state': state, 'month': month}
        
        if month < dancer_first_country[dancer_id]['month']:
            if country:
                dancer_first_country[dancer_id] = {'country': country, 'month': month}

print(f"  Определено локаций для {len(dancer_first_city)} танцоров")

# 5. Обрабатываем данные за 2025 и подсчитываем статистику
print("📊 Шаг 3: Обрабатываем данные за 2025 и подсчитываем статистику...")

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        # Обрабатываем только skill-level для подсчета поинтов и статистики
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue

        event_name = row['event_name']
        dancer_id = row['dancer_id']
        points = int(row['event_points'])
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
            
        if not geo:
            continue

        city = geo['city']
        state = geo['state']
        country = geo['country']
        
        region = REGION_MAP.get(country, 'Other')
        
        # Проверяем, является ли танцор новым для этой локации
        # Важно: проверяем по локации первых поинтов (которые могли быть в любой номинации)
        is_new_for_city = False
        is_new_for_state = False
        is_new_for_country = False
        
        if dancer_id in new_dancers_2025_global:
            # Проверяем, является ли это локацией первых поинтов (любая номинация)
            if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if city_key == dancer_first_city[dancer_id]['city_key']:
                    is_new_for_city = True
            
            if dancer_id in dancer_first_state and dancer_first_state[dancer_id]['state']:
                if country == 'United States' and state == dancer_first_state[dancer_id]['state']:
                    is_new_for_state = True
            
            if dancer_id in dancer_first_country and dancer_first_country[dancer_id]['country']:
                if country == dancer_first_country[dancer_id]['country']:
                    is_new_for_country = True

        # Update Helpers
        def update_stats(d, key, pts, did, is_new, extra_meta=None):
            d[key]['points'] += pts
            d[key]['events_set'].add(event_name)
            d[key]['dancers_set'].add(did)
            if is_new:
                d[key]['new_dancers_set'].add(did)
            if extra_meta:
                for k, v in extra_meta.items():
                    d[key][k] = v

        update_stats(stats_country, country, points, dancer_id, is_new_for_country)
        update_stats(stats_region, region, points, dancer_id, is_new_for_country)
        
        if country == 'United States' and state:
            update_stats(stats_state, state, points, dancer_id, is_new_for_state)
            
        city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
        update_stats(stats_city, city_key, points, dancer_id, is_new_for_city, 
                     {'display_name': city_key, 'country': country})

# 5.5. Добавляем новых танцоров, которые получили первые поинты в любых номинациях
# (включая Sophisticated/Masters на UCWDC и других ивентах)
print("📊 Шаг 4.5: Добавляем новых танцоров из всех номинаций...")
for dancer_id in new_dancers_2025_global:
    if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
        city_key = dancer_first_city[dancer_id]['city_key']
        # Добавляем этого танцора как нового для этого города
        if city_key not in stats_city:
            stats_city[city_key] = {
                'points': 0, 
                'events_set': set(), 
                'dancers_set': set(), 
                'new_dancers_set': set(),
                'display_name': city_key,
                'country': city_key.split(', ')[-1] if ', ' in city_key else ''
            }
        stats_city[city_key]['new_dancers_set'].add(dancer_id)
    
    if dancer_id in dancer_first_state and dancer_first_state[dancer_id]['state']:
        state = dancer_first_state[dancer_id]['state']
        if state not in stats_state:
            stats_state[state] = {
                'points': 0,
                'events_set': set(),
                'dancers_set': set(),
                'new_dancers_set': set()
            }
        stats_state[state]['new_dancers_set'].add(dancer_id)
    
    if dancer_id in dancer_first_country and dancer_first_country[dancer_id]['country']:
        country = dancer_first_country[dancer_id]['country']
        if country not in stats_country:
            stats_country[country] = {
                'points': 0,
                'events_set': set(),
                'dancers_set': set(),
                'new_dancers_set': set()
            }
        stats_country[country]['new_dancers_set'].add(dancer_id)

# 6. Выводим результаты
def print_table(stats_dict, label, top_n=200):
    output = []
    for key, data in stats_dict.items():
        output.append({
            'name': key if 'display_name' not in data else data['display_name'],
            'points': data['points'],
            'events': len(data['events_set']),
            'dancers': len(data['dancers_set']),
            'new_dancers': len(data['new_dancers_set']),
            'country': data.get('country', '')
        })
    
    output.sort(key=lambda x: x['points'], reverse=True)
    
    print(f"\n=== {label} (Sorted by Points) ===")
    print(f"{'#':<3} | {'Name':<35} | {'Events':<6} | {'Points':<8} | {'Dancers':<8} | {'New'}")
    print("-" * 90)
    for i, row in enumerate(output[:top_n], 1):
         print(f"{i:<3} | {row['name']:<35} | {row['events']:<6} | {row['points']:<8} | {row['dancers']:<8} | {row['new_dancers']}")
    return output

print_table(stats_city, "GLOBAL TOP CITIES", 10)
print("\n" + "="*80)
print_table(stats_state, "US STATES", 10)
print("\n" + "="*80)
print_table(stats_country, "ALL COUNTRIES", 10)

# Специально для DC
print("\n" + "="*80)
print("ПРОВЕРКА ДЛЯ DC:")
print("="*80)
for city_key, data in stats_city.items():
    if 'Washington' in city_key and ('DC' in city_key or 'District of Columbia' in city_key):
        print(f"Город: {city_key}")
        print(f"  Поинты: {data['points']}")
        print(f"  Уникальных: {len(data['dancers_set'])}")
        print(f"  Новых: {len(data['new_dancers_set'])}")

for state, data in stats_state.items():
    if state.upper() in ['DC', 'DISTRICT OF COLUMBIA']:
        print(f"\nШтат: {state}")
        print(f"  Поинты: {data['points']}")
        print(f"  Уникальных: {len(data['dancers_set'])}")
        print(f"  Новых: {len(data['new_dancers_set'])}")

