"""Microsoft Store 표시용 이미지 (네 언어 공통, 글자는 'Hushpad' 이름뿐이거나 없음).

python packaging/msix/store_listing/make_store_art.py
→ store_listing/art/poster_2x3_1440x2160.png   (2:3 포스터 아트, 이름 포함)
   store_listing/art/box_1x1_2160x2160.png      (1:1 박스 아트, 이름 포함)
   store_listing/art/superhero_16x9_3840x2160.png (16:9 수퍼히어로 아트, 글자 없음)

Microsoft 지침: 아래쪽 1/3에는 글자·중요한 그림을 두지 않는다(그라데이션·글자가 겹침).
수퍼히어로 아트는 제품 이름을 포함한 어떤 글자도 넣지 않고, 앱 화면도 넣지 않는다. 중요한 것은 가운데.
"""
from __future__ import annotations

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(HERE, "art")
ICON = os.path.join(ROOT, "assets", "app_1024.png")
FONT_B = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts", "segoeuib.ttf")

PLUM_DEEP, PLUM, PLUM2 = (58, 26, 74), (122, 60, 147), (155, 77, 181)
PEACH, PEACH_D = (255, 179, 138), (224, 112, 63)
WHITE = (255, 255, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def background(w, h):
    """짙은 자두색 → 자두색 → 밝은 자두색으로 부드럽게 이어지는 대각선 그라데이션."""
    import numpy as np
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = math.radians(35)
    t = (xx * math.cos(ang) + yy * math.sin(ang))
    t = (t - t.min()) / (t.max() - t.min())
    t = t * t * (3 - 2 * t)                               # smoothstep: 이음새 없이
    stops = np.array([PLUM_DEEP, PLUM, PLUM2], np.float32)
    u = np.clip(t * 2, 0, 2)
    i = np.minimum(u.astype(int), 1)
    f = (u - i)[..., None]
    rgb = stops[i] * (1 - f) + stops[i + 1] * f
    return Image.fromarray(rgb.astype(np.uint8), "RGB").convert("RGBA")


def glow(img, xy, r, color, alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x, y = xy
    ImageDraw.Draw(layer).ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.6)))


def page(w, h, alpha, lines=True):
    """반투명 메모지 한 장 (줄 몇 개). Hushpad 아이콘의 '흐려지는 종이'와 같은 모티프."""
    pad = int(w * 0.12)
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = int(w * 0.09)
    d.rounded_rectangle([pad, pad, pad + w, pad + h], r, fill=WHITE + (alpha,))
    if lines:
        lw = max(4, int(w * 0.035))
        y = pad + int(h * 0.2)
        rnd = random.Random(w * 7 + h)
        while y < pad + h - int(h * 0.14):
            ln = int(w * rnd.uniform(0.45, 0.72))
            d.rounded_rectangle([pad + int(w * 0.14), y, pad + int(w * 0.14) + ln, y + lw], lw // 2,
                                fill=PLUM + (min(255, int(alpha * 1.1)),))
            y += int(h * 0.13)
    return im


def scatter_pages(img, cx, cy, spread, scale, seed, n=9, avoid_r=0):
    """아이콘 둘레에 기울어진 메모지들이 흩어져 흐려진다(가까운 것은 또렷, 먼 것은 흐릿)."""
    rnd = random.Random(seed)
    placed = 0
    tries = 0
    while placed < n and tries < 400:
        tries += 1
        ang = rnd.uniform(0, 2 * math.pi)
        dist = rnd.uniform(0.35, 1.0)
        x = cx + math.cos(ang) * spread[0] * dist
        y = cy + math.sin(ang) * spread[1] * dist
        if math.hypot(x - cx, y - cy) < avoid_r:
            continue
        w = int(scale * rnd.uniform(0.55, 1.0))
        h = int(w * 1.28)
        far = dist
        p = page(w, h, int(150 - far * 90))
        p = p.rotate(rnd.uniform(-24, 24), resample=Image.BICUBIC, expand=True)
        p = p.filter(ImageFilter.GaussianBlur(2 + far * scale * 0.05))
        img.alpha_composite(p, (int(x - p.width / 2), int(y - p.height / 2)))
        placed += 1


