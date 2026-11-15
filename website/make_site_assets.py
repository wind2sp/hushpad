"""홈페이지용 그림 만들기: 앱 아이콘(../assets)에서 favicon·아이콘·공유 미리보기(og-image) 생성.
실행: python website/make_site_assets.py   (앱 아이콘을 바꾼 뒤 다시 실행)"""
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = Path(__file__).resolve().parent
APP = HERE.parent / "assets"
IMG = HERE / "assets" / "img"


def font(size, bold=False):
    for f in (["C:/Windows/Fonts/malgunbd.ttf"] if bold else []) + ["C:/Windows/Fonts/malgun.ttf"]:
        try:
            return ImageFont.truetype(f, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    IMG.mkdir(parents=True, exist_ok=True)
    big = Image.open(APP / "app_1024.png").convert("RGBA")
    shutil.copy2(APP / "app.ico", HERE / "favicon.ico")
    Image.open(APP / "app_small.png").save(HERE / "favicon-32.png")
    for n in (64, 256, 512):
        big.resize((n, n), Image.LANCZOS).save(IMG / f"icon-{n}.png")
    big.resize((180, 180), Image.LANCZOS).save(HERE / "apple-touch-icon.png")

    # 공유 미리보기 1200×630
    W, H = 1200, 630
    og = Image.new("RGB", (W, H), (28, 26, 31))
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    g.ellipse([-200, -260, 700, 560], fill=(122, 60, 147, 150))
    g.ellipse([700, 260, 1400, 900], fill=(224, 112, 63, 90))
    og.paste(Image.alpha_composite(Image.new("RGBA", (W, H), (28, 26, 31, 255)),
                                   glow.filter(ImageFilter.GaussianBlur(120))).convert("RGB"))
    ic = big.resize((260, 260), Image.LANCZOS)
    og.paste(ic, (110, 185), ic)
    d = ImageDraw.Draw(og)
    d.text((430, 190), "Hushpad", font=font(92, True), fill=(238, 234, 242))
    d.text((434, 310), "조용한 비밀 메모장", font=font(44, True), fill=(255, 179, 138))
    d.text((436, 388), "자동 저장 · 모든 메모 암호화 · 캡처에 보이지 않는 창", font=font(28), fill=(185, 178, 194))
    og.save(IMG / "og-image.png", optimize=True)
    print("ok")


if __name__ == "__main__":
    main()
