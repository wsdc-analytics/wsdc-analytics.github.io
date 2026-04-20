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

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    return country in european_countries

points = defaultdict(float)
dancer_events = defaultdict(set)
dancer_wins = defaultdict(int)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp != 'All-Stars':  # Только All-Stars
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        event_name = row.get('event_name','')
        if not is_european_event(country, event_name):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0:
            points[dancer_name] += pts
            dancer_events[dancer_name].add(event_name)
        if result == '1':
            dancer_wins[dancer_name] += 1

# Топ-5 по поинтам в All-Stars на европейских ивентах
top_allstars = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:5]

print("Топ-5 танцоров по поинтам в All-Stars на европейских ивентах (2025):")
print("="*70)
for i, (name, pts) in enumerate(top_allstars, 1):
    events_count = len(dancer_events[name])
    wins_count = dancer_wins[name]
    print(f"{i}. {name}: {pts:.0f} поинтов ({events_count} ивентов, {wins_count} побед)")
