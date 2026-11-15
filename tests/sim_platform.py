"""다른 OS인 척하고 Hushpad를 띄워 보는 점검 (Windows에서 macOS·Linux 경로를 미리 살피기용).

    python tests/sim_platform.py darwin     # macOS 흉내
    python tests/sim_platform.py linux      # 기본(base) 구현

- sys.platform을 바꾸고, Windows 전용 모듈(winreg, ctypes.wintypes, ctypes.windll)을 막은 뒤
  hushpad_app의 모든 모듈을 import하고 MainWindow를 화면 없이 만든다.
- macOS 시스템 라이브러리(/usr/lib/libobjc…)·/usr/bin/security는 없으므로 실패해야 정상이고,
  그 실패가 조용히 무시되는지(앱이 죽지 않는지)를 본다. 실제 macOS 동작 확인은 아니다.
"""
from __future__ import annotations

import ctypes
import os
import sys
import tempfile
from pathlib import Path

target = sys.argv[1] if len(sys.argv) > 1 else "darwin"
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["QT_QPA_PLATFORM"] = "offscreen"
prof = Path(tempfile.mkdtemp(prefix="hsp-sim-"))
os.environ["HUSHPAD_PROFILE"] = str(prof)

# 표준 라이브러리 중 import할 때 sys.platform을 보는 것은 먼저 불러 둔다 (진짜 OS용으로)
import hashlib, plistlib, shutil, subprocess, uuid, zipfile  # noqa: E401,F401,E402

# ---- Windows 전용 기능 막기 (이 뒤로 쓰면 바로 오류)
for mod in ("winreg", "ctypes.wintypes", "msvcrt", "_winapi_blocked"):
    sys.modules[mod] = None
if hasattr(ctypes, "windll"):
    del ctypes.windll
if hasattr(ctypes, "WinDLL"):
    del ctypes.WinDLL
real_platform = sys.platform
sys.platform = target

from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication([])

import hushpad_app.plat as plat  # noqa: E402
from hushpad_app import capture, crypto, dialogs, editors, i18n, store, theme, widgets, window  # noqa: E402,F401
from hushpad_app.common import Config  # noqa: E402

expect = {"darwin": "mac", "linux": "base"}[target]
assert plat.NAME == expect, plat.NAME
assert "hushpad_app.plat.win" not in sys.modules, "Windows module imported"
print("platform:", plat.NAME, "| global key:", plat.global_key("S"), "| app key:", plat.key_label("Ctrl+Shift+C"))
print("paths:", plat.config_dir(), plat.local_dir(), plat.default_data_dir())

i18n.set_language("en")
print("tr@mac:", i18n.tr("act.autostart"))
if target == "darwin":
    assert i18n.tr("act.autostart") == "Open at login"

# ---- 금고·키 기억 (키체인 없음 → None)
vault = prof / "data"
key = crypto.create_vault(vault, "test-pass-1234")
crypto.remember_key(crypto.vault_id(vault), key)
print("recall (expected None here):", crypto.recall_key(crypto.vault_id(vault)))

cfg = Config()
cfg.save = lambda: None
st = store.Store(vault, key)
st.load_all()
w = window.MainWindow(st, cfg, QIcon())
w.show()
app.processEvents()
t = w.new_note("rich")
t.edit.insertPlainText("hello")
t.dirty = True
t.save()
w.copy_all(plain=True)                       # mark_private (mac: QUtiMimeConverter 없음 → 그냥 복사)
w._toggle_topmost(True)
w._toggle_topmost(False)
w._toggle_hide_capture(True)
w.set_theme("dark")
print("autostart supported:", plat.AUTOSTART_SUPPORTED, "enabled:", w._autostart_on())
labels = [lbl for _, lbl, _ in w.palette_actions()]
assert not any("Notepad" in x for x in labels), "Notepad import should be hidden"
print("palette actions:", len(labels), "| e.g.", labels[:3])
print("screen capture allowed:", plat.screen_capture_allowed())
print("hotkeys started:", w.native.active)
w._quitting = True
w.close()
sys.platform = real_platform
print("OK", target)
sys.stdout.flush()
os._exit(0)   # Qt 정리 단계는 흉내 낸 OS와 상관없으므로 건너뜀
