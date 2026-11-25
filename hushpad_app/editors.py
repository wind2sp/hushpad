"""편집기 두 가지.

RichEdit  — 서식 메모. 웹·워드에서 복사한 서식을 그대로 붙이고, 이미지·스크린샷·동영상을 넣을 수 있다.
            내용의 '텍스트만' 버전은 항상 함께 저장되어, 밖으로 복사할 때 서식 포함/텍스트만을 고를 수 있다.
CodeEdit  — 텍스트 메모. HTML·JSON·코드를 고칠 때. 붙여넣기는 언제나 텍스트만, 줄 번호·자동 들여쓰기·색 구분.
"""
from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import QEvent, QMimeData, QRect, QRegularExpression, QSize, Qt, QUrl, Signal
from PySide6.QtGui import (QColor, QDesktopServices, QDrag, QPixmap, QFont, QFontDatabase, QImage, QKeySequence, QPainter,
                           QSyntaxHighlighter, QTextCharFormat, QAction, QIcon, QTextBlockFormat, QTextCursor, QTextFormat, QTextImageFormat, QTextLength,
                           QTextListFormat)
from PySide6.QtWidgets import QApplication, QFileDialog, QMenu, QPlainTextEdit, QTextEdit, QWidget

from . import plat
from .common import data_url_to_image, image_to_data_url, mark_private, share_image_files
from .i18n import tr

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".jfif", ".gif", ".bmp", ".webp", ".tif", ".tiff", ".ico"}


def _dropped_images(src: QMimeData) -> list | None:
    """탐색기에서 끌어온 것이 모두 그림 파일이면 그 경로 목록, 아니면 None."""
    if not src.hasUrls():
        return None
    urls = src.urls()
    files = [Path(u.toLocalFile()) for u in urls if u.isLocalFile()]
    if files and len(files) == len(urls) and all(f.suffix.lower() in IMAGE_EXT for f in files):
        return files
    return None
_REMOTE_IMG = re.compile(r"<img\b[^>]*\bsrc\s*=\s*[\"']?(?:https?:|file:|//)[^>]*>", re.I)
MAX_DISPLAY_W = 900
MAX_DISPLAY_H = 900   # 세로로 긴 그림(휴대폰 화면 캡처 등)은 이 높이 안으로 줄여 보인다 (원본 해상도는 그대로)


def mono_font(pt: int) -> QFont:
    from .theme import code_families
    f = QFont()
    f.setFamilies(code_families())
    f.setStyleHint(QFont.Monospace)
    f.setPointSize(max(7, pt - 1))
    return f


def body_font(pt: int) -> QFont:
    from .theme import ui_families
    f = QFont()
    f.setFamilies(ui_families())
    f.setPointSize(pt)
    return f


READ_WIDTH = 720
# 오른쪽 클릭 › 글자 색·형광펜 (이름은 locales의 color.*)
TEXT_COLORS = (("red", "#d93025"), ("orange", "#e8710a"), ("green", "#188038"),
               ("blue", "#1a73e8"), ("purple", "#8e24aa"), ("gray", "#80868b"))
MARK_COLORS = (("yellow", "#fff176"), ("green", "#c8e6c9"), ("blue", "#bbdefb"), ("pink", "#f8bbd0"))
MARK_TEXT = "#202124"     # 형광펜 위 글자는 어두운 테마에서도 읽히게 진한 색으로
# 줄 첫머리에 이렇게 쓰고 스페이스를 누르면 목록으로 바뀐다
AUTO_LIST = {"[]": "todo", "[ ]": "todo", "- [ ]": "todo", "[x]": "done", "- [x]": "done",
             "-": "bullet", "*": "bullet", "1.": "number"}
_UNCHECKED = QTextBlockFormat.MarkerType.Unchecked
_CHECKED = QTextBlockFormat.MarkerType.Checked
_NOMARK = QTextBlockFormat.MarkerType.NoMarker

DOC_CSS = ("h1 { font-size: 24px; font-weight: 700; } h2 { font-size: 19px; font-weight: 700; } "
           "h3 { font-size: 16px; font-weight: 600; } p, li { margin-top: 2px; margin-bottom: 2px; }")
_VALUE_RE = re.compile(r"""^\s*(?:export\s+)?["']?[\w.\- ]{1,60}["']?\s*[:=]\s*(.+?)\s*,?\s*$""")


def line_value(line: str) -> str:
    """'KEY=값', '"key": "값",' 같은 줄에서 값만 꺼낸다."""
    m = _VALUE_RE.match(line)
    if not m:
        return ""
    v = m.group(1).strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'`":
        v = v[1:-1]
    return v if v and v not in ("{", "[") else ""


