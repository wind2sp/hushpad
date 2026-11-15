"""대화상자: 처음 설정·잠금 풀기, 이전 버전, 메모장 탭 가져오기."""
from __future__ import annotations

import html
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QCheckBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
                               QSplitter, QTextBrowser, QVBoxLayout)

from . import crypto
from .common import DEFAULT_DATA_DIR, fmt_full
from .i18n import tr

MIN_PASSPHRASE = 8


class SetupDialog(QDialog):
    """데이터 폴더를 고르고, 새 금고를 만들거나 기존 금고를 연다."""

    def __init__(self, folder: str = "", reason: str = ""):
        super().__init__()
        self.setWindowTitle(tr("setup.title"))
        self.setMinimumWidth(560)
        self.key = None
        self.folder = None
        lay = QVBoxLayout(self)
        if reason:
            r = QLabel(reason)
            r.setWordWrap(True)
            r.setStyleSheet("color:#c0392b;")
            lay.addWidget(r)
        intro = QLabel("<br>".join(tr(k) for k in ("setup.intro1", "setup.intro2", "setup.intro3")))
        intro.setWordWrap(True)
        lay.addWidget(intro)
        row = QHBoxLayout()
        self.path = QLineEdit(folder or str(DEFAULT_DATA_DIR))
        browse = QPushButton(tr("setup.browse"))
        browse.clicked.connect(self._browse)
        row.addWidget(self.path, 1)
        row.addWidget(browse)
        form = QFormLayout()
        form.addRow(tr("setup.folder"), row)
        self.mode = QLabel()
        form.addRow("", self.mode)
        self.pw1 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2_label = QLabel(tr("setup.pw2"))
        form.addRow(tr("setup.pw"), self.pw1)
        form.addRow(self.pw2_label, self.pw2)
        lay.addLayout(form)
        self.warn = QLabel(tr("setup.warn"))
        self.warn.setWordWrap(True)
        lay.addWidget(self.warn)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("setup.start"))
        bb.button(QDialogButtonBox.Cancel).setText(tr("common.close"))
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.path.textChanged.connect(self._refresh)
        self._refresh()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, tr("setup.pick_folder"), self.path.text())
        if d:
            self.path.setText(str(Path(d)))

    def _existing(self) -> bool:
        p = Path(self.path.text().strip())
        return bool(self.path.text().strip()) and crypto.vault_exists(p)

    def _refresh(self):
        ex = self._existing()
        self.mode.setText(tr("setup.existing") if ex else tr("setup.new"))
        self.pw2.setVisible(not ex)
        self.pw2_label.setVisible(not ex)
        self.warn.setVisible(not ex)

    def _ok(self):
        folder = Path(self.path.text().strip())
        pw = self.pw1.text()
        if not self.path.text().strip():
            return
        try:
            if crypto.vault_exists(folder):
                self.key = crypto.unlock_vault(folder, pw)
            else:
                if any((folder / "notes").glob("*.own")):
                    # 메모 파일은 있는데 vault.json이 없음: 동기화가 덜 됐을 가능성. 새 금고를 만들면 기존 메모를 못 연다
                    QMessageBox.warning(self, tr("setup.folder_title"), tr("setup.unsynced"))
                    return
                if len(pw) < MIN_PASSPHRASE:
                    QMessageBox.warning(self, tr("setup.pw"), tr("setup.too_short"))
                    return
                if pw != self.pw2.text():
                    QMessageBox.warning(self, tr("setup.pw"), tr("setup.mismatch"))
                    return
                if folder.exists() and any(folder.iterdir()):
                    if QMessageBox.question(self, tr("setup.folder_title"), tr("setup.not_empty")) \
                            != QMessageBox.Yes:
                        return
                self.key = crypto.create_vault(folder, pw)
        except crypto.BadPassphrase:
            QMessageBox.warning(self, tr("setup.pw"), tr("setup.bad_pw"))
            self.pw1.selectAll()
            return
        except OSError as e:
            QMessageBox.critical(self, tr("setup.folder_title"), tr("setup.cant_write", err=e))
            return
        except (ValueError, KeyError, TypeError):   # 손상되거나 바뀐 vault.json (JSON 오류도 ValueError)
            QMessageBox.critical(self, tr("setup.folder_title"), tr("setup.bad_vault"))
            return
        crypto.remember_key(crypto.vault_id(folder), self.key)
        self.folder = folder
        self.accept()


