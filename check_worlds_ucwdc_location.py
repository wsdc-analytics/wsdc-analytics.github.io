#!/usr/bin/env python3
"""
Проверяем, где на самом деле проходило Worlds UCWDC в 2025 году
"""

import csv
import sys
from collections import defaultdict

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

filename_points = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

# 1. Проверяем локацию в events_wsdc.csv
print("="*80)
print("1. ПРОВЕРКА ЛОКАЦИИ В events_wsdc.csv")
print("="*80)

with open(filename_events, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if 'UCWDC' in row['name'] or 'Worlds' in row['name']:
            print(f"Событие: {row['name']}")
            print(f"Локация в CSV: {row.get('location', 'N/A')}")
            print(f"Дата: {row.get('date', 'N/A')}")
            
            # Нормализуем локацию
            loc = row.get('location', '').strip()
            if loc:
                city, state, country = normalize_location(loc)
                print(f"После нормализации: city={city}, state={state}, country={country}")
            print()

# 2. Проверяем данные из dancers_results_info.csv за 2025
print("="*80)
print("2. ПРОВЕРКА ДАННЫХ ЗА 2025 ГОД")
print("="*80)

event_years = defaultdict(set)
event_locations = defaultdict(set)

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        event_name = row['event_name']
        year = row['event_year']
        
        if 'UCWDC' in event_name or ('Worlds' in event_name and 'UCWDC' in event_name):
            event_years[event_name].add(year)
            # Попробуем найти локацию через events_wsdc
            with open(filename_events, 'r', encoding='utf-8') as ef:
                ereader = csv.DictReader(ef)
                for erow in ereader:
                    if erow['name'] == event_name:
                        event_locations[event_name].add(erow.get('location', 'N/A'))
                        break

print("Годы, когда проходило событие:")
for event_name, years in event_years.items():
    print(f"  {event_name}: {sorted(years)}")

print("\nЛокации в events_wsdc.csv:")
for event_name, locations in event_locations.items():
    for loc in locations:
        print(f"  {event_name}: {loc}")
        if loc:
            city, state, country = normalize_location(loc)
            print(f"    → city={city}, state={state}, country={country}")

# 3. Проверяем конкретно 2025 год
print("\n" + "="*80)
print("3. ДАННЫЕ ЗА 2025 ГОД")
print("="*80)

with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_year'] == '2025' and ('UCWDC' in row['event_name'] or ('Worlds' in row['event_name'] and 'UCWDC' in row['event_name'])):
            print(f"Событие: {row['event_name']}")
            print(f"Месяц: {row.get('event_month', 'N/A')}")
            
            # Проверяем локацию в events_wsdc
            event_name = row['event_name']
            with open(filename_events, 'r', encoding='utf-8') as ef:
                ereader = csv.DictReader(ef)
                for erow in ereader:
                    if erow['name'] == event_name:
                        loc = erow.get('location', 'N/A')
                        print(f"Локация в events_wsdc.csv: {loc}")
                        if loc != 'N/A':
                            city, state, country = normalize_location(loc)
                            print(f"После нормализации: {city}, {state}, {country}")
                        break

