"""여러 곳에서 쓰는 작은 도구: 설정, 경로, 클립보드, 캡처 숨김, 이미지 변환.

OS마다 다른 부분(경로·캡처 숨김·클립보드 표시)은 plat 모듈에 있다."""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QMimeData
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from . import plat
from .i18n import fmt_ts

APP_NAME = "Hushpad"
APP_ID = "windsp.Hushpad.Notes"

# HUSHPAD_PROFILE 환경 변수를 주면 설정·키·백업을 그 폴더에 둔다 (시험용)
# Windows: %APPDATA%\Hushpad\config.json, %LOCALAPPDATA%\Hushpad
# macOS:   ~/Library/Application Support/Hushpad
LOCAL_DIR = plat.local_dir()
CONFIG_FILE = plat.config_dir() / "config.json"
DEFAULT_DATA_DIR = plat.default_data_dir()


def resource(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base.joinpath(*parts)


# ------------------------------------------------------------------ 설정 (이 PC 전용)
DEFAULTS = {
    "data_dir": "",
    "open_tabs": [],
    "current_tab": "",
    "geometry": "",
    "splitter": "",
    "font_pt": 11,
    "wrap": True,
    "plain_paste": False,
    "clip_private": True,       # 복사한 내용을 클립보드 기록(Windows Win+V·클라우드 / macOS 클립보드 관리자)에서 빼기
    "secret_clear_sec": 30,     # 비밀 메모에서 복사하면 n초 뒤 클립보드 비움 (0 = 끔)
    "sort": "updated",
    "capture_delay": 0,
    "video_fps": 12,
    "video_max_sec": 180,
    "language": "system",       # system = 운영체제 언어(지원하지 않으면 영어) / ko / en / ja / zh
}


class Config(dict):
    def __init__(self):
        super().__init__(DEFAULTS)
        try:
            self.update(json.loads(CONFIG_FILE.read_text("utf-8")))
        except Exception:
            pass

    def save(self) -> None:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(self, ensure_ascii=False, indent=1), "utf-8")
        os.replace(tmp, CONFIG_FILE)


# ------------------------------------------------------------------ 화면 캡처에서 이 창 숨기기
def exclude_from_capture(widget, on: bool = True) -> bool:
    """이 창을 스크린샷·화면 녹화·화면 공유에서 보이지 않게 한다
    (Windows 10 2004 이상: SetWindowDisplayAffinity / macOS: NSWindow.sharingType)."""
    return plat.exclude_from_capture(widget, on)


# ------------------------------------------------------------------ 클립보드
TOKEN_MIME = "application/x-hushpad-token"


def mark_private(md: QMimeData, strict: bool = False) -> QMimeData:
    """클립보드 기록에 남지 않게 표시 (Windows: Win+V 기록·클라우드 / macOS: 클립보드 관리 프로그램).
    strict=True면 클립보드 감시 프로그램(클립보드 관리자 등)도 무시하도록 표시."""
    return plat.mark_private(md, strict)


def set_clipboard(md: QMimeData, private: bool, strict: bool = False, clear_after: int = 0) -> None:
    if private or strict:
        mark_private(md, strict)
    token = None
    if clear_after > 0:
        token = os.urandom(8).hex().encode()
        md.setData(TOKEN_MIME, QByteArray(token))
    QApplication.clipboard().setMimeData(md)
    if token:
        from PySide6.QtCore import QTimer

        def _clear():
            cur = QApplication.clipboard().mimeData()
            if cur is not None and cur.hasFormat(TOKEN_MIME) and bytes(cur.data(TOKEN_MIME)) == token:
                QApplication.clipboard().clear()
        QTimer.singleShot(clear_after * 1000, _clear)


def text_mime(text: str) -> QMimeData:
    md = QMimeData()
    md.setText(text)
    return md


# ------------------------------------------------------------------ 이미지 <-> data URL
def image_to_data_url(img: QImage, fmt: str = "PNG") -> str:
    ba = QByteArray()
    buf = QBuffer(ba)
    buf.open(QIODevice.WriteOnly)
    img.save(buf, fmt)
    mime = "image/png" if fmt.upper() == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(bytes(ba)).decode("ascii")


def data_url_to_image(url: str) -> QImage | None:
    if not url.startswith("data:") or "," not in url:
        return None
    img = QImage()
    img.loadFromData(base64.b64decode(url.split(",", 1)[1]))
    return None if img.isNull() else img


# ------------------------------------------------------------------ 시각 (언어에 맞춰)
def fmt_time(ts: float) -> str:
    now = time.localtime()
    t = time.localtime(ts)
    if t.tm_year == now.tm_year and t.tm_yday == now.tm_yday:
        return fmt_ts(ts, "fmt.hm")
    if t.tm_year == now.tm_year:
        return fmt_ts(ts, "fmt.md_hm")
    return fmt_ts(ts, "fmt.ymd")


def fmt_full(ts: float) -> str:
    return fmt_ts(ts, "fmt.full")


def fmt_stamp(ts: float | None = None, key: str = "fmt.md_hm") -> str:
    """메모 안에 적는 짧은 시각 (예: '📷 캡처 11-15 14:32')."""
    return fmt_ts(time.time() if ts is None else ts, key)
