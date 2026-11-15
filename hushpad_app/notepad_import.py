"""Windows 11 메모장의 열린 탭(저장 안 한 내용 포함)을 읽어 온다.

메모장은 %LOCALAPPDATA%\\Packages\\Microsoft.WindowsNotepad_8wekyb3d8bbwe\\LocalState\\TabState\\<guid>.bin
에 탭 상태를 둔다. 공개되지 않은 형식이라 알려진 구조대로 읽고, 실패한 파일은 건너뛴다.
원본 파일은 읽기만 하고 절대 고치지 않는다.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

TABSTATE = Path(os.environ.get("LOCALAPPDATA", "")) / "Packages" / \
    "Microsoft.WindowsNotepad_8wekyb3d8bbwe" / "LocalState" / "TabState"
_GUID_BIN = re.compile(r"^[0-9a-fA-F\-]{36}\.bin$")


@dataclass
class NotepadTab:
    text: str
    path: str        # 저장된 파일이면 그 경로
    mtime: float
    source: str      # tab-state 파일 이름


class _R:
    def __init__(self, b: bytes):
        self.b, self.p = b, 0

    def byte(self) -> int:
        v = self.b[self.p]
        self.p += 1
        return v

    def skip(self, n: int) -> None:
        if self.p + n > len(self.b):
            raise ValueError("eof")
        self.p += n

    def uleb(self) -> int:
        r = s = 0
        while True:
            v = self.byte()
            r |= (v & 0x7F) << s
            if not v & 0x80:
                return r
            s += 7
            if s > 63:
                raise ValueError("uleb")

    def u16s(self, n: int) -> str:
        if self.p + 2 * n > len(self.b):
            raise ValueError("eof")
        s = self.b[self.p:self.p + 2 * n].decode("utf-16-le", errors="replace")
        self.p += 2 * n
        return s


def parse_tab(data: bytes) -> tuple[str, str] | None:
    """(내용, 파일경로) — 형식이 다르면 None"""
    if data[:2] != b"NP":
        return None
    r = _R(data)
    r.p = 2
    r.uleb()                     # 순번
    saved = r.uleb()             # 0 = 저장 안 한 탭, 1 = 파일과 연결된 탭
    path = ""
    if saved == 1:
        path = r.u16s(r.uleb())
        r.uleb()                 # 저장된 내용 길이
        r.skip(2)                # 인코딩, 줄바꿈 종류
        r.uleb()                 # 파일 시각
        r.skip(32)               # sha256
        r.skip(2)                # 00 01
    elif saved == 0:
        r.skip(1)
    else:
        return None
    r.uleb()
    r.uleb()                     # 선택 시작·끝
    r.skip(3)                    # 줄바꿈·RTL·유니코드 표시
    r.skip(r.uleb())             # 추가 옵션
    text = r.u16s(r.uleb())
    r.skip(1 + 4)                # 저장 안 됨 표시, CRC
    # 뒤에 붙은 '아직 합쳐지지 않은 편집' 조각들을 반영
    while r.p < len(r.b):
        try:
            pos, dele, add = r.uleb(), r.uleb(), r.uleb()
            ins = r.u16s(add)
            r.skip(4)
        except (ValueError, IndexError):
            break
        if pos > len(text):
            break
        text = text[:pos] + ins + text[pos + dele:]
    return text.replace("\r\n", "\n").replace("\r", "\n"), path


def read_tabs(folder: Path = TABSTATE) -> list[NotepadTab]:
    out: list[NotepadTab] = []
    if not folder.is_dir():
        return out
    for p in sorted(folder.iterdir()):
        if not _GUID_BIN.match(p.name):
            continue  # <guid>.0.bin, .1.bin 은 창 설정
        try:
            res = parse_tab(p.read_bytes())
        except Exception:
            res = None
        if not res:
            continue
        text, path = res
        if not text.strip() and path and Path(path).is_file():
            try:
                text = Path(path).read_text("utf-8", errors="replace")
            except OSError:
                pass
        if text.strip():
            out.append(NotepadTab(text=text, path=path, mtime=p.stat().st_mtime, source=p.name))
    return out
