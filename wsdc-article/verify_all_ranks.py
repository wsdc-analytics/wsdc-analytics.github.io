import csv
from collections import defaultdict

filename_points = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'

EVENT_ALIASES = {
    "BudaFest Open WCS Championships": "BudaFest",
    "Budafest WCS Grand Prix": "BudaFest",
    "Budafest": "BudaFest",
    "Asia WCS Open": "Asia WCS Open",
    "Asia West Coast Swing Open": "Asia WCS Open",
    "Asian WCS Open Swingvitation": "Asia WCS Open",
    "St.Petersburg WCS Nights": "St.Petersburg WCS Nights",
    "King Swing": "King Swing",
    "MY Swing": "MY Swing",
    "Midnight Madness WCS": "Midnight Madness WCS",
    "SwingCouver": "SwingCouver",
    "Swing & Snow": "Swing & Snow",
    "Swing Over": "Swing Over",
    "West In Lyon": "West In Lyon",
    "Wild Wild Westie": "Wild Wild Westie",
    "Boogie By The Bay": "Boogie By The Bay",
    "Liberty Swing Dance Championships": "Liberty Swing",
    "Atlanta Swing Classic": "Atlanta Swing Classic",
    "Easter Swing": "Easter Swing",
    "Swingtacular": "Swingtacular",
    "J&J O'Rama": "J&J O'Rama",
    "German Open": "German Open",
    "German Open WCS Championships": "German Open",
}

def normalize_name(name):
    clean = name.split(' 20')[0].strip()
    return EVENT_ALIASES.get(clean, clean)

def get_events_ranking_by_points(year):
    # Skill Level divisions only (excludes age-based and special divisions)
    SKILL_LEVEL_DIVISIONS = {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}
    
    events_points = defaultdict(int)
    
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['event_year'] != str(year):
                continue
            
            # Filter only Skill Level divisions
            competition = row.get('event_competition', '').strip()
            if competition not in SKILL_LEVEL_DIVISIONS:
                continue
            
            event_name = row['event_name']
            try:
                points = int(row['event_points'])
            except:
                continue
            
            norm_name = normalize_name(event_name)
            events_points[norm_name] += points
    
    ranked = sorted(events_points.items(), key=lambda x: x[1], reverse=True)
    return {name: rank+1 for rank, (name, pts) in enumerate(ranked)}

def get_new_dancers_ranking(year):
    # Skill Level divisions only
    SKILL_LEVEL_DIVISIONS = {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}
    
    dancer_first_year = {}
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only count Skill Level divisions for first year determination
            competition = row.get('event_competition', '').strip()
            if competition not in SKILL_LEVEL_DIVISIONS:
                continue
                
            dancer_id = row['dancer_id']
            event_year = int(row['event_year'])
            if dancer_id not in dancer_first_year or event_year < dancer_first_year[dancer_id]:
                dancer_first_year[dancer_id] = event_year
    
    event_new_dancers = defaultdict(int)
    with open(filename_points, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['event_year'] != str(year):
                continue
            
            # Only count Skill Level divisions
            competition = row.get('event_competition', '').strip()
            if competition not in SKILL_LEVEL_DIVISIONS:
                continue
                
            dancer_id = row['dancer_id']
            if dancer_first_year.get(dancer_id) == year:
                event_name = row['event_name']
                norm_name = normalize_name(event_name)
                event_new_dancers[norm_name] += 1
    
    ranked = sorted(event_new_dancers.items(), key=lambda x: x[1], reverse=True)
    return {name: rank+1 for rank, (name, count) in enumerate(ranked)}

if __name__ == "__main__":
    ranks_2024_points = get_events_ranking_by_points(2024)
    ranks_2024_new = get_new_dancers_ranking(2024)
    
    # Global Points top 10 in 2025
    global_points_2025 = {
        "BudaFest": 1,
        "Wild Wild Westie": 2,
        "Boogie By The Bay": 3,
        "Liberty Swing": 4,
        "Atlanta Swing Classic": 5,
        "Easter Swing": 6,
        "Swingtacular": 7,
        "J&J O'Rama": 8,
        "German Open": 9,
        "King Swing": 10,
    }
    
    print("=== Global Points Corrections ===")
    for event, rank_2025 in global_points_2025.items():
        rank_2024 = ranks_2024_points.get(event)
        if rank_2024:
            diff = rank_2024 - rank_2025
            if diff > 0:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = ▲ +{diff}")
            elif diff < 0:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = ▼ {diff}")
            else:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = (no change)")
        else:
            print(f"{event}: NEW (not in 2024 top)")
    
    # Global New Dancers top 10 in 2025
    global_new_2025 = {
        "Asia WCS Open": 1,
        "West In Lyon": 2,
        "St.Petersburg WCS Nights": 3,
        "King Swing": 4,
        "MY Swing": 5,
        "Midnight Madness WCS": 6,
        "SwingCouver": 7,
        "Swing & Snow": 8,
        "Swing Over": 9,
        "BudaFest": 10,
    }
    
    print("\n=== Global New Dancers Corrections ===")
    for event, rank_2025 in global_new_2025.items():
        rank_2024 = ranks_2024_new.get(event)
        if rank_2024:
            diff = rank_2024 - rank_2025
            if diff > 0:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = ▲ +{diff}")
            elif diff < 0:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = ▼ {diff}")
            else:
                print(f"{event}: 2024 rank {rank_2024} → 2025 rank {rank_2025} = (no change)")
        else:
            print(f"{event}: NEW (not in 2024 top)")
