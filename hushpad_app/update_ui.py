"""자동 업데이트 화면 쪽: 언제 확인할지, 묻는 창, 받는 동안 진행 표시. 실제 일은 updater.py.

- 켜고 15초 뒤 한 번, 그 뒤 6시간마다 날짜가 바뀌었으면 다시 확인 (설정 'update_check'로 끔).
- 켠 직후 찾았고 창이 보이면 바로 묻는다. 트레이에 있거나 나중에 찾았으면 알림만 띄우고 메뉴에서 설치.
- '이 버전 건너뛰기'를 고른 버전은 자동 확인에서 다시 묻지 않는다 (메뉴의 '업데이트 확인'은 언제나 묻는다).
"""
from __future__ import annotations

import threading
import time

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QProgressDialog, \
    QPushButton, QVBoxLayout

from . import __version__, i18n, updater
from .i18n import tr


class _Bridge(QObject):
    checked = Signal(object, object, bool)       # info|None, error|None, manual
    progress = Signal(int, int)
    stage = Signal(str)
    finished = Signal(object, object)            # (kind, path)|None, error|None


class UpdateDialog(QDialog):
    NOW, LATER, SKIP = 1, 2, 3

    def __init__(self, parent, info: dict):
        super().__init__(parent)
        self.setWindowTitle(tr("upd.title"))
        self.choice = self.LATER
        lay = QVBoxLayout(self)
        head = QLabel(tr("upd.available", new=info["version"], cur=__version__))
        head.setWordWrap(True)
        head.setStyleSheet("font-weight:600; font-size:14px;")
        lay.addWidget(head)
        notes = updater.notes_for(info, i18n.current())
        if notes:
            lay.addWidget(QLabel(tr("upd.notes")))
            body = QLabel("<ul style='margin-left:-20px'>" + "".join(f"<li>{_esc(n)}</li>" for n in notes) + "</ul>")
            body.setWordWrap(True)
            body.setTextFormat(Qt.RichText)
            lay.addWidget(body)
        if info.get("important"):
            imp = QLabel(tr("upd.important"))
            imp.setStyleSheet("color:#d93c4a; font-weight:600;")
            imp.setWordWrap(True)
            lay.addWidget(imp)
        row = QHBoxLayout()
        skip = QPushButton(tr("upd.skip"))
        later = QPushButton(tr("upd.later"))
        now = QPushButton(tr("upd.now"))
        now.setDefault(True)
        row.addWidget(skip)
        row.addStretch(1)
        row.addWidget(later)
        row.addWidget(now)
        lay.addLayout(row)
        skip.clicked.connect(lambda: self._pick(self.SKIP))
        later.clicked.connect(lambda: self._pick(self.LATER))
        now.clicked.connect(lambda: self._pick(self.NOW))
        self.setMinimumWidth(420)

    def _pick(self, c):
        self.choice = c
        self.accept()


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class UpdateController(QObject):
    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.cfg = win.cfg
        self.pending: dict | None = None        # 찾아 두었지만 아직 설치하지 않은 새 버전
        self._busy = False
        self._last_day = ""
        self.b = _Bridge()
        self.b.checked.connect(self._on_checked)
        self.b.progress.connect(self._on_progress)
        self.b.stage.connect(self._on_stage)
        self.b.finished.connect(self._on_finished)
        self._prog: QProgressDialog | None = None
        self._cancel = False
        QTimer.singleShot(20000, updater.cleanup)
        QTimer.singleShot(15000, lambda: self.check(manual=False, first=True))
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._daily)
        self.timer.start(6 * 3600 * 1000)
        self._first = True

    # ------------------------------------------------------------ 확인
    def _daily(self):
        if time.strftime("%Y-%m-%d") != self._last_day:
            self.check(manual=False)

    def check(self, manual: bool, first: bool = False):
        if self._busy:
            return
        if not manual and not self.cfg.get("update_check", True):
            return
        self._busy = True
        self._first = first
        self._last_day = time.strftime("%Y-%m-%d")

        def work():
            try:
                info, err = updater.fetch_info(), None
            except Exception as e:
                info, err = None, e
            self.b.checked.emit(info, err, manual)
        threading.Thread(target=work, daemon=True).start()

    def _on_checked(self, info, err, manual):
        self._busy = False
        if err is not None or info is None:
            if manual:
                QMessageBox.warning(self.win, tr("upd.title"), tr("upd.check_fail"))
            return
        if not updater.is_newer(info):
            if manual:
                QMessageBox.information(self.win, tr("upd.title"), tr("upd.latest", cur=__version__))
            return
        self.pending = info
        self.win.update_found(info["version"])
        if not manual and self.cfg.get("skip_version") == info["version"] and not info.get("important"):
            return
        if manual or info.get("important") or (self._first and self.win.isVisible()):
            self.ask(info)
        else:
            self.win._notify(tr("upd.notify", new=info["version"]))

    # ------------------------------------------------------------ 묻고 설치
    def ask(self, info: dict | None = None):
        info = info or self.pending
        if info is None:
            self.check(manual=True)
            return
        self.win.bring_to_front()
        d = UpdateDialog(self.win, info)
        d.exec()
        if d.choice == UpdateDialog.SKIP:
            self.cfg["skip_version"] = info["version"]
            self.cfg.save()
        elif d.choice == UpdateDialog.NOW:
            self.install(info)

    def install(self, info: dict):
        kind = updater.file_kind()
        if not updater.has_file(info, kind):
            self._fail(tr("upd.fail", err="no file for this edition"))
            return
        target = updater.app_dir()
        if kind == "win" and not updater.can_replace(target):
            self._fail(tr("upd.readonly", path=str(target)))
            return
        self._busy = True
        self._cancel = False
        p = QProgressDialog(tr("upd.downloading"), tr("upd.cancel"), 0, 100, self.win)
        p.setWindowTitle(tr("upd.title"))
        p.setWindowModality(Qt.WindowModal)
        p.setMinimumDuration(0)
        p.setAutoClose(False)
        p.setAutoReset(False)
        p.canceled.connect(self._on_cancel)
        p.show()
        self._prog = p

        def work():
            try:
                z = updater.download(info, progress=lambda d, t: self.b.progress.emit(d, t),
                                     cancelled=lambda: self._cancel, kind=kind)
                if kind == "setup":                  # 설치판: 받은 설치 프로그램을 그대로 실행
                    self.b.finished.emit(("setup", z), None)
                    return
                self.b.stage.emit("verify")
                new_dir = updater.extract(z, info["version"])
                updater.selftest(new_dir)
                self.b.finished.emit(("win", new_dir), None)
            except Exception as e:
                self.b.finished.emit(None, e)
        threading.Thread(target=work, daemon=True).start()

    def _on_cancel(self):
        self._cancel = True

    def _on_progress(self, done, total):
        if self._prog and total:
            self._prog.setValue(int(done * 100 / total))
            self._prog.setLabelText(tr("upd.downloading") + f"  {done / 1e6:.1f} / {total / 1e6:.1f} MB")

    def _on_stage(self, stage):
        if self._prog and stage == "verify":
            self._prog.setRange(0, 0)              # 끝을 모르는 진행 표시
            self._prog.setLabelText(tr("upd.verifying"))
            self._prog.setCancelButton(None)

    def _on_finished(self, result, err):
        self._busy = False
        if self._prog:
            self._prog.close()
            self._prog = None
        if err is not None:
            if str(err) == "cancelled":
                return
            self._fail(tr("upd.fail", err=str(err)))
            return
        QMessageBox.information(self.win, tr("upd.title"), tr("upd.restart"))
        try:
            self.win.save_all()
            self.win.save_state()
            kind, path = result
            if kind == "setup":
                updater.launch_setup(path)
            else:
                updater.launch_finish(path, updater.app_dir())
        except Exception as e:
            self._fail(tr("upd.fail", err=str(e)))
            return
        self.win.quit_app()

    def _fail(self, msg: str):
        box = QMessageBox(QMessageBox.Warning, tr("upd.title"), msg, parent=self.win)
        page = box.addButton(tr("upd.open_page"), QMessageBox.ActionRole)
        box.addButton(QMessageBox.Close)
        box.exec()
        if box.clickedButton() is page:
            QDesktopServices.openUrl(QUrl(updater.DOWNLOAD_PAGE))

