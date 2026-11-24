"""'여러 PC에서 함께 쓰기' 홍보 그림 (글자 없음, 언어별로 앱 화면만 바뀜).

python marketing/make_sync_art.py
→ marketing/sync/sync_{ko,en,ja,zh}.png   (1600×900, 홈페이지·README·Store용)
   marketing/sync/sync_square_{ko,en}.png (1080×1080, SNS용)

가운데 클라우드 폴더(Dropbox·OneDrive·공유 폴더)에 자물쇠 — 파일은 암호화된 채로만 오간다.
왼쪽 데스크톱, 오른쪽 노트북에 같은 Hushpad 화면, 사이를 점선 화살표와 암호화된 메모 조각이 오간다.
앱 화면은 website/assets/img/app-light*.png, app-dark*.png (언어별).
"""
from __future__ import annotations

import math
import os

from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
IMG = os.path.join(ROOT, "website", "assets", "img")
OUT = os.path.join(HERE, "sync")
ICON = os.path.join(ROOT, "assets", "app_1024.png")

PLUM, PLUM2, PLUM_DEEP = (122, 60, 147), (155, 77, 181), (58, 26, 74)
PEACH, PEACH_D = (255, 179, 138), (224, 112, 63)
INK, SOFT = (28, 26, 31), (245, 244, 247)
WHITE = (255, 255, 255)
SS = 2   # 그릴 때 2배로 그리고 줄여 매끈하게


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def bg(w, h):
    im = Image.new("RGB", (w, h), SOFT)
    px = im.load()
    for y in range(h):
        for x in range(0, w, 4):
            t = (x / w * 0.55 + y / h * 0.45)
            c = lerp((248, 246, 251), (238, 228, 246), t)
            for k in range(4):
                if x + k < w:
                    px[x + k, y] = c
    return im.convert("RGBA")


def glow(img, xy, r, color, alpha):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x, y = xy
    ImageDraw.Draw(layer).ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(r * 0.55)))


def shadow(img, box, radius, blur, alpha, off=(0, 18)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(layer).rounded_rectangle([x0 + off[0], y0 + off[1], x1 + off[0], y1 + off[1]], radius,
                                            fill=(40, 16, 56, alpha))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(blur)))


