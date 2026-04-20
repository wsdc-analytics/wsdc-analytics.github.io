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

# Словари для хранения данных по каждой номинации
all_stars_points = defaultdict(float)
advanced_points = defaultdict(float)
intermediate_points = defaultdict(float)

all_stars_wins = defaultdict(int)
advanced_wins = defaultdict(int)
intermediate_wins = defaultdict(int)

all_stars_events = defaultdict(set)
advanced_events = defaultdict(set)
intermediate_events = defaultdict(set)

with open(RESULTS_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get('event_year','') != '2025':
            continue
        
        comp = row.get('event_competition','')
        dancer_id = row.get('dancer_id','')
        dancer_name = dancer_id_to_name.get(dancer_id,'')
        
        if not dancer_name:
            continue
        
        pts = float(row.get('event_points','0') or 0)
        result = str(row.get('event_result',''))
        event_name = row.get('event_name','')
        
        if pts > 0:
            if comp == 'All-Stars':
                all_stars_points[dancer_name] += pts
                all_stars_events[dancer_name].add(event_name)
            elif comp == 'Advanced':
                advanced_points[dancer_name] += pts
                advanced_events[dancer_name].add(event_name)
            elif comp == 'Intermediate':
                intermediate_points[dancer_name] += pts
                intermediate_events[dancer_name].add(event_name)
        
        if result == '1':
            if comp == 'All-Stars':
                all_stars_wins[dancer_name] += 1
            elif comp == 'Advanced':
                advanced_wins[dancer_name] += 1
            elif comp == 'Intermediate':
                intermediate_wins[dancer_name] += 1

def format_top(data_dict, wins_dict, events_dict, comp_name):
    top = sorted([(n, p) for n, p in data_dict.items() if p > 0], key=lambda x: x[1], reverse=True)[:10]
    
    print(f"\n{'='*70}")
    print(f"Топ-10 по поинтам в номинации {comp_name} (2025, все ивенты):")
    print("="*70)
    for i, (name, num_points) in enumerate(top, 1):
        num_events = len(events_dict[name])
        num_wins = wins_dict[name]
        print(f"{i}. {name}: {num_points:.0f} поинтов ({num_events} ивентов, {num_wins} побед)")
    
    print(f"\nJavaScript данные для {comp_name}:")
    print("[")
    rank = 1
    for i, (name, value) in enumerate(top):
        tied = (i > 0 and top[i-1][1] == value) or (i < len(top)-1 and top[i+1][1] == value)
        top3 = rank <= 3
        comma = "," if i < len(top) - 1 else ""
        print(f"                {{rank: {rank}, name: '{name}', value: {int(value)}, top3: {str(top3).lower()}, tied: {str(tied).lower()}}}{comma}")
        if i < len(top) - 1 and top[i+1][1] != value:
            rank = i + 2
    print("]")

# Выводим результаты для каждой номинации
format_top(all_stars_points, all_stars_wins, all_stars_events, "All-Stars")
format_top(advanced_points, advanced_wins, advanced_events, "Advanced")
format_top(intermediate_points, intermediate_wins, intermediate_events, "Intermediate")
