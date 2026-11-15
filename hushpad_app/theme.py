"""테마: 색 토큰(밝은/어두운) → Qt 스타일시트, 제목 표시줄 맞춤(Windows 11 DWM / macOS 외관).

가볍게: 이미지·웹 없이 QSS + 직접 그린 선 아이콘만 쓴다.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QPalette

from . import i18n, plat

# 브랜드: 자두색(plum) + 복숭아색(peach) — 앱 아이콘 "흩어지는 메모지"와 같은 색
LIGHT = {
    "window": "#F5F4F7", "sidebar": "#F5F4F7", "surface": "#FFFFFF", "elevated": "#FFFFFF",
    "border": "#DDD8E3", "border_subtle": "#EAE6EE",
    "text": "#1C1A20", "text2": "#4B4652", "muted": "#8A8492",
    "accent": "#7A3C93", "accent_hover": "#66307C", "accent2": "#9B4DB5", "accent_text": "#FFFFFF",
    "accent_subtle": "#F2E7F7", "accent_subtle_text": "#5E2A73",
    "hover": "#ECE8F0", "pressed": "#E2DCE8",
    "danger": "#C42B1C", "success": "#0F7B3F", "focus": "#9B4DB5", "gold": "#C98A06", "peach": "#E0703F",
    "scroll": "rgba(0,0,0,0.22)", "scroll_hover": "rgba(0,0,0,0.38)",
    "code_bg": "#FFFFFF", "gutter": "#FAF8FB", "primary_from": "#7A3C93", "primary_to": "#9B4DB5",
}
DARK = {
    "window": "#1C1A1F", "sidebar": "#1A181D", "surface": "#232026", "elevated": "#2B2830",
    "border": "#3A3540", "border_subtle": "#2E2A33",
    "text": "#EEEAF2", "text2": "#B9B2C2", "muted": "#7F7889",
    "accent": "#FFB38A", "accent_hover": "#FFC6A6", "accent2": "#C77DDF", "accent_text": "#1C1A1F",
    "accent_subtle": "#3A2645", "accent_subtle_text": "#F6DDFF",
    "hover": "#29252D", "pressed": "#332E38",
    "danger": "#FF7B6E", "success": "#5FCB8A", "focus": "#C77DDF", "gold": "#F2C94C", "peach": "#FFB38A",
    "scroll": "rgba(255,255,255,0.20)", "scroll_hover": "rgba(255,255,255,0.34)",
    "code_bg": "#232026", "gutter": "#201D23", "primary_from": "#7A3C93", "primary_to": "#9B4DB5",
}

# 글꼴: 앞에서부터 그 글자가 있는 글꼴을 쓴다. 언어마다 맞는 한자·가나 글꼴을 앞쪽에 둔다
# (일본어 한자를 한국어 글꼴로, 중국어를 일본어 글꼴로 그리지 않게).
_CJK_WIN = {"ja": ["Yu Gothic UI", "Meiryo"], "zh": ["Microsoft YaHei UI", "Microsoft YaHei"]}
_CJK_MAC = {"ja": ["Hiragino Sans"], "zh": ["PingFang SC"], "ko": ["Apple SD Gothic Neo"]}


def _dedup(xs):
    return list(dict.fromkeys(xs))


def ui_families(lang: str | None = None) -> list[str]:
    lang = lang or i18n.current()
    if plat.IS_MAC:
        return _dedup(["Pretendard"] + _CJK_MAC.get(lang, []) +
                      ["Apple SD Gothic Neo", "Hiragino Sans", "PingFang SC"])
    return _dedup(["Pretendard"] + _CJK_WIN.get(lang, []) +
                  ["Malgun Gothic", "Yu Gothic UI", "Microsoft YaHei UI"])


def code_families(lang: str | None = None) -> list[str]:
    mono = ["D2Coding", "Cascadia Mono", "Consolas"] + (["SF Mono", "Menlo"] if plat.IS_MAC else [])
    return _dedup(mono + ui_families(lang)[1:])


def _css(fams: list[str]) -> str:
    return ", ".join(f'"{f}"' for f in fams)


def system_is_dark() -> bool:
    try:
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except Exception:
        return False


def tokens(mode: str) -> dict:
    dark = system_is_dark() if mode == "auto" else mode == "dark"
    t = dict(DARK if dark else LIGHT)
    t["dark"] = dark
    return t


def palette(t: dict) -> QPalette:
    p = QPalette()
    c = lambda k: QColor(t[k])  # noqa: E731
    p.setColor(QPalette.Window, c("window"))
    p.setColor(QPalette.WindowText, c("text"))
    p.setColor(QPalette.Base, c("surface"))
    p.setColor(QPalette.AlternateBase, c("gutter"))
    p.setColor(QPalette.Text, c("text"))
    p.setColor(QPalette.PlaceholderText, c("muted"))
    p.setColor(QPalette.Button, c("surface"))
    p.setColor(QPalette.ButtonText, c("text"))
    p.setColor(QPalette.Highlight, c("accent"))
    p.setColor(QPalette.HighlightedText, c("accent_text"))
    p.setColor(QPalette.ToolTipBase, c("elevated"))
    p.setColor(QPalette.ToolTipText, c("text"))
    p.setColor(QPalette.Link, c("accent"))
    p.setColor(QPalette.Mid, c("border"))
    return p


def _icon_file(name: str, color: str) -> str:
    """QSS의 url()에 쓸 아이콘 파일 (이 PC 설정 폴더에 한 번 만들어 둠)."""
    from .common import LOCAL_DIR
    from .icons import svg
    d = LOCAL_DIR / "theme"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{name}-{color.lstrip('#')}.svg"
    if not f.exists():
        f.write_bytes(svg(name, color, 2.0))
    return f.as_posix()


def qss(t: dict) -> str:
    return QSS.format(ui=_css(ui_families()), code=_css(code_families()), close_icon=_icon_file("close", t["muted"]),
                      chev_icon=_icon_file("chev", "#FFFFFF"), chev_muted=_icon_file("chev", t["muted"]),
                      **{k: v for k, v in t.items() if k != "dark"})


QSS = """
* {{ font-family: {ui}; font-size: 13px; color: {text}; }}
QMainWindow, QDialog {{ background: {window}; }}
QToolTip {{ background: {elevated}; color: {text}; border: 1px solid {border}; border-radius: 6px; padding: 5px 8px; }}

