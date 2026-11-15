"""Hushpad SNS card generator (Pillow).

Outputs (marketing/cards/, English in cards/en/):
  card_01..09.png   1080x1350  carousel: cover + 7 pillars + CTA
  square_cover.png  1080x1080  feed / profile-grid cover
  link_card.png     1200x630   OG / link preview (blog, X, GeekNews…)
  story_cover.png   1080x1920  Story / Reels / Shorts cover (text inside 250px safe area)

Usage:
  python marketing/make_cards.py            # ko + en
  python marketing/make_cards.py --lang ko  # one language

App screenshots come from marketing/shots/*.png (rendered from a disposable test profile by
marketing/shots/render_shots.py — never from real notes). Every text block is measured; anything
that would overflow its box is reported as WARN at the end (and the run exits 1).
"""
from __future__ import annotations

import argparse
import math
import os
import sys

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOTS = os.path.join(HERE, "shots")   # Korean UI shots; English UI shots in shots/en (see build())
ICON = os.path.join(ROOT, "assets", "app_1024.png")
FONTS = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

# ───────── brand ─────────
PLUM, PLUM2 = (122, 60, 147), (155, 77, 181)
PEACH, PEACH_D = (255, 179, 138), (224, 112, 63)
INK, SOFT = (28, 26, 31), (245, 244, 247)
WHITE = (255, 255, 255)
MUTED = (98, 92, 106)
LINE = (226, 222, 232)
URL = "gdra.mycafe24.com/hushpad"

WARN: list[str] = []

# ───────── fonts ─────────
_FONT_FILES = {
    "ko": ("malgun.ttf", "malgunbd.ttf"),
    "en": ("segoeui.ttf", "segoeuib.ttf"),
    "ja": ("YuGothM.ttc", "YuGothB.ttc"),
    "zh": ("msyh.ttc", "msyhbd.ttc"),
    "mono": ("consola.ttf", "consolab.ttf"),
}
_cache: dict = {}


def F(size: int, bold: bool = False, script: str = "ko") -> ImageFont.FreeTypeFont:
    key = (size, bold, script)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(os.path.join(FONTS, _FONT_FILES[script][1 if bold else 0]), size)
    return _cache[key]


