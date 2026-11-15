"""Hushpad — 암호화되는 나만의 메모장.

실행:  python hushpad_main.py
점검:  python hushpad_main.py --selftest   (결과: %TEMP%\\hushpad_selftest.txt, 종료 코드 0 = 통과)
"""
from __future__ import annotations

import ctypes
import getpass
import os
import sys
import traceback
from pathlib import Path


def _set_app_id():
    try:
        from hushpad_app.common import APP_ID
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
    except Exception:
        pass


def _log_crash(exc_type, exc, tb):
    from hushpad_app.common import LOCAL_DIR
    try:
        LOCAL_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOCAL_DIR / "error.log", "a", encoding="utf-8") as f:
            import time
            f.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            traceback.print_exception(exc_type, exc, tb, file=f)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc, tb)


def main() -> int:
    if "--selftest" in sys.argv:
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from hushpad_app.selftest import run
        return run()

    _set_app_id()
    sys.excepthook = _log_crash
    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QIcon
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
    from PySide6.QtWidgets import QApplication, QMessageBox

    from hushpad_app import crypto
    from hushpad_app.common import APP_NAME, Config, resource
    from hushpad_app.dialogs import SetupDialog
    from hushpad_app.store import Store
    from hushpad_app.window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")   # QSS와 잘 맞는 기본 스타일
    icon = QIcon(str(resource("assets", "app.ico")))
    icon.addFile(str(resource("assets", "app.png")))
    app.setWindowIcon(icon)

    # 하나만 실행: 이미 떠 있으면 그 창을 앞으로
    server_name = f"Hushpad-{getpass.getuser()}"
    sock = QLocalSocket()
    sock.connectToServer(server_name)
    if sock.waitForConnected(300):
        sock.write(b"show")
        sock.flush()
        sock.waitForBytesWritten(300)
        return 0
    QLocalServer.removeServer(server_name)
    server = QLocalServer()
    server.listen(server_name)

    cfg = Config()
    key, folder, reason = None, None, ""
    if cfg.get("data_dir") and crypto.vault_exists(Path(cfg["data_dir"])):
        folder = Path(cfg["data_dir"])
        key = crypto.recall_key(crypto.vault_id(folder))
        if key is None:
            reason = "이 PC에서 처음 여는 보관 폴더이거나 암호가 바뀌었어요. 암호를 넣어 주세요."
    elif cfg.get("data_dir"):
        reason = f"보관 폴더를 찾을 수 없어요: {cfg['data_dir']}\n(동기화가 아직 안 됐거나 폴더가 옮겨졌을 수 있어요)"
    if key is None:
        d = SetupDialog(cfg.get("data_dir", ""), reason)
        d.setWindowIcon(icon)
        if not d.exec():
            return 0
        key, folder = d.key, d.folder
        cfg["data_dir"] = str(folder)
        cfg.save()
    store = Store(folder, key)
    store.load_all()
    try:
        crypto.unseal(key, crypto.seal(key, b"ok"))
    except Exception:
        QMessageBox.critical(None, APP_NAME, "암호화 모듈 점검에 실패했어요.")
        return 1

    win = MainWindow(store, cfg, icon)

    def _incoming():
        c = server.nextPendingConnection()
        if c:
            c.readyRead.connect(lambda: (c.readAll(), win.bring_to_front()))
    server.newConnection.connect(_incoming)
    app.setQuitOnLastWindowClosed(False)   # 창을 닫아도 트레이에서 계속
    if "--tray" in sys.argv and win.tray is not None:
        win._register_hotkeys()            # 창 없이 시작해도 전역 단축키는 동작
    else:
        win.show()
    app.aboutToQuit.connect(lambda: (win.save_all(), win.save_state()))
    rc = app.exec()
    server.close()
    if app.property("restart"):
        import subprocess
        args = [sys.executable] + ([] if getattr(sys, "frozen", False) else [os.path.abspath(__file__)])
        subprocess.Popen(args, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), close_fds=True)
    return rc


if __name__ == "__main__":
    sys.exit(main())
