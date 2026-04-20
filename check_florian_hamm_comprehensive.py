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
all_records = []

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
            all_records.append({
                'event': event_name,
                'comp': comp,
                'points': pts,
                'country': country,
                'loc_id': loc_id
            })

print(f"Все записи с поинтами для {target_name} (2025):")
print("="*70)
print(f"Всего записей: {len(all_records)}")

# Группируем по ивентам
events_dict = defaultdict(lambda: {'comps': set(), 'points': 0, 'country': ''})
for record in all_records:
    events_dict[record['event']]['comps'].add(record['comp'])
    events_dict[record['event']]['points'] += record['points']
    if record['country']:
        events_dict[record['event']]['country'] = record['country']

print(f"\nУникальных ивентов: {len(events_dict)}")
print(f"\nДетальный список всех ивентов:")
for i, (event, data) in enumerate(sorted(events_dict.items()), 1):
    print(f"  {i}. {event}")
    print(f"      Страна: {data['country'] if data['country'] else 'не указана'}")
    print(f"      Номинации: {', '.join(sorted(data['comps']))}")
    print(f"      Поинты: {data['points']:.0f}")

# Проверяем, какие могут быть европейскими
european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

eu_events = set()
for event, data in events_dict.items():
    country = data['country']
    if 'finnfest' in event.lower():
        eu_events.add(event)
    elif 'scandinavian open' in event.lower():
        eu_events.add(event)
    elif 'nordic' in event.lower() or 'scandinavia' in event.lower():
        eu_events.add(event)
    elif country in european_countries:
        eu_events.add(event)

print(f"\nЕвропейские ивенты (по логике): {len(eu_events)}")
print(f"Список:")
for i, event in enumerate(sorted(eu_events), 1):
    print(f"  {i}. {event}")

non_eu = set(events_dict.keys()) - eu_events
if non_eu:
    print(f"\nНеевропейские ивенты: {len(non_eu)}")
    for event in sorted(non_eu):
        print(f"  - {event} (страна: {events_dict[event]['country']})")