class _CopyMixin:
    """Ctrl+C / Ctrl+X 를 창(host)의 복사 함수로 보내 클립보드 보호 옵션을 적용.
    Ctrl+휠·터치패드 두 손가락 벌리기/모으기로 글자 크기 확대·축소."""
    host = None
    _wheel_acc = 0
    _pinch_acc = 0.0

    def wheelEvent(self, e):
        # Windows 정밀 터치패드의 두 손가락 확대·축소도 Ctrl+휠로 들어온다
        if e.modifiers() & Qt.ControlModifier:
            self._wheel_acc += e.angleDelta().y()
            while abs(self._wheel_acc) >= 120:
                step = 1 if self._wheel_acc > 0 else -1
                self._wheel_acc -= 120 * step
                self.host.zoom(step)
            e.accept()
            return
        super().wheelEvent(e)

    def event(self, e):
        # macOS 트랙패드 핀치
        if e.type() == QEvent.NativeGesture and e.gestureType() == Qt.ZoomNativeGesture:
            self._pinch_acc += e.value()
            while abs(self._pinch_acc) >= 0.08:
                step = 1 if self._pinch_acc > 0 else -1
                self._pinch_acc -= 0.08 * step
                self.host.zoom(step)
            return True
        return super().event(e)

    def _copy_keys(self, e) -> bool:
        if e.matches(QKeySequence.Copy):
            self.host.copy_selection(self, plain=False)
            return True
        if e.matches(QKeySequence.Cut):
            if self.textCursor().hasSelection() and not self.isReadOnly():
                self.host.copy_selection(self, plain=False)
                self.textCursor().removeSelectedText()
            return True
        return False


