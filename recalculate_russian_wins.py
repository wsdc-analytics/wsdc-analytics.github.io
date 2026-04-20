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

# Собираем всех танцоров
wins = defaultdict(int)
points = defaultdict(float)

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

# Берем только тех, кто есть в топ-10 по поинтам среди "российских" (или всех)
# Проверяем Ekaterina Gorianaya отдельно
print("Ekaterina Gorianaya:")
print(f"  Поинты (skill-level): {points.get('Ekaterina Gorianaya', 0):.0f}")
print(f"  Победы (skill-level): {wins.get('Ekaterina Gorianaya', 0)}")

# Топ по поинтам (для справки)
top_points = sorted([(n, p) for n, p in points.items()], key=lambda x: x[1], reverse=True)
print(f"\nТоп-10 по skill-level поинтам (все танцоры):")
for i, (name, pts) in enumerate(top_points[:10], 1):
    print(f"{i}. {name}: {pts:.0f}")

# Топ по победам
top_wins = sorted([(n, w) for n, w in wins.items() if w > 0], key=lambda x: x[1], reverse=True)
print(f"\nТоп по skill-level победам (все танцоры):")
for i, (name, w) in enumerate(top_wins[:15], 1):
    print(f"{i}. {name}: {w}")

