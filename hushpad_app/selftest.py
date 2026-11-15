"""--selftest: 화면 없이 핵심 기능을 점검. 결과는 %TEMP%\\hushpad_selftest.txt"""
from __future__ import annotations

import os
import sys
import tempfile
import traceback
from pathlib import Path


def run() -> int:
    out = Path(tempfile.gettempdir()) / "hushpad_selftest.txt"
    lines, ok = [], True

    def check(name, fn, soft=False):
        """soft=True: 실패해도 전체 결과는 통과 (CI처럼 키체인이 없을 수 있는 환경)."""
        nonlocal ok
        try:
            r = fn()
            lines.append(f"PASS {name}" + (f" — {r}" if r else ""))
        except Exception as e:
            if soft:
                lines.append(f"WARN {name}: {e!r}")
                return
            ok = False
            lines.append(f"FAIL {name}: {e!r}\n{traceback.format_exc()}")

    from PySide6.QtCore import QMimeData
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from . import crypto, i18n, notepad_import, plat
    from .common import Config, resource
    from .store import Store

    def icons():
        names = ["app.ico", "app.png", "app_small.png"] + (["app.icns"] if plat.IS_MAC else [])
        for n in names:
            p = resource("assets", n)
            assert p.is_file() and p.stat().st_size > 100, p
        return "assets OK"
    check("icon files bundled", icons)

    def platform_layer():
        assert plat.select("win32") == "win" and plat.select("darwin") == "mac" and plat.select("linux") == "base"
        assert plat.NAME == plat.select()
        if not plat.IS_WIN:
            assert "hushpad_app.plat.win" not in sys.modules, "Windows-only module imported"
        return f"{plat.NAME} (keystore {plat.keystore_name or 'none'})"
    check("platform layer", platform_layer)

    def keystore():
        vid = "selftest-" + os.urandom(4).hex()
        k = os.urandom(32)
        crypto.remember_key(vid, k)
        try:
            if plat.IS_WIN or plat.IS_MAC:
                assert crypto.recall_key(vid) == k, "recall failed"
        finally:
            crypto.forget_key(vid)
        assert crypto.recall_key(vid) is None, "forget failed"
        if plat.IS_WIN:
            assert plat._impl.dpapi_unprotect(plat._impl.dpapi_protect(b"secret-123")) == b"secret-123"
        return plat.keystore_name
    check("key cache roundtrip", keystore, soft=not plat.IS_WIN)

    def catalogs():
        import re
        cats = {lg: i18n.catalog(lg) for lg in i18n.SUPPORTED}
        base = set(cats["ko"])
        assert len(base) > 200, f"ko catalog too small ({len(base)})"
        ph = re.compile(r"\{(\w+)")

        def holders(v):
            vals = v.values() if isinstance(v, dict) else [v]
            return {m for x in vals for m in ph.findall(x)}
        for lg, c in cats.items():
            missing, extra = base - set(c), set(c) - base
            assert not missing and not extra, f"{lg}: missing {sorted(missing)[:5]} extra {sorted(extra)[:5]}"
            for k, v in c.items():
                assert holders(v) == holders(cats["ko"][k]), f"{lg}:{k} placeholders differ"
                if isinstance(v, dict):
                    assert "other" in v, f"{lg}:{k} plural without 'other'"
        return f"{len(base)} keys × {len(cats)} languages"
    check("i18n catalogs", catalogs)

    def tr_fallback():
        saved = i18n.current()
        cs = {lg: i18n.catalog(lg) for lg in i18n.SUPPORTED}
        try:
            cs["en"]["__t.en"] = "EN"
            cs["ko"]["__t.en"] = "KO"
            cs["ko"]["__t.ko"] = "KO only"
            i18n.set_language("ja")
            assert i18n.tr("__t.en") == "EN", "no English fallback"
            assert i18n.tr("__t.ko") == "KO only", "no Korean fallback"
            assert i18n.tr("__t.none") == "__t.none"
            i18n.set_language("en")
            assert i18n.tr("st.trashed", n=1).startswith("Moved 1 note ")
            assert "3 notes" in i18n.tr("st.trashed", n=3)
            i18n.set_language("ko")
            assert i18n.tr("note.chars", n=1234) == "1,234자"
            assert i18n.match("ko-KR") == "ko" and i18n.match("zh-Hans-CN") == "zh" and i18n.match("zh-TW") is None
            assert i18n.match("ja_JP") == "ja" and i18n.match("de-DE") is None
        finally:
            for k in ("__t.en", "__t.ko"):
                for c in cs.values():
                    c.pop(k, None)
            i18n.set_language(saved)
        return "lang → en → ko → key"
    check("tr() fallback", tr_fallback)

    tmp = Path(tempfile.mkdtemp(prefix="hsp-selftest-"))

    def vault():
        k = crypto.create_vault(tmp, "pass-word-1")
        assert crypto.unlock_vault(tmp, "pass-word-1") == k
        try:
            crypto.unlock_vault(tmp, "wrong")
            raise AssertionError("wrong passphrase accepted")
        except crypto.BadPassphrase:
            pass
        crypto.change_passphrase(tmp, k, "new-pass-2")
        assert crypto.unlock_vault(tmp, "new-pass-2") == k
        return "create/unlock/change"
    check("vault", vault)

    key = crypto.unlock_vault(tmp, "new-pass-2")
    st = Store(tmp, key)

    def store():
        n = st.create(kind="text", text='{"api_key": "sk-TEST-0000"}')
        raw = (tmp / "notes" / f"{n.id}.own").read_bytes()
        assert b"sk-TEST" not in raw and b"api_key" not in raw, "plaintext on disk"
        n.text += "\nmore"
        st.save(n)
        st2 = Store(tmp, key)
        st2.load_all()
        assert st2.notes[n.id].text.endswith("more")
        st.trash([n.id]); assert st.notes[n.id].deleted
        st.restore([n.id]); assert st.notes[n.id].deleted is None
        mid = st.put_media(b"\0" * 1000)
        assert st.get_media(mid) == b"\0" * 1000
        assert st.history(n.id), "no snapshot"
        st.add_category("업무")
        st.load_categories(); assert "업무" in st.categories
        return f"encrypted file {len(raw)} bytes"
    check("store save/load/encrypt", store)

    def scan():
        a = Store(tmp, key); a.load_all()
        b = Store(tmp, key); b.load_all()
        n = a.create(text="from A")
        changed, removed = b.scan()
        assert n.id in changed, changed
        a.purge([n.id])
        changed, removed = b.scan()
        assert n.id in removed
    check("sync scan between two instances", scan)

    def np_parser():
        def uleb(v):
            b = bytearray()
            while True:
                x = v & 0x7F; v >>= 7
                b.append(x | (0x80 if v else 0))
                if not v:
                    return bytes(b)
        txt = "hello 메모"
        data = b"NP" + uleb(0) + uleb(0) + b"\x01" + uleb(3) + uleb(3) + b"\x01\x00\x00" + uleb(1) + b"\x00" \
            + uleb(len(txt)) + txt.encode("utf-16-le") + b"\x01" + b"\0\0\0\0" \
            + uleb(5) + uleb(0) + uleb(1) + "!".encode("utf-16-le") + b"\0\0\0\0"
        r = notepad_import.parse_tab(data)
        assert r and r[0] == "hello! 메모", r
    check("Notepad tab parser", np_parser)

    def editors():
        from .window import MainWindow
        from PySide6.QtGui import QIcon
        cfg = Config()
        cfg["open_tabs"] = []
        cfg.save = lambda: None
        w = MainWindow(st, cfg, QIcon())
        t = w.new_note("rich")
        md = QMimeData()
        md.setHtml("<b>굵은</b> 글")
        md.setText("굵은 글")
        t.edit.insertFromMimeData(md)
        assert "font-weight" in t.edit.toHtml() or "<b>" in t.edit.toHtml()
        w._force_plain = True
        md2 = QMimeData(); md2.setHtml("<i>기울임</i>"); md2.setText("기울임")
        t.edit.insertFromMimeData(md2)
        w._force_plain = False
        img = QImage(40, 20, QImage.Format_RGB32); img.fill(QColor("red"))
        md3 = QMimeData(); md3.setImageData(img)
        t.edit.insertFromMimeData(md3)
        t.dirty = True
        t.save()
        n = st.notes[t.note.id]
        assert "data:image/png;base64" in n.html, "image not stored"
        assert "굵은 글" in n.text and "기울임" in n.text
        code = w.new_note("text")
        code.edit.insertFromMimeData(md)
        assert code.edit.toPlainText() == "굵은 글"
        code.edit.setPlainText('{"a":1,"b":[1,2]}')
        w._json_apply(False)
        assert '\n  "a": 1' in code.edit.toPlainText()
        ids = [t.note.id, code.note.id]
        code.save()
        w.merge_confirm = False
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.No)
        before = len(st.notes)
        w.merge(ids)
        assert len(st.notes) == before + 1
        w.close()
        return "rich/plain/image paste, JSON, merge"
    check("editors", editors)

    def recorder_backend():
        from PySide6.QtMultimedia import QMediaRecorder, QMediaFormat  # noqa
        from PySide6.QtMultimediaWidgets import QVideoWidget  # noqa
        return "QtMultimedia OK"
    check("multimedia modules", recorder_backend)

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    out.write_text(("ALL PASS\n" if ok else "SOME FAILED\n") + "\n".join(lines), "utf-8")
    try:
        print(out.read_text("utf-8"))
    except Exception:
        pass
    return 0 if ok else 1
