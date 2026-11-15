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


class SetupDialog(QDialog):
    """데이터 폴더를 고르고, 새 금고를 만들거나 기존 금고를 연다."""

    def __init__(self, folder: str = "", reason: str = ""):
        super().__init__()
        self.setWindowTitle("Hushpad — 메모 보관 폴더와 암호")
        self.setMinimumWidth(560)
        self.key = None
        self.folder = None
        lay = QVBoxLayout(self)
        if reason:
            r = QLabel(reason)
            r.setWordWrap(True)
            r.setStyleSheet("color:#c0392b;")
            lay.addWidget(r)
        intro = QLabel(
            "모든 메모는 이 폴더 한 곳에 <b>암호화된 파일</b>로 저장됩니다. 다른 프로그램이나 사람이 파일을 열어도 내용을 볼 수 없어요.<br>"
            "여러 PC에서 같이 쓰려면 Dropbox·OneDrive 같은 <b>동기화 폴더 안</b>을 고르고, 다른 PC에서도 같은 폴더와 같은 암호를 넣으면 됩니다.<br>"
            "이 PC에서는 암호를 한 번만 넣으면 Windows 계정에 묶어 기억해 두므로 다음부터 묻지 않습니다.")
        intro.setWordWrap(True)
        lay.addWidget(intro)
        row = QHBoxLayout()
        self.path = QLineEdit(folder or str(DEFAULT_DATA_DIR))
        browse = QPushButton("찾아보기...")
        browse.clicked.connect(self._browse)
        row.addWidget(self.path, 1)
        row.addWidget(browse)
        form = QFormLayout()
        form.addRow("보관 폴더", row)
        self.mode = QLabel()
        form.addRow("", self.mode)
        self.pw1 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2_label = QLabel("암호 확인")
        form.addRow("암호", self.pw1)
        form.addRow(self.pw2_label, self.pw2)
        lay.addLayout(form)
        self.warn = QLabel("⚠ 암호를 잊으면 아무도(만든 사람도) 메모를 되살릴 수 없습니다. 안전한 곳에 적어 두세요.")
        self.warn.setWordWrap(True)
        lay.addWidget(self.warn)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("시작")
        bb.button(QDialogButtonBox.Cancel).setText("닫기")
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        self.path.textChanged.connect(self._refresh)
        self._refresh()

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "메모 보관 폴더", self.path.text())
        if d:
            self.path.setText(str(Path(d)))

    def _existing(self) -> bool:
        p = Path(self.path.text().strip())
        return bool(self.path.text().strip()) and crypto.vault_exists(p)

    def _refresh(self):
        ex = self._existing()
        self.mode.setText("✔ 이미 Hushpad 메모가 있는 폴더입니다 — 그 암호를 넣으세요." if ex
                          else "새 보관 폴더를 만듭니다 — 사용할 암호를 정하세요 (6자 이상).")
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
                if len(pw) < 6:
                    QMessageBox.warning(self, "암호", "암호는 6자 이상으로 정해 주세요.")
                    return
                if pw != self.pw2.text():
                    QMessageBox.warning(self, "암호", "두 암호가 다릅니다.")
                    return
                if folder.exists() and any(folder.iterdir()):
                    if QMessageBox.question(self, "폴더", "비어 있지 않은 폴더입니다. 이 안에 Hushpad 파일을 만들까요?") \
                            != QMessageBox.Yes:
                        return
                self.key = crypto.create_vault(folder, pw)
        except crypto.BadPassphrase:
            QMessageBox.warning(self, "암호", "암호가 맞지 않습니다.")
            self.pw1.selectAll()
            return
        except OSError as e:
            QMessageBox.critical(self, "폴더", f"폴더를 쓸 수 없습니다.\n{e}")
            return
        crypto.remember_key(crypto.vault_id(folder), self.key)
        self.folder = folder
        self.accept()


class PassphraseDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("암호 바꾸기")
        lay = QFormLayout(self)
        self.pw1 = QLineEdit(echoMode=QLineEdit.Password)
        self.pw2 = QLineEdit(echoMode=QLineEdit.Password)
        lay.addRow("새 암호", self.pw1)
        lay.addRow("새 암호 확인", self.pw2)
        lay.addRow(QLabel("다른 PC에서는 다음에 열 때 새 암호를 한 번 물어봅니다."))
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self._ok)
        bb.rejected.connect(self.reject)
        lay.addRow(bb)

    def _ok(self):
        if len(self.pw1.text()) < 6 or self.pw1.text() != self.pw2.text():
            QMessageBox.warning(self, "암호", "6자 이상, 두 칸이 같아야 합니다.")
            return
        self.accept()


class HistoryDialog(QDialog):
    """이전 버전 보기·되돌리기."""

    def __init__(self, parent, store, note):
        super().__init__(parent)
        self.setWindowTitle(f"이전 버전 — {note.display_title()}")
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
            self.lst.addItem("(아직 저장된 이전 버전이 없어요 — 10분마다 하나씩 생깁니다)")
        self.lst.currentRowChanged.connect(self._show)
        bb = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.restore_btn = bb.addButton("이 버전으로 되돌리기", QDialogButtonBox.AcceptRole)
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
            self.view.setPlainText("(이 버전은 읽을 수 없습니다)")
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
        self.setWindowTitle("Windows 메모장 탭 가져오기")
        self.resize(760, 520)
        lay = QVBoxLayout(self)
        info = QLabel("Windows 메모장에 열려 있는 탭(저장하지 않은 것 포함)을 Hushpad로 복사합니다. "
                      "메모장 쪽은 건드리지 않아요. 이미 가져온 내용은 체크가 꺼져 있습니다.")
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
            it = QListWidgetItem(f"{name}  ({len(t.text):,}자)")
            it.setFlags(it.flags() | Qt.ItemIsUserCheckable)
            it.setCheckState(Qt.Unchecked if t.text in already else Qt.Checked)
            self.lst.addItem(it)
        self.lst.currentRowChanged.connect(lambda r: self.view.setPlainText(self.tabs[r].text if 0 <= r < len(self.tabs) else ""))
        self.as_text = QCheckBox("텍스트 메모로 가져오기 (HTML·JSON·코드가 많으면 추천)")
        self.as_text.setChecked(True)
        lay.addWidget(self.as_text)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.button(QDialogButtonBox.Ok).setText("가져오기")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)
        if tabs:
            self.lst.setCurrentRow(0)

    def selected(self):
        return [t for i, t in enumerate(self.tabs) if self.lst.item(i).checkState() == Qt.Checked]


def esc(s: str) -> str:
    return html.escape(s)
