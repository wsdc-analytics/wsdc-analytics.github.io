#!/usr/bin/env python3
"""
Сравнение двух подходов к подсчету новых танцоров:
1. Только skill level дивизионы
2. Все дивизионы (включая Masters, Sophisticated и т.д.)
"""

import csv
from collections import defaultdict

EVENT_IDS = {
    'Arousa Westie Fest': 344,
    'BeeMAD': 347,
    'Mediterranean Open WCS': 375
}

SKILL_LEVEL_DIVISIONS = {
    'Newcomer', 'Novice', 'Intermediate', 'Advanced', 
    'All-Stars', 'All-Star', 'All Stars', 'Champions'
}

def calculate_approach_1_skill_level_only():
    """Подход 1: Только skill level дивизионы для определения новых танцоров"""
    results_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    
    events_data = defaultdict(lambda: {'total_points': 0, 'dancers': set(), 'new_dancers': set()})
    dancer_first_year = {}
    dancer_first_event = {}
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        
        # Первый год - только skill level
        for row in all_rows:
            dancer_id = row.get('dancer_id', '')
            year = row.get('event_year', '')
            competition = row.get('event_competition', '')
            points_str = row.get('event_points', '0')
            
            if competition in SKILL_LEVEL_DIVISIONS:
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    if points > 0:
                        year_int = int(year) if year else 9999
                        if dancer_id and year_int < 9999:
                            if dancer_id not in dancer_first_year or year_int < dancer_first_year[dancer_id]:
                                dancer_first_year[dancer_id] = year_int
                except:
                    pass
        
        # Первое событие - только skill level
        for row in all_rows:
            dancer_id = row.get('dancer_id', '')
            year = row.get('event_year', '')
            month = row.get('event_month', '')
            competition = row.get('event_competition', '')
            event_id = row.get('event_name_id', '')
            points_str = row.get('event_points', '0')
            
            if competition in SKILL_LEVEL_DIVISIONS:
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    if points > 0 and dancer_id in dancer_first_year:
                        year_int = int(year) if year else 9999
                        month_int = int(month) if month and month != '' else 13
                        if year_int == dancer_first_year[dancer_id]:
                            if dancer_id not in dancer_first_event:
                                dancer_first_event[dancer_id] = (year_int, month_int, event_id)
                            else:
                                existing_year, existing_month, existing_event = dancer_first_event[dancer_id]
                                if month_int < existing_month or (month_int == existing_month and str(event_id) < str(existing_event)):
                                    dancer_first_event[dancer_id] = (year_int, month_int, event_id)
                except:
                    pass
        
        # Подсчет для событий 2025
        for row in all_rows:
            event_name = row.get('event_name', '')
            event_id = row.get('event_name_id', '')
            year = row.get('event_year', '')
            dancer_id = row.get('dancer_id', '')
            points_str = row.get('event_points', '0')
            competition = row.get('event_competition', '')
            
            matched_event = None
            for search_name, search_id in EVENT_IDS.items():
                if search_name.lower() in event_name.lower() or str(search_id) == str(event_id):
                    matched_event = search_name
                    break
            
            if year == '2025' and matched_event and competition in SKILL_LEVEL_DIVISIONS:
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    events_data[matched_event]['total_points'] += points
                    events_data[matched_event]['dancers'].add(dancer_id)
                    
                    if (dancer_id in dancer_first_year and dancer_first_year[dancer_id] == 2025 and
                        dancer_id in dancer_first_event):
                        first_year, first_month, first_event_id = dancer_first_event[dancer_id]
                        if str(first_event_id) == str(event_id) and points > 0:
                            events_data[matched_event]['new_dancers'].add(dancer_id)
                except:
                    pass
    
    return events_data

