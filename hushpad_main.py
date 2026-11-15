"""Hushpad — 암호화되는 나만의 메모장.

실행:  python hushpad_main.py
점검:  python hushpad_main.py --selftest   (결과: %TEMP%\\hushpad_selftest.txt, 종료 코드 0 = 통과)
Windows·macOS 공통 (OS마다 다른 부분은 hushpad_app/plat).
"""
from __future__ import annotations

import getpass
import os
import sys
import traceback
from pathlib import Path


def _set_app_id():
    try:
        from hushpad_app import plat
        from hushpad_app.common import APP_ID
        plat.set_app_id(APP_ID)      # Windows: 작업 표시줄 아이콘 묶음 (창을 만들기 전에)
    except Exception:
        pass


def _install_qt_translations(app, lang):
    """Qt 기본 단추(OK·Cancel·Yes…)와 입력 칸 오른쪽 클릭 메뉴를 고른 언어로."""
    if lang not in ("ko", "ja", "zh"):
        return
    from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
    tr = QTranslator(app)
    loc = QLocale({"ko": "ko_KR", "ja": "ja_JP", "zh": "zh_CN"}[lang])
    if tr.load(loc, "qtbase", "_", QLibraryInfo.path(QLibraryInfo.TranslationsPath)):
        app.installTranslator(tr)


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

    from hushpad_app import crypto, i18n
    from hushpad_app.common import APP_NAME, Config, resource
    from hushpad_app.i18n import tr

    app = QApplication(sys.argv)
    cfg = Config()
    i18n.set_language(i18n.resolve(cfg.get("language", "system")))   # 창을 만들기 전에 언어를 정한다
    _install_qt_translations(app, i18n.current())
    from hushpad_app.dialogs import SetupDialog
    from hushpad_app.store import Store
    from hushpad_app.window import MainWindow

    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")   # QSS와 잘 맞는 기본 스타일
    icon = QIcon(str(resource("assets", "app.png")))
    if sys.platform == "win32":
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

    key, folder, reason = None, None, ""
    if cfg.get("data_dir") and crypto.vault_exists(Path(cfg["data_dir"])):
        folder = Path(cfg["data_dir"])
        key = crypto.recall_key(crypto.vault_id(folder))
        if key is None:
            reason = tr("main.first_open")
    elif cfg.get("data_dir"):
        reason = tr("main.missing", path=cfg["data_dir"])
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
        QMessageBox.critical(None, APP_NAME, tr("main.crypto_fail"))
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
