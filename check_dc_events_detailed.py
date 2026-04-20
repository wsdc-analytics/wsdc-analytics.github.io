#!/usr/bin/env python3
"""
Детальная проверка событий и танцоров в DC для понимания расхождения
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

# Build Event Location Map
event_geo_map = {}
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

for name, loc_str in MANUAL_LOCATIONS.items():
    city, state, country = normalize_location(loc_str)
    event_geo_map[name] = {
        'city': city,
        'state': state,
        'country': country,
        'raw_loc': loc_str
    }

print("="*80)
print("ПРОВЕРКА СОБЫТИЙ В DC ЗА 2025 ГОД")
print("="*80)

dc_events = {}
all_dancers_in_dc = set()

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        
        if not geo:
            geo = event_geo_map.get(event_name)
        
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        city = geo['city']
        state = geo['state']
        country = geo['country']
        
        # Проверяем, это DC?
        is_dc = (state and state.upper() in ['DC', 'DISTRICT OF COLUMBIA'])
        
        if is_dc:
            dancer_id = row['dancer_id']
            all_dancers_in_dc.add(dancer_id)
            
            if event_name not in dc_events:
                dc_events[event_name] = {
                    'city': city,
                    'state': state,
                    'raw_loc': geo['raw_loc'],
                    'dancers': set(),
                    'points': 0
                }
            
            try:
                points = int(row['event_points'])
            except:
                points = 0
            
            if points > 0:
                dc_events[event_name]['dancers'].add(dancer_id)
                dc_events[event_name]['points'] += points

print(f"\n📍 Все события в DC за 2025 год ({len(dc_events)}):")
for event_name, data in sorted(dc_events.items()):
    print(f"\n  {event_name}")
    print(f"    Локация: {data['raw_loc']}")
    print(f"    Город: {data['city']}, Штат: {data['state']}")
    print(f"    Уникальных танцоров: {len(data['dancers'])}")
    print(f"    Поинтов: {data['points']:,}")

print(f"\n📊 Общая статистика:")
print(f"  Всего уникальных танцоров в DC: {len(all_dancers_in_dc)}")

# Проверяем, есть ли события, где city не Washington
print(f"\n🔍 Проверяем города в DC:")
cities_in_dc = set()
for event_name, data in dc_events.items():
    cities_in_dc.add(data['city'])
    print(f"  {event_name}: город = '{data['city']}'")

print(f"\n  Все города в DC: {sorted(cities_in_dc)}")

# Проверяем логику из get_geo_stats.py - глобальные первые поинты
print(f"\n" + "="*80)
print("ЛОГИКА ИЗ get_geo_stats.py (глобальные первые поинты в 2025)")
print("="*80)

dancer_first_year = {}
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        if dancer_id not in dancer_first_year or year < dancer_first_year[dancer_id]:
            dancer_first_year[dancer_id] = year

dc_new_global = set()
for dancer_id in all_dancers_in_dc:
    if dancer_first_year.get(dancer_id) == 2025:
        dc_new_global.add(dancer_id)

print(f"Новых танцоров в DC (глобальная логика, первые поинты вообще): {len(dc_new_global)}")

