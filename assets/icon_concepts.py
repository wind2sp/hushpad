"""Hushpad 아이콘 시안 3종 (Pillow만 사용).

a  Veil Pad  : 메모장 아래쪽을 젖빛 유리(아크릴)가 덮어 내용이 흐려진다 - 있지만 남에게는 안 보인다.
               대표 색: 잉크 슬레이트 + 민트 (차분·서늘). (shh_pad: 세로 막대 '쉿' 안 - 전원 버튼처럼 보여 뺐다)
b  Fade Page : 오른쪽 위가 접힌 메모장의 왼쪽이 작은 조각으로 흩어지며 사라진다 - 화면 캡처에 안 보이는 창.
               대표 색: 짙은 자두빛 + 복숭아.
c  H Page    : 위·아래 가운데가 파여 H 모양이 된 메모장(접힌 모서리) - 머리글자 H이자 메모 한 장.
               대표 색: 인디고 + 라일락.

1024px 그림은 2배로 그린 뒤 LANCZOS로 줄이고, 40px 이하는 상징만 굵게 남긴 그림을 크기마다 따로 그린다.
결과(assets/concepts/): a_1024.png, a.ico, b_1024.png, b.ico, c_1024.png, c.ico, preview.png
"""
import io
import math
import struct
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
OUT = HERE / "concepts"
SIZES = [16, 20, 24, 32, 40, 48, 64, 128, 256]
SMALL_MAX = 40
SS_BIG = 2048          # 1024 그림을 그릴 때의 내부 크기(2배 슈퍼샘플)
SS_SMALL = 12          # 작은 그림은 n*12 크기로 그려서 줄인다


# ───────────────────────── 공통 도구 ─────────────────────────
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lin_grad(size, stops, angle=90):
    """stops: [(t, color)...], angle=90 이면 위→아래, 135 면 왼쪽 위→오른쪽 아래."""
    ramp = Image.linear_gradient("L").resize((size * 2, size * 2), Image.BILINEAR)
    ramp = ramp.rotate(90 - angle, resample=Image.BILINEAR, expand=False)
    o = size // 2
    ramp = ramp.crop((o, o, o + size, o + size))
    out = Image.new("RGB", (size, size), stops[0][1])
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        lo, hi = round(t0 * 255), round(t1 * 255)
        span = max(1, hi - lo)
        lut = [0 if v <= lo else 255 if v >= hi else round((v - lo) * 255 / span) for v in range(256)]
        m = ramp.point(lut)
        out = Image.composite(Image.new("RGB", (size, size), c1), out, m)
    return out


def radial(size, cx, cy, r):
    """중심 (cx,cy)에서 1, 반지름 r에서 0 인 L 마스크."""
    g = Image.radial_gradient("L")  # 256x256, 가운데 0 → 가장자리 255
    g = g.point(lambda v: max(0, 255 - round(v * 255 / 128)))  # 가운데 255, 반지름 128px 에서 0
    d = round(r * 2)
    g = g.resize((d, d), Image.BICUBIC)
    m = Image.new("L", (size, size), 0)
    m.paste(g, (round(cx - r), round(cy - r)))
    return m


def squircle_pts(cx, cy, r, n=5.0, steps=720):
    pts = []
    for i in range(steps):
        a = 2 * math.pi * i / steps
        c, s = math.cos(a), math.sin(a)
        pts.append((cx + r * math.copysign(abs(c) ** (2 / n), c), cy + r * math.copysign(abs(s) ** (2 / n), s)))
    return pts


def poly_mask(size, pts):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m


def mul(a, b):
    return ImageChops.multiply(a, b)


def scale_alpha(m, k):
    return m.point(lambda v: round(v * k))


def shift(m, dx, dy):
    return ImageChops.offset(m, round(dx), round(dy))


def paint(canvas, mask, color, opacity=1.0):
    """마스크 모양으로 단색(또는 RGB 이미지)을 얹는다."""
    if opacity != 1.0:
        mask = scale_alpha(mask, opacity)
    src = color if isinstance(color, Image.Image) else Image.new("RGB", canvas.size, color)
    layer = src.convert("RGBA")
    layer.putalpha(mask)
    canvas.alpha_composite(layer)


