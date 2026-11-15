"""Hushpad 실제 화면을 일회용 시험 프로필에서 찍는다 (사용자 실제 데이터는 쓰지 않음).

python capture_shots.py [en] [ko] [--profile 프로필 폴더]
  - 언어를 안 주면 en만 다시 찍는다(한국어판은 이미 찍어 둔 shots/ko를 그대로 씀). 앱 UI 언어도 그 언어로 바꿔서 찍는다.
  - 프로필 폴더(기본: %TEMP%\\hushpad_video_profile)를 매번 새로 만들고, 시험 보관 폴더·암호(test-pass-1234)를 만든다.
  - 가짜 예시 메모만 넣는다 (sk-test-… 등). 결과: shots/ko/*.png, shots/en/*.png
  - 창은 화면에 띄우지 않는다 (Qt.WA_DontShowOnScreen + grab).
"""
import os
import shutil
import sys
import json
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]                      # C:\build_temp\hushpad
_args = sys.argv[1:]
_prof = None
if "--profile" in _args:
    i = _args.index("--profile")
    _prof = _args[i + 1]
    del _args[i:i + 2]
LANGS = [a for a in _args if a in ("ko", "en")] or ["en"]
PROFILE = Path(_prof) if _prof else Path(tempfile.gettempdir()) / "hushpad_video_profile"
SCALE = 1.5                                 # 1280×760 창을 1920×1140 픽셀로 선명하게

if PROFILE.exists():
    shutil.rmtree(PROFILE)
PROFILE.mkdir(parents=True)
os.environ["HUSHPAD_PROFILE"] = str(PROFILE)
os.environ["QT_SCALE_FACTOR"] = str(SCALE)
sys.path.insert(0, str(ROOT))

from PySide6.QtCore import Qt, QPointF, QRectF, QMimeData            # noqa: E402
from PySide6.QtGui import (QIcon, QImage, QPainter, QColor, QFont, QLinearGradient,  # noqa: E402
                           QPainterPath, QPen)
from PySide6.QtWidgets import QApplication                            # noqa: E402

app = QApplication(sys.argv[:1])
app.setStyle("Fusion")

from hushpad_app import crypto                    # noqa: E402
from hushpad_app.common import Config             # noqa: E402
from hushpad_app.store import Store               # noqa: E402
from hushpad_app.window import MainWindow         # noqa: E402
from hushpad_app import capture                   # noqa: E402
from hushpad_app import i18n                      # noqa: E402

ICON = QIcon(str(ROOT / "assets" / "app.png"))
W, H = 1280, 760

TXT = {
    "ko": {
        "cats": ["업무", "API 키", "회의"],
        "meeting": ("주간 회의", "<h3>주간 회의</h3><p>이번 주 할 일: 배포 전 점검, 문서 정리</p><ul><li>로그인 오류 재현</li><li>릴리스 노트 초안</li></ul>"),
        "parcel": "택배 송장 번호 (예시) 0000-1111-2222",
        "secret": "DEMO_API_KEY=sk-test-4f9a2c7e-not-real\nDB_PASSWORD=test-only-Pa55\nSTAGING_TOKEN=tok_test_8d1e  # 가짜 예시",
        "rich": ("출시 체크리스트",
                 "<h3>출시 체크리스트</h3><p><b>아이콘</b> 최종본 확인 — <span style='color:#9B4DB5'><b>16px까지</b></span> 점검</p>"
                 "<ul><li><b>스크린샷</b> 새로 찍기</li><li>홈페이지 문구 <i>한 번 더</i> 읽기</li>"
                 "<li><a href='https://example.com'>안내 문서 링크</a> 확인</li></ul>"),
        "typing": "목요일 디자인 리뷰\n시안 B로 가기로 함\n아이콘 크기 다시 확인\n발표 자료는 금요일까지",
        "shot_title": "📷 캡처 11-15 14:32",
        "chart": "예시 화면",
        "clip": "회의실 예약 번호 (예시) A-1203\n내일 오후 3시, 2층 작은 회의실",
        "query": "json",
    },
    "en": {
        "cats": ["Work", "API keys", "Meetings"],
        "meeting": ("Weekly sync", "<h3>Weekly sync</h3><p>This week: pre-release checks, tidy up docs</p><ul><li>Reproduce login bug</li><li>Draft release notes</li></ul>"),
        "parcel": "Parcel tracking no. (sample) 0000-1111-2222",
        "secret": "DEMO_API_KEY=sk-test-4f9a2c7e-not-real\nDB_PASSWORD=test-only-Pa55\nSTAGING_TOKEN=tok_test_8d1e  # fake sample",
        "rich": ("Launch checklist",
                 "<h3>Launch checklist</h3><p>Final <b>icon</b> check — test <span style='color:#9B4DB5'><b>down to 16px</b></span></p>"
                 "<ul><li>Retake <b>screenshots</b></li><li>Read the homepage copy <i>once more</i></li>"
                 "<li>Check the <a href='https://example.com'>guide link</a></li></ul>"),
        "typing": "Thursday design review\nGoing with option B\nRecheck the icon sizes\nSlides due Friday",
        "shot_title": "📷 Capture 11-15 14:32",
        "chart": "Sample screen",
        "clip": "Room booking no. (sample) A-1203\nTomorrow 3 PM, small room on 2F",
        "query": "json",
    },
}
JSON_RAW = '{"project":"hushpad-demo","env":"test","features":["autosave","encrypt","hide-from-capture"],"retry":3,"debug":false}'
HTML_SNIP = '<section class="hero">\n  <h1>Hello, Hushpad</h1>\n  <p class="sub">Sample snippet</p>\n  <a href="#start">Start</a>\n</section>'


