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

def get_location_info(loc_id, event_name):
    if loc_id in loc:
        country = loc[loc_id]['country']
        city = loc[loc_id]['city']
        return f"{city}, {country}" if city else country
    elif 'Nordic' in event_name or 'Scandinavia' in event_name:
        return "Stockholm, Sweden"
    return ""

targets = [
    'Allan Thivoz', 'Joshua Schubert', 'Stefanie Tschom', 'Alexandra Branco',
    'Dianeva Poirson', 'Attila Kobori', 'Maina Vila Cobarsi', 'Clement Turpain', 'Aless Tondolo'
]

for target in targets:
    events_data = defaultdict(float)
    
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
            if dancer_name != target:
                continue
            
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            event_name = row.get('event_name','')
            if not is_european_event(country, event_name):
                continue
            
            pts = float(row.get('event_points','0') or 0)
            if pts > 0:
                events_data[event_name] += pts
    
    if events_data:
        top_event, top_pts = max(events_data.items(), key=lambda x: x[1])
        top_location = ""
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                    dancer_id = row.get('dancer_id','')
                    if dancer_id_to_name.get(dancer_id,'') == target:
                        top_location = get_location_info(row.get('location_id',''), top_event)
                        break
        print(f"{target}: {top_event} ({top_location}) - {int(top_pts)} поинтов")

