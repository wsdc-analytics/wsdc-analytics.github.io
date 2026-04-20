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
age_based = {'Sophisticated','Masters','Juniors'}

wins_skill = defaultdict(int)
wins_all = defaultdict(int)
points_skill = defaultdict(float)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if not dancer_name:
            continue
        comp = row.get('event_competition','')
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if pts > 0 and comp in skill_levels:
            points_skill[dancer_name] += pts
        
        if result == '1':
            wins_all[dancer_name] += 1
            if comp in skill_levels:
                wins_skill[dancer_name] += 1

# Топ по skill-level победам (для сравнения с ru-wins)
top_wins_skill = sorted([(n, w) for n, w in wins_skill.items() if w > 0], key=lambda x: x[1], reverse=True)

print("Топ по skill-level победам (все танцоры):")
print("="*60)
for i, (name, w) in enumerate(top_wins_skill[:15], 1):
    pts = points_skill.get(name, 0)
    print(f"{i}. {name}: {w} побед (поинты: {pts:.0f})")

# Проверяем Ekaterina Gorianaya отдельно
print("\n" + "="*60)
print("Ekaterina Gorianaya - детализация:")
print(f"  Победы (skill-level): {wins_skill.get('Ekaterina Gorianaya', 0)}")
print(f"  Победы (все): {wins_all.get('Ekaterina Gorianaya', 0)}")
print(f"  Поинты (skill-level): {points_skill.get('Ekaterina Gorianaya', 0):.0f}")

