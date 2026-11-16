r"""Store 스크린샷 다시 만들기 (1920x1080, 언어마다 5장).

    $env:HUSHPAD_PROFILE = "<비어 있는 임시 폴더>"     # 실제 설정·메모를 건드리지 않게 반드시 일회용 프로필
    python packaging\msix\store_listing\make_screenshots.py ko packaging\msix\store_listing\screenshots\ko

프로필 안에 가짜 메모만 든 새 보관 폴더(data_<언어>)를 만들어 찍는다. 창은 화면에 띄우지 않고,
트레이 아이콘과 전역 단축키도 등록하지 않는다."""
import os
import sys
import time

os.environ["QT_SCALE_FACTOR"] = "1.5"          # 1280x720 논리 크기 → 1920x1080 그림
lang, out = sys.argv[1], sys.argv[2]
repo = str(__import__("pathlib").Path(__file__).resolve().parents[3])
sys.path.insert(0, repo)
if not os.environ.get("HUSHPAD_PROFILE"):
    sys.exit("set HUSHPAD_PROFILE to an empty temporary folder first (never your real profile)")
from pathlib import Path
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

app = QApplication(sys.argv)
app.setStyle("Fusion")
QSystemTrayIcon.isSystemTrayAvailable = staticmethod(lambda: False)   # 트레이 아이콘 띄우지 않음

from hushpad_app import crypto, i18n
from hushpad_app.common import Config
i18n.set_language(lang)
from hushpad_app.store import Store
from hushpad_app import window as W
W.MainWindow._register_hotkeys = lambda self: None                   # 전역 단축키 등록 안 함

prof = Path(os.environ["HUSHPAD_PROFILE"])
folder = prof / f"data_{lang}"
if folder.exists():
    import shutil
    shutil.rmtree(folder)
folder.mkdir(parents=True)
key = crypto.create_vault(folder, "sample-only-" + lang)
st = Store(folder, key)

S = {
    "ko": dict(
        cats=["업무", "개인", "개발"],
        meeting=("주간 회의 메모",
                 "<h2>주간 회의 메모</h2><p><b>11월 셋째 주</b> · 디자인팀, 개발팀</p>"
                 "<ul><li>새 온보딩 화면 시안 확정 — <i>금요일까지</i> 공유</li>"
                 "<li>베타 사용자 피드백 23건 정리, 우선순위 상위 5건만 이번 주에 처리</li>"
                 "<li>다음 회의: 목요일 오전 10시</li></ul>"
                 "<p>할 일</p><p>☑ 회의록 공유<br>☐ 일정표 다시 보내기<br>☐ 예산안 초안 검토</p>"),
        trip=("제주 여행 준비물", "제주 여행 준비물\n여권 대신 신분증, 충전기, 우산, 선크림"),
        parcel=("택배 송장 번호", "택배 송장 번호\n0000-1111-2222 (예시)"),
        books=("읽고 싶은 책", "읽고 싶은 책\n· 소설 두 권\n· 디자인 입문서"),
        secret=("공유기 관리자 암호", "공유기 관리자 암호\nadmin / example-pass-0000"),
        code_title="api 설정 (예시)", query="회의",
    ),
    "en": dict(
        cats=["Work", "Personal", "Dev"],
        meeting=("Weekly meeting notes",
                 "<h2>Weekly meeting notes</h2><p><b>Week 3, November</b> · Design, Engineering</p>"
                 "<ul><li>Lock the new onboarding mockups — share by <i>Friday</i></li>"
                 "<li>Sorted 23 pieces of beta feedback; only the top 5 go into this week</li>"
                 "<li>Next meeting: Thursday, 10 a.m.</li></ul>"
                 "<p>To do</p><p>☑ Send out the minutes<br>☐ Resend the schedule<br>☐ Review the draft budget</p>"),
        trip=("Packing list for Lisbon", "Packing list for Lisbon\nPassport, charger, umbrella, sunscreen"),
        parcel=("Parcel tracking number", "Parcel tracking number\n0000-1111-2222 (sample)"),
        books=("Books to read", "Books to read\n· Two novels\n· An intro to typography"),
        secret=("Router admin password", "Router admin password\nadmin / example-pass-0000"),
        code_title="api config (sample)", query="meeting",
    ),
    "ja": dict(
        cats=["仕事", "個人", "開発"],
        meeting=("週次ミーティングのメモ",
                 "<h2>週次ミーティングのメモ</h2><p><b>11月第3週</b> · デザイン、開発</p>"
                 "<ul><li>新しいオンボーディング画面の案を確定 — <i>金曜まで</i>に共有</li>"
                 "<li>ベータ版のフィードバック23件を整理、上位5件だけ今週対応</li>"
                 "<li>次回：木曜 午前10時</li></ul>"
                 "<p>やること</p><p>☑ 議事録を共有<br>☐ 日程表を再送<br>☐ 予算案の下書きを確認</p>"),
        trip=("京都旅行の持ち物", "京都旅行の持ち物\n身分証、充電器、折りたたみ傘、日焼け止め"),
        parcel=("宅配便の追跡番号", "宅配便の追跡番号\n0000-1111-2222（サンプル）"),
        books=("読みたい本", "読みたい本\n・小説を2冊\n・デザインの入門書"),
        secret=("ルーターの管理者パスワード", "ルーターの管理者パスワード\nadmin / example-pass-0000"),
        code_title="api 設定（サンプル）", query="ミーティング",
    ),
    "zh": dict(
        cats=["工作", "个人", "开发"],
        meeting=("每周例会记录",
                 "<h2>每周例会记录</h2><p><b>11 月第 3 周</b> · 设计组、开发组</p>"
                 "<ul><li>确定新的引导页方案，<i>周五前</i>发给大家</li>"
                 "<li>整理了 23 条内测反馈，本周只处理前 5 条</li>"
                 "<li>下次例会：周四上午 10 点</li></ul>"
                 "<p>待办</p><p>☑ 发送会议纪要<br>☐ 重新发送日程表<br>☐ 审阅预算草案</p>"),
        trip=("杭州出行清单", "杭州出行清单\n身份证、充电器、雨伞、防晒霜"),
        parcel=("快递单号", "快递单号\n0000-1111-2222（示例）"),
        books=("想读的书", "想读的书\n· 两本小说\n· 一本设计入门书"),
        secret=("路由器管理员密码", "路由器管理员密码\nadmin / example-pass-0000"),
        code_title="api 配置（示例）", query="例会",
    ),
}[lang]

