#!/usr/bin/env python3
"""
Сравнение двух подходов к расчету поинтов Флориды
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

print("="*80)
print("МЕТОД 1: С фильтрацией points <= 0 (мой подход)")
print("="*80)

fl_points_method1 = 0
fl_events_method1 = set()
fl_rows_method1 = 0

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
        
        # МОЙ ПОДХОД: фильтруем points <= 0
        if points <= 0:
            continue
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        if geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['FL', 'FLORIDA']:
            fl_points_method1 += points
            fl_events_method1.add(event_name)
            fl_rows_method1 += 1

print(f"Поинты: {fl_points_method1:,}")
print(f"Ивенты: {len(fl_events_method1)}")
print(f"Записей: {fl_rows_method1}")

print("\n" + "="*80)
print("МЕТОД 2: Без фильтрации points <= 0 (как в get_geo_stats.py)")
print("="*80)

fl_points_method2 = 0
fl_events_method2 = set()
fl_rows_method2 = 0

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        points = int(row['event_points'])  # Без проверки на <= 0
        
        geo = event_geo_map.get(event_name)
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if not geo:
            continue
        
        if geo['country'] == 'United States' and geo['state'] and geo['state'].upper() in ['FL', 'FLORIDA']:
            fl_points_method2 += points
            fl_events_method2.add(event_name)
            fl_rows_method2 += 1

print(f"Поинты: {fl_points_method2:,}")
print(f"Ивенты: {len(fl_events_method2)}")
print(f"Записей: {fl_rows_method2}")

print("\n" + "="*80)
print("СРАВНЕНИЕ")
print("="*80)
print(f"Разница в поинтах: {fl_points_method1 - fl_points_method2:,}")
print(f"Разница в записях: {fl_rows_method1 - fl_rows_method2}")

print(f"\nОжидаемое значение из статьи: 1,741")
print(f"Метод 1 (с фильтрацией): {fl_points_method1:,} (разница: {fl_points_method1 - 1741})")
print(f"Метод 2 (без фильтрации): {fl_points_method2:,} (разница: {fl_points_method2 - 1741})")

# Проверяем, какие события есть в одном методе, но нет в другом
events_only_in_method1 = fl_events_method1 - fl_events_method2
events_only_in_method2 = fl_events_method2 - fl_events_method1

if events_only_in_method1:
    print(f"\n⚠️  События только в методе 1: {events_only_in_method1}")
if events_only_in_method2:
    print(f"⚠️  События только в методе 2: {events_only_in_method2}")

