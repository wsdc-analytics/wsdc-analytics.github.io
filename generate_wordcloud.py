#!/usr/bin/env python3
"""
Генерация облака слов из городов и регионов статьи geo_2025.html
Размер слова зависит от значимости (количество поинтов)
"""

import re
import sys
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    from wordcloud import WordCloud
    HAS_LIBS = True
except ImportError as e:
    HAS_LIBS = False
    print(f"⚠️  Предупреждение: некоторые библиотеки не установлены: {e}")
    print("\n📦 Для работы скрипта установите зависимости:")
    print("   pip install wordcloud pillow numpy")
    print("\n   Продолжаю с извлечением данных...")

def extract_data_from_html(html_file):
    """Извлекает города и регионы с их поинтами из HTML"""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    words_freq = {}
    
    # Находим все таблицы rank-table
    tables = re.findall(r'<table class="rank-table">(.*?)</table>', content, re.DOTALL)
    
    print(f"   Найдено таблиц: {len(tables)}")
    
    for table_idx, table in enumerate(tables):
        # Извлекаем все строки таблицы
        rows = re.findall(r'<tr>(.*?)</tr>', table, re.DOTALL)
        
        for row_idx, row in enumerate(rows):
            # Пропускаем заголовки
            if '<th>' in row:
                continue
            
            # Извлекаем название
            name = None
            
            # Вариант 1: название с флагом (города, регионы, страны)
            # Паттерн: <td class="event-cell"><span class="event-flag">🇸🇪</span> Stockholm</td>
            name_patterns = [
                r'<td class="event-cell">.*?<span class="event-flag">[^<]*</span>\s*([^<]+)</td>',  # С флагом: флаг + название
                r'<td class="event-cell">([^<]+?)(?:\s*\([A-Z]{2}\))?</td>',  # Без флага (штаты США)
            ]
            
            for pattern in name_patterns:
                name_match = re.search(pattern, row, re.DOTALL)
                if name_match:
                    name = name_match.group(1).strip()
                    break
            
            if not name:
                continue
            
            # Очищаем название
            name_clean = re.sub(r'🇦-🇿\s+', '', name).strip()  # Убираем эмодзи-флаги (если есть)
            name_clean = re.sub(r'\s+', ' ', name_clean).strip()
            
            # Извлекаем все метрики (Events, Points, Unique, New)
            metrics = re.findall(r'<td class="metric-cell"[^>]*>([0-9,]+)</td>', row)
            
            if len(metrics) >= 2:  # Должны быть хотя бы Events и Points
                try:
                    # Вторая метрика - это Points (первая - Events)
                    points_str = metrics[1].replace(',', '').strip()
                    points = int(points_str)
                    
                    if name_clean and points > 0:
                        # Для регионов убираем ", USA"
                        if ', USA' in name_clean:
                            name_clean = name_clean.replace(', USA', '').strip()
                        
                        # Добавляем только если еще нет или больше поинтов
                        if name_clean not in words_freq or words_freq[name_clean] < points:
                            words_freq[name_clean] = points
                except (ValueError, IndexError) as e:
                    continue
    
    return words_freq

def create_starfield_background(width=1920, height=1080, output_path='starfield_background.png'):
    """Создает фоновое изображение звездного неба"""
    if not HAS_LIBS:
        print("⚠️  Не могу создать фоновое изображение без библиотек")
        return None
    
    # Создаем темное изображение
    img = Image.new('RGB', (width, height), (10, 15, 30))  # Темно-синий фон
    pixels = img.load()
    
    import random
    random.seed(42)  # Для воспроизводимости
    
    # Добавляем звезды разной яркости
    num_stars = 5000
    for _ in range(num_stars):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        
        brightness = random.randint(150, 255)
        star_type = random.random()
        
        if star_type < 0.1:  # Яркие звезды (белые/желтые) - 10%
            r = brightness
            g = brightness - random.randint(0, 30)
            b = brightness - random.randint(0, 50)
        elif star_type < 0.2:  # Голубые звезды - 10%
            r = brightness - random.randint(0, 50)
            g = brightness - random.randint(0, 30)
            b = brightness
        else:  # Обычные звезды (белые) - 80%
            r = g = b = brightness
        
        pixels[x, y] = (r, g, b)
        
        # Добавляем свечение для очень ярких звезд
        if brightness > 220:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        old_pixel = pixels[nx, ny]
                        glow_intensity = brightness // 4
                        new_r = min(255, old_pixel[0] + glow_intensity)
                        new_g = min(255, old_pixel[1] + glow_intensity)
                        new_b = min(255, old_pixel[2] + glow_intensity)
                        pixels[nx, ny] = (new_r, new_g, new_b)
    
    img.save(output_path, 'PNG')
    print(f"✅ Фоновое изображение создано: {output_path}")
    return output_path

