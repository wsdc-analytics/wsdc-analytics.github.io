import csv
from datetime import datetime
from collections import defaultdict

filename_points = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
filename_events = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

ALLOWED_DIVISIONS = {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}

EUROPEAN_COUNTRIES = {
    'France', 'Germany', 'United Kingdom', 'UK', 'Hungary', 'Sweden', 'Poland', 'Norway', 
    'Finland', 'Switzerland', 'Austria', 'Italy', 'Spain', 'Netherlands', 'Ukraine', 
    'Estonia', 'Latvia', 'Czech Republic', 'Ireland', 'Belgium', 'Portugal', 'Romania', 'Scotland', 'England'
}

# Load Russian and European events
russian_events = set()
european_events = set()
try:
    with open(filename_events, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            loc = row['location']
            if 'Russia' in loc:
                russian_events.add(row['name'])
            
            # Check for Europe (excluding Russia)
            is_euro = False
            for country in EUROPEAN_COUNTRIES:
                if country in loc:
                    is_euro = True
                    break
            
            # Catch some cities if country missing or different format
            if not is_euro and any(city in loc for city in ['Budapest', 'Paris', 'Lyon', 'London', 'Berlin', 'Munich', 'Vienna', 'Zurich', 'Stockholm', 'Oslo', 'Warsaw', 'Krakow']):
                is_euro = True
            
            if is_euro: # Russia is already in 'is_euro' logic if location matches list, but let's be explicit
                european_events.add(row['name'])
            
            # Explicitly add Russia to Europe if not caught above
            if 'Russia' in loc:
                 european_events.add(row['name'])

except FileNotFoundError:
    print(f"Error: {filename_events} not found.")

# Data structures
# stats[year][event_name] = {'unique_dancers': set(), 'total_points': 0, 'new_dancers': 0}
stats = {
    '2024': defaultdict(lambda: {'unique_dancers': set(), 'total_points': 0, 'new_dancers': 0}),
    '2025': defaultdict(lambda: {'unique_dancers': set(), 'total_points': 0, 'new_dancers': 0})
}

dancer_first_date = {} # dancer_id -> datetime
dancer_first_event = {} # dancer_id -> event_name
dancer_first_year = {} # dancer_id -> year string

# Pass 1: Determine first point date for every dancer
try:
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['event_competition'] not in ALLOWED_DIVISIONS:
                continue
                
            dancer_id = row['dancer_id']
            date_str = row['event_year_and_month']
            try:
                event_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                continue

            if dancer_id not in dancer_first_date or event_date < dancer_first_date[dancer_id]:
                dancer_first_date[dancer_id] = event_date
                dancer_first_event[dancer_id] = row['event_name']
                dancer_first_year[dancer_id] = row['event_year']
            elif event_date == dancer_first_date[dancer_id]:
                pass
except FileNotFoundError:
    print(f"Error: {filename_points} not found.")
    exit()

# Pass 2: Aggregate stats for 2024 and 2025
with open(filename_points, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['event_competition'] not in ALLOWED_DIVISIONS:
            continue

        event_year = row['event_year']
        if event_year not in ['2024', '2025']:
            continue

        event_name = row['event_name']
        dancer_id = row['dancer_id']
        points = int(row['event_points'])

        stats[event_year][event_name]['unique_dancers'].add(dancer_id)
        stats[event_year][event_name]['total_points'] += points

# Calculate New Dancers metric
for dancer_id, year in dancer_first_year.items():
    if year in ['2024', '2025']:
        first_event = dancer_first_event[dancer_id]
        if first_event in stats[year]:
            stats[year][first_event]['new_dancers'] += 1

# Compile results with growth
results = []
# We only care about events that happened in 2025 for the ranking, 
# but we need 2024 data for growth comparison.
for event_name, metrics_2025 in stats['2025'].items():
    metrics_2024 = stats['2024'].get(event_name, {'unique_dancers': set(), 'total_points': 0, 'new_dancers': 0})
    
    val_unique_2025 = len(metrics_2025['unique_dancers'])
    val_unique_2024 = len(metrics_2024['unique_dancers'])
    growth_unique = val_unique_2025 - val_unique_2024
    pct_unique = (growth_unique / val_unique_2024 * 100) if val_unique_2024 > 0 else 100.0 if val_unique_2025 > 0 else 0.0

    val_points_2025 = metrics_2025['total_points']
    val_points_2024 = metrics_2024['total_points']
    growth_points = val_points_2025 - val_points_2024
    pct_points = (growth_points / val_points_2024 * 100) if val_points_2024 > 0 else 100.0 if val_points_2025 > 0 else 0.0
    
    val_new_2025 = metrics_2025['new_dancers']
    val_new_2024 = metrics_2024['new_dancers']
    growth_new = val_new_2025 - val_new_2024
    pct_new = (growth_new / val_new_2024 * 100) if val_new_2024 > 0 else 100.0 if val_new_2025 > 0 else 0.0

    results.append({
        'Event Name': event_name,
        'Unique Dancers': val_unique_2025,
        'Unique Growth': f"{growth_unique:+d} ({pct_unique:+.1f}%)",
        'Total Points': val_points_2025,
        'Points Growth': f"{growth_points:+d} ({pct_points:+.1f}%)",
        'New Dancers': val_new_2025,
        'New Dancers Growth': f"{growth_new:+d} ({pct_new:+.1f}%)",
        'Is Russian': event_name in russian_events,
        'Is European': event_name in european_events
    })

def print_table(data, sort_key, title, limit=5):
    print(f"\n### {title}")
    # Sort by the numeric value of the key (not the growth string)
    sorted_data = sorted(data, key=lambda x: x[sort_key], reverse=True)[:limit]
    
    # Determine which growth key corresponds to the sort key
    growth_key = ''
    if sort_key == 'Unique Dancers': growth_key = 'Unique Growth'
    elif sort_key == 'Total Points': growth_key = 'Points Growth'
    elif sort_key == 'New Dancers': growth_key = 'New Dancers Growth'
    
    print(f"| Event Name | {sort_key} | Growth vs 2024 |")
    print(f"|---|---|---|")
    for item in sorted_data:
        print(f"| {item['Event Name']} | {item[sort_key]} | {item[growth_key]} |")

# Global Top 10
print("## 🌍 Global Top 10 Events (2025)")
print_table(results, 'Unique Dancers', 'By Unique Dancers', 10)
print_table(results, 'Total Points', 'By Total Points', 10)
print_table(results, 'New Dancers', 'By New Dancers', 10)

# Russian Top All
russian_results = [r for r in results if r['Is Russian']]
print("\n## 🇷🇺 All Russian Events (2025) - DETAILED")
print(f"{'Event Name':<40} | {'Points':<10} | {'Growth':<15} | {'Unique':<8} | {'New':<5}")
print("-" * 90)
sorted_rus = sorted(russian_results, key=lambda x: x['Total Points'], reverse=True)
for item in sorted_rus:
    print(f"{item['Event Name']:<40} | {item['Total Points']:<10} | {item['Points Growth']:<15} | {item['Unique Dancers']:<8} | {item['New Dancers']:<5}")



# European Top 10
european_results = [r for r in results if r['Is European']]
print("\n## 🇪🇺 European Top 10 Events (2025)")
print_table(european_results, 'Total Points', 'By Total Points', 10)
print_table(european_results, 'New Dancers', 'By New Dancers', 10)

