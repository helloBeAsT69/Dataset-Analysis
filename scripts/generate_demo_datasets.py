import os
import random
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEAN_DIR = os.path.join(BASE_DIR, "datasets", "clean_demo")
COMPROMISED_DIR = os.path.join(BASE_DIR, "datasets", "compromised_demo")

SIGN_TYPES = [
    ("STOP", "octagon", (210, 30, 30), (255, 255, 255)),
    ("SPEED 50", "circle", (245, 245, 245), (20, 20, 20)),
    ("YIELD", "triangle", (255, 255, 255), (210, 30, 30)),
    ("CAUTION", "diamond", (250, 200, 15), (20, 20, 20)),
    ("ONE WAY", "rect", (30, 30, 30), (255, 255, 255)),
    ("CROSSWALK", "diamond", (250, 200, 15), (20, 20, 20)),
    ("NO ENTRY", "circle", (210, 30, 30), (255, 255, 255)),
    ("ROUNDABOUT", "circle", (25, 95, 210), (255, 255, 255)),
    ("HOSPITAL", "rect", (25, 95, 210), (255, 255, 255)),
    ("PARKING", "rect", (25, 95, 210), (255, 255, 255)),
]

def generate_photorealistic_traffic_image(index: int, width: int = 128, height: int = 128) -> Image.Image:
    random.seed(index * 937 + 101)
    np.random.seed(index * 937 + 101)

    # 1. Realistic road / sky / environment backdrop with distinct color hues
    sky_hue = (index * 29) % 180
    sky_top = (70 + (sky_hue % 80), 110 + ((sky_hue * 3) % 70), 180 + ((sky_hue * 2) % 60))
    ground_bot = (random.randint(50, 90), random.randint(50, 90), random.randint(50, 90))
    
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        ratio = y / height
        r = int(sky_top[0] * (1 - ratio) + ground_bot[0] * ratio + random.randint(-4, 4))
        g = int(sky_top[1] * (1 - ratio) + ground_bot[1] * ratio + random.randint(-4, 4))
        b = int(sky_top[2] * (1 - ratio) + ground_bot[2] * ratio + random.randint(-4, 4))
        arr[y, :, 0] = np.clip(r, 0, 255)
        arr[y, :, 1] = np.clip(g, 0, 255)
        arr[y, :, 2] = np.clip(b, 0, 255)

    img = Image.fromarray(arr, 'RGB')
    draw = ImageDraw.Draw(img)

    # Add background environmental elements (road line, distant tree / structure)
    road_y = height // 2 + random.randint(5, 25)
    draw.polygon([(0, road_y), (width, road_y + random.randint(-10, 10)), (width, height), (0, height)], fill=(70, 75, 80))
    draw.line([(width // 2, road_y), (width // 2 + random.randint(-20, 20), height)], fill=(240, 240, 240), width=2)

    # 2. Add traffic sign object
    sign_text, shape, bg_col, fg_col = SIGN_TYPES[(index * 3 + index // 10) % len(SIGN_TYPES)]
    cx = width // 2 + ((index * 11) % 25 - 12)
    cy = height // 2 - ((index * 7) % 15 + 5)
    radius = 24 + ((index * 5) % 15)

    # Signpost
    draw.line([(cx, cy + radius), (cx, road_y + 15)], fill=(120, 120, 120), width=4)

    box = [cx - radius, cy - radius, cx + radius, cy + radius]

    if shape == "circle":
        draw.ellipse(box, fill=bg_col, outline=(200, 0, 0) if bg_col != (210, 30, 30) else (255, 255, 255), width=3)
    elif shape == "octagon":
        d = int(radius * 0.58)
        pts = [
            (cx - radius + d, cy - radius), (cx + radius - d, cy - radius),
            (cx + radius, cy - radius + d), (cx + radius, cy + radius - d),
            (cx + radius - d, cy + radius), (cx - radius + d, cy + radius),
            (cx - radius, cy + radius - d), (cx - radius, cy - radius + d)
        ]
        draw.polygon(pts, fill=bg_col, outline=(255, 255, 255), width=3)
    elif shape == "triangle":
        pts = [(cx, cy - radius), (cx + radius, cy + radius), (cx - radius, cy + radius)]
        draw.polygon(pts, fill=bg_col, outline=(200, 0, 0), width=3)
    elif shape == "diamond":
        pts = [(cx, cy - radius), (cx + radius, cy), (cx, cy + radius), (cx - radius, cy)]
        draw.polygon(pts, fill=bg_col, outline=(0, 0, 0), width=2)
    else: # rect
        draw.rounded_rectangle(box, radius=6, fill=bg_col, outline=(255, 255, 255), width=2)

    # Sign label
    draw.text((cx, cy), sign_text, fill=fg_col, anchor="mm")

    return img


def create_near_duplicate(img: Image.Image, mode: int) -> Image.Image:
    """Subtle perceptual modifications (Hamming distance 1..4)."""
    im = img.copy()
    if mode == 0:
        # Slight brightness
        return ImageEnhance.Brightness(im).enhance(1.12)
    elif mode == 1:
        # Slight contrast
        return ImageEnhance.Contrast(im).enhance(1.15)
    elif mode == 2:
        # Minor crop & resize back
        w, h = im.size
        return im.crop((2, 2, w - 2, h - 2)).resize((w, h), Image.Resampling.BILINEAR)
    elif mode == 3:
        # Slight color temperature adjustment
        return ImageEnhance.Color(im).enhance(1.20)
    elif mode == 4:
        # Subtle tiny watermark in bottom corner
        w, h = im.size
        draw = ImageDraw.Draw(im)
        draw.rectangle([4, h - 10, 16, h - 4], fill=(130, 130, 130))
        return im
    elif mode == 5:
        # Subtle Gaussian blur
        return im.filter(ImageFilter.GaussianBlur(radius=0.6))
    elif mode == 6:
        # Brightness decrease
        return ImageEnhance.Brightness(im).enhance(0.90)
    else:
        # Sharpness increase
        return ImageEnhance.Sharpness(im).enhance(1.25)


def create_anomaly(width: int = 128, height: int = 128, mode: int = 0) -> Image.Image:
    """Create severe synthetic corruption samples."""
    if mode == 0:
        # Pure uniform salt-and-pepper / sensor static
        np.random.seed(1337)
        noise = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(noise, 'RGB')
    elif mode == 1:
        # Complete camera blackout / occlusion
        black = np.random.randint(0, 4, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(black, 'RGB')
    elif mode == 2:
        # Complete glare whiteout / sensor saturation
        white = np.random.randint(252, 256, (height, width, 3), dtype=np.uint8)
        return Image.fromarray(white, 'RGB')
    else:
        # Severe hardware color-channel fault (pure magenta inversion defect)
        fault = np.zeros((height, width, 3), dtype=np.uint8)
        fault[:, :, 0] = 255 # R
        fault[:, :, 2] = 255 # B
        fault[::4, :, :] = 0 # Horizontal drop lines
        return Image.fromarray(fault, 'RGB')


def main():
    os.makedirs(CLEAN_DIR, exist_ok=True)
    os.makedirs(COMPROMISED_DIR, exist_ok=True)

    # Clear old images
    for d in [CLEAN_DIR, COMPROMISED_DIR]:
        for f in os.listdir(d):
            if f.endswith(".png"):
                os.remove(os.path.join(d, f))

    # 1. Clean Dataset: 50 distinct realistic images
    clean_images = []
    print(f"Generating 50 clean images in: {CLEAN_DIR}")
    for i in range(50):
        img = generate_photorealistic_traffic_image(index=i)
        img.save(os.path.join(CLEAN_DIR, f"clean_{i:03d}.png"), format="PNG")
        clean_images.append(img)

    # 2. Compromised Dataset (50 total images):
    # - 26 distinct normal images
    # - 12 exact duplicate copies (clones of the first 12 normal images)
    # - 8 near duplicates (perceptually altered versions of normal images 12..19)
    # - 4 anomalies (sensor noise, blackout, whiteout, channel fault)
    # Total = 26 + 12 + 8 + 4 = 50 images!
    print(f"Generating compromised dataset in: {COMPROMISED_DIR}")

    # 26 Normal base images
    for i in range(26):
        clean_images[i].save(os.path.join(COMPROMISED_DIR, f"sample_{i:03d}.png"), format="PNG")

    # 12 Exact Duplicates
    for i in range(12):
        clean_images[i].save(os.path.join(COMPROMISED_DIR, f"exact_dup_of_{i:03d}.png"), format="PNG")

    # 8 Near Duplicates
    for i in range(8):
        near_dup = create_near_duplicate(clean_images[12 + i], mode=i % 8)
        near_dup.save(os.path.join(COMPROMISED_DIR, f"near_dup_var_{i:03d}.png"), format="PNG")

    # 4 Anomalies
    for i in range(4):
        anom = create_anomaly(128, 128, mode=i)
        anom.save(os.path.join(COMPROMISED_DIR, f"anomaly_{i:03d}.png"), format="PNG")

    print(f"Finished generating datasets.")
    print(f"Clean count: {len(os.listdir(CLEAN_DIR))}")
    print(f"Compromised count: {len(os.listdir(COMPROMISED_DIR))}")


if __name__ == "__main__":
    main()
