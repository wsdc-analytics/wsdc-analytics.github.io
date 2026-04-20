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

target_name = 'Florian Hamm'
all_events = set()
eu_events = set()
all_points = 0
eu_points = 0

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name, loc_id):
    if 'finnfest' in event_name.lower():
        return True
    if 'scandinavian open' in event_name.lower():
        return True
    if 'nordic' in event_name.lower() or 'scandinavia' in event_name.lower():
        return True
    return country in european_countries

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
        if dancer_name != target_name:
            continue
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        event_name = row.get('event_name','')
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            all_events.add(event_name)
            all_points += pts
            
            if is_european_event(country, event_name, loc_id):
                eu_events.add(event_name)
                eu_points += pts

print(f"Данные по {target_name} (2025):")
print("="*70)
print(f"\nВсе ивенты (без фильтрации): {len(all_events)}")
print(f"Всего поинтов: {all_points:.0f}")
print(f"Список всех ивентов:")
for i, event in enumerate(sorted(all_events), 1):
    print(f"  {i}. {event}")

print(f"\nЕвропейские ивенты (с фильтрацией): {len(eu_events)}")
print(f"Поинтов на европейских: {eu_points:.0f}")
print(f"Список европейских ивентов:")
for i, event in enumerate(sorted(eu_events), 1):
    print(f"  {i}. {event}")

print(f"\nНеевропейские ивенты: {len(all_events - eu_events)}")
if all_events - eu_events:
    print("Список неевропейских ивентов:")
    for i, event in enumerate(sorted(all_events - eu_events), 1):
        print(f"  {i}. {event}")
