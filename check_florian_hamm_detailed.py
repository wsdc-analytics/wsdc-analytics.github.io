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
events_by_name = set()
events_by_name_comp = set()  # Ивенты с учетом номинации
events_detail = []

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
        if not is_european_event(country, event_name, loc_id):
            continue
        
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            events_by_name.add(event_name)
            events_by_name_comp.add((event_name, comp))
            events_detail.append({
                'event': event_name,
                'comp': comp,
                'points': pts,
                'country': country
            })

print(f"Данные по {target_name} на европейских ивентах (2025):")
print("="*70)
print(f"\nУникальные ивенты (по названию): {len(events_by_name)}")
print(f"Ивенты с учетом номинации: {len(events_by_name_comp)}")
print(f"\nДетальный список:")
for event in sorted(events_by_name):
    comps = [e['comp'] for e in events_detail if e['event'] == event]
    total_pts = sum([e['points'] for e in events_detail if e['event'] == event])
    print(f"  {event}: {', '.join(set(comps))} ({total_pts:.0f} поинтов)")

print(f"\nЕсли считать по номинациям отдельно:")
comps_by_event = defaultdict(set)
for event, comp in events_by_name_comp:
    comps_by_event[event].add(comp)
total_count = sum([len(comps) for comps in comps_by_event.values()])
print(f"  Всего записей: {total_count}")
