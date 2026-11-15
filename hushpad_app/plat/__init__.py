"""운영체제마다 다른 부분을 한곳에 모은 층.

Windows(win.py) · macOS(mac.py) · 그 밖(base.py: 아무것도 안 하는 안전한 기본값) 중 하나를 고른다.
win.py는 Windows에서만 import되므로 ctypes.windll·winreg가 다른 OS에서 실행될 일이 없다.

다른 모듈은 `from . import plat` 후 plat.exclude_from_capture(...)처럼 쓴다.
"""
from __future__ import annotations

import sys


def select(platform: str | None = None) -> str:
    """sys.platform 값 → 구현 모듈 이름 ('win' / 'mac' / 'base')."""
    p = sys.platform if platform is None else platform
    if p == "win32":
        return "win"
    if p == "darwin":
        return "mac"
    return "base"


NAME = select()
IS_WIN = NAME == "win"
IS_MAC = NAME == "mac"

if IS_WIN:
    from . import win as _impl
elif IS_MAC:
    from . import mac as _impl
else:
    from . import base as _impl

# ---- 경로
config_dir = _impl.config_dir            # () -> Path  설정(config.json)
local_dir = _impl.local_dir              # () -> Path  이 PC 전용(백업·임시·테마 아이콘)
default_data_dir = _impl.default_data_dir

# ---- 이 PC에 보관 폴더 키 기억 (Windows DPAPI / macOS 키체인)
keystore_name = _impl.keystore_name      # 사용자에게 보여 줄 이름
key_remember = _impl.key_remember        # (vault_id, key) -> None
key_recall = _impl.key_recall            # (vault_id) -> bytes | None
key_forget = _impl.key_forget            # (vault_id) -> None

# ---- 창
set_app_id = _impl.set_app_id            # (app_id) -> None   창을 만들기 전에
exclude_from_capture = _impl.exclude_from_capture   # (widget, on) -> bool
style_titlebar = _impl.style_titlebar    # (widget, tokens) -> None
set_topmost = _impl.set_topmost          # (widget, on) -> None
open_path = _impl.open_path              # (path) -> None  탐색기/Finder로 열기

# ---- 클립보드: 기록·관리 프로그램에서 빼기 표시
mark_private = _impl.mark_private        # (QMimeData, strict) -> QMimeData
CLIPBOARD_PRIVATE_SUPPORTED = _impl.CLIPBOARD_PRIVATE_SUPPORTED

# ---- 화면 캡처 권한 (macOS: 화면 기록 권한)
screen_capture_allowed = _impl.screen_capture_allowed   # () -> bool
request_screen_capture = _impl.request_screen_capture   # () -> None

# ---- 로그인할 때 실행
AUTOSTART_SUPPORTED = _impl.AUTOSTART_SUPPORTED
autostart_enabled = _impl.autostart_enabled  # () -> bool
set_autostart = _impl.set_autostart          # (on) -> bool  (False = 이 실행 방식에서는 못 함)

# ---- 전역 단축키·화면 잠금 알림
HOTKEYS_SUPPORTED = _impl.HOTKEYS_SUPPORTED
SESSION_LOCK_SUPPORTED = _impl.SESSION_LOCK_SUPPORTED
NOTEPAD_IMPORT_SUPPORTED = IS_WIN
GLOBAL_MODS = _impl.GLOBAL_MODS          # QKeySequence 표기 ('Ctrl+Alt+' / 'Meta+Alt+')
Integration = _impl.Integration          # 창마다 하나: 전역 단축키 + 잠금 알림


def global_key(letter: str) -> str:
    """전역 단축키를 이 OS 표기로 (Windows 'Ctrl+Alt+S', macOS '⌃⌥S')."""
    from PySide6.QtGui import QKeySequence
    return QKeySequence(GLOBAL_MODS + letter).toString(QKeySequence.NativeText)


def key_label(seq: str) -> str:
    """앱 안 단축키를 이 OS 표기로 (Windows 'Ctrl+Shift+C' 그대로, macOS '⇧⌘C')."""
    from PySide6.QtGui import QKeySequence
    return QKeySequence(seq).toString(QKeySequence.NativeText)
