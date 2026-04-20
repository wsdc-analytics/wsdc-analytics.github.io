import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

dancer_id_to_name = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id_to_name[row['dancer_id']] = row.get('dancer_name','')

loc = {}
with open(LOCATION_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        loc[row['location_id']] = {
            'country': row.get('event_country',''),
            'city': row.get('event_city','')
        }

# Проверяем проблемные ивенты
print("Проверка проблемных ивентов:")
print("="*70)

# Finnfest
print("\n1. Finnfest:")
finnfest_events = set()
finnfest_countries = set()
with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') == '2025' and 'finnfest' in row.get('event_name','').lower():
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            finnfest_countries.add(country)
            finnfest_events.add((row.get('event_name',''), country, loc_id))
            print(f"  Ивент: {row.get('event_name','')}, Страна: {country}, location_id: {loc_id}")

print(f"\n  Уникальные страны для Finnfest: {finnfest_countries}")

# Scandinavian Open
print("\n2. Scandinavian Open:")
scandinavian_events = set()
scandinavian_countries = set()
scandinavian_locations = set()
with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') == '2025' and 'scandinavian' in row.get('event_name','').lower():
            loc_id = row.get('location_id','')
            country = ''
            city = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
                city = loc[loc_id]['city']
            scandinavian_countries.add(country)
            scandinavian_locations.add((loc_id, country, city))
            scandinavian_events.add((row.get('event_name',''), country, city, loc_id))
            print(f"  Ивент: {row.get('event_name','')}, Страна: {country}, Город: {city}, location_id: {loc_id}")

print(f"\n  Уникальные страны для Scandinavian Open: {scandinavian_countries}")
print(f"  Уникальные локации: {scandinavian_locations}")
