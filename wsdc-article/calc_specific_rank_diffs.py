import csv
from collections import defaultdict

DANCERS_FILE = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
EVENTS_FILE = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

TARGET_EVENTS = {
    "Global": [
        "Asia WCS Open", "West In Lyon", "St.Petersburg WCS Nights", "King Swing", "MY Swing",
        "Midnight Madness WCS", "SwingCouver", "Swing & Snow", "Swing Over", "BudaFest"
    ],
    "Europe": [
        "West In Lyon", "St.Petersburg WCS Nights", "Swing & Snow", "BudaFest",
        "Mediterranean Open WCS", "D-Townswing", "Swingside Invitational", "Rock The Barn",
        "Warsaw Summer Nights Westival", "SwingVester"
    ],
    "US": [
        "Midnight Madness WCS", "SwingCouver", "Swing Over", "Boogie By The Bay",
        "Austin Rocks", "Trilogy Swing", "Midwest Westie Fest", "Rose City Swing",
        "Swing City Chicago", "Wild Wild Westie"
    ]
}

EUROPE_COUNTRIES = [
    "France", "Germany", "United Kingdom", "Russia", "Poland", "Hungary", "Sweden", "Finland",
    "Italy", "Spain", "Netherlands", "Switzerland", "Austria", "Norway", "Belgium", "Czech Republic",
    "Ukraine", "Ireland", "Israel", "Estonia", "Romania", "Latvia", "Lithuania"
]

def get_region(location):
    if not location: return "Other"
    loc = location.lower()
    if "united states" in loc or " usa" in loc: return "US"
    # Check for US State codes if needed, but usually Country is present.
    # Actually, many US events might just say "Phoenix, AZ".
    # Simple heuristic: if ends with 2 uppercase letters or "USA".
    
    for country in EUROPE_COUNTRIES:
        if country.lower() in loc:
            return "Europe"
    
    # Fallback for US states
    us_states = ["AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"]
    for state in us_states:
        if f", {state.lower()}" in loc or f" {state.lower()} " in loc:
            return "US"
            
    return "Other"

def get_ranks():
    # 1. Load Locations
    event_locations = {}
    with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_locations[row['name'].strip()] = row['location']

    # 2. Load Dancers (only Skill Level divisions)
    SKILL_LEVEL_DIVISIONS = {'Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions'}
    dancer_first_event = {}
    with open(DANCERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only count Skill Level divisions
            competition = row.get('event_competition', '').strip()
            if competition not in SKILL_LEVEL_DIVISIONS:
                continue
                
            dancer_id = row['dancer_id']
            year = int(row['event_year'])
            month = row['event_month']
            event_name = row['event_name'].strip()
            
            try:
                from datetime import datetime
                m_idx = datetime.strptime(month, '%B').month
            except:
                m_idx = 0
            
            date_tuple = (year, m_idx)
            
            if dancer_id not in dancer_first_event:
                dancer_first_event[dancer_id] = {'date': date_tuple, 'event': event_name}
            else:
                if date_tuple < dancer_first_event[dancer_id]['date']:
                    dancer_first_event[dancer_id] = {'date': date_tuple, 'event': event_name}
    
    # 3. Aggregate 2024
    counts_2024 = defaultdict(int)
    for d in dancer_first_event.values():
        if d['date'][0] == 2024:
            counts_2024[d['event']] += 1

    # 4. Rank Lists
    global_list = []
    europe_list = []
    us_list = []

    for event, count in counts_2024.items():
        global_list.append((event, count))
        
        loc = event_locations.get(event, "")
        region = get_region(loc)
        
        if region == "Europe":
            europe_list.append((event, count))
        elif region == "US":
            us_list.append((event, count))
            
    # Sort
    global_list.sort(key=lambda x: (-x[1], x[0]))
    europe_list.sort(key=lambda x: (-x[1], x[0]))
    us_list.sort(key=lambda x: (-x[1], x[0]))
    
    # Rank Maps
    global_ranks = {e: i+1 for i, (e, c) in enumerate(global_list)}
    europe_ranks = {e: i+1 for i, (e, c) in enumerate(europe_list)}
    us_ranks = {e: i+1 for i, (e, c) in enumerate(us_list)}

    # 5. Output
    rank_maps = {
        "Global": global_ranks,
        "Europe": europe_ranks,
        "US": us_ranks
    }

    for category, events in TARGET_EVENTS.items():
        print(f"\n--- {category} Analysis (Comparing to 2024 {category} Rank) ---")
        ranks = rank_maps[category]
        for i, event in enumerate(events):
            current_rank = i + 1
            prev_rank = ranks.get(event)
            
            # Fuzzy fallback
            if not prev_rank:
                for k, v in ranks.items():
                    if event.lower() in k.lower() or k.lower() in event.lower():
                        prev_rank = v
                        break
            
            diff_str = "NEW"
            if prev_rank:
                diff = prev_rank - current_rank
                if diff > 0: diff_str = f"▲ +{diff}"
                elif diff < 0: diff_str = f"▼ {diff}"
                else: diff_str = "="
            
            prev_rank_display = prev_rank if prev_rank else "N/A"
            print(f"{current_rank}. {event:<30} 2024_{category}_Rank: {prev_rank_display:<5} Diff: {diff_str}")

if __name__ == "__main__":
    get_ranks()
