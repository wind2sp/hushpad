"""앱 만들기:  python build.py
    Windows → dist\\Hushpad\\Hushpad.exe
    macOS   → dist/Hushpad.app   (서명·공증 없음)
그 뒤 만든 앱으로 --selftest를 돌려 점검한다."""
import hashlib
import os
import shutil
import subprocess
import zipfile
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
IS_MAC = sys.platform == "darwin"
SEP = os.pathsep   # --add-data 구분자: Windows ';' / macOS ':'
LEGAL = ("LICENSE", "NOTICE", "THIRD_PARTY_NOTICES.md")


def data(src: Path, dest: str) -> list[str]:
    return ["--add-data", f"{src}{SEP}{dest}"]


def main():
    subprocess.run([sys.executable, str(HERE / "assets" / "make_icon.py")], check=True, creationflags=NOWIN)
    excludes = ["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
                "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtCharts", "PySide6.QtDataVisualization",
                "PySide6.QtPdf", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtBluetooth", "PySide6.QtPositioning",
                "PySide6.QtLocation", "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtWebSockets",
                "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtOpenGLWidgets", "PySide6.QtSvgWidgets",
                "PySide6.QtQuick3D", "PySide6.QtGraphs", "PySide6.QtSpatialAudio", "PySide6.QtTextToSpeech"]
    icon = HERE / "assets" / ("app.icns" if IS_MAC else "app.ico")
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
           "--name", "Hushpad", "--icon", str(icon)]
    for n in ("app.ico", "app.png", "app_small.png") + (("app.icns",) if IS_MAC else ()):
        cmd += data(HERE / "assets" / n, "assets")
    cmd += data(HERE / "hushpad_app" / "locales", "hushpad_app/locales")     # 문구 목록 (ko·en·ja·zh)
    for n in LEGAL:                                                           # 라이선스 (앱 안에도, 서명 전에 넣음)
        cmd += data(HERE / n, ".")
    cmd += data(HERE / "licenses", "licenses")                                # 함께 배포하는 오픈소스의 라이선스 원문
    cmd += ["--hidden-import", "PySide6.QtMultimedia", "--hidden-import", "PySide6.QtMultimediaWidgets"]
    if IS_MAC:
        cmd += ["--osx-bundle-identifier", "com.hushpad.app"]
    for e in excludes:
        cmd += ["--exclude-module", e]
    cmd.append(str(HERE / "hushpad_main.py"))
    subprocess.run(cmd, check=True, cwd=HERE, creationflags=NOWIN)
    removed = prune(HERE / "dist" / ("Hushpad.app" if IS_MAC else "Hushpad"))
    print(f"pruned {removed} unused Qt files (virtual keyboard, QML/Quick, software OpenGL)")
    if IS_MAC:
        finish_mac_bundle(HERE / "dist" / "Hushpad.app")
    if IS_MAC:
        exe = HERE / "dist" / "Hushpad.app" / "Contents" / "MacOS" / "Hushpad"
    else:
        exe = HERE / "dist" / "Hushpad" / "Hushpad.exe"
    r = subprocess.run([str(exe), "--selftest"], creationflags=NOWIN)
    print("selftest", "PASS" if r.returncode == 0 else f"FAIL ({r.returncode})")
    if r.returncode == 0 and not IS_MAC:
        print(make_windows_zip())
    sys.exit(r.returncode)


# 쓰지 않는데 PySide6가 끌어오는 것: Qt 가상 키보드(GPL 전용 구성요소), QML·Quick, Mesa 소프트웨어 OpenGL.
# 남는 파일 중 이것들을 불러오는 것이 없음을 확인했다(가져오기 표 검사).
PRUNE_PATTERNS = ("*VirtualKeyboard*", "*virtualkeyboard*", "Qt6Qml*", "Qt6Quick*", "QtQml*", "QtQuick*",
                  "opengl32sw.dll",
                  # 쓰지 않는 그림 형식·플랫폼·터치 플러그인 (배포물과 라이선스 목록을 줄임)
                  "*qtiff*", "*qtga*", "*qwbmp*", "*qicns*", "*qdirect2d*", "*qminimal*",
                  "*qtuiotouchplugin*",
                  # Qt 네트워크 TLS용 OpenSSL 사본 (Hushpad는 네트워크를 쓰지 않음. Python의 libssl-3.dll은 남김)
                  "libssl-3-x64.dll", "libcrypto-3-x64.dll")
PRUNE_PLUGIN_DIRS = ("tls", "networkinformation", "platforminputcontexts")


def prune(root: Path) -> int:
    n = 0
    for plugins in [p for p in root.rglob("plugins") if p.is_dir()]:
        for d in PRUNE_PLUGIN_DIRS:
            if (plugins / d).is_dir():
                shutil.rmtree(plugins / d)
                n += 1
    for pat in PRUNE_PATTERNS:
        for f in sorted(root.rglob(pat), key=lambda x: -len(x.parts)):
            if f.is_symlink():          # macOS 번들의 Resources ↔ Frameworks 연결 (끊긴 연결도 지움)
                f.unlink()
                n += 1
                continue
            if not f.exists():
                continue
            if f.is_dir():
                shutil.rmtree(f)
            else:
                f.unlink()
            n += 1
    for plugins in [p for p in root.rglob("plugins") if p.is_dir()]:   # 비게 된 플러그인 폴더 정리
        for d in [d for d in plugins.iterdir() if d.is_dir() and not d.is_symlink() and not any(d.iterdir())]:
            d.rmdir()
    return n


def finish_mac_bundle(app: Path) -> None:
    """Info.plist에 버전을 적고, 파일을 바꿨으므로 임시 서명(ad-hoc)을 다시 한다."""
    import plistlib
    sys.path.insert(0, str(HERE))
    from hushpad_app import __version__
    pl = app / "Contents" / "Info.plist"
    info = plistlib.loads(pl.read_bytes())
    info.update({"CFBundleShortVersionString": __version__, "CFBundleVersion": __version__,
                 "CFBundleName": "Hushpad", "CFBundleDisplayName": "Hushpad",
                 "NSHumanReadableCopyright": "© 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad "
                                             "contributors · GPL-3.0-or-later",
                 "LSApplicationCategoryType": "public.app-category.productivity",
                 "NSHighResolutionCapable": True})
    pl.write_bytes(plistlib.dumps(info))
    subprocess.run(["codesign", "--force", "--deep", "--sign", "-", str(app)], check=True)


def make_windows_zip() -> str:
    """배포용 zip: dist/Hushpad-win64.zip (이름에 버전을 넣지 않아 홈페이지 링크가 늘 최신을 가리킴).
    zip 안: Hushpad/Hushpad.exe, _internal/, LICENSE, NOTICE, THIRD_PARTY_NOTICES.md, licenses/"""
    app_dir = HERE / "dist" / "Hushpad"
    for n in LEGAL:
        shutil.copy2(HERE / n, app_dir / n)
    shutil.copytree(HERE / "licenses", app_dir / "licenses", dirs_exist_ok=True)
    out = HERE / "dist" / "Hushpad-win64.zip"
    tmp = out.with_suffix(".tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(app_dir.rglob("*")):
            if f.is_file():
                z.write(f, Path("Hushpad") / f.relative_to(app_dir))
    os.replace(tmp, out)
    h = hashlib.sha256(out.read_bytes()).hexdigest()
    (out.parent / (out.name + ".sha256")).write_text(h + "  " + out.name + "\n", "ascii")
    return f"zip {out} {out.stat().st_size / 1e6:.1f}MB sha256 {h}"


if __name__ == "__main__":
    main()