def sample_screen(label: str) -> QImage:
    """메모에 넣을 '스크린샷' — 숫자 없는 일반 그림."""
    img = QImage(1100, 560, QImage.Format_ARGB32)
    img.fill(QColor("#F5F4F7"))
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing)
    p.fillRect(0, 0, 1100, 56, QColor("#EDE6F2"))
    for i, c in enumerate(("#E0703F", "#FFB38A", "#9B4DB5")):
        p.setBrush(QColor(c)); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(30 + i * 24, 28), 7, 7)
    f = QFont("Malgun Gothic", 22, QFont.Bold); p.setFont(f); p.setPen(QColor("#1C1A1F"))
    p.drawText(QRectF(40, 80, 600, 50), Qt.AlignLeft | Qt.AlignVCenter, label)
    heights = [0.35, 0.55, 0.45, 0.7, 0.62, 0.85, 0.78]
    for i, h in enumerate(heights):
        g = QLinearGradient(0, 520 - 330 * h, 0, 520)
        g.setColorAt(0, QColor("#9B4DB5")); g.setColorAt(1, QColor("#7A3C93"))
        path = QPainterPath(); path.addRoundedRect(QRectF(70 + i * 90, 520 - 330 * h, 56, 330 * h), 8, 8)
        p.fillPath(path, g)
    p.setPen(QPen(QColor("#E0703F"), 5)); p.setBrush(Qt.NoBrush)
    pts = [QPointF(760 + i * 50, 470 - 40 * ((i * 7) % 5)) for i in range(6)]
    for a, b in zip(pts, pts[1:]):
        p.drawLine(a, b)
    p.setBrush(QColor("#FFB38A")); p.setPen(Qt.NoPen)
    p.drawRoundedRect(QRectF(740, 150, 300, 22), 11, 11)
    p.setBrush(QColor("#E3DDE8")); p.drawRoundedRect(QRectF(740, 190, 240, 22), 11, 11)
    p.drawRoundedRect(QRectF(740, 230, 270, 22), 11, 11)
    p.end()
    return img


def plain(html: str) -> str:
    from PySide6.QtGui import QTextDocument
    d = QTextDocument(); d.setHtml(html)
    return d.toPlainText()


