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
        
        if pts > 0:
            points[dancer_name] += pts
        if result == '1':
            wins[dancer_name] += 1

# ru-points топ из HTML (топ-10)
ru_points_top = [
    'Elena Kotelnikova', 'Tatiana Kaneva', 'Polina Khapaeva', 'Marina Kondrateva',
    'Anastasiya Yuzhakova', 'Olga Khvan', 'Kalaychidi Vladislav', 'Anton Zverev',
    'Daniel Pavlov', 'Ekaterina Grigorieva'
]

# Берем только тех, кто в топ-10 по поинтам
wins_filtered = [(name, wins.get(name, 0)) for name in ru_points_top if wins.get(name, 0) > 0]
wins_filtered.sort(key=lambda x: x[1], reverse=True)

print("ru-wins топ (только из ru-points топ-10):")
print("="*60)
for i, (name, w) in enumerate(wins_filtered, 1):
    pts = points.get(name, 0)
    print(f"{i}. {name:35s} | Победы: {w} | Поинты: {pts:.0f}")

