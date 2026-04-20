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

wins_skill = []
wins_all = []
points_skill = 0
points_all = 0

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name != 'Ekaterina Gorianaya':
            continue
        comp = row.get('event_competition','')
        points = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        
        if result == '1':
            wins_all.append({
                'event': row.get('event_name',''),
                'comp': comp,
                'points': points
            })
            if comp in skill_levels:
                wins_skill.append({
                    'event': row.get('event_name',''),
                    'comp': comp,
                    'points': points
                })
        
        if points > 0:
            points_all += points
            if comp in skill_levels:
                points_skill += points

print(f"Ekaterina Gorianaya - все победы (2025):")
print(f"  Всего побед: {len(wins_all)}")
for win in wins_all:
    print(f"    {win['event']} - {win['comp']} ({win['points']} поинтов)")

print(f"\nПобеды в skill-level номинациях: {len(wins_skill)}")
for win in wins_skill:
    print(f"    {win['event']} - {win['comp']} ({win['points']} поинтов)")

print(f"\nПоинты:")
print(f"  Всего: {points_all:.0f}")
print(f"  Skill-level: {points_skill:.0f}")

