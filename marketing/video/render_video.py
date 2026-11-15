"""Hushpad 유튜브 홍보 영상을 코드로 그려 MP4(H.264 + AAC)로 만든다. 외부 소스 없음, 음악은 make_music.py로 직접 합성.

python render_video.py ko            → hushpad_promo_ko.mp4 (한국어 자막 화면에 포함)
python render_video.py en            → hushpad_promo_en.mp4
python render_video.py shorts        → shorts_ko.mp4 (1080×1920, 30초 이하)
python render_video.py shorts_en     → shorts_en.mp4 (영어 UI·영어 화면 글자)
python render_video.py srt           → subtitles/*.srt (ko·en·ja·zh-Hans)
python render_video.py thumbs        → thumbnail_ko.png, thumbnail_en.png
python render_video.py stills ko 3.2 18 …  → qa/still_main_ko_003.2.png … (인코딩 없이 그 시각 화면만; shorts_ko·shorts_en도 됨)
--silent 를 붙이면 배경 음악 없이 (기본은 music/*.wav를 AAC로 넣음, 먼저 python make_music.py)
python render_video.py all           → 위 전부

앞서 capture_shots.py로 shots/ko·shots/en 실제 앱 화면을 만들어 두어야 한다.
"""
import math
import random
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QRectF, QPointF, QUrl, QTimer, QObject
from PySide6.QtGui import (QGuiApplication, QImage, QPainter, QColor, QFont, QFontMetricsF, QPen,
                           QLinearGradient, QRadialGradient, QPainterPath, QPolygonF, QTextDocument)

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FPS = 30

PLUM, PLUM2 = QColor("#7A3C93"), QColor("#9B4DB5")
PEACH, PEACH2 = QColor("#FFB38A"), QColor("#E0703F")
INK, LIGHT = QColor("#1C1A1F"), QColor("#F5F4F7")
RED = QColor("#E5484D")
WHITE = QColor("#FFFFFF")

# ====================================================================== 문구 (화면·자막 공통)
TXT = {
    # 각 언어는 따로 다듬은 문장 (직역 아님). ja·zh는 자막 줄바꿈(\n)을 직접 넣음
    "hook":   {"ko": "화면 공유 중인데, 비밀번호 메모가 떠 있다면?",
               "en": "Sharing your screen… with a password note open?",
               "ja": "画面共有中に\nパスワードのメモが開いていたら？",
               "zh-Hans": "正在共享屏幕，\n密码笔记却还开着？"},
    "shh":    {"ko": "쉿.", "en": "Shh.", "ja": "しーっ。", "zh-Hans": "嘘。"},
    "logo":   {"ko": "Hushpad, 조용한 비밀 메모장", "en": "Hushpad. A quiet notepad for private notes.",
               "ja": "Hushpad\n静かな秘密のメモ帳", "zh-Hans": "Hushpad\n安静的私密记事本"},
    "logo_sub": {"ko": "조용한 비밀 메모장", "en": "A quiet notepad for private notes"},
    "sharing": {"ko": "화면 공유 중", "en": "Sharing your screen"},
    "seen":   {"ko": "다 보여요", "en": "Everyone can see this"},
    # 비트별 제목
    "t1": {"ko": "저장 버튼이 없어요", "en": "No Save button"},
    "t2": {"ko": "캡처에 안 찍히는 창", "en": "Hidden from screen capture"},
    "t3": {"ko": "비밀 메모", "en": "Secret notes"},
    "t4": {"ko": "서식 그대로, 또는 글자만", "en": "Copy rich or plain"},
    "t5": {"ko": "HTML·JSON 코드 메모", "en": "Code notes for HTML and JSON"},
    "t6": {"ko": "스크린샷과 짧은 녹화", "en": "Screenshots and short recordings"},
    "t7": {"ko": "트레이에서도 되는 단축키", "en": "Hotkeys that work from the tray"},
    # 자막(캡션)
    "c1a": {"ko": "저장 버튼은 없어요. 쓰면 바로 저장돼요", "en": "There's no Save button. It saves as you type.",
            "ja": "保存ボタンはありません。\n書いたそばから保存されます", "zh-Hans": "没有保存按钮，\n边写边存"},
    "c1b": {"ko": "디스크에는 암호화된 파일로만 남아요", "en": "On disk, every note is AES-256 encrypted.",
            "ja": "ディスクに残るのは\n暗号化されたファイルだけ", "zh-Hans": "磁盘上只留下加密文件"},
    "c2a": {"ko": "내 화면에서는 그대로 보이는데", "en": "You can see it on your screen,",
            "ja": "自分の画面には\nちゃんと見えているのに", "zh-Hans": "你自己的屏幕上看得到，"},
    "c2b": {"ko": "캡처하거나 화면을 공유하면 안 보여요", "en": "but screenshots and screen shares can't.",
            "ja": "スクショや画面共有には\n映りません", "zh-Hans": "截图和共享屏幕里\n却没有它"},
    "c3a": {"ko": "비밀 메모는 열 때마다 가려져 있어요", "en": "Secret notes open hidden. Click to reveal.",
            "ja": "秘密のメモは\n開くたびに伏せて表示", "zh-Hans": "机密笔记\n每次打开都先遮住"},
    "c3b": {"ko": "복사한 내용은 30초 뒤 클립보드에서 지워져요", "en": "Copy it, and the clipboard clears in 30 seconds.",
            "ja": "コピーしても30秒後には\nクリップボードから消えます", "zh-Hans": "复制后 30 秒，\n自动从剪贴板清除"},
    "c4a": {"ko": "Ctrl+C로 복사하면 서식까지 그대로", "en": "Ctrl+C copies it with the formatting.",
            "ja": "Ctrl+C なら書式ごとコピー", "zh-Hans": "Ctrl+C 连格式一起复制"},
    "c4b": {"ko": "글자만 필요하면 Ctrl+Shift+C", "en": "Just the text? Ctrl+Shift+C.",
            "ja": "文字だけなら Ctrl+Shift+C", "zh-Hans": "只要文字，\n就按 Ctrl+Shift+C"},
    "c5a": {"ko": "HTML이나 JSON은 코드 메모에 붙여 두세요", "en": "Paste HTML or JSON into a code note.",
            "ja": "HTMLやJSONは\nコードメモに貼っておけます", "zh-Hans": "HTML、JSON\n放进代码笔记就行"},
    "c5b": {"ko": "한 줄로 엉킨 JSON은 Ctrl+Alt+J로 정리", "en": "One-line JSON? Ctrl+Alt+J tidies it up.",
            "ja": "1行に詰まったJSONは\nCtrl+Alt+J で整形", "zh-Hans": "挤成一行的 JSON，\n按 Ctrl+Alt+J 整理"},
    "c6a": {"ko": "영역을 끌어서 찍으면 바로 메모에 들어가요", "en": "Drag over an area, and the shot lands in your note.",
            "ja": "範囲をドラッグすると\nそのままメモに入ります", "zh-Hans": "拖出一块区域，\n截图直接进笔记"},
    "c6b": {"ko": "3분까지는 화면 녹화도 돼요", "en": "Short screen recordings work too, up to 3 minutes.",
            "ja": "3分までなら\n画面録画もできます", "zh-Hans": "也能录屏，\n最长 3 分钟"},
    "c7a": {"ko": "Ctrl+Alt+M을 누르면 클립보드가 메모로 저장돼요", "en": "Ctrl+Alt+M saves whatever's on your clipboard as a note.",
            "ja": "Ctrl+Alt+M で\nクリップボードをメモに保存", "zh-Hans": "按 Ctrl+Alt+M，\n剪贴板直接存成笔记"},
    "c7b": {"ko": "뭘 찾든 Ctrl+K", "en": "Looking for something? Ctrl+K.",
            "ja": "探しものは Ctrl+K", "zh-Hans": "要找什么，按 Ctrl+K"},
    "tag":  {"ko": "조용히 적고, 아무도 못 보게", "en": "Write quietly. Seen by no one.",
             "ja": "静かに書いて、\n誰にも見せない", "zh-Hans": "安静记录，\n无人可见"},
    "release": {"ko": "무료 오픈소스 앱이에요\nWindows와 macOS에서 받으세요", "en": "Free and open source, for Windows and macOS.",
                "ja": "無料のオープンソース\nWindows・macOS対応", "zh-Hans": "免费开源\n支持 Windows、macOS"},
    "free_big": {"ko": "무료 · 오픈소스", "en": "Free & open source"},
    "free_small": {"ko": "Windows 10/11 · macOS(Apple Silicon)", "en": "Windows 10/11 · macOS (Apple Silicon)"},
    # 작은 라벨
    "my_screen": {"ko": "내 화면", "en": "Your screen"},
    "their_screen": {"ko": "스크린샷 · 화면 공유", "en": "Screenshot / screen share"},
    "on_disk": {"ko": "디스크에 저장된 실제 파일", "en": "The actual file on disk"},
    "k_new": {"ko": "새 메모", "en": "New note"},
    "k_reveal": {"ko": "가림막 열기", "en": "Reveal"},
    "k_copy": {"ko": "복사", "en": "Copy"},
    "k_rich": {"ko": "서식 포함 복사", "en": "Copy with formatting"},
    "k_plain": {"ko": "텍스트만 복사", "en": "Copy plain text"},
    "k_json": {"ko": "JSON 정리", "en": "Tidy JSON"},
    "k_code": {"ko": "새 코드 메모", "en": "New code note"},
    "k_shot": {"ko": "스크린샷", "en": "Screenshot"},
    "k_rec": {"ko": "화면 녹화", "en": "Screen recording"},
    "k_clip": {"ko": "클립보드를 메모로", "en": "Clipboard to note"},
    "k_quick": {"ko": "새 메모", "en": "New note"},
    "k_palette": {"ko": "찾기·명령", "en": "Search and commands"},
    "tray": {"ko": "창을 닫아 둬도 돼요", "en": "Even with the window closed"},
    "paste_rich": {"ko": "붙여 넣으면 서식 그대로", "en": "Pasted: formatting kept"},
    "paste_plain": {"ko": "붙여 넣으면 글자만", "en": "Pasted: text only"},
    "clip_auto": {"ko": "30초 뒤 클립보드 비움", "en": "Clipboard clears in 30 s"},
    "toast": {"ko": "클립보드를 메모로 저장했어요", "en": "Saved your clipboard as a note"},
    "toast_sub": {"ko": "창은 열리지 않아요", "en": "The window stays closed"},
    "saved": {"ko": "자동 저장됨", "en": "Auto-saved"},
    "notepad_title": {"ko": "제목 없음 (3) - 메모", "en": "Untitled (3) - Notes"},
    "np_tabs": {"ko": ["제목 없음", "제목 없음 (2)", "새 텍스트 문서", "제목 없음 (3)", "메모 (1)"],
                "en": ["Untitled", "Untitled (2)", "New Text Document", "Untitled (3)", "Note (1)"]},
    "np_menu": {"ko": ["파일", "편집", "보기"], "en": ["File", "Edit", "View"]},
    "np_text": {"ko": ["내일 할 일", "- 견적서 다시 보내기", "- 3시 회의 자료", "", "공유 폴더 비밀번호: Spring-2026!demo", "관리자 계정: test-admin"],
                "en": ["To do tomorrow", "- resend the quote", "- slides for the 3 PM sync", "", "Shared folder password: Spring-2026!demo", "Admin account: test-admin"]},
    "doc_title": {"ko": "발표 자료 (예시)", "en": "Slides (sample)"},
    "doc_lines": {"ko": ["다음 분기 계획", "• 일정 정리", "• 담당자 확인", "• 다음 회의 준비"],
                  "en": ["Next quarter plan", "• Sort out the schedule", "• Confirm owners", "• Prep next meeting"]},
    "clip_doc": {"ko": ["회의 안내 (예시)", "회의실 예약 번호 (예시) A-1203", "내일 오후 3시, 2층 작은 회의실", "참석하시는 분은 자료를 미리 읽어 주세요."],
                 "en": ["Meeting notice (sample)", "Room booking no. (sample) A-1203", "Tomorrow 3 PM, small room on 2F", "Please read the material beforehand."]},
}
URL = "gdra.mycafe24.com/hushpad"
LANG = "ko"