# ───────── copy ─────────
T = {
    "ko": {
        "brand_sub": "허시패드",
        "tagline": "조용히 적고, 아무도 못 보게",
        "foot": "지금 받기 · " + URL,
        "c1_kicker": "메모장 탭에 암호·API 키 적어 두셨죠?",
        "c1_title": "조용히 적고,\n아무도 못 보게",
        "c1_sub": "쓰는 대로 저장되고, 파일은 전부 암호화됩니다.\n화면을 공유해도 이 창은 상대에게 안 보여요.",
        "pills": ["저장 버튼 없음", "AES-256-GCM", "캡처에 안 보임"],
        "cards": [
            ("01 · 자동 저장", "저장 버튼이\n없어요", "쓰는 동안 알아서 저장됩니다. 제목이 없어도\n만든 시각으로 구분되고, 모두 한 폴더에 모여요."),
            ("02 · 암호화", "모든 메모를\n암호화해요", "파일은 AES-256-GCM으로 잠겨 있어요.\n클라우드에 올라가도 내용은 읽히지 않습니다."),
            ("03 · 대표 기능", "캡처에\n안 보이는 창", "화상회의에서 화면을 공유해도\n상대에게는 Hushpad 창이 보이지 않습니다."),
            ("04 · 복사", "서식 그대로,\n또는 글자만", "웹에서 복사한 표와 글꼴은 그대로 남고,\nCtrl+Shift+C로 복사하면 글자만 나갑니다."),
            ("05 · 코드 메모", "HTML·JSON\n급할 때", "줄 번호가 붙고, 엉킨 JSON은 단축키로 정리돼요.\nAPI_KEY=… 줄에서는 값만 골라 복사할 수 있습니다."),
            ("06 · 캡처", "스크린샷·녹화가\n바로 메모로", "Ctrl+Alt+S로 찍은 화면은 열린 메모에 바로 들어가요.\n짧은 화면 녹화는 Ctrl+Alt+R."),
            ("07 · 클립보드", "Ctrl+Alt+M\n클립보드를 메모로", "방금 복사한 글이나 이미지가 새 메모로 저장됩니다.\n창은 뜨지 않아요."),
        ],
        # card visuals
        "files_title": "보관 폴더 한 곳",
        "files_note": "메모 1개 = 파일 1개 · 만든 시각이 이름",
        "cipher_cmd": "> type notes\\20261115-091200-a1b2.own",
        "cipher_note": "# 열어 봐도 이렇게만 보여요",
        "veil": "비밀 메모는 열 때마다 가려져요",
        "crypto_chips": ["AES-256-GCM", "scrypt 열쇠", "Windows 계정에 묶음"],
        "mon_a": "내 모니터", "mon_b": "스크린샷 · 화면 공유",
        "mon_gone": "창 자리엔 뒤 화면이 찍혀요",
        "cap_points": ["창을 치우지 않고 그대로 캡처해도 돼요", "일부러 보여 줄 때는 메뉴에서 끄면 됩니다"],
        "copy_a": ("Ctrl+C", "서식 그대로"), "copy_b": ("Ctrl+Shift+C", "글자만"),
        "plain_lines": ["출장 준비 체크리스트", "11월 20일(목) 부산 · KTX 07:30", "노트북 충전기 · 발표 자료 최종본"],
        "rich_bullet": ("• 노트북 충전기 · ", "발표 자료 최종본"),
        "value_menu": "이 줄 값만 복사",
        "value_got": "복사됨: sk-test-51Hq9ZtE…",
        "json_btn": "JSON 정리  Ctrl+Alt+J",
        "rec_bar": "녹화 중 00:12",
        "rec_note": "빨간 테두리와 일시정지·정지 막대는\n내 화면에만 보이고, 녹화 영상엔\n찍히지 않아요",
        "keys_s": "영역 스크린샷", "keys_r": "화면 녹화 (최대 3분)",
        "clip_src": "어디서든 복사", "clip_toast_t": "Hushpad", "clip_toast": "클립보드를 메모로 저장했어요 (23자)",
        "clip_item": ("복사해 둔 문구", "방금"),
        "clip_text": ("“배송은 영업일 기준", "2~3일 걸립니다.”"),
        "clip_note": "창을 닫아도 트레이에서 동작해요",
        # CTA
        "cta_kicker": "무료 · 오픈소스",
        "cta_title": "조용히 적고,\n아무도 못 보게",
        "cta_rows": [("Windows·macOS", "Windows 10·11, Apple Silicon Mac"),
                     ("설치 없이", "압축 풀고 바로 실행하는 포터블 앱"),
                     ("계정·서버 없음", "인터넷 연결 없이 동작"),
                     ("4개 언어 지원", None)],
        "cta_btn": "지금 받기",
        "langs": [("한국어", "ko"), ("English", "en"), ("日本語", "ja"), ("简体中文", "zh")],
        "link_sub": "저장 버튼 없이 쓰고 전부 암호화되는 메모장.\n화면을 공유해도 창이 보이지 않아요.",
        "story_kicker": "쉿.",
        "story_hint": "넘겨서 보기 →",
    },
    "en": {
        "brand_sub": "허시패드",
        "tagline": "Write quietly. Seen by no one.",
        "foot": "Get it free · " + URL,
        "c1_kicker": "Passwords and API keys in Notepad tabs?",
        "c1_title": "Write quietly.\nSeen by no one.",
        "c1_sub": "It saves as you type and encrypts every file.\nShare your screen, and the window just isn't there.",
        "pills": ["No save button", "AES-256-GCM", "Invisible to capture"],
        "cards": [
            ("01 · Auto-save", "There's no\nsave button", "Saved as you type. Untitled notes are sorted\nby when you made them, all in one folder."),
            ("02 · Encryption", "Every note\nis encrypted", "Files are sealed with AES-256-GCM. Your cloud\nsync can copy them. It can't read them."),
            ("03 · Key feature","Invisible to\nscreen capture", "Share your screen on a call and the Hushpad\nwindow doesn't show up for anyone else."),
            ("04 · Copy", "Keep the format,\nor just the text", "Pasted formatting stays as it is.\nCtrl+Shift+C copies plain text only."),
            ("05 · Code notes", "HTML & JSON\nin a hurry", "Line numbers, and one shortcut to tidy messy JSON.\nRight-click API_KEY=… to copy just the value."),
            ("06 · Capture", "Screenshots and clips\nland in a note", "Ctrl+Alt+S grabs an area, Ctrl+Alt+R records.\nThe recording frame never shows in the video."),
            ("07 · Clipboard", "Ctrl+Alt+M\nclipboard → note", "Whatever you just copied becomes a new note.\nNo window pops up."),
        ],
        "files_title": "One vault folder",
        "files_note": "one note = one file · named by creation time",
        "cipher_cmd": "> type notes\\20261115-091200-a1b2.own",
        "cipher_note": "# this is all anyone else sees",
        "veil": "Secret notes stay veiled until you click",
        "crypto_chips": ["AES-256-GCM", "scrypt key", "per-Windows-user key"],
        "mon_a": "Your monitor", "mon_b": "Screenshot · screen share",
        "mon_gone": "window area shows what's behind",
        "cap_points": ["Capture without moving the window first", "Turn it off in one click when you do want to share"],
        "copy_a": ("Ctrl+C", "with formatting"), "copy_b": ("Ctrl+Shift+C", "plain text"),
        "plain_lines": ["Business trip checklist", "Thu, Nov 20 Busan · KTX 07:30", "Laptop charger · final slide deck"],
        "rich_bullet": ("• Laptop charger · ", "final slide deck"),
        "value_menu": "Copy only this line's value",
        "value_got": "Copied: sk-test-51Hq9ZtE…",
        "json_btn": "Tidy JSON  Ctrl+Alt+J",
        "rec_bar": "REC 00:12",
        "rec_note": "The red frame and pause/stop bar\nshow only on your screen,\nnever in the recording",
        "keys_s": "area screenshot", "keys_r": "screen recording\n(up to 3 min)",
        "clip_src": "Copy anywhere", "clip_toast_t": "Hushpad", "clip_toast": "Saved the clipboard as a note\n(35 characters)",
        "clip_item": ("Copied text", "just now"),
        "clip_text": ("“Delivery takes", "2–3 business days.”"),
        "clip_note": "Works with the window\nclosed (from the tray)",
        "cta_kicker": "Free · open source",
        "cta_title": "Write quietly.\nSeen by no one.",
        "cta_rows": [("Windows & Mac", "Windows 10/11, Apple silicon Macs"),
                     ("No installer", "portable: unzip and run"),
                     ("No account, no server", "works fully offline"),
                     ("4 UI languages", None)],
        "cta_btn": "Get it free",
        "langs": [("한국어", "ko"), ("English", "en"), ("日本語", "ja"), ("简体中文", "zh")],
        "link_sub": "No save button, every file encrypted,\nand hidden when you share your screen.",
        "story_kicker": "Shh.",
        "story_hint": "Swipe →",
    },
}