/* ---------- 사이드바 ---------- */
#Sidebar {{ background: {sidebar}; border-right: 1px solid {border_subtle}; }}
#Brand {{ font-size: 15px; font-weight: 700; padding: 2px 4px; }}
#SectionLabel {{ color: {muted}; font-size: 11px; font-weight: 600; letter-spacing: 0.3px; padding: 12px 10px 4px 10px; }}
#Search {{ background: {hover}; border: 1px solid transparent; border-radius: 8px; padding: 5px 8px; }}
#Search:hover {{ border-color: {border}; }}
#Search:focus {{ background: {surface}; border: 1px solid {accent}; }}
#CatList, #NoteList {{ background: transparent; border: none; outline: 0; }}
#CatList::item {{ height: 30px; padding: 0 10px; border-radius: 6px; margin: 1px 0; color: {text2}; }}
#CatList::item:hover {{ background: {hover}; }}
#CatList::item:selected {{ background: {accent_subtle}; color: {accent_subtle_text}; font-weight: 600; }}
#NoteList::item {{ border-radius: 8px; margin: 1px 6px; }}
#NoteList::item:hover {{ background: {hover}; }}
#NoteList::item:selected {{ background: {accent_subtle}; }}

/* ---------- 상단 막대 ---------- */
QToolBar#TopBar {{ background: {window}; border: none; border-bottom: 1px solid {border_subtle}; padding: 6px 10px; spacing: 2px; }}
#CommandBtn {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; padding: 5px 10px; min-width: 210px;
    color: {muted}; text-align: left; }}
