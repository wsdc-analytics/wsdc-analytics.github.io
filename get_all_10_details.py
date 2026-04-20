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
    'Slovenia','Estonia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}
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
    'Florian Hamm', 'Joshua Schubert', 'Allan Thivoz', 'Christina Landowski',
    'Daniel Curl', 'Melina Voglhuber', 'Thibault Ramirez', 'Joao Parada',
    'Vincent Roubadia', 'Ken Rutland'
]

for target in targets:
    stats = {
        'points': 0, 'weighted_points': 0, 'wins': 0, 'weighted_wins': 0,
        'events': set(), 'competitions': defaultdict(int),
        'points_by_level': defaultdict(float), 'wins_by_level': defaultdict(int),
        'roles': defaultdict(int), 'events_data': defaultdict(float),
        'global_points': 0
    }
    
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
            
            # Глобальные поинты
            pts = float(row.get('event_points','0') or 0)
            if pts > 0:
                stats['global_points'] += pts
            
            # Европейские данные
            loc_id = row.get('location_id','')
            country = ''
            if loc_id in loc:
                country = loc[loc_id]['country']
            event_name = row.get('event_name','')
            if not is_european_event(country, event_name):
                continue
            
            weight = {'Champions': 3.0, 'All-Stars': 2.0, 'Advanced': 1.5,
                     'Intermediate': 1.0, 'Novice': 0.5, 'Newcomer': 0.3}.get(comp, 1.0)
            result = str(row.get('event_result',''))
            role = row.get('dancer_role','')
            
            if pts > 0:
                stats['points'] += pts
                stats['weighted_points'] += pts * weight
                stats['points_by_level'][comp] += pts
                stats['events'].add(event_name)
                stats['competitions'][comp] += 1
                stats['roles'][role] += 1
                stats['events_data'][event_name] += pts
            if result == '1':
                stats['wins'] += 1
                stats['weighted_wins'] += weight
                stats['wins_by_level'][comp] += 1
    
    top_event, top_pts = max(stats['events_data'].items(), key=lambda x: x[1]) if stats['events_data'] else ('', 0)
    top_location = ""
    if top_event:
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025' and row.get('event_name','') == top_event:
                    dancer_id = row.get('dancer_id','')
                    if dancer_id_to_name.get(dancer_id,'') == target:
                        top_location = get_location_info(row.get('location_id',''), top_event)
                        break
    
    highest = max([l for l in stats['points_by_level'].keys()], 
                 key=lambda x: {'Champions': 6, 'All-Stars': 5, 'Advanced': 4,
                               'Intermediate': 3, 'Novice': 2, 'Newcomer': 1}.get(x, 0)) if stats['points_by_level'] else 'N/A'
    
    european_pct = (stats['points'] / stats['global_points'] * 100) if stats['global_points'] > 0 else 100
    
    print(f"{target}:")
    print(f"  Поинты: {stats['points']:.0f} (взвешенные: {stats['weighted_points']:.1f})")
    print(f"  Победы: {stats['wins']} (взвешенные: {stats['weighted_wins']:.1f})")
    print(f"  Ивенты: {len(stats['events'])}")
    print(f"  Высшая номинация: {highest}")
    print(f"  Поинты по номинациям: {dict(stats['points_by_level'])}")
    print(f"  Победы по номинациям: {dict(stats['wins_by_level'])}")
    print(f"  % европейских: {european_pct:.1f}%")
    print(f"  Топ-ивент: {top_event} ({top_location}) - {int(top_pts)} поинтов")
    print()

