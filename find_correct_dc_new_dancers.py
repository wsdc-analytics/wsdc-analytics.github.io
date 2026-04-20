#!/usr/bin/env python3
"""
Ищем правильные цифры для новых танцоров в DC, используя локальную логику
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

# Build Event Location Map с учетом дат
event_geo_map = {}
with open(filename_events, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        name = row['name'].strip()
        loc = row.get('location', '').strip()
        date_str = row.get('date', '').strip()
        
        if name and loc:
            city, state, country = normalize_location(loc)
            if country:
                from datetime import datetime
                event_date = None
                try:
                    for fmt in ['%B %Y', '%b %Y', '%Y-%m-%d', '%Y/%m/%d']:
                        try:
                            event_date = datetime.strptime(date_str.strip(), fmt)
                            break
                        except:
                            continue
                except:
                    pass
                
                if name not in event_geo_map:
                    event_geo_map[name] = {
                        'city': city,
                        'state': state,
                        'country': country,
                        'raw_loc': loc,
                        'date': event_date
                    }
                else:
                    existing_date = event_geo_map[name].get('date')
                    if event_date and (not existing_date or event_date > existing_date):
                        event_geo_map[name] = {
                            'city': city,
                            'state': state,
                            'country': country,
                            'raw_loc': loc,
                            'date': event_date
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
print("ЛОКАЛЬНАЯ ЛОГИКА: Первые поинты в городе/штате в 2025")
print("="*80)

# Сканируем всю историю для определения первых поинтов в городе и штате
dancer_first_city_year = {}  # dancer_id -> {city_key -> year}
dancer_first_state_year = {}  # dancer_id -> {state -> year}

print("\n📊 Сканируем всю историю...")
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}:
            continue
        
        event_name = row['event_name']
        dancer_id = row['dancer_id']
        year = int(row['event_year'])
        
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
            
            # Для городов
            if country == 'United States' and city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if dancer_id not in dancer_first_city_year:
                    dancer_first_city_year[dancer_id] = {}
                if city_key not in dancer_first_city_year[dancer_id] or year < dancer_first_city_year[dancer_id][city_key]:
                    dancer_first_city_year[dancer_id][city_key] = year
            
            # Для штатов
            if country == 'United States' and state:
                if dancer_id not in dancer_first_state_year:
                    dancer_first_state_year[dancer_id] = {}
                if state not in dancer_first_state_year[dancer_id] or year < dancer_first_state_year[dancer_id][state]:
                    dancer_first_state_year[dancer_id][state] = year

# Обрабатываем данные за 2025
print("📊 Обрабатываем данные за 2025...\n")

city_new = set()
state_new = set()
city_all = set()
state_all = set()

city_key_dc = None

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
        
        # Проверяем DC
        if country == 'United States' and state and state.upper() in ['DC', 'DISTRICT OF COLUMBIA']:
            state_all.add(dancer_id)
            
            # Проверяем, новый ли в штате
            if dancer_id in dancer_first_state_year and state in dancer_first_state_year[dancer_id]:
                if dancer_first_state_year[dancer_id][state] == 2025:
                    state_new.add(dancer_id)
            
            # Для города
            if city:
                city_key = f"{city}, {state if state else ''}, {country}".replace(', ,', ',')
                if not city_key_dc:
                    city_key_dc = city_key
                
                if city_key == city_key_dc:  # Только Washington
                    city_all.add(dancer_id)
                    
                    # Проверяем, новый ли в городе
                    if dancer_id in dancer_first_city_year and city_key in dancer_first_city_year[dancer_id]:
                        if dancer_first_city_year[dancer_id][city_key] == 2025:
                            city_new.add(dancer_id)

print(f"ГОРОД (Washington, DC):")
print(f"  Уникальных: {len(city_all)}")
print(f"  Новых (локальная логика): {len(city_new)}")

print(f"\nШТАТ (District of Columbia):")
print(f"  Уникальных: {len(state_all)}")
print(f"  Новых (локальная логика): {len(state_new)}")

print(f"\n📊 В статье указано:")
print(f"  Город: 57 новых")
print(f"  Штат: 74 новых")
print(f"\n📊 Мой расчет (локальная логика):")
print(f"  Город: {len(city_new)} новых")
print(f"  Штат: {len(state_new)} новых")

if len(city_new) != len(state_new):
    print(f"\n⚠️  НЕСООТВЕТСТВИЕ: В DC только один город, но цифры разные!")
    only_in_state = state_new - city_new
    print(f"  Танцоров только в штате (но не в городе): {len(only_in_state)}")
    
    # Проверяем, почему
    print(f"\n🔍 Анализ расхождения:")
    print(f"  city_all: {len(city_all)}")
    print(f"  state_all: {len(state_all)}")
    print(f"  Разница в уникальных: {len(state_all) - len(city_all)}")
    if len(state_all) != len(city_all):
        only_state_dancers = state_all - city_all
        print(f"  Танцоры в штате, но не в городе: {len(only_state_dancers)}")
        print(f"    Возможно, есть события в DC без указания города Washington")