#CommandBtn:hover {{ border-color: {accent}; color: {text2}; }}
QToolBar#TopBar QToolButton {{ background: transparent; border: none; border-radius: 6px; padding: 6px; margin: 0 1px;
    color: {text2}; min-width: 20px; min-height: 20px; }}
QToolBar#TopBar QToolButton:hover {{ background: {hover}; color: {text}; }}
QToolBar#TopBar QToolButton:pressed {{ background: {pressed}; }}
QToolBar#TopBar QToolButton:checked {{ background: {accent_subtle}; color: {accent_subtle_text}; }}
QToolBar#TopBar QToolButton#Primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {primary_from}, stop:1 {primary_to});
    color: #FFFFFF; font-weight: 600; padding: 6px 30px 6px 10px; min-height: 22px; margin-right: 6px; }}
QToolBar#TopBar QToolButton#Primary:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #66307C, stop:1 #8A3FA3); }}
QToolBar#TopBar QToolButton#Primary::menu-button {{ border-left: 1px solid rgba(255,255,255,0.25); width: 22px;
    border-top-right-radius: 6px; border-bottom-right-radius: 6px; }}
QToolBar#TopBar QToolButton#Primary::menu-arrow {{ image: url({chev_icon}); width: 10px; height: 10px; }}
QToolBar::separator {{ background: {border}; width: 1px; margin: 6px 6px; }}

/* ---------- 메뉴 ---------- */
QMenuBar {{ background: {window}; padding: 2px 6px; }}
QMenuBar::item {{ padding: 4px 10px; border-radius: 6px; background: transparent; color: {text2}; }}
QMenuBar::item:selected {{ background: {hover}; color: {text}; }}
QMenu {{ background: {elevated}; border: 1px solid {border}; border-radius: 10px; padding: 5px; }}
QMenu::item {{ padding: 6px 28px 6px 12px; border-radius: 6px; }}
QMenu::item:selected {{ background: {accent_subtle}; color: {accent_subtle_text}; }}
QMenu::item:disabled {{ color: {muted}; }}
QMenu::separator {{ height: 1px; background: {border_subtle}; margin: 5px 8px; }}
QMenu::indicator {{ width: 14px; height: 14px; left: 6px; }}

/* ---------- 탭 ---------- */
QTabWidget::pane {{ border: none; background: {surface}; }}
QTabBar {{ background: {window}; }}
QTabBar::tab {{ background: transparent; color: {text2}; padding: 6px 8px 6px 12px; margin: 6px 2px 0 0;
    border: 1px solid transparent; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px;
    min-width: 60px; max-width: 240px; height: 22px; font-size: 12.5px; }}
QTabBar::tab:hover:!selected {{ background: {hover}; color: {text}; }}
QTabBar::tab:selected {{ background: {surface}; color: {text}; border-color: {border_subtle};
    border-top: 2px solid {accent}; font-weight: 500; }}
QTabBar::tab:first {{ margin-left: 8px; }}
QTabBar::close-button {{ image: url({close_icon}); subcontrol-position: right; subcontrol-origin: padding;
    border-radius: 4px; margin: 0 2px; width: 16px; height: 16px; }}
QTabBar::close-button:hover {{ background: {pressed}; }}
QTabBar QToolButton {{ background: {window}; border: none; border-radius: 6px; }}
#TabCorner {{ background: transparent; border: none; border-radius: 7px; padding: 4px; margin: 6px 6px 0 0; }}
#TabCorner:hover {{ background: {hover}; }}

/* ---------- 편집기 ---------- */
QTextEdit, QPlainTextEdit, QTextBrowser {{ background: {surface}; border: none; selection-background-color: {accent};
    selection-color: {accent_text}; }}
#Editor {{ padding: 6px 0 0 0; }}
#CodeEditor {{ background: {code_bg}; font-family: {code}; }}
#EmptyState {{ background: {surface}; }}
#EmptyTitle {{ font-size: 20px; font-weight: 700; color: {text}; }}
#EmptyHint {{ color: {muted}; font-size: 13px; }}
#Kbd {{ background: {window}; border: 1px solid {border}; border-bottom-width: 2px; border-radius: 5px; padding: 1px 6px;
    color: {text2}; font-size: 12px; }}

