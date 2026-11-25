"""Hushpad 주 창."""
from __future__ import annotations

import html as html_mod
import json
import os
import shutil
import time
from pathlib import Path

from PySide6.QtCore import QByteArray, QEvent, QMimeData, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QIcon, QImage, QKeySequence, QShortcut,
                           QTextCharFormat, QTextCursor, QTextDocument, QTextDocumentFragment)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QHBoxLayout,
                               QHeaderView, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMainWindow, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSplitter,
                               QSizePolicy, QStackedWidget, QSystemTrayIcon, QTabWidget, QToolBar, QToolButton, QTreeWidget, QTreeWidgetItem,
                               QVBoxLayout, QWidget)

from . import __version__, capture, crypto, i18n, icons, notepad_import, plat, theme, updater
from .widgets import CommandPalette, CountDelegate, EmptyState, NoteList, rel_time
from .common import (APP_NAME, DEFAULTS, LOCAL_DIR, cleanup_share_files, exclude_from_capture, fmt_full, fmt_stamp, fmt_time, resource,
                     set_clipboard, text_mime)
from .i18n import tr
from .dialogs import HistoryDialog, ImportDialog, PassphraseDialog, RemoteViewDialog, SetupDialog
from .editors import CodeEdit, RichEdit, body_font, mono_font
from .store import Note, Store

IDS_MIME = "application/x-hushpad-ids"
SAVE_DELAY_MS = 600
TEXT_EXT = {".txt", ".json", ".html", ".htm", ".md", ".csv", ".xml", ".yaml", ".yml", ".ini", ".log", ".py",
            ".js", ".ts", ".css", ".sql", ".env", ".cfg", ".toml", ".bat", ".ps1", ".sh"}
# 전역 단축키(Windows Ctrl+Alt / macOS ⌃⌥): S 스크린샷, R 녹화, N 새 메모, M 클립보드를 메모로 — plat 모듈
K = plat.key_label      # 앱 안 단축키 표기 (macOS는 ⌘ 기호)
G = plat.global_key     # 전역 단축키 표기


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
                self.edit.fit_images()
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
            self.win.status(tr("tab.save_failed", err=e))
            self.timer.start(3000)

    def recover(self):
        """비밀 메모는 다른 탭으로 갔다 오면 다시 가린다."""
        if self.note.secret:
            t = self.win.t
            self.cover.setIcon(icons.icon("eye", t["text2"]))
            self.cover.setText("  " + tr("tab.secret_cover"))
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
                and self.cfg.get("hide_from_capture", True) and not isinstance(obj, capture.RegionOverlay) \
                and not (self.win is not None and self.win.remote_view_on()) \
                and obj.objectName() != "RemoteViewDialog" \
                and (plat.CAPTURE_EXCLUDE_WORKS or not isinstance(obj, (capture.RecordBar, capture._Frame))):
            exclude_from_capture(obj, True)
        return False


