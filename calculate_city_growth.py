#!/usr/bin/env python3
"""
Расчет прироста поинтов для городов Kraków и Freiburg (2024 vs 2025)
"""

import csv
import os
from collections import defaultdict
from datetime import datetime

# Skill Level divisions only
SKILL_LEVEL_DIVISIONS = ['Newcomer', 'Novice', 'Intermediate', 'Advanced', 'All-Stars', 'Champions', 'All-Star']

# Возможные пути к данным
data_paths = [
    '/Users/ania/.cursor/projects/tableau/My-Tableau-Projects/WSDC/WSDC Points/dancers_results_info.csv',
    'dancers_results_info.csv',
    '../dancers_results_info.csv',
]

def find_data_file():
    """Ищет файл с данными"""
    for path in data_paths:
        if os.path.exists(path):
            return path
    return None

def calculate_city_growth(city_name_2025, city_points_2025, city_rank_2025, city_rank_2024):
    """
    Рассчитывает прирост на основе данных из CSV
    """
    data_file = find_data_file()
    
    if not data_file:
        print(f"⚠️  Файл с данными не найден. Пробовал пути: {data_paths}")
        print("\n💡 Используем оценку на основе рангов\n")
        
        # Оценка на основе рангов
        rank_change = city_rank_2024 - city_rank_2025  # положительное = подъем
        
        if rank_change >= 10:
            estimated_growth_pct = 80 + (rank_change - 10) * 5
        elif rank_change >= 5:
            estimated_growth_pct = 40 + (rank_change - 5) * 8
        elif rank_change >= 3:
            estimated_growth_pct = 20 + (rank_change - 3) * 10
        else:
            estimated_growth_pct = rank_change * 7
        
        estimated_points_2024 = city_points_2025 / (1 + estimated_growth_pct / 100)
        
        print(f"📊 {city_name_2025}:")
        print(f"   Ранг 2024: {city_rank_2024} → Ранг 2025: {city_rank_2025} (↑+{rank_change})")
        print(f"   Поинты 2025: {city_points_2025:,}")
        print(f"   Оценка поинтов 2024: ~{estimated_points_2024:.0f}")
        print(f"   Оценка прироста: ~{estimated_growth_pct:.0f}%")
        print()
        
        return estimated_growth_pct
    
    # Используем реальные данные
    try:
        print(f"📖 Чтение данных из {data_file}...\n")
        
        city_variants = {
            'Kraków': ['Kraków', 'Krakow', 'Cracow'],
            'Freiburg': ['Freiburg']
        }
        
        if city_name_2025 not in city_variants:
            print(f"⚠️  Неизвестный город: {city_name_2025}")
            return None
        
        variants = city_variants[city_name_2025]
        
        # Подсчитываем поинты по годам
        points_by_year = defaultdict(float)
        
        with open(data_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    year = int(row['year'])
                    if year not in [2024, 2025]:
                        continue
                    
                    division = row.get('division', '')
                    if division not in SKILL_LEVEL_DIVISIONS:
                        continue
                    
                    location = row.get('event_location', '')
                    city = row.get('event_city', '')
                    
                    # Проверяем город
                    city_match = False
                    for variant in variants:
                        if variant.lower() in location.lower() or variant.lower() in city.lower():
                            city_match = True
                            break
                    
                    if not city_match:
                        continue
                    
                    points = float(row.get('points', 0))
                    points_by_year[year] += points
                    
                except (ValueError, KeyError) as e:
                    continue
        
        points_2024 = points_by_year.get(2024, 0)
        points_2025 = points_by_year.get(2025, city_points_2025)
        
        if points_2024 == 0:
            print(f"⚠️  Для {city_name_2025} не найдено данных за 2024 год")
            print("   Используем оценку на основе рангов\n")
            
            rank_change = city_rank_2024 - city_rank_2025
            if rank_change >= 10:
                estimated_growth_pct = 80 + (rank_change - 10) * 5
            elif rank_change >= 5:
                estimated_growth_pct = 40 + (rank_change - 5) * 8
            elif rank_change >= 3:
                estimated_growth_pct = 20 + (rank_change - 3) * 10
            else:
                estimated_growth_pct = rank_change * 7
            
            print(f"📊 {city_name_2025} (оценка):")
            print(f"   Ранг 2024: {city_rank_2024} → Ранг 2025: {city_rank_2025} (↑+{rank_change})")
            print(f"   Поинты 2025: {points_2025:,}")
            print(f"   Оценка прироста: ~{estimated_growth_pct:.0f}%")
            print()
            return estimated_growth_pct
        
        growth_pct = ((points_2025 - points_2024) / points_2024) * 100
        
        print(f"📊 {city_name_2025}:")
        print(f"   Поинты 2024: {points_2024:,.0f}")
        print(f"   Поинты 2025: {points_2025:,.0f}")
        print(f"   Прирост: {growth_pct:+.1f}%")
        print()
        
        return growth_pct
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return None

# Основной расчет
print("🔍 Расчет приростов для Kraków и Freiburg\n")
print("=" * 60)

krakow_growth = calculate_city_growth('Kraków', 1025, 8, 21)
freiburg_growth = calculate_city_growth('Freiburg', 1088, 7, 18)

print("=" * 60)
print("\n✅ Расчет завершен!\n")

if krakow_growth:
    print(f"📝 Kraków: прирост ~{krakow_growth:.0f}%")
if freiburg_growth:
    print(f"📝 Freiburg: прирост ~{freiburg_growth:.0f}%")