def icon_with_shadow(img, size, cx, cy):
    ic = Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    a = ic.split()[3].point(lambda v: v * 0.45)
    blk = Image.new("RGBA", ic.size, (20, 6, 28, 255))
    blk.putalpha(a)
    sh.alpha_composite(blk, (int(cx - size / 2), int(cy - size / 2 + size * 0.06)))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(size * 0.07)))
    img.alpha_composite(ic, (int(cx - size / 2), int(cy - size / 2)))


def wordmark(img, text, cx, top, size):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_B, size)
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, top), text, font=f, fill=WHITE)


def bottom_fade(img, frac=0.36):
    """아래쪽 1/3은 Store가 그라데이션·글자를 겹치는 자리라 조용하게 어둡힌다."""
    w, h = img.size
    m = Image.new("L", (1, 256))
    for y in range(256):
        m.putpixel((0, y), int(150 * max(0.0, (y / 255 - (1 - frac)) / frac) ** 1.4))
    m = m.resize((w, h))
    dark = Image.new("RGBA", (w, h), PLUM_DEEP + (255,))
    dark.putalpha(m)
    img.alpha_composite(dark)


def poster():                       # 2:3, 1440×2160 — 아이콘·이름은 위쪽 2/3 안
    W, H = 1440, 2160
    img = background(W, H)
    cx, cy = W // 2, int(H * 0.30)
    glow(img, (cx + 120, cy - 60), 620, PEACH, 70)
    glow(img, (cx - 260, int(H * 0.72)), 520, PEACH_D, 40)
    scatter_pages(img, cx, cy + 60, (640, 760), 300, seed=3, n=10, avoid_r=420)
    icon_with_shadow(img, 620, cx, cy)
    wordmark(img, "Hushpad", cx, cy + 380, 170)
    bottom_fade(img)
    return img


def box():                          # 1:1, 2160×2160 — 아이콘·이름은 위쪽 2/3 안
    W = H = 2160
    img = background(W, H)
    cx, cy = W // 2, int(H * 0.33)
    glow(img, (cx + 160, cy - 80), 760, PEACH, 70)
    glow(img, (int(W * 0.2), int(H * 0.8)), 600, PEACH_D, 40)
    scatter_pages(img, cx, cy + 80, (960, 820), 340, seed=11, n=12, avoid_r=560)
    icon_with_shadow(img, 700, cx, cy)
    wordmark(img, "Hushpad", cx, cy + 420, 190)
    bottom_fade(img)
    return img


def superhero():                    # 16:9, 3840×2160 — 글자·앱 화면 없음, 중요한 것은 가운데
    W, H = 3840, 2160
    img = background(W, H)
    cx, cy = W // 2, int(H * 0.42)
    glow(img, (cx + 260, cy - 120), 1000, PEACH, 75)
    glow(img, (int(W * 0.18), int(H * 0.75)), 760, PEACH_D, 45)
    glow(img, (int(W * 0.85), int(H * 0.2)), 640, PLUM2, 60)
    scatter_pages(img, cx, cy + 40, (1750, 900), 430, seed=29, n=18, avoid_r=720)
    icon_with_shadow(img, 900, cx, cy)
    bottom_fade(img, 0.34)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("poster_2x3_1440x2160.png", poster), ("box_1x1_2160x2160.png", box),
                     ("superhero_16x9_3840x2160.png", superhero)):
        im = fn().convert("RGB")
        path = os.path.join(OUT, name)
        im.save(path, optimize=True)
        print(name, im.size, f"{os.path.getsize(path) / 1e6:.1f}MB")


if __name__ == "__main__":
    main()