# ====================================================================== 서식 메모
class RichEdit(_CopyMixin, QTextEdit):
    play_video = Signal(str)

    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host = host
        self.setObjectName("Editor")
        self.setAcceptRichText(True)
        self.document().setDefaultFont(body_font(host.cfg["font_pt"]))
        self.document().setDocumentMargin(4)
        self.document().setDefaultStyleSheet(DOC_CSS)
        self.document().setIndentWidth(20)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.setMouseTracking(True)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        side = max(24, (self.width() - READ_WIDTH) // 2)   # 읽기 좋은 폭(720px)으로 가운데
        m = self.viewportMargins()
        if m.left() != side:
            self.setViewportMargins(side, 22, side, 0)

    def paintEvent(self, e):
        super().paintEvent(e)

    def retheme(self):
        pass

    def comfy(self):
        """줄 간격을 넉넉하게 (본문 150%)."""
        from PySide6.QtGui import QTextBlockFormat
        c = QTextCursor(self.document())
        c.select(QTextCursor.Document)
        bf = QTextBlockFormat()
        bf.setLineHeight(150, 1)  # ProportionalHeight
        c.mergeBlockFormat(bf)

    # ------------------------------------------------ 붙여넣기
    def canInsertFromMimeData(self, src: QMimeData) -> bool:
        return src.hasImage() or src.hasUrls() or super().canInsertFromMimeData(src)

    def insertFromMimeData(self, src: QMimeData) -> None:
        # 탐색기에서 끌어온 그림 파일: '일반 텍스트로 붙여넣기'가 켜져 있어도 그림으로 넣는다
        # (예전에는 이때 파일 경로 글자가 들어갔다). 못 읽는 그림도 경로 대신 안내만.
        files = _dropped_images(src)
        if files:
            bad = 0
            for f in files:
                img = QImage(str(f))
                if img.isNull():
                    bad += 1
                else:
                    self.insert_image(img)
            if bad:
                self.host.status(tr("ed.image_unreadable", n=bad))
            return
        if self.host.plain_paste_now():
            self.insert_plain(src.text())
            return
        if src.hasImage() and not (src.hasText() and src.text().strip()):
            img = QImage(src.imageData())
            if not img.isNull():
                self.insert_image(img)
                return
        if src.hasHtml():
            md = QMimeData()
            md.setHtml(_REMOTE_IMG.sub("", src.html()))  # 인터넷 그림 주소는 열 수 없어 빈 칸이 되므로 뺌
            if src.hasText():
                md.setText(src.text())
            super().insertFromMimeData(md)
            if "<img" in md.html().lower():
                c = self.textCursor()
                c.joinPreviousEditBlock()    # 붙여넣기와 한 번에 되돌리기
                self.fit_images()
                c.endEditBlock()
            return
        super().insertFromMimeData(src)

    @staticmethod
    @staticmethod
    def fit_format(fmt: QTextImageFormat) -> bool:
        """큰 그림이 메모 폭을 넘거나 너무 길면 줄여 보이게 한다 (보이는 크기만, 그림 데이터는 원본 그대로).
        폭은 메모 칸 안(최대 100%), 세로로 긴 그림은 높이 MAX_DISPLAY_H 안. 바꿀 것이 있으면 True."""
        w, h = fmt.width(), fmt.height()
        if not (w > 0 and h > 0):
            img = data_url_to_image(fmt.name())
            if img is None or img.isNull():
                return False
            dpr = img.devicePixelRatio() or 1
            iw, ih = img.width() / dpr, img.height() / dpr
            w = w if w > 0 else min(iw, MAX_DISPLAY_W)
            h = w * ih / iw if iw else ih
        want_w = round(min(w, w * MAX_DISPLAY_H / h), 1) if h > MAX_DISPLAY_H else round(w, 1)
        want_max = QTextLength(QTextLength.PercentageLength, 100)
        if (fmt.hasProperty(QTextFormat.ImageMaxWidth) and fmt.maximumWidth() == want_max
                and not fmt.hasProperty(QTextFormat.ImageHeight) and abs(fmt.width() - want_w) < 0.5):
            return False
        fmt.setWidth(want_w)
        fmt.setMaximumWidth(want_max)
        # 높이를 정해 두면 폭만 줄고 높이는 그대로라 그림이 찌그러진다. 폭만 두면 Qt가 비율대로 높이를 맞춘다.
        fmt.clearProperty(QTextFormat.ImageHeight)
        return True

    @staticmethod
    def _tight_image_line(block) -> bool:
        """그림만 있는 줄은 줄 간격 100% (150%면 큰 그림 아래에 그림 높이 절반만큼 빈칸이 생긴다)."""
        t = block.text()
        if not t or t.strip("￼"):
            return False
        bf = block.blockFormat()
        if bf.lineHeightType() == 1 and bf.lineHeight() == 100:
            return False
        from PySide6.QtGui import QTextBlockFormat
        nf = QTextBlockFormat()
        nf.setLineHeight(100, 1)   # ProportionalHeight
        QTextCursor(block).mergeBlockFormat(nf)
        return True

    def fit_images(self) -> int:
        """문서 안 모든 그림에 fit_format 적용. 바꾼 개수."""
        doc = self.document()
        n = 0
        block = doc.begin()
        while block.isValid():
            self._tight_image_line(block)
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                f = frag.charFormat()
                if f.isImageFormat():
                    fmt = f.toImageFormat()
                    if self.fit_format(fmt):
                        c = QTextCursor(doc)
                        c.setPosition(frag.position())
                        c.setPosition(frag.position() + frag.length(), QTextCursor.KeepAnchor)
                        c.setCharFormat(fmt)
                        n += 1
                it += 1
            block = block.next()
        return n

    def insert_plain(self, text: str) -> None:
        c = self.textCursor()
        c.insertText(text.replace("\r\n", "\n"), QTextCharFormat())
        self.setTextCursor(c)

    def insert_image(self, img: QImage, href: str = "") -> None:
        dpr = img.devicePixelRatio() or 1
        w, h = img.width() / dpr, img.height() / dpr
        disp_w = min(w, MAX_DISPLAY_W)
        fmt = QTextImageFormat()
        fmt.setName(image_to_data_url(img))
        fmt.setWidth(disp_w)
        fmt.setHeight(h * disp_w / w if w else h)
        if href:
            fmt.setAnchor(True)
            fmt.setAnchorHref(href)
            fmt.setToolTip(tr("ed.play_tip"))
        self.fit_format(fmt)
        c = self.textCursor()
        line_fmt = c.blockFormat()                 # 그림 다음 줄은 원래 줄 간격으로
        c.insertImage(fmt)
        self._tight_image_line(c.block())
        c.insertBlock(line_fmt)
        self.setTextCursor(c)
        self.ensureCursorVisible()

    # ------------------------------------------------ 복사
    def createMimeDataFromSelection(self) -> QMimeData:
        # Qt가 주는 QTextEditMimeData는 나중에 덧붙인 형식(그림·클립보드 보호 표시)을 클립보드로 넘기지 않는다.
        # 그래서 내용을 새 QMimeData에 옮겨 담는다.
        src = super().createMimeDataFromSelection()
        c = self.textCursor()
        imgs = self._images_in_selection(c)
        text = src.text().replace("￼", "")
        md = QMimeData()
        if imgs and not text.strip():
            # 그림만 골랐으면 그림으로만 복사한다. 글자 칸이 있으면 메신저·메일이 빈 글자를 붙여 넣는다.
            md.setImageData(imgs[0])
            if len(imgs) > 1:
                md.setHtml(src.html())

        else:
            md.setHtml(src.html())
            md.setText(text)
        if self.host.cfg["clip_private"]:
            mark_private(md)
        return md

    def _images_in_selection(self, c: QTextCursor) -> list:
        """선택 안의 그림(동영상 미리보기 포함)을 차례대로."""
        out = []
        if not c.hasSelection():
            return out
        start, end = c.selectionStart(), c.selectionEnd()
        block = self.document().findBlock(start)
        while block.isValid() and block.position() <= end:
            it = block.begin()
            while not it.atEnd():
                frag = it.fragment()
                if frag.position() + frag.length() > start and frag.position() < end:
                    f = frag.charFormat()
                    if f.isImageFormat():
                        img = data_url_to_image(f.toImageFormat().name())
                        if img is not None:
                            out.extend([img] * min(frag.length(), end - max(start, frag.position())))
                it += 1
            block = block.next()
        return out

    def image_at(self, pos) -> QTextImageFormat | None:
        c = self.cursorForPosition(pos)
        for delta in (1, 0):
            cc = QTextCursor(c)
            if delta:
                if not cc.movePosition(QTextCursor.Right):
                    continue
            f = cc.charFormat()
            if f.isImageFormat():
                return f.toImageFormat()
        return None

    # ------------------------------------------------ 키·마우스
    def keyPressEvent(self, e):
        if self._copy_keys(e):
            return
        mods = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier | Qt.AltModifier | Qt.MetaModifier)
        if mods == Qt.ControlModifier and e.key() in (Qt.Key_I, Qt.Key_U):
            (self.toggle_italic if e.key() == Qt.Key_I else self.toggle_underline)()
            return
        if mods == (Qt.ControlModifier | Qt.ShiftModifier) and e.key() == Qt.Key_L:
            self.set_list("todo")
            return
        if e.key() == Qt.Key_Space and not mods and self._auto_list():
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not mods:
            super().keyPressEvent(e)
            # 체크한 할 일 다음에 새로 생긴 줄은 빈 칸으로 시작
            k = self.textCursor()
            if k.block().blockFormat().marker() == _CHECKED and not k.block().text():
                bf = k.blockFormat()
                bf.setMarker(_UNCHECKED)
                k.setBlockFormat(bf)
            return
        super().keyPressEvent(e)

    def mousePressEvent(self, e):
        """그림을 한 번 누르면 그 그림을 고른다 (Ctrl+C로 바로 복사할 수 있게)."""
        super().mousePressEvent(e)
        self._drag_from = None
        if e.button() == Qt.LeftButton and not e.modifiers():
            c = self._image_cursor(e.position().toPoint())
            if c is not None:
                self.setTextCursor(c)
                self._drag_from = e.position().toPoint()

    def mouseMoveEvent(self, e):
        """그림을 눌러 끌면 그림 파일로 끌어 나간다 (웹 첨부 칸·탐색기·메일에 바로 놓기).
        복사만 한다. 옮기기로 놓으면 메모에서 그림이 지워지므로."""
        start = getattr(self, "_drag_from", None)
        if start is not None and e.buttons() & Qt.LeftButton:
            if (e.position().toPoint() - start).manhattanLength() >= QApplication.startDragDistance():
                self._drag_from = None
                md = self.createMimeDataFromSelection()
                imgs = self._images_in_selection(self.textCursor())
                # 끌 때만 파일로도 준다 (클립보드에 파일을 넣으면 파일 경로가 글자로도 붙어 메신저에 경로가 들어감)
                urls = share_image_files(imgs)
                if urls:
                    md.setUrls(urls)
                drag = QDrag(self)
                drag.setMimeData(md)
                if imgs:
                    drag.setPixmap(QPixmap.fromImage(imgs[0]).scaled(
                        160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                drag.exec(Qt.CopyAction)
                return
            return
        super().mouseMoveEvent(e)

    def _image_cursor(self, pos) -> QTextCursor | None:
        """pos 위치의 그림 한 칸을 고른 커서. 그림이 아니면 None."""
        base = self.cursorForPosition(pos).position()
        for p in (base, base - 1):
            if p < 0:
                continue
            c = QTextCursor(self.document())
            c.setPosition(p)
            left = self.cursorRect(c).left()            # 그림 왼쪽 끝
            if not c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor):
                continue
            f = c.charFormat()
            if f.isImageFormat():
                right = self.cursorRect(c).left()       # 그림 오른쪽 끝 (줄여 보인 크기)
                if right <= left:
                    right = left + (f.toImageFormat().width() or 0)
                if left - 2 <= pos.x() <= right + 2:   # 그림 위를 눌렀을 때만 (옆 빈 곳 제외)
                    return c
        return None

    def mouseDoubleClickEvent(self, e):
        f = self.image_at(e.position().toPoint())
        if f is not None and f.anchorHref().startswith("owvideo:"):
            self.play_video.emit(f.anchorHref().split(":", 1)[1])
            return
        super().mouseDoubleClickEvent(e)

    def mouseReleaseEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            href = self.anchorAt(e.position().toPoint())
            if href.startswith(("http://", "https://")):
                QDesktopServices.openUrl(QUrl(href))
                return
        super().mouseReleaseEvent(e)

    def contextMenuEvent(self, e):
        # 고른 글 밖을 누르면 누른 자리로 커서를 옮긴다 (그 자리에 서식을 주려고)
        c = self.textCursor()
        hit = self.cursorForPosition(e.pos()).position()
        if not c.hasSelection() or not (c.selectionStart() <= hit <= c.selectionEnd()):
            self.setTextCursor(self.cursorForPosition(e.pos()))
        menu = self.createStandardContextMenu(e.pos())
        f = self.image_at(e.pos())
        if f is None and not self.isReadOnly() and menu.actions():
            self.format_actions(menu, menu.actions()[0])
        if f is not None:
            menu.addSeparator()
            href = f.anchorHref()
            if href.startswith("owvideo:"):
                mid = href.split(":", 1)[1]
                menu.addAction(tr("ed.play"), lambda: self.play_video.emit(mid))
                menu.addAction(tr("ed.save_video"), lambda: self.host.export_video(mid))
            img = data_url_to_image(f.name())
            if img is not None:
                menu.addAction(tr("ed.copy_image"), lambda: self.host.copy_image(img))
                menu.addAction(tr("ed.save_image"), lambda: self._save_image(img))
        menu.addSeparator()
        menu.addAction(tr("ed.copy_plain") + "\t" + plat.key_label("Ctrl+Shift+C"), lambda: self.host.copy_selection(self, plain=True))
        menu.addAction(tr("act.paste_plain") + "\t" + plat.key_label("Ctrl+Shift+V"), self.host.paste_plain)
        if f is not None:
            menu.addAction(tr("act.clear_fmt"), self.host.clear_format)
        menu.exec(e.globalPos())

    # ------------------------------------------------ 서식 (오른쪽 클릭·단축키)
    def _fmt_target(self) -> QTextCursor:
        """서식을 바꿀 곳: 고른 글, 없으면 커서가 들어 있는 낱말. 낱말 밖이면 선택 없는 커서(다음에 쓸 글)."""
        c = self.textCursor()
        if not c.hasSelection():
            w = QTextCursor(c)
            w.select(QTextCursor.WordUnderCursor)
            if w.hasSelection() and w.selectionStart() < c.position() < w.selectionEnd():
                return w
        return c

    def merge_fmt(self, fmt: QTextCharFormat) -> None:
        c = self._fmt_target()
        if c.hasSelection():
            c.mergeCharFormat(fmt)
        else:
            self.mergeCurrentCharFormat(fmt)

    def fmt_state(self) -> QTextCharFormat:
        c = self._fmt_target()
        if c.hasSelection():
            k = QTextCursor(c)
            k.setPosition(c.selectionStart())
            k.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            return k.charFormat()
        return self.currentCharFormat()

    def toggle_bold(self):
        f = QTextCharFormat()
        f.setFontWeight(QFont.Normal if self.fmt_state().fontWeight() > QFont.Normal else QFont.Bold)
        self.merge_fmt(f)

    def toggle_italic(self):
        f = QTextCharFormat()
        f.setFontItalic(not self.fmt_state().fontItalic())
        self.merge_fmt(f)

    def toggle_underline(self):
        f = QTextCharFormat()
        f.setFontUnderline(not self.fmt_state().fontUnderline())
        self.merge_fmt(f)

    def toggle_strike(self):
        f = QTextCharFormat()
        f.setFontStrikeOut(not self.fmt_state().fontStrikeOut())
        self.merge_fmt(f)

    def set_text_color(self, color):
        """None이면 기본 색(테마를 따름)."""
        if color is None:
            self._clear_char_prop(self._fmt_target(), QTextFormat.ForegroundBrush)
            return
        f = QTextCharFormat()
        f.setForeground(QColor(color))
        self.merge_fmt(f)

    def set_highlight(self, color):
        if color is None:
            self._clear_char_prop(self._fmt_target(), QTextFormat.BackgroundBrush, drop_mark_text=True)
            return
        f = QTextCharFormat()
        f.setBackground(QColor(color))
        if not self.fmt_state().hasProperty(QTextFormat.ForegroundBrush):
            f.setForeground(QColor(MARK_TEXT))
        self.merge_fmt(f)

    def _clear_char_prop(self, c: QTextCursor, prop, drop_mark_text=False):
        """선택 안의 글자마다 서식 하나를 지운다 (mergeCharFormat으로는 지울 수 없어서)."""
        def strip(f: QTextCharFormat) -> QTextCharFormat:
            if drop_mark_text and f.foreground().color().name() == MARK_TEXT:
                f.clearForeground()
            f.clearProperty(prop)
            return f
        if not c.hasSelection():
            self.setCurrentCharFormat(strip(self.currentCharFormat()))
            return
        start, end = c.selectionStart(), c.selectionEnd()
        c.beginEditBlock()
        for pos in range(start, end):
            k = QTextCursor(self.document())
            k.setPosition(pos)
            k.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor)
            if not k.charFormat().isImageFormat():
                k.setCharFormat(strip(k.charFormat()))
        c.endEditBlock()

    @staticmethod
    def _kind_of(blk) -> str:
        """그 줄의 목록 종류: todo / done / bullet / number / ''."""
        m = blk.blockFormat().marker()
        if m == _UNCHECKED:
            return "todo"
        if m == _CHECKED:
            return "done"
        lst = blk.textList()
        if lst is None:
            return ""
        return "number" if lst.format().style() == QTextListFormat.ListDecimal else "bullet"

    def list_kind(self) -> str:
        return self._kind_of(self.textCursor().block())

    def set_list(self, kind: str):
        """고른 줄들(없으면 지금 줄)을 할 일·글머리 기호·번호 목록으로. 이미 그 목록이면 목록을 푼다."""
        c = self.textCursor()
        cur = self.list_kind()
        undo = cur == kind or (kind == "todo" and cur == "done")
        start, end = c.selectionStart(), c.selectionEnd()
        blocks = []
        b = self.document().findBlock(start)
        while b.isValid() and b.position() <= end:
            blocks.append(b)
            b = b.next()
        c.beginEditBlock()
        for blk in blocks:
            lst = blk.textList()
            if undo:
                if lst is not None:
                    lst.remove(blk)
                k = QTextCursor(blk)
                bf = k.blockFormat()
                bf.setMarker(_NOMARK)
                bf.setIndent(0)
                k.setBlockFormat(bf)
                continue
            want_num = kind == "number"
            if lst is not None and (lst.format().style() == QTextListFormat.ListDecimal) != want_num:
                lst.remove(blk)
                lst = None
            if lst is None:
                prev = blk.previous()
                plst = prev.textList() if prev.isValid() else None
                same_kind = {"todo": ("todo", "done"), "done": ("todo", "done")}.get(kind, (kind,))
                if plst is not None and self._kind_of(prev) in same_kind:
                    plst.add(blk)                       # 바로 위 목록에 이어 붙인다
                else:
                    lf = QTextListFormat()
                    lf.setStyle(QTextListFormat.ListDecimal if want_num else QTextListFormat.ListDisc)
                    QTextCursor(blk).createList(lf)
            k = QTextCursor(blk)
            bf = k.blockFormat()
            bf.setMarker(_UNCHECKED if kind == "todo" else _CHECKED if kind == "done" else _NOMARK)
            bf.setLineHeight(150, 1)                  # 본문과 같은 줄 간격 (comfy)
            k.setBlockFormat(bf)
        c.endEditBlock()

    def _auto_list(self) -> bool:
        """줄 첫머리의 '[] '·'- '·'1. ' 같은 글을 목록으로 바꾼다 (스페이스를 누른 순간)."""
        c = self.textCursor()
        if c.hasSelection() or c.block().textList() is not None:
            return False
        kind = AUTO_LIST.get(c.block().text()[:c.positionInBlock()])
        if kind is None:
            return False
        c.beginEditBlock()
        c.movePosition(QTextCursor.StartOfBlock, QTextCursor.KeepAnchor)
        c.removeSelectedText()
        c.endEditBlock()
        self.setTextCursor(c)
        self.set_list(kind)
        return True

    @staticmethod
    def _color_icon(color) -> QIcon:
        pm = QPixmap(14, 14)
        pm.fill(Qt.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QColor("#9aa0a6"))
        if color:
            p.setBrush(QColor(color))
        p.drawRoundedRect(1, 1, 12, 12, 3, 3)
        if not color:
            p.drawLine(3, 11, 11, 3)
        p.end()
        return QIcon(pm)

    def format_actions(self, menu: QMenu, before) -> None:
        """오른쪽 클릭 메뉴 맨 위에 서식 항목들을 넣는다."""
        st = self.fmt_state()
        items = []

        def act(text, slot, keys="", checked=None):
            a = QAction(text + ("\t" + plat.key_label(keys) if keys else ""), menu)
            a.triggered.connect(slot)
            if checked is not None:
                a.setCheckable(True)
                a.setChecked(bool(checked))
            items.append(a)

        def sep():
            a = QAction(menu)
            a.setSeparator(True)
            items.append(a)

        kind = self.list_kind()
        act(tr("fmt.todo"), lambda: self.set_list("todo"), "Ctrl+Shift+L", kind in ("todo", "done"))
        act(tr("fmt.bullets"), lambda: self.set_list("bullet"), "", kind == "bullet")
        act(tr("fmt.numbers"), lambda: self.set_list("number"), "", kind == "number")
        sep()
        act(tr("act.bold"), self.toggle_bold, "Ctrl+B", st.fontWeight() > QFont.Normal)
        act(tr("fmt.italic"), self.toggle_italic, "Ctrl+I", st.fontItalic())
        act(tr("fmt.underline"), self.toggle_underline, "Ctrl+U", st.fontUnderline())
        act(tr("fmt.strike"), self.toggle_strike, "", st.fontStrikeOut())
        cm = QMenu(tr("fmt.color"), menu)
        cm.addAction(self._color_icon(None), tr("color.default"), lambda: self.set_text_color(None))
        for key, col in TEXT_COLORS:
            cm.addAction(self._color_icon(col), tr("color." + key), lambda col=col: self.set_text_color(col))
        hm = QMenu(tr("fmt.highlight"), menu)
        hm.addAction(self._color_icon(None), tr("color.none"), lambda: self.set_highlight(None))
        for key, col in MARK_COLORS:
            hm.addAction(self._color_icon(col), tr("color." + key), lambda col=col: self.set_highlight(col))
        items.append(cm.menuAction())
        items.append(hm.menuAction())
        act(tr("act.clear_fmt"), self.host.clear_format)
        sep()
        for a in items:
            menu.insertAction(before, a)

    def _save_image(self, img: QImage):
        fn, _ = QFileDialog.getSaveFileName(self, tr("ed.save_image_title"), "image.png", "PNG (*.png);;JPEG (*.jpg)")
        if fn:
            img.save(fn)