def tr(key, lang=None):
    v = TXT[key]
    return v.get(lang or LANG, v.get("en"))


# ====================================================================== 수학
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def ease(x):
    x = clamp(x)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def eout(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def prog(t, a, b):
    return clamp((t - a) / (b - a)) if b > a else float(t >= a)


def lerp(a, b, u):
    return a + (b - a) * u


def window_alpha(t, a, b, c=None, d=None):
    """a→b 나타남, c→d 사라짐."""
    v = eout(prog(t, a, b))
    if c is not None:
        v *= 1 - ease(prog(t, c, d))
    return v


def col(c, alpha=1.0):
    q = QColor(c)
    q.setAlphaF(clamp(q.alphaF() * alpha))
    return q


# ====================================================================== 글꼴·그리기 도구
def font(px, weight=QFont.Bold, mono=False):
    f = QFont()
    if mono:
        f.setFamilies(["Consolas", "Malgun Gothic"])
    elif LANG == "ko":
        f.setFamilies(["Malgun Gothic", "Segoe UI"])
    else:
        f.setFamilies(["Segoe UI", "Malgun Gothic"])
    f.setPixelSize(int(px))
    f.setWeight(weight)
    f.setHintingPreference(QFont.PreferNoHinting)
    return f


def text(p, rect, s, px, color, align=Qt.AlignLeft | Qt.AlignTop, weight=QFont.Bold, wrap=True, alpha=1.0, mono=False):
    p.setFont(font(px, weight, mono))
    p.setPen(col(color, alpha))
    flags = align | (Qt.TextWordWrap if wrap else 0)
    p.drawText(QRectF(rect), flags, s)


def text_size(s, px, weight=QFont.Bold, width=10000, mono=False):
    fm = QFontMetricsF(font(px, weight, mono))
    r = fm.boundingRect(QRectF(0, 0, width, 10000), Qt.TextWordWrap, s)
    return r.width(), r.height()


def rrect(p, rect, r, fill=None, pen=None):
    path = QPainterPath()
    path.addRoundedRect(QRectF(rect), r, r)
    if fill is not None:
        p.fillPath(path, fill)
    if pen is not None:
        p.strokePath(path, pen)
    return path


def shadow(p, rect, r, strength=1.0, spread=28, dy=14):
    rect = QRectF(rect)
    for i in range(10, 0, -1):
        k = i / 10
        g = rect.adjusted(-spread * k, -spread * k + dy, spread * k, spread * k + dy)
        rrect(p, g, r + spread * k, fill=QColor(20, 10, 30, int(7 * strength)))


ICON = None


def icon_img():
    global ICON
    if ICON is None:
        ICON = QImage(str(ROOT / "assets" / "app_1024.png"))
    return ICON


def draw_icon(p, center, size, alpha=1.0):
    p.save()
    p.setOpacity(alpha)
    r = QRectF(center.x() - size / 2, center.y() - size / 2, size, size)
    p.drawImage(r, icon_img())
    p.restore()


def draw_cursor(p, pos, scale=1.6, alpha=1.0):
    x, y, s = pos.x(), pos.y(), scale
    arrow = QPolygonF([QPointF(x, y), QPointF(x, y + 17 * s), QPointF(x + 4.5 * s, y + 13 * s),
                       QPointF(x + 8 * s, y + 20 * s), QPointF(x + 10.5 * s, y + 19 * s),
                       QPointF(x + 7 * s, y + 12 * s), QPointF(x + 12.5 * s, y + 12 * s)])
    p.save()
    p.setOpacity(alpha)
    p.setPen(QPen(Qt.white, 1.6 * s / 1.3, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(QColor("#111"))
    p.drawPolygon(arrow)
    p.restore()


def ripple(p, pos, u, color=PEACH2, rmax=46):
    if u <= 0 or u >= 1:
        return
    p.save()
    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(col(color, 1 - u), 5 * (1 - u) + 1))
    r = rmax * eout(u)
    p.drawEllipse(pos, r, r)
    p.restore()


def ring(p, rect, alpha, color=PEACH2, width=5, radius=12):
    if alpha <= 0:
        return
    rrect(p, QRectF(rect).adjusted(-8, -8, 8, 8), radius, pen=QPen(col(color, alpha), width))


# ---------------------------------------------------------------- 키 캡
def key_widths(combo, h):
    keys = combo.split("+")
    ws = []
    for k in keys:
        w, _ = text_size(k, h * 0.42, QFont.DemiBold)
        ws.append(max(h * 1.05, w + h * 0.62))
    return keys, ws


def draw_keys(p, x, y, combo, h=52, pressed=0.0, alpha=1.0, dark=False):
    """키 모양 칩 'Ctrl+Alt+M'. pressed 0~1 (눌림 정도). 너비를 돌려준다."""
    keys, ws = key_widths(combo, h)
    gap = h * 0.36
    cx = x
    press = math.sin(clamp(pressed) * math.pi)  # 0→1→0
    for i, (k, w) in enumerate(zip(keys, ws)):
        dy = press * h * 0.08
        base = QRectF(cx, y + h * 0.1, w, h * 0.92)
        rrect(p, base, h * 0.2, fill=col("#CFC6DA" if not dark else "#0E0C10", alpha))
        top = QRectF(cx, y + dy, w, h * 0.9)
        face = QColor("#FFFFFF") if not dark else QColor("#2A2630")
        if press > 0:
            face = QColor.fromRgbF(*(lerp(a, b, press) for a, b in zip(face.getRgbF()[:3], PEACH.getRgbF()[:3])), 1)
        rrect(p, top, h * 0.2, fill=col(face, alpha), pen=QPen(col("#D9D2E2" if not dark else "#46404E", alpha), 1.5))
        text(p, top, k, h * 0.42, INK if not dark or press > 0.5 else WHITE, Qt.AlignCenter, QFont.DemiBold, False, alpha)
        cx += w
        if i < len(keys) - 1:
            text(p, QRectF(cx, y, gap, h * 0.9), "+", h * 0.4, "#8A8492", Qt.AlignCenter, QFont.Bold, False, alpha)
            cx += gap
    return cx - x


def keys_total_width(combo, h=52):
    keys, ws = key_widths(combo, h)
    return sum(ws) + h * 0.36 * (len(keys) - 1)


# ---------------------------------------------------------------- 배경
def draw_bg(p, L, t, dark=False):
    W, H = L.W, L.H
    p.fillRect(QRectF(0, 0, W, H), QColor("#17141B") if dark else LIGHT)
    for cx, cy, r, c, a, ph in ((0.12, 0.2, 0.55, PLUM2, 0.16, 0.0), (0.92, 0.85, 0.6, PEACH, 0.22, 1.7),
                                (0.85, 0.08, 0.35, PLUM, 0.10, 3.1)):
        x = W * (cx + 0.02 * math.sin(t * 0.35 + ph))
        y = H * (cy + 0.02 * math.cos(t * 0.3 + ph))
        g = QRadialGradient(QPointF(x, y), max(W, H) * r)
        g.setColorAt(0, col(c, a * (1.4 if dark else 1)))
        g.setColorAt(1, col(c, 0))
        p.fillRect(QRectF(0, 0, W, H), g)


def draw_wallpaper(p, rect, t=0.0):
    g = QLinearGradient(rect.topLeft(), rect.bottomRight())
    g.setColorAt(0, QColor("#2A1F3D"))
    g.setColorAt(0.55, QColor("#5B3270"))
    g.setColorAt(1, QColor("#C46A4A"))
    p.fillRect(rect, g)
    rg = QRadialGradient(QPointF(rect.left() + rect.width() * 0.75, rect.top() + rect.height() * 0.3), rect.width() * 0.5)
    rg.setColorAt(0, QColor(255, 179, 138, 70))
    rg.setColorAt(1, QColor(255, 179, 138, 0))
    p.fillRect(rect, rg)


def draw_taskbar(p, rect):
    s = rect.width() / 1920
    h = 56 * s
    bar = QRectF(rect.left(), rect.bottom() - h, rect.width(), h)
    p.fillRect(bar, QColor(24, 20, 30, 215))
    n = 6
    w = 34 * s
    x0 = rect.center().x() - (n * (w + 14 * s)) / 2
    for i in range(n):
        rrect(p, QRectF(x0 + i * (w + 14 * s), bar.top() + (h - w) / 2, w, w), 8 * s,
              fill=QColor(255, 255, 255, 60 if i else 120))
    text(p, QRectF(bar.right() - 160 * s, bar.top(), 140 * s, h), "14:32", 20 * s, WHITE, Qt.AlignRight | Qt.AlignVCenter,
         QFont.Normal, False)


def draw_doc_window(p, rect, title, lines, s, select_line=None, sel_u=0.0):
    """일반 문서 창 (특정 제품 모양 아님)."""
    shadow(p, rect, 14 * s, 1.2, 30 * s, 12 * s)
    path = rrect(p, rect, 14 * s, fill=QColor("#FFFFFF"))
    p.save()
    p.setClipPath(path)
    p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 54 * s), QColor("#EEEAF2"))
    for i, c in enumerate(("#E0703F", "#FFB38A", "#9B4DB5")):
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(rect.left() + 28 * s + i * 24 * s, rect.top() + 27 * s), 7 * s, 7 * s)
    text(p, QRectF(rect.left() + 110 * s, rect.top(), rect.width() - 140 * s, 54 * s), title, 22 * s, "#4A4452",
         Qt.AlignLeft | Qt.AlignVCenter, QFont.DemiBold, False)
    y = rect.top() + 90 * s
    for i, ln in enumerate(lines):
        px = (40 if i == 0 else 28) * s
        if select_line is not None and i == select_line and sel_u > 0:
            w, _ = text_size(ln, px, QFont.Normal)
            p.fillRect(QRectF(rect.left() + 46 * s, y - 4 * s, (w + 8 * s) * sel_u, px * 1.45), QColor(122, 60, 147, 70))
        text(p, QRectF(rect.left() + 50 * s, y, rect.width() - 100 * s, px * 1.6), ln, px, INK,
             weight=QFont.Bold if i == 0 else QFont.Normal, wrap=False)
        y += px * (1.9 if i == 0 else 1.7)
    for k in range(3):
        rrect(p, QRectF(rect.left() + 50 * s, y + 20 * s + k * 34 * s, rect.width() * (0.7 - 0.15 * k), 14 * s), 7 * s,
              fill=QColor("#ECE8F0"))
    p.restore()