def calculate_approach_2_all_divisions():
    """Подход 2: Все дивизионы для определения новых танцоров"""
    results_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    
    events_data = defaultdict(lambda: {'total_points': 0, 'dancers': set(), 'new_dancers': set()})
    dancer_first_year = {}
    dancer_first_event = {}
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        
        # Первый год - ВСЕ дивизионы
        for row in all_rows:
            dancer_id = row.get('dancer_id', '')
            year = row.get('event_year', '')
            points_str = row.get('event_points', '0')
            
            try:
                points = int(float(points_str)) if points_str and points_str != '' else 0
                if points > 0:
                    year_int = int(year) if year else 9999
                    if dancer_id and year_int < 9999:
                        if dancer_id not in dancer_first_year or year_int < dancer_first_year[dancer_id]:
                            dancer_first_year[dancer_id] = year_int
            except:
                pass
        
        # Первое событие - ВСЕ дивизионы
        for row in all_rows:
            dancer_id = row.get('dancer_id', '')
            year = row.get('event_year', '')
            month = row.get('event_month', '')
            event_id = row.get('event_name_id', '')
            points_str = row.get('event_points', '0')
            
            try:
                points = int(float(points_str)) if points_str and points_str != '' else 0
                if points > 0 and dancer_id in dancer_first_year:
                    year_int = int(year) if year else 9999
                    month_int = int(month) if month and month != '' else 13
                    if year_int == dancer_first_year[dancer_id]:
                        if dancer_id not in dancer_first_event:
                            dancer_first_event[dancer_id] = (year_int, month_int, event_id)
                        else:
                            existing_year, existing_month, existing_event = dancer_first_event[dancer_id]
                            if month_int < existing_month or (month_int == existing_month and str(event_id) < str(existing_event)):
                                dancer_first_event[dancer_id] = (year_int, month_int, event_id)
            except:
                pass
        
        # Подсчет для событий 2025 (пункты - только skill level, новые - все дивизионы)
        for row in all_rows:
            event_name = row.get('event_name', '')
            event_id = row.get('event_name_id', '')
            year = row.get('event_year', '')
            dancer_id = row.get('dancer_id', '')
            points_str = row.get('event_points', '0')
            competition = row.get('event_competition', '')
            
            matched_event = None
            for search_name, search_id in EVENT_IDS.items():
                if search_name.lower() in event_name.lower() or str(search_id) == str(event_id):
                    matched_event = search_name
                    break
            
            if year == '2025' and matched_event:
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    # Пункты считаем только для skill level
                    if competition in SKILL_LEVEL_DIVISIONS:
                        events_data[matched_event]['total_points'] += points
                        events_data[matched_event]['dancers'].add(dancer_id)
                    
                    # Новые танцоры - все дивизионы
                    if (dancer_id in dancer_first_year and dancer_first_year[dancer_id] == 2025 and
                        dancer_id in dancer_first_event):
                        first_year, first_month, first_event_id = dancer_first_event[dancer_id]
                        if str(first_event_id) == str(event_id) and points > 0:
                            events_data[matched_event]['new_dancers'].add(dancer_id)
                except:
                    pass
    
    return events_data

def main():
    print("="*70)
    print("СРАВНЕНИЕ ПОДХОДОВ К ПОДСЧЕТУ НОВЫХ ТАНЦОРОВ")
    print("="*70)
    print("\nПодход 1: Только skill level дивизионы для определения новых танцоров")
    print("Подход 2: Все дивизионы для определения новых танцоров (включая Masters, Sophisticated)")
    print("\n" + "="*70 + "\n")
    
    approach_1 = calculate_approach_1_skill_level_only()
    approach_2 = calculate_approach_2_all_divisions()
    
    print(f"{'Событие':<30} {'Подход 1':<20} {'Подход 2':<20} {'Разница':<15}")
    print("-"*85)
    
    for event_name in ['Arousa Westie Fest', 'BeeMAD', 'Mediterranean Open WCS']:
        new1 = len(approach_1[event_name]['new_dancers'])
        new2 = len(approach_2[event_name]['new_dancers'])
        diff = new2 - new1
        diff_str = f"{diff:+d}" if diff != 0 else "0"
        print(f"{event_name:<30} {new1:<20} {new2:<20} {diff_str:<15}")
    
    print("\n" + "="*70)
    print("ВЫВОД:")
    print("="*70)
    print("Подход 2 (все дивизионы) более корректен, так как:")
    print("- Новый танцор = тот, кто вообще вошел в систему WSDC в любом дивизионе")
    print("- Неважно, начал ли он с Masters, Sophisticated или Newcomer")
    print("- Это отражает реальное количество новых участников сообщества")

if __name__ == '__main__':
    main()

