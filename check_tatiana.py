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

stats = {'Tatiana Kaneva':{'total_points':0,'russian_points':0,'european_points':0,'wins':0,'competitions':defaultdict(int),'events_data':defaultdict(float)}}

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
        if dancer_name != 'Tatiana Kaneva':
            continue
        country = ''
        city = ''
        loc_id = row.get('location_id','')
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        
        st = stats['Tatiana Kaneva']
        st['total_points'] += points
        st['competitions'][comp] += 1
        
        event_name = row.get('event_name','')
        st['events_data'][event_name] += points
        
        if is_russian_event(country):
            st['russian_points'] += points
        elif is_european_event(country):
            st['european_points'] += points
        
        if str(row.get('event_result','')) == '1':
            st['wins'] += 1

st = stats['Tatiana Kaneva']
russian_pct = (st['russian_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0
european_pct = (st['european_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0

print(f"Tatiana Kaneva:")
print(f"  Всего: {st['total_points']:.0f} поинтов, Победы: {st['wins']}")
print(f"  Номинации: {dict(st['competitions'])}")
print(f"  География: {russian_pct:.1f}% российские, {european_pct:.1f}% европейские")
print(f"  Топ-ивент: {max(st['events_data'].items(), key=lambda x: x[1])}")

