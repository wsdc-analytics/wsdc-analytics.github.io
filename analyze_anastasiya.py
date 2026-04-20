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

def is_russian_event(country):
    return country == 'Russia'

def is_european_event(country):
    european = {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria','Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia','Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}
    return country in european

stats = {
    'total_points':0,
    'wins':0,
    'events':set(),
    'competitions':defaultdict(int),
    'roles':defaultdict(int),
    'russian_points':0,
    'european_points':0,
    'russian_events':set(),
    'european_events':set(),
    'events_data':defaultdict(float),
    'wins_by_event':[]
}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name != 'Anastasiya Yuzhakova':
            continue
        
        role = row.get('dancer_role','')
        event_name = row.get('event_name','')
        country = ''
        city = ''
        loc_id = row.get('location_id','')
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        
        stats['total_points'] += points
        stats['competitions'][comp] += 1
        stats['roles'][role] += 1
        stats['events'].add(event_name)
        stats['events_data'][event_name] += points
        
        if is_russian_event(country):
            stats['russian_points'] += points
            stats['russian_events'].add(event_name)
        elif is_european_event(country):
            stats['european_points'] += points
            stats['european_events'].add(event_name)
        
        if str(row.get('event_result','')) == '1':
            stats['wins'] += 1
            stats['wins_by_event'].append(event_name)

russian_pct = (stats['russian_points'] / stats['total_points'] * 100) if stats['total_points'] > 0 else 0
european_pct = (stats['european_points'] / stats['total_points'] * 100) if stats['total_points'] > 0 else 0

top_event, top_pts = max(stats['events_data'].items(), key=lambda x: x[1])
# Find location for top event
top_location = ''
for row in open(RESULTS_FILE, newline='', encoding='utf-8'):
    # This is a simple check, might need to re-read properly
    pass

# Re-read to get location
with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
            dancer_id = row.get('dancer_id','')
            if dancer_id_to_name.get(dancer_id,'') == 'Anastasiya Yuzhakova':
                loc_id = row.get('location_id','')
                if loc_id in loc:
                    top_location = f"{loc[loc_id]['city']}, {loc[loc_id]['country']}" if loc[loc_id]['city'] else loc[loc_id]['country']
                break

print(f"Anastasiya Yuzhakova - полный анализ:")
print(f"  Поинты: {stats['total_points']:.0f}")
print(f"  Победы: {stats['wins']}")
print(f"  Ивенты с поинтами: {len(stats['events'])}")
print(f"  Номинации: {dict(stats['competitions'])}")
print(f"  Роли: {dict(stats['roles'])}")
print(f"  География: {russian_pct:.1f}% российские ({len(stats['russian_events'])} ивентов), {european_pct:.1f}% европейские ({len(stats['european_events'])} ивентов)")
print(f"  Победы по ивентам: {stats['wins_by_event']}")
print(f"  Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")

