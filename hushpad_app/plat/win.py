"""Windows 구현: DPAPI 키 기억, 캡처 제외(SetWindowDisplayAffinity), DWM 제목 표시줄,
RegisterHotKey 전역 단축키, WTS 잠금 알림, Run 키 자동 실행, 클립보드 기록 제외 형식,
Microsoft Store(MSIX) 패키지 앱 감지.

이 모듈은 sys.platform == 'win32'일 때만 import된다."""
from __future__ import annotations

import base64
import ctypes
import json
import os
import struct
import sys
from ctypes import wintypes
from pathlib import Path

from .base import APP, HOTKEY_KEYS, _profile, default_data_dir  # noqa: F401  (default_data_dir 재사용)


# ------------------------------------------------------------------ 경로 (예전과 같음)
def config_dir() -> Path:
    if _profile():
        return _profile()
    return Path(os.environ.get("APPDATA", str(Path.home()))) / APP


def local_dir() -> Path:
    if _profile():
        return _profile() / "local"
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / APP


# ------------------------------------------------------------------ DPAPI (현재 Windows 사용자 전용)
class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


_crypt32 = ctypes.windll.crypt32
_kernel32 = ctypes.windll.kernel32
_crypt32.CryptProtectData.argtypes = [ctypes.POINTER(_BLOB), wintypes.LPCWSTR, ctypes.POINTER(_BLOB),
                                      ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_BLOB)]
_crypt32.CryptProtectData.restype = wintypes.BOOL
_crypt32.CryptUnprotectData.argtypes = [ctypes.POINTER(_BLOB), ctypes.c_void_p, ctypes.POINTER(_BLOB),
                                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_BLOB)]
_crypt32.CryptUnprotectData.restype = wintypes.BOOL
_kernel32.LocalFree.argtypes = [ctypes.c_void_p]
_kernel32.LocalFree.restype = ctypes.c_void_p
_ENTROPY = b"Hushpad-local-key-v1"


def _blob(data: bytes):
    buf = (ctypes.c_ubyte * max(1, len(data))).from_buffer_copy(data or b"\0")
    return _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))), buf


def _dpapi(data: bytes, protect: bool) -> bytes:
    src, b1 = _blob(data)
    ent, b2 = _blob(_ENTROPY)
    out = _BLOB()
    if protect:
        ok = _crypt32.CryptProtectData(ctypes.byref(src), "Hushpad", ctypes.byref(ent), None, None, 1,
                                       ctypes.byref(out))
    else:
        ok = _crypt32.CryptUnprotectData(ctypes.byref(src), None, ctypes.byref(ent), None, None, 1,
                                         ctypes.byref(out))
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        _kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))


def dpapi_protect(data: bytes) -> bytes:
    return _dpapi(data, True)


def dpapi_unprotect(data: bytes) -> bytes:
    return _dpapi(data, False)


keystore_name = "DPAPI"


def _keys_file() -> Path:
    return local_dir() / "keys.json"


def key_remember(vid: str, key: bytes) -> None:
    f = _keys_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc = json.loads(f.read_text("utf-8"))
    except Exception:
        doc = {}
    doc[vid] = base64.b64encode(dpapi_protect(key)).decode("ascii")
    f.write_text(json.dumps(doc), "utf-8")


def key_recall(vid: str) -> bytes | None:
    try:
        doc = json.loads(_keys_file().read_text("utf-8"))
        return dpapi_unprotect(base64.b64decode(doc[vid].encode("ascii")))
    except Exception:
        return None


def key_forget(vid: str) -> None:
    f = _keys_file()
    try:
        doc = json.loads(f.read_text("utf-8"))
        doc.pop(vid, None)
        f.write_text(json.dumps(doc), "utf-8")
    except Exception:
        pass


# ------------------------------------------------------------------ 패키지 앱(MSIX) 감지
APPMODEL_ERROR_NO_PACKAGE = 15700
ERROR_INSUFFICIENT_BUFFER = 122


def detect_packaged() -> bool:
    """Microsoft Store(MSIX)로 설치된 패키지 앱으로 실행 중이면 True.
    GetCurrentPackageFullName: 패키지 아님 → 15700, 패키지 → 0 또는 122(버퍼 부족). Windows 8 미만엔 함수가 없음."""
    try:
        fn = _kernel32.GetCurrentPackageFullName
    except AttributeError:
        return False
    try:
        fn.argtypes = [ctypes.POINTER(ctypes.c_uint32), wintypes.LPWSTR]
        fn.restype = ctypes.c_long
        n = ctypes.c_uint32(0)
        rc = fn(ctypes.byref(n), None)
    except Exception:
        return False
    return rc in (0, ERROR_INSUFFICIENT_BUFFER)


IS_PACKAGED = detect_packaged()


def open_startup_settings() -> bool:
    """설정 › 앱 › 시작 프로그램. 패키지 앱의 시작 작업(StartupTask)은 여기서 켜고 끈다."""
    try:
        os.startfile("ms-settings:startupapps")
        return True
    except OSError:
        return False


# ------------------------------------------------------------------ 창
def set_app_id(app_id: str) -> None:
    if IS_PACKAGED:      # 패키지 앱은 패키지의 앱 ID를 그대로 써야 시작 메뉴·작업 표시줄 고정과 묶인다
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


WDA_NONE = 0
WDA_EXCLUDEFROMCAPTURE = 0x11


def exclude_from_capture(widget, on: bool = True) -> bool:
    """이 창을 스크린샷·화면 녹화·화면 공유에서 보이지 않게 한다 (Windows 10 2004 이상)."""
    try:
        return bool(ctypes.windll.user32.SetWindowDisplayAffinity(
            int(widget.winId()), WDA_EXCLUDEFROMCAPTURE if on else WDA_NONE))
    except Exception:
        return False


