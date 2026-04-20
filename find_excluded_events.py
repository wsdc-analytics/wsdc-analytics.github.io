#!/usr/bin/env python3
"""
Ищем события, которые могут быть исключены из расчета
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

# Подсчитываем поинты по событиям во Флориде
event_points = defaultdict(int)

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        try:
            points = int(row['event_points'])
        except:
            points = 0
        
        if points <= 0:
            continue
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        if geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['FL', 'FLORIDA']:
            event_points[event_name] += points

print("События во Флориде с поинтами (отсортировано по поинтам):")
print("="*80)
print(f"{'Событие':<60} {'Поинты':<10}")
print("-"*80)

sorted_events = sorted(event_points.items(), key=lambda x: x[1], reverse=True)
for event_name, points in sorted_events:
    print(f"{event_name:<60} {points:>8,}")

total = sum(event_points.values())
print("-"*80)
print(f"{'ИТОГО':<60} {total:>8,}")

print(f"\n🔍 Ищем события с 143 поинтами или близкими к этому:")
target_diff = 143
for event_name, points in sorted_events:
    if abs(points - target_diff) <= 5:
        print(f"   ⚠️  {event_name}: {points} поинтов (разница от {target_diff} = {points - target_diff})")

print(f"\n📊 Проверяем, если исключить 'Worlds UCWDC' (143 поинта):")
worlds_points = event_points.get('Worlds UCWDC', 0)
new_total = total - worlds_points
print(f"   Было: {total:,}")
print(f"   Минус Worlds UCWDC: {worlds_points}")
print(f"   Станет: {new_total:,}")
print(f"   Разница с ожидаемым (1,741): {new_total - 1741}")

