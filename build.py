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
    cmd += ["--hidden-import", "PySide6.QtMultimedia", "--hidden-import", "PySide6.QtMultimediaWidgets"]
    if IS_MAC:
        cmd += ["--osx-bundle-identifier", "com.hushpad.app"]
    for e in excludes:
        cmd += ["--exclude-module", e]
    cmd.append(str(HERE / "hushpad_main.py"))
    subprocess.run(cmd, check=True, cwd=HERE, creationflags=NOWIN)
    if IS_MAC:
        exe = HERE / "dist" / "Hushpad.app" / "Contents" / "MacOS" / "Hushpad"
    else:
        exe = HERE / "dist" / "Hushpad" / "Hushpad.exe"
    r = subprocess.run([str(exe), "--selftest"], creationflags=NOWIN)
    print("selftest", "PASS" if r.returncode == 0 else f"FAIL ({r.returncode})")
    if r.returncode == 0 and not IS_MAC:
        print(make_windows_zip())
    sys.exit(r.returncode)


def make_windows_zip() -> str:
    """배포용 zip: dist/Hushpad-win64.zip (이름에 버전을 넣지 않아 홈페이지 링크가 늘 최신을 가리킴).
    zip 안: Hushpad/Hushpad.exe, _internal/, LICENSE, NOTICE, THIRD_PARTY_NOTICES.md"""
    app_dir = HERE / "dist" / "Hushpad"
    for n in LEGAL:
        shutil.copy2(HERE / n, app_dir / n)
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