# ───────── drawing helpers ─────────


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient(w, h, c1, c2, angle=35):
    """Linear gradient at `angle` degrees (fast: draw a 1-D ramp and rotate/resize)."""
    big = int(math.hypot(w, h)) + 4
    ramp = Image.new("RGB", (big, 1))
    for x in range(big):
        ramp.putpixel((x, 0), lerp(c1, c2, x / (big - 1)))
    ramp = ramp.resize((big, big)).rotate(-angle, resample=Image.BICUBIC)
    l, t = (big - w) // 2, (big - h) // 2
    return ramp.crop((l, t, l + w, t + h))


def glow(img, xy, r, color, alpha=90):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    d.ellipse([x - r, y - r, x + r, y + r], fill=color + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.55))
    img.alpha_composite(layer)


def rounded(im: Image.Image, r: int) -> Image.Image:
    im = im.convert("RGBA")
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], r, fill=255)
    im.putalpha(ImageChops.multiply(im.getchannel("A"), m))
    return im


def shadow_paste(base: Image.Image, im: Image.Image, xy, r=18, blur=28, off=(0, 16), alpha=70, border=None):
    x, y = xy
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x + off[0], y + off[1], x + off[0] + im.width, y + off[1] + im.height], r,
                                         fill=(30, 10, 40, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    im = rounded(im, r)
    base.alpha_composite(im, (x, y))
    if border:
        ImageDraw.Draw(base).rounded_rectangle([x, y, x + im.width - 1, y + im.height - 1], r, outline=border, width=2)


def shot(name, box=None, width=None):
    im = Image.open(os.path.join(SHOTS_DIR, name + ".png")).convert("RGBA")
    if box:
        im = im.crop(box)
    if width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    return im


def tw(font, s):
    return font.getlength(s)


def text_block(d, xy, s, font, fill, spacing=1.28, max_w=None, anchor_right=False, label=""):
    """Draw multi-line text; returns bottom y. Warns if a line is wider than max_w."""
    x, y = xy
    asc, desc = font.getmetrics()
    lh = round(font.size * spacing)
    for line in s.split("\n"):
        w = tw(font, line)
        if max_w and w > max_w + 0.5:
            WARN.append(f"{label}: '{line}' {w:.0f}px > {max_w}px")
        d.text((x - w if anchor_right else x, y), line, font=font, fill=fill)
        y += lh
    return y - lh + asc + desc


def pill(d, xy, s, font, fg, bg, pad=(22, 10), outline=None):
    x, y = xy
    w = tw(font, s)
    asc, desc = font.getmetrics()
    h = asc + desc
    d.rounded_rectangle([x, y, x + w + pad[0] * 2, y + h + pad[1] * 2], (h + pad[1] * 2) // 2, fill=bg,
                        outline=outline, width=2 if outline else 0)
    d.text((x + pad[0], y + pad[1]), s, font=font, fill=fg)
    return x + w + pad[0] * 2


def keycap(d, xy, s, font, dark=False):
    x, y = xy
    w = tw(font, s)
    asc, desc = font.getmetrics()
    h = asc + desc + 18
    bg, edge, fg = ((52, 46, 60), (24, 20, 28), WHITE) if dark else (WHITE, (205, 198, 214), INK)
    d.rounded_rectangle([x, y + 5, x + w + 32, y + h + 5], 12, fill=edge)
    d.rounded_rectangle([x, y, x + w + 32, y + h], 12, fill=bg, outline=edge, width=2)
    d.text((x + 16, y + 9), s, font=font, fill=fg)
    return x + w + 32


def keys(d, xy, combo, font, dark=False, gap=12):
    x, y = xy
    plus = F(font.size, False, "en")
    for i, k in enumerate(combo.split("+")):
        if i:
            d.text((x + gap, y + 8), "+", font=plus, fill=(200, 190, 210) if dark else MUTED)
            x += gap * 2 + tw(plus, "+")
        x = keycap(d, (x, y), k, font, dark)
    return x


def icon(size):
    return Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)


def mixed(d, xy, runs, size, fill, bold=False):
    """Draw [(text, script)] runs on one baseline; returns end x."""
    x, y = xy
    base = y + F(size, bold, runs[0][1]).getmetrics()[0]   # shared baseline
    for s, sc in runs:
        f = F(size, bold, sc)
        d.text((x, base), s, font=f, fill=fill, anchor="ls")
        x += tw(f, s)
    return x


# ───────── frame (shared layout grid) ─────────
W, H = 1080, 1350
M = 84            # side margin
COLW = W - 2 * M  # 912


