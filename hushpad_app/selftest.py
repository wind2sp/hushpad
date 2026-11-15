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

    def check(name, fn):
        nonlocal ok
        try:
            r = fn()
            lines.append(f"PASS {name}" + (f" — {r}" if r else ""))
        except Exception as e:
            ok = False
            lines.append(f"FAIL {name}: {e!r}\n{traceback.format_exc()}")

    from PySide6.QtCore import QMimeData
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication(sys.argv)

    from . import crypto, notepad_import
    from .common import Config, resource
    from .store import Store

    def icons():
        for n in ("app.ico", "app.png", "app_small.png"):
            p = resource("assets", n)
            assert p.is_file() and p.stat().st_size > 100, p
        return "assets OK"
    check("icon files bundled", icons)

    def dpapi():
        assert crypto.dpapi_unprotect(crypto.dpapi_protect(b"secret-123")) == b"secret-123"
    check("DPAPI roundtrip", dpapi)

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
