import csv
from collections import defaultdict
from pathlib import Path

DATA_DIR = Path('/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points')
RESULTS_FILE = DATA_DIR / 'dancers_results_info.csv'
DANCERS_FILE = DATA_DIR / 'dancer_role_info.csv'
LOCATION_FILE = DATA_DIR / 'location_info.csv'

skill_levels = {'Newcomer','Novice','Intermediate','Advanced','All-Stars','Champions','Sophisticated'}
dancers_needed = [
    'Nicole Ramirez',
    'Igor Pitangui',
    'Aleksandra Radziejewska',
    'Elena Kotelnikova',
    'Daniel Pavlov',
    'Marina Motronenko',
    'Polina Khapaeva'
]

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

def region(country):
    european = {'United Kingdom','France','Germany','Spain','Italy','Netherlands','Poland','Sweden','Denmark','Norway','Finland','Belgium','Switzerland','Austria','Portugal','Greece','Ireland','Czech Republic','Hungary','Romania','Croatia','Slovenia','Estonia','Latvia','Lithuania','Russia','Ukraine','Belarus','Bulgaria','Serbia'}
    if country in ('United States','Canada'):
        return 'North America'
    if country in european:
        return 'Europe'
    if country in ('Australia','New Zealand'):
        return 'Oceania'
    if country in ('Japan','South Korea','China','Singapore','Thailand','Malaysia','Philippines','Indonesia','Taiwan','Republic of Korea'):
        return 'Asia'
    if country in ('Brazil','Argentina','Mexico','Chile','Colombia'):
        return 'Latin America'
    return 'Other'

stats = {name:{'total_points':0,'wins':0,'regions':defaultdict(float),'wins_regions':defaultdict(int),'events':defaultdict(float)} for name in dancers_needed}

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
        if comp not in skill_levels:
            continue
        points = float(row.get('event_points','0') or 0)
        if points <= 0:
            continue
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        if dancer_name not in stats:
            continue
        country = ''
        city = ''
        loc_id = row.get('location_id','')
        if loc_id in loc:
            country = loc[loc_id]['country']
            city = loc[loc_id]['city']
        reg = region(country)
        st = stats[dancer_name]
        st['total_points'] += points
        st['regions'][reg] += points
        st['events'][row.get('event_name','unknown')] += points
        if str(row.get('event_result','')) == '1':
            st['wins'] +=1
            st['wins_regions'][reg] +=1
        st['last_city'] = city; st['last_country']=country

for name, st in stats.items():
    if st['total_points'] ==0:
        print(f"{name}: нет данных")
        continue
    regions_with_points = len(st['regions'])
    top_reg, top_reg_pts = max(st['regions'].items(), key=lambda x:x[1])
    top_reg_pct = top_reg_pts / st['total_points'] *100
    top_event, top_evt_pts = max(st['events'].items(), key=lambda x:x[1])
    wins_regions = st['wins_regions']
    wins_text = []
    for r,c in wins_regions.items():
        wins_text.append(f"{c} побед в {r}")
    wins_str = ", ".join(wins_text)
    print(f"{name}:")
    print(f"  География: {top_reg_pct:.1f}% поинтов на {top_reg}; регионы с победами: {wins_str if wins_str else 'нет побед'}")
    print(f"  Самый успешный ивент: {top_event} — {int(top_evt_pts)} поинтов")
    print()
