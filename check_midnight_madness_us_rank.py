#!/usr/bin/env python3
"""
Проверка рейтинга Midnight Madness WCS в США по новым участникам в 2024 году
"""

import csv
from collections import defaultdict

# Skill Level divisions only
SKILL_LEVEL_DIVISIONS = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions']

def get_new_dancers_by_event_2024():
    """Получить количество новых участников по ивентам в 2024 году (только США)"""
    
    # Читаем данные о результатах
    results_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    events_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'
    
    # Маппинг event_instance_id -> event name и location
    events_map = {}
    with open(events_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_instance_id = int(row['event_instance_id'])
            events_map[event_instance_id] = {
                'name': row['name'],
                'location': row['location']
            }
    
    # Собираем новых участников по ивентам
    new_dancers_by_event = defaultdict(set)  # event_instance_id -> set of dancer IDs
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            event_instance_id = int(row['event_instance_id'])
            dancer_id = int(row['dancer_id'])
            division = row['division']
            year = int(row['year'])
            
            # Только 2024 год
            if year != 2024:
                continue
            
            # Только Skill Level divisions
            if division not in SKILL_LEVEL_DIVISIONS:
                continue
            
            # Проверяем, что это первый результат танцора (новый участник)
            # Для этого нужно проверить, есть ли у танцора результаты в более ранних годах
            # Но для упрощения, будем считать всех участников в 2024 как потенциально новых
            # и проверим их первые результаты отдельно
            
            new_dancers_by_event[event_instance_id].add(dancer_id)
    
    # Теперь проверяем, какие танцоры действительно новые (получили первые поинты в 2024)
    # Читаем все результаты до 2024
    dancers_with_previous_points = set()
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            year = int(row['year'])
            if year < 2024:
                dancer_id = int(row['dancer_id'])
                division = row['division']
                if division in SKILL_LEVEL_DIVISIONS:
                    dancers_with_previous_points.add(dancer_id)
    
    # Фильтруем: оставляем только тех, кто получил первые поинты в 2024
    new_dancers_2024_by_event = {}
    for event_id, dancer_set in new_dancers_by_event.items():
        new_dancers = dancer_set - dancers_with_previous_points
        if new_dancers:
            new_dancers_2024_by_event[event_id] = len(new_dancers)
    
    # Фильтруем только США
    us_events = {}
    for event_id, count in new_dancers_2024_by_event.items():
        if event_id in events_map:
            location = events_map[event_id]['location']
            if 'United States' in location or ', US' in location or ', USA' in location:
                event_name = events_map[event_id]['name']
                us_events[event_id] = {
                    'name': event_name,
                    'location': location,
                    'new_dancers': count
                }
    
    # Сортируем по количеству новых участников
    sorted_events = sorted(us_events.items(), key=lambda x: x[1]['new_dancers'], reverse=True)
    
    # Ищем Midnight Madness
    midnight_madness_rank = None
    for rank, (event_id, data) in enumerate(sorted_events, 1):
        if 'Midnight Madness' in data['name']:
            midnight_madness_rank = rank
            print(f"\n🎯 Midnight Madness WCS найден:")
            print(f"   Ранг в США (2024): {rank}")
            print(f"   Новых участников: {data['new_dancers']}")
            print(f"   Локация: {data['location']}")
            break
    
    # Показываем топ 10
    print(f"\n📊 Топ 10 США по новым участникам (2024):")
    for rank, (event_id, data) in enumerate(sorted_events[:10], 1):
        marker = "🎯" if 'Midnight Madness' in data['name'] else "  "
        print(f"{marker} {rank:2d}. {data['name']:50s} - {data['new_dancers']:3d} новых")
    
    if midnight_madness_rank is None:
        print("\n⚠️  Midnight Madness WCS не найден в топе США 2024 года")
        print("   Это означает, что он был вне топ-10 или не проводился в 2024")
    
    return midnight_madness_rank, sorted_events

if __name__ == '__main__':
    rank, events = get_new_dancers_by_event_2024()


