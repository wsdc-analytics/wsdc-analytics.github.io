#!/usr/bin/env python3
"""
Создает "стену" из логотипов - плотное размещение без пробелов.
Логотипы касаются друг друга, образуя единое полотно.
"""

import os
import random
from PIL import Image, ImageEnhance
import math

# Путь к папке с логотипами
LOGOS_DIR = "/Users/ania/Desktop/Ранкинг пост/Events/Events Logos"

# Маппинг реальных имен файлов к названиям ивентов
FILE_TO_EVENT_MAPPING = {
    "Asia Open": "Asia WCS Open",
    "Atlanta Swing": "Atlanta Swing Classic",
    "Bavarian Open": "Bavarian Open",
    "Boogie By The Bay": "Boogie By The Bay",
    "BudaFest": "BudaFest",
    "D-Town": "D-Townswing",
    "Easter Swing": "Easter Swing",
    "Finnfest": "Finnfest",
    "German Open": "German Open",
    "J&J O'Rama": "J&J O'Rama",
    "King Swing": "King Swing",
    "Liberty Swing": "Liberty Swing Dance Championships",
    "Mediterrianean Open WCS": "Mediterranean Open WCS",
    "Midnight Madness": "Midnight Madness WCS",
    "Milan Modern Swing": "Milan Modern Swing",
    "My Swing": "MY Swing",
    "Paris Westie Fest": "Paris Westie Fest",
    "Rock The Barn": "Rock The Barn",
    "Spb WCS Nigths": "St.Petersburg WCS Nights",
    "Swing&Snow": "Swing & Snow",
    "SwingCouver": "SwingCouver",
    "SwingOver": "Swing Over",
    "SwingSide": "Swingside Invitational",
    "SwingVester": "SwingVester",
    "Swingtacular": "Swingtacular",
    "UK WCS": "UK WCS Championships",
    "Warsaw Helloween Swing": "Warsaw Halloween Swing",
    "Warsaw Summer Nights": "Warsaw Summer Nights Westival",
    "West in leon": "West In Lyon",
    "WWW3": "Wild Wild Westie",
}

def find_logo_files(logos_dir):
    """Находит все логотипы в папке"""
    logo_files = []
    extensions = ['.png', '.jpg', '.jpeg', '.PNG', '.JPG', '.JPEG']
    
    if not os.path.exists(logos_dir):
        print(f"❌ Папка {logos_dir} не найдена!")
        return []
    
    for filename in os.listdir(logos_dir):
        ext = None
        for e in extensions:
            if filename.endswith(e):
                ext = e
                break
        
        if not ext:
            continue
        
        file_base = filename[:-len(ext)]
        if file_base in FILE_TO_EVENT_MAPPING:
            file_path = os.path.join(logos_dir, filename)
            logo_files.append(file_path)
    
    return logo_files

def load_logo(file_path, target_size, opacity=0.85, brightness_boost=1.35):
    """Загружает логотип"""
    try:
        img = Image.open(file_path)
        
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Усиливаем яркость
        if img.mode == 'RGBA':
            rgb = img.convert('RGB')
            rgb_enhanced = ImageEnhance.Brightness(rgb).enhance(brightness_boost)
            rgb_enhanced = ImageEnhance.Contrast(rgb_enhanced).enhance(1.1)
            alpha = img.split()[3]
            img = rgb_enhanced.convert('RGBA')
            img.putalpha(alpha)
        
        # Применяем прозрачность
        alpha = img.split()[3]
        alpha_new = Image.new('L', alpha.size)
        pixels = alpha.load()
        pixels_new = alpha_new.load()
        for i in range(alpha.size[0]):
            for j in range(alpha.size[1]):
                pixels_new[i, j] = int(pixels[i, j] * opacity)
        img.putalpha(alpha_new)
        
        return img
    except Exception as e:
        print(f"⚠️  Ошибка загрузки {file_path}: {e}")
        return None

def check_overlap(box1, box2, margin=5):
    """Проверяет перекрытие двух прямоугольников с небольшим отступом"""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    # Добавляем margin для минимального расстояния
    return not (x1 + w1 + margin < x2 or x2 + w2 + margin < x1 or
                y1 + h1 + margin < y2 or y2 + h2 + margin < y1)

