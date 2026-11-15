"""Render real Hushpad screenshots for the SNS cards — from a disposable test profile only.

Usage (PowerShell):
  $env:HUSHPAD_PROFILE = "<copy of a test profile>"   # config.json "data_dir" must point at its own data folder
  python marketing/shots/render_shots.py marketing/shots              # Korean UI + Korean sample notes
  python marketing/shots/render_shots.py marketing/shots/en --lang en # English UI + English sample notes

Use a fresh profile copy per language (the sample notes and folder names are written in that language).
It adds clearly fake sample notes (sk-test-…, *.test domains) to that profile once, then grabs
off-screen (Qt.WA_DontShowOnScreen) windows with real fonts. Never point it at a real vault.
"""
import argparse
import base64
import io
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
if not os.environ.get("HUSHPAD_PROFILE"):
    sys.exit("HUSHPAD_PROFILE is not set — refusing to touch a real profile.")

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", default=".")
ap.add_argument("--lang", choices=["ko", "en"], default="ko")
args = ap.parse_args()
LANG = args.lang

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QIcon  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication(sys.argv[:1])
app.setStyle("Fusion")
from hushpad_app import crypto, i18n  # noqa: E402

i18n.set_language(LANG)   # before any window module builds its strings
from hushpad_app.common import Config  # noqa: E402
from hushpad_app.store import Store  # noqa: E402
from hushpad_app.window import MainWindow  # noqa: E402

cfg = Config()
cfg.save = lambda: None
cfg["language"] = LANG
folder = Path(cfg["data_dir"])
st = Store(folder, crypto.recall_key(crypto.vault_id(folder)))
st.load_all()
st.load_categories()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)

# Sample text per language (all values are fake / test-only).
S = {
    "ko": dict(
        mark="출장 준비 체크리스트",
        cats=("업무", "개발", "출장"),
        rename={},
        login=("로그인", "이메일", "비밀번호", "비밀번호가 올바르지 않습니다 (E-401)"),
        secret="결제 테스트 서버 계정 (테스트 전용)\nadmin / test-only-Plum!2026\nPAY_API_KEY=sk-test-51Hq9ZtE2vXk7Lw0aR\n",
        env_head="# .env — 스테이징 (가짜 값, 테스트 전용)\n",
        trip=("<h2>출장 준비 체크리스트</h2>"
              "<p><b>11월 20일(목)</b> 부산 · KTX 07:30 출발</p>"
              "<ul><li>노트북 충전기 · <span style='color:#9B4DB5'><b>발표 자료 최종본</b></span></li>"
              "<li>숙소 예약 확인 — <u>체크인 15:00</u></li>"
              "<li>명함 30장</li></ul>"
              "<p style='color:#6b6b6b'>웹에서 복사한 표·글자 모양이 그대로 남아요.</p>"
              "<table border='1' cellpadding='6' style='border-collapse:collapse'>"
              "<tr><th>시간</th><th>일정</th></tr>"
              "<tr><td>10:30</td><td>고객사 미팅</td></tr>"
              "<tr><td>14:00</td><td>현장 점검</td></tr></table>"),
        bug_title="로그인 화면 버그 재현",
        bug=("<p><b>로그인 화면 버그 재현</b></p><p>올바른 비밀번호인데 E-401 — 스테이징만 그럼</p>"
             "<p><img src='{img}'></p><p>재현: 브라우저 시크릿 창 · 두 번째 시도부터</p>"),
        meet_link="회의 링크 https://meet.example.test/abc-defg-hij\n",
        clip="“배송은 영업일 기준 2~3일 걸립니다.”\n",
        clip_find="배송은",
        stock={},
    ),
    "en": dict(
        mark="Business trip checklist",
        cats=("Work", "Dev", "Travel"),
        # folders and notes that come with the stock test profile
        rename={"업무": "Work", "API 키": "API keys", "회의": "Meetings"},
        login=("Sign in", "Email", "Password", "Incorrect password (E-401)"),
        secret="Payment test server account (test only)\nadmin / test-only-Plum!2026\nPAY_API_KEY=sk-test-51Hq9ZtE2vXk7Lw0aR\n",
        env_head="# .env — staging (fake values, test only)\n",
        trip=("<h2>Business trip checklist</h2>"
              "<p><b>Thu, Nov 20</b> Busan · KTX departs 07:30</p>"
              "<ul><li>Laptop charger · <span style='color:#9B4DB5'><b>final slide deck</b></span></li>"
              "<li>Confirm hotel booking — <u>check-in 15:00</u></li>"
              "<li>30 business cards</li></ul>"
              "<p style='color:#6b6b6b'>Tables and formatting copied from the web stay as they are.</p>"
              "<table border='1' cellpadding='6' style='border-collapse:collapse'>"
              "<tr><th>Time</th><th>Plan</th></tr>"
              "<tr><td>10:30</td><td>Client meeting</td></tr>"
              "<tr><td>14:00</td><td>Site check</td></tr></table>"),
        bug_title="Login screen bug repro",
        bug=("<p><b>Login screen bug repro</b></p><p>Right password, still E-401. Staging only</p>"
             "<p><img src='{img}'></p><p>Steps: private browser window · from the second try</p>"),
        meet_link="Meeting link https://meet.example.test/abc-defg-hij\n",
        clip="“Delivery takes 2–3 business days.”\n",
        clip_find="Delivery takes",
        stock={"택배": ("Parcel tracking no. 6894-2231-0045", "<p>Parcel tracking no. 6894-2231-0045</p>"),
               "주간 회의": ("Weekly meeting\nThis week's to-do: pre-release check, tidy up the docs\n"
                          "Reproduce the login error\nDraft the release notes",
                          "<h2>Weekly meeting</h2><p>This week's <b>to-do</b>: pre-release check, tidy up the docs</p>"
                          "<ul><li>Reproduce the login error</li><li>Draft the release notes</li></ul>")},
    ),
}[LANG]
MARK = S["mark"]


