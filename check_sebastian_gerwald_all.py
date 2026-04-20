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

european_countries = {
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland',
    'Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    return country in european_countries

target_name = 'Sebastian Gerwald'
roles_eu = set()
roles_all = set()
points_eu_by_role = defaultdict(float)
points_all_by_role = defaultdict(float)
events_eu = set()
events_all = set()

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp != 'All-Stars':
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
        is_eu = is_european_event(country, event_name)
        
        role = row.get('event_role','').strip().lower()
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            roles_all.add(role)
            points_all_by_role[role] += pts
            events_all.add(event_name)
            
            if is_eu:
                roles_eu.add(role)
                points_eu_by_role[role] += pts
                events_eu.add(event_name)

print(f"Данные по {target_name} в All-Stars (2025):")
print("="*70)
print("\nНа европейских ивентах:")
print(f"  Роли: {roles_eu}")
print(f"  Поинты по ролям: {dict(points_eu_by_role)}")
print(f"  Ивентов: {len(events_eu)}")
if 'leader' in roles_eu and 'follower' in roles_eu:
    print("  ✓ Получал поинты за обе роли на европейских ивентах")
else:
    print("  ✗ Получал поинты только за одну роль на европейских ивентах")

print("\nНа всех ивентах (включая неевропейские):")
print(f"  Роли: {roles_all}")
print(f"  Поинты по ролям: {dict(points_all_by_role)}")
print(f"  Ивентов: {len(events_all)}")
if 'leader' in roles_all and 'follower' in roles_all:
    print("  ✓ Получал поинты за обе роли на всех ивентах")
else:
    print("  ✗ Получал поинты только за одну роль на всех ивентах")