# ====================================================================== 텍스트 메모
class _LineArea(QWidget):
    def __init__(self, ed):
        super().__init__(ed)
        self.ed = ed

    def sizeHint(self):
        return QSize(self.ed.line_area_width(), 0)

    def paintEvent(self, e):
        self.ed.paint_lines(e)


class CodeHighlighter(QSyntaxHighlighter):
    """JSON·HTML·코드에 가벼운 색 구분 (내용을 바꾸지 않음)."""

    def __init__(self, doc, dark: bool):
        super().__init__(doc)
        pal = {
            "key": "#7cc4ff" if dark else "#0b5cad",
            "str": "#e6b673" if dark else "#a3410f",
            "num": "#b5e08a" if dark else "#2f7d1f",
            "kw": "#d79cff" if dark else "#8a2bb5",
            "tag": "#ff8f8f" if dark else "#b0182e",
            "attr": "#9fd6c8" if dark else "#1c7a6a",
            "cmt": "#8a8a8a",
        }

        def fmt(c, bold=False, italic=False):
            f = QTextCharFormat()
            f.setForeground(QColor(c))
            if bold:
                f.setFontWeight(QFont.Bold)
            f.setFontItalic(italic)
            return f
        R = QRegularExpression
        self.rules = [
            (R(r"</?[A-Za-z][\w:.-]*|/?>"), fmt(pal["tag"])),
            (R(r"\b[\w:-]+(?==)"), fmt(pal["attr"])),
            (R(r"\b(true|false|null|None|True|False)\b"), fmt(pal["kw"], bold=True)),
            (R(r"(?<![\w.])-?\d+(\.\d+)?([eE][+-]?\d+)?\b"), fmt(pal["num"])),
            (R(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'"), fmt(pal["str"])),
            (R(r"\"(?:[^\"\\]|\\.)*\"(?=\s*:)"), fmt(pal["key"])),
            (R(r"<!--.*?-->|(?<![:\"'\w])//[^\n]*$"), fmt(pal["cmt"], italic=True)),
        ]

    def highlightBlock(self, text):
        if len(text) > 4000:
            return  # 아주 긴 한 줄(압축된 JSON 등)은 색칠하지 않아 느려지지 않게
        for rx, f in self.rules:
            it = rx.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), f)