def style_titlebar(widget, t: dict) -> None:
    """제목 표시줄을 앱 색에 맞춘다 (어두운 모드, 캡션 색, 둥근 모서리, Mica)."""
    try:
        from PySide6.QtGui import QColor
        hwnd = wintypes.HWND(int(widget.winId()))
        dwm = ctypes.windll.dwmapi

        def setattr_(attr, value):
            v = ctypes.c_int(value)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(v), ctypes.sizeof(v))
        setattr_(20, 1 if t["dark"] else 0)                 # DWMWA_USE_IMMERSIVE_DARK_MODE
        setattr_(33, 2)                                     # DWMWA_WINDOW_CORNER_PREFERENCE = ROUND
        col = QColor(t["window"])
        setattr_(35, col.red() | (col.green() << 8) | (col.blue() << 16))  # DWMWA_CAPTION_COLOR (COLORREF)
        setattr_(36, QColor(t["text"]).red() | (QColor(t["text"]).green() << 8) | (QColor(t["text"]).blue() << 16))
        setattr_(34, 0xFFFFFFFE)                            # DWMWA_BORDER_COLOR = DWMWA_COLOR_NONE
    except Exception:
        pass


def set_topmost(widget, on: bool) -> None:
    HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
    ctypes.windll.user32.SetWindowPos(wintypes.HWND(int(widget.winId())),
                                      wintypes.HWND(HWND_TOPMOST if on else HWND_NOTOPMOST),
                                      0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)


def open_path(path) -> None:
    os.startfile(str(path))


# ------------------------------------------------------------------ 클립보드 기록(Win+V)·클라우드 제외
CLIPBOARD_PRIVATE_SUPPORTED = True
_WIN_FMT = 'application/x-qt-windows-mime;value="{}"'


def mark_private(md, strict: bool = False):
    """Windows 클립보드 기록(Win+V)·클라우드 클립보드에 남지 않게 표시.
    strict=True면 클립보드 감시 프로그램(클립보드 관리자 등)도 무시하도록 표시."""
    from PySide6.QtCore import QByteArray
    zero = QByteArray(struct.pack("<I", 0))
    md.setData(_WIN_FMT.format("CanIncludeInClipboardHistory"), zero)
    md.setData(_WIN_FMT.format("CanUploadToCloudClipboard"), zero)
    if strict:
        md.setData(_WIN_FMT.format("ExcludeClipboardContentFromMonitorProcessing"), QByteArray(b"\x01\0\0\0"))
    return md


# ------------------------------------------------------------------ 화면 캡처 권한 (Windows는 필요 없음)
def screen_capture_allowed() -> bool:
    return True


def request_screen_capture() -> None:
    pass


# ------------------------------------------------------------------ Windows 시작할 때 실행 (HKCU Run)
# 패키지 앱(Store)은 Run 키를 쓰지 않는다: 매니페스트의 시작 작업(StartupTask)이 대신하고, 켜고 끄기는 Windows 설정에서.
AUTOSTART_SUPPORTED = True
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autostart_enabled() -> bool:
    if IS_PACKAGED:
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP)
            return True
    except OSError:
        return False


def set_autostart(on: bool) -> bool:
    if IS_PACKAGED:
        return False
    import winreg
    if on and not getattr(sys, "frozen", False):
        return False
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP, 0, winreg.REG_SZ, f'"{sys.executable}" --tray')
        else:
            try:
                winreg.DeleteValue(k, APP)
            except OSError:
                pass
    return True


# ------------------------------------------------------------------ 전역 단축키 (RegisterHotKey) · 잠금 알림
HOTKEYS_SUPPORTED = True
SESSION_LOCK_SUPPORTED = True
GLOBAL_MODS = "Ctrl+Alt+"
WM_HOTKEY = 0x0312
WM_WTSSESSION_CHANGE = 0x02B1
WTS_SESSION_LOCK = 7
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x0001, 0x0002, 0x4000


class Integration:
    def __init__(self, widget, on_hotkey, on_session_lock):
        self.widget = widget
        self.on_hotkey = on_hotkey
        self.on_session_lock = on_session_lock
        self.ids: dict[int, str] = {}
        self.active = False
        self._wts = False

    def start(self) -> list[str]:
        if self.active:
            return []
        self.active = True
        hwnd = wintypes.HWND(int(self.widget.winId()))
        failed = []
        for hid, (name, letter) in enumerate(HOTKEY_KEYS, 1):
            if ctypes.windll.user32.RegisterHotKey(hwnd, hid, MOD_ALT | MOD_CONTROL | MOD_NOREPEAT, ord(letter)):
                self.ids[hid] = name
            else:
                failed.append(GLOBAL_MODS + letter)
        if not self._wts:
            try:
                self._wts = bool(ctypes.windll.wtsapi32.WTSRegisterSessionNotification(hwnd, 0))
            except Exception:
                pass
        return failed

    def stop(self) -> None:
        hwnd = wintypes.HWND(int(self.widget.winId()))
        for hid in self.ids:
            ctypes.windll.user32.UnregisterHotKey(hwnd, hid)
        self.ids = {}
        self.active = False

    def native_event(self, etype, message) -> bool:
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in self.ids:
                self.on_hotkey(self.ids[msg.wParam])
                return True
            if msg.message == WM_WTSSESSION_CHANGE and msg.wParam == WTS_SESSION_LOCK:
                self.on_session_lock()
        except Exception:
            pass
        return False