class Card:
    def __init__(self, lang, w=W, h=H, dark=False, plum=False):
        self.lang, self.w, self.h = lang, w, h
        self.t = T[lang]
        self.sc = "ko" if lang == "ko" else "en"
        if plum:
            self.im = gradient(w, h, PLUM, PLUM2, 30).convert("RGBA")
            glow(self.im, (int(w * 0.92), int(h * 0.08)), int(w * 0.38), PEACH, 70)
            glow(self.im, (int(w * 0.05), int(h * 0.95)), int(w * 0.45), (60, 20, 80), 120)
        elif dark:
            self.im = Image.new("RGBA", (w, h), INK + (255,))
            glow(self.im, (int(w * 0.85), int(h * 0.1)), int(w * 0.4), PLUM2, 60)
        else:
            self.im = Image.new("RGBA", (w, h), SOFT + (255,))
            glow(self.im, (int(w * 0.95), int(h * 0.02)), int(w * 0.36), PLUM2, 26)
        self.dark = dark or plum
        self.fg = WHITE if self.dark else INK
        self.mut = (226, 212, 236) if plum else ((178, 170, 188) if dark else MUTED)
        self.d = ImageDraw.Draw(self.im)

    def f(self, size, bold=False):
        return F(size, bold, self.sc)

    def header(self, page=None, total=9):
        d = self.d
        self.im.alpha_composite(icon(52), (M, 66))
        d.text((M + 68, 70), "Hushpad", font=F(30, True, "en"), fill=self.fg)
        if page:
            s = f"{page:02d} / {total:02d}"
            f = F(24, False, "en")
            d.text((self.w - M - tw(f, s), 78), s, font=f, fill=self.mut)

    def footer(self):
        d = self.d
        f = self.f(24)
        y = self.h - 92
        d.line([M, y - 28, self.w - M, y - 28], fill=(255, 255, 255, 60) if self.dark else LINE, width=2)
        d.text((M, y), self.t["tagline"], font=self.f(24, True), fill=self.fg)
        s = self.t["foot"]
        d.text((self.w - M - tw(f, s), y), s, font=f, fill=self.mut)

    def titleblock(self, kicker, title, sub, y=162, tsize=78):
        d = self.d
        kf = self.f(28, True)
        pill(d, (M, y), kicker, kf, PEACH_D if not self.dark else INK, (255, 232, 219) if not self.dark else PEACH)
        y += 92
        y = text_block(d, (M, y), title, self.f(tsize, True), self.fg, 1.2, COLW, label=f"{self.lang} title") + 30
        y = text_block(d, (M, y), sub, self.f(32), self.mut, 1.5, COLW, label=f"{self.lang} sub")
        return y

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.im.convert("RGB").save(path, optimize=True)


# ───────── visuals per card ─────────
VIS_TOP = 640      # visuals live between VIS_TOP and VIS_BOT
VIS_BOT = 1210


def vis_files(c: Card):
    """① list panel (real) + vault folder."""
    side = shot("rich_light", (0, 560, 300, 750), 420)           # note list with times
    side2 = shot("rich_light", (0, 56, 300, 300), 420)           # library header
    panel = Image.new("RGBA", (420, side2.height + side.height), WHITE)
    panel.alpha_composite(side2, (0, 0))
    panel.alpha_composite(side, (0, side2.height))
    panel = panel.resize((380, round(panel.height * 380 / 420)), Image.LANCZOS)
    shadow_paste(c.im, panel, (M, VIS_TOP + 10), border=LINE)
    # folder tree card
    x0, y0, w = M + 420, VIS_TOP + 40, COLW - 420
    box = Image.new("RGBA", (w, 470), (255, 255, 255, 255))
    shadow_paste(c.im, box, (x0, y0), border=LINE)
    d = c.d
    d.text((x0 + 32, y0 + 30), c.t["files_title"], font=c.f(30, True), fill=INK)
    mono = F(22, False, "mono")
    rows = [("Documents\\Hushpad\\", 0, INK), ("notes\\", 1, PLUM),
            ("20261115-091200-a1b2.own", 2, MUTED), ("20261115-110512-9c0e.own", 2, MUTED),
            ("20261115-132640-77fd.own", 2, MUTED), ("20261115-143205-e41a.own", 2, PEACH_D),
            ("history\\", 1, PLUM), ("media\\", 1, PLUM)]
    y = y0 + 96
    for s, lvl, col in rows:
        d.text((x0 + 32 + lvl * 26, y), ("└ " if lvl else "") + s, font=mono, fill=col)
        y += 38
    text_block(d, (x0 + 32, y0 + 420), c.t["files_note"], c.f(20), MUTED, max_w=w - 48, label="files_note")


def vis_crypto(c: Card):
    d = c.d
    x0, y0 = M, VIS_TOP + 6
    term = Image.new("RGBA", (COLW, 250), (22, 19, 26, 255))
    shadow_paste(c.im, term, (x0, y0))
    mono = F(26, False, "mono")
    d.text((x0 + 34, y0 + 32), c.t["cipher_cmd"], font=mono, fill=(200, 192, 210))
    d.text((x0 + 34, y0 + 88), "OWN1 Ÿ¤q9Æ¸0ÿ¡Zr#Ðk·ýR4æ»wQ%", font=F(28, False, "mono"), fill=PEACH)
    d.text((x0 + 34, y0 + 136), "ñ3¬Õ~x8ÁþM@j¦ÏbT1ô¿çE}Lv7¥ºgW", font=F(28, False, "mono"), fill=(170, 130, 190))
    d.text((x0 + 34, y0 + 192), c.t["cipher_note"], font=c.f(24) if c.lang == "ko" else F(24, False, "mono"),
           fill=(140, 132, 150))
    # secret veil (real crop)
    tab, mid = shot("secret_light", (500, 60, 1000, 100)), shot("secret_light", (500, 380, 1000, 476))
    veil = Image.new("RGBA", (500, tab.height + mid.height), WHITE)
    veil.alpha_composite(tab, (0, 0))
    veil.alpha_composite(mid, (0, tab.height))
    veil = veil.resize((560, round(veil.height * 560 / 500)), Image.LANCZOS)
    y1 = y0 + 290
    shadow_paste(c.im, veil, (x0, y1), border=LINE)
    d.text((x0, y1 + veil.height + 18), c.t["veil"], font=c.f(22), fill=MUTED)
    cx = x0 + 600
    y = y1 + 6
    for s in c.t["crypto_chips"]:
        ex = pill(d, (cx, y), s, c.f(24, True), PLUM, (238, 226, 245))
        if ex > W - M:
            WARN.append(f"{c.lang} crypto chip overflow: {s} {ex}")
        y += 78


