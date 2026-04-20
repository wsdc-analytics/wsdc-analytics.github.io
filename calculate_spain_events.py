#!/usr/bin/env python3
"""
Подсчет метрик для испанских событий 2025 года
"""

import csv
from collections import defaultdict

# ID событий из events_wsdc.csv
EVENT_IDS = {
    'Arousa Westie Fest': 344,
    'BeeMAD': 347,
    'Mediterranean Open WCS': 375
}

# Skill level дивизионы (для подсчета новых танцоров учитываем только их)
SKILL_LEVEL_DIVISIONS = {
    'Newcomer', 'Novice', 'Intermediate', 'Advanced', 
    'All-Stars', 'All-Star', 'All Stars', 'Champions'
}

def load_results():
    """Загружает данные о результатах"""
    results_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
    
    events_data = defaultdict(lambda: {
        'total_points': 0,
        'dancers': set(),
        'new_dancers': set()
    })
    
    # Словарь для отслеживания первого года каждого танцора (за все время, не только 2025)
    dancer_first_year = {}
    
    try:
        with open(results_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Сначала проходим по ВСЕМ данным за все годы, чтобы найти первый год каждого танцора
            print("📊 Загрузка данных...")
            all_rows = list(reader)
            print(f"   Загружено строк: {len(all_rows)}")
            if all_rows:
                print(f"   Столбцы: {list(all_rows[0].keys())[:10]}...")
            
            # Находим первый год получения пунктов для каждого танцора
            # ВАЖНО: для определения "нового танцора" учитываем ВСЕ дивизионы (включая Masters, Sophisticated и т.д.)
            # потому что новый танцор = тот, кто вообще вошел в систему WSDC в любом дивизионе
            for row in all_rows:
                dancer_id = row.get('dancer_id', '')
                year = row.get('event_year', '')
                points_str = row.get('event_points', '0')
                
                # Учитываем ВСЕ дивизионы для определения первого года (новый танцор = вошел в систему)
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    if points > 0:  # Только если получил пункты (в любом дивизионе)
                        year_int = int(year) if year else 9999
                        if dancer_id and year_int < 9999:
                            if dancer_id not in dancer_first_year or year_int < dancer_first_year[dancer_id]:
                                dancer_first_year[dancer_id] = year_int
                except:
                    pass
            
            print(f"   Найдено уникальных танцоров с пунктами (все дивизионы): {len(dancer_first_year)}")
            
            # Словарь для отслеживания первого события каждого танцора (где получил первые пункты)
            dancer_first_event = {}  # dancer_id -> (year, month, event_id)
            
            # Находим первое событие для каждого танцора (где получил первые пункты)
            # Учитываем ВСЕ дивизионы (не только skill level), так как новый танцор может войти через любой дивизион
            # Учитываем месяц, чтобы если танцор получил пункты на нескольких событиях в первый год,
            # выбрать самое первое по дате
            for row in all_rows:
                dancer_id = row.get('dancer_id', '')
                year = row.get('event_year', '')
                month = row.get('event_month', '')
                event_id = row.get('event_name_id', '')
                points_str = row.get('event_points', '0')
                
                # Учитываем ВСЕ дивизионы для определения первого события
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    if points > 0 and dancer_id in dancer_first_year:
                        year_int = int(year) if year else 9999
                        month_int = int(month) if month and month != '' else 13  # 13 = декабрь+1 для сортировки
                        
                        # Если это первый год танцора, запоминаем событие (самое первое по дате)
                        if year_int == dancer_first_year[dancer_id]:
                            if dancer_id not in dancer_first_event:
                                dancer_first_event[dancer_id] = (year_int, month_int, event_id)
                            else:
                                # Если уже есть событие, выбираем то, которое раньше по месяцу
                                existing_year, existing_month, existing_event = dancer_first_event[dancer_id]
                                if month_int < existing_month or (month_int == existing_month and str(event_id) < str(existing_event)):
                                    dancer_first_event[dancer_id] = (year_int, month_int, event_id)
                except Exception as e:
                    pass
            
            print(f"   Найдено танцоров с первым событием: {len(dancer_first_event)}")
            
            # Отладка: сколько танцоров получили первые пункты в 2025
            dancers_2025_first = [d for d, y in dancer_first_year.items() if y == 2025]
            print(f"   Танцоров с первым годом 2025: {len(dancers_2025_first)}")
            
            # Теперь обрабатываем события 2025 года
            spain_events_found = defaultdict(int)
            for row in all_rows:
                event_name = row.get('event_name', '')
                event_id = row.get('event_name_id', '')
                year = row.get('event_year', '')
                dancer_id = row.get('dancer_id', '')
                points_str = row.get('event_points', '0')
                
                # Ищем события по названию (частичное совпадение)
                matched_event = None
                matched_event_id = None
                for search_name, search_id in EVENT_IDS.items():
                    if search_name.lower() in event_name.lower() or str(search_id) == str(event_id):
                        matched_event = search_name
                        matched_event_id = str(search_id)
                        break
                
                # Собираем статистику по испанским событиям 2025
                if year == '2025' and matched_event:
                    spain_events_found[event_name] += 1
                
                # Проверяем, что это событие 2025 года и одно из наших событий
                if year == '2025' and matched_event:
                    competition = row.get('event_competition', '')
                    try:
                        points = int(float(points_str)) if points_str and points_str != '' else 0
                        
                        # Для подсчета пунктов учитываем только skill level дивизионы
                        if competition in SKILL_LEVEL_DIVISIONS:
                            events_data[matched_event]['total_points'] += points
                            events_data[matched_event]['dancers'].add(dancer_id)
                            
                            # Новый танцор = тот, кто получил свои первые пункты именно на ЭТОМ событии
                            # Проверяем: первый год = 2025 И первое событие = это событие
                            if (dancer_id in dancer_first_year and dancer_first_year[dancer_id] == 2025 and
                                dancer_id in dancer_first_event):
                                first_year, first_month, first_event_id = dancer_first_event[dancer_id]
                                # Сравниваем event_id как строки, так как в CSV они могут быть строками
                                if str(first_event_id) == str(event_id) and points > 0:
                                    events_data[matched_event]['new_dancers'].add(dancer_id)
                    except Exception as e:
                        pass  # Игнорируем ошибки парсинга
            
            print(f"   Испанские события 2025 найдено: {dict(spain_events_found)}")
    
    except FileNotFoundError:
        print(f"❌ Файл не найден: {results_file}")
        return None
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None
    
    return events_data

def main():
    events_data = load_results()
    
    if not events_data:
        return
    
    print("\n" + "="*60)
    print("🇪🇸 МЕТРИКИ ИСПАНСКИХ СОБЫТИЙ 2025")
    print("="*60 + "\n")
    
    for event_name in ['Arousa Westie Fest', 'BeeMAD', 'Mediterranean Open WCS']:
        if event_name in events_data:
            data = events_data[event_name]
            print(f"📅 {event_name}")
            print(f"   Пункты (Points): {data['total_points']}")
            print(f"   Новые танцоры (New): {len(data['new_dancers'])}")
            print(f"   Всего уникальных танцоров: {len(data['dancers'])}")
            print()

if __name__ == '__main__':
    main()