def build(lang: str, out: Path):
    T = TXT[lang]
    i18n.set_language(lang)                 # 창을 만들기 전에 앱 UI 언어를 정함 (hushpad_main.py와 같은 순서)
    out.mkdir(parents=True, exist_ok=True)
    data = PROFILE / f"data_{lang}"
    data.mkdir()
    key = crypto.create_vault(data, "test-pass-1234")
    crypto.remember_key(crypto.vault_id(data), key)
    (PROFILE / "config.json").write_text(json.dumps({"data_dir": str(data), "hide_from_capture": False, "language": lang}), "utf-8")
    cfg = Config()
    cfg.save = lambda: None
    st = Store(data, key)
    st.load_all()
    for c in T["cats"]:
        st.add_category(c)
    work, keys, meet = T["cats"]
    import time
    now = time.time()
    n_parcel = st.create("rich", "", text=T["parcel"], created=now - 7200)
    n_html = st.create("text", work, text=HTML_SNIP, created=now - 6000)
    n_json = st.create("text", work, text=JSON_RAW, created=now - 5000)
    n_secret = st.create("text", keys, text=T["secret"], created=now - 4000)
    n_secret.secret = True; st.save(n_secret)
    n_rich = st.create("rich", work, html=T["rich"][1], text=plain(T["rich"][1]), created=now - 3000)
    n_meet = st.create("rich", meet, html=T["meeting"][1], text=plain(T["meeting"][1]), created=now - 2000)
    n_meet.pinned = True; st.save(n_meet)

    def window(mode):
        cfg["theme"] = mode
        cfg["open_tabs"] = []
        w = MainWindow(st, cfg, ICON)
        w.resize(W, H)
        w.setAttribute(Qt.WA_DontShowOnScreen, True)
        w.palette_dlg.setAttribute(Qt.WA_DontShowOnScreen, True)
        w.show()
        app.processEvents()
        return w

    def shot(w, name):
        for _ in range(3):
            app.processEvents()
        w.grab().save(str(out / f"{name}.png"))

    def close(w):
        for k in range(w.tabs.count()):
            w.tabs.widget(k).save()
            w.tabs.widget(k).dirty = False
        w._quitting = True
        w._unregister_hotkeys()
        try:
            w.tray.hide()
        except Exception:
            pass
        w.close()
        app.processEvents()

    # ---------------- 밝게: 메인, 타이핑, 비밀 메모, 서식 메모, 미디어, 클립보드
    w = window("light")
    for n in (n_parcel, n_rich, n_meet):
        w.open_note(n.id)
    shot(w, "main")
    tab = w.new_note("rich")
    w.refresh_list()
    shot(w, "type_000")
    text = T["typing"]
    for i, ch in enumerate(text, 1):
        tab.edit.insert_plain(ch)
        w.update_status()
        shot(w, f"type_{i:03d}")
    tab.save(); w.refresh_list(); w.update_status()
    shot(w, "type_saved")
    (out / "type_count.txt").write_text(str(len(text)), "utf-8")

    w.open_note(n_secret.id)
    shot(w, "secret_cover")
    w._cur_tab().uncover()
    shot(w, "secret_open")

    w.open_note(n_rich.id)
    shot(w, "rich")

    media = st.create("rich", work, text=T["shot_title"], html=f"<p>{T['shot_title']}</p>")
    w.open_note(media.id)
    t = w._cur_tab()
    c = t.edit.textCursor(); c.movePosition(c.MoveOperation.End); t.edit.setTextCursor(c)
    t.edit.insert_plain("\n")
    t.edit.insert_image(sample_screen(T["chart"]).scaledToWidth(330, Qt.SmoothTransformation))
    t.edit.insert_plain("   ")
    mid = st.put_media(b"demo-not-a-real-video")
    t.edit.insert_image(capture.video_thumbnail(sample_screen(T["chart"]), 12).scaledToWidth(330, Qt.SmoothTransformation),
                        href=f"owvideo:{mid}")
    t.save(); w.refresh_list()
    t.edit.verticalScrollBar().setValue(0)
    shot(w, "media")

    md = QMimeData(); md.setText(T["clip"])
    QApplication.clipboard().setMimeData(md)
    w.clip_to_note()
    QApplication.clipboard().clear()
    w.refresh_list()
    newest = max(st.notes.values(), key=lambda n: n.created)
    w.open_note(newest.id, preview=True)
    w._select_in_list(newest.id)
    shot(w, "clip")
    w.open_palette()
    app.processEvents()
    w.palette_dlg.grab().save(str(out / "palette_l.png"))
    w.palette_dlg.close()
    close(w)

    # ---------------- 어둡게: 코드 메모, Ctrl+K
    w = window("dark")
    w.open_note(n_html.id)
    shot(w, "html")
    w.open_note(n_json.id)
    shot(w, "json_raw")
    w.json_pretty()
    w._cur_tab().save(); w.update_status()
    shot(w, "json_pretty")
    shot(w, "palette_bg")
    w.open_palette()
    w.palette_dlg.inp.setText(T["query"])
    app.processEvents()
    w.palette_dlg.grab().save(str(out / "palette.png"))
    w.palette_dlg.close()
    close(w)


if __name__ == "__main__":
    for lang in LANGS:
        build(lang, HERE / "shots" / lang)
    print("ok", PROFILE)
    os._exit(0)
