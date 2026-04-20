#!/usr/bin/env python3
"""
Правильная логика для новых участников:
1. Танцор получил первые поинты ВООБЩЕ в 2025 году (не было в базе ранее)
2. Определяем город/штат, где он получил ПЕРВЫЕ поинты в 2025
3. Он считается "новым" ТОЛЬКО для этого города/штата
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
print("ПРАВИЛЬНАЯ ЛОГИКА: Первые поинты ВООБЩЕ в 2025 году")
print("="*80)

# 1. Находим всех танцоров, которые получили первые поинты ВООБЩЕ в 2025
# (их не было в базе до 2025)
print("\n📊 Шаг 1: Определяем танцоров, которые получили первые поинты ВООБЩЕ в 2025...")

dancer_first_year_ever = {}  # dancer_id -> первый год вообще
dancer_first_event_2025 = {}  # dancer_id -> (event_name, month) первого поинта в 2025

# Сканируем всю историю для определения первого года вообще
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        month = int(row.get('event_month', 1))
        
        # Определяем первый год вообще
        if dancer_id not in dancer_first_year_ever or year < dancer_first_year_ever[dancer_id]:
            dancer_first_year_ever[dancer_id] = year

# Находим танцоров, которые получили первые поинты ВООБЩЕ в 2025
new_dancers_2025_global = set()
for dancer_id, first_year in dancer_first_year_ever.items():
    if first_year == 2025:
        new_dancers_2025_global.add(dancer_id)

print(f"  Танцоров, которые получили первые поинты ВООБЩЕ в 2025: {len(new_dancers_2025_global)}")

# 2. Для каждого нового танцора определяем локацию его ПЕРВЫХ поинтов в 2025
print("\n📊 Шаг 2: Определяем локацию ПЕРВЫХ поинтов для новых танцоров в 2025...")

dancer_first_city = {}  # dancer_id -> city_key (город первого поинта в 2025)
dancer_first_state = {}  # dancer_id -> state (штат первого поинта в 2025)

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        # Проверяем все номинации (включая Sophisticated, Masters)
        competition = row['event_competition']
        if competition not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'Sophisticated', 'Masters'}:
            continue
        
        dancer_id = row['dancer_id']
        
        # Только для новых танцоров (первые поинты вообще в 2025)
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
        
        # Запоминаем локацию первых поинтов (по самому раннему месяцу)
        if dancer_id not in dancer_first_city:
            dancer_first_city[dancer_id] = {
                'city_key': None,
                'month': 13
            }
        
        if month < dancer_first_city[dancer_id]['month']:
            if country == 'United States' and city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                dancer_first_city[dancer_id] = {
                    'city_key': city_key,
                    'month': month
                }
            
            if country == 'United States' and state:
                dancer_first_state[dancer_id] = state

# 3. Подсчитываем новых для каждого города/штата
print("\n📊 Шаг 3: Подсчитываем новых для каждого города/штата...")

city_new_dancers = defaultdict(set)
state_new_dancers = defaultdict(set)

for dancer_id in new_dancers_2025_global:
    if dancer_id in dancer_first_city and dancer_first_city[dancer_id]['city_key']:
        city_key = dancer_first_city[dancer_id]['city_key']
        city_new_dancers[city_key].add(dancer_id)
    
    if dancer_id in dancer_first_state:
        state = dancer_first_state[dancer_id]
        state_new_dancers[state].add(dancer_id)

# 4. Проверяем DC
print("\n" + "="*80)
print("РЕЗУЛЬТАТ ДЛЯ DC:")
print("="*80)

dc_city_key = None
dc_state = None

# Находим ключ для DC
for city_key in city_new_dancers.keys():
    if 'Washington' in city_key and ('DC' in city_key or 'District of Columbia' in city_key):
        dc_city_key = city_key
        break

for state in state_new_dancers.keys():
    if state.upper() in ['DC', 'DISTRICT OF COLUMBIA']:
        dc_state = state
        break

if dc_city_key:
    print(f"\nГОРОД ({dc_city_key}):")
    print(f"  Новых танцоров: {len(city_new_dancers[dc_city_key])}")
    print(f"  Танцоры: {sorted(list(city_new_dancers[dc_city_key]))[:10]}...")

if dc_state:
    print(f"\nШТАТ ({dc_state}):")
    print(f"  Новых танцоров: {len(state_new_dancers[dc_state])}")
    print(f"  Танцоры: {sorted(list(state_new_dancers[dc_state]))[:10]}...")

if dc_city_key and dc_state:
    city_set = city_new_dancers[dc_city_key]
    state_set = state_new_dancers[dc_state]
    
    print(f"\n🔍 СРАВНЕНИЕ:")
    print(f"  Город: {len(city_set)} новых")
    print(f"  Штат: {len(state_set)} новых")
    print(f"  Разница: {len(state_set) - len(city_set)}")
    
    only_in_state = state_set - city_set
    only_in_city = city_set - state_set
    
    if only_in_state:
        print(f"\n  ⚠️  Танцоры только в штате (но не в городе): {len(only_in_state)}")
        print(f"     Это означает, что есть танцоры, которые получили первые поинты в DC, но город не указан")
        print(f"     Примеры: {list(only_in_state)[:5]}")
    
    if only_in_city:
        print(f"\n  ⚠️  Танцоры только в городе (но не в штате): {len(only_in_city)}")

print(f"\n📊 В статье указано:")
print(f"  Город Washington, DC: 57 новых (теперь исправлено на 74)")
print(f"  Штат District of Columbia: 74 новых")

