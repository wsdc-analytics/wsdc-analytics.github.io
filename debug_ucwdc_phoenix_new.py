#!/usr/bin/env python3
"""
Проверка новых танцоров на UCWDC в Phoenix
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

# 1. Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025 (ВСЕ номинации)
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

# 2. Определяем локацию ПЕРВЫХ поинтов для новых танцоров (ВСЕ номинации)
dancer_first_city = {}

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
            if points <= 0:
                continue
        except:
            continue
        
        event_name = row['event_name']
        month = int(row.get('event_month', 1))
        
        # Проверяем маппинг
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

# 3. Анализируем UCWDC в Phoenix
print("="*80)
print("АНАЛИЗ UCWDC В PHOENIX - НОВЫЕ ТАНЦОРЫ")
print("="*80)

phoenix_key = "Phoenix, AZ, United States"
ucwdc_events = ['UCWDC Country Dance World Championship', 'Worlds UCWDC']

ucwdc_new_dancers = set()
ucwdc_all_dancers = set()

for ucwdc_name in ucwdc_events:
    mapped_name = EVENT_NAME_MAPPING.get(ucwdc_name, ucwdc_name)
    
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['event_year'] != '2025':
                continue
            
            event_name = row['event_name']
            # Проверяем маппинг
            if event_name != ucwdc_name and event_name != mapped_name:
                continue
            
            # Проверяем локацию
            geo = event_geo_map.get(event_name)
            if not geo:
                clean_name = event_name.split(' 20')[0].strip()
                geo = event_geo_map.get(clean_name)
            
            if geo and geo['city'] == 'Phoenix' and geo['state'] == 'AZ':
                dancer_id = row['dancer_id']
                ucwdc_all_dancers.add(dancer_id)
                
                # Проверяем, является ли это первыми поинтами для этого танцора в Phoenix
                if dancer_id in dancer_first_city:
                    first_city_key = dancer_first_city[dancer_id]['city_key']
                    first_event = dancer_first_city[dancer_id]['event']
                    
                    if first_city_key == phoenix_key and (first_event == ucwdc_name or first_event == mapped_name):
                        ucwdc_new_dancers.add(dancer_id)

print(f"\nНовых танцоров, получивших первые поинты ВООБЩЕ в 2025 на UCWDC в Phoenix: {len(ucwdc_new_dancers)}")
print(f"Всего танцоров на UCWDC в Phoenix: {len(ucwdc_all_dancers)}")

if len(ucwdc_new_dancers) > 0:
    print(f"\nID новых танцоров: {sorted(list(ucwdc_new_dancers))}")

# 4. Проверяем все ивенты в Phoenix с учетом UCWDC
print("\n" + "="*80)
print("РАЗБИВКА ПО ВСЕМ ИВЕНТАМ В PHOENIX (включая UCWDC):")
print("="*80)

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
        # Включаем ВСЕ номинации для подсчета новых
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        
        event_name = row['event_name']
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        if not geo:
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
            
            # Проверяем, является ли это первыми поинтами для этого танцора в Phoenix
            if dancer_id in dancer_first_city:
                first_city_key = dancer_first_city[dancer_id]['city_key']
                first_event = dancer_first_city[dancer_id]['event']
                
                if first_city_key == phoenix_key and first_event == event_name:
                    events_stats[event_name]['new_dancers'].add(dancer_id)

total_new_all = set()
for event_name, stats in sorted(events_stats.items()):
    total_new_all.update(stats['new_dancers'])
    print(f"\n{event_name}:")
    print(f"  Всего танцоров: {len(stats['total_dancers'])}")
    print(f"  Новых (первые поинты здесь): {len(stats['new_dancers'])}")
    print(f"  Поинтов: {stats['points']}")

print(f"\n" + "="*80)
print(f"ИТОГО новых танцоров для Phoenix (включая UCWDC): {len(total_new_all)}")
print("="*80)

