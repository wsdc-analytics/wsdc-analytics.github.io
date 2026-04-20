#!/usr/bin/env python3
"""
Проверка расхождения новых участников для Washington, DC (город) vs District of Columbia (штат)
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

print("="*80)
print("АНАЛИЗ НОВЫХ УЧАСТНИКОВ: Washington, DC (город) vs District of Columbia (штат)")
print("="*80)

# 2. Сканируем историю для определения первых поинтов в городе и штате
dancer_first_city_year = {}  # dancer_id -> {city -> year}
dancer_first_state_year = {}  # dancer_id -> {state -> year}

print("\n📊 Сканируем всю историю для определения первых поинтов...")
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        
        # Проверяем маппинг
        mapped_name = EVENT_NAME_MAPPING.get(event_name, event_name)
        geo = event_geo_map.get(mapped_name)
        
        if not geo:
            geo = event_geo_map.get(event_name)
        
        if not geo:
            clean_name = event_name.split(' 20')[0].strip()
            geo = event_geo_map.get(clean_name)
        
        if geo:
            city = geo['city']
            state = geo['state']
            country = geo['country']
            
            # Для городов (только для США и если есть город)
            if country == 'United States' and city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if dancer_id not in dancer_first_city_year:
                    dancer_first_city_year[dancer_id] = {}
                if city_key not in dancer_first_city_year[dancer_id] or year < dancer_first_city_year[dancer_id][city_key]:
                    dancer_first_city_year[dancer_id][city_key] = year
            
            # Для штатов (только для США и если есть штат)
            if country == 'United States' and state:
                if dancer_id not in dancer_first_state_year:
                    dancer_first_state_year[dancer_id] = {}
                if state not in dancer_first_state_year[dancer_id] or year < dancer_first_state_year[dancer_id][state]:
                    dancer_first_state_year[dancer_id][state] = year

# 3. Обрабатываем данные за 2025 год
print("📊 Обрабатываем данные за 2025 год...\n")

city_new_dancers = set()
state_new_dancers = set()
city_all_dancers = set()
state_all_dancers = set()

city_events = set()
state_events = set()

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] != '2025':
            continue
        
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        dancer_id = row['dancer_id']
        
        try:
            points = int(row['event_points'])
        except:
            points = 0
        
        if points <= 0:
            continue
        
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
        
        # Проверяем, это DC?
        city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
        
        is_dc_city = ('Washington' in city_key and ('DC' in city_key or 'District of Columbia' in city_key))
        is_dc_state = (state and state.upper() in ['DC', 'DISTRICT OF COLUMBIA'])
        
        if is_dc_city:
            city_all_dancers.add(dancer_id)
            city_events.add(event_name)
            
            # Проверяем, новый ли танцор в этом городе
            if dancer_id in dancer_first_city_year and city_key in dancer_first_city_year[dancer_id]:
                if dancer_first_city_year[dancer_id][city_key] == 2025:
                    city_new_dancers.add(dancer_id)
        
        if is_dc_state:
            state_all_dancers.add(dancer_id)
            state_events.add(event_name)
            
            # Проверяем, новый ли танцор в этом штате
            if dancer_id in dancer_first_state_year and state in dancer_first_state_year[dancer_id]:
                if dancer_first_state_year[dancer_id][state] == 2025:
                    state_new_dancers.add(dancer_id)

print(f"ГОРОД (Washington, DC):")
print(f"  Всего уникальных танцоров: {len(city_all_dancers)}")
print(f"  Новых танцоров (первые поинты в городе в 2025): {len(city_new_dancers)}")
print(f"  Ивентов: {len(city_events)}")
for event in sorted(city_events):
    print(f"    - {event}")

print(f"\nШТАТ (District of Columbia):")
print(f"  Всего уникальных танцоров: {len(state_all_dancers)}")
print(f"  Новых танцоров (первые поинты в штате в 2025): {len(state_new_dancers)}")
print(f"  Ивентов: {len(state_events)}")
for event in sorted(state_events):
    print(f"    - {event}")

print(f"\n🔍 РАЗНИЦА:")
print(f"  Разница в новых танцорах: {len(state_new_dancers) - len(city_new_dancers)}")
print(f"  Разница в уникальных танцорах: {len(state_all_dancers) - len(city_all_dancers)}")
print(f"  Разница в ивентах: {len(state_events) - len(city_events)}")

# Проверяем, какие танцоры есть в штате, но нет в городе
only_in_state = state_new_dancers - city_new_dancers
if only_in_state:
    print(f"\n⚠️  Новые танцоры, которые есть в штате, но нет в городе ({len(only_in_state)}):")
    print(f"   Это означает, что есть события в DC, которые не привязаны к городу Washington")