class AboutDialog(QDialog):
    """프로그램 정보: 아이콘, 이름·버전, 한 줄 소개, 만든 곳."""

    def __init__(self, parent, icon):
        super().__init__(parent)
        from . import __version__
        from .common import ABOUT_COMPANY, ABOUT_EMAIL, ABOUT_PERSON
        from .i18n import current as current_language
        self.setWindowTitle(tr("about.title"))
        self.setWindowIcon(icon)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(36, 26, 36, 20)
        lay.setSpacing(6)
        pic = QLabel(alignment=Qt.AlignCenter)
        pic.setPixmap(icon.pixmap(72, 72))
        lay.addWidget(pic)
        lay.addSpacing(6)
        name = QLabel(f"Hushpad&nbsp;&nbsp;v{__version__}", alignment=Qt.AlignCenter)
        name.setTextFormat(Qt.RichText)
        name.setStyleSheet("font-size: 20px; font-weight: 700;")
        lay.addWidget(name)
        sub = QLabel(tr("about.tagline"), alignment=Qt.AlignCenter, objectName="EmptyHint")
        lay.addWidget(sub)
        hint = QLabel(tr("about.hint"), alignment=Qt.AlignCenter, objectName="EmptyHint")
        lay.addWidget(hint)
        lay.addSpacing(14)
        company = ABOUT_COMPANY.get(current_language(), ABOUT_COMPANY["en"])
        person = ABOUT_PERSON.get(current_language(), ABOUT_PERSON["en"])
        for text in (company, f'<a href="mailto:{ABOUT_EMAIL}">{ABOUT_EMAIL}</a>', person):
            lb = QLabel(text, alignment=Qt.AlignCenter)
            lb.setTextFormat(Qt.RichText)
            lb.setOpenExternalLinks(True)
            lb.setTextInteractionFlags(Qt.TextBrowserInteraction)
            lay.addWidget(lb)
        lay.addSpacing(8)
        from PySide6.QtCore import QUrl
        from .common import resource
        cp = QLabel(tr("about.copyright"), alignment=Qt.AlignCenter, objectName="EmptyHint")
        lay.addWidget(cp)
        lic = QLabel(tr("about.license", url="https://github.com/wind2sp/hushpad"), alignment=Qt.AlignCenter,
                     objectName="EmptyHint")
        lic.setTextFormat(Qt.RichText)
        lic.setOpenExternalLinks(True)
        lay.addWidget(lic)
        oss = QLabel(tr("about.oss", notices=QUrl.fromLocalFile(str(resource("THIRD_PARTY_NOTICES.md"))).toString(),
                        license=QUrl.fromLocalFile(str(resource("LICENSE"))).toString()),
                     alignment=Qt.AlignCenter, objectName="EmptyHint")
        oss.setTextFormat(Qt.RichText)
        oss.setOpenExternalLinks(True)
        lay.addWidget(oss)
        lay.addSpacing(14)
        row = QHBoxLayout()
        row.addStretch(1)
        ok = QPushButton(tr("common.ok"))
        ok.setDefault(True)
        ok.setMinimumWidth(96)
        ok.clicked.connect(self.accept)
        row.addWidget(ok)
        row.addStretch(1)
        lay.addLayout(row)
        self.setFixedSize(self.sizeHint().expandedTo(self.minimumSizeHint()))


class PassphraseDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(tr("pwd.title"))
        lay = QFormLayout(self)
        self.pw1 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2 = QLineEdit(echoMode=QLineEdit.Password)
        lay.addRow(tr("pwd.new"), self.pw1)
        lay.addRow(tr("pwd.new2"), self.pw2)
        note = QLabel(tr("pwd.note"))
        note.setWordWrap(True)
        lay.addRow(note)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _ok(self):
        if len(self.pw1.text()) < MIN_PASSPHRASE or self.pw1.text() != self.pw2.text():
            QMessageBox.warning(self, tr("setup.pw"), tr("pwd.invalid"))
            return
        self.accept()


class HistoryDialog(QDialog):
    """이전 버전 보기·되돌리기."""

    def __init__(self, parent, store, note):
        super().__init__(parent)
        self.setWindowTitle(tr("hist.title", title=note.display_title()))
        self.resize(900, 560)
        self.store, self.note = store, note
        self.chosen = None
        lay = QVBoxLayout(self)
        sp = QSplitter()
        self.lst = QListWidget()
        self.view = QTextBrowser()
        sp.addWidget(self.lst)
        sp.addWidget(self.view)
        sp.setSizes([220, 680])
        lay.addWidget(sp, 1)
        self.items = store.history(note.id)
        for ts, p in self.items:
            self.lst.addItem(fmt_full(ts))
        if not self.items:
            self.lst.addItem(tr("hist.none"))
        self.lst.currentRowChanged.connect(self._show)
        bb = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.restore_btn = bb.addButton(tr("hist.restore"), QDialogButtonBox.AcceptRole)
        self.restore_btn.setEnabled(False)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        if self.items:
            self.lst.setCurrentRow(0)

    def _show(self, row):
        if not (0 <= row < len(self.items)):
            return
        try:
            snap = self.store.load_snapshot(self.items[row][1], self.note.id)
        except Exception:
            self.view.setPlainText(tr("hist.unreadable"))
            self.restore_btn.setEnabled(False)
            return
        self._snap = snap
        if snap.kind == "rich" and snap.html:
            self.view.setHtml(snap.html)
        else:
            self.view.setPlainText(snap.text)
        self.restore_btn.setEnabled(True)

    def _ok(self):
        self.chosen = getattr(self, "_snap", None)
        self.accept()


class ImportDialog(QDialog):
    """Windows 메모장 탭 고르기."""

    def __init__(self, parent, tabs, already: set[str]):
        super().__init__(parent)
        self.setWindowTitle(tr("imp.title"))
        self.resize(760, 520)
        lay = QVBoxLayout(self)
        info = QLabel(tr("imp.info"))
        info.setWordWrap(True)
        lay.addWidget(info)
        sp = QSplitter()
        self.lst = QListWidget()
        self.view = QTextBrowser()
        sp.addWidget(self.lst)
        sp.addWidget(self.view)
        sp.setSizes([330, 430])
        lay.addWidget(sp, 1)
        self.tabs = tabs
        for t in tabs:
            first = next((ln.strip() for ln in t.text.splitlines() if ln.strip()), "")[:50]
            name = Path(t.path).name if t.path else first
            it = QListWidgetItem(f"{name}  ({tr('note.chars', n=len(t.text))})")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if t.text in already else Qt.Checked)
            self.lst.addItem(it)
        self.lst.currentRowChanged.connect(lambda r: self.view.setPlainText(self.tabs[r].text if 0 <= r < len(self.tabs) else ""))
        self.as_text = QCheckBox(tr("imp.as_text"))
        self.as_text.setChecked(True)
        lay.addWidget(self.as_text)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText(tr("imp.ok"))
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        if tabs:
            self.lst.setCurrentRow(0)

    def selected(self):
        return [t for i, t in enumerate(self.tabs) if self.lst.item(i).checkState() == Qt.Checked]


def esc(s: str) -> str:
    return html.escape(s)
