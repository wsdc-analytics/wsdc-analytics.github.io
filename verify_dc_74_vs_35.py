#!/usr/bin/env python3
"""
Проверяем, почему в статье 74, а расчет показывает 35
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
print("ПРОВЕРКА РАЗНЫХ ЛОГИК")
print("="*80)

# ЛОГИКА 1: Как в get_geo_stats.py (только skill level, глобальные первые поинты)
print("\n📊 ЛОГИКА 1: get_geo_stats.py (только skill level, глобальные первые поинты)")

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

dc_new_method1 = set()
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        dancer_id = row['dancer_id']
        if dancer_first_year.get(dancer_id) != 2025:
            continue
        
        event_name = row['event_name']
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        if not geo:
            geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if geo and geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['DC', 'DISTRICT OF COLUMBIA']:
            dc_new_method1.add(dancer_id)

print(f"  Новых в DC: {len(dc_new_method1)}")

# ЛОГИКА 2: Правильная логика (все номинации, первые поинты вообще, локация первых поинтов)
print("\n📊 ЛОГИКА 2: Правильная логика (все номинации, первые поинты вообще, локация первых поинтов)")

dancer_first_year_all = {}
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        if dancer_id not in dancer_first_year_all or year < dancer_first_year_all[dancer_id]:
            dancer_first_year_all[dancer_id] = year

new_dancers_2025 = {d for d, y in dancer_first_year_all.items() if y == 2025}

dancer_first_dc_event = {}  # dancer_id -> month первого поинта в DC в 2025

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        
        dancer_id = row['dancer_id']
        if dancer_id not in new_dancers_2025:
            continue
        
        try:
            points = int(row['event_points'])
        except:
            points = 0
        if points <= 0:
            continue
        
        event_name = row['event_name']
        month = int(row.get('event_month', 1))
        
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        if not geo:
            geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if geo and geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['DC', 'DISTRICT OF COLUMBIA']:
            if dancer_id not in dancer_first_dc_event or month < dancer_first_dc_event[dancer_id]:
                dancer_first_dc_event[dancer_id] = month

# Проверяем, для скольких из новых танцоров DC был местом первых поинтов
dc_new_method2 = set()
for dancer_id in new_dancers_2025:
    # Находим локацию первых поинтов этого танцора в 2025
    first_month = 13
    first_location = None
    
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['event_year'] != '2025' or r['dancer_id'] != dancer_id:
                continue
            if r['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
                continue
            try:
                p = int(r['event_points'])
                if p <= 0:
                    continue
            except:
                continue
            
            m = int(r.get('event_month', 1))
            if m < first_month:
                first_month = m
                event_name = r['event_name']
                mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
                geo = event_geo_map.get(mapped_name)
                if not geo:
                    geo = event_geo_map.get(event_name)
                if not geo:
                    clean_name = event_name.split(' 20')[0].strip()
                    geo = event_geo_map.get(clean_name)
                
                if geo:
                    if geo['country'] == 'United States' and geo['state']:
                        first_location = geo['state']
    
    if first_location and first_location.upper() in ['DC', 'DISTRICT OF COLUMBIA']:
        dc_new_method2.add(dancer_id)

print(f"  Новых в DC (где DC - место первых поинтов): {len(dc_new_method2)}")

print(f"\n📊 СРАВНЕНИЕ:")
print(f"  Метод 1 (get_geo_stats.py логика): {len(dc_new_method1)}")
print(f"  Метод 2 (правильная логика): {len(dc_new_method2)}")
print(f"  В статье: 74")

