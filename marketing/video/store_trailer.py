"""Microsoft Store 트레일러 자료 만들기 (render_video.py로 본편을 먼저 만든 뒤).

python store_trailer.py
→ store_trailer/trailer_ko.mp4, trailer_en.mp4   본편과 같은 영상, moov를 앞으로 옮김(fast start, Store 권장)
   store_trailer/thumbnail_ko.png, thumbnail_en.png 1920×1080 PNG (영상 24초 장면, 트레일러마다 다른 그림)
   store_trailer/captions_{ko,en,ja,zh-Hans}.vtt    WebVTT 자막 (subtitles/*.srt에서 변환)

영상은 다시 인코딩하지 않는다(화질 그대로). 썸네일은 render_video.py stills로 뽑는다.
"""
from __future__ import annotations

import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "store_trailer"
CONTAINERS = {b"moov", b"trak", b"mdia", b"minf", b"stbl", b"edts", b"dinf", b"udta"}


def boxes(buf: bytes, start: int, end: int):
    i = start
    while i < end:
        size, typ = struct.unpack(">I4s", buf[i:i + 8])
        hdr = 8
        if size == 1:
            size = struct.unpack(">Q", buf[i + 8:i + 16])[0]
            hdr = 16
        elif size == 0:
            size = end - i
        yield i, size, typ, hdr
        i += size


def shift_chunk_offsets(moov: bytearray, delta: int) -> None:
    def walk(s, e):
        for i, size, typ, hdr in boxes(moov, s, e):
            if typ in CONTAINERS:
                walk(i + hdr, i + size)
            elif typ == b"stco":
                n = struct.unpack(">I", moov[i + 12:i + 16])[0]
                for k in range(n):
                    p = i + 16 + 4 * k
                    moov[p:p + 4] = struct.pack(">I", struct.unpack(">I", moov[p:p + 4])[0] + delta)
            elif typ == b"co64":
                n = struct.unpack(">I", moov[i + 12:i + 16])[0]
                for k in range(n):
                    p = i + 16 + 8 * k
                    moov[p:p + 8] = struct.pack(">Q", struct.unpack(">Q", moov[p:p + 8])[0] + delta)
    walk(0, len(moov))


def faststart(src: Path, dst: Path) -> None:
    buf = src.read_bytes()
    top = list(boxes(buf, 0, len(buf)))
    order = [t for _, _, t, _ in top]
    if order.index(b"moov") < order.index(b"mdat"):
        shutil.copy2(src, dst)
        return
    moov_i, moov_size = next((i, s) for i, s, t, _ in top if t == b"moov")
    moov = bytearray(buf[moov_i:moov_i + moov_size])
    shift_chunk_offsets(moov, moov_size)          # moov가 mdat 앞으로 오면 데이터가 그만큼 뒤로 밀린다
    out = bytearray()
    for i, s, t, _ in top:
        if t == b"moov":
            continue
        if t == b"mdat":
            out += moov
        out += buf[i:i + s]
    dst.write_bytes(bytes(out))


def srt_to_vtt(src: Path, dst: Path) -> None:
    text = src.read_text("utf-8-sig").replace("\r\n", "\n")
    text = re.sub(r"(\d\d:\d\d:\d\d),(\d\d\d)", r"\1.\2", text)
    dst.write_text("WEBVTT\n\n" + text.strip() + "\n", "utf-8")


def main() -> int:
    OUT.mkdir(exist_ok=True)
    for lang in ("ko", "en"):
        src = HERE / f"hushpad_promo_{lang}.mp4"
        if not src.is_file():
            print(f"없음: {src.name} (python render_video.py {lang})", file=sys.stderr)
            return 1
        faststart(src, OUT / f"trailer_{lang}.mp4")
        subprocess.run([sys.executable, str(HERE / "render_video.py"), "stills", lang, "24"], check=True,
                       capture_output=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        shutil.copy2(HERE / "qa" / f"still_main_{lang}_024.0.png", OUT / f"thumbnail_{lang}.png")
    for lang in ("ko", "en", "ja", "zh-Hans"):
        srt_to_vtt(HERE / "subtitles" / f"hushpad_promo.{lang}.srt", OUT / f"captions_{lang}.vtt")
    for p in sorted(OUT.iterdir()):
        print(f"{p.name:24} {p.stat().st_size / 1e6:6.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
