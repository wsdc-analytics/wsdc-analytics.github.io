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

# Все топ-10 российских танцоров
russian_top = [
    'Elena Kotelnikova', 'Tatiana Kaneva', 'Polina Khapaeva', 'Marina Kondrateva',
    'Anastasiya Yuzhakova', 'Olga Khvan', 'Kalaychidi Vladislav', 'Anton Zverev',
    'Daniel Pavlov', 'Ekaterina Grigorieva'
]

stats = {name:{
    'total_points':0,
    'wins':0,
    'events':0,
    'allstars_points':0,
    'champions_points':0,
    'competitions':defaultdict(int),
    'roles':defaultdict(int)
} for name in russian_top}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            year = int(row.get('event_year','0'))
        except:
            continue
        if year != 2025:
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name not in stats:
            continue
        role = row.get('dancer_role','')
        event_name = row.get('event_name','')
        
        st = stats[dancer_name]
        st['total_points'] += points
        st['competitions'][comp] += 1
        st['roles'][role] += 1
        
        if comp == 'All-Stars':
            st['allstars_points'] += points
        elif comp == 'Champions':
            st['champions_points'] += points
        
        if str(row.get('event_result','')) == '1':
            st['wins'] += 1

# Подсчитываем уникальные ивенты
event_counts = defaultdict(set)
for name in russian_top:
    with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('event_year','') == '2025':
                dancer_id = row.get('dancer_id','')
                if dancer_id_to_name.get(dancer_id,'') == name:
                    event_name = row.get('event_name','')
                    points = float(row.get('event_points','0') or 0)
                    if points > 0:
                        event_counts[name].add(event_name)
    stats[name]['events'] = len(event_counts[name])

print("Статистика российских топ-10 для поиска интересных кандидатов:")
print("="*80)
for name, st in sorted(stats.items(), key=lambda x: x[1]['total_points'], reverse=True):
    if st['total_points'] == 0:
        continue
    print(f"{name}:")
    print(f"  Поинты: {st['total_points']:.0f}, Победы: {st['wins']}, Ивенты: {st['events']}")
    print(f"  All-Stars: {st['allstars_points']:.0f}, Champions: {st['champions_points']:.0f}")
    print(f"  Номинации: {dict(st['competitions'])}")
    print(f"  Роли: {dict(st['roles'])}")
    print()

