#!/usr/bin/env python3
"""
Детальный анализ новых танцоров для Phoenix по ивентам
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

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
                event_geo_map[name] = {'city': city, 'state': state, 'country': country}

# 1. Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025
dancer_first_year_ever = {}
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        if dancer_id not in dancer_first_year_ever or year < dancer_first_year_ever[dancer_id]:
            dancer_first_year_ever[dancer_id] = year

new_dancers_2025_global = {d for d, y in dancer_first_year_ever.items() if y == 2025}

# 2. Определяем локацию ПЕРВЫХ поинтов для новых танцоров
dancer_first_city = {}

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        if dancer_id not in new_dancers_2025_global:
            continue
        try:
            points = int(row['event_points'])
            if points <= 0:
                continue
        except:
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
        
        if dancer_id not in dancer_first_city:
            dancer_first_city[dancer_id] = {'city_key': None, 'month': 13, 'event': None}
        
        if month < dancer_first_city[dancer_id]['month']:
            if city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                dancer_first_city[dancer_id] = {
                    'city_key': city_key,
                    'month': month,
                    'event': event_name
                }

# 3. Анализируем Phoenix
print("="*80)
print("АНАЛИЗ PHOENIX, AZ - НОВЫЕ ТАНЦОРЫ")
print("="*80)

phoenix_key = "Phoenix, AZ, United States"

# Собираем статистику по ивентам
events_stats = defaultdict(lambda: {
    'total_dancers': set(),
    'new_dancers': set(),
    'points': 0
})

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if geo and geo['city'] == 'Phoenix' and geo['state'] == 'AZ':
            dancer_id = row['dancer_id']
            events_stats[event_name]['total_dancers'].add(dancer_id)
            try:
                points = int(row['event_points'])
                events_stats[event_name]['points'] += points
            except:
                pass
            
            # Проверяем, является ли это первыми поинтами для этого танцора
            if dancer_id in dancer_first_city:
                first_city_key = dancer_first_city[dancer_id]['city_key']
                first_event = dancer_first_city[dancer_id]['event']
                if first_city_key == phoenix_key and first_event == event_name:
                    events_stats[event_name]['new_dancers'].add(dancer_id)

print(f"\n📊 ИВЕНТЫ В PHOENIX, AZ В 2025:")
total_new = set()
for event_name, stats in sorted(events_stats.items()):
    total_new.update(stats['new_dancers'])
    print(f"\n{event_name}:")
    print(f"  Всего танцоров: {len(stats['total_dancers'])}")
    print(f"  Новых (первые поинты здесь): {len(stats['new_dancers'])}")
    print(f"  Поинтов: {stats['points']}")

print(f"\n" + "="*80)
print(f"ИТОГО новых танцоров для Phoenix: {len(total_new)}")
print("="*80)