/* ---------- 입력·버튼 ---------- */
QLineEdit {{ background: {surface}; border: 1px solid {border}; border-radius: 7px; padding: 6px 9px;
    selection-background-color: {accent}; selection-color: {accent_text}; }}
QLineEdit:focus {{ border-color: {focus}; }}
QPushButton {{ background: {surface}; border: 1px solid {border}; border-radius: 7px; padding: 6px 14px; }}
QPushButton:hover {{ background: {hover}; }}
QPushButton:pressed {{ background: {pressed}; }}
QPushButton:default, QPushButton#Primary {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {primary_from}, stop:1 {primary_to});
    color: #FFFFFF; border: none; font-weight: 600; padding: 7px 16px; }}
QPushButton:default:hover, QPushButton#Primary:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #66307C, stop:1 #8A3FA3); }}
QPushButton#Ghost {{ background: transparent; border: none; color: {text2}; padding: 4px 8px; }}
QPushButton#Ghost:hover {{ background: {hover}; color: {text}; }}
QComboBox {{ background: transparent; border: 1px solid transparent; border-radius: 6px; padding: 2px 6px;
    color: {muted}; font-size: 11.5px; }}
QComboBox:hover {{ background: {hover}; }}
QComboBox::drop-down {{ border: none; width: 14px; }}
QComboBox::down-arrow {{ image: url({chev_muted}); width: 9px; height: 9px; }}
QComboBox QAbstractItemView {{ background: {elevated}; border: 1px solid {border}; border-radius: 8px; padding: 4px;
    selection-background-color: {accent_subtle}; selection-color: {accent_subtle_text}; outline: 0; }}
QCheckBox {{ spacing: 8px; }}

/* ---------- 찾기 막대·상태 막대 ---------- */
#FindBar {{ background: {window}; border-top: 1px solid {border_subtle}; }}
QStatusBar {{ background: {window}; color: {muted}; min-height: 24px; }}
QStatusBar QLabel {{ color: {muted}; font-size: 12px; padding: 0 8px; }}
QStatusBar::item {{ border: none; }}

/* ---------- 스크롤바 (얇게) ---------- */
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px 1px; }}
QScrollBar::handle:vertical {{ background: {scroll}; border-radius: 3px; min-height: 30px; margin: 0 2px; }}
QScrollBar::handle:vertical:hover {{ background: {scroll_hover}; margin: 0 1px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {scroll}; border-radius: 3px; min-width: 30px; margin: 2px 0; }}
QScrollBar::handle:horizontal:hover {{ background: {scroll_hover}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

QSplitter::handle {{ background: {border_subtle}; }}
QSplitter::handle:horizontal {{ width: 1px; }}
QHeaderView::section {{ background: transparent; border: none; color: {muted}; padding: 4px; }}

#SecretCover {{ background: {surface}; border: none; color: {text2}; font-size: 14px; }}
#SecretCover:hover {{ background: {hover}; color: {text}; }}

/* ---------- 명령 팔레트 ---------- */
#Palette {{ background: {elevated}; border: 1px solid {border}; border-radius: 14px; }}
#PaletteInput {{ background: transparent; border: none; border-bottom: 1px solid {border_subtle}; border-radius: 0;
    font-size: 15px; padding: 14px 16px; }}
#PaletteFoot {{ color: {muted}; font-size: 11.5px; border-top: 1px solid {border_subtle}; padding: 7px 14px; }}
#PaletteList {{ background: transparent; border: none; outline: 0; padding: 6px 8px; }}
#PaletteList::item {{ border: none; }}
#PaletteList::item:selected {{ background: transparent; }}
"""


# ------------------------------------------------------------------ 제목 표시줄
def style_titlebar(widget, t: dict) -> None:
    """제목 표시줄을 앱 색에 맞춘다 (Windows: 어두운 모드·캡션 색·둥근 모서리 / macOS: 밝게·어둡게 외관)."""
    plat.style_titlebar(widget, t)
