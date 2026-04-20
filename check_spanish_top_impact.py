import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

# Загружаем список испанских танцоров (нужно проверить, откуда он берется)
# Пока проверим на примере известных испанских танцоров из HTML
spanish_dancers = ['Alvaro Hilario Garcia', 'Fran Vidal', 'Julien Espagnet', 'Margarita Perepelkina', 
                   'Miquel Menendez', 'Aleix Figueras', 'Cristina Marino', 'Alena Muñoz Sánchez',
                   'Laura llacuna', 'Sara Mouchon', 'Alena Belousova', 'Ivan Jorquera Martine']

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

print("Проверка влияния на испанский топ:")
print("="*70)

# Проверяем, получали ли испанские танцоры поинты на проблемных ивентах
spanish_on_problem_events = defaultdict(lambda: {'events': set(), 'points': 0})

for dancer in spanish_dancers:
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
                            spanish_on_problem_events[dancer]['events'].add(event)
                            spanish_on_problem_events[dancer]['points'] += pts

print("\nИспанские танцоры, получившие поинты на проблемных ивентах:")
found_any = False
for dancer, data in spanish_on_problem_events.items():
    if data['events']:
        found_any = True
        print(f"  {dancer}: {', '.join(data['events'])} - {data['points']:.0f} поинтов")

if not found_any:
    print("  ✓ Испанские танцоры не получили поинты на проблемных ивентах")
else:
    print("\n⚠ ВНИМАНИЕ: Испанские танцоры получили поинты на этих ивентах!")
    print("   Если испанский топ фильтрует только по европейским ивентам,")
    print("   то эти поинты могли быть пропущены из-за ошибок в определении европейских ивентов.")
