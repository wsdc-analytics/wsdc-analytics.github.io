import csv

filename_events = 'projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

# List of events from the article
target_events = [
    "BudaFest Open WCS Championships", # BudaFest
    "Wild Wild Westie",
    "Boogie By The Bay",
    "Liberty Swing Dance Championships",
    "Atlanta Swing Classic",
    "Asia WCS Open",
    "West In Lyon",
    "St.Petersburg WCS Nights",
    "King Swing",
    "MY Swing",
    "German Open",
    "Warsaw Halloween Swing",
    "Milan Modern Swing",
    "Paris Westie Fest",
    "Bavarian Open",
    "Finnfest",
    "SwingVester",
    "UK WCS Championships",
    "Mediterranean Open WCS",
    "D-Townswing",
    "Swingside Invitational",
    "Rock The Barn",
    "Warsaw Summer Nights Westival",
    "St.Petersburg WCS Nights",
    "Swing & Snow",
    "Moscow Westie Fest Gala Edition",
    "Shooba Dooba Swing",
    "HONEY FEST",
    "Americano Dance Camp",
    "Sea Dance Fest"
]

# Normalize names for matching
target_map = {name.lower(): name for name in target_events}

found_urls = {}

try:
    with open(filename_events, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name']
            url = row['url']
            
            # Simple fuzzy match attempt
            name_lower = name.lower()
            
            # Check exact match first
            if name_lower in target_map:
                found_urls[target_map[name_lower]] = url
            else:
                # Check partial match
                for target in target_map:
                    if target in name_lower or name_lower in target:
                        # Prioritize exact matches if already found, else take this
                        real_name = target_map[target]
                        if real_name not in found_urls:
                            found_urls[real_name] = url

except FileNotFoundError:
    print(f"Error: {filename_events} not found.")

print("Found URLs:")
for event in target_events:
    url = found_urls.get(event, "NOT FOUND")
    print(f"{event}: {url}")

