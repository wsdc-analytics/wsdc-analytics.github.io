from PIL import Image, ImageOps
import os
import glob
import random

# Configuration
ARTIFACTS_DIR = "/Users/ania/.gemini/antigravity/brain/b227587e-49a3-43a3-81f0-f868cd6c1c4a"
OUTPUT_DIR = "/Users/ania/.gemini/antigravity/brain/b227587e-49a3-43a3-81f0-f868cd6c1c4a"
SOURCE_DIR = "/Users/ania/Desktop/Ранкинг пост/Dancers/Dancers"
BG_IMAGE_NAME = "uploaded_image_1768166979584.jpg"

CANVAS_SIZE = (1920, 1080)
MARGIN = 40
GAP = 15     # Smaller gap for denser grid

SHADOW_OFFSET = 6
SHADOW_COLOR = (0, 0, 0, 200)

def make_collage():
    # 1. Prepare Background
    bg_path = os.path.join(ARTIFACTS_DIR, BG_IMAGE_NAME)
    if not os.path.exists(bg_path):
        print(f"Error: Background image not found at {bg_path}")
        return

    bg = Image.open(bg_path).convert("RGBA")
    bg = ImageOps.fit(bg, CANVAS_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
    
    canvas = Image.new("RGBA", CANVAS_SIZE)
    canvas.paste(bg, (0, 0))
    
    # 2. Get Images
    extensions = ['*.jpg', '*.jpeg', '*.png']
    image_paths = []
    for ext in extensions:
        image_paths.extend(glob.glob(os.path.join(SOURCE_DIR, ext)))
        image_paths.extend(glob.glob(os.path.join(SOURCE_DIR, ext.upper())))
    
    image_paths = sorted(list(set(image_paths)))
    # Exclude the collage itself
    image_paths = [p for p in image_paths if "dancers_collage" not in os.path.basename(p)]
    
    if not image_paths:
        print(f"No images found in {SOURCE_DIR}")
        return

    count = len(image_paths)
    print(f"Found {count} unique images.")

    # 3. Duplicate images to fill a denser grid
    # Target: ~60 images (10 cols x 6 rows)
    # 15 * 4 = 60.
    target_count = 60
    
    # Repeat list until we have enough
    full_image_list = image_paths * (target_count // count + 1)
    # Trim to exact target or just use what we need
    random.shuffle(full_image_list) # Mix them up
    
    # 4. Calculate Layout (Grid 10x6)
    cols = 10
    rows = 6
    
    selected_images = full_image_list[:cols*rows]
    
    # Calculate Slot Size
    avail_w = CANVAS_SIZE[0] - 2*MARGIN - (cols-1)*GAP
    avail_h = CANVAS_SIZE[1] - 2*MARGIN - (rows-1)*GAP
    
    slot_w = avail_w // cols
    slot_h = avail_h // rows
    
    print(f"Grid: {cols}x{rows} = {len(selected_images)} items")
    print(f"Slot size: {slot_w}x{slot_h}")

    # Center grid
    total_grid_w = cols * slot_w + (cols-1) * GAP
    total_grid_h = rows * slot_h + (rows-1) * GAP
    
    start_x = (CANVAS_SIZE[0] - total_grid_w) // 2
    start_y = (CANVAS_SIZE[1] - total_grid_h) // 2

    # 5. Process and Place Images
    for i, img_path in enumerate(selected_images):
        try:
            r = i // cols
            c = i % cols
            
            x = start_x + c * (slot_w + GAP)
            y = start_y + r * (slot_h + GAP)
            
            img = Image.open(img_path).convert("RGBA")
            
            # NO CROP: Thumbnail to fit inside box
            img.thumbnail((slot_w, slot_h), Image.Resampling.LANCZOS)
            
            # Center in slot
            img_x = x + (slot_w - img.width) // 2
            img_y = y + (slot_h - img.height) // 2
            
            # Shadow
            if SHADOW_OFFSET > 0:
                shadow = Image.new("RGBA", (img.width, img.height), SHADOW_COLOR)
                canvas.paste(shadow, (img_x + SHADOW_OFFSET, img_y + SHADOW_OFFSET), mask=shadow)
            
            # Paste Image
            canvas.paste(img, (img_x, img_y))
            
        except Exception as e:
            print(f"Failed to process {img_path}: {e}")

    # 6. Save
    output_filename = "dancers_collage_v5.png"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    canvas.save(output_path, "PNG")
    print(f"Success: Collage saved to {output_path}")

if __name__ == "__main__":
    make_collage()
