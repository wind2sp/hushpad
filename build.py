"""exe 만들기:  python build.py   →  dist\\Hushpad\\Hushpad.exe  (그 뒤 --selftest로 점검)"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def main():
    subprocess.run([sys.executable, str(HERE / "assets" / "make_icon.py")], check=True, creationflags=NOWIN)
    excludes = ["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.Qt3DCore",
                "PySide6.QtQuick", "PySide6.QtQml", "PySide6.QtCharts", "PySide6.QtDataVisualization",
                "PySide6.QtPdf", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtBluetooth", "PySide6.QtPositioning",
                "PySide6.QtLocation", "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtWebSockets",
                "PySide6.QtDesigner", "PySide6.QtHelp", "PySide6.QtOpenGLWidgets", "PySide6.QtSvgWidgets",
                "PySide6.QtQuick3D", "PySide6.QtGraphs", "PySide6.QtSpatialAudio", "PySide6.QtTextToSpeech"]
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--windowed", "--onedir",
           "--name", "Hushpad", "--icon", str(HERE / "assets" / "app.ico"),
           "--add-data", f"{HERE / 'assets' / 'app.ico'};assets",
           "--add-data", f"{HERE / 'assets' / 'app.png'};assets",
           "--add-data", f"{HERE / 'assets' / 'app_small.png'};assets",
           "--hidden-import", "PySide6.QtMultimedia", "--hidden-import", "PySide6.QtMultimediaWidgets"]
    for e in excludes:
        cmd += ["--exclude-module", e]
    cmd.append(str(HERE / "hushpad_main.py"))
    subprocess.run(cmd, check=True, cwd=HERE, creationflags=NOWIN)
    exe = HERE / "dist" / "Hushpad" / "Hushpad.exe"
    r = subprocess.run([str(exe), "--selftest"], creationflags=NOWIN)
    print("selftest", "PASS" if r.returncode == 0 else f"FAIL ({r.returncode})")
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
