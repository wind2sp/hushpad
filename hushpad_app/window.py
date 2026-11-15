"""Hushpad 주 창."""
from __future__ import annotations

import ctypes
import html as html_mod
import json
import os
import shutil
import time
from ctypes import wintypes
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QMimeData, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QIcon, QImage, QKeySequence, QShortcut,
                           QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QFileDialog, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
                               QSizePolicy, QStackedWidget, QSystemTrayIcon, QTabWidget, QToolBar, QToolButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from . import capture, crypto, icons, notepad_import, theme
from .widgets import CommandPalette, CountDelegate, EmptyState, NoteList, rel_time
from .common import (APP_NAME, LOCAL_DIR, exclude_from_capture, fmt_full, fmt_time, resource, set_clipboard,
                     text_mime)
from .dialogs import HistoryDialog, ImportDialog, PassphraseDialog, SetupDialog
from .editors import CodeEdit, RichEdit, body_font, mono_font
from .store import Note, Store

IDS_MIME = "application/x-hushpad-ids"
SAVE_DELAY_MS = 600
TEXT_EXT = {".txt", ".json", ".html", ".htm", ".md", ".csv", ".xml", ".yaml", ".yml", ".ini", ".log", ".py",
            ".js", ".ts", ".css", ".sql", ".env", ".cfg", ".toml", ".bat", ".ps1", ".sh"}
WM_HOTKEY = 0x0312
# Ctrl+Alt+S 스크린샷, R 녹화, N 새 메모, M 클립보드를 메모로
HOTKEYS = {1: ("shot", 0x53), 2: ("record", 0x52), 3: ("quick", 0x4E), 4: ("clip", 0x4D)}
WM_WTSSESSION_CHANGE = 0x02B1
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ====================================================================== 메모 한 장(탭)
class NoteTab(QWidget):
    def __init__(self, win: "MainWindow", note: Note):
        super().__init__()
        self.win, self.note = win, note
        self.dirty = False
        self.loading = False
        self.preview = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        lay.addWidget(self.stack)
        self.plain_view = QPlainTextEdit(readOnly=True)
        self.plain_view.setPlaceholderText("")
        self.cover = QPushButton(objectName="SecretCover")
        self.cover.setCursor(Qt.PointingHandCursor)
        self.cover.clicked.connect(self.uncover)
        self._make_editor()
        self.timer = QTimer(self, singleShot=True, interval=SAVE_DELAY_MS, timeout=self.save)

    def _make_editor(self):
        old = getattr(self, "edit", None)
        if old is not None:
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.removeWidget(self.plain_view)
        self.stack.removeWidget(self.cover)
        if self.note.kind == "text":
            self.edit = CodeEdit(self.win)
        else:
            self.edit = RichEdit(self.win)
            self.edit.play_video.connect(self.win.play_video)
        self.edit.setLineWrapMode(self.edit.LineWrapMode.WidgetWidth if self.win.cfg["wrap"]
                                  else self.edit.LineWrapMode.NoWrap)
        self.stack.addWidget(self.edit)
        self.stack.addWidget(self.plain_view)
        self.stack.addWidget(self.cover)
        self.load_content()
        self.recover()
        self.edit.textChanged.connect(self._changed)
        self.edit.cursorPositionChanged.connect(self.win.update_status)

    def load_content(self):
        self.loading = True
        try:
            if self.note.kind == "text":
                self.edit.setPlainText(self.note.text)
            elif self.note.html:
                self.edit.setHtml(self.note.html)
            else:
                self.edit.setPlainText(self.note.text)
            if self.note.kind == "rich":
                self.edit.comfy()
            self.edit.document().setModified(False)
        finally:
            self.loading = False

    def reload(self, note: Note):
        pos = self.edit.textCursor().position()
        bar = self.edit.verticalScrollBar().value()
        self.note = note
        self.load_content()
        c = self.edit.textCursor()
        c.setPosition(min(pos, len(self.edit.toPlainText())))
        self.edit.setTextCursor(c)
        self.edit.verticalScrollBar().setValue(bar)
        self.dirty = False

    def _changed(self):
        if self.loading:
            return
        self.dirty = True
        self.timer.start()
        self.win.on_tab_dirty(self)

    def collect(self):
        if self.note.kind == "text":
            self.note.text = self.edit.toPlainText()
            self.note.html = ""
        else:
            self.note.html = self.edit.toHtml()
            self.note.text = self.edit.toPlainText().replace("￼", "")

    def save(self):
        if not self.dirty:
            return
        self.timer.stop()
        self.collect()
        try:
            self.win.store.save(self.note)
            self.dirty = False
            self.win.on_saved(self)
        except OSError as e:
            self.win.status(f"⚠ 저장 실패 — 다시 시도합니다: {e}")
            self.timer.start(3000)

    def recover(self):
        """비밀 메모는 다른 탭으로 갔다 오면 다시 가린다."""
        if self.note.secret:
            t = self.win.t
            self.cover.setIcon(icons.icon("eye", t["text2"]))
            self.cover.setText("  비밀 메모 — 눌러서 보기 (Enter)")
            self.stack.setCurrentWidget(self.cover)
        elif self.stack.currentWidget() is self.cover:
            self.stack.setCurrentWidget(self.edit)

    def uncover(self):
        self.stack.setCurrentWidget(self.edit)
        self.edit.setFocus()

    def covered(self) -> bool:
        return self.stack.currentWidget() is self.cover

    def show_plain(self, on: bool):
        if self.note.kind != "rich":
            return
        if on:
            self.plain_view.setFont(mono_font(self.win.cfg["font_pt"]))
            self.plain_view.setPlainText(self.edit.toPlainText().replace("￼", ""))
            self.stack.setCurrentWidget(self.plain_view)
        else:
            self.stack.setCurrentWidget(self.edit)

    def showing_plain(self) -> bool:
        return self.stack.currentWidget() is self.plain_view


