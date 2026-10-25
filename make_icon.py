#!/usr/bin/env python3
"""Generate icon-512.png — brand §6: eclipse motif on navy (#0d1b2a),
one per-product glyph. Compass's glyph is the navigator's instrument:
a four-point compass star with a needle, inside the gradient eclipse
ring. PIL only; deterministic."""
from PIL import Image, ImageDraw

S = 512
NAVY = (13, 27, 42, 255)
STOPS = [(15, 246, 247), (0, 212, 255), (123, 44, 191)]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3)) + (255,)


def grad(t):
    return lerp(STOPS[0], STOPS[1], t * 2) if t < 0.5 else \
        lerp(STOPS[1], STOPS[2], (t - 0.5) * 2)


def main():
    img = Image.new("RGBA", (S, S), NAVY)
    d = ImageDraw.Draw(img)
    ring = [54, 54, 458, 458]
    for i in range(72):
        t = i / 72
        d.arc(ring, start=i * 5, end=i * 5 + 6, fill=grad(t), width=13)
    d.ellipse([126, 126, 386, 386], fill=NAVY)
    cx = cy = 256
    # Four-point compass star (long N/E/S/W points, short diagonals).
    for angle, length, width, t in (
            (0, 108, 17, 0.05), (90, 96, 15, 0.35),
            (180, 96, 15, 0.6), (270, 96, 15, 0.85),
            (45, 56, 10, 0.25), (135, 56, 10, 0.5),
            (225, 56, 10, 0.7), (315, 56, 10, 0.95)):
        import math
        rad = math.radians(angle - 90)
        rad_l = math.radians(angle - 90 - 90)
        rad_r = math.radians(angle - 90 + 90)
        tip = (cx + length * math.cos(rad), cy + length * math.sin(rad))
        left = (cx + width * math.cos(rad_l), cy + width * math.sin(rad_l))
        right = (cx + width * math.cos(rad_r), cy + width * math.sin(rad_r))
        d.polygon([tip, left, right], fill=grad(t))
    # Needle hub.
    d.ellipse([cx - 20, cy - 20, cx + 20, cy + 20],
              fill=(254, 254, 254, 255))
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=NAVY)
    img.save("icon-512.png")
    print("wrote icon-512.png", img.size, img.mode)


if __name__ == "__main__":
    main()
