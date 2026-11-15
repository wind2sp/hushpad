"""스크린샷·짧은 화면 녹화.

Hushpad 창, 영역 테두리, 녹화 버튼 막대는 모두 '캡처 제외'(Windows SetWindowDisplayAffinity /
macOS NSWindow.sharingType) 상태라 화면에는 보이지만 찍히는 그림·동영상에는 들어가지 않는다.

macOS는 '화면 기록' 권한이 있어야 다른 앱 창이 찍힌다. 권한이 없으면 배경 화면만 찍히므로
screen_capture_ok()로 미리 묻고, 찍은 그림이 비었는지(looks_blank)도 살핀다.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from PySide6.QtCore import QBuffer, QByteArray, QElapsedTimer, QIODevice, QObject, QPoint, QPointF, QRect, Qt, \
    QTimer, QUrl, Signal
from PySide6.QtGui import QColor, QCursor, QGuiApplication, QImage, QPainter, QPainterPath, QPen, QPixmap, \
    QPolygonF
from PySide6.QtWidgets import QDialog, QFileDialog, QHBoxLayout, QLabel, QPushButton, QSlider, QVBoxLayout, QWidget

from . import plat
from .common import LOCAL_DIR, exclude_from_capture
from .i18n import tr


def screen_under_cursor():
    return QGuiApplication.screenAt(QCursor.pos()) or QGuiApplication.primaryScreen()


def grab_screen(screen) -> QPixmap:
    return screen.grabWindow(0)


def screen_capture_ok() -> bool:
    """화면을 찍을 수 있는지 (macOS: 화면 기록 권한). 없으면 권한 창을 한 번 띄운다."""
    if plat.screen_capture_allowed():
        return True
    plat.request_screen_capture()
    return False


def looks_blank(pix: QPixmap) -> bool:
    """찍은 그림이 비었거나 한 가지 색뿐인지 (권한이 없을 때 생기는 검은·빈 화면)."""
    if pix.isNull() or pix.width() < 2 or pix.height() < 2:
        return True
    img = pix.toImage().scaled(32, 32)
    first = img.pixel(0, 0)
    return all(img.pixel(x, y) == first for x in range(img.width()) for y in range(img.height()))


# ====================================================================== 영역 고르기
class RegionOverlay(QWidget):
    """멈춘 화면 위에서 끌어서 영역을 고른다. Enter = 화면 전체, Esc/오른쪽 클릭 = 취소."""
    chosen = Signal(QRect)
    cancelled = Signal()

    def __init__(self, screen, pix: QPixmap, purpose: str):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.screen_, self.pix, self.purpose = screen, pix, purpose
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CrossCursor)
        self.origin = None
        self.rect_ = QRect()
        self.setMouseTracking(True)

    def start(self):
        self.show()
        self.windowHandle().setScreen(self.screen_)
        self.setGeometry(self.screen_.geometry())
        self.activateWindow()
        self.raise_()

    def paintEvent(self, e):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.pix)
        shade = QPainterPath()
        shade.addRect(self.rect())
        r = self.rect_.normalized()
        if not r.isEmpty():
            hole = QPainterPath()
            hole.addRect(r)
            shade = shade.subtracted(hole)
        p.fillPath(shade, QColor(0, 0, 0, 110))
        accent = QColor("#ff4757") if self.purpose == "video" else QColor("#2ec4b6")
        if not r.isEmpty():
            p.setPen(QPen(accent, 2))
            p.drawRect(r.adjusted(0, 0, -1, -1))
            dpr = self.pix.devicePixelRatio()
            label = f"{round(r.width() * dpr)} × {round(r.height() * dpr)}"
            self._tag(p, r.left(), r.top() - 26 if r.top() > 30 else r.bottom() + 6, label, accent)
        hint = tr("cap.hint_video") if self.purpose == "video" else tr("cap.hint_image")
        hw = p.fontMetrics().horizontalAdvance(hint) + 16
        self._tag(p, (self.width() - hw) // 2, 18, hint, QColor(30, 30, 30))

    def _tag(self, p, x, y, text, bg):
        fm = p.fontMetrics()
        w = fm.horizontalAdvance(text) + 16
        p.fillRect(QRect(x, y, w, 22), bg)
        p.setPen(Qt.white)
        p.drawText(QRect(x, y, w, 22), Qt.AlignCenter, text)

    def mousePressEvent(self, e):
        if e.button() == Qt.RightButton:
            self._cancel()
            return
        self.origin = e.position().toPoint()
        self.rect_ = QRect(self.origin, self.origin)
        self.update()

    def mouseMoveEvent(self, e):
        if self.origin is not None:
            self.rect_ = QRect(self.origin, e.position().toPoint())
            self.update()

    def mouseReleaseEvent(self, e):
        if self.origin is None:
            return
        r = self.rect_.normalized()
        self.origin = None
        if r.width() < 8 or r.height() < 8:
            self.rect_ = QRect()
            self.update()
            return
        self._done(r)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self._cancel()
        elif e.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._done(self.rect())

    def _done(self, r):
        self.hide()
        self.chosen.emit(r)
        self.close()

    def _cancel(self):
        self.hide()
        self.cancelled.emit()
        self.close()


def crop(pix: QPixmap, r: QRect) -> QImage:
    dpr = pix.devicePixelRatio()
    img = pix.toImage().copy(round(r.x() * dpr), round(r.y() * dpr), round(r.width() * dpr),
                             round(r.height() * dpr))
    img.setDevicePixelRatio(dpr)
    return img


# ====================================================================== 녹화
class _Frame(QWidget):
    """녹화 영역 바깥에 그리는 빨간 테두리 (마우스 통과, 캡처 제외)."""

    def __init__(self, global_rect: QRect):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool |
                         Qt.WindowTransparentForInput)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setGeometry(global_rect.adjusted(-3, -3, 3, 3))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setPen(QPen(QColor("#ff4757"), 3, Qt.DashLine))
        p.drawRect(self.rect().adjusted(1, 1, -2, -2))


class RecordBar(QWidget):
    def __init__(self, rec: "Recorder"):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.rec = rec
        self.setStyleSheet("""
            QWidget#bar { background:#1f2330; border-radius:8px; }
            QLabel { color:#ffffff; font-weight:600; padding:0 6px; }
            QPushButton { color:#ffffff; background:#343a4d; border:none; border-radius:5px; padding:5px 10px; }
            QPushButton:hover { background:#4a5270; }
            QPushButton#stop { background:#e0384a; }
        """)
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        bar = QWidget(objectName="bar")
        outer.addWidget(bar)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 6, 8, 6)
        self.lbl = QLabel("● 00:00")
        self.pause_btn = QPushButton(tr("rec.pause"))
        stop = QPushButton(tr("rec.save"), objectName="stop")
        cancel = QPushButton(tr("rec.cancel"))
        for w in (self.lbl, self.pause_btn, stop, cancel):
            lay.addWidget(w)
        self.pause_btn.clicked.connect(self._pause)
        stop.clicked.connect(rec.stop)
        cancel.clicked.connect(rec.cancel)
        self._drag = None

    def _pause(self):
        self.rec.toggle_pause()
        self.pause_btn.setText(tr("rec.resume") if self.rec.paused else tr("rec.pause"))

    def tick(self, sec: float, paused: bool):
        m, s = divmod(int(sec), 60)
        self.lbl.setText(f"{'❚❚' if paused else '●'} {m:02d}:{s:02d} / " + tr("rec.max", n=self.rec.max_sec // 60))

    def mousePressEvent(self, e):
        self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e):
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, e):
        self._drag = None


class Recorder(QObject):
    """화면 일부를 일정 간격으로 찍어 MP4(H.264)로 만든다. finished(mp4 bytes, 첫 화면, 길이초)"""
    finished = Signal(bytes, QImage, float)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, screen, rect: QRect, fps: int = 12, max_sec: int = 180):
        super().__init__()
        from PySide6.QtMultimedia import QMediaCaptureSession, QMediaFormat, QMediaRecorder, QVideoFrameInput
        self.screen_, self.rect = screen, rect
        self.fps, self.max_sec = max(2, min(30, fps)), max_sec
        dpr = screen.devicePixelRatio()
        self.out_w = max(16, int(rect.width() * dpr) // 2 * 2)   # H.264는 짝수 크기
        self.out_h = max(16, int(rect.height() * dpr) // 2 * 2)
        if self.out_w > 1920:  # 너무 크면 줄임
            self.out_h = int(self.out_h * 1920 / self.out_w) // 2 * 2
            self.out_w = 1920
        tmpdir = LOCAL_DIR / "tmp"
        tmpdir.mkdir(parents=True, exist_ok=True)
        self.tmp = tmpdir / f"rec-{os.getpid()}-{int(time.time())}.mp4"
        self.session = QMediaCaptureSession()
        self.input = QVideoFrameInput()
        self.session.setVideoFrameInput(self.input)
        self.recorder = QMediaRecorder()
        self.session.setRecorder(self.recorder)
        fmt = QMediaFormat(QMediaFormat.MPEG4)
        fmt.setVideoCodec(QMediaFormat.VideoCodec.H264)
        self.recorder.setMediaFormat(fmt)
        self.recorder.setQuality(QMediaRecorder.HighQuality)
        self.recorder.setVideoFrameRate(self.fps)
        self.recorder.setVideoResolution(self.out_w, self.out_h)
        self.recorder.setOutputLocation(QUrl.fromLocalFile(str(self.tmp)))
        self.recorder.errorOccurred.connect(lambda err, msg: self._fail(msg or str(err)))
        self.recorder.recorderStateChanged.connect(self._state)
        self.timer = QTimer(self)
        self.timer.setTimerType(Qt.PreciseTimer)
        self.timer.timeout.connect(self._grab)
        self.clock = QElapsedTimer()
        self.paused = False
        self.pause_total = 0
        self.pause_start = 0
        self.thumb = QImage()
        self.frames = 0
        self._cancel = False
        self._done = False
        g = rect.translated(screen.geometry().topLeft())
        self.frame_win = _Frame(g)
        self.bar = RecordBar(self)

    def start(self):
        g = self.rect.translated(self.screen_.geometry().topLeft())
        for w in (self.frame_win, self.bar):
            w.show()
            exclude_from_capture(w)
        sg = self.screen_.availableGeometry()
        self.bar.adjustSize()
        x = min(max(sg.left(), g.right() - self.bar.width()), sg.right() - self.bar.width())
        bh = self.bar.height()
        if g.bottom() + 8 + bh <= sg.bottom():
            y = g.bottom() + 8                      # 영역 아래
        elif g.top() - 8 - bh >= sg.top():
            y = g.top() - 8 - bh                    # 영역 위
        else:
            y = g.bottom() - bh - 8                 # 화면 전체 — 영역 안쪽 (캡처 제외라 찍히지 않음)
        self.bar.move(x, y)
        self.recorder.record()
        self.clock.start()
        self.timer.start(int(1000 / self.fps))

    def _elapsed_ms(self) -> int:
        now = self.clock.elapsed()
        pause = self.pause_total + (now - self.pause_start if self.paused else 0)
        return now - pause

    def toggle_pause(self):
        if self.paused:
            self.pause_total += self.clock.elapsed() - self.pause_start
            self.paused = False
        else:
            self.pause_start = self.clock.elapsed()
            self.paused = True

    def _grab(self):
        t = self._elapsed_ms()
        self.bar.tick(t / 1000, self.paused)
        if self.paused:
            return
        if t / 1000 >= self.max_sec:
            self.stop()
            return
        from PySide6.QtMultimedia import QVideoFrame
        r = self.rect
        pix = self.screen_.grabWindow(0, r.x(), r.y(), r.width(), r.height())
        img = pix.toImage().convertToFormat(QImage.Format_RGB32)
        # 마우스 포인터 그리기 (스크린샷 API에는 포인터가 없다)
        local = QCursor.pos() - self.screen_.geometry().topLeft() - r.topLeft()
        if 0 <= local.x() < r.width() and 0 <= local.y() < r.height():
            dpr = img.width() / max(1, r.width())
            p = QPainter(img)
            p.setRenderHint(QPainter.Antialiasing)
            x, y, s = local.x() * dpr, local.y() * dpr, 1.3 * dpr
            arrow = QPolygonF([QPointF(x, y), QPointF(x, y + 17 * s), QPointF(x + 4.5 * s, y + 13 * s),
                               QPointF(x + 8 * s, y + 20 * s), QPointF(x + 10.5 * s, y + 19 * s),
                               QPointF(x + 7 * s, y + 12 * s), QPointF(x + 12.5 * s, y + 12 * s)])
            p.setPen(QPen(Qt.white, 1.5 * s))
            p.setBrush(Qt.black)
            p.drawPolygon(arrow)
            p.end()
        if img.width() != self.out_w or img.height() != self.out_h:
            img = img.scaled(self.out_w, self.out_h, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        if self.thumb.isNull():
            self.thumb = img.copy()
        f = QVideoFrame(img)
        f.setStartTime(t * 1000)
        f.setEndTime((t + 1000 // self.fps) * 1000)
        if self.input.sendVideoFrame(f):
            self.frames += 1

    def stop(self):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self._close_ui()
        self.recorder.stop()

    def cancel(self):
        self._cancel = True
        self.stop()

    def _close_ui(self):
        self.frame_win.close()
        self.bar.close()

    def _state(self, st):
        from PySide6.QtMultimedia import QMediaRecorder
        if st != QMediaRecorder.StoppedState or not self._done:
            return
        QTimer.singleShot(200, self._finish)

    def _finish(self):
        data = b""
        try:
            if self.tmp.exists():
                data = self.tmp.read_bytes()
        finally:
            try:
                self.tmp.unlink()
            except OSError:
                pass
        if self._cancel:
            self.cancelled.emit()
        elif not data or self.frames == 0:
            self.failed.emit(tr("rec.nothing"))
        else:
            self.finished.emit(data, self.thumb, self._elapsed_ms() / 1000)
        self.deleteLater()

    def _fail(self, msg):
        if self._done:
            return
        self._done = True
        self.timer.stop()
        self._close_ui()
        try:
            self.tmp.unlink()
        except OSError:
            pass
        self.failed.emit(msg)


def video_thumbnail(img: QImage, seconds: float) -> QImage:
    """첫 화면 위에 재생 표시와 길이를 그린 미리보기."""
    w = min(640, img.width())
    th = img.scaledToWidth(w, Qt.SmoothTransformation).convertToFormat(QImage.Format_ARGB32)
    p = QPainter(th)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(th.rect(), QColor(0, 0, 0, 60))
    c = QPointF(th.width() / 2, th.height() / 2)
    r = max(18.0, min(th.width(), th.height()) * 0.12)
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(0, 0, 0, 150))
    p.drawEllipse(c, r, r)
    p.setBrush(Qt.white)
    p.drawPolygon(QPolygonF([QPointF(c.x() - r * 0.35, c.y() - r * 0.5), QPointF(c.x() - r * 0.35, c.y() + r * 0.5),
                             QPointF(c.x() + r * 0.55, c.y())]))
    m, s = divmod(int(round(seconds)), 60)
    label = tr("vid.thumb", time=f"{m}:{s:02d}")
    f = p.font()
    f.setPointSize(10)
    f.setBold(True)
    p.setFont(f)
    tw = p.fontMetrics().horizontalAdvance(label) + 14
    p.setBrush(QColor(0, 0, 0, 170))
    p.drawRoundedRect(8, th.height() - 30, tw, 22, 4, 4)
    p.setPen(Qt.white)
    p.drawText(QRect(8, th.height() - 30, tw, 22), Qt.AlignCenter, label)
    p.end()
    return th


# ====================================================================== 재생
class VideoDialog(QDialog):
    """암호화된 동영상을 메모리에서 바로 재생 (복호화한 파일을 디스크에 남기지 않음)."""

    def __init__(self, parent, data: bytes, title: str, on_export):
        super().__init__(parent)
        from PySide6.QtMultimedia import QMediaPlayer
        from PySide6.QtMultimediaWidgets import QVideoWidget
        self.setWindowTitle(title)
        self.resize(900, 600)
        self.ba = QByteArray(data)
        self.buf = QBuffer(self.ba, self)
        self.buf.open(QIODevice.ReadOnly)
        self.player = QMediaPlayer(self)
        self.view = QVideoWidget(self)
        self.player.setVideoOutput(self.view)
        self.player.setSourceDevice(self.buf, QUrl("clip.mp4"))
        lay = QVBoxLayout(self)
        lay.addWidget(self.view, 1)
        row = QHBoxLayout()
        self.play_btn = QPushButton("⏸")
        self.play_btn.setFixedWidth(44)
        self.slider = QSlider(Qt.Horizontal)
        self.time = QLabel("0:00 / 0:00")
        save = QPushButton(tr("vid.save_file"))
        row.addWidget(self.play_btn)
        row.addWidget(self.slider, 1)
        row.addWidget(self.time)
        row.addWidget(save)
        lay.addLayout(row)
        self.play_btn.clicked.connect(self._toggle)
        save.clicked.connect(on_export)
        self.player.durationChanged.connect(lambda d: self.slider.setRange(0, d))
        self.player.positionChanged.connect(self._pos)
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.playbackStateChanged.connect(
            lambda s: self.play_btn.setText("⏸" if s == QMediaPlayer.PlayingState else "▶"))
        self.player.play()

    def _toggle(self):
        from PySide6.QtMultimedia import QMediaPlayer
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            if self.player.position() >= self.player.duration() > 0:
                self.player.setPosition(0)
            self.player.play()

    def _pos(self, ms):
        if not self.slider.isSliderDown():
            self.slider.setValue(ms)
        d = self.player.duration()
        self.time.setText(f"{ms // 60000}:{ms // 1000 % 60:02d} / {d // 60000}:{d // 1000 % 60:02d}")

    def closeEvent(self, e):
        self.player.stop()
        super().closeEvent(e)
