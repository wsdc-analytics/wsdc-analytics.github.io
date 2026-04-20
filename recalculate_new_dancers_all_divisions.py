#!/usr/bin/env python3
"""
Пересчет новых танцоров с новой логикой (все дивизионы, не только skill level)
Сравнение со старыми данными из статей
"""

import csv
from collections import defaultdict

# События из таблиц статей (глобальный топ новых танцоров)
GLOBAL_EVENTS_FROM_ARTICLE = {
    'Asia WCS Open': 32,
    'West In Lyon': 27,
    'St.Petersburg WCS Nights': 27,
    'King Swing': 27,
    'MY Swing': 27,
    'Midnight Madness WCS': 25,
    'SwingCouver': 25,
    'Swing & Snow': 25,
    'Swing Over': 24,
    'BudaFest': 24,
}

# Европейские события из статьи (европейский топ новых танцоров)
# Значения из текущих статей - европейский топ новых танцоров
EUROPEAN_EVENTS_FROM_ARTICLE = {
    'West In Lyon': 27,
    'St.Petersburg WCS Nights': 27,
    'Swing & Snow': 25,
    'BudaFest': 24,
    'BudaFest Open WCS Championships': 24,  # может быть полное название
    'Mediterranean Open WCS': 24,
    'D-Townswing': 24,
    'Swingside Invitational': 23,
    'Rock The Barn': 22,
    'Warsaw Summer Nights Westival': 22,  # из статьи видно 22, не 21
    'German Open': 23,  # не в топ-10 европейских по новым
    'Polish Open': 21,
    'Swingtzerland': 19,
    'Paris Westie Fest': 18,
    'SwingVester': 21,  # место 10 в европейском топе
}

results_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv'
events_file = '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/events_wsdc.csv'