def draw_desktop(p, rect, t=0.0, doc=True, doc_key="doc", select_line=None, sel_u=0.0):
    p.save()
    p.setClipRect(rect)
    draw_wallpaper(p, rect, t)
    s = rect.width() / 1920
    if doc:
        title = tr("doc_title") if doc_key == "doc" else tr("clip_doc")[0]
        lines = tr("doc_lines") if doc_key == "doc" else tr("clip_doc")
        d = QRectF(rect.left() + 140 * s, rect.top() + 110 * s, 1000 * s, 700 * s)
        draw_doc_window(p, d, title, lines, s, select_line, sel_u)
    draw_taskbar(p, rect)
    p.restore()


# ---------------------------------------------------------------- 앱 창
class Shots:
    def __init__(self, lang):
        base = HERE / "shots" / lang
        if not base.exists():
            sys.exit(f"{base} 없음 — 먼저 python capture_shots.py 를 실행하세요")
        self.base = base
        self.cache = {}
        self.ntype = int((base / "type_count.txt").read_text("utf-8"))

    def __getitem__(self, name):
        if name not in self.cache:
            img = QImage(str(self.base / f"{name}.png"))
            if img.isNull():
                raise FileNotFoundError(self.base / f"{name}.png")
            self.cache[name] = img.convertToFormat(QImage.Format_ARGB32_Premultiplied)
        return self.cache[name]


SH = None


def win_rect_for(L, ar=1920 / 1140):
    return L.win


def draw_window(p, rect, img, dark=False, zoom=1.0, focus=None, alpha=1.0, img2=None, mix=0.0, shadow_k=1.0):
    """앱 창 그리기. rect = 제목 표시줄 포함 바깥. 돌려주는 함수 m(ix,iy) → 화면 좌표."""
    rect = QRectF(rect)
    s = rect.width() / 1280
    tb = 38 * s
    p.save()
    p.setOpacity(alpha)
    shadow(p, rect, 14 * s, 1.3 * shadow_k, 34 * s, 16 * s)
    path = rrect(p, rect, 14 * s, fill=QColor("#1F1C24") if dark else QColor("#ECE9F0"))
    p.setClipPath(path, Qt.IntersectClip)  # 바깥 클립(썸네일의 왼쪽 절반 등)을 지킴
    # 제목 표시줄
    draw_icon(p, QPointF(rect.left() + 24 * s, rect.top() + tb / 2), 20 * s)
    text(p, QRectF(rect.left() + 44 * s, rect.top(), 300 * s, tb), "Hushpad", 15 * s, "#E8E4EE" if dark else "#3B3542",
         Qt.AlignLeft | Qt.AlignVCenter, QFont.Normal, False)
    gc = QColor("#B9B2C2") if dark else QColor("#6E6777")
    p.setPen(QPen(gc, 1.4 * s))
    y = rect.top() + tb / 2
    xr = rect.right() - 26 * s
    p.drawLine(QPointF(xr - 6 * s, y - 6 * s), QPointF(xr + 6 * s, y + 6 * s))
    p.drawLine(QPointF(xr - 6 * s, y + 6 * s), QPointF(xr + 6 * s, y - 6 * s))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(xr - 52 * s, y - 6 * s, 12 * s, 12 * s))
    p.drawLine(QPointF(xr - 98 * s, y), QPointF(xr - 86 * s, y))
    # 내용
    content = QRectF(rect.left(), rect.top() + tb, rect.width(), rect.height() - tb)
    iw, ih = img.width(), img.height()
    ca = content.width() / content.height()
    sh_ = ih / zoom
    sw_ = sh_ * ca
    if sw_ > iw / zoom:
        sw_ = iw / zoom
        sh_ = sw_ / ca
    fx, fy = focus if focus else (iw / 2, ih / 2)
    sx = clamp(fx - sw_ / 2, 0, iw - sw_)
    sy = clamp(fy - sh_ / 2, 0, ih - sh_)
    src = QRectF(sx, sy, sw_, sh_)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    p.drawImage(content, img, src)
    if img2 is not None and mix > 0:
        p.setOpacity(alpha * mix)
        p.drawImage(content, img2, src)
    p.restore()
    k = content.width() / sw_

    def m(ix, iy):
        return QPointF(content.left() + (ix - sx) * k, content.top() + (iy - sy) * k)
    m.k = k
    return m


# ---------------------------------------------------------------- 자막·제목
def caption(p, L, t, items, dark=False):
    """items: [(t0, t1, key)] — 한 번에 하나."""
    for t0, t1, key in items:
        if t0 <= t < t1:
            a = window_alpha(t, t0, t0 + 0.35, t1 - 0.25, t1)
            s = tr(key).replace("\n", " ")
            px = L.cap_px
            maxw = L.cap_w
            w, h = text_size(s, px, QFont.Bold, maxw)
            padx, pady = px * 0.9, px * 0.45
            w += 8
            r = QRectF(L.W / 2 - w / 2 - padx, L.cap_y - h / 2 - pady + (1 - eout(prog(t, t0, t0 + 0.35))) * 18,
                       w + padx * 2, h + pady * 2)
            shadow(p, r, r.height() / 2 if h < px * 1.6 else 28, 0.8 * a, 16, 8)
            rrect(p, r, r.height() / 2 if h < px * 1.6 else 28, fill=col(PLUM if dark else INK, 0.95 * a))
            text(p, r.adjusted(padx, pady, -padx, -pady), s, px, WHITE, Qt.AlignCenter, QFont.Bold, True, a)


def side_title(p, L, t, idx, key, chips, dark=False):
    """왼쪽(가로) 또는 위(세로)에 번호·제목·키 칩. chips: [(combo, label_key, press_time)]"""
    a = window_alpha(t, 0.0, 0.5)
    ink = WHITE if dark else INK
    sub = QColor("#B9B2C2") if dark else QColor("#6E6777")
    if L.portrait:
        x, y, w = 60, 150, L.W - 120
        tw, th = text_size(tr(key), 76, QFont.Bold, w)
        dy = (1 - eout(prog(t, 0, 0.5))) * 24
        text(p, QRectF(x, y + 56 + dy, w, th + 10), tr(key), 76, ink, Qt.AlignHCenter | Qt.AlignTop, QFont.Bold, True, a)
        # 칩 한 줄 (가운데 정렬, 최대 2개)
        hh = 58
        row = chips[:2]
        widths = [keys_total_width(c, hh) for c, _, _ in row]
        total = sum(widths) + 50 * (len(row) - 1)
        cx = L.W / 2 - total / 2
        cy = y + 56 + th + 40
        for (combo, lk, pt), cw in zip(row, widths):
            ca = window_alpha(t, 0.3, 0.8)
            draw_keys(p, cx, cy, combo, hh, prog(t, pt, pt + 0.45) if pt is not None else 0, ca, dark)
            cx += cw + 50
        return
    x, w = 90, 420
    y0 = L.title_y
    text(p, QRectF(x, y0, w, 40), f"{idx:02d} / 07", 28, PEACH2, Qt.AlignLeft | Qt.AlignTop, QFont.Bold, False, a)
    tpx = 58
    tw, th = text_size(tr(key), tpx, QFont.Bold, w)
    while th > tpx * 2.8 and tpx > 40:  # 두 줄 안에 들어가게 줄임
        tpx -= 4
        tw, th = text_size(tr(key), tpx, QFont.Bold, w)
    dx = (1 - eout(prog(t, 0, 0.5))) * -30
    text(p, QRectF(x + dx, y0 + 48, w, th + 10), tr(key), tpx, ink, Qt.AlignLeft | Qt.AlignTop, QFont.Bold, True, a)
    p.fillRect(QRectF(x, y0 + 48 + th + 26, 64 * eout(prog(t, 0.2, 0.8)), 6), PEACH2)
    cy = y0 + 48 + th + 70
    for i, (combo, lk, pt) in enumerate(chips):
        ca = window_alpha(t, 0.35 + i * 0.12, 0.85 + i * 0.12)
        hh = 50
        draw_keys(p, x, cy, combo, hh, prog(t, pt, pt + 0.45) if pt is not None else 0, ca, dark)
        if lk:
            text(p, QRectF(x, cy + hh + 8, w, 36), tr(lk), 24, sub, Qt.AlignLeft | Qt.AlignTop, QFont.Normal, False, ca)
        cy += hh + 62
    return cy


# ====================================================================== 레이아웃
class Layout:
    def __init__(self, portrait=False):
        self.portrait = portrait
        if portrait:
            self.W, self.H = 1080, 1920
            # 세로: 창은 편집 영역을 잘라 보여 줌
            self.win = QRectF(40, 560, 1000, 960)
            self.cap_y, self.cap_px, self.cap_w = 1665, 46, 900
        else:
            self.W, self.H = 1920, 1080
            self.win = QRectF(580, 96, 1280, 38 + 1280 * 1140 / 1920)
            self.cap_y, self.cap_px, self.cap_w = 1000, 38, 1600
            self.title_y = 230


