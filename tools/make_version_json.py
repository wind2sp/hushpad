"""GitHub 릴리스에 함께 올릴 version.json 만들기 (zip판 자동 업데이트가 읽는 파일).

python tools/make_version_json.py <Hushpad-win64.zip> --notes notes.json [--important] [-o version.json]
notes.json = {"ko": ["…"], "en": ["…"], "ja": ["…"], "zh": ["…"]}
버전은 hushpad_app.__version__, zip 주소는 releases/download/v<버전>/<파일 이름>.
릴리스에는 zip을 먼저, version.json을 마지막에 올린다.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPO = "wind2sp/hushpad"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip")
    ap.add_argument("--notes", required=True)
    ap.add_argument("--important", action="store_true")
    ap.add_argument("-o", "--out", default="version.json")
    a = ap.parse_args()
    from hushpad_app import __version__
    z = Path(a.zip)
    data = z.read_bytes()
    notes = json.loads(Path(a.notes).read_text("utf-8"))
    for lang in ("ko", "en", "ja", "zh"):
        if not notes.get(lang):
            print(f"notes.json: '{lang}' is missing", file=sys.stderr)
            return 1
    info = {
        "version": __version__,
        "date": time.strftime("%Y-%m-%d"),
        "important": a.important,
        "notes": notes,
        "files": {"win": {"name": z.name,
                          "url": f"https://github.com/{REPO}/releases/download/v{__version__}/{z.name}",
                          "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}},
    }
    Path(a.out).write_text(json.dumps(info, ensure_ascii=False, indent=2) + "\n", "utf-8")
    print(f"{a.out}: {__version__} {len(data)} bytes {info['files']['win']['sha256']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
