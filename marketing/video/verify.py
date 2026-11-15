"""만든 MP4를 Qt로 열어 길이·해상도·fps를 확인하고, 몇 시각의 프레임을 qa\\에 PNG로 뽑는다.

python verify.py                     → 세 파일 모두 (기본 시각)
python verify.py hushpad_promo_ko.mp4 3 20 …
"""
import sys
import time
from pathlib import Path

from PySide6.QtCore import QUrl, QEventLoop, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtMultimedia import QMediaPlayer, QVideoSink, QMediaMetaData

HERE = Path(__file__).resolve().parent
DEFAULT = {
    "hushpad_promo_ko.mp4": [2.0, 4.4, 6.3, 11.0, 22.0, 33.0, 40.0, 49.0, 57.0, 67.0, 76.0],
    "hushpad_promo_en.mp4": [2.0, 14.0, 24.0, 41.0, 54.0, 63.0, 76.0],
    "shorts_ko.mp4": [2.5, 12.0, 18.5, 25.0, 29.0],
}


def wait(cond, timeout=8.0):
    loop = QEventLoop()
    end = time.time() + timeout
    while not cond() and time.time() < end:
        QTimer.singleShot(15, loop.quit)
        loop.exec()
    return cond()


def probe(app, name, times):
    path = HERE / name
    player = QMediaPlayer()
    sink = QVideoSink()
    player.setVideoSink(sink)
    got = {}
    sink.videoFrameChanged.connect(lambda f: got.__setitem__("f", f))
    player.setSource(QUrl.fromLocalFile(str(path)))
    wait(lambda: player.mediaStatus() in (QMediaPlayer.LoadedMedia, QMediaPlayer.InvalidMedia))
    md = player.metaData()
    dur = player.duration() / 1000
    res = md.value(QMediaMetaData.Resolution)
    fps = md.value(QMediaMetaData.VideoFrameRate)
    try:
        codec = md.stringValue(QMediaMetaData.VideoCodec)
    except Exception:
        codec = "?"
    size = path.stat().st_size / 1e6
    print(f"{name}: {dur:.2f}s  {res}  fps={fps}  codec={codec}  {size:.1f}MB", flush=True)
    q = HERE / "qa"
    q.mkdir(exist_ok=True)
    player.play()
    wait(lambda: "f" in got, 5)
    player.pause()
    for t in times:
        got.clear()
        player.setPosition(int(t * 1000))
        ok = wait(lambda: "f" in got and got["f"].isValid() and got["f"].startTime() >= (t - 0.2) * 1e6, 6)
        if not ok and "f" in got:
            ok = True
        if ok:
            img = got["f"].toImage()
            out = q / f"{Path(name).stem}_{t:05.1f}s.png"
            img.save(str(out))
            print(f"  frame {t:5.1f}s → {out.name} ({img.width()}x{img.height()})", flush=True)
        else:
            print(f"  frame {t:5.1f}s: 못 받음", flush=True)
    player.stop()


def main():
    app = QGuiApplication(sys.argv[:1])
    args = sys.argv[1:]
    if args:
        probe(app, args[0], [float(x) for x in args[1:]] or [1.0])
    else:
        for name, ts in DEFAULT.items():
            if (HERE / name).exists():
                probe(app, name, ts)


if __name__ == "__main__":
    main()