# ====================================================================== 목록·분류
class NoteTree(QTreeWidget):
    files_dropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)

    def mimeData(self, items):
        md = QMimeData()
        md.setData(IDS_MIME, QByteArray(json.dumps([i.data(0, Qt.UserRole) for i in items]).encode()))
        return md

    def mimeTypes(self):
        return [IDS_MIME, "text/uri-list"]

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            self.files_dropped.emit([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
            e.acceptProposedAction()
        else:
            e.ignore()


class CategoryList(QListWidget):
    ids_dropped = Signal(object, list)   # (분류 key, ids)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasFormat(IDS_MIME) else e.ignore()

    def dragMoveEvent(self, e):
        it = self.itemAt(e.position().toPoint())
        if e.mimeData().hasFormat(IDS_MIME) and it and it.data(Qt.UserRole)[0] in ("cat", "none", "trash", "pinned"):
            self.setCurrentItem(it) if False else None
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e):
        it = self.itemAt(e.position().toPoint())
        if it and e.mimeData().hasFormat(IDS_MIME):
            ids = json.loads(bytes(e.mimeData().data(IDS_MIME)).decode())
            self.ids_dropped.emit(it.data(Qt.UserRole), ids)
            e.acceptProposedAction()


class _CaptureHider(QObject):
    """새로 뜨는 Hushpad 창(대화상자 포함)도 캡처에서 숨김."""

    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg

    win = None

    def eventFilter(self, obj, ev):
        if self.win is not None and ev.type() in (QEvent.KeyPress, QEvent.MouseButtonPress):
            self.win._last_input = time.time()
        if ev.type() == QEvent.Show and isinstance(obj, QWidget) and obj.isWindow() \
                and self.cfg.get("hide_from_capture", True) and not isinstance(obj, capture.RegionOverlay):
            exclude_from_capture(obj, True)
        return False


# ====================================================================== 주 창
class MainWindow(QMainWindow):
    def __init__(self, store: Store, cfg, app_icon: QIcon):
        super().__init__()
        self.store, self.cfg = store, cfg
        self.cfg.setdefault("hide_from_capture", True)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon)
        self._force_plain = False
        self._filter = ("all",)
        self._recorder = None
        self._hotkeys = []
        self.hider = _CaptureHider(cfg)
        QApplication.instance().installEventFilter(self.hider)
        self.t = theme.tokens(cfg.get("theme", "auto"))
        self._themed = []   # (위젯/동작, 아이콘 이름, 색 키)
        self._quitting = False
        self.locked = False
        self._last_input = time.time()
        self.hider.win = self

        self._build_ui()
        self._build_actions()
        self.palette_dlg = CommandPalette(self)
        self._setup_tray()
        self.idle_timer = QTimer(self, interval=20000, timeout=self._idle_check)
        self.idle_timer.start()
        self.apply_theme()
        try:
            QApplication.styleHints().colorSchemeChanged.connect(
                lambda *_: self.cfg.get("theme", "auto") == "auto" and self.apply_theme())
        except Exception:
            pass
        self.list_timer = QTimer(self, singleShot=True, interval=150, timeout=self.refresh_list)
        self.scan_timer = QTimer(self, interval=3000, timeout=self.scan_remote)
        self.scan_timer.start()
        self.refresh_categories()
        self.refresh_list()
        self._restore_state()
        if store.broken:
            QTimer.singleShot(500, lambda: QMessageBox.warning(
                self, APP_NAME, f"읽을 수 없는 메모 파일 {len(store.broken)}개가 있습니다 (다른 암호이거나 손상됨):\n"
                + "\n".join(store.broken[:10])))
        try:
            store.daily_backup(LOCAL_DIR / "backups")
        except Exception:
            pass

    # ------------------------------------------------------------ 화면 구성
    def _build_ui(self):
        left = QWidget(objectName="Sidebar")
        left.setAttribute(Qt.WA_StyledBackground, True)
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 10, 8, 6)
        lv.setSpacing(4)
        brand = QHBoxLayout()
        self.brand_icon = QLabel()
        self.brand_icon.setPixmap(QIcon(str(resource("assets", "app.png"))).pixmap(20, 20))
        brand.addWidget(self.brand_icon)
        brand.addWidget(QLabel("Hushpad", objectName="Brand"))
        brand.addStretch(1)
        self.shield = QLabel()
        self.shield.setToolTip("모든 메모가 암호화되어 저장됩니다")
        brand.addWidget(self.shield)
        lv.addLayout(brand)
        lv.addSpacing(4)
        self.search = QLineEdit(objectName="Search", placeholderText="메모 찾기")
        self.search.setToolTip("메모 찾기  Ctrl+E · 모든 곳에서 찾기 Ctrl+K")
        self.search.setClearButtonEnabled(True)
        self.search_act = self.search.addAction(QIcon(), QLineEdit.LeadingPosition)
        self._themed.append((self.search_act, "search", "muted"))
        self.search.textChanged.connect(lambda: self.list_timer.start())
        self.search.returnPressed.connect(self._open_first_result)
        self.search.setMinimumHeight(32)
        lv.addWidget(self.search)
        hrow = QHBoxLayout()
        hrow.setContentsMargins(0, 0, 0, 0)
        hrow.addWidget(QLabel("보관함", objectName="SectionLabel"))
        hrow.addStretch(1)
        self._cat_header = hrow
        lv.addLayout(hrow)
        self.cats = CategoryList()
        self.cats.setObjectName("CatList")
        self.cats.setIconSize(QSize(16, 16))
        self.cats.setItemDelegate(CountDelegate(self))
        self.cats.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.cats.currentItemChanged.connect(self._cat_changed)
        self.cats.ids_dropped.connect(self._drop_on_category)
        self.cats.setContextMenuPolicy(Qt.CustomContextMenu)
        self.cats.customContextMenuRequested.connect(self._cat_menu)
        lv.addWidget(self.cats)
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(QLabel("메모", objectName="SectionLabel"))
        row.addStretch(1)
        self.sort = QComboBox()
        self.sort.addItem("고친 순", "updated")
        self.sort.addItem("만든 순", "created")
        self.sort.addItem("제목 순", "title")
        i = self.sort.findData(self.cfg.get("sort", "updated"))
        self.sort.setCurrentIndex(max(0, i))
        self.sort.currentIndexChanged.connect(self._sort_changed)
        self.add_cat_btn = QPushButton(objectName="Ghost")
        self.add_cat_btn.setToolTip("새 분류")
        self.add_cat_btn.clicked.connect(self.new_category)
        self._themed.append((self.add_cat_btn, "tag", "text2"))
        row.addWidget(self.sort)
        self._cat_header.addWidget(self.add_cat_btn)
        lv.addLayout(row)
        self.tree = NoteList(self)
        self.tree.itemClicked.connect(lambda it: self.open_note(it.data(Qt.UserRole), preview=True))
        self.tree.itemActivated.connect(lambda it: self.open_note(it.data(Qt.UserRole), preview=False))
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._list_menu)
        self.tree.files_dropped.connect(self.import_files)
        lv.addWidget(self.tree, 1)

        right = QWidget()
        rv = QVBoxLayout(right)
        rv.setContentsMargins(0, 0, 0, 0)
        rv.setSpacing(0)
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.setUsesScrollButtons(True)
        self.tabs.tabBar().setElideMode(Qt.ElideRight)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self._tab_changed)
        self.tabs.tabBar().tabBarDoubleClicked.connect(self._tab_dbl)
        self.tabs.tabBar().setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.tabBar().customContextMenuRequested.connect(self._tab_menu)
        newbtn = QToolButton(objectName="TabCorner")
        newbtn.setToolTip("새 메모 (Ctrl+N)")
        self._themed.append((newbtn, "plus", "text2"))
        newbtn.clicked.connect(lambda: self.new_note("rich"))
        self.tabs.setCornerWidget(newbtn, Qt.TopRightCorner)
        rv.addWidget(self.tabs, 1)
        self.empty = EmptyState(self)
        rv.addWidget(self.empty, 1)

        # 찾기·바꾸기 막대
        self.findbar = QWidget(objectName="FindBar")
        self.findbar.setAttribute(Qt.WA_StyledBackground, True)
        fl = QHBoxLayout(self.findbar)
        fl.setContentsMargins(10, 6, 10, 6)
        self.find_in = QLineEdit(placeholderText="이 메모에서 찾기")
        self.repl_in = QLineEdit(placeholderText="바꿀 내용")
        b_prev, b_next = QPushButton("▲"), QPushButton("▼")
        b_rep, b_all, b_close = QPushButton("바꾸기"), QPushButton("모두 바꾸기"), QPushButton("✕")
        for b in (b_prev, b_next, b_close):
            b.setFixedWidth(32)
        for w in (self.find_in, b_prev, b_next, self.repl_in, b_rep, b_all, b_close):
            fl.addWidget(w)
        self.find_in.returnPressed.connect(lambda: self.find_next(False))
        b_next.clicked.connect(lambda: self.find_next(False))
        b_prev.clicked.connect(lambda: self.find_next(True))
        b_rep.clicked.connect(self.replace_one)
        b_all.clicked.connect(self.replace_all)
        b_close.clicked.connect(self.findbar.hide)
        self.findbar.hide()
        rv.addWidget(self.findbar)

        self.split = QSplitter()
        self.split.addWidget(left)
        self.split.addWidget(right)
        self.split.setStretchFactor(1, 1)
        self.split.setSizes([300, 940])
        self.split.setHandleWidth(1)
        self.split.setChildrenCollapsible(False)
        left.setMinimumWidth(230)
        self.central = QStackedWidget()
        self.central.addWidget(self.split)
        self.lockpage = self._build_lockpage()
        self.central.addWidget(self.lockpage)
        self.setCentralWidget(self.central)
        self.status_lbl = QLabel()
        self.statusBar().addPermanentWidget(self.status_lbl)

    def _act(self, menu, text, slot, key=None, checkable=False, checked=False, tip=""):
        a = QAction(text, self)
        if key:
            a.setShortcut(QKeySequence(key))
            a.setShortcutContext(Qt.WindowShortcut)
        if checkable:
            a.setCheckable(True)
            a.setChecked(checked)
            a.toggled.connect(slot)
        else:
            a.triggered.connect(lambda _=False: slot())
        if tip:
            a.setStatusTip(tip)
        if menu is not None:
            menu.addAction(a)
        self.addAction(a)
        return a

    def _build_actions(self):
        mb = self.more_menu = QMenu(self)
        self.menuBar().hide()
        m = mb.addMenu("파일")
        self.a_new = self._act(m, "새 서식 메모", lambda: self.new_note("rich"), "Ctrl+N")
        self.a_new_text = self._act(m, "새 텍스트 메모 (HTML·JSON·코드)", lambda: self.new_note("text"), "Ctrl+Shift+N")
        self._act(m, "탭 닫기 (메모는 목록에 남음)", lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        m.addSeparator()
        self._act(m, "Windows 메모장 탭 가져오기...", self.import_notepad)
        self._act(m, "파일 가져오기 (txt·json·html…)...", self._import_files_dialog)
        self._act(m, "선택한 메모 내보내기...", lambda: self.export_notes(self.selected_ids() or self._cur_ids()))
        m.addSeparator()
        self._act(m, "보관 폴더 열기", lambda: os.startfile(str(self.store.folder)))
        self._act(m, "보관 폴더 바꾸기/옮기기...", self.change_folder)
        self._act(m, "암호 바꾸기...", self.change_passphrase)
        m.addSeparator()
        self._act(m, "잠그기", self.lock, "Ctrl+L")
        self._act(m, "끝내기", self.quit_app, "Ctrl+Q")

        m = mb.addMenu("편집")
        self._act(m, "서식 없이 복사 (텍스트만)", lambda: self.copy_selection(self._cur_editor(), plain=True),
                  "Ctrl+Shift+C")
        self._act(m, "서식 없이 붙여넣기", self.paste_plain, "Ctrl+Shift+V")
        self.a_plain_paste = self._act(m, "늘 텍스트만 붙여넣기", self._toggle_plain_paste, checkable=True,
                                       checked=self.cfg["plain_paste"])
        m.addSeparator()
        self._act(m, "메모 전체 복사 — 서식 포함", lambda: self.copy_all(plain=False), "Ctrl+Alt+C")
        self._act(m, "메모 전체 복사 — 텍스트만", lambda: self.copy_all(plain=True), "Ctrl+Alt+Shift+C")
        m.addSeparator()
        self._act(m, "선택 부분 서식 지우기", self.clear_format, "Ctrl+Space")
        self._act(m, "굵게", self.toggle_bold, "Ctrl+B")
        m.addSeparator()
        self._act(m, "찾기", self.show_find, "Ctrl+F")
        self._act(m, "바꾸기", lambda: self.show_find(replace=True), "Ctrl+H")
        self._act(m, "다음 찾기", lambda: self.find_next(False), "F3")
        self._act(m, "메모 목록에서 찾기", lambda: (self.search.setFocus(), self.search.selectAll()), "Ctrl+E")
        m.addSeparator()
        self._act(m, "JSON 보기 좋게 정리", self.json_pretty, "Ctrl+Alt+J")
        self._act(m, "JSON 한 줄로 줄이기", self.json_compact)

        m = mb.addMenu("메모")
        self._act(m, "이름 정하기...", lambda: self.rename_note(self._cur_id()), "F2")
        self._act(m, "분류 정하기...", lambda: self.pick_category(self.selected_ids() or self._cur_ids()), "Ctrl+M")
        self._act(m, "고정/고정 풀기", lambda: self.toggle_pin(self.selected_ids() or self._cur_ids()), "Ctrl+P")
        self._act(m, "비밀 메모 켜기/끄기", lambda: self.toggle_secret(self.selected_ids() or self._cur_ids()))
        self._act(m, "서식 ↔ 텍스트 메모로 바꾸기", self.convert_kind)
        self._act(m, "이전 버전 보기...", lambda: self.show_history(self._cur_id()), "Ctrl+Shift+H")
        m.addSeparator()
        self._act(m, "선택한 메모 합치기", lambda: self.merge(self.selected_ids()), "Ctrl+Shift+M")
        self._act(m, "휴지통으로", lambda: self.trash_ids(self.selected_ids() if self.tree.hasFocus()
                                                         else self._cur_ids()), "Ctrl+Del")

        m = mb.addMenu("캡처")
        self._act(m, "📷 영역 스크린샷", lambda: self.screenshot("region"), "Ctrl+Shift+S",
                  tip="Hushpad 창은 찍히지 않습니다. 다른 곳에서도 Ctrl+Alt+S")
        self._act(m, "🖥 화면 전체 스크린샷", lambda: self.screenshot("full"))
        self._act(m, "🎬 화면 녹화 (짧은 동영상)", self.record_video, "Ctrl+Shift+R",
                  tip="다른 곳에서도 Ctrl+Alt+R")
        m.addSeparator()
        self._act(m, "다른 프로그램의 캡처·화면 공유에서 Hushpad 창 숨기기", self._toggle_hide_capture,
                  checkable=True, checked=self.cfg.get("hide_from_capture", True))

        m = mb.addMenu("보기")
        self.a_plainview = self._act(m, "텍스트만 보기 (서식 메모)", self._toggle_plain_view, "Ctrl+T",
                                     checkable=True)
        self._act(m, "자동 줄 바꿈", self._toggle_wrap, "Alt+Z", checkable=True, checked=self.cfg["wrap"])
        self._act(m, "글자 크게", lambda: self._zoom(1), "Ctrl+=")
        self._act(m, "글자 작게", lambda: self._zoom(-1), "Ctrl+-")
        self._act(m, "목록 보이기/숨기기", self._toggle_list, "Ctrl+\\")
        self._act(m, "항상 위에 두기", self._toggle_topmost, "Ctrl+Alt+T", checkable=True)
        m.addSeparator()
        tm = m.addMenu("테마")
        grp = QActionGroup(self)
        for key, label in (("auto", "시스템 따라가기"), ("light", "밝게"), ("dark", "어둡게")):
            a = tm.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.cfg.get("theme", "auto") == key)
            a.triggered.connect(lambda _=False, k=key: self.set_theme(k))
            grp.addAction(a)
        self.a_palette = self._act(m, "명령·메모 찾기 (명령 팔레트)", self.open_palette, "Ctrl+K")
        m.addSeparator()
        self._act(m, "다음 탭", lambda: self._cycle(1), "Ctrl+Tab")
        self._act(m, "이전 탭", lambda: self._cycle(-1), "Ctrl+Shift+Tab")

        m = mb.addMenu("보안")
        self._act(m, "복사한 내용을 Windows 클립보드 기록·클라우드에 남기지 않기", self._toggle_clip_private,
                  checkable=True, checked=self.cfg["clip_private"])
        lm = m.addMenu("자리 비우면 잠그기")
        lgrp = QActionGroup(self)
        for mins, label in ((0, "끔"), (5, "5분"), (10, "10분"), (30, "30분")):
            a = lm.addAction(label)
            a.setCheckable(True)
            a.setChecked(self.cfg.get("lock_idle_min", 0) == mins)
            a.triggered.connect(lambda _=False, v=mins: self.cfg.__setitem__("lock_idle_min", v))
            lgrp.addAction(a)
        self._act(m, "Windows를 잠그면 함께 잠그기", lambda on: self.cfg.__setitem__("lock_on_winlock", on),
                  checkable=True, checked=self.cfg.get("lock_on_winlock", False))
        self._act(m, "창을 닫으면 트레이에 남기 (단축키 계속 동작)", lambda on: self.cfg.__setitem__("close_to_tray", on),
                  checkable=True, checked=self.cfg.get("close_to_tray", True))
        self._act(m, "Windows 시작할 때 실행", self._toggle_autostart, checkable=True, checked=self._autostart_on())
        m.addSeparator()
        self.a_clear = self._act(m, "비밀 메모에서 복사하면 30초 뒤 클립보드 비우기", self._toggle_secret_clear,
                                 checkable=True, checked=self.cfg["secret_clear_sec"] > 0)
        m.addSeparator()
        self._act(m, "이 PC에서 암호 잊기 (다음 실행 때 다시 물음)", self.forget_here)

        tb = QToolBar("도구", objectName="TopBar")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setContextMenuPolicy(Qt.PreventContextMenu)
        self.addToolBar(tb)
        new_btn = QToolButton(objectName="Primary")
        new_btn.setText("새 메모")
        new_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        new_btn.setToolTip("새 서식 메모  Ctrl+N\n▾ 코드 메모(HTML·JSON)  Ctrl+Shift+N")
        new_btn.setPopupMode(QToolButton.MenuButtonPopup)
        nm = QMenu(new_btn)
        nm.addAction(self.a_new)
        nm.addAction(self.a_new_text)
        new_btn.setMenu(nm)
        new_btn.clicked.connect(lambda: self.new_note("rich"))
        self._themed.append((new_btn, "plus", "accent_text"))
        tb.addWidget(new_btn)
        self.a_new.setText("새 서식 메모")
        self.a_new_text.setText("새 코드 메모 (HTML·JSON·키)")
        self._themed += [(self.a_new, "note", "text2"), (self.a_new_text, "code", "text2")]
        tb.addSeparator()

        def tbtn(icon, tip, slot, color="text2"):
            a = QAction(tip.split("  ")[0], self)
            a.setToolTip(tip)
            a.triggered.connect(lambda _=False: slot())
            tb.addAction(a)
            self._themed.append((a, icon, color))
            return a
        tbtn("copy", "텍스트만 복사  Ctrl+Shift+C", lambda: self.copy_selection(self._cur_editor(), plain=True))
        tbtn("paste", "텍스트만 붙여넣기  Ctrl+Shift+V", self.paste_plain)
        self.a_tb_plain = QAction("늘 텍스트만 붙여넣기", self)
        self.a_tb_plain.setCheckable(True)
        self.a_tb_plain.setChecked(self.cfg["plain_paste"])
        self.a_tb_plain.toggled.connect(lambda on: self.a_plain_paste.setChecked(on))
        tb.addAction(self.a_tb_plain)
        self._themed.append((self.a_tb_plain, "text", "text2"))
        tb.addSeparator()
        tbtn("camera", "영역 스크린샷  Ctrl+Shift+S · 어디서든 Ctrl+Alt+S", lambda: self.screenshot("region"))
        self.a_tb_rec = tbtn("video", "화면 녹화  Ctrl+Shift+R · 어디서든 Ctrl+Alt+R", self.record_video)
        tb.addSeparator()
        tbtn("history", "이전 버전  Ctrl+Shift+H", lambda: self.show_history(self._cur_id()))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        self.palette_btn = QPushButton("  찾기·명령…", objectName="CommandBtn")
        self.palette_btn.setCursor(Qt.PointingHandCursor)
        self.palette_btn.setToolTip("메모와 모든 명령 찾기  Ctrl+K")
        kl = QHBoxLayout(self.palette_btn)
        kl.setContentsMargins(0, 0, 8, 0)
        kl.addStretch(1)
        kl.addWidget(QLabel("Ctrl+K", objectName="Kbd"))
        self.palette_btn.clicked.connect(self.open_palette)
        self._themed.append((self.palette_btn, "search", "muted"))
        tb.addWidget(self.palette_btn)
        tb.addWidget(QLabel(" "))
        more = QToolButton()
        more.setToolTip("메뉴 — 파일·편집·메모·캡처·보기·보안")
        more.setPopupMode(QToolButton.InstantPopup)
        more.setMenu(self.more_menu)
        more.setStyleSheet("QToolButton::menu-indicator { image: none; width: 0; }")
        self._themed.append((more, "more", "text2"))
        tb.addWidget(more)
        self._sync_paste_label()

        QShortcut(QKeySequence("Delete"), self.tree, activated=lambda: self._list_delete_key())

    # ------------------------------------------------------------ 상태 저장·복원
    def _restore_state(self):
        g = self.cfg.get("geometry")
        if g:
            self.restoreGeometry(QByteArray.fromBase64(g.encode()))
        else:
            self.resize(1280, 800)
        s = self.cfg.get("splitter")
        if s:
            self.split.restoreState(QByteArray.fromBase64(s.encode()))
        for nid in self.cfg.get("open_tabs", []):
            n = self.store.notes.get(nid)
            if n and n.deleted is None:
                self._add_tab(n)
        cur = self.cfg.get("current_tab")
        i = self._tab_index(cur) if cur else -1
        if i >= 0:
            self.tabs.setCurrentIndex(i)
        self._update_empty()
        QTimer.singleShot(0, lambda: (self._cur_tab().edit.setFocus() if self._cur_tab() else self.tree.setFocus()))

    def save_state(self):
        self.cfg["geometry"] = bytes(self.saveGeometry().toBase64()).decode()
        self.cfg["splitter"] = bytes(self.split.saveState().toBase64()).decode()
        self.cfg["open_tabs"] = [self.tabs.widget(i).note.id for i in range(self.tabs.count())
                                 if not self.tabs.widget(i).preview or self.tabs.widget(i).dirty]
        t = self._cur_tab()
        self.cfg["current_tab"] = t.note.id if t else ""
        try:
            self.cfg.save()
        except OSError:
            pass

    def save_all(self):
        for i in range(self.tabs.count()):
            self.tabs.widget(i).save()

    def closeEvent(self, e):
        self.save_all()
        self.save_state()
        if not self._quitting and self.cfg.get("close_to_tray", True) and self.tray is not None:
            e.ignore()
            self.hide()
            if not self.cfg.get("tray_told"):
                self.cfg["tray_told"] = True
                self.tray.showMessage(APP_NAME, "트레이에서 계속 실행 중이에요. Ctrl+Alt+N 새 메모 · Ctrl+Alt+M 클립보드를 메모로",
                                      QSystemTrayIcon.Information, 5000)
            return
        if self._recorder is not None:
            self._recorder.stop()
        self._unregister_hotkeys()
        if self.tray is not None:
            self.tray.hide()
        super().closeEvent(e)
        QApplication.instance().quit()

    def quit_app(self):
        self._quitting = True
        self.close()

    def showEvent(self, e):
        super().showEvent(e)
        theme.style_titlebar(self, self.t)
        if self.cfg.get("hide_from_capture", True):
            exclude_from_capture(self, True)
        if not self._hotkeys:
            self._register_hotkeys()
            try:
                ctypes.windll.wtsapi32.WTSRegisterSessionNotification(wintypes.HWND(int(self.winId())), 0)
            except Exception:
                pass

    # ------------------------------------------------------------ 전역 단축키
    def _register_hotkeys(self):
        hwnd = int(self.winId())
        failed = []
        for hid, (name, vk) in HOTKEYS.items():
            if ctypes.windll.user32.RegisterHotKey(wintypes.HWND(hwnd), hid, 0x0001 | 0x0002 | 0x4000, vk):
                self._hotkeys.append(hid)
            else:
                failed.append("Ctrl+Alt+" + chr(vk))
        if failed:
            self.status("다른 프로그램이 이미 쓰는 단축키라 등록하지 못함: " + ", ".join(failed))

    def _unregister_hotkeys(self):
        hwnd = int(self.winId())
        for hid in self._hotkeys:
            ctypes.windll.user32.UnregisterHotKey(wintypes.HWND(hwnd), hid)
        self._hotkeys = []

    def nativeEvent(self, etype, message):
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == WM_HOTKEY and msg.wParam in HOTKEYS:
                name = HOTKEYS[msg.wParam][0]
                fn = {"shot": lambda: self.screenshot("region"), "record": self.record_video,
                      "quick": self.quick_note, "clip": self.clip_to_note}[name]
                QTimer.singleShot(0, fn)
                return True, 0
            if msg.message == WM_WTSSESSION_CHANGE and msg.wParam == 7 and self.cfg.get("lock_on_winlock"):
                QTimer.singleShot(0, self.lock)
        except Exception:
            pass
        return super().nativeEvent(etype, message)

    # ------------------------------------------------------------ 빠른 메모·트레이·잠금
    def _setup_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip("Hushpad — 암호화 메모")
        m = QMenu()
        m.addAction("열기", self.bring_to_front)
        m.addAction("새 메모   Ctrl+Alt+N", self.quick_note)
        m.addAction("클립보드를 메모로   Ctrl+Alt+M", self.clip_to_note)
        m.addSeparator()
        m.addAction("스크린샷   Ctrl+Alt+S", lambda: self.screenshot("region"))
        m.addAction("화면 녹화   Ctrl+Alt+R", self.record_video)
        m.addSeparator()
        m.addAction("잠그기", self.lock)
        m.addAction("끝내기", self.quit_app)
        self._tray_menu = m
        self.tray.setContextMenu(m)
        self.tray.activated.connect(
            lambda r: self.bring_to_front() if r in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick) else None)
        self.tray.show()

    def quick_note(self):
        self.bring_to_front()
        if self.locked:
            return
        t = self._cur_tab()
        if t and t.note.is_empty() and not t.note.title:
            t.edit.setFocus()
            return
        self.new_note("rich")

    def clip_to_note(self):
        """지금 클립보드 내용을 창을 띄우지 않고 새 메모로 저장."""
        md = QApplication.clipboard().mimeData()
        if md is None:
            return
        img = QImage(md.imageData()) if md.hasImage() else QImage()
        text = md.text() if md.hasText() else ""
        if not img.isNull() and not text.strip():
            from .common import image_to_data_url
            html = f'<p>📋 클립보드 {time.strftime("%m.%d %H:%M")}</p><p><img src="{image_to_data_url(img)}" width="{min(img.width(), 900)}"></p>'
            n = self.store.create(kind="rich", html=html, text=f"📋 클립보드 {time.strftime('%m.%d %H:%M')}")
            what = f"이미지 {img.width()}×{img.height()}"
        elif text.strip():
            looks_code = text.lstrip()[:1] in "{[<" or "=" in text.split("\n", 1)[0] or "\t" in text
            if md.hasHtml() and not looks_code:
                n = self.store.create(kind="rich", html=md.html(), text=text)
            else:
                n = self.store.create(kind="text", text=text)
            what = f"{len(text):,}자"
        else:
            self._notify("클립보드가 비어 있어요")
            return
        self.list_timer.start()
        self._notify(f"클립보드를 메모로 저장했어요 ({what})")

    def _notify(self, msg):
        if self.isVisible() and self.isActiveWindow():
            self.status(msg)
        elif self.tray is not None:
            self.tray.showMessage(APP_NAME, msg, QSystemTrayIcon.Information, 2500)
        else:
            self.status(msg)

    def _build_lockpage(self):
        w = QWidget(objectName="EmptyState")
        w.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(w)
        lay.addStretch(3)
        self.lock_icon = QLabel(alignment=Qt.AlignCenter)
        lay.addWidget(self.lock_icon)
        lay.addWidget(QLabel("잠겨 있어요", objectName="EmptyTitle", alignment=Qt.AlignCenter))
        lay.addWidget(QLabel("보관 폴더 암호를 넣으면 열립니다", objectName="EmptyHint", alignment=Qt.AlignCenter))
        row = QHBoxLayout()
        row.addStretch(1)
        self.lock_pw = QLineEdit(echoMode=QLineEdit.Password, placeholderText="암호")
        self.lock_pw.setFixedWidth(260)
        self.lock_pw.returnPressed.connect(self.unlock)
        ok = QPushButton("열기", objectName="Primary")
        ok.clicked.connect(self.unlock)
        row.addWidget(self.lock_pw)
        row.addWidget(ok)
        row.addStretch(1)
        lay.addSpacing(10)
        lay.addLayout(row)
        self.lock_msg = QLabel("", objectName="EmptyHint", alignment=Qt.AlignCenter)
        lay.addWidget(self.lock_msg)
        lay.addStretch(4)
        return w

    def lock(self):
        if self.locked:
            return
        self.save_all()
        self.locked = True
        self.palette_dlg.close()
        self.findChild(QToolBar, "TopBar").setEnabled(False)
        self.central.setCurrentWidget(self.lockpage)
        self.lock_icon.setPixmap(icons.pixmap("lock", self.t["gold"], 48))
        self.lock_pw.clear()
        self.lock_msg.setText("")
        self.lock_pw.setFocus()

    def unlock(self):
        try:
            key = crypto.unlock_vault(self.store.folder, self.lock_pw.text())
        except Exception:
            key = None
        if key != self.store.key:
            self.lock_msg.setText("암호가 맞지 않아요")
            self.lock_pw.selectAll()
            return
        self.locked = False
        self.lock_pw.clear()
        self.findChild(QToolBar, "TopBar").setEnabled(True)
        self.central.setCurrentWidget(self.split)
        t = self._cur_tab()
        if t:
            t.recover()
        self._last_input = time.time()

    def _idle_check(self):
        mins = self.cfg.get("lock_idle_min", 0)
        if mins and not self.locked and time.time() - self._last_input > mins * 60:
            self.lock()

    def _toggle_topmost(self, on):
        HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
        ctypes.windll.user32.SetWindowPos(wintypes.HWND(int(self.winId())),
                                          wintypes.HWND(HWND_TOPMOST if on else HWND_NOTOPMOST),
                                          0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        self.status("항상 위에 " + ("켜짐" if on else "꺼짐"))

    def _autostart_on(self) -> bool:
        import winreg
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
                winreg.QueryValueEx(k, APP_NAME)
                return True
        except OSError:
            return False

    def _toggle_autostart(self, on):
        import sys
        import winreg
        if on and not getattr(sys, "frozen", False):
            self.status("시작 프로그램 등록은 exe로 실행할 때만 할 수 있어요")
            return
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if on:
                winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, f'"{sys.executable}" --tray')
            else:
                try:
                    winreg.DeleteValue(k, APP_NAME)
                except OSError:
                    pass
        self.status("Windows 시작할 때 " + ("트레이로 실행해요" if on else "실행하지 않아요"))

    def copy_text(self, text, msg=""):
        t = self._cur_tab()
        self._clip(text_mime(text), t.note if t else None)
        if msg:
            self.status(msg)

    def bring_to_front(self):
        if self.isMinimized():
            self.showNormal()
        self.show()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------ 탭
    def _cur_tab(self) -> NoteTab | None:
        w = self.tabs.currentWidget()
        return w if isinstance(w, NoteTab) else None

    def _cur_editor(self):
        t = self._cur_tab()
        return t.edit if t else None

    def _cur_id(self):
        t = self._cur_tab()
        return t.note.id if t else None

    def _cur_ids(self):
        i = self._cur_id()
        return [i] if i else []

    def _tab_index(self, nid) -> int:
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).note.id == nid:
                return i
        return -1

    def tab_label(self, note: Note) -> str:
        if note.title:
            base = note.title
        elif note.secret:
            base = "비밀 메모"
        else:
            fl = note.first_line()
            base = (fl[:22] + ("…" if len(fl) > 22 else "")) if fl else ("(이미지)" if note.has_images() else "새 메모")
        return base

    def _set_tab_look(self, i: int):
        t = self.tabs.widget(i)
        n = t.note
        self.tabs.setTabText(i, ("● " if t.dirty else "") + self.tab_label(n))
        tk = self.t
        ic = "lock" if n.secret else ("code" if n.kind == "text" else "note")
        self.tabs.setTabIcon(i, icons.icon(ic, tk["gold"] if n.secret else (tk["muted"] if t.preview else tk["text2"])))
        f = self.tabs.tabBar().font()
        self.tabs.tabBar().setTabTextColor(i, QColor(tk["muted"]) if t.preview else QColor())
        self.tabs.setTabToolTip(i, f"{n.display_title()}\n분류: {n.category or '없음'}\n"
                                   f"만든 때: {fmt_full(n.created)}\n고친 때: {fmt_full(n.updated)}"
                                   + ("\n(미리보기 탭 — 고치거나 두 번 클릭하면 고정)" if t.preview else ""))

    def _add_tab(self, note: Note, preview=False) -> int:
        t = NoteTab(self, note)
        t.preview = preview
        i = self.tabs.addTab(t, "")
        self._set_tab_look(i)
        self._update_empty()
        return i

    def open_note(self, nid, preview=False):
        n = self.store.notes.get(nid)
        if not n:
            return
        if n.deleted is not None:
            self.status("휴지통에 있는 메모예요. 오른쪽 클릭 → 되살리기")
            return
        i = self._tab_index(nid)
        if i >= 0:
            if not preview and self.tabs.widget(i).preview:
                self.tabs.widget(i).preview = False
                self._set_tab_look(i)
            self.tabs.setCurrentIndex(i)
            return
        if preview:
            for j in range(self.tabs.count()):
                t = self.tabs.widget(j)
                if t.preview and not t.dirty:
                    self.tabs.removeTab(j)
                    t.deleteLater()
                    i = self.tabs.insertTab(j, NoteTab(self, n), "")
                    self.tabs.widget(i).preview = True
                    self._set_tab_look(i)
                    self.tabs.setCurrentIndex(i)
                    return
        i = self._add_tab(n, preview)
        self.tabs.setCurrentIndex(i)

    def close_tab(self, i):
        if i < 0:
            return
        t = self.tabs.widget(i)
        t.save()
        self.tabs.removeTab(i)
        note = t.note
        t.deleteLater()
        if note.is_empty() and not note.title and note.id in self.store.notes:
            self.store.purge([note.id])   # 아무것도 안 쓴 새 메모는 남기지 않음
            self.list_timer.start()
        self._update_empty()

    # ------------------------------------------------------------ 테마
    MENU_ICONS = {"파일": "note", "편집": "copy", "메모": "note", "캡처": "camera", "보기": "eye", "보안": "shield",
                  "테마": "settings", "자리 비우면 잠그기": "lock"}

    def palette_actions(self):
        """(동작, '메뉴: 이름', 아이콘) — 하위 메뉴 이름뿐인 항목·구분선은 뺀다."""
        out, seen = [], set()

        def walk(menu, path):
            for a in menu.actions():
                if a.isSeparator() or not a.isVisible():
                    continue
                if a.menu() is not None:
                    walk(a.menu(), path + [a.text().replace("&", "")])
                    continue
                txt = a.text().replace("&", "").split("\t")[0].strip()
                if not txt or a is self.a_palette:
                    continue
                label = f"{path[-1]}: {txt}" if path and path[-1] in ("테마", "자리 비우면 잠그기") else txt
                if label in seen:
                    continue
                seen.add(label)
                group = path[-1] if path else ""
                ic = a.icon() if not a.icon().isNull() else icons.icon(self.MENU_ICONS.get(group, "command"),
                                                                       self.t["text2"])
                out.append((a, label, ic))
        walk(self.more_menu, [])
        return out

    def open_palette(self):
        self.palette_dlg.open_()

    def set_theme(self, mode):
        self.cfg["theme"] = mode
        self.apply_theme()

    def apply_theme(self):
        self.t = t = theme.tokens(self.cfg.get("theme", "auto"))
        app = QApplication.instance()
        app.setPalette(theme.palette(t))
        app.setStyleSheet(theme.qss(t))
        for obj, name, ck in self._themed:
            obj.setIcon(icons.icon(name, t[ck]))
        self.shield.setPixmap(icons.pixmap("shield", t["success"], 16))
        self.empty.retheme(t)
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            if hasattr(tab.edit, "retheme"):
                tab.edit.retheme()
            self._set_tab_look(i)
        self.refresh_categories()
        self.tree.viewport().update()
        theme.style_titlebar(self, t)

    def _update_empty(self):
        has = self.tabs.count() > 0
        self.tabs.setVisible(has)
        self.empty.setVisible(not has)

    def _tab_changed(self, i):
        prev = getattr(self, "_prev_tab", None)
        if prev is not None and prev is not self._cur_tab():
            try:
                prev.recover()
            except RuntimeError:
                pass
        self._prev_tab = self._cur_tab()
        t = self._cur_tab()
        self.a_plainview.blockSignals(True)
        self.a_plainview.setChecked(bool(t and t.showing_plain()))
        self.a_plainview.blockSignals(False)
        self.update_status()
        if t:
            self._select_in_list(t.note.id)

    def _tab_dbl(self, i):
        if i < 0:
            self.new_note("rich")
            return
        t = self.tabs.widget(i)
        if t.preview:
            t.preview = False
            self._set_tab_look(i)
        else:
            self.rename_note(t.note.id)

    def _tab_menu(self, pos):
        i = self.tabs.tabBar().tabAt(pos)
        if i < 0:
            return
        nid = self.tabs.widget(i).note.id
        m = QMenu(self)
        m.addAction("이름 정하기...", lambda: self.rename_note(nid))
        m.addAction("분류 정하기...", lambda: self.pick_category([nid]))
        m.addAction("이전 버전 보기...", lambda: self.show_history(nid))
        m.addSeparator()
        m.addAction("탭 닫기", lambda: self.close_tab(self._tab_index(nid)))
        m.addAction("다른 탭 모두 닫기", lambda: self._close_others(nid))
        m.addAction("오른쪽 탭 모두 닫기", lambda: self._close_right(nid))
        m.addSeparator()
        m.addAction("휴지통으로", lambda: self.trash_ids([nid]))
        m.exec(self.tabs.tabBar().mapToGlobal(pos))

    def _close_others(self, nid):
        for i in reversed(range(self.tabs.count())):
            if self.tabs.widget(i).note.id != nid:
                self.close_tab(i)

    def _close_right(self, nid):
        k = self._tab_index(nid)
        for i in reversed(range(k + 1, self.tabs.count())):
            self.close_tab(i)

    def _cycle(self, d):
        if self.tabs.count():
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + d) % self.tabs.count())

    def on_tab_dirty(self, t: NoteTab):
        if t.preview:
            t.preview = False
        self._set_tab_look(self.tabs.indexOf(t))
        self.status_lbl.setText("저장 중…")

    def on_saved(self, t: NoteTab):
        i = self.tabs.indexOf(t)
        if i >= 0:
            self._set_tab_look(i)
        self.list_timer.start()
        self.update_status(saved=True)

    def status(self, msg: str, ms: int = 6000):
        self.statusBar().showMessage(msg, ms)

    def update_status(self, saved=False):
        t = self._cur_tab()
        if not t:
            self.status_lbl.setText("")
            return
        ed = t.edit
        c = ed.textCursor()
        line = c.blockNumber() + 1
        col = c.positionInBlock() + 1
        chars = len(t.note.text) if not t.dirty else ed.document().characterCount() - 1
        kind = "텍스트 메모" if t.note.kind == "text" else "서식 메모"
        state = "저장 중…" if t.dirty else f"저장됨 {time.strftime('%H:%M:%S', time.localtime(t.note.updated))}"
        self.status_lbl.setText(f"{kind} · 줄 {line}, 칸 {col} · {chars:,}자 · {state}")

    # ------------------------------------------------------------ 목록
    def refresh_categories(self):
        cur = self._filter
        self.cats.blockSignals(True)
        self.cats.clear()
        live = [n for n in self.store.notes.values() if n.deleted is None]
        trash = sum(1 for n in self.store.notes.values() if n.deleted is not None)
        entries = [("inbox", "모든 메모", ("all",), len(live)),
                   ("pin", "고정", ("pinned",), sum(1 for n in live if n.pinned)),
                   ("calendar", "오늘", ("today",), sum(1 for n in live if self._is_today(n))),
                   ("archive", "30일 넘게 안 본 메모", ("stale",), sum(1 for n in live if self._is_stale(n))),
                   ("folder", "분류 없음", ("none",), sum(1 for n in live if not n.category))]
        for c in self.store.all_categories():
            entries.append(("tag", c, ("cat", c), sum(1 for n in live if n.category == c)))
        entries.append(("trash", "휴지통", ("trash",), trash))
        sel = None
        t = self.t
        for ic, text, key, cnt in entries:
            it = QListWidgetItem(icons.icon(ic, t["text2"], t["accent_subtle_text"], 16), f"{text}")
            it.setData(Qt.UserRole, key)
            it.setData(Qt.UserRole + 2, cnt)
            it.setText(text)
            self.cats.addItem(it)
            if key == cur:
                sel = it
        if sel is None:
            sel = self.cats.item(0)
            self._filter = ("all",)
        self.cats.setCurrentItem(sel)
        self.cats.blockSignals(False)
        self.cats.setFixedHeight(min(self.cats.count(), 11) * 32 + 6)

    @staticmethod
    def _is_today(n) -> bool:
        a, b = time.localtime(n.updated), time.localtime()
        return a.tm_year == b.tm_year and a.tm_yday == b.tm_yday

    @staticmethod
    def _is_stale(n) -> bool:
        return time.time() - n.updated > 30 * 86400 and not n.pinned

    def _cat_changed(self, cur, _prev):
        if cur is not None:
            self._filter = tuple(cur.data(Qt.UserRole))
            self.refresh_list()

    def _sort_changed(self):
        self.cfg["sort"] = self.sort.currentData()
        self.refresh_list()

    def filtered_notes(self) -> list[Note]:
        f = self._filter
        q = [w for w in self.search.text().lower().split() if w]
        out = []
        for n in self.store.notes.values():
            if f[0] == "trash":
                if n.deleted is None:
                    continue
            elif n.deleted is not None:
                continue
            if f[0] == "pinned" and not n.pinned:
                continue
            if f[0] == "today" and not self._is_today(n):
                continue
            if f[0] == "stale" and not self._is_stale(n):
                continue
            if f[0] == "none" and n.category:
                continue
            if f[0] == "cat" and n.category != f[1]:
                continue
            if q:
                hay = f"{n.title}\n{n.category}\n{n.text}".lower()
                if not all(w in hay for w in q):
                    continue
            out.append(n)
        key = self.sort.currentData()
        if key == "title":
            out.sort(key=lambda n: n.display_title().lower())
        else:
            out.sort(key=lambda n: getattr(n, key), reverse=True)
        out.sort(key=lambda n: not n.pinned)
        return out

    def refresh_list(self):
        selected = set(self.selected_ids())
        cur_tab = self._cur_id()
        open_ids = {self.tabs.widget(i).note.id for i in range(self.tabs.count())}
        key = self.sort.currentData()
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        for n in self.filtered_notes():
            snippet = "" if n.secret else n.snippet()
            if not snippet:
                snippet = "비밀 메모 — 내용 숨김" if n.secret else ("이미지" if n.has_images() else "")
            it = QListWidgetItem()
            it.setData(Qt.UserRole, n.id)
            it.setData(Qt.UserRole + 1, {
                "title": n.display_title(), "snippet": snippet, "category": n.category,
                "time": rel_time(n.created if key == "created" else n.updated),
                "pinned": n.pinned, "secret": n.secret, "kind": n.kind, "open": n.id in open_ids})
            it.setToolTip(f"{n.display_title()}\n만든 때 {fmt_full(n.created)}\n고친 때 {fmt_full(n.updated)}")
            self.tree.addItem(it)
            if n.id in selected or (not selected and n.id == cur_tab):
                it.setSelected(True)
        self.tree.setUpdatesEnabled(True)
        self.refresh_categories()

    def _select_in_list(self, nid):
        for i in range(self.tree.count()):
            it = self.tree.item(i)
            if it.data(Qt.UserRole) == nid:
                self.tree.blockSignals(True)
                self.tree.clearSelection()
                self.tree.setCurrentItem(it)
                self.tree.blockSignals(False)
                return

    def selected_ids(self) -> list[str]:
        return [it.data(Qt.UserRole) for it in self.tree.selectedItems()]

    def _open_first_result(self):
        if self.tree.count():
            self.open_note(self.tree.item(0).data(Qt.UserRole))
            t = self._cur_tab()
            if t:
                t.edit.setFocus()

    def _list_delete_key(self):
        ids = self.selected_ids()
        if not ids:
            return
        if self._filter[0] == "trash":
            self.purge_ids(ids)
        else:
            self.trash_ids(ids)

    def _list_menu(self, pos):
        ids = self.selected_ids()
        if not ids:
            return
        m = QMenu(self)
        if self._filter[0] == "trash":
            m.addAction(f"되살리기 ({len(ids)})", lambda: self.restore_ids(ids))
            m.addAction(f"영구 삭제 ({len(ids)})...", lambda: self.purge_ids(ids))
            m.addSeparator()
            m.addAction("휴지통 비우기...", self.empty_trash)
        else:
            m.addAction("열기", lambda: [self.open_note(i) for i in ids])
            if len(ids) == 1:
                m.addAction("이름 정하기...", lambda: self.rename_note(ids[0]))
            cm = m.addMenu("분류 정하기")
            for c in self.store.all_categories():
                cm.addAction(c, lambda c=c: self.set_category(ids, c))
            cm.addSeparator()
            cm.addAction("새 분류...", lambda: self.pick_category(ids, new=True))
            cm.addAction("분류 없음", lambda: self.set_category(ids, ""))
            m.addAction("고정/고정 풀기", lambda: self.toggle_pin(ids))
            m.addAction("비밀 메모 켜기/끄기", lambda: self.toggle_secret(ids))
            if len(ids) >= 2:
                m.addSeparator()
                m.addAction(f"메모 {len(ids)}개 합치기", lambda: self.merge(ids))
            m.addSeparator()
            m.addAction("텍스트만 복사", lambda: self._copy_notes(ids, True))
            m.addAction("내보내기...", lambda: self.export_notes(ids))
            if len(ids) == 1:
                m.addAction("이전 버전 보기...", lambda: self.show_history(ids[0]))
            m.addSeparator()
            m.addAction(f"휴지통으로 ({len(ids)})", lambda: self.trash_ids(ids))
        m.exec(self.tree.viewport().mapToGlobal(pos))

    def _cat_menu(self, pos):
        it = self.cats.itemAt(pos)
        if not it:
            return
        key = it.data(Qt.UserRole)
        m = QMenu(self)
        if key[0] == "cat":
            m.addAction("분류 이름 바꾸기...", lambda: self.rename_category(key[1]))
            m.addAction("분류 지우기 (메모는 '분류 없음'으로)", lambda: self.delete_category(key[1]))
        elif key[0] == "trash":
            m.addAction("휴지통 비우기...", self.empty_trash)
        m.addAction("새 분류...", self.new_category)
        m.exec(self.cats.mapToGlobal(pos))

    def _drop_on_category(self, key, ids):
        if key[0] == "cat":
            self.set_category(ids, key[1])
        elif key[0] == "none":
            self.set_category(ids, "")
        elif key[0] == "trash":
            self.trash_ids(ids)
        elif key[0] == "pinned":
            for i in ids:
                n = self.store.notes.get(i)
                if n and not n.pinned:
                    n.pinned = True
                    self.store.save(n, touch=False, snapshot=False)
            self.list_timer.start()

    # ------------------------------------------------------------ 메모 다루기
    def _sync_tab_note(self, nid):
        i = self._tab_index(nid)
        if i >= 0:
            t = self.tabs.widget(i)
            t.note = self.store.notes[nid]
            self._set_tab_look(i)

    def _flush(self, ids):
        for nid in ids:
            i = self._tab_index(nid)
            if i >= 0:
                self.tabs.widget(i).save()

    def new_note(self, kind="rich", text="", html=""):
        cat = self._filter[1] if self._filter[0] == "cat" else ""
        n = self.store.create(kind=kind, category=cat, text=text, html=html)
        if self._filter[0] == "trash":
            self._filter = ("all",)
        i = self._add_tab(n)
        self.tabs.setCurrentIndex(i)
        self.tabs.widget(i).edit.setFocus()
        self.list_timer.start()
        return self.tabs.widget(i)

    def rename_note(self, nid):
        n = self.store.notes.get(nid)
        if not n:
            return
        name, ok = QInputDialog.getText(self, "이름 정하기", "메모 이름 (비우면 첫 줄과 만든 때로 자동):", text=n.title)
        if ok:
            self._flush([nid])
            n.title = name.strip()
            self.store.save(n, touch=False, snapshot=False)
            self._sync_tab_note(nid)
            self.list_timer.start()

    def set_category(self, ids, cat):
        self._flush(ids)
        if cat:
            self.store.add_category(cat)
        for nid in ids:
            n = self.store.notes.get(nid)
            if n:
                n.category = cat
                self.store.save(n, touch=False, snapshot=False)
                self._sync_tab_note(nid)
        self.list_timer.start()
        self.status(f"{len(ids)}개 → {cat or '분류 없음'}")

    def pick_category(self, ids, new=False):
        if not ids:
            return
        cats = self.store.all_categories()
        if new or not cats:
            name, ok = QInputDialog.getText(self, "새 분류", "분류 이름:")
        else:
            name, ok = QInputDialog.getItem(self, "분류 정하기", "분류 (새 이름을 써도 됩니다, 비우면 분류 없음):",
                                            cats, 0, True)
        if ok:
            self.set_category(ids, name.strip())

    def new_category(self):
        name, ok = QInputDialog.getText(self, "새 분류", "분류 이름:")
        if ok and name.strip():
            self.store.add_category(name.strip())
            self.refresh_categories()

    def rename_category(self, old):
        name, ok = QInputDialog.getText(self, "분류 이름 바꾸기", "새 이름:", text=old)
        if ok and name.strip() and name.strip() != old:
            self.save_all()
            self.store.rename_category(old, name.strip())
            if self._filter == ("cat", old):
                self._filter = ("cat", name.strip())
            for i in range(self.tabs.count()):
                self._sync_tab_note(self.tabs.widget(i).note.id)
            self.refresh_list()

    def delete_category(self, name):
        self.save_all()
        self.store.remove_category(name)
        if self._filter == ("cat", name):
            self._filter = ("all",)
        for i in range(self.tabs.count()):
            self._sync_tab_note(self.tabs.widget(i).note.id)
        self.refresh_list()

    def toggle_pin(self, ids):
        self._flush(ids)
        ns = [self.store.notes[i] for i in ids if i in self.store.notes]
        on = not all(n.pinned for n in ns)
        for n in ns:
            n.pinned = on
            self.store.save(n, touch=False, snapshot=False)
        self.list_timer.start()

    def toggle_secret(self, ids):
        self._flush(ids)
        ns = [self.store.notes[i] for i in ids if i in self.store.notes]
        on = not all(n.secret for n in ns)
        for n in ns:
            n.secret = on
            self.store.save(n, touch=False, snapshot=False)
            self._sync_tab_note(n.id)
            i = self._tab_index(n.id)
            if i >= 0 and not on:
                self.tabs.widget(i).recover()
        self.list_timer.start()
        self.status("비밀 메모: 목록에 첫 줄이 보이지 않고, 복사하면 30초 뒤 클립보드에서 지워집니다." if on
                    else "비밀 메모를 껐습니다.")

    def trash_ids(self, ids):
        ids = [i for i in ids if i]
        if not ids:
            return
        self._flush(ids)
        for nid in ids:
            i = self._tab_index(nid)
            if i >= 0:
                t = self.tabs.widget(i)
                self.tabs.removeTab(i)
                t.deleteLater()
        empties = [i for i in ids if i in self.store.notes and self.store.notes[i].is_empty()
                   and not self.store.notes[i].title]
        self.store.purge(empties)
        self.store.trash([i for i in ids if i not in empties])
        self._update_empty()
        self.refresh_list()
        self.status(f"{len(ids)}개를 휴지통으로 옮겼어요 (휴지통에서 되살릴 수 있어요)")

    def restore_ids(self, ids):
        self.store.restore(ids)
        self.refresh_list()

    def purge_ids(self, ids):
        if QMessageBox.question(self, "영구 삭제", f"메모 {len(ids)}개를 완전히 지울까요?\n이전 버전까지 지워지고 되돌릴 수 없습니다.") \
                != QMessageBox.Yes:
            return
        self.store.purge(ids)
        self.refresh_list()

    def empty_trash(self):
        ids = [n.id for n in self.store.notes.values() if n.deleted is not None]
        if ids:
            self.purge_ids(ids)

    def merge(self, ids):
        if len(ids) < 2:
            self.status("목록에서 Ctrl/Shift로 메모를 2개 이상 고른 뒤 합치세요.")
            return
        self._flush(ids)
        notes = sorted([self.store.notes[i] for i in ids if i in self.store.notes], key=lambda n: n.created)
        all_text = all(n.kind == "text" for n in notes)
        if all_text:
            parts = [f"──── {n.display_title()} · {fmt_full(n.created)} ────\n{n.text.rstrip()}\n" for n in notes]
            merged = self.store.create(kind="text", text="\n".join(parts), category=notes[0].category,
                                       created=notes[0].created)
        else:
            doc = QTextDocument()
            c = QTextCursor(doc)
            for k, n in enumerate(notes):
                if k:
                    c.insertBlock()
                hf = QTextCharFormat()
                hf.setFontWeight(QFont.Bold)
                hf.setForeground(QColor("#6b5bd2"))
                c.insertText(f"──── {n.display_title()} · {fmt_full(n.created)} ────", hf)
                c.insertBlock()
                c.setCharFormat(QTextCharFormat())
                if n.kind == "rich" and n.html:
                    c.insertFragment(QTextDocumentFragment.fromHtml(n.html))
                else:
                    c.insertText(n.text)
            merged = self.store.create(kind="rich", html=doc.toHtml(), text=doc.toPlainText().replace("￼", ""),
                                       category=notes[0].category, created=notes[0].created)
        merged.title = f"합친 메모 ({len(notes)}개) · {time.strftime('%m-%d %H:%M')}"
        self.store.save(merged, snapshot=False)
        r = QMessageBox.question(self, "합치기", f"메모 {len(notes)}개를 하나로 합쳤어요.\n원래 메모들은 휴지통으로 옮길까요?")
        if r == QMessageBox.Yes:
            self.trash_ids([n.id for n in notes])
        self.refresh_list()
        self.open_note(merged.id)

    def convert_kind(self):
        t = self._cur_tab()
        if not t:
            return
        t.save()
        n = t.note
        if n.kind == "rich":
            if QMessageBox.question(self, "텍스트 메모로", "서식·이미지가 빠지고 글자만 남습니다. 바꿀까요?\n(이전 버전에서 되돌릴 수 있어요)") \
                    != QMessageBox.Yes:
                return
            self.store.snapshot(n, force=True)
            n.kind, n.html = "text", ""
        else:
            n.kind = "rich"
            n.html = ""
        self.store.save(n, snapshot=False)
        t.note = n
        t._make_editor()
        self._set_tab_look(self.tabs.indexOf(t))
        self.list_timer.start()

    def show_history(self, nid):
        n = self.store.notes.get(nid)
        if not n:
            return
        self._flush([nid])
        d = HistoryDialog(self, self.store, n)
        if d.exec() and d.chosen is not None:
            self.store.snapshot(n, force=True)
            snap = d.chosen
            n.kind, n.html, n.text = snap.kind, snap.html, snap.text
            self.store.save(n, snapshot=False)
            i = self._tab_index(nid)
            if i >= 0:
                t = self.tabs.widget(i)
                t.note = n
                t._make_editor()
            self.list_timer.start()
            self.status("이전 버전으로 되돌렸어요. (되돌리기 직전 내용도 이전 버전에 남아 있어요)")

    # ------------------------------------------------------------ 복사·붙여넣기
    def plain_paste_now(self) -> bool:
        return self._force_plain or self.cfg["plain_paste"]

    def _note_of_editor(self, ed):
        for i in range(self.tabs.count()):
            if self.tabs.widget(i).edit is ed:
                return self.tabs.widget(i).note
        return None

    def _clip(self, md: QMimeData, note: Note | None):
        secret = bool(note and note.secret)
        set_clipboard(md, private=self.cfg["clip_private"], strict=secret,
                      clear_after=self.cfg["secret_clear_sec"] if secret else 0)
        if secret and self.cfg["secret_clear_sec"]:
            self.status(f"🔒 비밀 메모 — {self.cfg['secret_clear_sec']}초 뒤 클립보드를 비웁니다")

    def copy_selection(self, ed, plain=False):
        if ed is None:
            return
        t = self._cur_tab()
        if t and t.showing_plain():
            ed = t.plain_view
        c = ed.textCursor()
        if not c.hasSelection():
            return
        note = self._note_of_editor(ed) or (t.note if t else None)
        if plain or isinstance(ed, (QPlainTextEdit,)) and not isinstance(ed, RichEdit):
            text = c.selection().toPlainText().replace("￼", "")
            self._clip(text_mime(text), note)
            if plain:
                self.status("텍스트만 복사했어요")
        else:
            md = ed.createMimeDataFromSelection()
            self._clip(md, note)

    def copy_all(self, plain):
        t = self._cur_tab()
        if not t:
            return
        t.save()
        if plain or t.note.kind == "text":
            self._clip(text_mime(t.edit.toPlainText().replace("￼", "")), t.note)
        else:
            md = QMimeData()
            md.setHtml(t.edit.toHtml())
            md.setText(t.edit.toPlainText().replace("￼", ""))
            self._clip(md, t.note)
        self.status("메모 전체를 " + ("텍스트만" if plain else "서식 포함으로") + " 복사했어요")

    def _copy_notes(self, ids, plain=True):
        self._flush(ids)
        notes = [self.store.notes[i] for i in ids if i in self.store.notes]
        txt = "\n\n".join(n.text for n in notes)
        self._clip(text_mime(txt), notes[0] if len(notes) == 1 else None)
        self.status(f"메모 {len(notes)}개를 텍스트로 복사했어요")

    def copy_image(self, img: QImage):
        md = QMimeData()
        md.setImageData(img)
        self._clip(md, None)

    def paste_plain(self):
        ed = self._cur_editor()
        if ed is None:
            return
        self._force_plain = True
        try:
            ed.paste()
        finally:
            self._force_plain = False

    def _toggle_plain_paste(self, on):
        self.cfg["plain_paste"] = on
        self._sync_paste_label()

    def _sync_paste_label(self):
        on = self.cfg["plain_paste"]
        self.a_tb_plain.blockSignals(True)
        self.a_tb_plain.setChecked(on)
        self.a_tb_plain.blockSignals(False)
        self.a_tb_plain.setToolTip("붙여넣기: " + ("늘 텍스트만 (켜짐)" if on else "서식 유지 — 누르면 늘 텍스트만"))

    def clear_format(self):
        ed = self._cur_editor()
        if not isinstance(ed, RichEdit):
            return
        c = ed.textCursor()
        if not c.hasSelection():
            c.select(QTextCursor.Document)
        text = c.selection().toPlainText().replace("￼", "")
        c.insertText(text, QTextCharFormat())

    def toggle_bold(self):
        ed = self._cur_editor()
        if isinstance(ed, RichEdit):
            ed.setFontWeight(QFont.Normal if ed.fontWeight() > QFont.Normal else QFont.Bold)

    # ------------------------------------------------------------ JSON
    def _json_apply(self, compact: bool):
        t = self._cur_tab()
        if not t:
            return
        ed = t.edit
        c = ed.textCursor()
        whole = not c.hasSelection()
        src = ed.toPlainText() if whole else c.selection().toPlainText()
        try:
            obj = json.loads(src)
        except json.JSONDecodeError as e:
            self.status(f"⚠ JSON 오류: 줄 {e.lineno}, 칸 {e.colno} — {e.msg}", 10000)
            if whole:
                cc = ed.textCursor()
                cc.setPosition(min(e.pos, len(src)))
                ed.setTextCursor(cc)
            return
        out = json.dumps(obj, ensure_ascii=False, separators=(",", ":")) if compact else \
            json.dumps(obj, ensure_ascii=False, indent=2)
        if whole:
            c.select(QTextCursor.Document)
        c.insertText(out)
        self.status("JSON을 " + ("한 줄로 줄였어요" if compact else "정리했어요") + " (Ctrl+Z로 되돌리기)")

    def json_pretty(self):
        self._json_apply(False)

    def json_compact(self):
        self._json_apply(True)

    # ------------------------------------------------------------ 찾기
    def show_find(self, replace=False):
        self.findbar.show()
        ed = self._cur_editor()
        if ed and ed.textCursor().hasSelection():
            self.find_in.setText(ed.textCursor().selectedText())
        self.find_in.setFocus()
        self.find_in.selectAll()

    def find_next(self, back):
        ed = self._cur_editor()
        s = self.find_in.text()
        if not ed or not s:
            return
        flags = QTextDocument.FindBackward if back else QTextDocument.FindFlag(0)
        if not ed.find(s, flags):
            c = ed.textCursor()
            c.movePosition(QTextCursor.End if back else QTextCursor.Start)
            ed.setTextCursor(c)
            if not ed.find(s, flags):
                self.status("찾는 내용이 없어요")

    def replace_one(self):
        ed = self._cur_editor()
        if ed and ed.textCursor().hasSelection() and ed.textCursor().selectedText() == self.find_in.text():
            ed.textCursor().insertText(self.repl_in.text())
        self.find_next(False)

    def replace_all(self):
        ed = self._cur_editor()
        s, r = self.find_in.text(), self.repl_in.text()
        if not ed or not s:
            return
        c = ed.textCursor()
        c.beginEditBlock()
        cc = QTextCursor(ed.document())
        n = 0
        while True:
            cc = ed.document().find(s, cc)
            if cc.isNull():
                break
            cc.insertText(r)
            n += 1
        c.endEditBlock()
        self.status(f"{n}곳을 바꿨어요")

    # ------------------------------------------------------------ 보기
    def _toggle_plain_view(self, on):
        t = self._cur_tab()
        if t:
            t.save()
            t.show_plain(on)

    def _toggle_wrap(self, on):
        self.cfg["wrap"] = on
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i).edit
            ed.setLineWrapMode(ed.LineWrapMode.WidgetWidth if on else ed.LineWrapMode.NoWrap)

    def _zoom(self, d):
        self.cfg["font_pt"] = max(7, min(32, self.cfg["font_pt"] + d))
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i).edit
            if isinstance(ed, RichEdit):
                ed.document().setDefaultFont(body_font(self.cfg["font_pt"]))
            else:
                ed.setFont(mono_font(self.cfg["font_pt"]))
        self.status(f"글자 크기 {self.cfg['font_pt']}pt")

    def _toggle_list(self):
        w = self.split.widget(0)
        w.setVisible(not w.isVisible())

    def _toggle_hide_capture(self, on):
        self.cfg["hide_from_capture"] = on
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                exclude_from_capture(w, on)
        self.status("다른 프로그램의 캡처·화면 공유에 Hushpad 창이 " + ("보이지 않아요" if on else "보입니다"))

    def _toggle_clip_private(self, on):
        self.cfg["clip_private"] = on

    def _toggle_secret_clear(self, on):
        self.cfg["secret_clear_sec"] = 30 if on else 0

    # ------------------------------------------------------------ 캡처
    def _capture_target(self) -> NoteTab:
        t = self._cur_tab()
        if t and t.note.kind == "rich" and not t.showing_plain():
            return t
        t = self.new_note("rich")
        t.edit.insert_plain(f"📷 캡처 {time.strftime('%m-%d %H:%M')}\n")
        return t

    def screenshot(self, mode="region"):
        if self._recorder is not None:
            return
        screen = capture.screen_under_cursor()

        def go():
            pix = capture.grab_screen(screen)
            if mode == "full":
                self._insert_shot(pix.toImage())
                return
            ov = capture.RegionOverlay(screen, pix, "image")
            ov.chosen.connect(lambda r: self._insert_shot(capture.crop(pix, r)))
            ov.start()
            self._overlay = ov
        QTimer.singleShot(60, go)

    def _insert_shot(self, img: QImage):
        t = self._capture_target()
        t.edit.insert_image(img)
        self.copy_image(img)
        self.bring_to_front()
        self.status(f"스크린샷 {img.width()}×{img.height()} — 메모에 넣고 클립보드에도 복사했어요")

    def record_video(self):
        if self._recorder is not None:
            self._recorder.stop()
            return
        screen = capture.screen_under_cursor()
        pix = capture.grab_screen(screen)
        ov = capture.RegionOverlay(screen, pix, "video")
        ov.chosen.connect(lambda r: self._start_record(screen, r))
        ov.start()
        self._overlay = ov

    def _start_record(self, screen, rect):
        try:
            rec = capture.Recorder(screen, rect, fps=self.cfg.get("video_fps", 12),
                                   max_sec=self.cfg.get("video_max_sec", 180))
        except Exception as e:
            QMessageBox.warning(self, "녹화", f"녹화를 시작할 수 없어요.\n{e}")
            return
        self._recorder = rec
        rec.finished.connect(self._video_done)
        rec.failed.connect(self._video_failed)
        rec.cancelled.connect(self._video_cancelled)
        rec.start()
        self.status("🎬 녹화 중 — 빨간 테두리 안이 녹화돼요. 다시 Ctrl+Alt+R 또는 ⏹ 저장으로 끝내기", 0)

    def _video_done(self, data: bytes, first: QImage, secs: float):
        self._recorder = None
        mid = self.store.put_media(data)
        t = self._capture_target()
        t.edit.insert_image(capture.video_thumbnail(first, secs), href=f"owvideo:{mid}")
        self.bring_to_front()
        self.status(f"🎬 동영상 {secs:.0f}초 ({len(data) / 1e6:.1f}MB, 암호화 저장) — 그림을 두 번 클릭하면 재생", 8000)

    def _video_failed(self, msg):
        self._recorder = None
        self.statusBar().clearMessage()
        QMessageBox.warning(self, "녹화", f"녹화에 실패했어요.\n{msg}")

    def _video_cancelled(self):
        self._recorder = None
        self.status("녹화를 취소했어요")

    def play_video(self, mid):
        try:
            data = self.store.get_media(mid)
        except Exception:
            QMessageBox.warning(self, "동영상", "동영상 파일을 찾을 수 없어요 (다른 PC에서 아직 동기화되지 않았을 수 있어요).")
            return
        d = capture.VideoDialog(self, data, "동영상", lambda: self.export_video(mid))
        d.setAttribute(Qt.WA_DeleteOnClose)
        d.show()

    def export_video(self, mid):
        fn, _ = QFileDialog.getSaveFileName(self, "동영상 저장 (암호화되지 않은 파일)", f"{mid}.mp4", "MP4 (*.mp4)")
        if fn:
            Path(fn).write_bytes(self.store.get_media(mid))
            self.status(f"저장: {fn}")

    # ------------------------------------------------------------ 가져오기·내보내기
    def import_notepad(self):
        tabs = notepad_import.read_tabs()
        if not tabs:
            QMessageBox.information(self, "메모장 가져오기", "Windows 메모장 탭을 찾지 못했어요.")
            return
        already = {n.text for n in self.store.notes.values()}
        d = ImportDialog(self, tabs, already)
        if not d.exec():
            return
        chosen = d.selected()
        kind = "text" if d.as_text.isChecked() else "rich"
        cat = "메모장에서 가져옴"
        self.store.add_category(cat)
        for t in chosen:
            title = Path(t.path).name if t.path else ""
            self.store.create(kind=kind, text=t.text, category=cat, title=title, created=t.mtime)
        self._filter = ("cat", cat)
        self.refresh_list()
        self.status(f"메모장 탭 {len(chosen)}개를 가져왔어요 (분류: {cat})")

    def _import_files_dialog(self):
        fns, _ = QFileDialog.getOpenFileNames(self, "가져올 파일", "", "텍스트 파일 (*.*)")
        if fns:
            self.import_files(fns)

    def import_files(self, paths):
        n = 0
        for p in map(Path, paths):
            if not p.is_file() or p.stat().st_size > 20_000_000:
                continue
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
                img = QImage(str(p))
                if not img.isNull():
                    t = self.new_note("rich")
                    t.edit.insert_plain(p.name + "\n")
                    t.edit.insert_image(img)
                    n += 1
                continue
            try:
                text = p.read_text("utf-8")
            except UnicodeDecodeError:
                try:
                    text = p.read_text("cp949")
                except Exception:
                    continue
            kind = "text" if p.suffix.lower() in TEXT_EXT - {".txt"} else "rich"
            if p.suffix.lower() == ".txt":
                kind = "text"
            self.store.create(kind=kind, text=text, title=p.name, created=p.stat().st_mtime)
            n += 1
        self.refresh_list()
        self.status(f"파일 {n}개를 가져왔어요")

    def export_notes(self, ids):
        ids = [i for i in ids if i in self.store.notes]
        if not ids:
            return
        if QMessageBox.question(self, "내보내기", "내보낸 파일은 암호화되지 않은 일반 파일이라 다른 프로그램이 읽을 수 있어요.\n계속할까요?") \
                != QMessageBox.Yes:
            return
        d = QFileDialog.getExistingDirectory(self, "내보낼 폴더")
        if not d:
            return
        self._flush(ids)
        for nid in ids:
            n = self.store.notes[nid]
            safe = "".join(ch for ch in n.display_title() if ch not in '\\/:*?"<>|').strip()[:60] or nid
            base = Path(d) / f"{time.strftime('%Y%m%d-%H%M', time.localtime(n.created))} {safe}"
            if n.kind == "rich" and n.html:
                base.with_suffix(".html").write_text(n.html, "utf-8")
            base.with_suffix(".txt").write_text(n.text, "utf-8")
        self.status(f"{len(ids)}개를 내보냈어요: {d}")

    # ------------------------------------------------------------ 보관 폴더·암호
    def change_folder(self):
        cur = str(self.store.folder)
        d = QFileDialog.getExistingDirectory(self, "새 보관 폴더 (예: Dropbox 안)", cur)
        if not d or Path(d).resolve() == self.store.folder.resolve():
            return
        dest = Path(d)
        self.save_all()
        if crypto.vault_exists(dest):
            QMessageBox.information(self, "보관 폴더", "그 폴더에 이미 Hushpad 메모가 있어요. 다시 시작하면서 그 폴더의 암호를 물어볼게요.")
        else:
            r = QMessageBox.question(self, "보관 폴더 옮기기",
                                     f"지금 메모들을 새 폴더로 복사할까요?\n{cur}\n→ {dest}\n(원래 폴더는 그대로 남겨 둡니다)")
            if r != QMessageBox.Yes:
                return
            dest.mkdir(parents=True, exist_ok=True)
            for name in ("vault.json", "categories.own"):
                if (self.store.folder / name).exists():
                    shutil.copy2(self.store.folder / name, dest / name)
            for sub in ("notes", "history", "media"):
                if (self.store.folder / sub).exists():
                    shutil.copytree(self.store.folder / sub, dest / sub, dirs_exist_ok=True)
        self.cfg["data_dir"] = str(dest)
        self.save_state()
        QMessageBox.information(self, "보관 폴더", "Hushpad를 다시 시작합니다.")
        QApplication.instance().setProperty("restart", True)
        self.close()

    def change_passphrase(self):
        d = PassphraseDialog(self)
        if d.exec():
            crypto.change_passphrase(self.store.folder, self.store.key, d.pw1.text())
            self.status("암호를 바꿨어요. 다른 PC에서는 다음에 열 때 새 암호를 넣으세요.")

    def forget_here(self):
        crypto.forget_key(crypto.vault_id(self.store.folder))
        self.status("이 PC에서 암호를 잊었어요. 다음 실행 때 다시 물어봅니다.")

    # ------------------------------------------------------------ 다른 PC 동기화
    def scan_remote(self):
        changed, removed = self.store.scan()
        if not changed and not removed:
            return
        for nid in changed:
            i = self._tab_index(nid)
            if i < 0:
                continue
            t = self.tabs.widget(i)
            remote = self.store.notes[nid]
            if t.dirty:  # 양쪽에서 동시에 고침 — 내 쪽을 사본으로 살려 둠
                t.collect()
                copy = self.store.create(kind=t.note.kind, text=t.note.text, html=t.note.html,
                                         category=t.note.category,
                                         title=f"(충돌 사본) {t.note.display_title()}")
                self.status(f"다른 PC에서도 같은 메모를 고쳐서, 이 PC 내용을 '{copy.title}'로 따로 저장했어요", 10000)
            t.reload(remote)
            self._set_tab_look(i)
        for nid in removed:
            i = self._tab_index(nid)
            if i >= 0:
                t = self.tabs.widget(i)
                self.tabs.removeTab(i)
                t.deleteLater()
        self._update_empty()
        self.list_timer.start()
