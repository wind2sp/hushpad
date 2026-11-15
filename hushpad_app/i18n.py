"""아주 작은 번역 층.

    from .i18n import tr
    tr("menu.file")                 → "파일" / "File" / "ファイル" / "文件"
    tr("st.trashed", n=3)           → 자리표시자 {n} 채우기. 값이 {"one": …, "other": …}면 n으로 고른다.

- 문구 목록: hushpad_app/locales/{ko,en,ja,zh}.json (UTF-8). 네 파일의 열쇠는 모두 같아야 한다(--selftest가 검사).
- 'key@mac' 열쇠가 있으면 macOS에서는 그 문구를 쓴다 (예: 'Windows 시작할 때 실행' → '로그인할 때 실행').
- 찾는 순서: 지금 언어 → 영어 → 한국어 → 열쇠 이름 그대로.
- 언어 설정(config "language"): "system"(기본) 또는 ko/en/ja/zh. 시스템 언어가 지원 목록에 없으면 영어.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SUPPORTED = ("ko", "en", "ja", "zh")
NATIVE_NAMES = {"ko": "한국어", "en": "English", "ja": "日本語", "zh": "简体中文"}
FALLBACK = ("en", "ko")

_catalogs: dict[str, dict] = {}
_lang = "en"


def locales_dir() -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return base / "hushpad_app" / "locales"


def catalog(lang: str) -> dict:
    if lang not in _catalogs:
        try:
            _catalogs[lang] = json.loads((locales_dir() / f"{lang}.json").read_text("utf-8"))
        except Exception:
            _catalogs[lang] = {}
    return _catalogs[lang]


def match(tag: str) -> str | None:
    """'ko-KR', 'zh-Hans-CN', 'ja_JP' 같은 언어 표기 → 지원 언어 (없으면 None)."""
    t = tag.replace("_", "-").lower()
    head = t.split("-")[0]
    if head in ("ko", "ja", "en"):
        return head
    if head == "zh":
        parts = t.split("-")[1:]
        if "hant" in parts or any(p in ("tw", "hk", "mo") for p in parts) and "hans" not in parts:
            return None          # 번체는 아직 없음 → 영어
        return "zh"
    return None


def system_language() -> str:
    try:
        from PySide6.QtCore import QLocale
        langs = QLocale.system().uiLanguages()
    except Exception:
        langs = []
    if langs:
        return match(langs[0]) or "en"
    return "en"


def resolve(setting: str | None) -> str:
    return setting if setting in SUPPORTED else system_language()


def set_language(lang: str) -> None:
    global _lang
    _lang = lang if lang in SUPPORTED else "en"


def current() -> str:
    return _lang


def _lookup(lang: str, key: str):
    cat = catalog(lang)
    if sys.platform == "darwin" and f"{key}@mac" in cat:
        return cat[f"{key}@mac"]
    return cat.get(key)


def tr_in(lang: str, key: str, /, **kw) -> str:
    v = None
    for lg in (lang,) + FALLBACK:
        v = _lookup(lg, key)
        if v is not None:
            break
    if v is None:
        return key
    if isinstance(v, dict):
        n = kw.get("n")
        v = v.get("one") if n == 1 and "one" in v else v.get("other", "")
    if kw:
        try:
            return v.format(**kw)
        except (KeyError, IndexError, ValueError):
            return v
    return v


def tr(key: str, /, **kw) -> str:
    return tr_in(_lang, key, **kw)


# ------------------------------------------------------------------ 날짜·시간 (Qt 날짜 형식 문자열을 문구 목록에 둔다)
_QLOCALE = {"ko": "ko_KR", "en": "en_US", "ja": "ja_JP", "zh": "zh_CN"}


def fmt_ts(ts: float, fmt_key: str) -> str:
    from PySide6.QtCore import QDateTime, QLocale
    dt = QDateTime.fromSecsSinceEpoch(int(ts))
    return QLocale(_QLOCALE.get(_lang, "en_US")).toString(dt, tr(fmt_key))
