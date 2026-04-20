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

dancers_needed = [
    'Elena Kotelnikova',
    'Daniel Pavlov',
    'Marina Motronenko',
    'Polina Khapaeva',
    'Olga Khvan'
]

def is_russian_event(country):
    return country == 'Russia'

events_data = {name: defaultdict(float) for name in dancers_needed}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            year = int(row.get('event_year','0'))
        except:
            continue
        if year != 2025:
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name not in events_data:
            continue
        event_name = row.get('event_name','')
        events_data[dancer_name][event_name] += points

for name, events in events_data.items():
    if not events:
        continue
    top_event, top_pts = max(events.items(), key=lambda x: x[1])
    loc_id = None
    country = ''
    city = ''
    # Find location for top event
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                dancer_id = row.get('dancer_id','')
                if dancer_id_to_name.get(dancer_id,'') == name:
                    loc_id = row.get('location_id','')
                    break
    if loc_id and loc_id in loc:
        country = loc[loc_id]['country']
        city = loc[loc_id]['city']
    location = f"{city}, {country}" if city else country
    print(f"{name}: {top_event} ({location}) - {int(top_pts)} поинтов")

