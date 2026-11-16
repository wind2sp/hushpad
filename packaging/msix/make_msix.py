"""Microsoft Store용 MSIX 만들기 (Windows 전용).

먼저:   python build.py                 → dist\\Hushpad\\ (zip 빌드와 같은 앱 폴더)
그다음: python packaging\\msix\\make_msix.py [--name ... --publisher ... --publisher-display-name ...]
결과:   dist\\Hushpad-<버전>.msix       (서명하지 않음. Store에 올리면 Microsoft가 서명한다)

- 패키지 이름·게시자는 store_identity.json(또는 명령줄)에서 가져온다. 값은 Partner Center › 제품 관리 › 제품 ID.
- 버전은 hushpad_app.__version__ + ".0" (Store는 네 자리, 마지막은 0이어야 함).
- 아이콘(Assets\\*.png)은 assets/icon_concepts.py의 그림으로 만든다. 40px 이하는 단순한 작은 그림.
- 필요: Windows 10/11 SDK의 makeappx.exe·makepri.exe (C:\\Program Files (x86)\\Windows Kits\\10\\bin\\<버전>\\x64).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)   # 콘솔 창을 띄우지 않는다
APP_DIR = ROOT / "dist" / "Hushpad"
WORK = ROOT / "build" / "msix"
LAYOUT = WORK / "layout"
PRI_STAGE = WORK / "pri"
LEGAL = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")
MAX_TESTED = "10.0.26100.0"
SCALES = (100, 125, 150, 200, 400)
TARGET_SIZES = (16, 24, 32, 48, 256)

# 시작 메뉴·설정에 보이는 이름과 설명 (언어별)
STRINGS = {
    "ko-KR": ("Hushpad", "암호화되는 조용한 메모장"),
    "en-US": ("Hushpad", "A quiet notepad that encrypts every note"),
    "ja-JP": ("Hushpad", "すべてのメモを暗号化する静かなメモ帳"),
    "zh-CN": ("Hushpad", "加密每一条笔记的安静记事本"),
}


def fail(msg: str) -> None:
    print("make_msix: " + msg, file=sys.stderr)
    sys.exit(1)


def run(cmd: list[str], what: str) -> None:
    r = subprocess.run(cmd, capture_output=True, creationflags=NOWIN)
    if r.returncode != 0:
        def text(b: bytes) -> str:      # makepri는 UTF-16, makeappx는 콘솔 코드 페이지로 쓴다
            if b.count(b"\0") > len(b) // 4:
                return b.decode("utf-16-le", "replace")
            return b.decode("mbcs" if sys.platform == "win32" else "utf-8", "replace")
        print(text(r.stdout)[-6000:], text(r.stderr)[-3000:], sep="\n", file=sys.stderr)
        fail(f"{what} failed (exit {r.returncode})")


# ------------------------------------------------------------------ SDK 도구
def sdk_tool(name: str) -> Path:
    base = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"

    def ver(p: Path):
        return tuple(int(x) for x in re.findall(r"\d+", p.parent.parent.name))
    found = sorted(base.glob(rf"10.*\x64\{name}"), key=ver, reverse=True)
    if not found:
        fail(f"{name} not found under {base}\\<version>\\x64.\n"
             "  Install the Windows 10/11 SDK (Visual Studio Installer › Individual components › Windows SDK,\n"
             "  or https://developer.microsoft.com/windows/downloads/windows-sdk/) and run again.")
    return found[0]


# ------------------------------------------------------------------ 식별 정보
def identity(args) -> dict:
    ident = json.loads((HERE / "store_identity.json").read_text("utf-8"))
    for key, val in (("Name", args.name), ("Publisher", args.publisher),
                     ("PublisherDisplayName", args.publisher_display_name)):
        if val:
            ident[key] = val
    if not re.fullmatch(r"[-.A-Za-z0-9]{3,50}", ident["Name"]):
        fail(f"Identity Name {ident['Name']!r}: 3–50 letters, digits, '-' or '.'")
    if not ident["Publisher"].startswith("CN="):
        fail(f"Publisher {ident['Publisher']!r} must be a distinguished name such as CN=...")
    return ident


def package_version() -> str:
    sys.path.insert(0, str(ROOT))
    from hushpad_app import __version__
    nums = [int(x) for x in __version__.split(".")][:3]
    nums += [0] * (3 - len(nums))
    return ".".join(str(n) for n in nums) + ".0"


# ------------------------------------------------------------------ 아이콘
def icon_painter():
    sys.path.insert(0, str(ROOT / "assets"))
    import icon_concepts as ic
    import make_icon
    fn = next(c[3] for c in ic.CONCEPTS if c[0] == make_icon.CHOSEN)
    big = Image.open(ROOT / "assets" / "app_1024.png").convert("RGBA")
    cache: dict[int, Image.Image] = {}

    def icon(n: int) -> Image.Image:
        if n not in cache:
            if n <= ic.SMALL_MAX:     # 작은 크기는 상징만 굵게 남긴 따로 그린 그림
                cache[n] = fn(n * ic.SS_SMALL, True).resize((n, n), Image.LANCZOS)
            else:
                cache[n] = big.resize((n, n), Image.LANCZOS)
        return cache[n]
    return icon


def on_canvas(icon, w: int, h: int, frac: float) -> Image.Image:
    """투명한 w×h 바탕 가운데에 높이(짧은 변)의 frac만큼 아이콘을 놓는다."""
    n = max(1, round(min(w, h) * frac))
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas.alpha_composite(icon(n), ((w - n) // 2, (h - n) // 2))
    return canvas


def make_assets(dest: Path) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    icon = icon_painter()
    count = 0

    def save(img: Image.Image, name: str):
        nonlocal count
        img.save(dest / name, optimize=True)
        count += 1
    for s in SCALES:
        k = s / 100
        q = f".scale-{s}.png"
        save(icon(round(44 * k)), "Square44x44Logo" + q)                       # 시작 메뉴 목록·작업 표시줄
        save(on_canvas(icon, round(150 * k), round(150 * k), 0.66), "Square150x150Logo" + q)   # 중간 타일
        save(on_canvas(icon, round(310 * k), round(150 * k), 0.66), "Wide310x150Logo" + q)     # 넓은 타일
        save(icon(round(50 * k)), "StoreLogo" + q)                             # 패키지 로고
        save(on_canvas(icon, round(620 * k), round(300 * k), 0.5), "SplashScreen" + q)
    for t in TARGET_SIZES:                                                     # 작업 표시줄·탐색기 (바탕판 없이)
        img = icon(t)
        save(img, f"Square44x44Logo.targetsize-{t}.png")
        save(img, f"Square44x44Logo.targetsize-{t}_altform-unplated.png")
        save(img, f"Square44x44Logo.targetsize-{t}_altform-lightunplated.png")
    return count


def write_resw(stage: Path) -> None:
    for lang, (name, desc) in STRINGS.items():
        d = stage / "Strings" / lang
        d.mkdir(parents=True, exist_ok=True)
        (d / "Resources.resw").write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n<root>\n'
            '  <resheader name="resmimetype"><value>text/microsoft-resx</value></resheader>\n'
            '  <resheader name="version"><value>2.0</value></resheader>\n'
            '  <resheader name="reader"><value>System.Resources.ResXResourceReader, System.Windows.Forms, '
            'Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value></resheader>\n'
            '  <resheader name="writer"><value>System.Resources.ResXResourceWriter, System.Windows.Forms, '
            'Version=4.0.0.0, Culture=neutral, PublicKeyToken=b77a5c561934e089</value></resheader>\n'
            f'  <data name="AppDisplayName" xml:space="preserve"><value>{escape(name)}</value></data>\n'
            f'  <data name="AppDescription" xml:space="preserve"><value>{escape(desc)}</value></data>\n'
            '</root>\n', "utf-8")


# ------------------------------------------------------------------ 만들기
def main() -> None:
    if sys.platform != "win32":
        fail("MSIX packages are built on Windows only")
    ap = argparse.ArgumentParser(description="Build dist\\Hushpad-<version>.msix from dist\\Hushpad\\")
    ap.add_argument("--name", help="Package/Identity/Name from Partner Center")
    ap.add_argument("--publisher", help="Package/Identity/Publisher from Partner Center (CN=...)")
    ap.add_argument("--publisher-display-name", help="Package/Properties/PublisherDisplayName")
    args = ap.parse_args()

    exe = APP_DIR / "Hushpad.exe"
    if not exe.is_file():
        fail(f"{exe} not found. Run 'python build.py' first.")
    makeappx, makepri = sdk_tool("makeappx.exe"), sdk_tool("makepri.exe")
    ident = identity(args)
    version = package_version()
    placeholder = "TODO" in ident["Name"] or "TODO" in ident["Publisher"]

    if WORK.exists():
        shutil.rmtree(WORK)
    LAYOUT.mkdir(parents=True)

    # 1) 앱 파일: layout\Hushpad\  (zip과 같은 내용 — 라이선스 파일 포함)
    shutil.copytree(APP_DIR, LAYOUT / "Hushpad")
    for n in LEGAL:
        if not (LAYOUT / "Hushpad" / n).is_file():
            shutil.copy2(ROOT / n, LAYOUT / "Hushpad" / n)
    if not (LAYOUT / "Hushpad" / "licenses").is_dir():
        shutil.copytree(ROOT / "licenses", LAYOUT / "Hushpad" / "licenses")

    # 2) 매니페스트
    tpl = string.Template((HERE / "AppxManifest.template.xml").read_text("utf-8"))
    manifest = tpl.substitute(NAME=escape(ident["Name"]), PUBLISHER=escape(ident["Publisher"], {'"': "&quot;"}),
                              PUBLISHER_DISPLAY_NAME=escape(ident["PublisherDisplayName"]),
                              VERSION=version, MAX_TESTED=MAX_TESTED)
    (LAYOUT / "AppxManifest.xml").write_text(manifest, "utf-8")

    # 3) 아이콘과 언어별 이름 → resources.pri  (앱 파일 수천 개를 색인하지 않도록 따로 모아서 만든다)
    PRI_STAGE.mkdir(parents=True)
    n_assets = make_assets(PRI_STAGE / "Assets")
    write_resw(PRI_STAGE)
    cfg = WORK / "priconfig.xml"
    run([str(makepri), "createconfig", "/cf", str(cfg), "/dq", "ko-KR", "/pv", "10.0.0", "/o"], "makepri createconfig")
    # 번들(.msixbundle)용 언어·배율별 분할을 끈다: .msix 하나에 모든 언어·배율이 든 resources.pri 하나
    cfg.write_text(re.sub(r"\s*<packaging>.*?</packaging>", "", cfg.read_text("utf-8"), flags=re.S), "utf-8")
    run([str(makepri), "new", "/pr", str(PRI_STAGE), "/cf", str(cfg), "/in", ident["Name"],
         "/of", str(PRI_STAGE / "resources.pri"), "/o"], "makepri new")
    shutil.copytree(PRI_STAGE / "Assets", LAYOUT / "Assets")
    shutil.copy2(PRI_STAGE / "resources.pri", LAYOUT / "resources.pri")

    # 4) 묶기
    out = ROOT / "dist" / f"Hushpad-{version.rsplit('.', 1)[0]}.msix"
    run([str(makeappx), "pack", "/d", str(LAYOUT), "/p", str(out), "/o"], "makeappx pack")
    print(f"msix {out} {out.stat().st_size / 1e6:.1f}MB  version {version}  assets {n_assets}  "
          f"identity {ident['Name']} / {ident['Publisher']}")
    print(f"  makeappx: {makeappx}")
    if placeholder:
        print("  NOTE: placeholder identity (store_identity.json). Fill in the values from Partner Center "
              "before uploading.")


if __name__ == "__main__":
    main()
