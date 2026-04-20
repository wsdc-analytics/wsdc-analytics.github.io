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
    'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'
}

def is_european_event(country, event_name):
    if 'Nordic' in event_name or 'Scandinavia' in event_name:
        return True
    return country in european_countries

# Ищем Sebastian Gerwald
target_name = 'Sebastian Gerwald'
roles = set()
points_by_role = defaultdict(float)
events_by_role = defaultdict(set)
total_points = 0
total_events = set()

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
        if not is_european_event(country, event_name):
            continue
        
        role = row.get('event_role','').strip().lower()
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            roles.add(role)
            points_by_role[role] += pts
            events_by_role[role].add(event_name)
            total_points += pts
            total_events.add(event_name)

print(f"Данные по {target_name} в All-Stars на европейских ивентах (2025):")
print("="*70)
print(f"Всего поинтов: {total_points:.0f}")
print(f"Всего ивентов: {len(total_events)}")
print(f"Роли: {roles}")
print()
print("По ролям:")
for role in sorted(roles):
    print(f"  {role}: {points_by_role[role]:.0f} поинтов, {len(events_by_role[role])} ивентов")
    print(f"    Ивенты: {sorted(events_by_role[role])}")

if 'leader' in roles and 'follower' in roles:
    print("\n✓ Получал поинты за обе роли!")
else:
    print("\n✗ Получал поинты только за одну роль или роли не определены")
