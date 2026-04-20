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

problem_events = ['Finnfest', 'Scandinavian Open']

# Проверяем топ-10 танцоров из общего топа
top_dancers = ['Kristen Wallace', 'Zachary Skinner', 'Igor Pitangui', 'Nicole Ramirez', 
               'Aleksandra Radziejewska', 'Hanna Junk', 'Mathias Mendillo', 'Sebastian Quinones',
               'Mackenzie Keister', 'Keerigan Rudd']

print("Проверка влияния на общий топ (глобальный):")
print("="*70)

# Проверяем, получали ли топ-танцоры поинты на проблемных ивентах
for dancer in top_dancers:
    events_found = []
    for event in problem_events:
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025':
                    dancer_id = row.get('dancer_id','')
                    dancer_name = dancer_id_to_name.get(dancer_id,'')
                    if dancer_name == dancer and event.lower() in row.get('event_name','').lower():
                        pts = float(row.get('event_points','0') or 0)
                        if pts > 0:
                            events_found.append((event, pts))
                            break
    
    if events_found:
        print(f"{dancer}: получил поинты на {', '.join([f'{e[0]} ({e[1]:.0f})' for e in events_found])}")

if not any(events_found for events_found in [[(dancer, []) for dancer in top_dancers]]):
    print("✓ Топ-10 танцоров не получили поинты на проблемных ивентах")

# Проверяем Sophisticated раздел
print("\n" + "="*70)
print("Проверка влияния на Sophisticated раздел:")
sophisticated_dancers = ['Jerome Tangha', 'Lucie Renaud', 'Joshua Schubert', 'Allan Thivoz']

for dancer in sophisticated_dancers:
    events_found = []
    for event in problem_events:
        with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('event_year','') == '2025' and row.get('event_competition','') == 'Sophisticated':
                    dancer_id = row.get('dancer_id','')
                    dancer_name = dancer_id_to_name.get(dancer_id,'')
                    if dancer_name == dancer and event.lower() in row.get('event_name','').lower():
                        pts = float(row.get('event_points','0') or 0)
                        if pts > 0:
                            events_found.append((event, pts))
                            break
    
    if events_found:
        print(f"{dancer}: получил поинты на {', '.join([f'{e[0]} ({e[1]:.0f})' for e in events_found])}")