# ====================================================================== 장면
def sc_hook(p, L, t, D):
    k = D / 7.0
    T = lambda x: x * k  # noqa: E731
    W, H = L.W, L.H
    full = QRectF(0, 0, W, H)
    # 배경 = 바탕화면 + 일반 메모장
    cam = 1.0 + 0.05 * ease(prog(t, 0, T(3.7)))
    p.save()
    p.translate(W / 2, H / 2)
    p.scale(cam, cam)
    p.translate(-W / 2, -H / 2)
    draw_wallpaper(p, full)
    if L.portrait:
        nr = QRectF(50, 470, 980, 1000)
    else:
        nr = QRectF(W / 2 - 700, 190, 1400, 760)
    pw_rect = draw_notepad(p, nr, t)
    if not L.portrait:
        draw_taskbar(p, full)
    if pw_rect is not None:
        pw_rect = p.transform().mapRect(pw_rect)
    p.restore()
    # 위쪽 훅 문구
    a = window_alpha(t, T(0.1), T(0.5))
    s = tr("hook")
    if L.portrait:
        s = s.replace("… ", "…\n")  # 영어 훅은 뜻 단위로 줄바꿈
        tw, th = text_size(s, 68, QFont.Bold, 960)
        r = QRectF(60, 170, 960, th + 10)
        text(p, r.translated(0, 3), s, 68, QColor(0, 0, 0, 120), Qt.AlignHCenter, QFont.Bold, True, a)
        text(p, r, s, 68, WHITE, Qt.AlignHCenter, QFont.Bold, True, a)
    else:
        tw, th = text_size(s, 60, QFont.Bold, 1700)
        r = QRectF(W / 2 - tw / 2 - 40, 50, tw + 80, th + 36)
        rrect(p, r, r.height() / 2, fill=col(INK, 0.85 * a))
        text(p, r, s, 60, WHITE, Qt.AlignCenter, QFont.Bold, False, a)
    # 화면 공유 표시
    sa = window_alpha(t, T(1.7), T(2.0))
    if sa > 0:
        p.setPen(QPen(col(RED, sa), 10))
        p.setBrush(Qt.NoBrush)
        p.drawRect(full.adjusted(5, 5, -5, -5))
        lab = "●  " + tr("sharing")
        lw, lh = text_size(lab, 30, QFont.Bold, 2000)
        ly = (H - 150) if not L.portrait else 1560
        lr = QRectF(W / 2 - lw / 2 - 30, ly, lw + 60, 60)
        rrect(p, lr, 30, fill=col(RED, sa))
        text(p, lr, lab, 30, WHITE, Qt.AlignCenter, QFont.Bold, False, sa)
    # 찰칵 + 강조
    fl = prog(t, T(2.6), T(2.95))
    if 0 < fl < 1:
        p.fillRect(full, QColor(255, 255, 255, int(230 * (1 - fl))))
    ha = window_alpha(t, T(2.8), T(3.1))
    if ha > 0 and pw_rect is not None:
        r = pw_rect
        p.setPen(QPen(col(RED, ha), 6))
        p.setBrush(col(RED, 0.10 * ha))
        p.drawRoundedRect(r.adjusted(-18, -8, 18, 8), 12, 12)
        lab = tr("seen")
        lw, _ = text_size(lab, 30, QFont.Bold, 2000)
        lr = QRectF(r.right() - lw - 40, r.top() - 70, lw + 40, 52)
        rrect(p, lr, 26, fill=col(RED, ha))
        text(p, lr, lab, 30, WHITE, Qt.AlignCenter, QFont.Bold, False, ha)
    # 쉿.
    sh = prog(t, T(3.6), T(4.0))
    if sh > 0:
        p.fillRect(full, col(INK, ease(sh)))
        a2 = window_alpha(t, T(3.75), T(4.15), T(4.85), T(5.1))
        if a2 > 0:
            sc = lerp(1.25, 1.0, eout(prog(t, T(3.75), T(4.3))))
            p.save()
            p.translate(W / 2, H / 2)
            p.scale(sc, sc)
            for i in range(3):
                rr = 210 + i * 70 + 30 * eout(prog(t, T(3.8), T(4.8)))
                p.setPen(QPen(col(PEACH, 0.18 * a2 / (i + 1)), 3))
                p.setBrush(Qt.NoBrush)
                p.drawEllipse(QPointF(0, 0), rr, rr)
            text(p, QRectF(-600, -170, 1200, 340), tr("shh"), 230, PEACH, Qt.AlignCenter, QFont.Black, False, a2)
            p.restore()
    # 로고
    lg = prog(t, T(4.95), T(5.4))
    if lg > 0:
        g = QLinearGradient(0, 0, W, H)
        g.setColorAt(0, col(PLUM, ease(lg)))
        g.setColorAt(1, col(PLUM2, ease(lg)))
        p.fillRect(full, g)
        rg = QRadialGradient(QPointF(W * 0.8, H * 0.85), W * 0.6)
        rg.setColorAt(0, col(PEACH, 0.35 * lg))
        rg.setColorAt(1, col(PEACH, 0))
        p.fillRect(full, rg)
        u = eout(prog(t, T(5.05), T(5.7)))
        cy = H / 2 - (90 if not L.portrait else 140)
        draw_icon(p, QPointF(W / 2, cy), lerp(150, 230, u) if not L.portrait else lerp(200, 300, u), u)
        a3 = window_alpha(t, T(5.4), T(5.9))
        ny = cy + (150 if not L.portrait else 200)
        text(p, QRectF(0, ny + (1 - a3) * 20, W, 130), "Hushpad", 112 if not L.portrait else 130, WHITE,
             Qt.AlignHCenter | Qt.AlignTop, QFont.Bold, False, a3)
        a4 = window_alpha(t, T(5.7), T(6.2))
        text(p, QRectF(0, ny + (150 if not L.portrait else 170), W, 70), tr("logo_sub"), 44 if not L.portrait else 52,
             QColor("#FFE3D3"), Qt.AlignHCenter | Qt.AlignTop, QFont.Bold, False, a4)


def draw_notepad(p, rect, t):
    """평범한 일반 메모장 (특정 제품 모양 아님). 비밀번호 줄 사각형을 돌려준다."""
    s = rect.width() / 1400
    shadow(p, rect, 10 * s, 1.5, 36 * s, 16 * s)
    path = rrect(p, rect, 10 * s, fill=QColor("#FFFFFF"))
    p.save()
    p.setClipPath(path)
    # 제목 줄 + 탭
    p.fillRect(QRectF(rect.left(), rect.top(), rect.width(), 108 * s), QColor("#E9E9EC"))
    tabs = tr("np_tabs")
    x = rect.left() + 16 * s
    for i, name in enumerate(tabs):
        w, _ = text_size(name, 21 * s, QFont.Normal)
        w = min(w + 70 * s, 260 * s)
        r = QRectF(x, rect.top() + 14 * s, w, 46 * s)
        active = i == 3
        if active:
            rrect(p, r.adjusted(0, 0, 0, 12 * s), 8 * s, fill=QColor("#FFFFFF"))
        p.setPen(Qt.NoPen)
        p.setBrush(QColor("#9A9AA2"))
        p.drawRoundedRect(QRectF(r.left() + 14 * s, r.top() + 14 * s, 14 * s, 18 * s), 2 * s, 2 * s)
        p.setFont(font(21 * s, QFont.Normal))
        p.setPen(QColor("#2B2B30"))
        fm = QFontMetricsF(p.font())
        p.drawText(QRectF(r.left() + 36 * s, r.top(), w - 50 * s, r.height()), Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(name, Qt.ElideRight, w - 50 * s))
        x += w + 6 * s
        if x > rect.right() - 300 * s:
            break
    text(p, QRectF(x + 8 * s, rect.top() + 14 * s, 40 * s, 46 * s), "+", 30 * s, "#55555C", Qt.AlignCenter, QFont.Normal, False)
    # 창 단추
    gy = rect.top() + 37 * s
    xr = rect.right() - 34 * s
    p.setPen(QPen(QColor("#55555C"), 1.6 * s))
    p.drawLine(QPointF(xr - 8 * s, gy - 8 * s), QPointF(xr + 8 * s, gy + 8 * s))
    p.drawLine(QPointF(xr - 8 * s, gy + 8 * s), QPointF(xr + 8 * s, gy - 8 * s))
    p.setBrush(Qt.NoBrush)
    p.drawRect(QRectF(xr - 66 * s, gy - 8 * s, 16 * s, 16 * s))
    p.drawLine(QPointF(xr - 126 * s, gy), QPointF(xr - 110 * s, gy))
    # 메뉴 줄
    p.fillRect(QRectF(rect.left(), rect.top() + 72 * s, rect.width(), 46 * s), QColor("#FFFFFF"))
    mx = rect.left() + 26 * s
    for m in tr("np_menu"):
        text(p, QRectF(mx, rect.top() + 72 * s, 120 * s, 46 * s), m, 21 * s, "#2B2B30", Qt.AlignLeft | Qt.AlignVCenter,
             QFont.Normal, False)
        mx += text_size(m, 21 * s, QFont.Normal)[0] + 34 * s
    p.fillRect(QRectF(rect.left(), rect.top() + 118 * s, rect.width(), 1.5 * s), QColor("#E2E2E6"))
    # 본문
    y = rect.top() + 150 * s
    pw = None
    px = 30 * s
    lh = px * 1.75
    lines = tr("np_text")
    for i, ln in enumerate(lines):
        p.setFont(font(px, QFont.Normal, mono=True))
        p.setPen(QColor("#1E1E22"))
        p.drawText(QRectF(rect.left() + 34 * s, y, rect.width() - 60 * s, lh), Qt.AlignLeft | Qt.AlignVCenter, ln)
        if i == 4:
            w = QFontMetricsF(p.font()).horizontalAdvance(ln)
            pw = QRectF(rect.left() + 34 * s, y, w, lh)
            if (t * 2) % 1 < 0.55:
                p.fillRect(QRectF(rect.left() + 34 * s + w + 3 * s, y + 6 * s, 2.5 * s, lh - 12 * s), QColor("#1E1E22"))
        y += lh
    # 상태 줄
    p.fillRect(QRectF(rect.left(), rect.bottom() - 40 * s, rect.width(), 40 * s), QColor("#F3F3F5"))
    text(p, QRectF(rect.left() + 26 * s, rect.bottom() - 40 * s, rect.width() - 52 * s, 40 * s),
         "Ln 5, Col 38      100%      UTF-8", 18 * s, "#66666E", Qt.AlignRight | Qt.AlignVCenter, QFont.Normal, False)
    p.restore()
    return pw


def sc_autosave(p, L, t, D):
    draw_bg(p, L, t)
    n = SH.ntype
    t0, t1 = 0.5, 0.5 + 3.4 * (D / 9.0)
    if t < t1 + 0.4:
        i = int(round(n * clamp((t - t0) / (t1 - t0))))
        img = SH[f"type_{i:03d}"]
    else:
        img = SH["type_saved"]
    z = lerp(1.0, 1.32, ease(prog(t, 0.2, t1)))
    fz = (1200, 380)
    ts = t1 + 0.5
    if t > ts:
        u = ease(prog(t, ts, ts + 0.9))
        z = lerp(1.32, 1.18, u)
        fz = (lerp(1200, 1600, u), lerp(380, 1000, u))
    if L.portrait:
        z, fz = 1.6, (950, 420)
    m = draw_window(p, L.win, img, False, z, fz)
    # 저장됨 강조
    ra = window_alpha(t, ts + 0.6, ts + 1.0)
    if ra > 0 and not L.portrait:
        a, b = m(1720, 1104), m(1880, 1140)
        r = QRectF(a, b)
        if r.right() > L.win.right() - 10:
            r.moveRight(L.win.right() - 20)
        ring(p, r, ra)
        lab = "✓ " + tr("saved")
        lw, _ = text_size(lab, 30, QFont.Bold)
        lr = QRectF(r.right() - lw - 40, r.top() - 76, lw + 40, 54)
        rrect(p, lr, 27, fill=col(PEACH2, ra))
        text(p, lr, lab, 30, WHITE, Qt.AlignCenter, QFont.Bold, False, ra)
    # 암호화 카드
    ca = window_alpha(t, D * 0.6, D * 0.6 + 0.6)
    if ca > 0:
        if L.portrait:
            cr = QRectF(90, 1010, 900, 470)
        else:
            cr = QRectF(L.win.right() - 860, L.win.top() + 150, 820, 430)
        cr.translate((1 - eout(prog(t, D * 0.6, D * 0.6 + 0.6))) * 80, 0)
        draw_cipher_card(p, cr, ca, t)
    if not L.portrait:
        side_title(p, L, t, 1, "t1", [("Ctrl+N", "k_new", 0.2)])
    else:
        side_title(p, L, t, 1, "t1", [("Ctrl+N", "k_new", 0.2)])
    caption(p, L, t, [(0.3, D * 0.6, "c1a"), (D * 0.6, D - 0.1, "c1b")])


