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

# Российские танцоры
russian_dancers = [
    'Elena Kotelnikova', 'Tatiana Kaneva', 'Polina Khapaeva', 'Marina Kondrateva',
    'Anastasiya Yuzhakova', 'Olga Khvan', 'Kalaychidi Vladislav', 'Anton Zverev',
    'Daniel Pavlov', 'Ekaterina Grigorieva', 'Marina Motronenko', 'Ekaterina Gorianaya'
]

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}

wins = {name: {'skill':0, 'all':0} for name in russian_dancers}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name not in wins:
            continue
        comp = row.get('event_competition','')
        result = str(row.get('event_result',''))
        
        if result == '1':
            wins[dancer_name]['all'] += 1
            if comp in skill_levels:
                wins[dancer_name]['skill'] += 1

print("Победы российских танцоров:")
print("="*60)
for name in sorted(russian_dancers):
    if wins[name]['all'] > 0 or wins[name]['skill'] > 0:
        print(f"{name}:")
        print(f"  Все победы: {wins[name]['all']}")
        print(f"  Skill-level победы: {wins[name]['skill']}")
        if wins[name]['all'] != wins[name]['skill']:
            print(f"  ⚠️ РАЗНИЦА!")
        print()