def screen(name, w, h):
    s = Image.open(os.path.join(IMG, name)).convert("RGB")
    # 화면 비율에 맞춰 위쪽 기준으로 잘라 넣는다
    r = w / h
    if s.width / s.height > r:
        nw = int(s.height * r)
        s = s.crop(((s.width - nw) // 2, 0, (s.width - nw) // 2 + nw, s.height))
    else:
        s = s.crop((0, 0, s.width, int(s.width / r)))
    return s.resize((w, h), Image.LANCZOS)


def rounded_paste(img, im, xy, r):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    img.paste(im, xy, mask)


def monitor(img, cx, top, w, shot):
    """데스크톱 모니터 (화면 w, 받침대 포함)."""
    d = ImageDraw.Draw(img)
    h = int(w * 0.6)
    bez = int(w * 0.03)
    x0, y0 = cx - w // 2 - bez, top
    x1, y1 = cx + w // 2 + bez, top + h + bez * 2
    shadow(img, (x0, y0, x1, y1 + int(w * 0.12)), 28 * SS, 30 * SS, 70)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], 18 * SS, fill=(34, 30, 40))
    rounded_paste(img, screen(shot, w, h), (x0 + bez, y0 + bez), 6 * SS)
    # 받침대
    nw, nh = int(w * 0.12), int(w * 0.09)
    d.polygon([(cx - nw // 2, y1), (cx + nw // 2, y1), (cx + nw // 2 + 14 * SS, y1 + nh), (cx - nw // 2 - 14 * SS, y1 + nh)],
              fill=(206, 200, 214))
    bw = int(w * 0.34)
    d.rounded_rectangle([cx - bw // 2, y1 + nh - 4 * SS, cx + bw // 2, y1 + nh + 12 * SS], 8 * SS, fill=(190, 183, 200))
    return (x0, y0, x1, y1)


def laptop(img, cx, top, w, shot):
    """노트북 (화면 w)."""
    d = ImageDraw.Draw(img)
    h = int(w * 0.62)
    bez = int(w * 0.035)
    x0, y0 = cx - w // 2 - bez, top
    x1, y1 = cx + w // 2 + bez, top + h + bez * 2
    shadow(img, (x0 - 40 * SS, y0, x1 + 40 * SS, y1 + 30 * SS), 26 * SS, 30 * SS, 70)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([x0, y0, x1, y1], 16 * SS, fill=(34, 30, 40))
    rounded_paste(img, screen(shot, w, h), (x0 + bez, y0 + bez), 5 * SS)
    # 아래판
    d.rounded_rectangle([x0 - 46 * SS, y1 - 2 * SS, x1 + 46 * SS, y1 + 18 * SS], 10 * SS, fill=(214, 208, 222))
    d.rounded_rectangle([cx - 60 * SS, y1 - 2 * SS, cx + 60 * SS, y1 + 6 * SS], 4 * SS, fill=(190, 183, 200))
    return (x0, y0, x1, y1)


def cloud(img, cx, cy, s):
    """구름 + 자물쇠 배지 (s = 너비)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    r1, r2, r3 = int(s * 0.24), int(s * 0.31), int(s * 0.2)
    base_y = cy + int(s * 0.12)
    d.ellipse([cx - int(s * 0.42) - r1, base_y - r1 * 2 + int(s * 0.06), cx - int(s * 0.42) + r1, base_y + int(s * 0.06)], fill=WHITE)
    d.ellipse([cx - r2 - int(s * 0.05), base_y - r2 * 2 - int(s * 0.02), cx + r2 - int(s * 0.05), base_y - int(s * 0.02)], fill=WHITE)
    d.ellipse([cx + int(s * 0.3) - r3, base_y - r3 * 2 + int(s * 0.02), cx + int(s * 0.3) + r3, base_y + int(s * 0.02)], fill=WHITE)
    d.rounded_rectangle([cx - int(s * 0.62), base_y - int(s * 0.2), cx + int(s * 0.52), base_y + int(s * 0.08)], int(s * 0.14), fill=WHITE)
    mask = layer.split()[3]
    # 그림자
    sh = Image.new("RGBA", img.size, (40, 16, 56, 0))
    sh.putalpha(mask.point(lambda v: v * 70 // 255))
    img.alpha_composite(sh.transform(img.size, Image.AFFINE, (1, 0, 0, 0, 1, -16 * SS)).filter(ImageFilter.GaussianBlur(22 * SS)))
    # 자두색 그라데이션 구름
    grad = Image.new("RGBA", img.size)
    gd = ImageDraw.Draw(grad)
    top, bot = cy - int(s * 0.62), base_y + int(s * 0.1)
    for y in range(top, bot):
        t = (y - top) / max(1, bot - top)
        gd.line([(0, y), (img.width, y)], fill=lerp(PLUM2, PLUM_DEEP, t) + (255,))
    grad.putalpha(mask)
    img.alpha_composite(grad)
    # 구름 위 반짝임
    hl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([cx - int(s * 0.32), cy - int(s * 0.58), cx + int(s * 0.12), cy - int(s * 0.28)], fill=(255, 255, 255, 40))
    hl = hl.filter(ImageFilter.GaussianBlur(14 * SS))
    hl.putalpha(Image.composite(hl.split()[3], Image.new("L", img.size, 0), mask))
    img.alpha_composite(hl)
    # 자물쇠 배지
    d = ImageDraw.Draw(img)
    br = int(s * 0.17)
    bx, by = cx - int(s * 0.04), cy - int(s * 0.08)
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=PEACH)
    lw, lh = int(br * 0.95), int(br * 0.72)
    d.rounded_rectangle([bx - lw // 2, by - lh // 4, bx + lw // 2, by - lh // 4 + lh], int(br * 0.14), fill=WHITE)
    sw = max(3, int(br * 0.14))
    d.arc([bx - int(lw * 0.32), by - int(lh * 0.95), bx + int(lw * 0.32), by - lh // 4 + sw], 180, 360, fill=WHITE, width=sw)
    d.ellipse([bx - sw, by + int(lh * 0.12), bx + sw, by + int(lh * 0.12) + sw * 2], fill=PEACH_D)


def chip(img, cx, cy, w, color=PLUM):
    """암호화된 메모 조각 (점 무늬)."""
    d = ImageDraw.Draw(img)
    h = int(w * 0.62)
    shadow(img, (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2), 8 * SS, 8 * SS, 60, off=(0, 6 * SS))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2], 8 * SS, fill=WHITE, outline=color + (255,), width=2 * SS)
    dot = max(2, w // 14)
    for row in range(2):
        for col in range(5):
            x = cx - w // 2 + int(w * 0.16) + col * int(w * 0.17)
            y = cy - h // 4 + row * int(h * 0.42)
            d.ellipse([x - dot, y - dot, x + dot, y + dot], fill=color if (row + col) % 3 else PEACH_D)


def dashed_arc(img, p0, p1, bend, color, width, dash, gap, arrow_end=True, arrow_start=True):
    """p0→p1을 잇는 휘어진 점선 + 양쪽 화살촉. 점들을 돌려준다."""
    d = ImageDraw.Draw(img)
    (x0, y0), (x1, y1) = p0, p1
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    ln = math.hypot(nx, ny) or 1
    qx, qy = mx + nx / ln * bend, my + ny / ln * bend
    pts = []
    for i in range(201):
        t = i / 200
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * qx + t * t * x1
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * qy + t * t * y1
        pts.append((x, y))
    acc, on, last = 0.0, True, pts[0]
    seg = [pts[0]]
    for p in pts[1:]:
        acc += math.hypot(p[0] - last[0], p[1] - last[1])
        seg.append(p)
        if acc >= (dash if on else gap):
            if on:
                d.line(seg, fill=color, width=width, joint="curve")
            seg, acc, on = [p], 0.0, not on
        last = p
    if on and len(seg) > 1:
        d.line(seg, fill=color, width=width, joint="curve")

    def head(tip, prev):
        ang = math.atan2(tip[1] - prev[1], tip[0] - prev[0])
        L = width * 4.2
        a1 = (tip[0] - L * math.cos(ang - 0.5), tip[1] - L * math.sin(ang - 0.5))
        a2 = (tip[0] - L * math.cos(ang + 0.5), tip[1] - L * math.sin(ang + 0.5))
        d.polygon([tip, a1, a2], fill=color)
    if arrow_end:
        head(pts[-1], pts[-8])
    if arrow_start:
        head(pts[0], pts[7])
    return pts


def make(lang: str, w=1600, h=900):
    sfx = "" if lang == "ko" else f"-{lang}"
    W, H = w * SS, h * SS
    img = bg(W, H)
    glow(img, (int(W * 0.5), int(H * 0.2)), int(W * 0.22), PEACH, 70)
    glow(img, (int(W * 0.15), int(H * 0.9)), int(W * 0.2), PLUM2, 40)
    glow(img, (int(W * 0.88), int(H * 0.85)), int(W * 0.2), PEACH, 45)
    # 기기
    mon = monitor(img, int(W * 0.235), int(H * 0.36), int(W * 0.34), f"app-light{sfx}.png")
    lap = laptop(img, int(W * 0.77), int(H * 0.43), int(W * 0.30), f"app-dark{sfx}.png")
    # 구름
    ccx, ccy = int(W * 0.5), int(H * 0.22)
    # 연결선 (구름 ↔ 기기)
    col = PLUM + (235,)
    left_pts = dashed_arc(img, (int(W * 0.29), mon[1] - 18 * SS), (ccx - int(W * 0.105), ccy + int(H * 0.04)), -70 * SS, col, 5 * SS, 18 * SS, 14 * SS)
    right_pts = dashed_arc(img, (ccx + int(W * 0.1), ccy + int(H * 0.04)), (int(W * 0.72), lap[1] - 18 * SS), -70 * SS, col, 5 * SS, 18 * SS, 14 * SS)
    cloud(img, ccx, ccy, int(W * 0.17))
    # 오가는 암호화 조각
    for pts, t in ((left_pts, 0.42), (right_pts, 0.58)):
        x, y = pts[int(t * 200)]
        chip(img, int(x), int(y) - 4 * SS, int(W * 0.045))
    # 아이콘 배지 (두 기기 화면 위 구석에 작은 Hushpad 아이콘)
    ic = Image.open(ICON).convert("RGBA").resize((int(W * 0.05),) * 2, Image.LANCZOS)
    for box in (mon, lap):
        img.alpha_composite(ic, (box[2] - ic.width // 2 - 6 * SS, box[1] - ic.height // 2 + 6 * SS))
    return img.resize((w, h), Image.LANCZOS).convert("RGB")


def main():
    os.makedirs(OUT, exist_ok=True)
    for lang in ("ko", "en", "ja", "zh"):
        im = make(lang)
        p = os.path.join(OUT, f"sync_{lang}.png")
        im.save(p, optimize=True)
        print(p, im.size)
    for lang in ("ko", "en"):
        im = make(lang)
        sq = Image.new("RGB", (1080, 1080), SOFT)
        r = im.resize((1080, 608), Image.LANCZOS)
        sq.paste(r, (0, 236))
        p = os.path.join(OUT, f"sync_square_{lang}.png")
        sq.save(p, optimize=True)
        print(p, sq.size)


if __name__ == "__main__":
    main()
