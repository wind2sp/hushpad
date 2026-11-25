"""메모 저장소.

데이터 폴더 구조 (모든 파일은 암호화되어 있어 다른 프로그램이 내용을 읽을 수 없다)
  vault.json            암호로 감싼 데이터 키
  notes/<id>.own        메모 하나 = 파일 하나 (id = 만든 시각, 예: 20261115-143205-a1b2)
  history/<id>/<ts>.owh 메모의 이전 버전 (10분마다 한 번, 최근 40개)
  media/<mid>.owm       동영상 같은 큰 첨부
  categories.own        분류 목록
  catcolors.own         분류 색 (1.0.7~, 예전 버전은 이 파일을 모르고 지나감)

메모 하나가 파일 하나라서 Dropbox 같은 동기화 폴더에 두어도 충돌이 메모 단위로만 생긴다.
저장은 임시 파일에 쓰고 fsync 후 교체(os.replace)하므로 저장 도중 꺼져도 이전 내용이 남는다.
"""
from __future__ import annotations

import json
import os
import re
import secrets
import shutil
import time
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

from . import crypto
from .i18n import tr

SNAPSHOT_EVERY = 600  # 초
SNAPSHOT_KEEP = 40
MEDIA_RE = re.compile(r"owvideo:([0-9a-zA-Z\-]+)")


@dataclass
class Note:
    id: str
    kind: str = "rich"          # rich = 서식 메모(이미지·동영상 가능), text = 텍스트 메모(HTML·JSON·코드)
    title: str = ""             # 비어 있으면 자동 제목
    category: str = ""
    pinned: bool = False
    starred: bool = False       # ★ 별표 (즐겨찾기)
    secret: bool = False        # 목록에서 첫 줄 숨김 + 복사 후 클립보드 자동 지움
    created: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    deleted: float | None = None
    html: str = ""
    text: str = ""

    def first_line(self) -> str:
        fallback = ""
        for line in self.text.splitlines():
            s = line.replace("￼", "").strip()
            if not s:
                continue
            fallback = fallback or s
            if any(ch.isalnum() for ch in s):  # '{', '<div>' 처럼 기호만 있는 줄은 건너뜀
                return s.strip("{}[]<>,;").strip()[:80] or s[:80]
        return fallback[:80]

    def snippet(self, n: int = 160) -> str:
        """목록 둘째 줄: 첫 줄(제목) 다음 내용."""
        lines = [ln.replace("\ufffc", " ").strip() for ln in self.text.splitlines()]
        lines = [ln for ln in lines if ln]
        if not self.title:
            # \uc81c\ubaa9\uc73c\ub85c \uc4f4 \uc904(\uae00\uc790\uac00 \uc788\ub294 \uccab \uc904)\uae4c\uc9c0 \ud1b5\uc9f8\ub85c \uac74\ub108\ub700
            for i, ln in enumerate(lines):
                if any(ch.isalnum() for ch in ln):
                    lines = lines[i + 1:]
                    break
        flat = " ".join(" ".join(lines).split()).strip(" ,;")
        if not flat:
            flat = tr("note.chars", n=len(self.text.strip())) + (tr("note.with_image") if self.has_images() else "")
        return flat[:n]

    def has_images(self) -> bool:
        return "<img" in self.html

    def is_empty(self) -> bool:
        return not self.text.replace("￼", "").strip() and not self.has_images()

    def display_title(self) -> str:
        if self.title:
            return self.title
        if self.secret:
            return tr("note.secret")
        fl = self.first_line()
        if fl:
            return fl
        if self.has_images():
            return tr("note.image")
        return tr("note.empty")

    def media_ids(self) -> set[str]:
        return set(MEDIA_RE.findall(self.html))

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self), ensure_ascii=False).encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes, nid: str) -> "Note":
        d = json.loads(data.decode("utf-8"))
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        known["id"] = nid  # 파일 이름이 기준 (동기화 충돌 사본도 별도 메모로 보이게)
        return cls(**known)


def new_id(ts: float | None = None) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(ts or time.time())) + "-" + secrets.token_hex(2)


def _write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".~{path.name}.{os.getpid()}.tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    for i in range(5):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:  # 동기화·백신 프로그램이 잠깐 잡고 있을 때
            time.sleep(0.1 * (i + 1))
    os.replace(tmp, path)