def create_wall_texture(output_file="events_background.png",
                       width=2000, height=700,
                       bg_color=(45, 55, 72),
                       opacity=0.85):
    """
    Создает плотную "стену" из логотипов без пробелов
    """
    
    logo_files = find_logo_files(LOGOS_DIR)
    
    if not logo_files:
        print(f"❌ Не найдено ни одного логотипа!")
        return False
    
    print(f"✅ Найдено {len(logo_files)} логотипов")
    
    # Создаем фон
    background = Image.new('RGBA', (width, height), (*bg_color, 255))
    
    # Вычисляем оптимальный размер для 30 логотипов
    # Площадь: 2000 * 700 = 1,400,000 пикселей
    # На каждый: ~46,667 пикселей, средний размер ~216px
    # Используем диапазон 210-270px для гарантии размещения всех
    size_options = [230, 250, 240, 260, 220, 270, 210, 255, 245, 235, 265]
    
    # Загружаем каждый логотип один раз
    logos_with_size = []
    random.seed(42)
    
    for file_path in logo_files:
        size = random.choice(size_options)
        logo = load_logo(file_path, (size, size), opacity)
        if logo:
            logos_with_size.append(logo)
    
    print(f"✅ Подготовлено {len(logos_with_size)} логотипов")
    print(f"🎨 Размещаем все {len(logos_with_size)} логотипов равномерно...")
    
    # Создаем базовую сетку для равномерного распределения
    num_logos = len(logos_with_size)
    cols = int(math.ceil(math.sqrt(num_logos * (width / height))))
    rows = int(math.ceil(num_logos / cols))
    cell_w = width / cols
    cell_h = height / rows
    
    # Список размещенных (x, y, width, height)
    placed_boxes = []
    placed_count = 0
    
    # Создаем список позиций сетки, но притягиваем их к центру
    grid_positions = []
    center_x = width / 2
    center_y = height / 2
    
    for i in range(num_logos):
        row = i // cols
        col = i % cols
        # Исходная позиция в сетке
        original_x = col * cell_w + cell_w / 2
        original_y = row * cell_h + cell_h / 2
        
        # Притягиваем к центру (умеренное притяжение)
        dist_from_center = math.sqrt((original_x - center_x)**2 + (original_y - center_y)**2)
        max_dist = math.sqrt((width/2)**2 + (height/2)**2)
        pull_factor = 0.2 * (dist_from_center / max_dist)  # До 20% притяжения к центру (уменьшено)
        
        # Смещаем позицию к центру
        base_x = original_x - (original_x - center_x) * pull_factor
        base_y = original_y - (original_y - center_y) * pull_factor
        
        grid_positions.append((base_x, base_y, row, col, dist_from_center))
    
    # Сортируем: сначала размещаем центральные ячейки
    grid_positions.sort(key=lambda pos: pos[4])
    
    # Размещаем логотипы
    for idx, logo in enumerate(logos_with_size):
        logo_w, logo_h = logo.size
        
        # Базовая позиция из сетки (приоритет центральным ячейкам)
        base_x, base_y, row, col, dist_from_center = grid_positions[idx]
        
        placed = False
        max_attempts = 600  # Еще больше попыток
        
        # Пробуем разместить вокруг базовой позиции
        for attempt in range(max_attempts):
            if attempt == 0:
                # Первая попытка - прямо в центре ячейки
                x = int(base_x - logo_w // 2)
                y = int(base_y - logo_h // 2)
            else:
                # Смещения: меньше для центра, но не слишком ограничиваем края
                max_dist = math.sqrt((width/2)**2 + (height/2)**2)
                center_factor = 1.0 - (dist_from_center / max_dist) * 0.5  # Умеренное ограничение (0.5-1.0)
                
                offset_range_x = cell_w * 0.3 * center_factor  # Центр: ~0.15, края: ~0.3
                offset_range_y = cell_h * 0.3 * center_factor
                offset_x = random.uniform(-offset_range_x, offset_range_x)
                offset_y = random.uniform(-offset_range_y, offset_range_y)
                x = int(base_x + offset_x - logo_w // 2)
                y = int(base_y + offset_y - logo_h // 2)
            
            # Ограничиваем границами
            x = max(0, min(x, width - logo_w))
            y = max(0, min(y, height - logo_h))
            
            # Случайный поворот
            angle = random.choice([0, 0, 0, 5, -5, 10, -10, 8, -8, 12, -12, 15, -15, 20, -20])
            
            if angle != 0:
                logo_rotated = logo.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
                logo_w_rot, logo_h_rot = logo_rotated.size
                paste_x = x
                paste_y = y
                box = (paste_x, paste_y, logo_w_rot, logo_h_rot)
                logo_to_place = logo_rotated
            else:
                paste_x = x
                paste_y = y
                box = (paste_x, paste_y, logo_w, logo_h)
                logo_to_place = logo
            
            # Проверяем перекрытие (разрешаем касание)
            overlaps = False
            for placed_box in placed_boxes:
                if check_overlap(box, placed_box, margin=0):  # 0 = касание разрешено
                    overlaps = True
                    break
            
            if not overlaps:
                try:
                    temp = Image.new('RGBA', background.size, (0, 0, 0, 0))
                    temp.paste(logo_to_place, (paste_x, paste_y), logo_to_place)
                    background = Image.alpha_composite(background, temp)
                    placed_boxes.append(box)
                    placed_count += 1
                    placed = True
                    break
                except:
                    pass
        
        # Если не удалось, пробуем с небольшим перекрытием
        if not placed:
            max_dist = math.sqrt((width/2)**2 + (height/2)**2)
            center_factor = 1.0 - (dist_from_center / max_dist) * 0.4  # Умеренное ограничение
            
            for attempt in range(500):  # Больше попыток
                # Смещения с учетом центра
                offset_range_x = cell_w * 0.5 * center_factor
                offset_range_y = cell_h * 0.5 * center_factor
                offset_x = random.uniform(-offset_range_x, offset_range_x)
                offset_y = random.uniform(-offset_range_y, offset_range_y)
                x = int(base_x + offset_x - logo_w // 2)
                y = int(base_y + offset_y - logo_h // 2)
                x = max(-logo_w // 4, min(x, width - logo_w * 3 // 4))
                y = max(-logo_h // 4, min(y, height - logo_h * 3 // 4))
                
                angle = random.choice([0, 0, 5, -5, 10, -10, 8, -8, 12, -12, 15, -15, 20, -20])
                
                if angle != 0:
                    logo_rotated = logo.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
                    logo_w_rot, logo_h_rot = logo_rotated.size
                    paste_x = x
                    paste_y = y
                    box = (paste_x, paste_y, logo_w_rot, logo_h_rot)
                    logo_to_place = logo_rotated
                else:
                    paste_x = x
                    paste_y = y
                    box = (paste_x, paste_y, logo_w, logo_h)
                    logo_to_place = logo
                
                # Вычисляем площадь перекрытия
                overlap_area = 0
                overlap_count = 0
                for placed_box in placed_boxes:
                    if check_overlap(box, placed_box, margin=-30):
                        overlap_count += 1
                        # Оцениваем перекрытие
                        overlap_x = max(x, placed_box[0])
                        overlap_y = max(y, placed_box[1])
                        overlap_w = min(x + box[2], placed_box[0] + placed_box[2]) - overlap_x
                        overlap_h = min(y + box[3], placed_box[1] + placed_box[3]) - overlap_y
                        if overlap_w > 0 and overlap_h > 0:
                            overlap_area += overlap_w * overlap_h
                
                # Разрешаем до 45% перекрытия для размещения всех
                if overlap_area < (box[2] * box[3] * 0.45) and overlap_count <= 4:
                    try:
                        temp = Image.new('RGBA', background.size, (0, 0, 0, 0))
                        temp.paste(logo_to_place, (paste_x, paste_y), logo_to_place)
                        background = Image.alpha_composite(background, temp)
                        placed_boxes.append(box)
                        placed_count += 1
                        placed = True
                        break
                    except:
                        pass
        
        # Последняя попытка - размещаем в центре ячейки
        if not placed:
            # Размещаем точно в центре ячейки с поворотом
            x = int(base_x - logo_w // 2)
            y = int(base_y - logo_h // 2)
            x = max(-logo_w // 2, min(x, width - logo_w // 2))
            y = max(-logo_h // 2, min(y, height - logo_h // 2))
            
            angle = random.choice([0, 5, -5, 10, -10, 15, -15])
            if angle != 0:
                logo_rotated = logo.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))
                logo_w_rot, logo_h_rot = logo_rotated.size
                paste_x = x
                paste_y = y
                box = (paste_x, paste_y, logo_w_rot, logo_h_rot)
                logo_to_place = logo_rotated
            else:
                paste_x = x
                paste_y = y
                box = (paste_x, paste_y, logo_w, logo_h)
                logo_to_place = logo
            
            try:
                temp = Image.new('RGBA', background.size, (0, 0, 0, 0))
                temp.paste(logo_to_place, (paste_x, paste_y), logo_to_place)
                background = Image.alpha_composite(background, temp)
                placed_boxes.append(box)
                placed_count += 1
            except:
                pass
    
    # Конвертируем в RGB
    final = background.convert('RGB')
    
    # Сохраняем
    final.save(output_file, 'PNG', quality=95)
    print(f"\n✅ Стена из логотипов сохранена: {output_file}")
    print(f"   Размер: {width}x{height} пикселей")
    print(f"   Логотипов размещено: {placed_count}/{num_logos}")
    print(f"   Стиль: Равномерное распределение, хаотичные повороты")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("Генератор стены из логотипов")
    print("Плотное размещение без пробелов")
    print("=" * 70)
    
    create_wall_texture(
        output_file="events_background.png",
        width=2000,
        height=700,
        bg_color=(45, 55, 72),
        opacity=0.85
    )