def bevel(canvas, mask, d, blur, hi=0.55, lo=0.35, hi_col=(255, 255, 255), lo_col=(0, 0, 0)):
    """왼쪽 위에서 빛이 온다: 왼쪽 위 가장자리는 밝게, 오른쪽 아래 가장자리는 어둡게."""
    b = mask.filter(ImageFilter.GaussianBlur(blur))
    light = mul(mask, ImageChops.invert(shift(b, d, d)))
    dark = mul(mask, ImageChops.invert(shift(b, -d, -d)))
    paint(canvas, light, hi_col, hi)
    paint(canvas, dark, lo_col, lo)


def drop_shadow(canvas, mask, dy, blur, color, opacity):
    s = shift(mask, dy * 0.25, dy).filter(ImageFilter.GaussianBlur(blur))
    paint(canvas, s, color, opacity)


def tile_bg(N, pal, small):
    """둥근 사각(squircle) 바탕. 빛은 왼쪽 위."""
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    margin = N * (0.0 if small else 0.035)
    r = N / 2 - margin
    if small and N < 24 * SS_SMALL:
        r = N / 2 - N * 0.01
    sq = poly_mask(N, squircle_pts(N / 2, N / 2, r, n=5.0 if not small else 4.6))
    if not small:  # 바탕 아래 부드러운 그림자
        drop_shadow(canvas, sq, N * 0.012, N * 0.012, (0, 0, 0), 0.30)
    body = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    paint(body, sq, lin_grad(N, pal["bg"], angle=115))
    # 왼쪽 위 은은한 빛
    paint(body, mul(radial(N, N * 0.28, N * 0.18, N * 0.75), sq), (255, 255, 255), pal.get("glow", 0.16))
    if not small:
        # 테두리 안쪽 빛(위)과 그늘(아래)
        inner = poly_mask(N, squircle_pts(N / 2, N / 2 + N * 0.006, r - N * 0.006, n=5.0))
        rim = ImageChops.subtract(sq, inner)
        paint(body, mul(rim, lin_grad(N, [(0, (255,) * 3), (0.5, (0,) * 3)], 90).convert("L")),
              (255, 255, 255), 0.45)
        inner2 = poly_mask(N, squircle_pts(N / 2, N / 2 - N * 0.007, r - N * 0.006, n=5.0))
        rim2 = ImageChops.subtract(sq, inner2)
        paint(body, mul(rim2, lin_grad(N, [(0.5, (0,) * 3), (1, (255,) * 3)], 90).convert("L")),
              (0, 0, 0), 0.25)
    if small and pal.get("rim_small"):
        # 어두운 바탕(작업 표시줄)에서도 테두리가 보이게 얇은 밝은 테두리
        rim = ImageChops.subtract(sq, sq.filter(ImageFilter.MinFilter(_odd(N * 0.06))))
        paint(body, rim, (170, 185, 230), pal["rim_small"])
    canvas.alpha_composite(body)
    return canvas, sq


def finish(img, n):
    return img.resize((n, n), Image.LANCZOS)


# ───────────────────────── a. Lattice ─────────────────────────
PAL_A = {
    "bg": [(0, rgb("#5B54F0")), (0.55, rgb("#5B3FE6")), (1, rgb("#6D28D9"))],
    "warp": [(0, rgb("#FFFFFF")), (1, rgb("#DCDCFB"))],
    "weft": [(0, rgb("#FDE68A")), (0.5, rgb("#FBBF24")), (1, rgb("#EA8A0C"))],
    "shadow": rgb("#1E1065"),
}


