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

mentioned = {
    'Igor Pitangui', 'Aleksandra Radziejewska', 'Nicole Ramirez', 
    'Keerigan Rudd', 'Kristen Wallace', 'Zachary Skinner',
    'Charlie Fournier', 'Sebastian Gerwald', 'Alexa Partos', 
    'Fabio Zanardelli', 'Hanna Junk'
}

stats = {}

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
        if not dancer_name or dancer_name in mentioned:
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
            if dancer_name not in stats:
                stats[dancer_name] = {'points': 0}
            stats[dancer_name]['points'] += pts

# Топ-10 по поинтам
top_points = sorted(stats.items(), key=lambda x: x[1]['points'], reverse=True)[:10]

print("ТОП-10 ПО ПОИНТАМ (европейские ивенты):")
for i, (name, st) in enumerate(top_points, 1):
    # Попытка определить пол по имени (не очень точно, но может помочь)
    # Обычно женские имена заканчиваются на -a, -ia и т.д., но это неточно
    print(f"{i:2d}. {name:30s} | {st['points']:5.0f} pts")

print("\nПроверяем имена, которые могут быть женскими:")
female_indicators = ['Melina', 'Camille', 'Tina', 'Elodie', 'Christina', 'Alexandra', 'Dianeva']
for i, (name, st) in enumerate(top_points, 1):
    if any(ind in name for ind in female_indicators) or name.endswith('a') or 'ia' in name:
        print(f"{i:2d}. {name:30s} | {st['points']:5.0f} pts")