def desktop(c: Card, w, h, with_window: bool):
    """A plain desktop: wallpaper + a generic doc window behind, Hushpad window on top (or not)."""
    im = gradient(w, h, (232, 222, 240), (255, 222, 204), 20).convert("RGBA")
    d = ImageDraw.Draw(im)
    # generic background window (spreadsheet-like)
    bx, by, bw, bh = 18, 22, w - 70, h - 60
    d.rounded_rectangle([bx, by, bx + bw, by + bh], 10, fill=WHITE, outline=(214, 206, 222))
    d.rectangle([bx, by, bx + bw, by + 26], fill=(236, 233, 240))
    for i in range(3):
        d.ellipse([bx + 10 + i * 16, by + 9, bx + 19 + i * 16, by + 18], fill=(205, 198, 212))
    for r in range(9):
        yy = by + 46 + r * 22
        d.rounded_rectangle([bx + 18, yy, bx + 18 + (bw - 60) * (0.9 if r % 3 else 0.55), yy + 9], 4,
                            fill=(226, 222, 232))
    if with_window:
        win = shot("rich_dark", None, int(w * 0.62))
        win = rounded(win, 8)
        sx, sy = w - win.width - 14, h - win.height - 34
        sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(sh).rounded_rectangle([sx, sy + 8, sx + win.width, sy + win.height + 8], 8, fill=(20, 0, 30, 90))
        im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
        im.alpha_composite(win, (sx, sy))
        return im, (sx, sy, win.width, win.height)
    return im, None


