"""기본 구현 — 지원하지 않는 OS(예: Linux)용. 아무 일도 하지 않거나 Qt만으로 할 수 있는 일만 한다.
win.py·mac.py도 공통 부분은 여기 것을 그대로 쓴다."""
from __future__ import annotations

import os
from pathlib import Path

APP = "Hushpad"
# 전역 단축키: (이름, 글자) — Ctrl+Alt(Windows) / ⌃⌥(macOS) + 글자
HOTKEY_KEYS = (("shot", "S"), ("record", "R"), ("quick", "N"), ("clip", "M"))


def _profile() -> Path | None:
    p = os.environ.get("HUSHPAD_PROFILE")
    return Path(p) if p else None


# ------------------------------------------------------------------ 경로
def config_dir() -> Path:
    if _profile():
        return _profile()
    return Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / APP


def local_dir() -> Path:
    if _profile():
        return _profile() / "local"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / APP


def default_data_dir() -> Path:
    return Path.home() / "Documents" / APP


# ------------------------------------------------------------------ 키 기억 (없음 → 매번 암호를 묻는다)
keystore_name = ""


def key_remember(vid: str, key: bytes) -> None:
    pass


def key_recall(vid: str) -> bytes | None:
    return None


def key_forget(vid: str) -> None:
    pass


# ------------------------------------------------------------------ 창
def set_app_id(app_id: str) -> None:
    pass


def exclude_from_capture(widget, on: bool = True) -> bool:
    return False


def style_titlebar(widget, t: dict) -> None:
    pass


def set_topmost(widget, on: bool) -> None:
    """Qt만으로 '항상 위' (창을 다시 띄워야 적용됨)."""
    from PySide6.QtCore import Qt
    vis = widget.isVisible()
    widget.setWindowFlag(Qt.WindowStaysOnTopHint, on)
    if vis:
        widget.show()


def open_path(path) -> None:
    from PySide6.QtCore import QUrl
    from PySide6.QtGui import QDesktopServices
    QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))


# ------------------------------------------------------------------ 클립보드
CLIPBOARD_PRIVATE_SUPPORTED = False


def mark_private(md, strict: bool = False):
    return md


# ------------------------------------------------------------------ 화면 캡처 권한
def screen_capture_allowed() -> bool:
    return True


def request_screen_capture() -> None:
    pass


# ------------------------------------------------------------------ 로그인할 때 실행
AUTOSTART_SUPPORTED = False


def autostart_enabled() -> bool:
    return False


def set_autostart(on: bool) -> bool:
    return False


# ------------------------------------------------------------------ 전역 단축키·잠금 알림
HOTKEYS_SUPPORTED = False
SESSION_LOCK_SUPPORTED = False
GLOBAL_MODS = "Ctrl+Alt+"


class Integration:
    """창 하나에 붙는 OS 기능. 기본: 아무것도 안 함."""

    def __init__(self, widget, on_hotkey, on_session_lock):
        self.widget = widget
        self.on_hotkey = on_hotkey
        self.on_session_lock = on_session_lock
        self.active = False

    def start(self) -> list[str]:
        """전역 단축키 등록 → 등록하지 못한 단축키 이름 목록."""
        self.active = True
        return []

    def stop(self) -> None:
        self.active = False

    def native_event(self, etype, message) -> bool:
        return False
