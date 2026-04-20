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

# Проверяем проблемные ивенты в разных контекстах
problem_events = ['Finnfest', 'Scandinavian Open']

print("Проверка влияния исправлений на другие разделы:")
print("="*70)

# Проверяем, есть ли эти ивенты в США
print("\n1. Американские ивенты (United States):")
us_events = set()
for event in problem_events:
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025' and event.lower() in row.get('event_name','').lower():
                loc_id = row.get('location_id','')
                country = ''
                if loc_id in loc:
                    country = loc[loc_id]['country']
                if country == 'United States':
                    us_events.add(event)
                    print(f"  {event} найден в США: {country}")

if not us_events:
    print("  ✓ Эти ивенты не найдены в США")

# Проверяем, есть ли эти ивенты в других странах (не Европа)
print("\n2. Неевропейские страны:")
non_eu_countries = set()
for event in problem_events:
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025' and event.lower() in row.get('event_name','').lower():
                loc_id = row.get('location_id','')
                country = ''
                if loc_id in loc:
                    country = loc[loc_id]['country']
                if country and country not in {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Polska',
                    'Sweden','Denmark','Norway','Finland','Finalnd','Belgium','Belgique','Switzerland','Austria',
                    'Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia',
                    'Slovenia','Estonia','Latvia','Lithuania','Ukraine','Belarus','Bulgaria','Serbia'}:
                    non_eu_countries.add((event, country))
                    print(f"  {event} найден в неевропейской стране: {country}")

if not non_eu_countries:
    print("  ✓ Эти ивенты найдены только в Европе или без локации")

# Проверяем, есть ли танцоры из других разделов на этих ивентах
print("\n3. Танцоры на проблемных ивентах (проверка влияния на другие разделы):")
dancers_on_problem_events = defaultdict(set)
for event in problem_events:
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025' and event.lower() in row.get('event_name','').lower():
                dancer_id = row.get('dancer_id','')
                dancer_name = dancer_id_to_name.get(dancer_id,'')
                if dancer_name:
                    pts = float(row.get('event_points','0') or 0)
                    if pts > 0:
                        dancers_on_problem_events[event].add(dancer_name)

for event, dancers in dancers_on_problem_events.items():
    print(f"\n  {event}: {len(dancers)} танцоров получили поинты")
    print(f"    Примеры: {', '.join(list(dancers)[:5])}")

# Проверяем, есть ли эти танцоры в топах других разделов
print("\n4. Проверка влияния на другие топы:")
print("  (Нужно проверить, есть ли танцоры из этих ивентов в других разделах)")