def fake_screenshot_png() -> str:
    """A made-up web login error screen (my-shop.test), drawn with Pillow."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 700, 430
    title, l_mail, l_pw, err = S["login"]
    im = Image.new("RGB", (W, H), "#F3F4F6")
    d = ImageDraw.Draw(im)
    f = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf" if b else r"C:\Windows\Fonts\malgun.ttf", s)
    d.rectangle([0, 0, W, 44], fill="#E5E7EB")
    for i, c in enumerate(("#EF4444", "#F59E0B", "#22C55E")):
        d.ellipse([16 + i * 22, 16, 28 + i * 22, 28], fill=c)
    d.rounded_rectangle([96, 10, W - 20, 34], 12, fill="#FFFFFF")
    d.text((112, 13), "https://my-shop.test/login", font=f(14), fill="#6B7280")
    d.rounded_rectangle([170, 74, W - 170, H - 30], 14, fill="#FFFFFF", outline="#E5E7EB")
    d.text((206, 96), title, font=f(24, True), fill="#111827")
    for y, lab, val in ((150, l_mail, "tester@my-shop.test"), (222, l_pw, "••••••••••")):
        d.text((206, y), lab, font=f(13), fill="#6B7280")
        d.rounded_rectangle([206, y + 22, W - 206, y + 56], 8, fill="#FFFFFF",
                            outline="#EF4444" if lab == l_pw else "#D1D5DB", width=2)
        d.text((248, y + 29), val, font=f(15), fill="#111827")
    d.text((206, 284), err, font=f(13), fill="#DC2626")
    d.rounded_rectangle([206, 318, W - 206, 356], 8, fill="#2563EB")
    d.text((W // 2, 337), title, font=f(15, True), fill="#FFFFFF", anchor="mm")
    buf = io.BytesIO()
    im.save(buf, "PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def seed():
    if any(MARK in n.text for n in st.notes.values()):
        return
    # a day ago, so the list shows "n hours ago" whatever time it is run (not future "just now")
    today = time.time() - 24 * 3600
    at = lambda h, m: today + h * 3600 + m * 60
    for old, new in S["rename"].items():
        if old in st.all_categories():
            st.rename_category(old, new)
    st.load_all()
    for c in S["cats"]:
        if c not in st.all_categories():
            st.add_category(c)
    # replace the stock notes' text (secret note: clearly fake, brand-free values)
    for n in list(st.notes.values()):
        if n.secret:
            n.text = S["secret"]
            st.save(n)
            continue
        for start, (text, html) in S["stock"].items():
            if n.text.startswith(start):
                n.text, n.html = text, html
                st.save(n)
    work, dev, trip = S["cats"]
    st.create("text", dev, title="", created=at(9, 12), text=(
        S["env_head"] +
        "APP_ENV=staging\n"
        "API_BASE_URL=https://api.my-shop.test/v2\n"
        "PAY_API_KEY=sk-test-51Hq9ZtE2vXk7Lw0aR3m\n"
        "DB_PASSWORD=test-only-Plum!2026\n"
        "WEBHOOK_SECRET=whsec_test_8f2c1d7a9b\n"
        "SESSION_TTL=3600\n"))
    st.create("text", dev, created=at(10, 41), text=(
        '{\n  "order_id": "A-20261115-0042",\n  "status": "paid",\n  "amount": 39000,\n'
        '  "currency": "KRW",\n  "items": [\n    { "sku": "PAD-01", "qty": 1 },\n'
        '    { "sku": "PAD-02", "qty": 2 }\n  ],\n  "test_mode": true\n}\n'))
    st.create("rich", trip, created=at(11, 5), text=MARK, html=S["trip"])
    st.create("rich", work, created=at(13, 26), text=S["bug_title"], html=S["bug"].format(img=fake_screenshot_png()))
    st.create("text", work, created=at(14, 3), text=S["meet_link"])
    for n in list(st.notes.values()):   # spread "last edited" over the day instead of all "just now"
        n.updated = n.created + 600
        st.save(n, touch=False, snapshot=False)
    # what Ctrl+Alt+M produces for plain copied text: a text note, created "just now"
    st.create("text", "", text=S["clip"])
    st.load_all()


seed()


def find(t):
    return next(n.id for n in st.notes.values() if t in n.text and n.deleted is None)


def window(mode, w=1280, h=780):
    cfg["theme"] = mode
    cfg["open_tabs"] = []
    win = MainWindow(st, cfg, QIcon(str(ROOT / "assets" / "app.png")))
    win.resize(w, h)
    win.setAttribute(Qt.WA_DontShowOnScreen, True)
    win.show()
    return win


def done(win):
    for k in range(win.tabs.count()):
        win.tabs.widget(k).dirty = False
    win._quitting = True
    win._unregister_hotkeys()
    win.close()


def shot(mode, opens, name, w=1280, h=780, palette=False):
    win = window(mode, w, h)
    for t in opens:
        win.open_note(find(t))
    app.processEvents()
    win.grab().save(str(out / f"{name}.png"))
    if palette:
        win.open_palette()
        app.processEvents()
        win.palette_dlg.grab().save(str(out / f"{name}_palette.png"))
        win.palette_dlg.close()
    done(win)


BUG = S["bug_title"][:8]
SECRET = "PAY_API_KEY=sk-test-51Hq9ZtE2vXk7Lw0aR\n"
shot("light", (BUG, '"order_id"', MARK), "rich_light")
shot("dark", (BUG, '"order_id"', MARK), "rich_dark")
shot("dark", (MARK, '"order_id"', "APP_ENV"), "env_dark")
shot("light", (MARK, "APP_ENV", '"order_id"'), "json_light")
shot("dark", (MARK, '"order_id"'), "json_dark", palette=True)
shot("light", (MARK, SECRET), "secret_light")
shot("dark", (MARK, SECRET), "secret_dark")
shot("light", (MARK, BUG), "capture_light")
shot("dark", (MARK, BUG), "capture_dark")
shot("light", (MARK, S["clip_find"]), "clip_light")
print("ok", sorted(p.name for p in out.glob("*.png")))
