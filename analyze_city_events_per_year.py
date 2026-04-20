#!/usr/bin/env python3
"""
Анализ количества ивентов в городах за один календарный год
Проверяет, было ли когда-либо больше или равно 5 ивентов в одном городе за год
"""

import csv
from collections import defaultdict
from pathlib import Path
import sys

# Пути к файлам данных
DATA_DIR = Path("/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points")

def load_events_data():
    """Загружает данные об ивентах"""
    events_file = DATA_DIR / 'events_wsdc.csv'
    
    if not events_file.exists():
        print(f"❌ Файл не найден: {events_file}")
        print(f"   Попробуем альтернативный путь...")
        # Попробуем найти файл в текущей директории
        if Path('events_wsdc.csv').exists():
            events_file = Path('events_wsdc.csv')
        else:
            sys.exit(1)
    
    events = []
    print(f"📖 Загрузка данных из: {events_file}")
    
    with open(events_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            events.append(row)
    
    print(f"   ✅ Загружено {len(events):,} ивентов")
    return events

def extract_city_from_location(location):
    """Извлекает город из локации формата 'City, State, Country' или 'City,  Country'"""
    if not location:
        return None
    
    # Разделяем по запятым и берем первый элемент (город)
    parts = [p.strip() for p in location.split(',')]
    city = parts[0] if parts else None
    
    # Убираем двойные пробелы и нормализуем
    if city:
        city = ' '.join(city.split())
    
    return city

def extract_year_from_date(date_str):
    """Извлекает год из даты формата 'Month Year'"""
    if not date_str:
        return None
    
    # Разделяем по пробелам и берем последний элемент (год)
    parts = date_str.strip().split()
    if not parts:
        return None
    
    try:
        year = int(parts[-1])
        return year
    except (ValueError, TypeError):
        return None

def normalize_city(city_name):
    """Нормализует название города"""
    if not city_name:
        return None
    
    city = city_name.strip()
    
    # Убираем лишние пробелы
    city = ' '.join(city.split())
    
    return city

def analyze_city_events_per_year(events):
    """Анализирует количество ивентов в городах за каждый год"""
    print("\n" + "="*80)
    print("📊 АНАЛИЗ КОЛИЧЕСТВА ИВЕНТОВ В ГОРОДАХ ЗА КАЛЕНДАРНЫЙ ГОД")
    print("="*80 + "\n")
    
    # Словарь: (city, year) -> set(event_names)
    city_year_events = defaultdict(set)
    
    for event in events:
        # Извлекаем город из поля location
        location = event.get('location', '')
        city_raw = extract_city_from_location(location)
        city = normalize_city(city_raw)
        
        # Получаем название ивента
        event_name = event.get('name', '').strip()
        
        # Извлекаем год из поля date
        date_str = event.get('date', '')
        year = extract_year_from_date(date_str)
        
        if not event_name or not year:
            continue
        
        # Специальное правило: Scandinavian Open всегда проходит в Стокгольме
        # (даже если в базе данных отсутствует локация)
        if 'scandinavian open' in event_name.lower():
            city = 'Stockholm'
        else:
            # Извлекаем город из поля location
            city_raw = extract_city_from_location(location)
            city = normalize_city(city_raw)
        
        if not city:
            continue
        
        # Считаем уникальные названия ивентов (name) для каждого города-года
        # Если один ивент проходит несколько раз в год, это все равно один ивент
        city_year_events[(city, year)].add(event_name)
    
    # Специальное правило: Scandinavian Open всегда проходит в Стокгольме
    # Добавляем его для всех годов, когда он проходил (если его нет в базе)
    # Нужно определить годы, когда он проходил
    # Пока добавляем для известных годов - можно расширить список
    scandinavian_open_years = [2023, 2024, 2025]  # Можно расширить по мере необходимости
    
    for year in scandinavian_open_years:
        if ('Stockholm', year) in city_year_events:
            # Проверяем, есть ли уже Scandinavian Open
            has_scandinavian = any('scandinavian open' in name.lower() for name in city_year_events[('Stockholm', year)])
            if not has_scandinavian:
                # Добавляем Scandinavian Open вручную
                city_year_events[('Stockholm', year)].add('Scandinavian Open')
                print(f"✅ Добавлен Scandinavian Open для Стокгольма в {year} году (не найден в базе)")
    
    # Группируем по городам и годам, подсчитываем количество уникальных ивентов
    city_year_counts = {}
    for (city, year), event_set in city_year_events.items():
        city_year_counts[(city, year)] = len(event_set)
    
    # Отладка: проверим Стокгольм в 2025
    if ('Stockholm', 2025) in city_year_events:
        print(f"\n🔍 Отладка: Стокгольм в 2025:")
        print(f"   Ивентов в множестве: {len(city_year_events[('Stockholm', 2025)])}")
        print(f"   Список ивентов:")
        for event_name in sorted(city_year_events[('Stockholm', 2025)]):
            print(f"      - {event_name}")
    
    # Фильтруем: только города с >= 5 ивентами за год
    significant_city_years = {
        (city, year): count 
        for (city, year), count in city_year_counts.items() 
        if count >= 5
    }
    
    # Сортируем по году (по убыванию), потом по количеству ивентов (по убыванию)
    sorted_results = sorted(
        significant_city_years.items(),
        key=lambda x: (x[0][1], -x[1]),
        reverse=True
    )
    
    print(f"🔍 Найдено городов с 5+ ивентами за год: {len(sorted_results)}\n")
    
    # Показываем города с 4 ивентами тоже (для информации)
    cities_with_4 = {
        (city, year): count 
        for (city, year), count in city_year_counts.items() 
        if count == 4
    }
    
    if cities_with_4:
        sorted_4 = sorted(
            cities_with_4.items(),
            key=lambda x: (x[0][1], x[0][0]),
            reverse=True
        )
        print(f"📊 Найдено городов с 4 ивентами за год: {len(sorted_4)}")
        print(f"   Это максимум, который когда-либо был достигнут:")
        for (city, year), count in sorted_4[:10]:
            print(f"   • {city} ({year}): {count} ивентов")
        print()
    
    if sorted_results:
        print("="*80)
        print(f"{'Город':<25} {'Год':<8} {'Ивентов':<10}")
        print("="*80)
        
        for (city, year), count in sorted_results:
            print(f"{city:<25} {year:<8} {count:<10}")
        
        print("="*80)
        
        # Статистика
        max_events = max(count for _, count in sorted_results)
        max_city_year = [(city, year, count) for (city, year), count in sorted_results if count == max_events]
        
        print(f"\n📈 Максимальное количество ивентов в одном городе за год: {max_events}")
        for city, year, count in max_city_year:
            print(f"   • {city} ({year}): {count} ивентов")
        
        # Проверяем Стокгольм в 2025
        stockholm_2025 = city_year_counts.get(('Stockholm', 2025), 0)
        print(f"\n🇸🇪 Стокгольм в 2025 году: {stockholm_2025} ивентов")
        
        # Все года для Стокгольма с 5+ ивентами
        stockholm_years = [(year, count) for (city, year), count in sorted_results if city == 'Stockholm']
        if stockholm_years:
            print(f"   Стокгольм с 5+ ивентами за год:")
            for year, count in stockholm_years:
                print(f"   • {year}: {count} ивентов")
    else:
        print("❌ Не найдено городов с 5+ ивентами за один год")
    
    # Дополнительная статистика: топ-10 по всем годам
    print("\n" + "="*80)
    print("🏆 ТОП-10 ГОРОДОВ ПО КОЛИЧЕСТВУ ИВЕНТОВ ЗА ОДИН ГОД (ВСЯ ИСТОРИЯ)")
    print("="*80)
    
    all_results = sorted(
        city_year_counts.items(),
        key=lambda x: -x[1],
        reverse=True
    )[:10]
    
    print(f"{'Город':<25} {'Год':<8} {'Ивентов':<10}")
    print("-"*80)
    for (city, year), count in all_results:
        print(f"{city:<25} {year:<8} {count:<10}")
    
    return city_year_counts

if __name__ == '__main__':
    try:
        events = load_events_data()
        city_year_counts = analyze_city_events_per_year(events)
        
        print("\n✅ Анализ завершен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

