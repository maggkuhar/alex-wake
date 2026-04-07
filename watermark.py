from PIL import Image, ImageDraw, ImageFont
import os, math

ORIGINALS_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'paintings')
WATERMARKED_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images', 'paintings')

os.makedirs(ORIGINALS_DIR, exist_ok=True)
os.makedirs(WATERMARKED_DIR, exist_ok=True)

def apply_watermark(filename):
    """Накладывает водяной знак на изображение. Оригинал сохраняется в uploads/paintings/"""
    original_path = os.path.join(ORIGINALS_DIR, filename)
    watermarked_path = os.path.join(WATERMARKED_DIR, filename)

    if not os.path.exists(original_path):
        return False

    img = Image.open(original_path).convert('RGBA')
    w, h = img.size

    # Слой для водяного знака
    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    text = '© ALEX WAKE'
    font_size = max(24, min(w, h) // 18)

    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
    except:
        font = ImageFont.load_default()

    # Получаем размер текста
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]

    # Диагональный паттерн водяных знаков
    step_x = tw + 80
    step_y = th + 60
    angle = -30

    for y in range(-h, h * 2, step_y):
        for x in range(-w, w * 2, step_x):
            draw.text((x, y), text, font=font, fill=(255, 255, 255, 55))

    # Один крупный знак по центру
    cx = (w - tw) // 2
    cy = (h - th) // 2
    draw.text((cx, cy), text, font=font, fill=(255, 255, 255, 80))

    # Склеиваем
    watermarked = Image.alpha_composite(img, overlay).convert('RGB')
    watermarked.save(watermarked_path, 'JPEG', quality=85)

    return True
