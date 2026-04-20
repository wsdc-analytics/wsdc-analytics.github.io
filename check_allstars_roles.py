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

# Проверяем все уникальные значения ролей
all_roles = set()
dancer_roles_dict = defaultdict(set)

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
        if not dancer_name:
            continue
        
        loc_id = row.get('location_id','')
        country = ''
        if loc_id in loc:
            country = loc[loc_id]['country']
        
        event_name = row.get('event_name','')
        if not is_european_event(country, event_name):
            continue
        
        role = row.get('dancer_role','')
        pts = float(row.get('event_points','0') or 0)
        
        if pts > 0:
            all_roles.add(role)
            dancer_roles_dict[dancer_name].add(role)

print("Все уникальные значения ролей в All-Stars на европейских ивентах:")
print(all_roles)
print()

# Находим танцоров с обеими ролями
both_roles_dancers = []
for dancer_name, roles in dancer_roles_dict.items():
    # Проверяем разные варианты написания
    has_leader = 'Leader' in roles or 'leader' in roles or 'L' in roles
    has_follower = 'Follower' in roles or 'follower' in roles or 'F' in roles
    
    if has_leader and has_follower:
        both_roles_dancers.append({
            'name': dancer_name,
            'roles': roles
        })

print(f"Танцоры с обеими ролями (все варианты): {len(both_roles_dancers)}")
for dancer in both_roles_dancers[:10]:
    print(f"  {dancer['name']}: {dancer['roles']}")