def lattice(N, small):
    canvas, sq = tile_bg(N, PAL_A, small)
    k = 3 if not small else 2
    side = N * (0.56 if not small else 0.62)           # 돌리기 전 정사각형 한 변
    pitch = side / k
    band = pitch * (0.70 if not small else 0.82)
    c = N / 2
    x0 = c - side / 2 + (pitch - band) / 2
    rad = band * (0.22 if not small else 0.12)

    def rot(m):
        return m.rotate(45, resample=Image.BICUBIC, center=(c, c))

    def rect(box):
        m = Image.new("L", (N, N), 0)
        ImageDraw.Draw(m).rounded_rectangle(box, radius=rad, fill=255)
        return m

    ovh = 0
    lo, hi = x0 - ovh, x0 + (k - 1) * pitch + band + ovh   # 실 끝을 바깥 실의 가장자리에 맞춘다
    H = [rot(rect([lo, x0 + i * pitch, hi, x0 + i * pitch + band])) for i in range(k)]
    V = [rot(rect([x0 + j * pitch, lo, x0 + j * pitch + band, hi])) for j in range(k)]
    warp = lin_grad(N, PAL_A["warp"], 120)
    weft = lin_grad(N, PAL_A["weft"], 120)
    shc = PAL_A["shadow"]

    allm = Image.new("L", (N, N), 0)
    for m in H + V:
        allm = ImageChops.lighter(allm, m)
    if not small:
        drop_shadow(canvas, allm, N * 0.022, N * 0.02, shc, 0.55)
    else:
        drop_shadow(canvas, allm, N * 0.03, N * 0.01, shc, 0.35)

    for m in H:
        paint(canvas, m, weft)
    if not small:
        for m in H:
            bevel(canvas, m, N * 0.006, N * 0.006, 0.45, 0.25)
    for j, mv in enumerate(V):
        if not small:
            sh = mul(drop_or(H), shift(mv, N * 0.004, N * 0.012).filter(ImageFilter.GaussianBlur(N * 0.012)))
            paint(canvas, sh, shc, 0.55)
        paint(canvas, mv, warp)
        if not small:
            bevel(canvas, mv, N * 0.006, N * 0.006, 0.6, 0.18, lo_col=shc)
    # 씨실이 위로 오는 교차점을 다시 그린다
    for i, mh in enumerate(H):
        for j, mv in enumerate(V):
            if (i + j) % 2 == 1:
                patch = mul(mh, mv)
                # 교차점 양옆으로 조금 더 넓혀야 씨실이 끊기지 않는다
                if not small:
                    sh = mul(mv, shift(patch, N * 0.004, N * 0.012).filter(ImageFilter.GaussianBlur(N * 0.012)))
                    paint(canvas, sh, shc, 0.6)
                paint(canvas, patch, weft)
                if not small:
                    bevel(canvas, patch, N * 0.006, N * 0.006, 0.45, 0.0)
    return canvas


def drop_or(ms):
    out = Image.new("L", ms[0].size, 0)
    for m in ms:
        out = ImageChops.lighter(out, m)
    return out


def _odd(v):
    v = max(3, round(v))
    return v if v % 2 else v + 1


# ───────────────────────── b. Twin-V W ─────────────────────────
PAL_B = {
    "bg": [(0, rgb("#14B8A6")), (0.45, rgb("#0F8C86")), (1, rgb("#0B5563"))],
    "glow": 0.14,
    "v1": [(0, rgb("#FFB4A2")), (0.5, rgb("#FB7A65")), (1, rgb("#E5533F"))],
    "v2": [(0, rgb("#FFFFFF")), (1, rgb("#FDECD8"))],
    "shadow": rgb("#06343D"),
}


def twin_w(N, small):
    canvas, sq = tile_bg(N, PAL_B, small)
    c = N / 2
    W = N * (0.70 if not small else 0.84)
    Ht = N * (0.50 if not small else 0.60)
    w = N * (0.115 if not small else 0.165)
    left, top = c - W / 2, c - Ht / 2 + N * (0.005 if not small else 0.0)
    bot = top + Ht

    def P(x, y):
        return (left + x * W, top + y * Ht)

    inset = w / W * 0.55   # 바깥 팔이 정사각 틀을 넘지 않게
    a1 = [P(inset, -0.25), P(0.25, 1 - w / Ht * 0.40), P(0.76, -0.25)]
    a2 = [P(0.24, -0.25), P(0.75, 1 - w / Ht * 0.40), P(1 - inset, -0.25)]

    def vmask(pts):
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        d.line(pts, fill=255, width=round(w), joint="curve")
        clip = Image.new("L", (N, N), 0)
        ImageDraw.Draw(clip).rectangle([0, top, N, N], fill=255)
        return mul(m, clip)

    m1, m2 = vmask(a2), vmask(a1)   # m1(크림)이 아래, m2(코럴)가 위
    # 가운데 교차: 크림 실(v2)이 코럴 실(v1) 위로. 오른쪽 아래 다리에서는 v1 이 v2 위로 다시 지나가게 하기 위해
    # 두 실이 겹치는 곳은 하나뿐이므로, 가운데 X만 v2 위.
    allm = ImageChops.lighter(m1, m2)
    shc = PAL_B["shadow"]
    drop_shadow(canvas, allm, N * (0.022 if not small else 0.03), N * (0.02 if not small else 0.01),
                shc, 0.55 if not small else 0.4)
    g1 = lin_grad(N, PAL_B["v2"], 100)
    g2 = lin_grad(N, PAL_B["v1"], 100)
    paint(canvas, m1, g1)
    if not small:
        bevel(canvas, m1, N * 0.007, N * 0.007, 0.6, 0.20, lo_col=shc)
    # v2 아래 그림자 + 틈
    gap = m2.filter(ImageFilter.MaxFilter(_odd(N * (0.022 if not small else 0.07))))
    if not small:
        sh = mul(m1, shift(m2, N * 0.004, N * 0.014).filter(ImageFilter.GaussianBlur(N * 0.014)))
        paint(canvas, sh, shc, 0.65)
        paint(canvas, mul(ImageChops.subtract(gap, m2), m1), g1.point(lambda v: round(v * 0.55)))
    else:
        paint(canvas, mul(ImageChops.subtract(gap, m2), m1), shc, 0.85)
    paint(canvas, m2, g2)
    if not small:
        bevel(canvas, m2, N * 0.007, N * 0.007, 0.35, 0.25)
    return canvas