class CodeEdit(_CopyMixin, QPlainTextEdit):
    def __init__(self, host, parent=None):
        super().__init__(parent)
        self.host = host
        self.setObjectName("CodeEditor")
        self.setFont(mono_font(host.cfg["font_pt"]))
        self.document().setDocumentMargin(8)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self.lines = _LineArea(self)
        self.blockCountChanged.connect(self._update_margin)
        self.updateRequest.connect(self._update_area)
        self.cursorPositionChanged.connect(self._mark_line)
        self._update_margin()
        self.hl = None
        self.retheme()

    def retheme(self):
        dark = getattr(self.host, "t", {}).get("dark", self.palette().base().color().lightness() < 128)
        if self.hl is not None:
            self.hl.setDocument(None)
        self.hl = CodeHighlighter(self.document(), dark)
        self.lines.update()

    # 줄 번호
    def line_area_width(self) -> int:
        digits = max(3, len(str(max(1, self.blockCount()))))
        return 22 + self.fontMetrics().horizontalAdvance("9") * digits

    def _update_margin(self, *_):
        self.setViewportMargins(self.line_area_width(), 0, 0, 0)

    def _update_area(self, rect, dy):
        if dy:
            self.lines.scroll(0, dy)
        else:
            self.lines.update(0, rect.y(), self.lines.width(), rect.height())

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.lines.setGeometry(QRect(cr.left(), cr.top(), self.line_area_width(), cr.height()))

    def paint_lines(self, e):
        p = QPainter(self.lines)
        t = getattr(self.host, "t", None)
        p.fillRect(e.rect(), QColor(t["gutter"]) if t else self.palette().alternateBase().color())
        if t:
            p.setPen(QColor(t["border_subtle"]))
            p.drawLine(self.lines.width() - 1, e.rect().top(), self.lines.width() - 1, e.rect().bottom())
        cur = self.textCursor().blockNumber()
        p.setFont(self.font())
        block = self.firstVisibleBlock()
        num = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        h = round(self.blockBoundingRect(block).height()) if block.isValid() else self.fontMetrics().height()
        while block.isValid() and top <= e.rect().bottom():
            if block.isVisible():
                p.setPen(QColor(t["text"] if num == cur else t["muted"]) if t else self.palette().placeholderText().color())
                p.drawText(0, top, self.lines.width() - 8, h, Qt.AlignRight, str(num + 1))
            block = block.next()
            top += round(self.blockBoundingRect(block).height()) if block.isValid() else h
            num += 1

    def _mark_line(self):
        sel = QTextEdit.ExtraSelection()
        t = getattr(self.host, "t", None)
        c = QColor(t["accent"]) if t else self.palette().highlight().color()
        c.setAlpha(22 if t and t["dark"] else 14)
        sel.format.setBackground(c)
        sel.format.setProperty(QTextFormat.FullWidthSelection, True)
        sel.cursor = self.textCursor()
        sel.cursor.clearSelection()
        self.setExtraSelections([sel])

    # 붙여넣기·복사
    def canInsertFromMimeData(self, src):
        return src.hasText() or src.hasUrls() or src.hasImage()

    def insertFromMimeData(self, src: QMimeData):
        # 탐색기에서 끌어온 파일은 text()가 파일 경로라서 먼저 살핀다 (경로 글자가 들어가지 않게)
        if _dropped_images(src):
            self.host.status(tr("ed.no_image", key=plat.key_label("Ctrl+N")))  # 글 메모에는 그림을 못 넣음
        elif src.hasUrls() and all(u.isLocalFile() for u in src.urls()):
            for u in src.urls():
                if u.isLocalFile():
                    try:
                        self.insertPlainText(Path(u.toLocalFile()).read_text("utf-8", errors="replace"))
                    except OSError:
                        pass
        elif src.hasText():
            self.insertPlainText(src.text().replace("\r\n", "\n"))
        elif src.hasImage():
            self.host.status(tr("ed.no_image", key=plat.key_label("Ctrl+N")))

    def createMimeDataFromSelection(self):
        md = super().createMimeDataFromSelection()
        if self.host.cfg["clip_private"]:
            mark_private(md)
        return md

    def keyPressEvent(self, e):
        if self._copy_keys(e):
            return
        if e.key() in (Qt.Key_Return, Qt.Key_Enter) and not e.modifiers():
            line = self.textCursor().block().text()
            indent = line[:len(line) - len(line.lstrip(" \t"))]
            before = line[:self.textCursor().positionInBlock()].rstrip()
            if before.endswith(("{", "[", "(")):
                indent += "  " if "\t" not in indent else "\t"
            self.textCursor().insertText("\n" + indent)
            self.ensureCursorVisible()
            return
        if e.key() == Qt.Key_Backtab:
            self._unindent()
            return
        super().keyPressEvent(e)

    def _unindent(self):
        c = self.textCursor()
        c.movePosition(QTextCursor.StartOfBlock)
        line = c.block().text()
        n = 1 if line.startswith("\t") else min(4, len(line) - len(line.lstrip(" ")))
        if n:
            c.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n)
            c.removeSelectedText()

    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu(e.pos())
        line = self.cursorForPosition(e.pos()).block().text()
        val = line_value(line)
        menu.addSeparator()
        if val:
            short = val if len(val) <= 24 else val[:10] + "…" + val[-6:]
            menu.addAction(tr("ed.copy_value", v=short), lambda: self.host.copy_text(val, tr("ed.copied_value")))
        if line.strip():
            menu.addAction(tr("ed.copy_line"), lambda: self.host.copy_text(line.strip(), tr("ed.copied_line")))
        menu.addSeparator()
        menu.addAction(tr("act.json_pretty"), self.host.json_pretty)
        menu.addAction(tr("act.json_compact"), self.host.json_compact)
        menu.exec(e.globalPos())
