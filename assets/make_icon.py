"""Hushpad 앱 아이콘 만들기.

디자인 시안은 icon_concepts.py에 있다 (A 서리유리 메모 · B 흩어지는 메모지 · C H 모양 메모지).
CHOSEN을 바꾸면 다른 시안으로 바뀐다. 기본: B — 한쪽 끝이 조각나 사라지는 메모지 = 캡처에 안 보이는 조용한 메모장.
1024px 그림을 줄이고, 40px 이하는 시안마다 따로 그린 단순한 그림을 쓴다.
결과: app.ico(16~256), app.png(256), app_small.png(32), app_1024.png, icon_preview.png(밝은·어두운 배경)
"""
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import icon_concepts as ic  # noqa: E402

CHOSEN = "b"


def main():
    key, name, desc, fn = next(c for c in ic.CONCEPTS if c[0] == CHOSEN)
    big, frames = ic.render(fn)
    ic.write_ico(HERE / "app.ico", [frames[n] for n in ic.SIZES])
    frames[256].save(HERE / "app.png")
    frames[32].save(HERE / "app_small.png")
    big.save(HERE / "app_1024.png")
    pad = 20
    w = sum(ic.SIZES) + pad * (len(ic.SIZES) + 1)
    h = 256 + pad * 2
    prev = Image.new("RGBA", (w, h * 2), (243, 243, 243, 255))
    prev.paste((32, 32, 32, 255), (0, h, w, h * 2))
    x = pad
    for n in ic.SIZES:
        for row in (0, 1):
            prev.alpha_composite(frames[n], (x, row * h + pad + (256 - n) // 2))
        x += n + pad
    prev.convert("RGB").save(HERE / "icon_preview.png")
    print("ok", name, HERE / "app.ico")


if __name__ == "__main__":
    main()