def vis_capture(c: Card):
    d = c.d
    pw, ph = (COLW - 36) // 2, 300
    y0 = VIS_TOP + 20
    a, rect = desktop(c, pw, ph, True)
    b, _ = desktop(c, pw, ph, False)
    sx, sy, ww, wh = rect
    db = ImageDraw.Draw(b)
    for i in range(0, ww, 14):     # dashed outline where the window would be
        db.line([sx + i, sy, sx + min(i + 7, ww), sy], fill=PEACH_D, width=2)
        db.line([sx + i, sy + wh, sx + min(i + 7, ww), sy + wh], fill=PEACH_D, width=2)
    for j in range(0, wh, 14):
        db.line([sx, sy + j, sx, sy + min(j + 7, wh)], fill=PEACH_D, width=2)
        db.line([sx + ww, sy + j, sx + ww, sy + min(j + 7, wh)], fill=PEACH_D, width=2)
    for k, (img, lab) in enumerate(((a, c.t["mon_a"]), (b, c.t["mon_b"]))):
        x = M + k * (pw + 36)
        d.text((x, y0), lab, font=c.f(28, True), fill=WHITE)
        # monitor bezel
        bez = Image.new("RGBA", (pw + 20, ph + 20), (12, 10, 14, 255))
        bez.alpha_composite(rounded(img, 6), (10, 10))
        shadow_paste(c.im, bez, (x - 10, y0 + 54), r=14, alpha=120)
        d.rounded_rectangle([x + pw // 2 - 40, y0 + 54 + ph + 20, x + pw // 2 + 40, y0 + 54 + ph + 44], 4,
                            fill=(60, 52, 66))
        d.rounded_rectangle([x + pw // 2 - 90, y0 + 54 + ph + 44, x + pw // 2 + 90, y0 + 54 + ph + 54], 5,
                            fill=(60, 52, 66))
    # label inside capture
    lab = c.t["mon_gone"]
    f = c.f(20, True)
    bx = M + pw + 36 + sx + ww // 2 - int(tw(f, lab)) // 2 - 14
    bx = min(bx, M + 2 * pw + 36 - int(tw(f, lab)) - 40)
    pill(d, (bx, y0 + 54 + 10 + sy + wh // 2 - 20), lab, f, WHITE, PEACH_D, pad=(14, 6))
    y = y0 + 54 + ph + 100
    for s in c.t["cap_points"]:
        d.ellipse([M, y + 14, M + 14, y + 28], fill=PEACH)
        text_block(d, (M + 32, y), s, c.f(30), WHITE, max_w=COLW - 32, label="cap_points")
        y += 56


def vis_copy(c: Card):
    d = c.d
    ed = shot("rich_light", (420, 120, 860, 470), 560)
    y0 = VIS_TOP + 6
    shadow_paste(c.im, ed, (M, y0), border=LINE)
    # outputs on the right
    x = M + 600
    w = COLW - 600
    for i, ((k, lab), plain) in enumerate(((c.t["copy_a"], False), (c.t["copy_b"], True))):
        y = y0 + i * 270
        keys(d, (x, y), k, F(24, True, "en"))
        d.text((x, y + 64), lab, font=c.f(26, True), fill=PLUM if not plain else PEACH_D)
        box = Image.new("RGBA", (w, 140), WHITE)
        shadow_paste(c.im, box, (x, y + 108), r=14, blur=16, alpha=40, border=LINE)
        lines = c.t["plain_lines"]
        if plain:
            for j, s in enumerate(lines):
                d.text((x + 18, y + 124 + j * 36), s, font=F(19, False, c.sc), fill=INK)
        else:
            d.text((x + 18, y + 120), lines[0], font=F(24, True, c.sc), fill=INK)
            d.text((x + 18, y + 160), lines[1], font=F(18, False, c.sc), fill=INK)
            b0, b1 = c.t["rich_bullet"]
            d.text((x + 18, y + 192), b0, font=F(18, False, c.sc), fill=INK)
            d.text((x + 18 + tw(F(18, False, c.sc), b0), y + 192), b1, font=F(18, True, c.sc), fill=PLUM2)
        for j, s in enumerate(lines):   # text starts 18px into the box
            if tw(F(24 if (j == 0 and not plain) else 19, not plain and j == 0, c.sc), s) > w - 22:
                WARN.append(f"{c.lang} copy box line too wide: {s}")
    d.text((M, y0 + ed.height + 22), "Ctrl+Shift+V  " + ("붙여넣기도 글자만" if c.lang == "ko" else "pastes plain text, too"),
           font=c.f(24), fill=MUTED)


def vis_code(c: Card):
    d = c.d
    y0 = VIS_TOP - 4
    ed = shot("env_dark", (300, 98, 720, 240), 700)
    shadow_paste(c.im, ed, (M, y0))
    # highlight line 4 (PAY_API_KEY) — rows are 15px apart in the source shot
    s = 700 / 420
    ly = y0 + int((152 - 98) * s)
    hl = Image.new("RGBA", c.im.size, (0, 0, 0, 0))
    ImageDraw.Draw(hl).rectangle([M, ly, M + 700, ly + int(16 * s)], fill=PEACH + (60,))
    c.im.alpha_composite(hl)
    # context menu callout
    mx, my = M + 380, ly + 30
    menu = Image.new("RGBA", (COLW - 380 + 0, 120), (44, 40, 50, 255))
    shadow_paste(c.im, menu, (mx, my), r=12, blur=16, alpha=120)
    d.rounded_rectangle([mx + 8, my + 10, mx + menu.width - 8, my + 56], 8, fill=(122, 60, 147))
    d.text((mx + 24, my + 16), c.t["value_menu"], font=c.f(24, True), fill=WHITE)
    lab, val = c.t["value_got"].split(": ")
    x = mixed(d, (mx + 24, my + 70), [(lab + ": ", c.sc)], 22, (200, 190, 210))
    d.text((x, my + 70), val, font=F(22, False, "mono"), fill=PEACH)
    # JSON (real) below
    js = shot("json_dark", (300, 98, 660, 290), 520)
    y1 = my + 170
    shadow_paste(c.im, js, (M, y1))
    pill(d, (M + 560, y1 + 30), c.t["json_btn"], c.f(24, True), INK, PEACH)
    t2 = ("줄 번호 · 색 구분 · 자동 들여쓰기" if c.lang == "ko" else "line numbers · highlighting · auto-indent")
    text_block(d, (M + 560, y1 + 110), t2.replace(" · ", "\n"), c.f(26), MUTED, 1.5, COLW - 560, label="code pts")


def vis_shot(c: Card):
    d = c.d
    y0 = VIS_TOP + 4
    note = shot("capture_light", (420, 120, 1150, 640), 560)
    shadow_paste(c.im, note, (M, y0), border=LINE)
    text_block(d, (M, y0 + note.height + 34), c.t["rec_note"], c.f(25), MUTED, 1.45, 560, label="rec_note")
    x, cw = M + 604, COLW - 604
    keys(d, (x, y0 + 4), "Ctrl+Alt+S", F(22, True, "en"))
    text_block(d, (x, y0 + 64), c.t["keys_s"], c.f(24), INK, max_w=cw, label="keys_s")
    keys(d, (x, y0 + 130), "Ctrl+Alt+R", F(22, True, "en"))
    text_block(d, (x, y0 + 190), c.t["keys_r"], c.f(24), INK, 1.3, cw, label="keys_r")
    # recording frame illustration (what you see while recording)
    ry = y0 + 270
    scr = gradient(cw, 260, (232, 222, 240), (255, 222, 204), 20).convert("RGBA")
    shadow_paste(c.im, scr, (x, ry), r=14, blur=16, alpha=50)
    fx0, fy0, fx1, fy1 = x + 26, ry + 26, x + cw - 26, ry + 260 - 70
    ds = c.d
    ds.rectangle([fx0, fy0, fx1, fy1], fill=WHITE)
    for r_ in range(4):
        ds.rounded_rectangle([fx0 + 18, fy0 + 20 + r_ * 26, fx0 + 18 + (fx1 - fx0 - 36) * (0.8 if r_ % 2 else 0.5),
                              fy0 + 30 + r_ * 26], 4, fill=(226, 222, 232))
    ds.rectangle([fx0, fy0, fx1, fy1], outline=(229, 57, 53), width=4)
    bw_ = 220
    bx0, by0 = (fx0 + fx1) // 2 - bw_ // 2, fy1 + 12
    ds.rounded_rectangle([bx0, by0, bx0 + bw_, by0 + 40], 20, fill=(28, 26, 31))
    ds.ellipse([bx0 + 16, by0 + 13, bx0 + 30, by0 + 27], fill=(229, 57, 53))
    ds.text((bx0 + 40, by0 + 7), c.t["rec_bar"], font=F(18, True, c.sc), fill=WHITE)
    px = bx0 + bw_ - 58
    ds.rectangle([px, by0 + 12, px + 5, by0 + 28], fill=WHITE)
    ds.rectangle([px + 10, by0 + 12, px + 15, by0 + 28], fill=WHITE)
    ds.rectangle([px + 26, by0 + 12, px + 42, by0 + 28], fill=WHITE)


def vis_clip(c: Card):
    d = c.d
    y0 = VIS_TOP + 10
    big = F(40, True, "en")
    x = keys(d, (M, y0), "Ctrl+Alt+M", big)
    # flow: copy → toast → list item
    y1 = y0 + 120
    box = Image.new("RGBA", (300, 150), WHITE)
    shadow_paste(c.im, box, (M, y1), border=LINE)
    d.text((M + 22, y1 + 18), c.t["clip_src"], font=c.f(22, True), fill=PEACH_D)
    for j, s in enumerate(c.t["clip_text"]):
        d.text((M + 22, y1 + 60 + j * 30), s, font=F(20, False, c.sc), fill=INK)
        if tw(F(20, False, c.sc), s) > 300 - 40:
            WARN.append(f"{c.lang} clip text too wide: {s}")
    d.rectangle([M + 20, y1 + 60, M + 230, y1 + 118], outline=(170, 200, 255), width=0)
    # arrow
    ax = M + 330
    d.line([ax, y1 + 75, ax + 60, y1 + 75], fill=PLUM, width=5)
    d.polygon([(ax + 60, y1 + 63), (ax + 78, y1 + 75), (ax + 60, y1 + 87)], fill=PLUM)
    # toast (Windows-like, generic)
    tx, tw_ = ax + 104, COLW - (ax + 104 - M)
    toast = Image.new("RGBA", (tw_, 150), (40, 36, 46, 255))
    shadow_paste(c.im, toast, (tx, y1), r=14, alpha=110)
    c.im.alpha_composite(icon(40), (tx + 22, y1 + 22))
    d.text((tx + 76, y1 + 24), c.t["clip_toast_t"], font=F(22, True, "en"), fill=WHITE)
    text_block(d, (tx + 22, y1 + 80), c.t["clip_toast"], c.f(23), (225, 218, 232), max_w=tw_ - 40, label="toast")
    # real list crop with the new note on top
    y2 = y1 + 190
    lst = shot("clip_light", (0, 560, 300, 700), 420)
    shadow_paste(c.im, lst, (M, y2), border=LINE)
    text_block(d, (M + 470, y2 + 30), c.t["clip_note"], c.f(28, True), INK, 1.4, COLW - 470, label="clip_note")
    text_block(d, (M + 470, y2 + 120), ("복사한 내용이 메모 목록\n맨 위에 바로 들어가요" if c.lang == "ko"
                                       else "It lands at the top\nof your note list"), c.f(24), MUTED, 1.5,
               COLW - 470, label="clip_note2")


VIS = [vis_files, vis_crypto, vis_capture, vis_copy, vis_code, vis_shot, vis_clip]

# ───────── cards ─────────


def card_cover(lang):
    c = Card(lang, plum=True)
    c.header(1)
    d = c.d
    pill(d, (M, 170), c.t["c1_kicker"], c.f(28, True), INK, PEACH)
    y = text_block(d, (M, 262), c.t["c1_title"], c.f(96, True), WHITE, 1.16, COLW, label="cover title") + 34
    y = text_block(d, (M, y), c.t["c1_sub"], c.f(32), (238, 226, 245), 1.5, COLW, label="cover sub") + 40
    x = M
    for s in c.t["pills"]:
        x = pill(d, (x, y), s, c.f(24, True), WHITE, None, outline=(236, 214, 244)) + 14
    if x > W - M:
        WARN.append(f"{lang} cover pills overflow {x}")
    app = shot("rich_light", None, 1000)
    shadow_paste(c.im, app, (M + 40, y + 110), r=18, alpha=120)
    return c


def card_pillar(lang, i):
    dark = i == 2
    c = Card(lang, dark=dark)
    c.header(i + 2)
    k, t, s = T[lang]["cards"][i]
    c.titleblock(k, t, s)
    VIS[i](c)
    c.footer()
    return c


def card_cta(lang):
    c = Card(lang, plum=True)
    c.header(9)
    d = c.d
    c.im.alpha_composite(icon(200), (M - 10, 170))
    d.text((M + 220, 210), "Hushpad", font=F(84, True, "en"), fill=WHITE)
    d.text((M + 226, 312), c.t["brand_sub"] if lang == "ko" else "허시패드 · hush + pad", font=F(30, False, "ko"),
           fill=(238, 226, 245))
    pill(d, (M, 430), c.t["cta_kicker"], c.f(28, True), INK, PEACH)
    y = text_block(d, (M, 520), c.t["cta_title"], c.f(80, True), WHITE, 1.18, COLW, label="cta title") + 60
    for a, b in c.t["cta_rows"]:
        d.ellipse([M, y + 15, M + 14, y + 29], fill=PEACH)
        x = M + 34
        fa = c.f(30, True)
        d.text((x, y), a, font=fa, fill=WHITE)
        x += tw(fa, a) + 18
        if b:
            d.text((x, y + 2), b, font=c.f(28), fill=(232, 216, 242))
            if x + tw(c.f(28), b) > W - M:
                WARN.append(f"{lang} cta row overflow: {b}")
        else:   # language list in each language's own font
            runs = []
            for j, (s, sc) in enumerate(c.t["langs"]):
                if j:
                    runs.append(("  ·  ", "en"))
                runs.append((s, sc))
            ex = mixed(d, (x, y + 2), runs, 28, (232, 216, 242))
            if ex > W - M:
                WARN.append(f"{lang} langs overflow {ex}")
        y += 62
    # button
    by = y + 70
    bf = c.f(32, True)
    label = c.t["cta_btn"]
    d.rounded_rectangle([M, by, M + COLW, by + 96], 48, fill=WHITE)
    d.text((M + COLW // 2, by + 48), label, font=bf, fill=PLUM, anchor="mm")
    d.text((M + COLW // 2, by + 140), URL, font=F(34, True, "en"), fill=WHITE, anchor="mm")
    return c


# ───────── other formats ─────────


def square_cover(lang):
    c = Card(lang, 1080, 1080, plum=True)
    d = c.d
    c.im.alpha_composite(icon(120), (M, 84))
    d.text((M + 140, 100), "Hushpad", font=F(56, True, "en"), fill=WHITE)
    d.text((M + 144, 170), "허시패드" if lang == "ko" else "hush + pad", font=F(26, False, "ko"), fill=(238, 226, 245))
    y = text_block(d, (M, 290), c.t["c1_title"], c.f(96, True), WHITE, 1.16, COLW, label="sq title") + 30
    text_block(d, (M, y), c.t["c1_sub"], c.f(30), (238, 226, 245), 1.5, COLW, label="sq sub")
    app = shot("rich_light", (0, 0, 1280, 520), 900)
    shadow_paste(c.im, app, (M + 90, 700), alpha=120)
    return c


def link_card(lang):
    w, h = 1200, 630
    c = Card(lang, w, h, plum=True)
    d = c.d
    c.im.alpha_composite(icon(96), (64, 64))
    d.text((180, 72), "Hushpad", font=F(52, True, "en"), fill=WHITE)
    d.text((184, 136), "허시패드" if lang == "ko" else "hush + pad", font=F(24, False, "ko"), fill=(238, 226, 245))
    t = c.t["c1_title"]
    y = text_block(d, (64, 214), t, c.f(64, True), WHITE, 1.16, 560, label="link title") + 26
    sub = c.t["link_sub"]
    y = text_block(d, (64, y), sub, c.f(25), (238, 226, 245), 1.45, 560, label="link sub")
    d.text((64, h - 64), c.t["foot"], font=c.f(22, True), fill=PEACH)
    app = shot("rich_dark", (0, 0, 1000, 760), 560)
    shadow_paste(c.im, app, (w - 560 + 40, 120), alpha=130)
    return c


def story_cover(lang):
    w, h = 1080, 1920
    c = Card(lang, w, h, plum=True)
    d = c.d
    top = 300  # keep text out of the top/bottom 250px UI zones
    c.im.alpha_composite(icon(140), (M, top))
    d.text((M + 166, top + 20), "Hushpad", font=F(64, True, "en"), fill=WHITE)
    d.text((M + 170, top + 100), "허시패드" if lang == "ko" else "hush + pad", font=F(28, False, "ko"),
           fill=(238, 226, 245))
    d.text((M, top + 230), c.t["story_kicker"], font=c.f(120, True), fill=PEACH)
    y = text_block(d, (M, top + 400), c.t["c1_title"], c.f(104, True), WHITE, 1.16, COLW, label="story title") + 40
    y = text_block(d, (M, y), c.t["c1_sub"], c.f(32), (238, 226, 245), 1.5, COLW, label="story sub") + 60
    by = h - 330   # bottom band, kept above the bottom 250px UI zone
    app_h = by - 50 - y
    app = shot("rich_light", (0, 0, 1280, min(760, round(app_h * 1280 / COLW))), COLW)
    shadow_paste(c.im, app, (M, y), alpha=120)
    d.rounded_rectangle([M, by, M + COLW, by + 80], 40, fill=WHITE)
    d.text((M + COLW // 2, by + 40), c.t["foot"], font=c.f(30, True), fill=PLUM, anchor="mm")
    return c


SHOTS_DIR = SHOTS


def build(lang):
    global SHOTS_DIR
    SHOTS_DIR = SHOTS if lang == "ko" else os.path.join(SHOTS, lang)
    out = os.path.join(HERE, "cards") if lang == "ko" else os.path.join(HERE, "cards", "en")
    card_cover(lang).save(os.path.join(out, "card_01.png"))
    for i in range(7):
        card_pillar(lang, i).save(os.path.join(out, f"card_{i + 2:02d}.png"))
    card_cta(lang).save(os.path.join(out, "card_09.png"))
    square_cover(lang).save(os.path.join(out, "square_cover.png"))
    link_card(lang).save(os.path.join(out, "link_card.png"))
    story_cover(lang).save(os.path.join(out, "story_cover.png"))
    print("wrote", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", choices=["ko", "en", "all"], default="all")
    a = ap.parse_args()
    for lg in (["ko", "en"] if a.lang == "all" else [a.lang]):
        build(lg)
    for w_ in WARN:
        print("WARN", w_)
    sys.exit(1 if WARN else 0)
