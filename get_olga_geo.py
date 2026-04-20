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

stats = {'Olga Khvan':{'total_points':0,'russian_points':0,'european_points':0,'other_points':0,'russian_events':set(),'european_events':set(),'wins':0}}

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
        if dancer_name != 'Olga Khvan':
            continue
        country = ''
        city = ''
        loc_id = row.get('location_id','')
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        
        st = stats['Olga Khvan']
        st['total_points'] += points
        
        if is_russian_event(country):
            st['russian_points'] += points
            st['russian_events'].add(row.get('event_name',''))
        elif is_european_event(country):
            st['european_points'] += points
            st['european_events'].add(row.get('event_name',''))
        else:
            st['other_points'] += points
        
        if str(row.get('event_result','')) == '1':
            st['wins'] += 1

st = stats['Olga Khvan']
russian_pct = (st['russian_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0
european_pct = (st['european_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0
other_pct = (st['other_points'] / st['total_points'] * 100) if st['total_points'] > 0 else 0

geo_text = ""
if russian_pct > 0 and european_pct > 0:
    geo_text = f"{russian_pct:.1f}% на российских ивентах ({len(st['russian_events'])} ивентов), {european_pct:.1f}% на европейских ({len(st['european_events'])} ивентов)"
elif russian_pct > 90:
    geo_text = f"все {st['total_points']:.0f} поинтов на российских ивентах ({len(st['russian_events'])} ивентов) - локальное достижение"
elif european_pct > 90:
    geo_text = f"{european_pct:.1f}% на европейских ивентах ({len(st['european_events'])} ивентов), что демонстрирует успех на международной арене"
elif other_pct > 0:
    geo_text = f"также получила поинты в других регионах"

print(f"Olga Khvan: {geo_text}")
print(f"Российские ивенты: {sorted(st['russian_events'])}")
print(f"Европейские ивенты: {sorted(st['european_events'])}")