def load_event_ids():
    """Загружает ID событий из events_wsdc.csv"""
    event_name_to_id = {}
    event_id_to_name = {}
    
    try:
        with open(events_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                event_name = row.get('Event', '').strip()
                event_id = row.get('Event ID', '').strip()
                year_month = row.get('Year and Month', '').strip()
                
                if event_name and event_id and '2025' in year_month:
                    event_name_to_id[event_name] = event_id
                    event_id_to_name[event_id] = event_name
    except Exception as e:
        print(f"Ошибка загрузки events_wsdc.csv: {e}")
    
    return event_name_to_id, event_id_to_name

def calculate_new_dancers_all_divisions():
    """Пересчет новых танцоров с учетом всех дивизионов"""
    
    event_name_to_id, event_id_to_name = load_event_ids()
    
    # Словарь для первого года каждого танцора (ВСЕ дивизионы)
    dancer_first_year = {}
    dancer_first_event = {}  # dancer_id -> (year, month, event_id)
    
    # Словарь для подсчета новых танцоров по событиям 2025
    events_new_dancers = defaultdict(set)
    events_all_data = defaultdict(lambda: {'dancers': set(), 'points': 0})
    
    print("📊 Загрузка данных...")
    
    with open(results_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        all_rows = list(reader)
        print(f"   Загружено строк: {len(all_rows)}")
        
        # Первый проход: находим первый год для каждого танцора (ВСЕ дивизионы)
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
        
        print(f"   Найдено уникальных танцоров: {len(dancer_first_year)}")
        print(f"   Танцоров с первым годом 2025: {sum(1 for y in dancer_first_year.values() if y == 2025)}")
        
        # Второй проход: находим первое событие каждого танцора
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
        
        print(f"   Найдено танцоров с первым событием: {len(dancer_first_event)}")
        
        # Третий проход: подсчитываем новых танцоров по событиям 2025
        for row in all_rows:
            event_name = row.get('event_name', '').strip()
            event_id = row.get('event_name_id', '')
            year = row.get('event_year', '')
            dancer_id = row.get('dancer_id', '')
            points_str = row.get('event_points', '0')
            
            if year == '2025':
                try:
                    points = int(float(points_str)) if points_str and points_str != '' else 0
                    
                    # Проверяем, является ли этот танцор новым и получил ли он первые пункты на этом событии
                    if (dancer_id in dancer_first_year and dancer_first_year[dancer_id] == 2025 and
                        dancer_id in dancer_first_event and points > 0):
                        first_year, first_month, first_event_id = dancer_first_event[dancer_id]
                        if str(first_event_id) == str(event_id):
                            events_new_dancers[event_name].add(dancer_id)
                    
                    # Также собираем общую статистику
                    if points > 0:
                        events_all_data[event_name]['dancers'].add(dancer_id)
                        events_all_data[event_name]['points'] += points
                except:
                    pass
    
    return events_new_dancers, events_all_data, event_name_to_id

def get_european_countries():
    """Возвращает список европейских стран"""
    return [
        'Russia', 'France', 'Germany', 'United Kingdom', 'Poland', 'Italy', 'Spain',
        'Netherlands', 'Sweden', 'Austria', 'Switzerland', 'Belgium', 'Norway',
        'Denmark', 'Finland', 'Hungary', 'Czech Republic', 'Romania', 'Portugal',
        'Greece', 'Ireland', 'Ukraine', 'Slovakia', 'Bulgaria', 'Croatia', 'Serbia',
        'Slovenia', 'Estonia', 'Latvia', 'Lithuania'
    ]

def is_european_event(event_name, events_file_path, event_name_to_id):
    """Проверяет, является ли событие европейским"""
    # Список известных европейских событий
    known_european_events = {
        'West In Lyon', 'St.Petersburg WCS Nights', 'Swing & Snow', 'BudaFest',
        'BudaFest Open WCS Championships', 'German Open', 'King Swing', 
        'Mediterranean Open WCS', 'BeeMAD', 'Arousa Westie Fest',
        'D-Townswing', 'Polish Open', 'Swingtzerland', 'Paris Westie Fest',
        'Paris Swing Classic', 'Swing Resolution', 'Dutch open West Coast swing',
        'Scottish Swing Classic', 'Swingside Invitational'
    }
    
    # Проверяем точное совпадение или частичное
    for known_event in known_european_events:
        if known_event.lower() in event_name.lower() or event_name.lower() in known_event.lower():
            return True
    
    # Проверяем по локации в events_wsdc.csv
    try:
        with open(events_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_event_name = row.get('Event', '').strip()
                if row_event_name == event_name and '2025' in row.get('Year and Month', ''):
                    location = row.get('Location', '').strip()
                    european_keywords = ['russia', 'france', 'germany', 'spain', 'italy', 'uk', 
                                       'poland', 'sweden', 'norway', 'netherlands', 'belgium',
                                       'switzerland', 'austria', 'hungary', 'portugal', 'greece',
                                       'ireland', 'ukraine', 'czech', 'romania', 'denmark', 'finland',
                                       'slovenia', 'croatia', 'serbia', 'estonia', 'latvia', 'lithuania',
                                       'scotland', 'england', 'scotland', 'madrid', 'lyon', 'st. petersburg',
                                       'petersburg', 'moscow', 'budapest', 'paris', 'barcelona']
                    if any(keyword.lower() in location.lower() for keyword in european_keywords):
                        return True
    except Exception as e:
        pass
    return False

def main():
    events_new_dancers, events_all_data, event_name_to_id = calculate_new_dancers_all_divisions()
    
    # Преобразуем в список для сортировки
    events_list = [(event_name, len(new_dancers)) for event_name, new_dancers in events_new_dancers.items()]
    events_list.sort(key=lambda x: x[1], reverse=True)
    
    # Старые ранги из статьи (глобальный топ)
    old_global_ranks = {
        'Asia WCS Open': 1,
        'West In Lyon': 2,
        'St.Petersburg WCS Nights': 3,
        'King Swing': 4,
        'MY Swing': 5,
        'Midnight Madness WCS': 6,
        'SwingCouver': 7,
        'Swing & Snow': 8,
        'Swing Over': 9,
        'BudaFest': 10,
    }
    
    print("\n" + "="*80)
    print("📊 ГЛОБАЛЬНЫЙ ТОП-10 НОВЫХ ТАНЦОРОВ (все дивизионы)")
    print("="*80)
    print(f"\n{'Новый':<6} {'Старый':<6} {'Событие':<40} {'Новые (новый)':<15} {'Новые (старый)':<15} {'Изменение ранга':<15}")
    print("-"*95)
    
    # Топ-10 глобальных
    for i, (event_name, new_count) in enumerate(events_list[:10], 1):
        old_rank = old_global_ranks.get(event_name, '—')
        old_count = GLOBAL_EVENTS_FROM_ARTICLE.get(event_name, '—')
        
        rank_change = ''
        if old_rank != '—':
            rank_diff = old_rank - i
            if rank_diff > 0:
                rank_change = f"↑+{rank_diff}"
            elif rank_diff < 0:
                rank_change = f"↓{rank_diff}"
            else:
                rank_change = "—"
        
        old_rank_str = str(old_rank) if old_rank != '—' else '—'
        print(f"{i:<6} {old_rank_str:<6} {event_name:<40} {new_count:<15} {old_count:<15} {rank_change:<15}")
    
    # Старые ранги из статьи (европейский топ)
    old_european_ranks = {
        'West In Lyon': 1,
        'St.Petersburg WCS Nights': 2,
        'Swing & Snow': 3,
        'BudaFest': 4,
        'Mediterranean Open WCS': 5,
        'D-Townswing': 6,
        'Swingside Invitational': 7,
        'Rock The Barn': 8,
        'Warsaw Summer Nights Westival': 9,
        'SwingVester': 10,
    }
    
    # Европейские события
    print("\n" + "="*80)
    print("📊 ЕВРОПЕЙСКИЙ ТОП-10 НОВЫХ ТАНЦОРОВ (все дивизионы)")
    print("="*80)
    print(f"\n{'Новый':<6} {'Старый':<6} {'Событие':<40} {'Новые (новый)':<15} {'Новые (старый)':<15} {'Изменение ранга':<15}")
    print("-"*95)
    
    # Фильтруем европейские события
    european_events = []
    for event_name, new_count in events_list:
        if is_european_event(event_name, events_file, event_name_to_id):
            european_events.append((event_name, new_count))
    
    for i, (event_name, new_count) in enumerate(european_events[:10], 1):
        # Определяем старый ранг
        old_rank = None
        for old_name, old_r in old_european_ranks.items():
            if old_name.lower() in event_name.lower() or event_name.lower() in old_name.lower():
                old_rank = old_r
                break
        
        # Пытаемся найти старое значение (проверяем разные варианты названий)
        old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get(event_name, '—')
        if old_count == '—':
            # Проверяем альтернативные названия
            if 'BudaFest' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('BudaFest', '—')
            elif 'Mediterranean' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('Mediterranean Open WCS', '—')
            elif 'D-Town' in event_name or 'D-Townswing' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('D-Townswing', '—')
            elif 'German Open' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('German Open', '—')
            elif 'Polish' in event_name or 'Warsaw' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('Warsaw Summer Nights Westival', 
                                                             EUROPEAN_EVENTS_FROM_ARTICLE.get('Polish Open', '—'))
            elif 'Swingside' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('Swingside Invitational', '—')
            elif 'Rock The Barn' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('Rock The Barn', '—')
            elif 'Paris' in event_name:
                old_count = EUROPEAN_EVENTS_FROM_ARTICLE.get('Paris Westie Fest', '—')
        
        rank_change = ''
        if old_rank is not None:
            rank_diff = old_rank - i
            if rank_diff > 0:
                rank_change = f"↑+{rank_diff}"
            elif rank_diff < 0:
                rank_change = f"↓{rank_diff}"
            else:
                rank_change = "—"
        
        old_rank_str = str(old_rank) if old_rank is not None else '—'
        print(f"{i:<6} {old_rank_str:<6} {event_name:<40} {new_count:<15} {old_count:<15} {rank_change:<15}")
    
    print("\n" + "="*80)
    print("📝 ПРИМЕЧАНИЕ:")
    print("="*80)
    print("'Новые (новый)' - пересчет с учетом ВСЕХ дивизионов (включая Masters, Sophisticated и т.д.)")
    print("'Новые (старый)' - данные из текущих статей (только skill level дивизионы)")
    print("'Разница' - показывает изменение при переходе на новую логику")

if __name__ == '__main__':
    main()

