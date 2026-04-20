import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'

dancer_id_to_name = {}
with open(DANCERS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        dancer_id_to_name[row['dancer_id']] = row.get('dancer_name','')

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}

points = defaultdict(float)
wins = defaultdict(int)
events = defaultdict(set)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in skill_levels:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        event_name = row.get('event_name','')
        
        if pts > 0:
            points[dancer_name] += pts
            events[dancer_name].add(event_name)
        if result == '1':
            wins[dancer_name] += 1

# Топ-10 по поинтам (российские)
ru_top_points = sorted([(n, p, len(events[n])) for n, p in points.items()], key=lambda x: x[1], reverse=True)[:10]

print("Топ-10 по поинтам (skill-level):")
print("="*70)
for i, (name, pts, evts) in enumerate(ru_top_points, 1):
    w = wins.get(name, 0)
    print(f"{i:2d}. {name:35s} | Поинты: {pts:5.0f} | Победы: {w} | Ивенты: {evts}")

# Проверяем, кто в ru-wins топе
ru_wins_in_html = [
    'Daniel Pavlov', 'Ekaterina Gorianaya', 'Ilmira Galieva', 'Pavel Katunin',
    'Anastasiya Ivanova', 'Anastasiya Yuzhakova', 'Artem Lebsak', 'Artur Radzikhovsky',
    'Elena Kotelnikova', 'Fedor Mayboroda', 'Ilyas Galiev', 'Konstantin Salin',
    'Olga Mikheeva', 'Tatiana Kaneva', 'Vasiliy Skurydin', 'Viacheslav Volkov'
]

print("\n" + "="*70)
print("Проверка ru-wins топа:")
print("="*70)
ru_top_names = {name for name, _, _ in ru_top_points}
for name in ru_wins_in_html:
    in_top_points = name in ru_top_names
    pts = points.get(name, 0)
    w = wins.get(name, 0)
    status = "✓" if in_top_points else "✗"
    print(f"{status} {name:35s} | Поинты: {pts:5.0f} | Победы: {w} {'[НЕТ В ТОП-10 ПО ПОИНТАМ]' if not in_top_points else ''}")

