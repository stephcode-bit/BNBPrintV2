"""
Generates the BNBPRINT app icons (PWA + favicon) from a simple vector
description, so there's no external image dependency. Matches the
components/Logo.tsx mark: a dark rounded-square badge with a BNB-yellow
diamond burst.

Run: python3 scripts/generate_icons.py
Requires: pillow (pip install pillow)
"""
import math
import os

from PIL import Image, ImageDraw

BLACK = (11, 14, 17, 255)
YELLOW = (240, 185, 11, 255)
YELLOW_DIM = (240, 185, 11, 140)

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "public", "icons")
os.makedirs(OUT_DIR, exist_ok=True)


def diamond(cx, cy, r):
    return [(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)]


def draw_mark(size: int, padding_ratio: float = 0.0, rounded: bool = True) -> Image.Image:
    scale = 4  # supersample for smooth edges
    s = size * scale
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    pad = int(s * padding_ratio)
    if rounded:
        radius = int(s * 0.24)
        draw.rounded_rectangle([pad, pad, s - pad, s - pad], radius=radius, fill=BLACK)
    else:
        draw.rectangle([pad, pad, s - pad, s - pad], fill=BLACK)

    cx, cy = s / 2, s / 2
    unit = s / 48  # matches the 48x48 viewBox used in Logo.tsx

    # central diamond
    draw.polygon(diamond(cx, cy, unit * 6), fill=YELLOW)
    # orbiting shards
    offset = unit * 12
    shard_r = unit * 3.5
    draw.polygon(diamond(cx - offset, cy, shard_r), fill=YELLOW)
    draw.polygon(diamond(cx + offset, cy, shard_r), fill=YELLOW)
    draw.polygon(diamond(cx, cy + offset, shard_r), fill=YELLOW)
    draw.polygon(diamond(cx, cy - offset, shard_r), fill=YELLOW_DIM)

    return img.resize((size, size), Image.LANCZOS)


def main():
    # Standard PWA icons
    for size in (192, 512):
        icon = draw_mark(size)
        icon.save(os.path.join(OUT_DIR, f"icon-{size}.png"))

    # Maskable icon needs extra safe-area padding (Android adaptive icons)
    maskable = draw_mark(512, padding_ratio=0.08)
    maskable.save(os.path.join(OUT_DIR, "icon-512-maskable.png"))

    # Apple touch icon
    apple = draw_mark(180)
    apple.save(os.path.join(OUT_DIR, "apple-touch-icon.png"))

    # Favicon (multi-size .ico) in the public/ root
    fav_sizes = [16, 32, 48]
    favicon_dir = os.path.join(OUT_DIR, "..")
    fav_img = draw_mark(48)
    fav_img.save(
        os.path.join(favicon_dir, "favicon.ico"),
        sizes=[(s, s) for s in fav_sizes],
    )

    print("Icons generated in", os.path.abspath(OUT_DIR))


if __name__ == "__main__":
    main()