class Store:
    def __init__(self, folder: Path, key: bytes):
        self.folder = Path(folder)
        self.key = key
        self.notes_dir = self.folder / "notes"
        self.hist_dir = self.folder / "history"
        self.media_dir = self.folder / "media"
        self.cat_file = self.folder / "categories.own"
        self.color_file = self.folder / "catcolors.own"
        for d in (self.notes_dir, self.hist_dir, self.media_dir):
            d.mkdir(parents=True, exist_ok=True)
        self.notes: dict[str, Note] = {}
        self._mtimes: dict[str, int] = {}
        self._last_snap: dict[str, float] = {}
        self.broken: list[str] = []
        self.categories: list[str] = []
        self.cat_colors: dict[str, str] = {}

    # ------------------------------------------------------------ 읽기
    def _path(self, nid: str) -> Path:
        return self.notes_dir / f"{nid}.own"

    def _load_file(self, p: Path) -> Note:
        return Note.from_bytes(crypto.unseal(self.key, p.read_bytes()), p.stem)

    def load_all(self) -> None:
        self.notes.clear()
        self._mtimes.clear()
        self.broken = []
        for p in self.notes_dir.glob("*.own"):
            try:
                st = p.stat()
                self.notes[p.stem] = self._load_file(p)
                self._mtimes[p.stem] = st.st_mtime_ns
            except Exception:
                self.broken.append(p.name)
        self.load_categories()

    def scan(self) -> tuple[list[str], list[str]]:
        """다른 PC(동기화)에서 바뀐 메모를 찾아 다시 읽는다. (바뀐 id, 사라진 id)"""
        changed, seen = [], set()
        try:
            entries = list(os.scandir(self.notes_dir))
        except OSError:
            return [], []
        for e in entries:
            if not e.name.endswith(".own") or e.name.startswith(".~"):
                continue
            nid = e.name[:-4]
            seen.add(nid)
            try:
                m = e.stat().st_mtime_ns
            except OSError:
                continue
            if self._mtimes.get(nid) == m:
                continue
            try:
                note = self._load_file(Path(e.path))
            except Exception:
                continue  # 아직 쓰는 중이거나 다른 암호 — 다음 검사 때 다시
            self._mtimes[nid] = m
            old = self.notes.get(nid)
            if old is not None and note.updated <= old.updated:
                continue
            self.notes[nid] = note
            changed.append(nid)
        removed = [nid for nid in list(self.notes) if nid not in seen]
        for nid in removed:
            self.notes.pop(nid, None)
            self._mtimes.pop(nid, None)
        return changed, removed

    # ------------------------------------------------------------쓰기
    def save(self, note: Note, touch: bool = True, snapshot: bool = True) -> None:
        if touch:
            note.updated = time.time()
        p = self._path(note.id)
        _write_atomic(p, crypto.seal(self.key, note.to_bytes()))
        self._mtimes[note.id] = p.stat().st_mtime_ns
        self.notes[note.id] = note
        if snapshot:
            self.snapshot(note)

    def create(self, kind: str = "rich", category: str = "", text: str = "", html: str = "",
               title: str = "", created: float | None = None) -> Note:
        ts = created or time.time()
        nid = new_id(ts)
        while self._path(nid).exists():
            nid = new_id(ts)
        note = Note(id=nid, kind=kind, category=category, text=text, html=html, title=title,
                    created=ts, updated=time.time())
        self.save(note, touch=False, snapshot=False)
        return note

    def trash(self, ids) -> None:
        now = time.time()
        for nid in ids:
            n = self.notes.get(nid)
            if n and n.deleted is None:
                n.deleted = now
                self.save(n, touch=False, snapshot=False)

    def restore(self, ids) -> None:
        for nid in ids:
            n = self.notes.get(nid)
            if n and n.deleted is not None:
                n.deleted = None
                self.save(n, touch=False, snapshot=False)

    def purge(self, ids) -> None:
        ids = set(ids)
        doomed_media = set()
        for nid in ids:
            n = self.notes.get(nid)
            if n:
                doomed_media |= n.media_ids()
        for nid in ids:
            self.notes.pop(nid, None)
            self._mtimes.pop(nid, None)
            try:
                self._path(nid).unlink()
            except FileNotFoundError:
                pass
            shutil.rmtree(self.hist_dir / nid, ignore_errors=True)
        still = set()
        for n in self.notes.values():
            still |= n.media_ids()
        for mid in doomed_media - still:
            try:
                (self.media_dir / f"{mid}.owm").unlink()
            except FileNotFoundError:
                pass

    # ------------------------------------------------------------ 이전 버전
    def snapshot(self, note: Note, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_snap.get(note.id, 0) < SNAPSHOT_EVERY:
            return
        d = self.hist_dir / note.id
        if not force and not self._last_snap.get(note.id):
            snaps = sorted(d.glob("*.owh")) if d.exists() else []
            if snaps:
                try:
                    last = int(snaps[-1].stem) / 1000
                    if now - last < SNAPSHOT_EVERY:
                        self._last_snap[note.id] = last
                        return
                except ValueError:
                    pass
        self._last_snap[note.id] = now
        _write_atomic(d / f"{int(now * 1000)}.owh", crypto.seal(self.key, note.to_bytes(), b"hist"))
        snaps = sorted(d.glob("*.owh"))
        for old in snaps[:-SNAPSHOT_KEEP]:
            try:
                old.unlink()
            except OSError:
                pass

    def history(self, nid: str) -> list[tuple[float, Path]]:
        d = self.hist_dir / nid
        out = []
        for p in sorted(d.glob("*.owh"), reverse=True) if d.exists() else []:
            try:
                out.append((int(p.stem) / 1000, p))
            except ValueError:
                pass
        return out

    def load_snapshot(self, path: Path, nid: str) -> Note:
        return Note.from_bytes(crypto.unseal(self.key, path.read_bytes(), b"hist"), nid)

    # ------------------------------------------------------------ 첨부(동영상)
    def put_media(self, data: bytes) -> str:
        mid = time.strftime("%Y%m%d-%H%M%S") + "-" + secrets.token_hex(3)
        _write_atomic(self.media_dir / f"{mid}.owm", crypto.seal(self.key, data, b"media"))
        return mid

    def get_media(self, mid: str) -> bytes:
        return crypto.unseal(self.key, (self.media_dir / f"{mid}.owm").read_bytes(), b"media")

    # ------------------------------------------------------------ 분류
    def load_categories(self) -> None:
        try:
            self.categories = json.loads(crypto.unseal(self.key, self.cat_file.read_bytes(), b"cats"))
        except Exception:
            self.categories = []
        try:
            self.cat_colors = json.loads(crypto.unseal(self.key, self.color_file.read_bytes(), b"catcolors"))
        except Exception:
            self.cat_colors = {}

    def save_cat_colors(self) -> None:
        _write_atomic(self.color_file, crypto.seal(self.key, json.dumps(self.cat_colors, ensure_ascii=False)
                                                   .encode("utf-8"), b"catcolors"))

    def set_cat_color(self, name: str, color: str | None) -> None:
        if color:
            self.cat_colors[name] = color
        else:
            self.cat_colors.pop(name, None)
        self.save_cat_colors()

    def save_categories(self) -> None:
        _write_atomic(self.cat_file, crypto.seal(self.key, json.dumps(self.categories, ensure_ascii=False)
                                                 .encode("utf-8"), b"cats"))

    def all_categories(self) -> list[str]:
        names = list(self.categories)
        for n in self.notes.values():
            if n.category and n.category not in names:
                names.append(n.category)
        return names

    def add_category(self, name: str) -> None:
        if name and name not in self.categories:
            self.categories.append(name)
            self.save_categories()

    def rename_category(self, old: str, new: str) -> None:
        self.categories = [new if c == old else c for c in self.categories]
        if new not in self.categories:
            self.categories.append(new)
        self.categories = list(dict.fromkeys(self.categories))
        self.save_categories()
        if old in self.cat_colors:
            self.cat_colors[new] = self.cat_colors.pop(old)
            self.save_cat_colors()
        for n in list(self.notes.values()):
            if n.category == old:
                n.category = new
                self.save(n, touch=False, snapshot=False)

    def remove_category(self, name: str) -> None:
        self.categories = [c for c in self.categories if c != name]
        self.save_categories()
        if self.cat_colors.pop(name, None):
            self.save_cat_colors()
        for n in list(self.notes.values()):
            if n.category == name:
                n.category = ""
                self.save(n, touch=False, snapshot=False)

    # ------------------------------------------------------------ 로컬 백업
    def daily_backup(self, backup_dir: Path, keep: int = 14) -> Path | None:
        """하루 한 번 notes 폴더(암호화된 그대로)를 이 PC에 zip으로 보관."""
        backup_dir.mkdir(parents=True, exist_ok=True)
        target = backup_dir / f"notes-{time.strftime('%Y%m%d')}.zip"
        if target.exists():
            return None
        tmp = target.with_suffix(".tmp")
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_STORED) as z:
            for p in self.notes_dir.glob("*.own"):
                z.write(p, f"notes/{p.name}")
            for name in ("vault.json", "categories.own", "catcolors.own"):
                if (self.folder / name).exists():
                    z.write(self.folder / name, name)
        os.replace(tmp, target)
        for old in sorted(backup_dir.glob("notes-*.zip"))[:-keep]:
            try:
                old.unlink()
            except OSError:
                pass
        return target