# ====================================================================== 주 창
def autostart_allowed() -> bool:
    """자동 실행 등록을 건드려도 되는 실행인가.
    - 배포된 앱(exe/.app)에서만. python으로 돌리는 개발 실행은 아님
    - 자체 점검(--selftest)·시험용 프로필(HUSHPAD_PROFILE)·HUSHPAD_NO_AUTOSTART=1 이면 절대 안 건드림
    - macOS에서 서명 없는 앱을 다운로드 폴더에서 바로 열면 임시 경로(App Translocation)라 등록하지 않음
    - Microsoft Store(MSIX) 패키지 앱은 매니페스트의 시작 작업이 맡으므로 레지스트리를 건드리지 않음"""
    import sys
    if plat.IS_PACKAGED:
        return False
    if not plat.AUTOSTART_SUPPORTED or not getattr(sys, "frozen", False):
        return False
    if "--selftest" in sys.argv or os.environ.get("HUSHPAD_PROFILE") or os.environ.get("HUSHPAD_NO_AUTOSTART"):
        return False
    if sys.platform == "darwin" and "/AppTranslocation/" in sys.executable:
        return False
    return True


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
        self.native = plat.Integration(self, self._on_hotkey, self._on_session_lock)
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
        self._init_autostart()
        self._clean_temp_recordings()
        self._init_updates()
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
                self, APP_NAME, tr("win.broken", n=len(store.broken)) + "\n" + "\n".join(store.broken[:10])))
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
        self.shield.setToolTip(tr("side.shield_tip"))
        brand.addWidget(self.shield)
        lv.addLayout(brand)
        lv.addSpacing(4)
        self.search = QLineEdit(objectName="Search", placeholderText=tr("side.search"))
        self.search.setToolTip(tr("side.search_tip", k1=K("Ctrl+E"), k2=K("Ctrl+K")))
        self.search.setClearButtonEnabled(True)
        self.search_act = self.search.addAction(QIcon(), QLineEdit.LeadingPosition)
        self._themed.append((self.search_act, "search", "muted"))
        self.search.textChanged.connect(lambda: self.list_timer.start())
        self.search.returnPressed.connect(self._open_first_result)
        self.search.setMinimumHeight(32)
        lv.addWidget(self.search)
        hrow = QHBoxLayout()
        hrow.setContentsMargins(0, 0, 0, 0)
        hrow.addWidget(QLabel(tr("side.vault"), objectName="SectionLabel"))
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
        row.addWidget(QLabel(tr("side.notes"), objectName="SectionLabel"))
        row.addStretch(1)
        self.sort = QComboBox()
        self.sort.addItem(tr("sort.updated"), "updated")
        self.sort.addItem(tr("sort.created"), "created")
        self.sort.addItem(tr("sort.title"), "title")
        i = self.sort.findData(self.cfg.get("sort", "updated"))
        self.sort.setCurrentIndex(max(0, i))
        self.sort.currentIndexChanged.connect(self._sort_changed)
        self.add_cat_btn = QPushButton(objectName="Ghost")
        self.add_cat_btn.setToolTip(tr("dlg.new_cat"))
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
        newbtn.setToolTip(tr("tab.new_tip", key=K("Ctrl+N")))
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
        self.find_in = QLineEdit(placeholderText=tr("find.placeholder"))
        self.repl_in = QLineEdit(placeholderText=tr("find.replace_ph"))
        b_prev, b_next = QPushButton("▲"), QPushButton("▼")
        b_rep, b_all, b_close = QPushButton(tr("act.replace")), QPushButton(tr("find.replace_all")), QPushButton("✕")
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
        # 원격으로 볼 때 잠깐 보이는 중이면 남은 시간 (누르면 다시 숨김)
        self.rv_btn = QPushButton("", flat=True, cursor=Qt.PointingHandCursor)
        self.rv_btn.setStyleSheet("color:#e0a020; font-weight:600; padding:0 6px")
        self.rv_btn.clicked.connect(lambda: self.stop_remote_view())
        self.rv_btn.hide()
        self.statusBar().addPermanentWidget(self.rv_btn)
        self._rv_until = 0.0
        self.rv_timer = QTimer(self, interval=15000, timeout=self._rv_tick)

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

    def _menu(self, parent, key):
        """하위 메뉴 — 이름은 번역, 열쇠(key)는 아이콘·명령 팔레트에서 쓴다."""
        m = parent.addMenu(tr(f"menu.{key}"))
        m.menuAction().setData(key)
        return m

    def _build_actions(self):
        mb = self.more_menu = QMenu(self)
        self.menuBar().hide()
        m = self._menu(mb, "file")
        self.a_new = self._act(m, tr("act.new_rich"), lambda: self.new_note("rich"), "Ctrl+N")
        self.a_new_text = self._act(m, tr("act.new_code"), lambda: self.new_note("text"), "Ctrl+Shift+N")
        self._act(m, tr("act.close_tab"), lambda: self.close_tab(self.tabs.currentIndex()), "Ctrl+W")
        m.addSeparator()
        if plat.NOTEPAD_IMPORT_SUPPORTED:
            self._act(m, tr("act.import_notepad"), self.import_notepad)
        self._act(m, tr("act.import_files"), self._import_files_dialog)
        self._act(m, tr("act.export_sel"), lambda: self.export_notes(self.selected_ids() or self._cur_ids()))
        m.addSeparator()
        self._act(m, tr("act.open_folder"), lambda: plat.open_path(self.store.folder))
        self._act(m, tr("act.change_folder"), self.change_folder)
        self._act(m, tr("act.change_pw"), self.change_passphrase)
        m.addSeparator()
        self._act(m, tr("act.lock"), self.lock, "Ctrl+L")
        self._act(m, tr("act.quit"), self.quit_app, "Ctrl+Q")

        m = self._menu(mb, "edit")
        self._act(m, tr("act.copy_plain"), lambda: self.copy_selection(self._cur_editor(), plain=True),
                  "Ctrl+Shift+C")
        self._act(m, tr("act.paste_plain"), self.paste_plain, "Ctrl+Shift+V")
        self.a_plain_paste = self._act(m, tr("act.always_plain"), self._toggle_plain_paste, checkable=True,
                                       checked=self.cfg["plain_paste"])
        m.addSeparator()
        self._act(m, tr("act.copy_all_rich"), lambda: self.copy_all(plain=False), "Ctrl+Alt+C")
        self._act(m, tr("act.copy_all_plain"), lambda: self.copy_all(plain=True), "Ctrl+Alt+Shift+C")
        m.addSeparator()
        self._act(m, tr("act.clear_fmt"), self.clear_format, "Ctrl+Space")
        self._act(m, tr("act.bold"), self.toggle_bold, "Ctrl+B")
        m.addSeparator()
        self._act(m, tr("act.find"), self.show_find, "Ctrl+F")
        self._act(m, tr("act.replace"), lambda: self.show_find(replace=True), "Ctrl+H")
        self._act(m, tr("act.find_next"), lambda: self.find_next(False), "F3")
        self._act(m, tr("act.find_list"), lambda: (self.search.setFocus(), self.search.selectAll()), "Ctrl+E")
        m.addSeparator()
        self._act(m, tr("act.json_pretty"), self.json_pretty, "Ctrl+Alt+J")
        self._act(m, tr("act.json_compact"), self.json_compact)

        m = self._menu(mb, "note")
        self._act(m, tr("act.rename"), lambda: self.rename_note(self._cur_id()), "F2")
        self._act(m, tr("act.set_cat"), lambda: self.pick_category(self.selected_ids() or self._cur_ids()), "Ctrl+M")
        self._act(m, tr("act.pin"), lambda: self.toggle_pin(self.selected_ids() or self._cur_ids()), "Ctrl+P")
        self._act(m, tr("act.secret"), lambda: self.toggle_secret(self.selected_ids() or self._cur_ids()))
        self._act(m, tr("act.convert"), self.convert_kind)
        self._act(m, tr("act.history"), lambda: self.show_history(self._cur_id()), "Ctrl+Shift+H")
        m.addSeparator()
        self._act(m, tr("act.merge"), lambda: self.merge(self.selected_ids()), "Ctrl+Shift+M")
        self._act(m, tr("act.trash"), lambda: self.trash_ids(self.selected_ids() if self.tree.hasFocus()
                                                             else self._cur_ids()), "Ctrl+Del")

        m = self._menu(mb, "capture")
        anywhere = plat.HOTKEYS_SUPPORTED
        self._act(m, tr("act.shot_region"), lambda: self.screenshot("region"), "Ctrl+Shift+S",
                  tip=tr("act.shot_tip", gkey=G("S")) if anywhere else "")
        self._act(m, tr("act.shot_full"), lambda: self.screenshot("full"))
        self._act(m, tr("act.record"), self.record_video, "Ctrl+Shift+R",
                  tip=tr("act.record_tip", gkey=G("R")) if anywhere else "")
        m.addSeparator()
        self._act(m, tr("act.hide_capture"), self._toggle_hide_capture,
                  checkable=True, checked=self.cfg.get("hide_from_capture", True))
        self._act(m, tr("act.remote_view"), self.start_remote_view)

        m = self._menu(mb, "view")
        self.a_plainview = self._act(m, tr("act.plain_view"), self._toggle_plain_view, "Ctrl+T",
                                     checkable=True)
        self._act(m, tr("act.wrap"), self._toggle_wrap, "Alt+Z", checkable=True, checked=self.cfg["wrap"])
        self._act(m, tr("act.zoom_in"), lambda: self._zoom(1), "Ctrl+=")
        self._act(m, tr("act.zoom_out"), lambda: self._zoom(-1), "Ctrl+-")
        self._act(m, tr("act.zoom_reset"), lambda: self._zoom(0), "Ctrl+0")
        self._act(m, tr("act.toggle_list"), self._toggle_list, "Ctrl+\\")
        self._act(m, tr("act.topmost"), self._toggle_topmost, "Ctrl+Alt+T", checkable=True)
        m.addSeparator()
        tm = self._menu(m, "theme")
        grp = QActionGroup(self)
        for key in ("auto", "light", "dark"):
            a = tm.addAction(tr(f"theme.{key}"))
            a.setCheckable(True)
            a.setChecked(self.cfg.get("theme", "auto") == key)
            a.triggered.connect(lambda _=False, k=key: self.set_theme(k))
            grp.addAction(a)
        lm = self._menu(m, "language")
        lgrp = QActionGroup(self)
        cur_lang = self.cfg.get("language", "system")
        for code in ("system",) + i18n.SUPPORTED:
            label = tr("lang.system") if code == "system" else i18n.NATIVE_NAMES[code]
            a = lm.addAction(label)
            a.setCheckable(True)
            a.setChecked(cur_lang == code or (code == "system" and cur_lang not in i18n.SUPPORTED))
            a.triggered.connect(lambda _=False, c=code: self.set_language(c))
            lgrp.addAction(a)
        self.a_palette = self._act(m, tr("act.palette"), self.open_palette, "Ctrl+K")
        m.addSeparator()
        self._act(m, tr("act.next_tab"), lambda: self._cycle(1), "Ctrl+Tab")
        self._act(m, tr("act.prev_tab"), lambda: self._cycle(-1), "Ctrl+Shift+Tab")

        m = self._menu(mb, "security")
        if plat.CLIPBOARD_PRIVATE_SUPPORTED:
            self._act(m, tr("act.clip_private"), self._toggle_clip_private,
                      checkable=True, checked=self.cfg["clip_private"])
        lm = self._menu(m, "idle_lock")
        lgrp = QActionGroup(self)
        for mins in (0, 5, 10, 30):
            a = lm.addAction(tr("idle.off") if mins == 0 else tr("idle.min", n=mins))
            a.setCheckable(True)
            a.setChecked(self.cfg.get("lock_idle_min", 0) == mins)
            a.triggered.connect(lambda _=False, v=mins: self.cfg.__setitem__("lock_idle_min", v))
            lgrp.addAction(a)
        if plat.SESSION_LOCK_SUPPORTED:
            self._act(m, tr("act.lock_winlock"), lambda on: self.cfg.__setitem__("lock_on_winlock", on),
                      checkable=True, checked=self.cfg.get("lock_on_winlock", False))
        self._act(m, tr("act.close_tray"), lambda on: self.cfg.__setitem__("close_to_tray", on),
                  checkable=True, checked=self.cfg.get("close_to_tray", True))
        if plat.IS_PACKAGED:      # Store 앱: 시작 작업은 Windows 설정에서 켜고 끈다
            self._act(m, tr("act.startup_settings"), self._open_startup_settings)
        elif plat.AUTOSTART_SUPPORTED:
            self.a_autostart = self._act(m, tr("act.autostart"), self._toggle_autostart, checkable=True,
                                         checked=self._autostart_on())
        if updater.supported():
            self._act(m, tr("act.auto_update"), self._toggle_update_check, checkable=True,
                      checked=self.cfg.get("update_check", True))
        m.addSeparator()
        self.a_clear = self._act(m, tr("act.secret_clear"), self._toggle_secret_clear,
                                 checkable=True, checked=self.cfg["secret_clear_sec"] > 0)
        m.addSeparator()
        self._act(m, tr("act.forget"), self.forget_here)
        mb.addSeparator()
        if updater.supported():
            self.a_update = self._act(mb, tr("act.check_update"), self.check_update)
        self._act(mb, tr("act.about"), self.show_about)

        tb = QToolBar(tr("tb.name"), objectName="TopBar")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setIconSize(QSize(18, 18))
        tb.setContextMenuPolicy(Qt.PreventContextMenu)
        self.addToolBar(tb)
        new_btn = QToolButton(objectName="Primary")
        new_btn.setText(tr("tb.new"))
        new_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        new_btn.setToolTip(tr("tb.new_tip", k1=K("Ctrl+N"), k2=K("Ctrl+Shift+N")))
        new_btn.setPopupMode(QToolButton.MenuButtonPopup)
        nm = QMenu(new_btn)
        nm.addAction(self.a_new)
        nm.addAction(self.a_new_text)
        new_btn.setMenu(nm)
        new_btn.clicked.connect(lambda: self.new_note("rich"))
        self._themed.append((new_btn, "plus", "accent_text"))
        tb.addWidget(new_btn)
        self._themed += [(self.a_new, "note", "text2"), (self.a_new_text, "code", "text2")]
        tb.addSeparator()

        def tbtn(icon, label, keys, slot, color="text2", gkey=None):
            tip = f"{label}  {K(keys)}"
            if gkey and plat.HOTKEYS_SUPPORTED:
                tip += " · " + tr("tb.anywhere", gkey=G(gkey))
            a = QAction(label, self)
            a.setToolTip(tip)
            a.triggered.connect(lambda _=False: slot())
            tb.addAction(a)
            self._themed.append((a, icon, color))
            return a
        tbtn("copy", tr("tb.copy_plain"), "Ctrl+Shift+C", lambda: self.copy_selection(self._cur_editor(), plain=True))
        tbtn("paste", tr("tb.paste_plain"), "Ctrl+Shift+V", self.paste_plain)
        self.a_tb_plain = QAction(tr("act.always_plain"), self)
        self.a_tb_plain.setCheckable(True)
        self.a_tb_plain.setChecked(self.cfg["plain_paste"])
        self.a_tb_plain.toggled.connect(lambda on: self.a_plain_paste.setChecked(on))
        tb.addAction(self.a_tb_plain)
        self._themed.append((self.a_tb_plain, "text", "text2"))
        tb.addSeparator()
        tbtn("camera", tr("tb.shot"), "Ctrl+Shift+S", lambda: self.screenshot("region"), gkey="S")
        self.a_tb_rec = tbtn("video", tr("tb.record"), "Ctrl+Shift+R", self.record_video, gkey="R")
        tb.addSeparator()
        tbtn("history", tr("tb.history"), "Ctrl+Shift+H", lambda: self.show_history(self._cur_id()))
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(spacer)
        self.palette_btn = QPushButton("  " + tr("tb.palette"), objectName="CommandBtn")
        self.palette_btn.setCursor(Qt.PointingHandCursor)
        self.palette_btn.setToolTip(tr("tb.palette_tip", key=K("Ctrl+K")))
        kl = QHBoxLayout(self.palette_btn)
        kl.setContentsMargins(0, 0, 8, 0)
        kl.addStretch(1)
        kl.addWidget(QLabel(K("Ctrl+K"), objectName="Kbd"))
        self.palette_btn.clicked.connect(self.open_palette)
        self._themed.append((self.palette_btn, "search", "muted"))
        tb.addWidget(self.palette_btn)
        tb.addWidget(QLabel(" "))
        more = QToolButton()
        more.setToolTip(tr("tb.more_tip"))
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
                msg = tr("tray.still_running", k1=G("N"), k2=G("M")) if plat.HOTKEYS_SUPPORTED \
                    else tr("tray.still_running_nokeys")
                self.tray.showMessage(APP_NAME, msg, QSystemTrayIcon.Information, 5000)
            return
        if self._recorder is not None:
            self._recorder.stop()
        self._unregister_hotkeys()
        if self.tray is not None:
            self.tray.hide()
        cleanup_share_files()  # 붙여 넣기용 임시 그림 파일
        super().closeEvent(e)
        QApplication.instance().quit()

    def quit_app(self):
        self._quitting = True
        self.close()

    def showEvent(self, e):
        super().showEvent(e)
        theme.style_titlebar(self, self.t)
        if self.cfg.get("hide_from_capture", True) and not self.remote_view_on():
            exclude_from_capture(self, True)
        if not self.native.active:
            self._register_hotkeys()

    # ------------------------------------------------------------ 전역 단축키 (plat.Integration)
    def _register_hotkeys(self):
        failed = self.native.start()
        if failed:
            self.status(tr("hk.failed", keys=", ".join(K(f) for f in failed)))

    def _unregister_hotkeys(self):
        self.native.stop()

    def _on_hotkey(self, name):
        fn = {"shot": lambda: self.screenshot("region"), "record": self.record_video,
              "quick": self.quick_note, "clip": self.clip_to_note}.get(name)
        if fn:
            QTimer.singleShot(0, fn)

    def _on_session_lock(self):
        if self.cfg.get("lock_on_winlock"):
            QTimer.singleShot(0, self.lock)

    def nativeEvent(self, etype, message):
        if self.native.native_event(etype, message):
            return True, 0
        return super().nativeEvent(etype, message)

    # ------------------------------------------------------------ 빠른 메모·트레이·잠금
    def _setup_tray(self):
        self.tray = None
        self.tray_autostart = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self.windowIcon(), self)
        self.tray.setToolTip(tr("tray.tip"))
        m = QMenu()

        def lbl(key, letter):
            return tr(key) + (f"   {G(letter)}" if plat.HOTKEYS_SUPPORTED else "")
        m.addAction(tr("common.open"), self.bring_to_front)
        # 원격에서 Hushpad 창은 검게 보여도 트레이 메뉴는 보이므로 여기서 켠다
        self.tray_rv = m.addAction(tr("act.remote_view"), self._tray_remote_view)
        m.addAction(lbl("tb.new", "N"), self.quick_note)
        m.addAction(lbl("tray.clip", "M"), self.clip_to_note)
        m.addSeparator()
        m.addAction(lbl("empty.k_shot", "S"), lambda: self.screenshot("region"))
        m.addAction(lbl("tb.record", "R"), self.record_video)
        m.addSeparator()
        if plat.IS_PACKAGED:
            m.addAction(tr("act.startup_settings"), self._open_startup_settings)
        elif plat.AUTOSTART_SUPPORTED:
            self.tray_autostart = m.addAction(tr("act.autostart"))
            self.tray_autostart.setCheckable(True)
            self.tray_autostart.setChecked(self._autostart_on())
            self.tray_autostart.toggled.connect(self._toggle_autostart)
        if updater.supported():
            self.tray_update = m.addAction(tr("act.check_update"), self.check_update)
        m.addAction(tr("act.about"), self.show_about)
        m.addSeparator()
        m.addAction(tr("act.lock"), self.lock)
        m.addAction(tr("act.quit"), self.quit_app)
        m.aboutToShow.connect(self._sync_autostart_checks)
        m.aboutToShow.connect(lambda: self.tray_rv.setText(
            tr("rv.hide_now") if self.remote_view_on() else tr("act.remote_view")))
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
            title = html_mod.escape(tr("clip.title", time=fmt_stamp(key="fmt.clip")))
            html = f'<p>{title}</p><p><img src="{image_to_data_url(img)}" width="{min(img.width(), 900)}"></p>'
            n = self.store.create(kind="rich", html=html, text=tr("clip.title", time=fmt_stamp(key="fmt.clip")))
            what = tr("clip.image", w=img.width(), h=img.height())
        elif text.strip():
            looks_code = text.lstrip()[:1] in "{[<" or "=" in text.split("\n", 1)[0] or "\t" in text
            if md.hasHtml() and not looks_code:
                n = self.store.create(kind="rich", html=md.html(), text=text)
            else:
                n = self.store.create(kind="text", text=text)
            what = tr("note.chars", n=len(text))
        else:
            self._notify(tr("clip.empty"))
            return
        self.list_timer.start()
        self._notify(tr("clip.saved", what=what))

    # ------------------------------------------------------------ 자동 업데이트 (zip판, update_ui.py)
    def _init_updates(self):
        self.updates = None
        if not updater.supported():
            return
        from .update_ui import UpdateController
        self.updates = UpdateController(self)
        last = self.cfg.get("last_version", "")
        if last and last != __version__:
            QTimer.singleShot(2500, lambda: self._notify(tr("upd.done", ver=__version__)))
        if last != __version__:
            self.cfg["last_version"] = __version__
            self.cfg.save()

    def check_update(self):
        if self.updates is None:
            return
        if self.updates.pending is not None:
            self.updates.ask()
        else:
            self.updates.check(manual=True)

    def update_found(self, ver: str):
        """새 버전을 찾았을 때 메뉴 글자를 '업데이트 설치 (1.0.3)'로."""
        label = tr("act.install_update", ver=ver)
        for a in (getattr(self, "a_update", None), getattr(self, "tray_update", None)):
            if a is not None:
                a.setText(label)

    def _toggle_update_check(self, on):
        self.cfg["update_check"] = on
        self.cfg.save()
        self.status(tr("upd.auto_on") if on else tr("upd.auto_off"))

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
        lay.addWidget(QLabel(tr("lock.title"), objectName="EmptyTitle", alignment=Qt.AlignCenter))
        lay.addWidget(QLabel(tr("lock.hint"), objectName="EmptyHint", alignment=Qt.AlignCenter))
        row = QHBoxLayout()
        row.addStretch(1)
        self.lock_pw = QLineEdit(echoMode=QLineEdit.Password, placeholderText=tr("setup.pw"))
        self.lock_pw.setFixedWidth(260)
        self.lock_pw.returnPressed.connect(self.unlock)
        ok = QPushButton(tr("lock.open"), objectName="Primary")
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
        self.stop_remote_view(quiet=True)
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
            self.lock_msg.setText(tr("lock.wrong"))
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
        plat.set_topmost(self, on)
        self.status(tr("topmost.on") if on else tr("topmost.off"))

    def _autostart_on(self) -> bool:
        try:
            return plat.autostart_enabled()
        except Exception:
            return False

    def _toggle_autostart(self, on):
        try:
            done = plat.set_autostart(on)
        except OSError as e:
            self.status(str(e))
            done = False
        if not done:
            if on:
                self.status(tr("autostart.need_app"))
            self._sync_autostart_checks()
            return
        self.cfg["autostart"] = on
        self._sync_autostart_checks()
        self._notify(tr("autostart.on") if on else tr("autostart.off"))

    def _open_startup_settings(self):
        if not plat.open_startup_settings():
            self.status(tr("startup_settings.fail"))

    def _sync_autostart_checks(self):
        """보안 메뉴와 트레이 메뉴의 체크를 실제 등록 상태에 맞춘다."""
        on = self._autostart_on()
        for a in (getattr(self, "a_autostart", None), getattr(self, "tray_autostart", None)):
            if a is not None and a.isChecked() != on:
                a.blockSignals(True)
                a.setChecked(on)
                a.blockSignals(False)

    def _init_autostart(self):
        """첫 실행 때 '시작할 때 실행'을 켜고, 그 뒤로는 켜져 있으면 프로그램 위치를 새로 적는다
        (폴더를 옮겨도 자동 실행이 끊기지 않게). 개발용(python) 실행에서는 건드리지 않는다."""
        if not autostart_allowed():
            return
        try:
            if not self.cfg.get("autostart_initialized"):
                self.cfg["autostart_initialized"] = True
                self.cfg["autostart"] = bool(plat.set_autostart(True))
                self.cfg.save()
                if self.cfg["autostart"]:
                    QTimer.singleShot(1500, lambda: self._notify(tr("autostart.first")))
            elif self._autostart_on():
                plat.set_autostart(True)
        except Exception:
            pass
        self._sync_autostart_checks()

    @staticmethod
    def _clean_temp_recordings():
        """녹화가 비정상 종료돼 남은 임시 MP4(암호화 전)를 지운다."""
        import sys
        if "--selftest" in sys.argv or os.environ.get("HUSHPAD_NO_AUTOSTART"):
            return   # 점검 중에는 다른 실행의 녹화 파일을 건드리지 않음
        from .common import LOCAL_DIR
        for f in (LOCAL_DIR / "tmp").glob("rec-*.mp4"):
            try:
                f.unlink()
            except OSError:
                pass

    def show_about(self):
        from .dialogs import AboutDialog
        AboutDialog(self, self.windowIcon()).exec()

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
            base = tr("note.secret")
        else:
            fl = note.first_line()
            base = (fl[:22] + ("…" if len(fl) > 22 else "")) if fl else (tr("note.image") if note.has_images()
                                                                       else tr("tb.new"))
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
        self.tabs.setTabToolTip(i, tr("tab.tip", title=n.display_title(), cat=n.category or tr("cat.none_short"),
                                      created=fmt_full(n.created), updated=fmt_full(n.updated))
                                + ("\n" + tr("tab.tip_preview") if t.preview else ""))

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
            self.status(tr("st.in_trash"))
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
    MENU_ICONS = {"file": "note", "edit": "copy", "note": "note", "capture": "camera", "view": "eye",
                  "security": "shield", "theme": "settings", "idle_lock": "lock", "language": "settings"}
    PREFIXED = ("theme", "idle_lock", "language")   # 팔레트에서 '테마: 밝게'처럼 앞에 메뉴 이름을 붙임

    def palette_actions(self):
        """(동작, '메뉴: 이름', 아이콘) — 하위 메뉴 이름뿐인 항목·구분선은 뺀다."""
        out, seen = [], set()

        def walk(menu, path):
            for a in menu.actions():
                if a.isSeparator() or not a.isVisible():
                    continue
                if a.menu() is not None:
                    walk(a.menu(), path + [(a.data() or "", a.text().replace("&", ""))])
                    continue
                txt = a.text().replace("&", "").split("\t")[0].strip()
                if not txt or a is self.a_palette:
                    continue
                label = f"{path[-1][1]}: {txt}" if path and path[-1][0] in self.PREFIXED else txt
                if label in seen:
                    continue
                seen.add(label)
                group = path[-1][0] if path else ""
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
        m.addAction(tr("act.rename"), lambda: self.rename_note(nid))
        m.addAction(tr("act.set_cat"), lambda: self.pick_category([nid]))
        m.addAction(tr("act.history"), lambda: self.show_history(nid))
        m.addSeparator()
        m.addAction(tr("tabm.close"), lambda: self.close_tab(self._tab_index(nid)))
        m.addAction(tr("tabm.close_others"), lambda: self._close_others(nid))
        m.addAction(tr("tabm.close_right"), lambda: self._close_right(nid))
        m.addSeparator()
        m.addAction(tr("act.trash"), lambda: self.trash_ids([nid]))
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
        self.status_lbl.setText(tr("status.saving"))

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
        kind = tr("kind.text") if t.note.kind == "text" else tr("kind.rich")
        state = tr("status.saving") if t.dirty else tr("status.saved", time=time.strftime(
            '%H:%M:%S', time.localtime(t.note.updated)))
        self.status_lbl.setText(tr("status.line", kind=kind, line=line, col=col,
                                   chars=tr("note.chars", n=chars), state=state))

    # ------------------------------------------------------------ 목록
    def refresh_categories(self):
        cur = self._filter
        self.cats.blockSignals(True)
        self.cats.clear()
        live = [n for n in self.store.notes.values() if n.deleted is None]
        trash = sum(1 for n in self.store.notes.values() if n.deleted is not None)
        entries = [("inbox", tr("cat.all"), ("all",), len(live)),
                   ("pin", tr("cat.pinned"), ("pinned",), sum(1 for n in live if n.pinned)),
                   ("calendar", tr("cat.today"), ("today",), sum(1 for n in live if self._is_today(n))),
                   ("archive", tr("cat.stale"), ("stale",), sum(1 for n in live if self._is_stale(n))),
                   ("folder", tr("cat.none"), ("none",), sum(1 for n in live if not n.category))]
        for c in self.store.all_categories():
            entries.append(("tag", c, ("cat", c), sum(1 for n in live if n.category == c)))
        entries.append(("trash", tr("cat.trash"), ("trash",), trash))
        sel = None
        t = self.t
        for ic, text, key, cnt in entries:
            it = QListWidgetItem(icons.icon(ic, t["text2"], t["accent_subtle_text"], 16), f"{text}")
            it.setData(Qt.UserRole, key)
            it.setData(Qt.UserRole + 2, cnt)
            it.setText(text)
            it.setToolTip(text)
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
                snippet = tr("list.secret") if n.secret else (tr("list.image") if n.has_images() else "")
            it = QListWidgetItem()
            it.setData(Qt.UserRole, n.id)
            it.setData(Qt.UserRole + 1, {
                "title": n.display_title(), "snippet": snippet, "category": n.category,
                "time": rel_time(n.created if key == "created" else n.updated),
                "pinned": n.pinned, "secret": n.secret, "kind": n.kind, "open": n.id in open_ids})
            it.setToolTip(tr("list.tip", title=n.display_title(), created=fmt_full(n.created),
                             updated=fmt_full(n.updated)))
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
            m.addAction(tr("lm.restore", n=len(ids)), lambda: self.restore_ids(ids))
            m.addAction(tr("lm.purge", n=len(ids)), lambda: self.purge_ids(ids))
            m.addSeparator()
            m.addAction(tr("lm.empty_trash"), self.empty_trash)
        else:
            m.addAction(tr("common.open"), lambda: [self.open_note(i) for i in ids])
            if len(ids) == 1:
                m.addAction(tr("act.rename"), lambda: self.rename_note(ids[0]))
            cm = m.addMenu(tr("lm.set_cat"))
            for c in self.store.all_categories():
                cm.addAction(c, lambda c=c: self.set_category(ids, c))
            cm.addSeparator()
            cm.addAction(tr("lm.new_cat"), lambda: self.pick_category(ids, new=True))
            cm.addAction(tr("cat.none"), lambda: self.set_category(ids, ""))
            m.addAction(tr("act.pin"), lambda: self.toggle_pin(ids))
            m.addAction(tr("act.secret"), lambda: self.toggle_secret(ids))
            if len(ids) >= 2:
                m.addSeparator()
                m.addAction(tr("lm.merge", n=len(ids)), lambda: self.merge(ids))
            m.addSeparator()
            m.addAction(tr("tb.copy_plain"), lambda: self._copy_notes(ids, True))
            m.addAction(tr("lm.export"), lambda: self.export_notes(ids))
            if len(ids) == 1:
                m.addAction(tr("act.history"), lambda: self.show_history(ids[0]))
            m.addSeparator()
            m.addAction(tr("lm.trash", n=len(ids)), lambda: self.trash_ids(ids))
        m.exec(self.tree.viewport().mapToGlobal(pos))

    def _cat_menu(self, pos):
        it = self.cats.itemAt(pos)
        if not it:
            return
        key = it.data(Qt.UserRole)
        m = QMenu(self)
        if key[0] == "cat":
            m.addAction(tr("cm.rename"), lambda: self.rename_category(key[1]))
            m.addAction(tr("cm.delete"), lambda: self.delete_category(key[1]))
        elif key[0] == "trash":
            m.addAction(tr("lm.empty_trash"), self.empty_trash)
        m.addAction(tr("lm.new_cat"), self.new_category)
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
        name, ok = QInputDialog.getText(self, tr("dlg.rename_title"), tr("dlg.rename_label"), text=n.title)
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
        self.status(tr("st.set_cat", n=len(ids), cat=cat or tr("cat.none")))

    def pick_category(self, ids, new=False):
        if not ids:
            return
        cats = self.store.all_categories()
        if new or not cats:
            name, ok = QInputDialog.getText(self, tr("dlg.new_cat"), tr("dlg.cat_name"))
        else:
            name, ok = QInputDialog.getItem(self, tr("lm.set_cat"), tr("dlg.pick_cat_label"), cats, 0, True)
        if ok:
            self.set_category(ids, name.strip())

    def new_category(self):
        name, ok = QInputDialog.getText(self, tr("dlg.new_cat"), tr("dlg.cat_name"))
        if ok and name.strip():
            self.store.add_category(name.strip())
            self.refresh_categories()

    def rename_category(self, old):
        name, ok = QInputDialog.getText(self, tr("dlg.rename_cat"), tr("dlg.new_name"), text=old)
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
        self.status(tr("st.secret_on") if on else tr("st.secret_off"))

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
        self.status(tr("st.trashed", n=len(ids)))

    def restore_ids(self, ids):
        self.store.restore(ids)
        self.refresh_list()

    def purge_ids(self, ids):
        if QMessageBox.question(self, tr("dlg.purge_title"), tr("dlg.purge_q", n=len(ids))) \
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
            self.status(tr("st.merge_need"))
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
        merged.title = tr("merge.title", n=len(notes), time=fmt_stamp())
        self.store.save(merged, snapshot=False)
        r = QMessageBox.question(self, tr("dlg.merge_title"), tr("dlg.merge_q", n=len(notes)))
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
            if QMessageBox.question(self, tr("dlg.to_text_title"), tr("dlg.to_text_q")) \
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
            self.status(tr("st.restored"))

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
            self.status(tr("st.secret_clip", n=self.cfg["secret_clear_sec"]))

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
                self.status(tr("st.copied_plain"))
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
        self.status(tr("st.copied_all_plain") if plain else tr("st.copied_all_rich"))

    def _copy_notes(self, ids, plain=True):
        self._flush(ids)
        notes = [self.store.notes[i] for i in ids if i in self.store.notes]
        txt = "\n\n".join(n.text for n in notes)
        self._clip(text_mime(txt), notes[0] if len(notes) == 1 else None)
        self.status(tr("st.copied_notes", n=len(notes)))

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
        self.a_tb_plain.setToolTip(tr("tip.paste_on") if on else tr("tip.paste_off"))

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
            self.status(tr("st.json_err", line=e.lineno, col=e.colno, msg=e.msg), 10000)
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
        self.status(tr("st.json_compact" if compact else "st.json_pretty", undo=K("Ctrl+Z")))

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
                self.status(tr("st.not_found"))

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
        self.status(tr("st.replaced", n=n))

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

    def zoom(self, d):
        """편집기의 Ctrl+휠·터치패드 확대/축소."""
        self._zoom(d)

    def _zoom(self, d):
        """글자 크기 d만큼 (0이면 기본 크기로)."""
        base = DEFAULTS["font_pt"] if d == 0 else self.cfg["font_pt"] + d
        new = max(7, min(32, base))
        if new == self.cfg["font_pt"] and d:
            return
        self.cfg["font_pt"] = new
        for i in range(self.tabs.count()):
            ed = self.tabs.widget(i).edit
            if isinstance(ed, RichEdit):
                ed.document().setDefaultFont(body_font(self.cfg["font_pt"]))
            else:
                ed.setFont(mono_font(self.cfg["font_pt"]))
            self.tabs.widget(i).plain_view.setFont(mono_font(self.cfg["font_pt"]))
        self.status(tr("st.font_size", n=self.cfg["font_pt"]))

    def _toggle_list(self):
        w = self.split.widget(0)
        w.setVisible(not w.isVisible())

    def _toggle_hide_capture(self, on):
        self.cfg["hide_from_capture"] = on
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                exclude_from_capture(w, on)
        self.status(tr("st.capture_hidden") if on else tr("st.capture_visible"))

    # ------------------------------------------------------------ 원격으로 볼 때 잠깐 보이기
    # 원격 접속·화면 공유에서는 Hushpad 창이 검게 보인다. 암호를 확인하고 정한 시간 동안만 캡처 숨김을 푼다.
    # 설정(hide_from_capture)은 바꾸지 않는다. 시간이 지나거나 잠그거나 끝내면 다시 숨긴다.
    def remote_view_on(self) -> bool:
        return getattr(self, "_rv_until", 0.0) > time.time()

    def _tray_remote_view(self):
        if self.remote_view_on():
            self.stop_remote_view()
        else:
            self.start_remote_view()

    def _verify_pw(self, pw: str) -> bool:
        try:
            return crypto.unlock_vault(self.store.folder, pw) == self.store.key
        except Exception:
            return False

    def start_remote_view(self):
        if not self.cfg.get("hide_from_capture", True):
            self.status(tr("rv.already"))
            if self.tray is not None:
                self.tray.showMessage(APP_NAME, tr("rv.already"), QSystemTrayIcon.Information, 4000)
            return
        dlg = RemoteViewDialog(self if self.isVisible() else None, self._verify_pw)
        if dlg.exec() != QDialog.Accepted:
            return
        self._rv_until = time.time() + dlg.minutes() * 60
        if self.locked:                      # 잠겨 있었으면 같은 암호로 함께 푼다
            self.lock_pw.setText(dlg.passphrase())
            self.unlock()
        for w in QApplication.topLevelWidgets():
            if w.isVisible():
                exclude_from_capture(w, False)
        self.rv_timer.start()
        self._rv_tick()
        self.bring_to_front()

    def stop_remote_view(self, quiet: bool = False):
        was = self._rv_until > 0
        self._rv_until = 0.0
        self.rv_timer.stop()
        self.rv_btn.hide()
        if not was:
            return
        if self.cfg.get("hide_from_capture", True):
            for w in QApplication.topLevelWidgets():
                if w.isVisible() and not isinstance(w, capture.RegionOverlay):
                    exclude_from_capture(w, True)
        if not quiet:
            self.status(tr("rv.off"))

    def _rv_tick(self):
        left = self._rv_until - time.time()
        if left <= 0:
            self.stop_remote_view()
            return
        self.rv_btn.setText(tr("rv.on", n=max(1, -int(-left // 60))))
        self.rv_btn.show()

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
        t.edit.insert_plain(tr("cap.note_title", time=fmt_stamp()) + "\n")
        return t

    def screenshot(self, mode="region"):
        if self._recorder is not None:
            return
        if not capture.screen_capture_ok():
            self._capture_denied()
            return
        screen = capture.screen_under_cursor()
        hidden = self._hide_for_capture()

        def go():
            pix = capture.grab_screen(screen)
            self._restore_after_capture(hidden)
            if self._blank_capture(pix):
                return
            if mode == "full":
                self._insert_shot(pix.toImage())
                return
            ov = capture.RegionOverlay(screen, pix, "image")
            ov.chosen.connect(lambda r: self._insert_shot(capture.crop(pix, r)))
            ov.start()
            self._overlay = ov
        QTimer.singleShot(250 if hidden else 60, go)

    # 오래된 Windows 10(빌드 19041 미만)은 '캡처 제외' 창이 검게 찍히고, macOS 15 이상은 창이 찍힐 수 있다.
    # 그런 곳(plat.CAPTURE_EXCLUDE_WORKS가 False)에서는 Hushpad 자체 캡처·녹화 때만 열린 Hushpad 창을
    # 잠깐 숨겼다가(찍는 동안·녹화하는 동안) 다시 보인다.
    def _hide_for_capture(self) -> list:
        if (plat.CAPTURE_EXCLUDE_WORKS and not self.remote_view_on()) or not self.cfg.get("hide_from_capture", True):
            return []
        hidden = [w for w in QApplication.topLevelWidgets()
                  if w.isVisible() and not isinstance(w, (capture.RegionOverlay, capture.RecordBar, capture._Frame))]
        for w in hidden:
            w.hide()
        return hidden

    def _restore_after_capture(self, hidden: list) -> None:
        for w in hidden:
            try:
                w.show()
            except RuntimeError:        # 그 사이 닫힌 창
                pass
        if self in hidden:
            self.bring_to_front()

    def _capture_denied(self):
        """macOS: 화면 기록 권한이 없을 때 어디서 켜는지 알려 준다."""
        self.bring_to_front()
        QMessageBox.information(self, tr("perm.title"), tr("perm.msg"))

    def _blank_capture(self, pix) -> bool:
        """찍은 화면이 비었으면(권한 없음 등) 알리고 True."""
        if pix.isNull() or (plat.IS_MAC and capture.looks_blank(pix)):
            self._capture_denied()
            return True
        return False

    def _insert_shot(self, img: QImage):
        t = self._capture_target()
        t.edit.insert_image(img)
        self.copy_image(img)
        self.bring_to_front()
        self.status(tr("st.shot", w=img.width(), h=img.height()))

    def record_video(self):
        if self._recorder is not None:
            self._recorder.stop()
            return
        if not capture.screen_capture_ok():
            self._capture_denied()
            return
        screen = capture.screen_under_cursor()
        self._rec_hidden = self._hide_for_capture()     # 녹화가 끝날 때까지 숨겨 둠 (오래된 Windows 10·macOS 15 이상)

        def go():
            pix = capture.grab_screen(screen)
            if self._blank_capture(pix):
                self._rec_restore()
                return
            ov = capture.RegionOverlay(screen, pix, "video")
            ov.chosen.connect(lambda r: self._start_record(screen, r))
            ov.cancelled.connect(self._rec_restore)
            ov.start()
            self._overlay = ov
        if self._rec_hidden:
            QTimer.singleShot(250, go)
        else:
            go()

    def _rec_restore(self):
        hidden, self._rec_hidden = getattr(self, "_rec_hidden", []), []
        self._restore_after_capture(hidden)

    def _start_record(self, screen, rect):
        try:
            rec = capture.Recorder(screen, rect, fps=self.cfg.get("video_fps", 12),
                                   max_sec=self.cfg.get("video_max_sec", 180))
        except Exception as e:
            self._rec_restore()
            QMessageBox.warning(self, tr("dlg.rec_title"), tr("dlg.rec_cant", err=e))
            return
        self._recorder = rec
        rec.finished.connect(self._video_done)
        rec.failed.connect(self._video_failed)
        rec.cancelled.connect(self._video_cancelled)
        rec.start()
        self.status(tr("st.recording", gkey=G("R") if plat.HOTKEYS_SUPPORTED else K("Ctrl+Shift+R")), 0)

    def _video_done(self, data: bytes, first: QImage, secs: float):
        self._recorder = None
        self._rec_restore()
        mid = self.store.put_media(data)
        t = self._capture_target()
        t.edit.insert_image(capture.video_thumbnail(first, secs), href=f"owvideo:{mid}")
        self.bring_to_front()
        self.status(tr("st.video_done", s=f"{secs:.0f}", mb=f"{len(data) / 1e6:.1f}"), 8000)

    def _video_failed(self, msg):
        self._recorder = None
        self._rec_restore()
        self.statusBar().clearMessage()
        QMessageBox.warning(self, tr("dlg.rec_title"), tr("dlg.rec_failed", msg=msg))

    def _video_cancelled(self):
        self._recorder = None
        self._rec_restore()
        self.status(tr("st.rec_cancelled"))

    def play_video(self, mid):
        try:
            data = self.store.get_media(mid)
        except Exception:
            QMessageBox.warning(self, tr("dlg.video"), tr("dlg.video_missing"))
            return
        d = capture.VideoDialog(self, data, tr("dlg.video"), lambda: self.export_video(mid))
        d.setAttribute(Qt.WA_DeleteOnClose)
        d.show()

    def export_video(self, mid):
        fn, _ = QFileDialog.getSaveFileName(self, tr("dlg.save_video"), f"{mid}.mp4", "MP4 (*.mp4)")
        if fn:
            Path(fn).write_bytes(self.store.get_media(mid))
            self.status(tr("st.saved_to", path=fn))

    # ------------------------------------------------------------ 가져오기·내보내기
    def import_notepad(self):
        tabs = notepad_import.read_tabs()
        if not tabs:
            QMessageBox.information(self, tr("dlg.np_title"), tr("dlg.np_none"))
            return
        already = {n.text for n in self.store.notes.values()}
        d = ImportDialog(self, tabs, already)
        if not d.exec():
            return
        chosen = d.selected()
        kind = "text" if d.as_text.isChecked() else "rich"
        cat = tr("np.category")
        self.store.add_category(cat)
        for t in chosen:
            title = Path(t.path).name if t.path else ""
            self.store.create(kind=kind, text=t.text, category=cat, title=title, created=t.mtime)
        self._filter = ("cat", cat)
        self.refresh_list()
        self.status(tr("st.np_done", n=len(chosen), cat=cat))

    def _import_files_dialog(self):
        fns, _ = QFileDialog.getOpenFileNames(self, tr("dlg.import_files"), "", tr("dlg.text_filter"))
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
        self.status(tr("st.files_imported", n=n))

    def export_notes(self, ids):
        ids = [i for i in ids if i in self.store.notes]
        if not ids:
            return
        if QMessageBox.question(self, tr("dlg.export_title"), tr("dlg.export_q")) \
                != QMessageBox.Yes:
            return
        d = QFileDialog.getExistingDirectory(self, tr("dlg.export_dir"))
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
        self.status(tr("st.exported", n=len(ids), path=d))

    # ------------------------------------------------------------ 보관 폴더·암호
    def change_folder(self):
        cur = str(self.store.folder)
        d = QFileDialog.getExistingDirectory(self, tr("dlg.new_folder"), cur)
        if not d or Path(d).resolve() == self.store.folder.resolve():
            return
        dest = Path(d)
        self.save_all()
        if crypto.vault_exists(dest):
            QMessageBox.information(self, tr("setup.folder"), tr("dlg.folder_exists"))
        else:
            r = QMessageBox.question(self, tr("dlg.move_title"), tr("dlg.move_q", cur=cur, dest=dest))
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
        QMessageBox.information(self, tr("setup.folder"), tr("dlg.restarting"))
        self.restart_app()

    def restart_app(self):
        """열린 메모를 모두 저장하고 끝낸 뒤 다시 실행 (hushpad_main.py가 'restart' 속성을 보고 새로 띄움)."""
        self.save_all()
        self.save_state()
        QApplication.instance().setProperty("restart", True)
        self.quit_app()   # close()만 하면 '트레이에 남기'일 때 숨기만 하므로 quit_app으로 끝낸다

    # ------------------------------------------------------------ 언어
    def set_language(self, code):
        old = i18n.current()
        self.cfg["language"] = code
        try:
            self.cfg.save()
        except OSError:
            pass
        new = i18n.resolve(code)
        if new == old:
            return
        msg = tr("lang.restart_msg")
        other = i18n.tr_in(new, "lang.restart_msg")
        box = QMessageBox(QMessageBox.Question, tr("menu.language"), msg if other == msg else f"{msg}\n\n{other}",
                          parent=self)
        now = box.addButton(tr("lang.restart_now"), QMessageBox.AcceptRole)
        box.addButton(tr("lang.later"), QMessageBox.RejectRole)
        box.setDefaultButton(now)
        box.exec()
        if box.clickedButton() is now:
            self.restart_app()
        else:
            self.status(tr("st.lang_later"))

    def change_passphrase(self):
        d = PassphraseDialog(self)
        if d.exec():
            crypto.change_passphrase(self.store.folder, self.store.key, d.pw1.text())
            self.status(tr("st.pw_changed"))

    def forget_here(self):
        crypto.forget_key(crypto.vault_id(self.store.folder))
        self.status(tr("st.forgot"))

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
                                         title=tr("conflict.title", title=t.note.display_title()))
                self.status(tr("st.conflict", title=copy.title), 10000)
            t.reload(remote)
            self._set_tab_look(i)
        for nid in removed:
            i = self._tab_index(nid)
            if i >= 0:
                t = self.tabs.widget(i)
                if t.dirty:  # 다른 곳에서 지워졌는데 아직 저장 안 된 고침이 있음 — 새 메모로 살려 둠
                    t.timer.stop()
                    t.collect()
                    copy = self.store.create(kind=t.note.kind, text=t.note.text, html=t.note.html,
                                             category=t.note.category,
                                             title=tr("conflict.title", title=t.note.display_title()))
                    self.status(tr("st.conflict", title=copy.title), 10000)
                    t.dirty = False
                self.tabs.removeTab(i)
                t.deleteLater()
        self._update_empty()
        self.list_timer.start()
