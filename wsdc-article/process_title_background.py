"""
Process all_logos_clean.png into an organic title background.
Uses multi-layer blending to create a textured background while preserving logo visibility.
"""
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

INPUT_FILE = "/Users/ania/Downloads/Swing dance event logo collage.png"
OUTPUT_FILE = "events_background.png"
TARGET_WIDTH = 2000
TARGET_HEIGHT = 700
BG_COLOR = (45, 55, 72)  # #2d3748


def create_organic_title_background():
    """Create an organic poster background from clean logo grid."""
    
    # 1. Load and prepare base image
    try:
        img = Image.open(INPUT_FILE).convert("RGBA")
        print(f"Original size: {img.size}")
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    # 2. Stretch directly to target size (ignore aspect ratio, fill completely)
    # This ensures no internal padding/borders are added
    img_cropped = img.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)

    # 3. Slightly reduce brightness (preserves structure, logos remain visible)
    brightness_enhancer = ImageEnhance.Brightness(img_cropped)
    img_darkened = brightness_enhancer.enhance(0.75)  # 75% brightness - logos visible

    # 4. Create dark blue overlay with lighter opacity
    overlay = Image.new("RGBA", img_darkened.size, BG_COLOR + (140,))  # ~55% opacity
    
    # Use blend for better color mixing
    # Blend mode: img1 * (1 - alpha) + img2 * alpha
    img_blended = Image.blend(img_darkened, overlay, alpha=0.45)  # Lighter blend

    # 5. Enhance contrast to make logos stand out as texture
    contrast_enhancer = ImageEnhance.Contrast(img_blended)
    img_final = contrast_enhancer.enhance(1.25)  # More contrast for visibility

    # 6. Optional: Very subtle blur for organic feel (commented out for now)
    # img_final = img_final.filter(ImageFilter.GaussianBlur(radius=0.5))

    # 7. Save
    img_final.save(OUTPUT_FILE)
    print(f"✓ Title background saved to {OUTPUT_FILE} ({TARGET_WIDTH}x{TARGET_HEIGHT}px)")


if __name__ == "__main__":
    create_organic_title_background()

