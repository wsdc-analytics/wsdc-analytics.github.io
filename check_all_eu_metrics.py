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

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    european = {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}
    return country in european

stats = defaultdict(lambda: {'points': 0, 'wins': 0, 'events': set()})

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}:
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
            stats[dancer_name]['points'] += pts
            stats[dancer_name]['events'].add(event_name)
        
        if result == '1':
            stats[dancer_name]['wins'] += 1

# Топ-10 по каждой метрике
top_points = sorted(stats.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
top_wins = sorted(stats.items(), key=lambda x: x[1]['wins'], reverse=True)[:10]
top_events = sorted(stats.items(), key=lambda x: len(x[1]['events']), reverse=True)[:10]

print("ТОП-10 ПО ПОИНТАМ:")
print("=" * 70)
for i, (name, data) in enumerate(top_points, 1):
    print(f"{i:2d}. {name:30s} | {data['points']:5.0f} pts")

print("\nТОП-10 ПО ПОБЕДАМ:")
print("=" * 70)
for i, (name, data) in enumerate(top_wins, 1):
    print(f"{i:2d}. {name:30s} | {data['wins']:2d} wins")

print("\nТОП-10 ПО ИВЕНТАМ:")
print("=" * 70)
for i, (name, data) in enumerate(top_events, 1):
    print(f"{i:2d}. {name:30s} | {len(data['events']):2d} events")