def draw_cipher_card(p, cr, a, t):
    shadow(p, cr, 22, a * 1.5, 30, 14)
    rrect(p, cr, 22, fill=col(INK, 0.97 * a))
    s = cr.width() / 820
    text(p, QRectF(cr.left() + 36 * s, cr.top() + 26 * s, cr.width() - 72 * s, 40 * s), tr("on_disk"), 26 * s,
         QColor("#B9B2C2"), Qt.AlignLeft | Qt.AlignVCenter, QFont.Normal, False, a)
    text(p, QRectF(cr.left() + 36 * s, cr.top() + 70 * s, cr.width() - 72 * s, 44 * s),
         "notes\\20261115-143205-a1b2.own", 28 * s, PEACH, Qt.AlignLeft | Qt.AlignVCenter, QFont.Bold, False, a, mono=True)
    rnd = random.Random(7)
    rows = 6
    shown = int(rows * 32 * clamp(prog(t, 0, 1) if False else 1))
    for r in range(rows):
        hexs = " ".join(f"{rnd.randrange(256):02x}" for _ in range(16))
        text(p, QRectF(cr.left() + 36 * s, cr.top() + (132 + r * 40) * s, cr.width() - 72 * s, 40 * s), hexs, 24 * s,
             QColor("#8F86A0"), Qt.AlignLeft | Qt.AlignVCenter, QFont.Normal, False, a, mono=True)
    # 자물쇠 + AES-256
    br = QRectF(cr.right() - 250 * s, cr.top() + 22 * s, 214 * s, 52 * s)
    rrect(p, br, 26 * s, fill=col(PLUM2, a))
    draw_lock(p, QPointF(br.left() + 34 * s, br.center().y()), 15 * s, a)
    text(p, br.adjusted(52 * s, 0, 0, 0), "AES-256", 24 * s, WHITE, Qt.AlignVCenter | Qt.AlignLeft, QFont.Bold, False, a)
    del shown


def draw_lock(p, c, s, a=1.0, color=WHITE):
    p.save()
    p.setPen(QPen(col(color, a), s * 0.22))
    p.setBrush(Qt.NoBrush)
    p.drawArc(QRectF(c.x() - s * 0.45, c.y() - s * 1.0, s * 0.9, s * 1.1), 0, 180 * 16)
    p.setPen(Qt.NoPen)
    p.setBrush(col(color, a))
    p.drawRoundedRect(QRectF(c.x() - s * 0.7, c.y() - s * 0.42, s * 1.4, s * 1.05), s * 0.18, s * 0.18)
    p.restore()


def sc_invisible(p, L, t, D):
    draw_bg(p, L, t)
    W, H = L.W, L.H
    k = D / 11.0
    if L.portrait:
        a = window_alpha(t, 0, 0.5)
        text(p, QRectF(60, 150, W - 120, 50), "02 / 07", 34, PEACH2, Qt.AlignHCenter, QFont.Bold, False, a)
        tpx = 76
        while text_size(tr("t2"), tpx, QFont.Bold)[0] > W - 140 and tpx > 50:  # 영어 제목이 한 줄에 들어가게
            tpx -= 2
        text(p, QRectF(60, 206, W - 120, 100), tr("t2"), tpx, INK, Qt.AlignHCenter, QFont.Bold, False, a)
        pl = QRectF(60, 400, 960, 540)
        pr = QRectF(60, 1030, 960, 540)
    else:
        a = window_alpha(t, 0, 0.5)
        text(p, QRectF(0, 60, W, 50), "02 / 07", 28, PEACH2, Qt.AlignHCenter, QFont.Bold, False, a)
        text(p, QRectF(0, 100, W, 90), tr("t2"), 62, INK, Qt.AlignHCenter, QFont.Bold, False, a)
        pl = QRectF(70, 250, 860, 484)
        pr = QRectF(990, 250, 860, 484)
    main = SH["main"]

    def panel(r, u, with_app, share):
        if u <= 0:
            return
        p.save()
        p.setOpacity(u)
        off = (1 - eout(u)) * 60
        r = r.translated(0, off)
        shadow(p, r, 18, 1.2, 26, 12)
        path = rrect(p, r, 18, fill=QColor("#000"))
        p.setClipPath(path)
        draw_desktop(p, r, t)
        s = r.width() / 1920
        appr = QRectF(r.left() + 600 * s, r.top() + 90 * s, 1260 * s, (38 + 1260 * 1140 / 1920) * s * 1.0)
        if with_app:
            au = eout(prog(t, 0.9 * k, 1.5 * k))
            if au > 0:
                draw_window(p, appr.translated(0, (1 - au) * 40 * s), main, False, 1.0, None, au, shadow_k=0.8)
        else:
            # 그 자리 — 아무것도 없음 (점선 윤곽으로 강조)
            ga = window_alpha(t, 6.0 * k, 6.6 * k) * (0.55 + 0.45 * math.sin(t * 4))
            if ga > 0:
                pen = QPen(col(PEACH, ga), 4, Qt.DashLine)
                rrect(p, appr, 12 * s * 1.5, pen=pen)
        if share:
            sa = window_alpha(t, 2.3 * k, 2.6 * k)
            p.setPen(QPen(col(RED, sa), 8))
            p.setBrush(Qt.NoBrush)
            p.drawRect(r.adjusted(4, 4, -4, -4))
            fl = prog(t, 3.3 * k, 3.65 * k)
            if 0 < fl < 1:
                p.fillRect(r, QColor(255, 255, 255, int(220 * (1 - fl))))
        p.restore()
        return r

    ul = prog(t, 0.2 * k, 0.9 * k)
    ur = prog(t, 1.6 * k, 2.3 * k)
    rl = panel(pl, ul, True, False)
    rr = panel(pr, ur, False, True)
    # 라벨
    for r, u, key, red in ((pl, ul, "my_screen", False), (pr, ur, "their_screen", True)):
        if u <= 0:
            continue
        lab = ("●  " if red else "") + tr(key)
        px = 32 if not L.portrait else 34
        lw, _ = text_size(lab, px, QFont.Bold)
        if L.portrait:
            lr = QRectF(r.left() + 24, r.top() + 22, lw + 50, 62)
        else:
            lr = QRectF(r.center().x() - (lw + 50) / 2, r.bottom() + 34, lw + 50, 64)
        aa = eout(u)
        shadow(p, lr, 31, 0.8 * aa, 12, 6)
        rrect(p, lr, 31, fill=col(RED if red else INK, aa))
        text(p, lr, lab, px, WHITE, Qt.AlignCenter, QFont.Bold, False, aa)
    # 카메라 표시 (오른쪽)
    del rl, rr
    caption(p, L, t, [(0.4 * k, 5.2 * k, "c2a"), (5.2 * k, D - 0.1, "c2b")])


