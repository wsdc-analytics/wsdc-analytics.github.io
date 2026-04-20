#!/usr/bin/env python3
"""
Детальный анализ расхождений по Флориде между расчетами
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

MANUAL_LOCATIONS = {
    'Scandinavian Open': 'Stockholm, Sweden',
    'Scandinavian Open WCS': 'Stockholm, Sweden',
    'Scandinavian Open WCS 2022': 'Stockholm, Sweden',
    'Scandinavian Open WCS "SNOW"': 'Stockholm, Sweden',
}

filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

# 1. Build Event Location Map
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

print(f"✅ Загружено {len(event_geo_map)} событий с локациями\n")

# 2. Находим все события во Флориде
florida_events = {}
for event_name, geo in event_geo_map.items():
    if geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['FL', 'FLORIDA']:
        florida_events[event_name] = geo

print(f"📍 События во Флориде (2025): {len(florida_events)}")
for event_name, geo in sorted(florida_events.items()):
    print(f"   - {event_name}: {geo['city']}, {geo['state']}")

# 3. Подсчитываем поинты по событиям
event_stats = defaultdict(lambda: {'points': 0, 'count': 0, 'rows': []})
total_points = 0
total_rows = 0
rows_with_zero = 0
rows_excluded_competition = 0

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        event_name = row['event_name']
        competition = row['event_competition']
        
        # Проверяем competition
        if competition not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            rows_excluded_competition += 1
            continue
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        # Проверяем, что это Флорида
        if geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['FL', 'FLORIDA']:
            try:
                points = int(row['event_points'])
            except:
                points = 0
            
            total_rows += 1
            
            if points <= 0:
                rows_with_zero += 1
                continue
            
            event_stats[event_name]['points'] += points
            event_stats[event_name]['count'] += 1
            event_stats[event_name]['rows'].append({
                'dancer_id': row['dancer_id'],
                'points': points,
                'competition': competition
            })
            total_points += points

print(f"\n📊 ДЕТАЛЬНАЯ СТАТИСТИКА ПО ФЛОРИДЕ:")
print(f"{'='*80}")
print(f"Всего строк для Флориды: {total_rows}")
print(f"Строк с points <= 0: {rows_with_zero}")
print(f"Строк с неподходящим competition (не учтено): {rows_excluded_competition}")
print(f"Итого поинтов (исключая нули): {total_points:,}")
print(f"{'='*80}\n")

print(f"{'Событие':<50} {'Поинты':<10} {'Записей':<10}")
print("-"*80)
for event_name in sorted(florida_events.keys()):
    if event_name in event_stats:
        stats = event_stats[event_name]
        print(f"{event_name:<50} {stats['points']:>8,}  {stats['count']:>8}")
    else:
        print(f"{event_name:<50} {'0':>8}  {'0':>8}")

print(f"\n{'ИТОГО':<50} {total_points:>8,}  {sum(s['count'] for s in event_stats.values()):>8}")

# 4. Проверяем, есть ли события во Флориде, которые не в списке
print(f"\n🔍 Проверка событий, которые могут быть во Флориде, но не найдены:")
for event_name in event_stats:
    if event_name not in florida_events:
        geo = event_geo_map.get(event_name)
        if geo:
            print(f"   ⚠️  {event_name}: {geo['raw_loc']} (country: {geo['country']}, state: {geo['state']})")

