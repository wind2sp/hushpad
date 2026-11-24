"""zip판(Windows) 자동 업데이트.

GitHub 릴리스의 version.json(최신 릴리스에 함께 올린 파일)을 읽어 새 버전이 있으면 묻고, 같은 릴리스의 새 zip을 받아 크기·SHA-256과 새 exe의 --selftest를
확인한 뒤, 새 exe를 `--finish-update <지금 앱 폴더> <pid>`로 띄우고 지금 앱은 끝낸다. 새 exe(받아서 푼 임시 폴더에서 실행)가
지금 앱이 끝나기를 기다렸다가 앱 폴더를 `<폴더>.old-<시각>`으로 옮기고, 새 폴더를 같은 자리·같은 이름으로 복사한 뒤 다시 켠다.
같은 경로이므로 Windows 시작 프로그램(Run 키)·바로가기·설정이 그대로 이어진다. 메모(보관 폴더)는 건드리지 않는다.

- Microsoft Store판(패키지)은 Store가 업데이트하므로 쓰지 않는다. macOS판·개발용 파이썬 실행도 쓰지 않는다.
- 설치판(설치 프로그램으로 깐 것, 폴더에 'Uninstall Hushpad.exe'가 있음)은 zip 대신 새 설치 프로그램을 받아
  SHA-256을 확인한 뒤 `/S /WAITPID=<pid> /RELAUNCH`로 조용히 실행하고 끝난다 (packaging/installer/hushpad.nsi).
- 연결하는 곳은 GitHub(버전 파일·zip 내려받기)뿐이다. 메모·설정·사용 기록을 보내지 않는다. 설정에서 자동 확인을 끌 수 있다.
- 릴리스를 낼 때 zip과 함께 version.json을 올린다 (tools/make_version_json.py).
- 시험: HUSHPAD_UPDATE_URL로 version.json 주소를 바꿀 수 있다(127.0.0.1만 http 허용).

version.json
{ "version": "1.0.2", "date": "2026-11-24", "important": false,
  "notes": {"ko": ["…"], "en": ["…"], "ja": ["…"], "zh": ["…"]},
  "files": {"win": {"name": "Hushpad-win64.zip", "url": "https://github.com/…/v1.0.2/Hushpad-win64.zip",
                    "size": 45761102, "sha256": "…"},
            "setup": {"name": "Hushpad-win64-setup.exe", "url": "…", "size": …, "sha256": "…"}} }
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from urllib.parse import urlparse

from . import __version__, plat
from .common import LOCAL_DIR

VERSION_URL = "https://github.com/wind2sp/hushpad/releases/latest/download/version.json"
DOWNLOAD_PAGE = "https://github.com/wind2sp/hushpad/releases/latest"
EXE_NAME = "Hushpad.exe"
UNINSTALLER = "Uninstall Hushpad.exe"
UPDATE_DIR = LOCAL_DIR / "update"
NOWIN = getattr(subprocess, "CREATE_NO_WINDOW", 0)
USER_AGENT = f"Hushpad/{__version__} (update check)"


class UpdateError(Exception):
    pass


def supported() -> bool:
    """자동 업데이트를 쓰는 실행인가: Windows zip판(배포된 exe), Store 패키지 아님."""
    return sys.platform == "win32" and bool(getattr(sys, "frozen", False)) and not plat.IS_PACKAGED \
        and Path(sys.executable).name.lower() == EXE_NAME.lower() and "--selftest" not in sys.argv


def version_url() -> str:
    return os.environ.get("HUSHPAD_UPDATE_URL") or VERSION_URL


def parse_version(v: str) -> tuple:
    out = []
    for part in str(v).strip().lstrip("vV").split("."):
        digits = "".join(ch for ch in part if ch.isdigit())
        out.append(int(digits) if digits else 0)
    return tuple(out + [0] * (4 - len(out)))[:4]


def is_newer(info: dict, current: str = __version__) -> bool:
    return parse_version(info.get("version", "0")) > parse_version(current)


def _check_url(url: str) -> None:
    u = urlparse(url)
    if u.scheme == "https":
        return
    if u.scheme == "http" and u.hostname in ("127.0.0.1", "localhost"):   # 시험용 로컬 서버
        return
    raise UpdateError(f"refused URL: {url}")


def _open(url: str, timeout: float):
    _check_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Cache-Control": "no-cache"})
    return urllib.request.urlopen(req, timeout=timeout)


def fetch_info(timeout: float = 10) -> dict:
    """version.json을 읽는다. 실패하면 UpdateError."""
    try:
        with _open(version_url(), timeout) as r:
            data = r.read(256 * 1024)
        info = json.loads(data.decode("utf-8"))
    except UpdateError:
        raise
    except Exception as e:
        raise UpdateError(str(e)) from e
    files = info.get("files") or {}
    ok = [k for k in ("win", "setup") if all((files.get(k) or {}).get(x) for x in ("url", "sha256", "size"))]
    if not info.get("version") or not ok:
        raise UpdateError("version.json is missing fields")
    return info


def installed() -> bool:
    """설치 프로그램으로 깐 Hushpad인가 (아니면 zip 포터블판)."""
    return (app_dir() / UNINSTALLER).is_file()


def file_kind() -> str:
    return "setup" if installed() else "win"


def has_file(info: dict, kind: str) -> bool:
    f = (info.get("files") or {}).get(kind) or {}
    return bool(f.get("url") and f.get("sha256") and f.get("size"))


def notes_for(info: dict, lang: str) -> list:
    n = info.get("notes") or []
    if isinstance(n, dict):
        n = n.get(lang) or n.get("en") or next(iter(n.values()), [])
    return [str(x) for x in n]


def app_dir() -> Path:
    return Path(sys.executable).resolve().parent


def can_replace(target: Path) -> bool:
    """앱 폴더를 옮기고 새로 만들 수 있는지 (Program Files 같은 곳은 안 됨)."""
    try:
        probe = target.parent / f".hushpad-write-test-{os.getpid()}"
        probe.mkdir()
        probe.rmdir()
        t = target / f".hushpad-write-test-{os.getpid()}"
        t.write_bytes(b"")
        t.unlink()
        return True
    except OSError:
        return False


# ------------------------------------------------------------------ 받기·확인
def download(info: dict, progress=None, cancelled=None, kind: str = "win") -> Path:
    """새 zip(kind='win') 또는 설치 프로그램(kind='setup')을 받아 크기·SHA-256을 확인하고 경로를 돌려준다."""
    f = info["files"][kind]
    UPDATE_DIR.mkdir(parents=True, exist_ok=True)
    dest = UPDATE_DIR / (f"Hushpad-{info['version']}-setup.exe" if kind == "setup" else f"Hushpad-{info['version']}-win64.zip")
    part = dest.with_suffix(".part")
    total = int(f["size"])
    h = hashlib.sha256()
    done = 0
    try:
        with _open(f["url"], 30) as r, open(part, "wb") as out:
            while True:
                if cancelled and cancelled():
                    raise UpdateError("cancelled")
                chunk = r.read(256 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if done > total + 1024 * 1024:
                    raise UpdateError("file is larger than expected")
                if progress:
                    progress(done, total)
    except UpdateError:
        part.unlink(missing_ok=True)
        raise
    except Exception as e:
        part.unlink(missing_ok=True)
        raise UpdateError(str(e)) from e
    if done != total:
        part.unlink(missing_ok=True)
        raise UpdateError(f"size mismatch ({done} != {total})")
    if h.hexdigest().lower() != f["sha256"].lower():
        part.unlink(missing_ok=True)
        raise UpdateError("SHA-256 mismatch")
    os.replace(part, dest)
    return dest


def extract(zip_path: Path, version: str) -> Path:
    """zip을 풀어 새 앱 폴더(…/Hushpad)를 돌려준다. 폴더 밖으로 나가는 경로는 거부."""
    root = UPDATE_DIR / f"v{version}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    with zipfile.ZipFile(zip_path) as z:
        base = root.resolve()
        for name in z.namelist():
            p = (root / name).resolve()
            if base not in p.parents and p != base:
                raise UpdateError(f"bad path in zip: {name}")
        z.extractall(root)
    exes = [p for p in root.rglob(EXE_NAME) if p.parent.name.lower() == "hushpad"]
    if not exes:
        raise UpdateError(f"{EXE_NAME} not found in the zip")
    return exes[0].parent


def selftest(new_dir: Path, timeout: float = 300) -> None:
    """새 exe의 자체 점검. 실패하면 UpdateError."""
    exe = new_dir / EXE_NAME
    try:
        r = subprocess.run([str(exe), "--selftest"], timeout=timeout, creationflags=NOWIN,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        raise UpdateError(f"self-test could not run: {e}") from e
    if r.returncode != 0:
        raise UpdateError(f"self-test failed (code {r.returncode})")


def launch_finish(new_dir: Path, target: Path) -> None:
    """새 exe가 바꿔치기를 맡게 띄운다. 이 뒤에 지금 앱은 바로 끝나야 한다."""
    exe = new_dir / EXE_NAME
    flags = NOWIN | getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([str(exe), "--finish-update", str(target), str(os.getpid())],
                     cwd=str(new_dir), creationflags=flags, close_fds=True)


def launch_setup(setup: Path) -> None:
    """설치판: 새 설치 프로그램을 조용히 실행. 이 앱이 끝나기를 기다렸다가 덮어쓰고 Hushpad를 다시 켠다."""
    flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    subprocess.Popen([str(setup), "/S", f"/WAITPID={os.getpid()}", "/RELAUNCH"],
                     cwd=str(setup.parent), creationflags=flags, close_fds=True)


# ------------------------------------------------------------------ 바꿔치기 (새 exe 안에서)
def _wait_pid(pid: int, seconds: float) -> None:
    if sys.platform != "win32":
        return
    import ctypes
    SYNCHRONIZE = 0x00100000
    h = ctypes.windll.kernel32.OpenProcess(SYNCHRONIZE, False, pid)
    if not h:
        return                      # 이미 끝남
    try:
        ctypes.windll.kernel32.WaitForSingleObject(h, int(seconds * 1000))
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def _log(msg: str) -> None:
    try:
        UPDATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(UPDATE_DIR / "update.log", "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + msg + "\n")
    except OSError:
        pass


def _start(exe: Path) -> None:
    subprocess.Popen([str(exe)], cwd=str(exe.parent), creationflags=NOWIN, close_fds=True)


def finish_update(target: str, pid: str) -> int:
    """`--finish-update <앱 폴더> <pid>`: 지금 앱이 끝나기를 기다렸다가 앱 폴더를 새 것으로 바꾸고 다시 켠다."""
    tgt = Path(target)
    src = Path(sys.executable).resolve().parent
    _log(f"finish-update {src} -> {tgt} (pid {pid})")
    try:
        _wait_pid(int(pid), 60)
    except ValueError:
        pass
    time.sleep(0.5)
    if not (tgt / EXE_NAME).is_file() or src == tgt.resolve():
        _log("target is not a Hushpad folder; stop")
        return 2
    old = tgt.with_name(f"{tgt.name}.old-{time.strftime('%Y%m%d%H%M%S')}")
    for _ in range(40):                        # 백신·탐색기가 잠깐 파일을 쥐고 있을 수 있다
        try:
            os.replace(tgt, old)
            break
        except OSError as e:
            last = e
            time.sleep(0.5)
    else:
        _log(f"could not move the old folder: {last}")
        _start(tgt / EXE_NAME)
        return 3
    try:
        shutil.copytree(src, tgt)
    except Exception as e:
        _log(f"copy failed: {e}; rolling back")
        shutil.rmtree(tgt, ignore_errors=True)
        try:
            os.replace(old, tgt)
        except OSError as e2:
            _log(f"rollback failed: {e2}")
        _start(tgt / EXE_NAME)
        return 4
    try:
        (UPDATE_DIR / "cleanup.json").write_text(json.dumps({"old": str(old)}), "utf-8")
    except OSError:
        pass
    _log("done")
    _start(tgt / EXE_NAME)
    return 0


def cleanup() -> None:
    """지난 업데이트가 남긴 것(예전 앱 폴더, 받은 zip·푼 폴더)을 지운다. 앱이 켜진 뒤 조용히."""
    try:
        marker = UPDATE_DIR / "cleanup.json"
        if marker.is_file():
            old = Path(json.loads(marker.read_text("utf-8")).get("old", ""))
            if old.name and ".old-" in old.name and (old / EXE_NAME).exists():
                shutil.rmtree(old, ignore_errors=True)
            if not old.exists():
                marker.unlink(missing_ok=True)
        if UPDATE_DIR.is_dir():
            for p in UPDATE_DIR.iterdir():
                if p.name in ("cleanup.json", "update.log"):
                    continue
                if p.is_dir():
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    p.unlink(missing_ok=True)
    except Exception:
        pass