CODE = """{
  "service": "example-notes",
  "endpoint": "https://api.example.com/v1",
  "api_key": "sk-test-0000-EXAMPLE-ONLY",
  "timeout_sec": 30,
  "retry": { "count": 3, "backoff": [1, 2, 4] },
  "features": ["sync", "export", "search"]
}"""

now = time.time()
for c in S["cats"]:
    st.add_category(c)
work, personal, dev = S["cats"]
html = S["meeting"][1]
import re
plain = re.sub(r"<[^>]+>", "\n", html)
plain = "\n".join(x for x in (ln.strip() for ln in plain.splitlines()) if x)
meeting = st.create("rich", work, text=plain, html=html, created=now - 3600)
meeting.pinned = True
st.save(meeting, touch=False, snapshot=False)
code = st.create("text", dev, text=CODE, title=S["code_title"], created=now - 7200)
trip = st.create("rich", personal, text=S["trip"][1], created=now - 86400 * 2)
parcel = st.create("text", personal, text=S["parcel"][1], created=now - 86400 * 3)
books = st.create("rich", personal, text=S["books"][1], created=now - 86400 * 6)
secret = st.create("text", personal, text=S["secret"][1], created=now - 86400 * 9)
secret.secret = True
st.save(secret, touch=False, snapshot=False)
for n, ts in ((meeting, now - 600), (code, now - 3000), (trip, now - 86400 * 2), (parcel, now - 86400 * 3),
              (books, now - 86400 * 6), (secret, now - 86400 * 9)):
    n.updated = ts
    st.save(n, touch=False, snapshot=False)
st.load_all()

cfg = Config()
cfg.save = lambda: None
cfg["data_dir"] = str(folder)
cfg["hide_from_capture"] = False
icon = QIcon(str(Path(repo) / "assets" / "app.png"))
outd = Path(out)
outd.mkdir(parents=True, exist_ok=True)


def make(theme_mode, tabs, current):
    cfg["theme"] = theme_mode
    cfg["open_tabs"] = []
    w = W.MainWindow(st, cfg, icon)
    w.resize(1280, 720)
    w.setAttribute(Qt.WA_DontShowOnScreen, True)
    w.show()
    for nid in tabs:
        w.open_note(nid)
    if current:
        w.open_note(current)
    app.processEvents()
    return w


def done(w):
    for k in range(w.tabs.count()):
        w.tabs.widget(k).dirty = False
    w._quitting = True
    w.close()
    app.processEvents()


def save(pix: QPixmap, name):
    img = pix.toImage()
    assert (img.width(), img.height()) == (1920, 1080), (name, img.width(), img.height())
    img.save(str(outd / f"{name}.png"))


# 1) 서식 메모 (밝게)
w = make("light", [trip.id, code.id], meeting.id)
save(w.grab(), "1-rich-light")
done(w)

# 2) 코드 메모 JSON (어둡게)
w = make("dark", [meeting.id, trip.id], code.id)
shot2 = w.grab()
save(shot2, "2-code-dark")
# 3) Ctrl+K 찾기·명령 (어둡게) — 두 번째 grab은 코드 편집기 글자가 비어 나와서 위 그림 위에 겹친다
base = shot2.copy()
w.open_palette()
app.processEvents()
pal = w.palette_dlg.grab()
p = QPainter(base)
x = (1280 - w.palette_dlg.width()) // 2
p.drawPixmap(QPoint(x, 70), pal)
p.end()
w.palette_dlg.close()
save(base, "3-palette-dark")
done(w)

# 4) 비밀 메모 가림막 (밝게)
w = make("light", [meeting.id, code.id], secret.id)
save(w.grab(), "4-secret-light")
done(w)

# 5) 빈 화면 (어둡게) — 탭을 모두 닫은 상태
w = make("dark", [], None)
save(w.grab(), "5-empty-dark")
done(w)
print("ok", lang, outd)