def create_wordcloud_with_background(word_frequencies, background_image_path, output_path):
    """Создает облако слов на фоне изображения"""
    if not HAS_LIBS:
        print("❌ Не могу создать облако слов без библиотек wordcloud, pillow, numpy")
        print("   Установите: pip install wordcloud pillow numpy")
        return
    
    # Загружаем или создаем фоновое изображение
    if os.path.exists(background_image_path):
        print(f"📖 Загрузка фонового изображения: {background_image_path}")
        background = Image.open(background_image_path)
        if background.mode != 'RGB':
            background = background.convert('RGB')
        bg_width, bg_height = background.size
    else:
        print(f"⚠️  Фоновое изображение не найдено: {background_image_path}")
        print(f"   Создаю фоновое изображение звездного неба...")
        created_path = create_starfield_background()
        if not created_path:
            return
        background = Image.open(created_path)
        bg_width, bg_height = background.size
    
    if not word_frequencies:
        print("❌ Ошибка: не найдено данных для облака слов")
        return
    
    print(f"\n🎨 Создание облака слов из {len(word_frequencies)} элементов...")
    
    # Функция для приглушенного голубого цвета
    def muted_blue_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return "#6B8FAE"  # Приглушенный голубой цвет
    
    # Используем Arial как строгий шрифт
    font_path = None
    possible_fonts = [
        '/System/Library/Fonts/Supplemental/Arial.ttf',
        '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        '/System/Library/Fonts/Supplemental/Helvetica.ttc'
    ]
    
    for font in possible_fonts:
        if os.path.exists(font):
            font_path = font
            print(f"   Используется шрифт: {font}")
            break
    
    # Создаем облако слов с прозрачным фоном
    # Настройки для расположения от центра без поворотов, менее плотное
    wordcloud = WordCloud(
        width=bg_width,
        height=bg_height,
        background_color=None,  # Прозрачный фон
        mode='RGBA',
        max_words=60,  # Ограничиваем для читаемости
        min_font_size=16,  # Уменьшено для менее плотного вида
        max_font_size=200,  # Уменьшено для менее плотного вида
        relative_scaling=0.5,  # Более плавное распределение размеров
        color_func=muted_blue_color_func,  # Приглушенный голубой цвет для всех слов
        prefer_horizontal=0.9,  # 90% горизонтально, почти без поворотов
        margin=25,  # Увеличено расстояние между словами для менее плотного расположения
        random_state=42,
        repeat=False,
        font_path=font_path  # Arial шрифт
    ).generate_from_frequencies(word_frequencies)
    
    # Конвертируем в изображение
    wordcloud_image = wordcloud.to_image()
    
    # Создаем финальное изображение
    final_image = Image.new('RGB', background.size)
    final_image.paste(background, (0, 0))
    
    # Накладываем облако слов с альфа-каналом
    if wordcloud_image.mode == 'RGBA':
        final_image.paste(wordcloud_image, (0, 0), wordcloud_image)
    else:
        wordcloud_rgb = wordcloud_image.convert('RGB')
        final_image = Image.blend(background, wordcloud_rgb, alpha=0.8)
    
    # Сохраняем результат
    final_image.save(output_path, 'PNG', dpi=(300, 300))
    print(f"✅ Облако слов сохранено: {output_path}")

# Основной код
if __name__ == "__main__":
    html_file = 'geo_2025.html'
    # Используем пользовательское фоновое изображение
    background_image = 'custom_background.png'
    output_file = 'wsdc_geo_wordcloud.png'
    
    if not os.path.exists(html_file):
        print(f"❌ Ошибка: файл {html_file} не найден")
        sys.exit(1)
    
    print("📖 Извлечение данных из статьи...")
    word_frequencies = extract_data_from_html(html_file)
    
    if not word_frequencies:
        print("❌ Ошибка: не удалось извлечь данные из статьи")
        sys.exit(1)
    
    print(f"\n📊 Найдено {len(word_frequencies)} городов и регионов:")
    sorted_words = sorted(word_frequencies.items(), key=lambda x: x[1], reverse=True)
    for word, freq in sorted_words[:40]:
        print(f"   {word}: {freq:,} поинтов")
    
    if HAS_LIBS:
        print(f"\n🎨 Создание облака слов...")
        print(f"   Фон: {background_image}")
        print(f"   Выходной файл: {output_file}")
        print(f"   Размер: {1920}x1080 (или по размеру фона)")
        
        create_wordcloud_with_background(word_frequencies, background_image, output_file)
        
        print(f"\n✅ Готово! Облако слов сохранено в {output_file}")
        print(f"   Для использования своего фона измените переменную background_image в скрипте")
    else:
        print(f"\n⚠️  Библиотеки не установлены.")
        print(f"   Установите: pip install wordcloud pillow numpy")
        print(f"   Затем запустите скрипт снова для генерации облака слов")
