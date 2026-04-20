#!/usr/bin/env python3
"""
Проверяем, почему Worlds UCWDC попадает во Флориду вместо Аризоны
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

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
                # Проверяем, если это Worlds UCWDC
                if 'UCWDC' in name or 'Worlds' in name:
                    print(f"Событие: {name}")
                    print(f"  Локация в CSV: {loc}")
                    print(f"  Нормализовано: city={city}, state={state}, country={country}")
                
                event_geo_map[name] = {
                    'city': city,
                    'state': state,
                    'country': country,
                    'raw_loc': loc
                }

print("\n" + "="*80)
print("ПРОВЕРКА ДАННЫХ ЗА 2025 ГОД")
print("="*80)

# Проверяем, как определяется локация для Worlds UCWDC за 2025 год
ucwdc_count_by_state = defaultdict(int)
ucwdc_points_by_state = defaultdict(int)

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        
        if 'UCWDC' not in event_name and 'Worlds' not in event_name:
            continue
        
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
            if geo and ('UCWDC' in event_name or 'Worlds' in event_name):
                print(f"\n⚠️  Событие в dancers_results_info: '{event_name}'")
                print(f"   После очистки: '{clean_name}'")
                print(f"   Найдена гео: city={geo['city']}, state={geo['state']}, country={geo['country']}")
        
        if geo:
            state_key = geo['state'] if geo['state'] else 'Unknown'
            ucwdc_count_by_state[state_key] += 1
            ucwdc_points_by_state[state_key] += points

print(f"\n📊 Распределение Worlds UCWDC по штатам в 2025 году:")
print("-"*80)
for state in sorted(ucwdc_count_by_state.keys()):
    print(f"  {state}: {ucwdc_count_by_state[state]} записей, {ucwdc_points_by_state[state]:,} поинтов")

# Проверяем, какие именно названия событий встречаются
print(f"\n🔍 Все уникальные названия событий с UCWDC за 2025:")
unique_ucwdc_names = set()
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] == '2025' and ('UCWDC' in row['event_name'] or ('Worlds' in row['event_name'] and 'UCWDC' in row['event_name'])):
            unique_ucwdc_names.add(row['event_name'])

for name in sorted(unique_ucwdc_names):
    print(f"  - {name}")

