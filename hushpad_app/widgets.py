"""새 UI 부품: 2줄 메모 목록, 빈 화면, 명령 팔레트(Ctrl+K)."""
from __future__ import annotations

import json
import time

from PySide6.QtCore import QByteArray, QMimeData, QModelIndex, QPoint, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QIcon, QPainter, QPainterPath
from PySide6.QtWidgets import (QAbstractItemView, QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget,
                               QListWidgetItem, QPushButton, QStyle, QStyledItemDelegate, QVBoxLayout, QWidget)

from . import icons, plat
from .i18n import fmt_ts, tr

IDS_MIME = "application/x-hushpad-ids"
META = Qt.UserRole + 1


def rel_time(ts: float) -> str:
    d = time.time() - ts
    if d < 60:
        return tr("rel.now")
    if d < 3600:
        return tr("rel.min", n=int(d // 60))
    lt, now = time.localtime(ts), time.localtime()
    if lt.tm_year == now.tm_year and lt.tm_yday == now.tm_yday:
        return tr("rel.hour", n=int(d // 3600))
    if d < 86400 * 2 and (now.tm_yday - lt.tm_yday) % 365 == 1:
        return tr("rel.yesterday", time=fmt_ts(ts, "fmt.hm"))
    if lt.tm_year == now.tm_year:
        return fmt_ts(ts, "fmt.rel_md")
    return fmt_ts(ts, "fmt.rel_ymd")


# ====================================================================== 메모 목록
class NoteDelegate(QStyledItemDelegate):
    H = 60

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def sizeHint(self, opt, idx):
        return QSize(opt.rect.width(), self.H)

    def paint(self, p: QPainter, opt, idx: QModelIndex):
        t = self.owner.t
        m = idx.data(META) or {}
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(opt.rect).adjusted(6, 1, -6, -1)
        sel = bool(opt.state & QStyle.State_Selected)
        hov = bool(opt.state & QStyle.State_MouseOver)
        if sel or hov:
            path = QPainterPath()
            path.addRoundedRect(r, 7, 7)
            p.fillPath(path, QColor(t["accent_subtle"] if sel else t["hover"]))
        if sel:
            bar = QRectF(r.left() + 1, r.center().y() - 9, 3, 18)
            bp = QPainterPath()
            bp.addRoundedRect(bar, 1.5, 1.5)
            p.fillPath(bp, QColor(t["accent"]))
        right = r.right() - 10
        f1 = QFont(opt.font)
        f1.setPixelSize(13)
        f1.setWeight(QFont.DemiBold)
        f2 = QFont(opt.font)
        f2.setPixelSize(12)
        f3 = QFont(opt.font)
        f3.setPixelSize(11)
        fm1, fm2, fm3 = QFontMetrics(f1), QFontMetrics(f2), QFontMetrics(f3)
        y1 = r.top() + 10
        # 시간 (오른쪽)
        tm = m.get("time", "")
        p.setFont(f2)
        p.setPen(QColor(t["muted"]))
        tw = fm2.horizontalAdvance(tm)
        p.drawText(QRectF(right - tw, y1, tw + 2, fm1.height()), Qt.AlignRight | Qt.AlignVCenter, tm)
        # 앞쪽 고정 칸: 가장 중요한 상태 아이콘 하나 (자물쇠 > 고정 > 코드)
        slot = r.left() + 14
        name, col = None, None
        if m.get("secret"):
            name, col = "lock", t["gold"]
        elif m.get("pinned"):
            name, col = "pin", t["accent"]
        elif m.get("kind") == "text":
            name, col = "code", t["muted"]
        if name:
            p.drawPixmap(QRect(int(slot), int(y1 + (fm1.height() - 14) / 2), 14, 14), icons.pixmap(name, col, 14))
        x = slot + 20
        p.setFont(f1)
        p.setPen(QColor(t["accent_subtle_text"] if sel else t["text"]))
        title_w = right - tw - 10 - x
        p.drawText(QRectF(x, y1, title_w, fm1.height()), Qt.AlignLeft | Qt.AlignVCenter,
                   fm1.elidedText(m.get("title", ""), Qt.ElideRight, int(title_w)))
        if m.get("open") and not sel:
            p.setBrush(QColor(t["accent"]))
            p.setPen(Qt.NoPen)
            p.drawEllipse(QRectF(r.left() + 5, y1 + fm1.height() / 2 - 2, 4, 4))
        # 2줄: 분류 칩 · 미리보기
        y2 = y1 + fm1.height() + 6
        x2 = x
        cat = m.get("category", "")
        if cat:
            p.setFont(f3)
            cw = fm3.horizontalAdvance(cat) + 12
            chip = QRectF(x2, y2 + 1, cw, fm3.height() + 2)
            cp = QPainterPath()
            cp.addRoundedRect(chip, 4, 4)
            cc = QColor(t["accent"])
            cc.setAlpha(30)
            p.fillPath(cp, cc if sel else QColor(t["border_subtle"]))
            p.setPen(QColor(t["text2"]))
            p.drawText(chip, Qt.AlignCenter, cat)
            x2 += cw + 6
        p.setFont(f2)
        p.setPen(QColor(t["muted"]))
        snip = m.get("snippet", "")
        p.drawText(QRectF(x2, y2 + 1, right - x2, fm2.height()), Qt.AlignLeft | Qt.AlignVCenter,
                   fm2.elidedText(snip, Qt.ElideRight, int(right - x2)))
        p.restore()


class NoteList(QListWidget):
    files_dropped = Signal(list)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("NoteList")
        self.setItemDelegate(NoteDelegate(self))
        self.setMouseTracking(True)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    @property
    def t(self):
        return self.owner.t

    def mimeData(self, items):
        md = QMimeData()
        md.setData(IDS_MIME, QByteArray(json.dumps([i.data(Qt.UserRole) for i in items]).encode()))
        return md

    def mimeTypes(self):
        return [IDS_MIME, "text/uri-list"]

    def dragEnterEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        e.acceptProposedAction() if e.mimeData().hasUrls() else e.ignore()

    def dropEvent(self, e):
        if e.mimeData().hasUrls():
            self.files_dropped.emit([u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()])
            e.acceptProposedAction()
        else:
            e.ignore()


class CountDelegate(QStyledItemDelegate):
    """분류 목록: 기본 그리기 + 오른쪽 끝에 흐린 개수."""

    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def sizeHint(self, opt, idx):
        return QSize(opt.rect.width(), 32)

    def paint(self, p, opt, idx):
        super().paint(p, opt, idx)
        cnt = idx.data(Qt.UserRole + 2)
        if cnt:
            t = self.owner.t
            p.save()
            f = QFont(opt.font)
            f.setPixelSize(12)
            p.setFont(f)
            sel = bool(opt.state & QStyle.State_Selected)
            p.setPen(QColor(t["accent_subtle_text"] if sel else t["muted"]))
            p.drawText(QRect(opt.rect).adjusted(0, 0, -12, 0), Qt.AlignRight | Qt.AlignVCenter, str(cnt))
            p.restore()


# ====================================================================== 빈 화면
class EmptyState(QWidget):
    def __init__(self, owner):
        super().__init__()
        self.owner = owner
        self.setObjectName("EmptyState")
        self.setAttribute(Qt.WA_StyledBackground, True)
        lay = QVBoxLayout(self)
        lay.addStretch(3)
        self.icon = QLabel(alignment=Qt.AlignCenter)
        title = QLabel(tr("empty.title"), objectName="EmptyTitle", alignment=Qt.AlignCenter)
        hint = QLabel(tr("empty.hint"), objectName="EmptyHint", alignment=Qt.AlignCenter)
        hint.setWordWrap(True)
        row = QHBoxLayout()
        row.addStretch(1)
        self.b1 = QPushButton("  " + tr("tb.new"), objectName="Primary")
        self.b2 = QPushButton("  " + tr("empty.code"))
        self.b1.clicked.connect(lambda: owner.new_note("rich"))
        self.b2.clicked.connect(lambda: owner.new_note("text"))
        for b in (self.b1, self.b2):
            b.setMinimumHeight(34)
            b.setCursor(Qt.PointingHandCursor)
            row.addWidget(b)
        row.addStretch(1)
        keys = QHBoxLayout()
        keys.addStretch(1)
        chips = [(plat.key_label("Ctrl+K"), tr("empty.k_palette"))]
        if plat.HOTKEYS_SUPPORTED:
            chips += [(plat.global_key("S"), tr("empty.k_shot")), (plat.global_key("R"), tr("tb.record"))]
        else:
            chips += [(plat.key_label("Ctrl+Shift+S"), tr("empty.k_shot")),
                      (plat.key_label("Ctrl+Shift+R"), tr("tb.record"))]
        for k, d in chips:
            keys.addWidget(QLabel(k, objectName="Kbd"))
            keys.addWidget(QLabel(d, objectName="EmptyHint"))
            keys.addSpacing(14)
        keys.addStretch(1)
        for w in (self.icon, title, hint):
            lay.addWidget(w)
            lay.addSpacing(4)
        lay.addSpacing(14)
        lay.addLayout(row)
        lay.addSpacing(22)
        lay.addLayout(keys)
        lay.addStretch(4)

    def retheme(self, t):
        self.icon.setPixmap(icons.pixmap("note", t["muted"], 48))
        self.b1.setIcon(icons.icon("plus", t["accent_text"]))
        self.b2.setIcon(icons.icon("code", t["text2"]))


# ====================================================================== 명령 팔레트
ROW = 36


class PaletteDelegate(QStyledItemDelegate):
    def __init__(self, owner):
        super().__init__(owner)
        self.owner = owner

    def sizeHint(self, opt, idx):
        kind = (idx.data(Qt.UserRole) or ("", None))[0]
        return QSize(opt.rect.width(), 26 if kind == "header" else ROW)

    def paint(self, p, opt, idx):
        t = self.owner.owner.t
        kind, _ref = idx.data(Qt.UserRole) or ("", None)
        title, sub, ic = idx.data(Qt.UserRole + 1) or ("", "", None)
        p.save()
        p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(opt.rect)
        if kind == "header":
            f = QFont(opt.font)
            f.setPixelSize(11)
            f.setWeight(QFont.DemiBold)
            p.setFont(f)
            p.setPen(QColor(t["muted"]))
            p.drawText(r.adjusted(12, 6, 0, 0), Qt.AlignLeft | Qt.AlignVCenter, title)
            p.restore()
            return
        sel = bool(opt.state & QStyle.State_Selected)
        if sel:
            path = QPainterPath()
            path.addRoundedRect(r.adjusted(0, 1, 0, -1), 7, 7)
            p.fillPath(path, QColor(t["accent_subtle"]))
        if ic is not None and not ic.isNull():
            ic.paint(p, QRect(int(r.left() + 12), int(r.center().y() - 8), 16, 16))
        f = QFont(opt.font)
        f.setPixelSize(13)
        p.setFont(f)
        fm = QFontMetrics(f)
        right = r.right() - 10
        sw = 0
        if sub:
            fk = QFont(opt.font)
            fk.setPixelSize(11)
            fmk = QFontMetrics(fk)
            sw = fmk.horizontalAdvance(sub) + 12
            chip = QRectF(right - sw, r.center().y() - 10, sw, 20)
            if kind == "cmd":
                cp = QPainterPath()
                cp.addRoundedRect(chip, 5, 5)
                p.fillPath(cp, QColor(t["window"]))
                p.setPen(QColor(t["border"]))
                p.drawPath(cp)
            p.setFont(fk)
            p.setPen(QColor(t["text2"] if kind == "cmd" else t["muted"]))
            p.drawText(chip, Qt.AlignCenter, sub)
            p.setFont(f)
        p.setPen(QColor(t["accent_subtle_text"] if sel else t["text"]))
        x = r.left() + 38
        w = right - sw - 12 - x
        p.drawText(QRectF(x, r.top(), w, r.height()), Qt.AlignLeft | Qt.AlignVCenter,
                   fm.elidedText(title, Qt.ElideRight, int(w)))
        p.restore()


class CommandPalette(QDialog):
    """Ctrl+K: 메모 제목·내용과 모든 명령을 한 곳에서 찾아 실행."""

    def __init__(self, owner):
        super().__init__(owner, Qt.FramelessWindowHint | Qt.Popup)
        self.owner = owner
        self.setAttribute(Qt.WA_TranslucentBackground)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        box = QFrame(objectName="Palette")
        outer.addWidget(box)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.inp = QLineEdit(objectName="PaletteInput", placeholderText=tr("pal.placeholder"))
        self.search_act = self.inp.addAction(QIcon(), QLineEdit.LeadingPosition)
        self.lst = QListWidget(objectName="PaletteList")
        self.lst.setItemDelegate(PaletteDelegate(self))
        self.lst.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lst.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        foot = QLabel(tr("pal.foot"), objectName="PaletteFoot")
        lay.addWidget(self.inp)
        lay.addWidget(self.lst)
        lay.addWidget(foot)
        self.inp.textChanged.connect(self._fill)
        self.inp.installEventFilter(self)
        self.lst.itemActivated.connect(self._run)
        self.lst.itemClicked.connect(self._run)
        self.setFixedWidth(600)

    def open_(self):
        t = self.owner.t
        self.search_act.setIcon(icons.icon("search", t["muted"]))
        self.inp.clear()
        self._fill("")
        g = self.owner.geometry()
        self.move(g.center().x() - self.width() // 2, g.top() + 80)
        self.show()
        self.inp.setFocus()

    def _add(self, kind, ref, title, sub="", ic=None):
        it = QListWidgetItem()
        it.setData(Qt.UserRole, (kind, ref))
        it.setData(Qt.UserRole + 1, (title, sub, ic))
        if kind == "header":
            it.setFlags(Qt.NoItemFlags)
        self.lst.addItem(it)

    def _fill(self, q):
        t = self.owner.t
        self.lst.clear()
        words = q.lower().split()
        notes = [n for n in self.owner.store.notes.values() if n.deleted is None]
        notes.sort(key=lambda n: n.updated, reverse=True)
        hits_n = []
        for n in notes:
            hay = (n.display_title() + " " + (n.category or "")).lower()
            if not n.secret:
                hay += " " + n.text[:4000].lower()
            if all(w in hay for w in words):
                hits_n.append(n)
        hits_c = [(a, label, ic) for a, label, ic in self.owner.palette_actions()
                  if all(w in label.lower() for w in words)]
        sections = [(tr("pal.notes") if words else tr("pal.recent"), hits_n[: (30 if words else 6)], "note"),
                    (tr("pal.commands"), hits_c, "cmd")]
        if not words:
            sections.reverse()
            sections = [sections[1], sections[0]]
        for head, items, kind in sections:
            if not items:
                continue
            self._add("header", None, head)
            for x in items:
                if kind == "note":
                    ic = icons.icon("lock" if x.secret else ("code" if x.kind == "text" else "note"),
                                    t["gold"] if x.secret else t["text2"])
                    self._add("note", x.id, x.display_title(), x.category or rel_time(x.updated), ic)
                else:
                    a, label, ic = x
                    sc = a.shortcut().toString(QKeySequenceFormat()) if not a.shortcut().isEmpty() else ""
                    self._add("cmd", a, label, sc, ic)
        for i in range(self.lst.count()):
            if self.lst.item(i).flags() & Qt.ItemIsSelectable:
                self.lst.setCurrentRow(i)
                break
        rows = sum(26 if self.lst.item(i).data(Qt.UserRole)[0] == "header" else ROW
                   for i in range(min(self.lst.count(), 11)))
        self.lst.setFixedHeight(max(ROW, rows) + 14)
        self.adjustSize()

    def _step(self, d):
        r = self.lst.currentRow()
        for _ in range(self.lst.count()):
            r = max(0, min(self.lst.count() - 1, r + d))
            if self.lst.item(r).flags() & Qt.ItemIsSelectable:
                self.lst.setCurrentRow(r)
                return
            if r in (0, self.lst.count() - 1):
                return

    def eventFilter(self, obj, e):
        from PySide6.QtCore import QEvent
        if e.type() == QEvent.KeyPress:
            k = e.key()
            if k in (Qt.Key_Down, Qt.Key_Up):
                self._step(1 if k == Qt.Key_Down else -1)
                return True
            if k in (Qt.Key_Return, Qt.Key_Enter):
                it = self.lst.currentItem()
                if it:
                    self._run(it)
                return True
            if k == Qt.Key_Escape:
                self.close()
                return True
        return super().eventFilter(obj, e)

    def _run(self, it):
        kind, ref = it.data(Qt.UserRole)
        if kind == "header":
            return
        self.close()
        if kind == "cmd":
            ref.trigger()
        else:
            self.owner.open_note(ref)
            tab = self.owner._cur_tab()
            if tab:
                tab.edit.setFocus()


def QKeySequenceFormat():
    from PySide6.QtGui import QKeySequence
    return QKeySequence.NativeText
