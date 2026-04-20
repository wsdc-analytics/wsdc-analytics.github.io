#!/usr/bin/env python3
"""
Сравнение результатов расчета с данными в статье
"""

# Данные из статьи (из geo_2025.html)
article_data = {
    'cities': {
        'Stockholm, Sweden': {'points': 2069, 'events': 5, 'unique': 368, 'new': 68},
        'Budapest, Hungary': {'points': 1934, 'events': 4, 'unique': 337, 'new': 76},
        'Washington, DC, United States': {'points': 824, 'events': 2, 'unique': 167, 'new': 57},  # БЫЛО 57, стало 74
        'San Francisco, CA, United States': {'points': 1292, 'events': 2, 'unique': 220, 'new': 28},
        'Boston, MA, United States': {'points': 1276, 'events': 3, 'unique': 248, 'new': 45},
        'Orlando, FL, United States': {'points': 1136, 'events': 4, 'unique': 248, 'new': 53},
        'Atlanta, GA, United States': {'points': 1101, 'events': 2, 'unique': 205, 'new': 35},
        'Freiburg, Germany': {'points': 1088, 'events': 2, 'unique': 210, 'new': 35},  # Было 42, стало 45
        'Phoenix, AZ, United States': {'points': 1082, 'events': 3, 'unique': 207, 'new': 17},
        'Kraków, Poland': {'points': 1025, 'events': 2, 'unique': 191, 'new': 46},
        'Seattle, WA, United States': {'points': 965, 'events': 2, 'unique': 188, 'new': 35},
    },
    'us_states': {
        'CA': {'points': 5472, 'events': 12, 'unique': 619, 'new': 96},  # Было 127, стало 128
        'TX': {'points': 3063, 'events': 8, 'unique': 434, 'new': 123},
        'FL': {'points': 1884, 'events': 7, 'unique': 343, 'new': 83},  # Было 76, стало 85
        'OR': {'points': 1736, 'events': 5, 'unique': 316, 'new': 85},
        'MA': {'points': 1505, 'events': 4, 'unique': 286, 'new': 55},
        'IL': {'points': 1178, 'events': 3, 'unique': 246, 'new': 50},
        'GA': {'points': 1101, 'events': 2, 'unique': 205, 'new': 35},
        'AZ': {'points': 1082, 'events': 3, 'unique': 207, 'new': 17},
        'NC': {'points': 990, 'events': 2, 'unique': 185, 'new': 40},
        'DC': {'points': 824, 'events': 2, 'unique': 167, 'new': 74},  # БЫЛО 74
        'WA': {'points': 965, 'events': 2, 'unique': 188, 'new': 36},
    },
    'countries': {
        'France': {'points': 4280, 'events': 11, 'unique': 600, 'new': 161},  # Было 169, стало 173
        'Germany': {'points': 3843, 'events': 10, 'unique': 580, 'new': 173},  # Было 194, стало 197
        'Sweden': {'points': 2603, 'events': 7, 'unique': 444, 'new': 110},
        'Poland': {'points': 2393, 'events': 5, 'unique': 402, 'new': 108},
        'Russia': {'points': 2037, 'events': 7, 'unique': 256, 'new': 95},
        'United Kingdom': {'points': 2012, 'events': 7, 'unique': 369, 'new': 98},
        'Hungary': {'points': 1934, 'events': 4, 'unique': 337, 'new': 76},
        'Canada': {'points': 1359, 'events': 6, 'unique': 277, 'new': 75},
        'Finland': {'points': 1037, 'events': 3, 'unique': 194, 'new': 56},
        'Spain': {'points': 963, 'events': 3, 'unique': 200, 'new': 69},  # Было 64
    }
}

# Результаты правильного расчета
correct_data = {
    'cities': {
        'Stockholm, Sweden': {'points': 2069, 'events': 5, 'unique': 368, 'new': 68},
        'Budapest, Hungary': {'points': 1934, 'events': 4, 'unique': 337, 'new': 76},
        'Washington, DC, United States': {'points': 824, 'events': 2, 'unique': 167, 'new': 35},
        'San Francisco, CA, United States': {'points': 1292, 'events': 2, 'unique': 220, 'new': 28},
        'Boston, MA, United States': {'points': 1276, 'events': 3, 'unique': 248, 'new': 45},
        'Orlando, FL, United States': {'points': 1136, 'events': 4, 'unique': 248, 'new': 53},
        'Atlanta, GA, United States': {'points': 1101, 'events': 2, 'unique': 205, 'new': 35},
        'Freiburg, Germany': {'points': 1088, 'events': 2, 'unique': 210, 'new': 35},
        'Phoenix, AZ, United States': {'points': 1082, 'events': 3, 'unique': 207, 'new': 17},
        'Kraków, Poland': {'points': 1025, 'events': 2, 'unique': 191, 'new': 46},
        'Seattle, WA, United States': {'points': 965, 'events': 2, 'unique': 188, 'new': 35},
    },
    'us_states': {
        'CA': {'points': 5472, 'events': 12, 'unique': 619, 'new': 96},
        'TX': {'points': 3063, 'events': 8, 'unique': 434, 'new': 123},
        'FL': {'points': 1884, 'events': 7, 'unique': 343, 'new': 83},
        'OR': {'points': 1736, 'events': 5, 'unique': 316, 'new': 85},
        'MA': {'points': 1505, 'events': 4, 'unique': 286, 'new': 55},
        'IL': {'points': 1178, 'events': 3, 'unique': 246, 'new': 50},
        'GA': {'points': 1101, 'events': 2, 'unique': 205, 'new': 35},
        'AZ': {'points': 1082, 'events': 3, 'unique': 207, 'new': 17},
        'NC': {'points': 990, 'events': 2, 'unique': 185, 'new': 40},
        'DC': {'points': 824, 'events': 2, 'unique': 167, 'new': 35},
        'WA': {'points': 965, 'events': 2, 'unique': 188, 'new': 36},
    },
    'countries': {
        'France': {'points': 4280, 'events': 11, 'unique': 600, 'new': 161},
        'Germany': {'points': 3843, 'events': 10, 'unique': 580, 'new': 173},
        'Sweden': {'points': 2603, 'events': 7, 'unique': 444, 'new': 110},
        'Poland': {'points': 2393, 'events': 5, 'unique': 402, 'new': 108},
        'Russia': {'points': 2037, 'events': 7, 'unique': 256, 'new': 95},
        'United Kingdom': {'points': 2012, 'events': 7, 'unique': 369, 'new': 98},
        'Hungary': {'points': 1934, 'events': 4, 'unique': 337, 'new': 76},
        'Canada': {'points': 1359, 'events': 6, 'unique': 277, 'new': 75},
        'Finland': {'points': 1037, 'events': 3, 'unique': 194, 'new': 56},
        'Spain': {'points': 963, 'events': 3, 'unique': 200, 'new': 69},
    }
}

print("="*80)
print("СРАВНЕНИЕ: Статья vs Правильный расчет (разница в 'New')")
print("="*80)

for table_type in ['cities', 'us_states', 'countries']:
    print(f"\n📊 {table_type.upper()}:")
    print(f"{'Name':<40} | {'В статье':<8} | {'Правильно':<8} | {'Разница':<8}")
    print("-" * 70)
    
    for name in article_data[table_type]:
        if name not in correct_data[table_type]:
            continue
        
        article_new = article_data[table_type][name]['new']
        correct_new = correct_data[table_type][name]['new']
        
        if article_new != correct_new:
            diff = correct_new - article_new
            print(f"{name:<40} | {article_new:<8} | {correct_new:<8} | {diff:+d}")