def sc_secret(p, L, t, D):
    draw_bg(p, L, t)
    k = D / 8.0
    tc = 2.0 * k
    img = SH["secret_cover"] if t < tc + 0.12 else SH["secret_open"]
    if t < tc + 0.12:
        z, f = lerp(1.0, 1.08, ease(prog(t, 0, tc))), (1180, 600)
    else:
        u = ease(prog(t, tc + 0.2, tc + 1.2))
        z, f = lerp(1.08, 1.55, u), (lerp(1180, 1090, u), lerp(600, 300, u))
    if L.portrait:
        if t < tc + 0.12:
            z, f = lerp(1.2, 1.3, ease(prog(t, 0, tc))), (1180, 600)
        else:
            z, f = lerp(1.3, 1.7, u), (lerp(1180, 860, u), lerp(600, 400, u))
    m = draw_window(p, L.win, img, False, z, f)
    # 커서가 가림막을 누름
    if t < tc + 0.8:
        target = m(1180, 630)
        start = QPointF(L.win.right() - 60, L.win.bottom() - 40)
        u = ease(prog(t, 0.5 * k, tc - 0.15))
        pos = QPointF(lerp(start.x(), target.x(), u), lerp(start.y(), target.y(), u))
        ca = window_alpha(t, 0.4 * k, 0.7 * k, tc + 0.4, tc + 0.8)
        ripple(p, target, prog(t, tc, tc + 0.5))
        draw_cursor(p, pos, 1.8, ca)
    # 클립보드 자동 비움 카드
    t2 = 4.4 * k
    ca = window_alpha(t, t2, t2 + 0.5)
    if ca > 0:
        if L.portrait:
            cr = QRectF(140, 1180, 800, 200)
        else:
            cr = QRectF(L.win.right() - 760, L.win.bottom() - 250, 720, 200)
        cr.translate(0, (1 - eout(prog(t, t2, t2 + 0.5))) * 40)
        shadow(p, cr, 22, 1.4 * ca, 26, 12)
        rrect(p, cr, 22, fill=col(INK, 0.97 * ca))
        # 비워지는 고리
        c = QPointF(cr.left() + 100, cr.center().y())
        u = prog(t, t2 + 0.4, D - 0.3)
        p.save()
        p.setPen(QPen(col("#3A3540", ca), 12))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(c, 52, 52)
        p.setPen(QPen(col(PEACH, ca), 12, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(c.x() - 52, c.y() - 52, 104, 104), 90 * 16, int(-360 * 16 * (1 - u)))
        p.restore()
        draw_clipboard_glyph(p, c, 30, ca)
        text(p, QRectF(cr.left() + 180, cr.top(), cr.width() - 200, cr.height()), tr("clip_auto"), 34, WHITE,
             Qt.AlignLeft | Qt.AlignVCenter, QFont.Bold, True, ca)
    side_title(p, L, t, 3, "t3", [("Enter", "k_reveal", tc - 0.1), ("Ctrl+C", "k_copy", t2 - 0.3)])
    caption(p, L, t, [(0.3, t2, "c3a"), (t2, D - 0.1, "c3b")])


def draw_clipboard_glyph(p, c, s, a):
    p.save()
    p.setPen(QPen(col(WHITE, a), s * 0.12))
    p.setBrush(Qt.NoBrush)
    p.drawRoundedRect(QRectF(c.x() - s * 0.5, c.y() - s * 0.6, s, s * 1.25), s * 0.12, s * 0.12)
    p.setBrush(col(WHITE, a))
    p.drawRoundedRect(QRectF(c.x() - s * 0.25, c.y() - s * 0.75, s * 0.5, s * 0.3), s * 0.08, s * 0.08)
    p.restore()


def sc_copy(p, L, t, D):
    draw_bg(p, L, t)
    k = D / 8.0
    z = lerp(1.0, 1.45, ease(prog(t, 0.2, 2.0 * k)))
    if L.portrait:
        z *= 1.15
    draw_window(p, L.win, SH["rich"], False, z, (1120, 330))
    html = SH_RICH_HTML[LANG]
    ta, tb = 1.9 * k, 4.4 * k
    for i, (t0, key, plain) in enumerate(((ta, "paste_rich", False), (tb, "paste_plain", True))):
        a = window_alpha(t, t0, t0 + 0.5)
        if a <= 0:
            continue
        if L.portrait:
            cr = QRectF(90, 1000 + i * 0, 900, 470) if False else QRectF(90 + i * 0, 900 + i * 300, 900, 280)
        else:
            cr = QRectF(L.win.left() + 60 + i * 600, L.win.bottom() - 340, 560, 300)
        cr.translate(0, (1 - eout(prog(t, t0, t0 + 0.5))) * 50)
        shadow(p, cr, 20, 1.6 * a, 28, 14)
        rrect(p, cr, 20, fill=col(WHITE, a), pen=QPen(col("#E3DDE8", a), 2))
        hr = QRectF(cr.left(), cr.top(), cr.width(), 64)
        rrect(p, hr, 20, fill=col(PLUM if not plain else INK, a))
        p.fillRect(QRectF(cr.left(), cr.top() + 40, cr.width(), 24), col(PLUM if not plain else INK, a))
        text(p, hr.adjusted(26, 0, -20, 0), tr(key), 28, WHITE, Qt.AlignLeft | Qt.AlignVCenter, QFont.Bold, False, a)
        doc = QTextDocument()
        if plain:
            d = QTextDocument()
            d.setHtml(html)
            doc.setDefaultFont(font(22, QFont.Normal, mono=True))
            doc.setPlainText(d.toPlainText())
        else:
            doc.setDefaultFont(font(22, QFont.Normal))
            doc.setHtml(html)
        doc.setTextWidth(cr.width() - 56)
        p.save()
        p.setOpacity(a)
        p.translate(cr.left() + 28, cr.top() + 82)
        p.setClipRect(QRectF(0, 0, cr.width() - 56, cr.height() - 96))
        doc.drawContents(p)
        p.restore()
    side_title(p, L, t, 4, "t4", [("Ctrl+C", "k_rich", ta - 0.35), ("Ctrl+Shift+C", "k_plain", tb - 0.35)])
    caption(p, L, t, [(0.3, tb, "c4a"), (tb, D - 0.1, "c4b")])


SH_RICH_HTML = {
    "ko": "<h3>출시 체크리스트</h3><p><b>아이콘</b> 최종본 확인 — <span style='color:#9B4DB5'><b>16px까지</b></span> 점검</p>"
          "<ul><li><b>스크린샷</b> 새로 찍기</li><li>홈페이지 문구 <i>한 번 더</i> 읽기</li></ul>",
    "en": "<h3>Launch checklist</h3><p>Final <b>icon</b> check — test <span style='color:#9B4DB5'><b>down to 16px</b></span></p>"
          "<ul><li>Retake <b>screenshots</b></li><li>Read the homepage copy <i>once more</i></li></ul>",
}


def sc_code(p, L, t, D):
    draw_bg(p, L, t, dark=True)
    k = D / 8.0
    a1, a2, tj = 2.6 * k, 4.4 * k, 4.4 * k
    if t < a1:
        img, z, f = SH["html"], lerp(1.0, 1.55, ease(prog(t, 0.2, a1))), (1090, 260)
        mix, img2 = 0, None
    elif t < tj + 0.25:
        img, z, f = SH["json_raw"], 1.55, (1090, 260)
        mix, img2 = 0, None
    else:
        img, img2 = SH["json_raw"], SH["json_pretty"]
        mix = ease(prog(t, tj + 0.25, tj + 0.7))
        z, f = 1.55, (1090, lerp(260, 330, mix))
    if L.portrait:
        z *= 1.1
    draw_window(p, L.win, img, True, z, f, 1.0, img2, mix)
    side_title(p, L, t, 5, "t5", [("Ctrl+Shift+N", "k_code", 0.3), ("Ctrl+Alt+J", "k_json", tj - 0.2)], dark=True)
    caption(p, L, t, [(0.3, a2, "c5a"), (a2, D - 0.1, "c5b")], dark=True)


def sc_capture(p, L, t, D):
    draw_bg(p, L, t)
    k = D / 9.0
    sw = 3.0 * k
    win = L.win
    if t < sw + 0.5:
        # 바탕화면에서 영역 고르기
        a = 1 - ease(prog(t, sw, sw + 0.5))
        p.save()
        p.setOpacity(a)
        shadow(p, win, 16, 1.2)
        path = rrect(p, win, 16, fill=QColor("#000"))
        p.setClipPath(path)
        draw_desktop(p, win, t)
        dim = window_alpha(t, 0.5 * k, 0.8 * k)
        s = win.width() / 1920
        x0, y0 = win.left() + 170 * s, win.top() + 140 * s
        x1, y1 = win.left() + 1120 * s, win.top() + 740 * s
        u = ease(prog(t, 0.9 * k, 2.2 * k))
        cx, cy = lerp(x0, x1, u), lerp(y0, y1, u)
        sel = QRectF(QPointF(x0, y0), QPointF(cx, cy))
        if dim > 0:
            outer = QPainterPath()
            outer.addRect(win)
            inner = QPainterPath()
            if u > 0:
                inner.addRect(sel)
            p.fillPath(outer.subtracted(inner), QColor(10, 6, 16, int(140 * dim)))
            if u > 0:
                p.setPen(QPen(col(PEACH, dim), 3, Qt.DashLine))
                p.setBrush(Qt.NoBrush)
                p.drawRect(sel)
                lab = f"{int(sel.width() / s)} × {int(sel.height() / s)}"
                lw, _ = text_size(lab, 24, QFont.Bold)
                lr = QRectF(sel.right() - lw - 28, sel.bottom() + 12, lw + 28, 40)
                rrect(p, lr, 20, fill=col(INK, 0.9 * dim))
                text(p, lr, lab, 24, WHITE, Qt.AlignCenter, QFont.Bold, False, dim)
        fl = prog(t, 2.45 * k, 2.8 * k)
        if 0 < fl < 1:
            p.fillRect(win, QColor(255, 255, 255, int(220 * (1 - fl))))
        p.restore()
        if t < 2.4 * k:
            draw_cursor(p, QPointF(cx if u > 0 else lerp(win.right() - 100, x0, ease(prog(t, 0.2 * k, 0.9 * k))),
                                   cy if u > 0 else lerp(win.bottom() - 100, y0, ease(prog(t, 0.2 * k, 0.9 * k)))), 1.8,
                        window_alpha(t, 0.1 * k, 0.3 * k))
    if t > sw:
        a = ease(prog(t, sw, sw + 0.5))
        u = ease(prog(t, sw + 0.3, D * 0.62))
        f = (lerp(900, 920, u), lerp(360, 560, u))
        z = lerp(1.05, 1.35, u)
        if L.portrait:
            z *= 1.1
        m = draw_window(p, win, SH["media"], False, z, f, a)
        t2 = 5.4 * k
        ra = window_alpha(t, t2 + 0.2, t2 + 0.6)
        if ra > 0:
            r = QRectF(m(672, 621), m(1166, 872))
            ring(p, r, ra, RED, 6, 14)
            lab = "●  REC  ≤ 3:00"
            lw, _ = text_size(lab, 26, QFont.Bold)
            lr = QRectF(r.left(), r.top() - 66, lw + 40, 50)
            rrect(p, lr, 25, fill=col(RED, ra))
            text(p, lr, lab, 26, WHITE, Qt.AlignCenter, QFont.Bold, False, ra)
    side_title(p, L, t, 6, "t6", [("Ctrl+Alt+S", "k_shot", 0.45 * k), ("Ctrl+Alt+R", "k_rec", 5.2 * k)])
    caption(p, L, t, [(0.3, 5.4 * k, "c6a"), (5.4 * k, D - 0.1, "c6b")])


def sc_hotkeys(p, L, t, D):
    draw_bg(p, L, t)
    k = D / 10.0
    win = L.win
    tm, tb_, tk = 1.4 * k, 4.4 * k, 6.3 * k
    if t < tb_ + 0.5:
        a = 1 - ease(prog(t, tb_, tb_ + 0.5))
        p.save()
        p.setOpacity(a)
        shadow(p, win, 16, 1.2)
        path = rrect(p, win, 16, fill=QColor("#000"))
        p.setClipPath(path)
        draw_desktop(p, win, t, True, "clip", select_line=1, sel_u=ease(prog(t, 0.2 * k, 0.9 * k)) * 1.0)
        # 알림
        na = window_alpha(t, tm + 0.3, tm + 0.7, tb_ - 0.4, tb_)
        if na > 0:
            s = win.width() / 1920
            nr = QRectF(win.right() - 760 * s, win.bottom() - 330 * s, 720 * s, 200 * s)
            nr.translate((1 - eout(prog(t, tm + 0.3, tm + 0.7))) * 120 * s, 0)
            shadow(p, nr, 16 * s, 1.4 * na, 22 * s, 10 * s)
            rrect(p, nr, 16 * s, fill=col("#24212A", 0.98 * na))
            draw_icon(p, QPointF(nr.left() + 70 * s, nr.center().y()), 76 * s, na)
            text(p, QRectF(nr.left() + 130 * s, nr.top() + 36 * s, nr.width() - 150 * s, 50 * s), tr("toast"), 32 * s,
                 WHITE, Qt.AlignLeft | Qt.AlignVCenter, QFont.Bold, False, na)
            text(p, QRectF(nr.left() + 130 * s, nr.top() + 100 * s, nr.width() - 150 * s, 50 * s), tr("toast_sub"),
                 26 * s, QColor("#B9B2C2"), Qt.AlignLeft | Qt.AlignVCenter, QFont.Normal, False, na)
        p.restore()
    if t > tb_:
        a = ease(prog(t, tb_, tb_ + 0.5))
        z = 1.0 if not L.portrait else 1.25
        f = (700, 600) if not L.portrait else (400, 600)
        m = draw_window(p, win, SH["clip"], False, z, f, a)
        ra = window_alpha(t, tb_ + 0.5, tb_ + 0.9, tk - 0.3, tk)
        if ra > 0:
            ring(p, QRectF(m(22, 850), m(415, 930)), ra, PEACH2, 5, 12)
        pa = window_alpha(t, tk, tk + 0.35)
        if pa > 0:
            p.save()
            p.fillRect(win, QColor(20, 10, 30, int(70 * pa)))
            pal = SH["palette_l"]
            pk = m.k
            tl = m(1920 / 2 - pal.width() / 2, 120)
            sc = lerp(0.96, 1.0, eout(prog(t, tk, tk + 0.35)))
            pr = QRectF(tl.x(), tl.y(), pal.width() * pk, pal.height() * pk)
            if L.portrait:
                pr = QRectF(win.left() + 30, win.top() + 90, win.width() - 60, (win.width() - 60) * pal.height() / pal.width())
            c = pr.center()
            pr = QRectF(c.x() - pr.width() * sc / 2, c.y() - pr.height() * sc / 2, pr.width() * sc, pr.height() * sc)
            shadow(p, pr, 14, 1.6 * pa, 30, 14)
            p.setOpacity(pa)
            p.setRenderHint(QPainter.SmoothPixmapTransform)
            p.drawImage(pr, pal)
            p.restore()
    chips = [("Ctrl+Alt+M", "k_clip", tm), ("Ctrl+K", "k_palette", tk - 0.3)]
    if not L.portrait:
        chips = [("Ctrl+Alt+M", "k_clip", tm), ("Ctrl+K", "k_palette", tk - 0.3), ("Ctrl+Alt+N", "k_quick", None)]
    cy = side_title(p, L, t, 7, "t7", chips)
    if not L.portrait:
        a = window_alpha(t, 0.9, 1.4)
        text(p, QRectF(90, cy - 6, 440, 40), "↳ " + tr("tray"), 24, PLUM, Qt.AlignLeft | Qt.AlignTop, QFont.Bold, False, a)
    caption(p, L, t, [(0.3, tk - 0.3, "c7a"), (tk - 0.3, D - 0.1, "c7b")])


def sc_outro(p, L, t, D):
    W, H = L.W, L.H
    full = QRectF(0, 0, W, H)
    g = QLinearGradient(0, 0, W, H)
    g.setColorAt(0, PLUM)
    g.setColorAt(1, PLUM2)
    p.fillRect(full, g)
    for cx, cy, r, c, a in ((0.85, 0.9, 0.7, PEACH, 0.35), (0.1, 0.1, 0.5, QColor("#5B2C70"), 0.5)):
        rg = QRadialGradient(QPointF(W * cx + 30 * math.sin(t * 0.4), H * cy), max(W, H) * r)
        rg.setColorAt(0, col(c, a))
        rg.setColorAt(1, col(c, 0))
        p.fillRect(full, rg)
    a0 = 1 - ease(prog(t, 0, 0.5))
    if a0 > 0:  # 앞 장면에서 넘어올 때 흰 플래시 없이 부드럽게
        p.fillRect(full, col(LIGHT, a0))
    por = L.portrait
    t = t * max(1.0, 4.0 / D)  # 짧은 아웃트로(쇼츠)는 같은 동작을 빠르게
    u = eout(prog(t, 0.2, 0.9))
    cy = (250 if not por else 520)
    draw_icon(p, QPointF(W / 2, cy), lerp(120, 170, u) if not por else lerp(180, 250, u), u)
    a1 = window_alpha(t, 0.6, 1.2)
    ty = cy + (120 if not por else 180)
    px = 88 if not por else 80
    tag = tr("tag")
    if por:
        tag = tag.replace(", ", ",\n").replace(". ", ".\n")
    text(p, QRectF(60, ty + (1 - a1) * 20, W - 120, px * 2.8), tag, px, WHITE, Qt.AlignHCenter | Qt.AlignTop,
         QFont.Bold, True, a1)
    _, th = text_size(tag, px, QFont.Bold, W - 120)
    a2 = window_alpha(t, 1.4, 1.9)
    uy = ty + th + (50 if not por else 80)
    lab = URL
    lw, _ = text_size(lab, 40, QFont.Bold)
    ur = QRectF(W / 2 - lw / 2 - 40, uy, lw + 80, 76)
    rrect(p, ur, 38, fill=col(WHITE, a2))
    text(p, ur, lab, 40, PLUM, Qt.AlignCenter, QFont.Bold, False, a2)
    a3 = window_alpha(t, 2.0, 2.5)
    sy = uy + 120
    lab = tr("free_big")
    lw, _ = text_size(lab, 40, QFont.Bold)
    sr = QRectF(W / 2 - lw / 2 - 36, sy, lw + 72, 70)
    rrect(p, sr, 35, fill=col(PEACH2, a3))
    text(p, sr, lab, 40, WHITE, Qt.AlignCenter, QFont.Bold, False, a3)
    text(p, QRectF(0, sy + 90, W, 50), tr("free_small"), 32, QColor("#F3E6F7"), Qt.AlignHCenter | Qt.AlignTop,
         QFont.Normal, False, a3)


# ====================================================================== 타임라인
def timeline(kind):
    """[(이름, 함수, 길이)]"""
    if kind == "shorts":
        return [("hook", sc_hook, 6.0), ("invisible", sc_invisible, 8.0), ("secret", sc_secret, 7.0),
                ("autosave", sc_autosave, 6.0), ("outro", sc_outro, 3.0)]
    return [("hook", sc_hook, 7.0), ("autosave", sc_autosave, 9.0), ("invisible", sc_invisible, 11.0),
            ("secret", sc_secret, 8.0), ("copy", sc_copy, 8.0), ("code", sc_code, 8.0),
            ("capture", sc_capture, 9.0), ("hotkeys", sc_hotkeys, 10.0), ("outro", sc_outro, 9.0)]


def total(kind):
    return sum(d for _, _, d in timeline(kind))


XFADE = 0.35


class Renderer:
    def __init__(self, kind, lang):
        global LANG, SH
        LANG = lang
        SH = Shots(lang)
        self.kind = kind
        self.L = Layout(portrait=(kind == "shorts"))
        self.tl = timeline(kind)
        self.dur = total(kind)
        self.prev = None

    def frame(self, t):
        L = self.L
        img = QImage(L.W, L.H, QImage.Format_RGB32)
        p = QPainter(img)
        p.setRenderHint(QPainter.Antialiasing)
        p.setRenderHint(QPainter.TextAntialiasing)
        p.setRenderHint(QPainter.SmoothPixmapTransform)
        start = 0.0
        for i, (name, fn, d) in enumerate(self.tl):
            if t < start + d or i == len(self.tl) - 1:
                fn(p, L, t - start, d)
                # 다음 장면과 겹쳐 사라지기 (장면 끝 XFADE초)
                if i + 1 < len(self.tl) and t > start + d - XFADE and self.tl[i + 1][0] != "outro" and name != "hook":
                    u = ease(prog(t, start + d - XFADE, start + d))
                    p.save()
                    p.setOpacity(u)
                    layer = QImage(L.W, L.H, QImage.Format_ARGB32_Premultiplied)
                    lp = QPainter(layer)
                    lp.setRenderHint(QPainter.Antialiasing)
                    lp.setRenderHint(QPainter.TextAntialiasing)
                    lp.setRenderHint(QPainter.SmoothPixmapTransform)
                    self.tl[i + 1][1](lp, L, 0.0, self.tl[i + 1][2])
                    lp.end()
                    p.drawImage(0, 0, layer)
                    p.restore()
                if name == "hook" and t > start + d - XFADE and i + 1 < len(self.tl):
                    u = ease(prog(t, start + d - XFADE, start + d))
                    p.fillRect(QRectF(0, 0, L.W, L.H), col(LIGHT, u))
                break
            start += d
        # 끝 0.4초 페이드아웃은 하지 않음 (종료 화면용으로 마지막 장면 유지)
        p.end()
        return img


# ====================================================================== 자막 파일
def captions_timeline(kind="main"):
    """[(시작, 끝, 키)] — 화면 자막과 같은 시각."""
    out = []
    start = 0.0
    for name, fn, d in timeline(kind):
        k = d / {"hook": 7.0, "autosave": 9.0, "invisible": 11.0, "secret": 8.0, "copy": 8.0, "code": 8.0,
                 "capture": 9.0, "hotkeys": 10.0, "outro": 9.0}[name]
        s = start
        if name == "hook":
            out += [(s + 0.1 * k, s + 3.6 * k, "hook"), (s + 3.75 * k, s + 4.95 * k, "shh"), (s + 5.4 * k, s + d, "logo")]
        elif name == "autosave":
            out += [(s + 0.3, s + d * 0.6, "c1a"), (s + d * 0.6, s + d - 0.1, "c1b")]
        elif name == "invisible":
            out += [(s + 0.4 * k, s + 5.2 * k, "c2a"), (s + 5.2 * k, s + d - 0.1, "c2b")]
        elif name == "secret":
            out += [(s + 0.3, s + 4.4 * k, "c3a"), (s + 4.4 * k, s + d - 0.1, "c3b")]
        elif name == "copy":
            out += [(s + 0.3, s + 4.4 * k, "c4a"), (s + 4.4 * k, s + d - 0.1, "c4b")]
        elif name == "code":
            out += [(s + 0.3, s + 4.4 * k, "c5a"), (s + 4.4 * k, s + d - 0.1, "c5b")]
        elif name == "capture":
            out += [(s + 0.3, s + 5.4 * k, "c6a"), (s + 5.4 * k, s + d - 0.1, "c6b")]
        elif name == "hotkeys":
            out += [(s + 0.3, s + 6.3 * k - 0.3, "c7a"), (s + 6.3 * k - 0.3, s + d - 0.1, "c7b")]
        elif name == "outro":
            out += [(s + 0.6, s + 4.0, "tag"), (s + 4.0, s + 6.5, "release"), (s + 6.5, s + d, "url")]
        start += d
    return out


def srt_time(x):
    ms = int(round(x * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def wrap_sub(txt, lang):
    """자막 한 줄 길이: 라틴 42자, 한국어 22자, 일본어·중국어 16자. 넘으면 가운데 가까운 띄어쓰기에서 두 줄로."""
    limit = {"en": 42, "ko": 22}.get(lang, 16)
    out = []
    for ln in txt.split("\n"):
        if len(ln) <= limit or " " not in ln:
            out.append(ln)
            continue
        mid = len(ln) / 2
        cut = min((i for i, c in enumerate(ln) if c == " "),
                  key=lambda i: abs(i - mid) - (len(ln) * 0.3 if ln[i - 1] in ",.?…" else 0))
        out += [ln[:cut], ln[cut + 1:]]
    return "\n".join(out)


def write_srts():
    d = HERE / "subtitles"
    d.mkdir(exist_ok=True)
    tl = captions_timeline()
    for lang in ("ko", "en", "ja", "zh-Hans"):
        lines = []
        for i, (a, b, key) in enumerate(tl, 1):
            txt = URL if key == "url" else TXT[key].get(lang)
            txt = wrap_sub(txt, lang)
            lines.append(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{txt}\n")
        (d / f"hushpad_promo.{lang}.srt").write_text("\n".join(lines), "utf-8-sig")
    print("srt ok", len(tl))


# ====================================================================== 썸네일
def thumbnail(lang):
    global LANG, SH
    LANG = lang
    SH = Shots(lang)
    W, H = 1280, 720
    img = QImage(W, H, QImage.Format_RGB32)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)
    p.setRenderHint(QPainter.SmoothPixmapTransform)
    g = QLinearGradient(0, 0, W, H)
    g.setColorAt(0, QColor("#5E2B76"))
    g.setColorAt(1, PLUM2)
    p.fillRect(0, 0, W, H, g)
    rg = QRadialGradient(QPointF(W * 0.95, H * 1.0), 700)
    rg.setColorAt(0, col(PEACH, 0.55))
    rg.setColorAt(1, col(PEACH, 0))
    p.fillRect(0, 0, W, H, rg)
    # 오른쪽: 창 — 왼쪽 절반은 보이고, 오른쪽 절반은 '캡처'에서 사라짐
    wr = QRectF(610, 150, 640, 38 * 0.5 + 640 * 1140 / 1920)
    p.save()
    p.translate(wr.center())
    p.rotate(-3)
    p.translate(-wr.center())
    clipL = QRectF(0, 0, wr.center().x(), H)
    p.save()
    p.setClipRect(clipL)
    draw_window(p, wr, SH["main"], False, 1.0, None)
    p.restore()
    pen = QPen(col(WHITE, 0.95), 5, Qt.DashLine)
    p.save()
    p.setClipRect(QRectF(wr.center().x(), 0, W, H))
    rrect(p, wr, 14 * wr.width() / 1280, pen=pen)
    p.restore()
    p.setPen(QPen(PEACH, 6))
    p.drawLine(QPointF(wr.center().x(), wr.top() - 30), QPointF(wr.center().x(), wr.bottom() + 30))
    p.restore()
    # 라벨
    for key, red in (("my_screen", False), ("their_screen", True)):
        lab = ("● " if red else "") + tr(key)
        lw, _ = text_size(lab, 24, QFont.Bold)
        if red:
            lr = QRectF(min(wr.center().x() + 40, W - 30 - lw - 36), wr.bottom() + 40, lw + 36, 46)
        else:
            lr = QRectF(wr.left() + 20, wr.bottom() + 40, lw + 36, 46)
        rrect(p, lr, 23, fill=RED if red else INK)
        text(p, lr, lab, 24, WHITE, Qt.AlignCenter, QFont.Bold, False)
    # 왼쪽: 큰 문구
    draw_icon(p, QPointF(92, 92), 84)
    text(p, QRectF(150, 58, 400, 70), "Hushpad", 46, WHITE, Qt.AlignLeft | Qt.AlignVCenter, QFont.Bold, False)
    big = {"ko": ["캡처에", "안 찍히는", "메모장"], "en": ["The notepad", "screenshots", "can't see"]}[lang]
    px = 92 if lang == "ko" else 78
    y = 200
    for i, ln in enumerate(big):
        c = PEACH if i == 1 else WHITE
        text(p, QRectF(60, y + 4, 600, px * 1.3), ln, px, QColor(30, 0, 40, 110), Qt.AlignLeft | Qt.AlignTop, QFont.Black, False)
        text(p, QRectF(56, y, 600, px * 1.3), ln, px, c, Qt.AlignLeft | Qt.AlignTop, QFont.Black, False)
        y += px * 1.18
    sub = {"ko": "자동 저장 · 모두 암호화", "en": "Auto-save · Everything encrypted"}[lang]
    text(p, QRectF(60, y + 22, 560, 50), sub, 34, QColor("#FFE3D3"), Qt.AlignLeft | Qt.AlignTop, QFont.Bold, False)
    p.end()
    out = HERE / f"thumbnail_{lang}.png"
    img.save(str(out))
    print("thumb", out)


# ====================================================================== 인코딩
AUDIO_SR, AUDIO_CHUNK = 48000, 4800   # 0.1초씩 보냄


def read_wav_pcm(path):
    """16비트 스테레오 48 kHz WAV → bytes (make_music.py가 만든 형식)."""
    import wave
    with wave.open(str(path), "rb") as w:
        if (w.getsampwidth(), w.getnchannels(), w.getframerate()) != (2, 2, AUDIO_SR):
            raise SystemExit(f"{path}: 48 kHz 16비트 스테레오 WAV가 아님")
        return w.readframes(w.getnframes())


class Encoder(QObject):
    """QVideoFrameInput(+QAudioBufferInput) → QMediaRecorder(MP4, H.264 + AAC).

    인코딩 메모 (PySide6 6.12, Windows): Qt의 FFmpeg에는 Media Foundation 인코더(h264_mf)만 있고,
    비트레이트·모드(CBR/ABR/품질) 설정과 상관없이 이 영상에서는 4~5 Mbps 근처에서 멈춘다(품질 100이 상한).
    대신 원본 프레임과 비교한 PSNR이 약 47 dB라 눈으로는 원본과 구분되지 않는다. H.265를 요청해도 H.264로 돌아감.
    ConstantQualityEncoding은 소리를 HE-AAC 16 kbps로 만들어 버려서, AverageBitRateEncoding(AAC-LC 192 kbps)을 쓴다.
    """
    def __init__(self, renderer, path, app, audio=None):
        super().__init__()
        from PySide6.QtMultimedia import (QMediaCaptureSession, QMediaFormat, QMediaRecorder, QVideoFrameInput,
                                          QAudioBufferInput, QAudioFormat)
        self.r, self.path, self.app = renderer, Path(path), app
        self.n = int(round(renderer.dur * FPS))
        self.i = 0
        self.pending = None
        self.done = False
        self.failed = None
        if self.path.exists():
            self.path.unlink()
        self.session = QMediaCaptureSession()
        self.input = QVideoFrameInput()
        self.session.setVideoFrameInput(self.input)
        # 소리 (배경 음악 WAV)
        self.ain = None
        self.ai, self.na, self.apending = 0, 0, None
        if audio:
            self.pcm = read_wav_pcm(audio)
            frames = min(len(self.pcm) // 4, int(round(renderer.dur * AUDIO_SR)))
            self.pcm = self.pcm[: frames * 4]
            self.na = (frames + AUDIO_CHUNK - 1) // AUDIO_CHUNK
            self.afmt = QAudioFormat()
            self.afmt.setSampleRate(AUDIO_SR)
            self.afmt.setChannelCount(2)
            self.afmt.setSampleFormat(QAudioFormat.Int16)
            self.ain = QAudioBufferInput()
            self.session.setAudioBufferInput(self.ain)
        self.rec = QMediaRecorder()
        self.session.setRecorder(self.rec)
        fmt = QMediaFormat(QMediaFormat.MPEG4)
        fmt.setVideoCodec(QMediaFormat.VideoCodec.H264)
        if self.ain:
            fmt.setAudioCodec(QMediaFormat.AudioCodec.AAC)
        self.rec.setMediaFormat(fmt)
        self.rec.setQuality(QMediaRecorder.VeryHighQuality)
        self.rec.setEncodingMode(QMediaRecorder.AverageBitRateEncoding)
        self.rec.setVideoBitRate(14_000_000 if renderer.L.W * renderer.L.H >= 1920 * 1080 else 10_000_000)
        if self.ain:
            self.rec.setAudioSampleRate(AUDIO_SR)
            self.rec.setAudioChannelCount(2)
            self.rec.setAudioBitRate(192_000)
        self.rec.setVideoFrameRate(FPS)
        self.rec.setVideoResolution(renderer.L.W, renderer.L.H)
        self.rec.setOutputLocation(QUrl.fromLocalFile(str(self.path)))
        self.rec.errorOccurred.connect(self._err)
        self.rec.recorderStateChanged.connect(self._state)
        self.input.readyToSendVideoFrame.connect(self.pump)
        if self.ain:
            self.ain.readyToSendAudioBuffer.connect(self.pump)
        self.kick = QTimer(self)
        self.kick.setInterval(20)
        self.kick.timeout.connect(self.pump)

    def _err(self, e, msg):
        self.failed = msg or str(e)
        print("ERROR", self.failed, flush=True)
        self.app.quit()

    def start(self):
        self.rec.record()
        self.kick.start()

    def pump(self):
        from PySide6.QtMultimedia import QVideoFrame
        if self.done:
            return
        from PySide6.QtCore import QByteArray
        from PySide6.QtMultimedia import QAudioBuffer
        budget = 6
        while (self.i < self.n or self.ai < self.na) and budget > 0:
            # 소리는 영상과 같은 시각까지 앞서 보내 둔다 (시간 순서대로 섞어서)
            if self.ai < self.na and (self.ai * AUDIO_CHUNK / AUDIO_SR <= self.i / FPS or self.i >= self.n):
                if self.apending is None:
                    a = self.ai * AUDIO_CHUNK * 4
                    self.apending = QAudioBuffer(QByteArray(self.pcm[a:a + AUDIO_CHUNK * 4]), self.afmt,
                                                 int(self.ai * AUDIO_CHUNK * 1_000_000 / AUDIO_SR))
                if not self.ain.sendAudioBuffer(self.apending):
                    return
                self.apending = None
                self.ai += 1
                continue
            if self.pending is None:
                img = self.r.frame(self.i / FPS)
                f = QVideoFrame(img)
                f.setStartTime(int(self.i * 1_000_000 / FPS))
                f.setEndTime(int((self.i + 1) * 1_000_000 / FPS))
                self.pending = f
            if not self.input.sendVideoFrame(self.pending):
                return  # 바쁨 — readyToSendVideoFrame 또는 타이머로 다시
            self.pending = None
            self.i += 1
            budget -= 1
            if self.i % 150 == 0:
                print(f"  {self.path.name}: {self.i}/{self.n}", flush=True)
        if self.i >= self.n and self.ai >= self.na and not self.done:
            self.done = True
            self.kick.stop()
            self.rec.stop()

    def _state(self, st):
        from PySide6.QtMultimedia import QMediaRecorder
        if st == QMediaRecorder.StoppedState and self.done:
            print(f"  saved {self.path} ({self.i} frames)", flush=True)
            self.app.quit()


MUSIC = {"main": HERE / "music" / "hushpad_bgm_main.wav", "shorts": HERE / "music" / "hushpad_bgm_shorts.wav"}
SILENT = False   # --silent 이면 음악 없이


def encode(kind, lang, out, app):
    r = Renderer(kind, lang)
    audio = None if SILENT else MUSIC[kind]
    if audio is not None and not audio.exists():
        raise SystemExit(f"{audio} 없음 — 먼저 python make_music.py 를 실행하세요 (또는 --silent)")
    print(f"render {out.name}: {r.dur:.1f}s, {r.L.W}x{r.L.H}@{FPS}, audio={audio.name if audio else 'none'}", flush=True)
    enc = Encoder(r, out, app, audio)
    QTimer.singleShot(0, enc.start)
    app.exec()
    if enc.failed:
        raise SystemExit(enc.failed)


def stills(lang, times, kind="main"):
    r = Renderer(kind, lang)
    q = HERE / "qa"
    q.mkdir(exist_ok=True)
    for x in times:
        r.frame(float(x)).save(str(q / f"still_{kind}_{lang}_{float(x):05.1f}.png"))
    print("stills ok")


def main():
    global SILENT
    app = QGuiApplication(sys.argv[:1])
    args = [a for a in sys.argv[1:] if a != "--silent"]
    SILENT = "--silent" in sys.argv[1:]
    args = args or ["all"]
    cmd = args[0]
    if cmd in ("ko", "en"):
        encode("main", cmd, HERE / f"hushpad_promo_{cmd}.mp4", app)
    elif cmd in ("shorts", "shorts_ko", "shorts_en"):
        lg = "en" if cmd == "shorts_en" else "ko"
        encode("shorts", lg, HERE / f"shorts_{lg}.mp4", app)
    elif cmd == "srt":
        write_srts()
    elif cmd == "thumbs":
        thumbnail("ko")
        thumbnail("en")
    elif cmd == "stills":
        kind = "main"
        lang = args[1]
        ts = args[2:]
        if lang.startswith("shorts"):
            kind, lang = "shorts", ("en" if lang == "shorts_en" else "ko")
        stills(lang, ts, kind)
    elif cmd == "all":
        write_srts()
        thumbnail("ko")
        thumbnail("en")
        for k in ("ko", "en"):
            encode("main", k, HERE / f"hushpad_promo_{k}.mp4", app)
        for k in ("ko", "en"):
            encode("shorts", k, HERE / f"shorts_{k}.mp4", app)


if __name__ == "__main__":
    main()
