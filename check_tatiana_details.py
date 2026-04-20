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

stats = {'Tatiana Kaneva':{'competitions':defaultdict(int),'wins_by_comp':defaultdict(int),'events':set()}}

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        comp = row.get('event_competition','')
        if comp not in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name != 'Tatiana Kaneva':
            continue
        
        st = stats['Tatiana Kaneva']
        st['competitions'][comp] += 1
        st['events'].add(row.get('event_name',''))
        
        if str(row.get('event_result','')) == '1':
            st['wins_by_comp'][comp] += 1

st = stats['Tatiana Kaneva']
skill_levels = {k:v for k,v in st['competitions'].items() if k in {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions'}}
age_based = {k:v for k,v in st['competitions'].items() if k in {'Sophisticated','Masters','Juniors'}}

print(f"Tatiana Kaneva:")
print(f"  Skill-level номинации: {dict(skill_levels)}")
print(f"  Age-based номинации: {dict(age_based)}")
print(f"  Победы: {dict(st['wins_by_comp'])}")
print(f"  Ивенты: {len(st['events'])}")

