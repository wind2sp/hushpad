"""만든 MP4를 Qt로 열어 길이·해상도·fps·코덱·비트레이트·소리 트랙을 확인하고, 몇 시각의 프레임을 qa\\에 PNG로 뽑는다.
소리가 있으면 MP4의 소리를 풀어서 music/*.wav와 맞대어 어긋남(ms)과 음량을 잰다.

python verify.py                     → 네 파일 모두 (기본 시각)
python verify.py hushpad_promo_ko.mp4 3 20 …
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_LOGGING_RULES", "qt.multimedia.ffmpeg*=true")  # FFmpeg 스트림 정보(코덱·프로필) 출력

import numpy as np                                                       # noqa: E402
from PySide6.QtCore import QUrl, QEventLoop, QTimer                      # noqa: E402
from PySide6.QtGui import QGuiApplication                                # noqa: E402
from PySide6.QtMultimedia import (QMediaPlayer, QVideoSink, QMediaMetaData, QAudioDecoder,  # noqa: E402
                                  QAudioFormat)

HERE = Path(__file__).resolve().parent
DEFAULT = {
    "hushpad_promo_ko.mp4": [2.0, 4.4, 6.3, 11.0, 22.0, 33.0, 40.0, 49.0, 57.0, 67.0, 76.0],
    "hushpad_promo_en.mp4": [2.0, 4.4, 11.0, 14.0, 24.0, 33.0, 41.0, 49.0, 54.0, 63.0, 67.0, 76.0],
    "shorts_ko.mp4": [2.5, 12.0, 18.5, 25.0, 29.0],
    "shorts_en.mp4": [2.5, 10.0, 12.0, 18.5, 25.0, 29.0],
}
MUSIC = {"shorts": HERE / "music" / "hushpad_bgm_shorts.wav", "main": HERE / "music" / "hushpad_bgm_main.wav"}


def wait(cond, timeout=8.0):
    loop = QEventLoop()
    end = time.time() + timeout
    while not cond() and time.time() < end:
        QTimer.singleShot(15, loop.quit)
        loop.exec()
    return cond()


def decode_audio(path):
    """MP4의 소리 → float32 (n, 2) @48k."""
    dec = QAudioDecoder()
    fmt = QAudioFormat()
    fmt.setSampleRate(48000)
    fmt.setChannelCount(2)
    fmt.setSampleFormat(QAudioFormat.Int16)
    dec.setAudioFormat(fmt)
    dec.setSource(QUrl.fromLocalFile(str(path)))
    chunks = []
    st = {"done": False}
    dec.bufferReady.connect(lambda: chunks.append(bytes(dec.read().constData())))
    dec.finished.connect(lambda: st.__setitem__("done", True))
    dec.error.connect(lambda e: st.__setitem__("done", True))
    dec.start()
    wait(lambda: st["done"], 60)
    a = np.frombuffer(b"".join(chunks), "<i2").reshape(-1, 2).astype(np.float32) / 32768
    return a


def check_audio(path):
    import make_music as mm
    kind = "shorts" if path.name.startswith("shorts") else "main"
    a = decode_audio(path)
    if not len(a):
        print("  audio: 풀어낸 소리 없음")
        return
    src = mm.read_wav(MUSIC[kind]).astype(np.float32)
    # 앞 12초 envelope(10 ms)로 어긋남 추정
    def env(x):
        h = 480
        n = min(len(x), 48000 * 12) // h
        return np.sqrt((x[: n * h].mean(1).reshape(n, h) ** 2).mean(1))
    ea, es = env(a), env(src)
    n = min(len(ea), len(es))
    ea, es = ea[:n] - ea[:n].mean(), es[:n] - es[:n].mean()
    lags = range(-30, 31)
    best = max(lags, key=lambda L: float(np.dot(np.roll(ea, -L), es)))
    print(f"  audio: {len(a) / 48000:.2f}s decoded, offset vs WAV ≈ {best * 10:+d} ms, "
          f"{mm.lufs(a.astype(np.float64)):.1f} LUFS, peak {20 * np.log10(np.abs(a).max() + 1e-9):.1f} dBFS", flush=True)


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
    codec = md.stringValue(QMediaMetaData.VideoCodec)
    size = path.stat().st_size
    print(f"{name}: {dur:.2f}s  {res}  fps={fps}  codec={codec}  {size / 1e6:.1f}MB  "
          f"{size * 8 / dur / 1e6:.2f} Mbps (전체)  audio={'yes' if player.hasAudio() else 'NO'}", flush=True)
    q = HERE / "qa"
    q.mkdir(exist_ok=True)
    player.setAudioOutput(None)
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
    if player.hasAudio():
        check_audio(path)


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
