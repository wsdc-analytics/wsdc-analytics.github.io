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

events_data = defaultdict(lambda: {'points':0, 'country':'', 'city':''})

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name != 'Olga Khvan':
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        event_name = row.get('event_name','')
        loc_id = row.get('location_id','')
        country = ''
        city = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        events_data[event_name]['points'] += points
        if not events_data[event_name]['country']:
            events_data[event_name]['country'] = country
            events_data[event_name]['city'] = city

print("Olga Khvan - все ивенты:")
for event, data in sorted(events_data.items(), key=lambda x: x[1]['points'], reverse=True):
    location = f"{data['city']}, {data['country']}" if data['city'] else data['country']
    print(f"  {event} ({location}): {int(data['points'])} поинтов")

countries = set()
for data in events_data.values():
    if data['country']:
        countries.add(data['country'])

print(f"\nСтраны: {sorted(countries)}")

