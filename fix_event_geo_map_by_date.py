#!/usr/bin/env python3
"""
Проверяем, как правильно строить event_geo_map с учетом дат
"""

import csv
import sys
from datetime import datetime

sys.path.insert(0, '/Users/ania/.cursor')
from normalize_geo_data import normalize_location

filename_events = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

def parse_event_date(date_str):
    """Парсит дату события"""
    if not date_str:
        return None
    
    try:
        # Пробуем разные форматы
        for fmt in ['%B %Y', '%b %Y', '%Y-%m-%d', '%Y/%m/%d', '%d.%m.%Y', '%m/%d/%Y', '%B %d, %Y']:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except:
                continue
        return None
    except:
        return None

# Build Event Location Map с учетом дат
event_geo_map = {}
event_by_id = {}  # По ID события

print("Построение event_geo_map с учетом дат...")
with open(filename_events, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        event_id = row.get('id', '').strip()
        name = row['name'].strip()
        loc = row.get('location', '').strip()
        date_str = row.get('date', '').strip()
        
        if name and loc:
            city, state, country = normalize_location(loc)
            if country:
                event_date = parse_event_date(date_str)
                
                # Сохраняем по ID (уникальный ключ)
                if event_id:
                    event_by_id[event_id] = {
                        'name': name,
                        'city': city,
                        'state': state,
                        'country': country,
                        'raw_loc': loc,
                        'date': event_date,
                        'date_str': date_str
                    }
                
                # Для событий с одинаковым названием выбираем самое позднее
                if name not in event_geo_map:
                    event_geo_map[name] = {
                        'city': city,
                        'state': state,
                        'country': country,
                        'raw_loc': loc,
                        'date': event_date,
                        'date_str': date_str
                    }
                else:
                    # Если дата есть, выбираем более позднее событие
                    existing_date = event_geo_map[name].get('date')
                    if event_date and (not existing_date or event_date > existing_date):
                        event_geo_map[name] = {
                            'city': city,
                            'state': state,
                            'country': country,
                            'raw_loc': loc,
                            'date': event_date,
                            'date_str': date_str
                        }

print(f"\n✅ Построено {len(event_geo_map)} событий по названию")
print(f"✅ Построено {len(event_by_id)} событий по ID")

# Проверяем Worlds UCWDC
print(f"\n🔍 Проверка 'Worlds UCWDC':")
if 'Worlds UCWDC' in event_geo_map:
    geo = event_geo_map['Worlds UCWDC']
    print(f"  Локация: {geo['raw_loc']}")
    print(f"  Нормализовано: {geo['city']}, {geo['state']}, {geo['country']}")
    print(f"  Дата: {geo.get('date_str', 'N/A')}")

# Проверяем для 2025 года - какое событие должно использоваться
print(f"\n🔍 События Worlds UCWDC для 2025 года:")
for event_id, event_data in event_by_id.items():
    if 'Worlds UCWDC' in event_data['name'] or 'UCWDC' in event_data['name']:
        if event_data.get('date') and event_data['date'].year == 2025:
            print(f"  ID {event_id}: {event_data['name']}")
            print(f"    Локация: {event_data['raw_loc']}")
            print(f"    Дата: {event_data['date_str']}")

