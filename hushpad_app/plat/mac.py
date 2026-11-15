"""macOS 구현 (추가 패키지 없이 ctypes + Objective-C 런타임·Carbon·CoreGraphics, 그리고 /usr/bin/security).

- 키 기억: 로그인 키체인의 일반 암호 항목 (서비스 'Hushpad', 계정 = 보관 폴더 id)
- 캡처 제외: NSWindow.sharingType = NSWindowSharingNone
  (macOS 15 이상에서 ScreenCaptureKit을 쓰는 일부 캡처 프로그램은 이 설정을 무시할 수 있다)
- 전역 단축키: Carbon RegisterEventHotKey, ⌃⌥(Control+Option) + S/R/N/M
- 로그인할 때 실행: ~/Library/LaunchAgents/com.hushpad.app.plist
- 클립보드: org.nspasteboard.TransientType / ConcealedType 표시 (QUtiMimeConverter가 있을 때)
- 화면 기록 권한: CGPreflightScreenCaptureAccess / CGRequestScreenCaptureAccess

이 모듈은 sys.platform == 'darwin'일 때만 import된다. 모든 시스템 호출은 실패해도 조용히 넘어간다.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
import plistlib
import struct
import subprocess
import sys
from ctypes import CFUNCTYPE, POINTER, Structure, c_bool, c_char_p, c_int32, c_long, c_size_t, c_uint32, \
    c_ulong, c_void_p
from pathlib import Path

from . import base
from .base import APP, HOTKEY_KEYS, _profile, default_data_dir, open_path  # noqa: F401


# ------------------------------------------------------------------ 경로
def config_dir() -> Path:
    if _profile():
        return _profile()
    return Path.home() / "Library" / "Application Support" / APP


def local_dir() -> Path:
    if _profile():
        return _profile() / "local"
    return Path.home() / "Library" / "Application Support" / APP


# ------------------------------------------------------------------ Objective-C 런타임
_objc = None
_sends: dict = {}


def _lib():
    global _objc
    if _objc is None:
        _objc = ctypes.cdll.LoadLibrary("/usr/lib/libobjc.A.dylib")
        _objc.objc_getClass.restype = c_void_p
        _objc.objc_getClass.argtypes = [c_char_p]
        _objc.sel_registerName.restype = c_void_p
        _objc.sel_registerName.argtypes = [c_char_p]
    return _objc


def _send(obj, sel: str, restype=c_void_p, argtypes=(), *args):
    """objc_msgSend를 정확한 함수 모양으로 바꿔 부른다 (arm64에서도 안전)."""
    sig = (restype, tuple(argtypes))
    fn = _sends.get(sig)
    if fn is None:
        fn = CFUNCTYPE(restype, c_void_p, c_void_p, *argtypes)(("objc_msgSend", _lib()))
        _sends[sig] = fn
    return fn(obj, _lib().sel_registerName(sel.encode()), *args)


def _cls(name: str):
    return _lib().objc_getClass(name.encode())


def _nsstring(s: str):
    return _send(_cls("NSString"), "stringWithUTF8String:", c_void_p, [c_char_p], s.encode("utf-8"))


def _nswindow(widget):
    """QWidget → NSWindow* (아직 창이 없으면 None). winId()는 macOS 화면(cocoa)에서만 NSView*.
    offscreen·minimal 같은 다른 Qt 플랫폼에서는 winId가 Objective-C 객체가 아니라서
    보내면 프로그램이 죽는다 → 그때는 아무것도 하지 않는다."""
    from PySide6.QtGui import QGuiApplication
    if QGuiApplication.platformName() != "cocoa":
        return None
    view = int(widget.winId())
    if not view:
        return None
    return _send(c_void_p(view), "window") or None


def _on_window(widget, fn) -> bool:
    """NSWindow가 생긴 뒤 fn(nswindow) 실행. Show 이벤트 때는 아직 없을 수 있어 한 번 미뤄 다시 시도."""
    try:
        w = _nswindow(widget)
    except Exception:
        return False
    if w:
        try:
            fn(w)
            return True
        except Exception:
            return False
    from PySide6.QtCore import QTimer

    def later():
        try:
            w2 = _nswindow(widget)
            if w2:
                fn(w2)
        except Exception:
            pass
    QTimer.singleShot(0, later)
    return False


# ------------------------------------------------------------------ 키체인 (/usr/bin/security)
keystore_name = "Keychain"
_SECURITY = "/usr/bin/security"


def _service() -> str:
    p = _profile()
    return APP if not p else f"{APP}-profile-{hashlib.sha1(str(p).encode()).hexdigest()[:8]}"


def _security(args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([_SECURITY] + args, input=stdin, capture_output=True, text=True, timeout=15)


def key_remember(vid: str, key: bytes) -> None:
    secret = base64.b64encode(key).decode("ascii")
    cmd = f'add-generic-password -U -s {_service()} -a {vid} -w {secret}\n'
    try:
        # 'security -i'로 표준 입력에 명령을 넘겨 키가 프로세스 목록(ps)에 보이지 않게 한다
        r = _security(["-i"], stdin=cmd)
        if r.returncode == 0 and key_recall(vid) == key:
            return
        _security(["add-generic-password", "-U", "-s", _service(), "-a", vid, "-l", "Hushpad vault key",
                   "-w", secret])
    except Exception:
        pass


def key_recall(vid: str) -> bytes | None:
    try:
        r = _security(["find-generic-password", "-s", _service(), "-a", vid, "-w"])
        if r.returncode != 0:
            return None
        key = base64.b64decode(r.stdout.strip().encode("ascii"))
        return key if len(key) == 32 else None
    except Exception:
        return None


def key_forget(vid: str) -> None:
    try:
        _security(["delete-generic-password", "-s", _service(), "-a", vid])
    except Exception:
        pass


# ------------------------------------------------------------------ 창
def set_app_id(app_id: str) -> None:
    pass   # macOS는 번들 id(com.hushpad.app)로 앱을 구분한다


NSWindowSharingNone, NSWindowSharingReadOnly = 0, 1


def exclude_from_capture(widget, on: bool = True) -> bool:
    return _on_window(widget, lambda w: _send(w, "setSharingType:", None, [c_ulong],
                                              NSWindowSharingNone if on else NSWindowSharingReadOnly))


def style_titlebar(widget, t: dict) -> None:
    """제목 표시줄을 앱 테마(밝게/어둡게)에 맞춘다: NSWindow.appearance."""
    def apply(w):
        name = _nsstring("NSAppearanceNameDarkAqua" if t.get("dark") else "NSAppearanceNameAqua")
        ap = _send(_cls("NSAppearance"), "appearanceNamed:", c_void_p, [c_void_p], name)
        if ap:
            _send(w, "setAppearance:", None, [c_void_p], ap)
    _on_window(widget, apply)


def set_topmost(widget, on: bool) -> None:
    NSNormalWindowLevel, NSFloatingWindowLevel = 0, 3
    if not _on_window(widget, lambda w: _send(w, "setLevel:", None, [c_long],
                                              NSFloatingWindowLevel if on else NSNormalWindowLevel)):
        base.set_topmost(widget, on)


# ------------------------------------------------------------------ 클립보드: nspasteboard.org 표시
CONCEALED_MIME = "application/x-hushpad-nspasteboard-concealed"
TRANSIENT_MIME = "application/x-hushpad-nspasteboard-transient"
_UTI = {CONCEALED_MIME: "org.nspasteboard.ConcealedType", TRANSIENT_MIME: "org.nspasteboard.TransientType"}
_converter = None   # None = 아직, False = 쓸 수 없음


def _ensure_converter() -> bool:
    """Qt의 QUtiMimeConverter로 위 MIME을 그대로 그 UTI로 내보내게 한다."""
    global _converter
    if _converter is None:
        try:
            from PySide6.QtCore import QByteArray
            from PySide6.QtGui import QUtiMimeConverter

            class _Markers(QUtiMimeConverter):
                def mimeForUti(self, uti):
                    return next((m for m, u in _UTI.items() if u == uti), "")

                def utiForMime(self, mime):
                    return _UTI.get(mime, "")

                def convertToMime(self, mime, data, uti):
                    return QByteArray(bytes(data[0])) if data else QByteArray()

                def convertFromMime(self, mime, data, uti):
                    return [QByteArray(bytes(data) if data is not None else b"")]

            _converter = _Markers()
        except Exception:
            _converter = False
    return _converter is not False


CLIPBOARD_PRIVATE_SUPPORTED = True


def mark_private(md, strict: bool = False):
    """클립보드 관리 프로그램(Maccy, Raycast, Alfred …)이 기록하지 않도록 표시.
    strict=True면 '숨김(Concealed)'까지 — 암호처럼 화면에 보여 주지도 않게."""
    if not _ensure_converter():
        return md
    from PySide6.QtCore import QByteArray
    md.setData(TRANSIENT_MIME, QByteArray(b"1"))
    if strict:
        md.setData(CONCEALED_MIME, QByteArray(b"1"))
    return md


# ------------------------------------------------------------------ 화면 기록 권한
_cg = None


def _coregraphics():
    global _cg
    if _cg is None:
        try:
            _cg = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
            _cg.CGPreflightScreenCaptureAccess.restype = c_bool
            _cg.CGRequestScreenCaptureAccess.restype = c_bool
        except Exception:
            _cg = False
    return _cg or None


def screen_capture_allowed() -> bool:
    cg = _coregraphics()
    if cg is None:
        return True       # 알 수 없으면 일단 찍어 보고, 결과가 비었는지로 판단
    try:
        return bool(cg.CGPreflightScreenCaptureAccess())
    except Exception:
        return True


def request_screen_capture() -> None:
    """처음 한 번 시스템 권한 창을 띄우고 '시스템 설정 › 개인정보 보호 및 보안 › 화면 기록'에 앱을 올린다."""
    cg = _coregraphics()
    try:
        if cg is not None:
            cg.CGRequestScreenCaptureAccess()
    except Exception:
        pass


# ------------------------------------------------------------------ 로그인할 때 실행 (LaunchAgent)
AUTOSTART_SUPPORTED = True
AGENT_LABEL = "com.hushpad.app"


def _agent_file() -> Path:
    return Path.home() / "Library" / "LaunchAgents" / f"{AGENT_LABEL}.plist"


def autostart_enabled() -> bool:
    return _agent_file().is_file()


def set_autostart(on: bool) -> bool:
    f = _agent_file()
    if not on:
        try:
            f.unlink()
        except FileNotFoundError:
            pass
        return True
    if not getattr(sys, "frozen", False):
        return False
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(plistlib.dumps({
        "Label": AGENT_LABEL,
        "ProgramArguments": [sys.executable, "--tray"],   # …/Hushpad.app/Contents/MacOS/Hushpad
        "RunAtLoad": True,
        "ProcessType": "Interactive",
    }))
    return True


# ------------------------------------------------------------------ 전역 단축키 (Carbon)
HOTKEYS_SUPPORTED = True
SESSION_LOCK_SUPPORTED = False     # 화면 잠금 알림은 아직 Windows만
GLOBAL_MODS = "Meta+Alt+"          # Qt 표기: macOS에서 Meta = ⌃Control, Alt = ⌥Option
_VK = {"S": 0x01, "R": 0x0F, "N": 0x2D, "M": 0x2E}   # kVK_ANSI_*
controlKey, optionKey = 0x1000, 0x0800


def _fourcc(s: str) -> int:
    return struct.unpack(">I", s.encode("ascii"))[0]


class _EventTypeSpec(Structure):
    _fields_ = [("eventClass", c_uint32), ("eventKind", c_uint32)]


class _EventHotKeyID(Structure):
    _fields_ = [("signature", c_uint32), ("id", c_uint32)]


_HANDLER = CFUNCTYPE(c_int32, c_void_p, c_void_p, c_void_p)
_carbon = None


def _carbon_lib():
    global _carbon
    if _carbon is None:
        c = ctypes.cdll.LoadLibrary("/System/Library/Frameworks/Carbon.framework/Carbon")
        c.GetApplicationEventTarget.restype = c_void_p
        c.GetApplicationEventTarget.argtypes = []
        c.InstallEventHandler.restype = c_int32
        c.InstallEventHandler.argtypes = [c_void_p, _HANDLER, c_uint32, POINTER(_EventTypeSpec), c_void_p,
                                          POINTER(c_void_p)]
        c.RemoveEventHandler.restype = c_int32
        c.RemoveEventHandler.argtypes = [c_void_p]
        c.RegisterEventHotKey.restype = c_int32
        c.RegisterEventHotKey.argtypes = [c_uint32, c_uint32, _EventHotKeyID, c_void_p, c_uint32,
                                          POINTER(c_void_p)]
        c.UnregisterEventHotKey.restype = c_int32
        c.UnregisterEventHotKey.argtypes = [c_void_p]
        c.GetEventParameter.restype = c_int32
        c.GetEventParameter.argtypes = [c_void_p, c_uint32, c_uint32, c_void_p, c_size_t, c_void_p, c_void_p]
        _carbon = c
    return _carbon


class Integration(base.Integration):
    SIGNATURE = _fourcc("HSHP")

    def __init__(self, widget, on_hotkey, on_session_lock):
        super().__init__(widget, on_hotkey, on_session_lock)
        self._refs: list[c_void_p] = []
        self._names: dict[int, str] = {}
        self._handler_ref = None
        self._cb = _HANDLER(self._on_event)   # 참조를 붙잡아 둬야 콜백이 사라지지 않는다

    def _on_event(self, _call, event, _data):
        try:
            hk = _EventHotKeyID()
            err = _carbon_lib().GetEventParameter(event, _fourcc("----"), _fourcc("hkid"), None,
                                                  ctypes.sizeof(hk), None, ctypes.byref(hk))
            if err == 0 and hk.signature == self.SIGNATURE and hk.id in self._names:
                self.on_hotkey(self._names[hk.id])
        except Exception:
            pass
        return 0

    def start(self) -> list[str]:
        if self.active:
            return []
        self.active = True
        try:
            c = _carbon_lib()
            target = c.GetApplicationEventTarget()
            if self._handler_ref is None:
                spec = _EventTypeSpec(_fourcc("keyb"), 5)       # kEventClassKeyboard, kEventHotKeyPressed
                ref = c_void_p()
                if c.InstallEventHandler(target, self._cb, 1, ctypes.byref(spec), None, ctypes.byref(ref)) != 0:
                    raise OSError("InstallEventHandler")
                self._handler_ref = ref
        except Exception:
            return [GLOBAL_MODS + letter for _, letter in HOTKEY_KEYS]
        failed = []
        for hid, (name, letter) in enumerate(HOTKEY_KEYS, 1):
            ref = c_void_p()
            err = c.RegisterEventHotKey(_VK[letter], controlKey | optionKey, _EventHotKeyID(self.SIGNATURE, hid),
                                        target, 0, ctypes.byref(ref))
            if err == 0:
                self._refs.append(ref)
                self._names[hid] = name
            else:
                failed.append(GLOBAL_MODS + letter)
        return failed

    def stop(self) -> None:
        try:
            c = _carbon_lib()
            for ref in self._refs:
                c.UnregisterEventHotKey(ref)
            if self._handler_ref is not None:
                c.RemoveEventHandler(self._handler_ref)
        except Exception:
            pass
        self._refs, self._names, self._handler_ref = [], {}, None
        self.active = False

