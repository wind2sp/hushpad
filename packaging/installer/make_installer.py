"""Windows 설치 프로그램 만들기 (NSIS).

먼저:   python build.py                      → dist\Hushpad\ (zip판과 같은 앱 폴더)
그다음: python packaging\installer\make_installer.py
결과:   dist\Hushpad-win64-setup.exe (+ .sha256)

makensis.exe가 필요하다 (NSIS 3). PATH 또는 C:\Program Files (x86)\NSIS\makensis.exe.
GitHub Actions(windows-latest)에서는 build-windows 워크플로가 설치해 쓴다.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
OUT_NAME = "Hushpad-win64-setup.exe"


def find_makensis() -> str:
    exe = shutil.which("makensis")
    if exe:
        return exe
    for base in (os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), os.environ.get("ProgramFiles", r"C:\Program Files")):
        p = Path(base) / "NSIS" / "makensis.exe"
        if p.is_file():
            return str(p)
    sys.exit("make_installer: makensis.exe not found (install NSIS 3)")


def main() -> int:
    from hushpad_app import __version__
    src = ROOT / "dist" / "Hushpad"
    if not (src / "Hushpad.exe").is_file():
        sys.exit("make_installer: dist\Hushpad\Hushpad.exe not found — run build.py first")
    out = ROOT / "dist" / OUT_NAME
    out.unlink(missing_ok=True)
    cmd = [find_makensis(), "/V2", "/INPUTCHARSET", "UTF8",
           f"/DVERSION={__version__}", f"/DSRC={src}", f"/DOUT={out}",
           f"/DICON={ROOT / 'assets' / 'app.ico'}",
           str(Path(__file__).with_name("hushpad.nsi"))]
    r = subprocess.run(cmd, capture_output=True, text=True, creationflags=NOWIN)
    if r.returncode != 0 or not out.is_file():
        print(r.stdout[-6000:], r.stderr[-3000:], sep="\n", file=sys.stderr)
        return 1
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_name(out.name + ".sha256").write_text(f"{digest}  {out.name}\n", "utf-8")
    print(f"setup {out} {out.stat().st_size / 1e6:.1f}MB sha256 {digest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