# ───────────────────────── c. Knot ─────────────────────────
PAL_C = {
    "bg": [(0, rgb("#36446A")), (0.5, rgb("#1D2843")), (1, rgb("#111A30"))],
    "glow": 0.10,
    "rim_small": 0.22,
    "gold": [(0, rgb("#FFF1B8")), (0.35, rgb("#FCD34D")), (0.75, rgb("#F59E0B")), (1, rgb("#C2690A"))],
    "shadow": rgb("#05070F"),
}


def knot_path(cx, cy, R, steps=1440):
    pts = []
    for i in range(steps + 1):
        t = 2 * math.pi * i / steps
        x = math.sin(t) + 2 * math.sin(2 * t)
        y = math.cos(t) - 2 * math.cos(2 * t)
        pts.append((cx + x * R / 3.0, cy - y * R / 3.0 + R * 0.07))
    return pts


def knot_crossings(pts):
    """경로가 스스로 겹치는 곳(교차점) 3개를 찾는다: 경로상 멀리 떨어진 두 점 중 가장 가까운 쌍."""
    n = len(pts) - 1
    step = 4
    cand = []
    for i in range(0, n, step):
        for j in range(i + n // 8, n, step):
            if (n - j + i) < n // 8:
                continue
            cand.append((math.dist(pts[i], pts[j]), i, j))
    cand.sort()
    groups = []
    for dist, i, j in cand:
        if all(abs(g[0] - i) > n // 12 or abs(g[1] - j) > n // 12 for g in groups):
            groups.append((i, j))
        if len(groups) == 3:
            break
    # 각 교차점 근처에서 한 칸 단위로 다시 맞춘다
    out = []
    for i, j in groups:
        best = min(((math.dist(pts[a % n], pts[b % n]), a % n, b % n)
                    for a in range(i - step, i + step + 1) for b in range(j - step, j + step + 1)))
        out.append((best[1], best[2]))
    return out


def knot(N, small):
    canvas, sq = tile_bg(N, PAL_C, small)
    c = N / 2
    tiny = small and N <= 24 * SS_SMALL
    R = N * (0.335 if not small else 0.40 if not tiny else 0.43)
    w = N * (0.085 if not small else 0.105 if not tiny else 0.115)
    pts = knot_path(c, c, R)
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    dx, dy = c - (min(xs) + max(xs)) / 2, c - (min(ys) + max(ys)) / 2
    pts = [(x + dx, y + dy) for x, y in pts]
    n = len(pts) - 1
    cross = knot_crossings(pts)
    # 경로를 따라가며 만나는 교차점 순서대로 위/아래를 번갈아 정한다
    events = sorted([(i, k) for k, (a, b) in enumerate(cross) for i in (a, b)])
    overs = [i for idx, (i, k) in enumerate(events) if idx % 2 == 0]
    seg_len = math.dist(pts[0], pts[1])

    def stroke(m, a, b, width):
        d = ImageDraw.Draw(m)
        r = width / 2
        for k in range(a, b + 1):
            p = pts[k % n]
            d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=255)

    under_of = {}
    for a, b in cross:
        under_of[a if a in overs else b] = b if a in overs else a

    def build(width, gapw):
        """아래로 지나가는 실에서, 위로 지나가는 실 둘레(틈)만큼만 지운다. 다른 실은 건드리지 않는다."""
        m = Image.new("L", (N, N), 0)
        stroke(m, 0, n, width)
        h = round(gapw * 1.6 / seg_len)
        for i, j in under_of.items():
            over = Image.new("L", (N, N), 0)
            stroke(over, i - h * 2, i + h * 2, width)
            ring = Image.new("L", (N, N), 0)
            stroke(ring, i - h * 2, i + h * 2, gapw)
            under = Image.new("L", (N, N), 0)
            stroke(under, j - h, j + h, width)
            m = ImageChops.subtract(m, ImageChops.subtract(mul(under, ring), over))
        return m

    gapw = w * (1.7 if not small else 1.5 if not tiny else 1.35)
    m = build(w, gapw)
    shc = PAL_C["shadow"]
    if not small:
        # 매듭 뒤 은은한 금빛
        paint(canvas, mul(radial(N, c, c, R * 1.35), sq), rgb("#F59E0B"), 0.16)
        drop_shadow(canvas, m, N * 0.02, N * 0.018, shc, 0.7)
    gold = lin_grad(N, PAL_C["gold"], 120)
    paint(canvas, m, gold)
    if not small:
        bevel(canvas, m, N * 0.008, N * 0.009, 0.55, 0.40, lo_col=rgb("#5A2A00"))
        # 위로 지나가는 실이 아래 실에 드리우는 그림자
        for i in overs:
            o = Image.new("L", (N, N), 0)
            half = round(gapw * 1.6 / seg_len)
            stroke(o, i - half, i + half, w)
            o_long = Image.new("L", (N, N), 0)
            stroke(o_long, i - half * 3, i + half * 3, w * 1.05)
            sh = shift(o, N * 0.003, N * 0.012).filter(ImageFilter.GaussianBlur(N * 0.012))
            paint(canvas, mul(mul(sh, m), ImageChops.invert(o_long)), rgb("#3A1A00"), 0.55)
    return canvas


# ═════════════════════ Hushpad 시안 (현재) ═════════════════════
def rrect(N, box, r):
    m = Image.new("L", (N, N), 0)
    ImageDraw.Draw(m).rounded_rectangle([round(v) for v in box], radius=round(r), fill=255)
    return m


def page_with_fold(N, box, r, f):
    """오른쪽 위 모서리가 접힌 메모장. (종이 마스크, 접힌 삼각형 마스크)"""
    L, T, R, B = box
    page = rrect(N, box, r)
    cut = poly_mask(N, [(R - f, T - 2), (R + 2, T - 2), (R + 2, T + f)])
    page = ImageChops.subtract(page, cut)
    fold = poly_mask(N, [(R - f, T), (R, T + f), (R - f, T + f)])
    return page, fold


def fold_shadow(canvas, page, fold, N, col, op):
    sh = shift(fold, -N * 0.006, N * 0.012).filter(ImageFilter.GaussianBlur(N * 0.012))
    paint(canvas, mul(sh, ImageChops.subtract(page, fold)), col, op)


# ───────────── a. Shh Pad: 둥근 메모장 앞을 세로 막대 하나가 가로지른다(쉿) ─────────────
PAL_HA = {
    "bg": [(0, rgb("#33445F")), (0.5, rgb("#1F2B40")), (1, rgb("#121A2A"))],
    "glow": 0.12,
    "rim_small": 0.22,
    "page": [(0, rgb("#FFFFFF")), (1, rgb("#DCE6EE"))],
    "mint": [(0, rgb("#A7F3D9")), (0.5, rgb("#5EDDB8")), (1, rgb("#22A386"))],
    "shadow": rgb("#070C16"),
}


def shh_pad(N, small):
    canvas, sq = tile_bg(N, PAL_HA, small)
    c = N / 2
    if not small:
        pw, ph, cy, r = N * 0.46, N * 0.54, N * 0.535, N * 0.075
        bw, top_over, length = N * 0.115, N * 0.11, N * 0.42
    else:
        pw, ph, cy, r = N * 0.60, N * 0.66, N * 0.55, N * 0.10
        bw, top_over, length = N * 0.17, N * 0.12, N * 0.50
    box = [c - pw / 2, cy - ph / 2, c + pw / 2, cy + ph / 2]
    page = rrect(N, box, r)
    bar = rrect(N, [c - bw / 2, box[1] - top_over, c + bw / 2, box[1] - top_over + length], bw / 2)
    shc = PAL_HA["shadow"]
    drop_shadow(canvas, ImageChops.lighter(page, bar), N * (0.025 if not small else 0.03),
                N * (0.025 if not small else 0.012), shc, 0.6 if not small else 0.45)
    paint(canvas, page, lin_grad(N, PAL_HA["page"], 110))
    if not small:
        bevel(canvas, page, N * 0.006, N * 0.008, 0.7, 0.22, lo_col=rgb("#5B6B85"))
        sh = mul(page, shift(bar, N * 0.008, N * 0.02).filter(ImageFilter.GaussianBlur(N * 0.018)))
        paint(canvas, sh, rgb("#1F2B40"), 0.45)
    else:
        sh = mul(page, ImageChops.subtract(bar.filter(ImageFilter.MaxFilter(_odd(N * 0.07))), bar))
        paint(canvas, sh, rgb("#1F2B40"), 0.35)
    paint(canvas, bar, lin_grad(N, PAL_HA["mint"], 100))
    if not small:
        bevel(canvas, bar, N * 0.006, N * 0.008, 0.55, 0.25, lo_col=rgb("#0B4F43"))
    return canvas


def veil_pad(N, small):
    """메모장 아래 절반을 젖빛 유리(Windows 11 아크릴 느낌)가 덮는다 - 내용은 있지만 흐려서 안 보인다."""
    canvas, sq = tile_bg(N, PAL_HA, small)
    c = N / 2
    shc = PAL_HA["shadow"]
    mint = lin_grad(N, PAL_HA["mint"], 100)
    if not small:
        pw, ph, r = N * 0.44, N * 0.54, N * 0.065
        px, py = c - N * 0.055, c - N * 0.045
    else:
        pw, ph, r = N * 0.56, N * 0.64, N * 0.09
        px, py = c - N * 0.08, c - N * 0.07
    pbox = [px - pw / 2, py - ph / 2, px + pw / 2, py + ph / 2]
    page = rrect(N, pbox, r)
    drop_shadow(canvas, page, N * (0.022 if not small else 0.03), N * (0.022 if not small else 0.012),
                shc, 0.55 if not small else 0.45)
    paint(canvas, page, lin_grad(N, PAL_HA["page"], 110))
    if not small:
        bevel(canvas, page, N * 0.006, N * 0.008, 0.7, 0.2, lo_col=rgb("#5B6B85"))
        # 메모 내용(굵은 덩어리 몇 개) - 유리 밑에서 흐려진다
        L, T = pbox[0] + pw * 0.15, pbox[1] + ph * 0.14
        blocks = [(0, 0, 0.55, 0.10, "mint"), (0, 0.24, 0.70, 0.08, "ink"), (0, 0.42, 0.70, 0.30, "ink")]
        for bx, by, bw_, bh, kind in blocks:
            m = rrect(N, [L + bx * pw, T + by * ph, L + (bx + bw_) * pw, T + by * ph + bh * ph], bh * ph / 2)
            paint(canvas, m, mint if kind == "mint" else rgb("#9AA8BC"))
    else:
        L, T = pbox[0] + pw * 0.18, pbox[1] + ph * 0.18
        m = rrect(N, [L, T, L + pw * 0.50, T + ph * 0.14], ph * 0.07)
        paint(canvas, m, mint)
    # 젖빛 유리 판
    if not small:
        gw, gh, gr = N * 0.50, N * 0.38, N * 0.07
        gx, gy = c + N * 0.06, c + N * 0.135
    else:
        gw, gh, gr = N * 0.62, N * 0.46, N * 0.10
        gx, gy = c + N * 0.08, c + N * 0.17
    gbox = [gx - gw / 2, gy - gh / 2, gx + gw / 2, gy + gh / 2]
    glass = rrect(N, gbox, gr)
    drop_shadow(canvas, glass, N * (0.02 if not small else 0.025), N * (0.03 if not small else 0.015),
                shc, 0.45 if not small else 0.35)
    if not small:
        blurred = canvas.filter(ImageFilter.GaussianBlur(N * 0.03))
        layer = blurred.copy()
        layer.putalpha(glass)
        canvas.alpha_composite(layer)
        paint(canvas, glass, rgb("#EAFBF5"), 0.60)
        paint(canvas, mul(glass, lin_grad(N, [(0, (255,) * 3), (0.6, (0,) * 3)], 120).convert("L")),
              (255, 255, 255), 0.30)
        paint(canvas, glass, rgb("#5EDDB8"), 0.18)
        bevel(canvas, glass, N * 0.005, N * 0.004, 0.85, 0.15)
        # 유리 가장자리 얇은 빛
        rim = ImageChops.subtract(glass, glass.filter(ImageFilter.MinFilter(_odd(N * 0.006))))
        paint(canvas, rim, (255, 255, 255), 0.45)
    else:
        paint(canvas, glass, rgb("#B5F2DE"), 0.80)
        rim = ImageChops.subtract(glass, glass.filter(ImageFilter.MinFilter(_odd(N * 0.06))))
        paint(canvas, rim, (255, 255, 255), 0.7)
    return canvas


# ───────────── b. Fade Page: 왼쪽부터 조각으로 흩어져 사라지는 메모장(캡처에 안 보임) ─────────────
PAL_HB = {
    "bg": [(0, rgb("#6A3A86")), (0.5, rgb("#4A2366")), (1, rgb("#2C1342"))],
    "glow": 0.13,
    "page": [(0, rgb("#FFF4EC")), (1, rgb("#FFD9C2"))],
    "fold": [(0, rgb("#FFB38A")), (1, rgb("#F08A63"))],
    "shadow": rgb("#16081F"),
}


def fade_page(N, small):
    canvas, sq = tile_bg(N, PAL_HB, small)
    c = N / 2
    if not small:
        pw, ph, r, f = N * 0.42, N * 0.54, N * 0.055, N * 0.13
        cx = c + N * 0.115
    else:
        pw, ph, r, f = N * 0.50, N * 0.66, N * 0.08, N * 0.20
        cx = c + N * 0.10
    box = [cx - pw / 2, c - ph / 2, cx + pw / 2, c + ph / 2]
    page, fold = page_with_fold(N, box, r, f)
    pix = []
    rows = 5 if not small else 3
    cols = 3 if not small else 2
    cell = ph / rows
    for col in range(cols):
        size = cell * ([0.78, 0.58, 0.40][col] if not small else [0.80, 0.55][col])
        alpha = [0.85, 0.55, 0.30][col] if not small else [0.85, 0.5][col]
        step = cell * (0.80 if not small else 1.0)
        x = box[0] - step * (col + 0.5) - (N * 0.012 if not small else N * 0.035)
        for row in range(rows):
            if (row + col) % 2:
                continue
            y = box[1] + cell * (row + 0.5)
            m = rrect(N, [x - size / 2, y - size / 2, x + size / 2, y + size / 2], size * 0.22)
            pix.append((m, alpha))
    shc = PAL_HB["shadow"]
    drop_shadow(canvas, page, N * (0.025 if not small else 0.03), N * (0.025 if not small else 0.012),
                shc, 0.6 if not small else 0.45)
    pg = lin_grad(N, PAL_HB["page"], 110)
    for m, a in pix:
        paint(canvas, m, pg, a)
    paint(canvas, page, pg)
    if not small:
        bevel(canvas, page, N * 0.006, N * 0.008, 0.6, 0.2, lo_col=rgb("#9A5A55"))
        edge = mul(page, lin_grad(N, [(0, (255,) * 3), (0.42, (0,) * 3)], 0).convert("L"))
        paint(canvas, edge, rgb("#4A2366"), 0.30)
    fold_shadow(canvas, page, fold, N, shc, 0.45 if not small else 0.3)
    paint(canvas, fold, lin_grad(N, PAL_HB["fold"], 135))
    if not small:
        bevel(canvas, fold, N * 0.004, N * 0.005, 0.5, 0.15)
    return canvas


# ───────────── c. H Page: 위·아래가 파여 H 모양이 된 메모장(머리글자 H + 메모) ─────────────
PAL_HC = {
    "bg": [(0, rgb("#6366F1")), (0.5, rgb("#4F46E5")), (1, rgb("#3B2FB0"))],
    "glow": 0.14,
    "page": [(0, rgb("#FFFFFF")), (1, rgb("#E4E1FB"))],
    "fold": [(0, rgb("#C9BEFF")), (1, rgb("#9F8CF5"))],
    "shadow": rgb("#170F55"),
}


def h_page(N, small):
    canvas, sq = tile_bg(N, PAL_HC, small)
    c = N / 2
    if not small:
        pw, ph, r, f = N * 0.54, N * 0.58, N * 0.07, N * 0.13
        nw, nd = N * 0.13, N * 0.165
    else:
        pw, ph, r, f = N * 0.70, N * 0.72, N * 0.09, N * 0.20
        nw, nd = N * 0.17, N * 0.21
    box = [c - pw / 2, c - ph / 2, c + pw / 2, c + ph / 2]
    page, fold = page_with_fold(N, box, r, f)
    nr = nw / 2
    for y0, y1 in ((box[1] - nr * 2, box[1] + nd), (box[3] - nd, box[3] + nr * 2)):
        page = ImageChops.subtract(page, rrect(N, [c - nw / 2, y0, c + nw / 2, y1], nr))
    shc = PAL_HC["shadow"]
    drop_shadow(canvas, page, N * (0.025 if not small else 0.03), N * (0.025 if not small else 0.012),
                shc, 0.55 if not small else 0.45)
    paint(canvas, page, lin_grad(N, PAL_HC["page"], 110))
    if not small:
        bevel(canvas, page, N * 0.006, N * 0.008, 0.7, 0.22, lo_col=rgb("#5A50B8"))
    fold_shadow(canvas, page, fold, N, shc, 0.5 if not small else 0.3)
    paint(canvas, fold, lin_grad(N, PAL_HC["fold"], 135))
    if not small:
        bevel(canvas, fold, N * 0.004, N * 0.005, 0.5, 0.15)
    return canvas


# ───────────────────────── 출력 ─────────────────────────
CONCEPTS = [
    ("a", "Veil Pad", "note under frosted glass · ink + mint", veil_pad),
    ("b", "Fade Page", "page dissolving out of sight · plum + peach", fade_page),
    ("c", "H Page", "H-shaped folded note · indigo + lilac", h_page),
]
# OmniWeave 때의 시안(lattice / twin_w / knot) 함수는 참고용으로 남겨 둔다.


def render(fn):
    big = fn(SS_BIG, False).resize((1024, 1024), Image.LANCZOS)
    frames = {}
    for n in SIZES:
        if n <= SMALL_MAX:
            frames[n] = fn(n * SS_SMALL, True).resize((n, n), Image.LANCZOS)
        else:
            frames[n] = big.resize((n, n), Image.LANCZOS)
    return big, frames


def write_ico(path, images):
    blobs = []
    for im in images:
        b = io.BytesIO()
        im.save(b, "PNG")
        blobs.append((im.size[0], b.getvalue()))
    head = struct.pack("<HHH", 0, 1, len(blobs))
    off = 6 + 16 * len(blobs)
    entries, data = b"", b""
    for n, png in blobs:
        entries += struct.pack("<BBBBHHII", n % 256, n % 256, 0, 0, 1, 32, len(png), off + len(data))
        data += png
    path.write_bytes(head + entries + data)


def font(sz, bold=False):
    for f in (["C:/Windows/Fonts/segoeuib.ttf"] if bold else []) + ["C:/Windows/Fonts/segoeui.ttf"]:
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return ImageFont.load_default()


def preview(results):
    gap = 18
    order = [256] + sorted([n for n in SIZES if n != 256], reverse=True)
    panel_w = sum(order) + gap * (len(order) + 1)
    label_w = 300
    row_h = 256 + 2 * gap
    W = label_w + panel_w * 2
    H = row_h * len(results)
    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(img)
    for r, (key, name, desc, frames) in enumerate(results):
        y0 = r * row_h
        d.rectangle([0, y0, label_w, y0 + row_h], fill=(250, 250, 250))
        d.text((24, y0 + 70), key.upper(), font=font(64, True), fill=(30, 30, 30))
        d.text((24, y0 + 150), name, font=font(26, True), fill=(30, 30, 30))
        d.text((24, y0 + 186), desc, font=font(14), fill=(90, 90, 90))
        for p, bgc in enumerate([(243, 243, 243), (32, 32, 32)]):
            x = label_w + p * panel_w
            d.rectangle([x, y0, x + panel_w, y0 + row_h - 1], fill=bgc)
            x += gap
            for n in order:
                fr = frames[n]
                yy = y0 + gap + (256 - n) // 2 if n == 256 else y0 + gap + 256 - n - 20
                img.alpha_composite(fr, (x, yy))
                if n != 256:
                    d.text((x + n // 2, y0 + row_h - gap - 8), str(n), font=font(11),
                           fill=(120, 120, 120) if p == 0 else (160, 160, 160), anchor="mm")
                x += n + gap
        d.line([0, y0 + row_h - 1, W, y0 + row_h - 1], fill=(200, 200, 200))
    img.convert("RGB").save(OUT / "preview.png")


def main():
    OUT.mkdir(exist_ok=True)
    results = []
    for key, name, desc, fn in CONCEPTS:
        big, frames = render(fn)
        big.save(OUT / f"{key}_1024.png")
        write_ico(OUT / f"{key}.ico", [frames[n] for n in SIZES])
        results.append((key, name, desc, frames))
        print("ok", key, name)
    preview(results)
    print("ok", OUT / "preview.png")


if __name__ == "__main__":
    main()
