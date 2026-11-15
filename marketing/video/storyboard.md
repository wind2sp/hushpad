# Hushpad 홍보 영상 — 스토리보드 / Storyboard

- 길이 79초 · 1920×1080 · 30fps · 배경 음악은 `make_music.py`로 직접 합성(84 BPM, 약 -18 LUFS) / 79 s · 1920×1080 · 30 fps · original procedural music
- 화면은 모두 `render_video.py`가 코드로 그림. 앱 화면은 일회용 시험 프로필에서 찍은 **실제 Hushpad 화면**(`capture_shots.py`).
  Everything is drawn by code; app shots are real Hushpad windows grabbed from a throwaway test profile.
- 한국어판은 한국어 앱 화면, 영어판·영어 쇼츠는 **영어 앱 화면**(capture_shots.py가 `i18n.set_language("en")`으로 찍음)과 영어 예시 메모.
  The Korean cut shows the Korean UI; the English cut and English Short show the English UI with English sample notes.
- 예시 데이터는 모두 가짜(`sk-test-…-not-real`, `test-only-Pa55`, `Spring-2026!demo`, "(예시)" 표시). 숫자·후기 없음. "무료·오픈소스"는 공개 후 사실이라 아웃트로·설명에 씀. 다른 회사 제품 이름·로고 없음(훅의 메모장은 직접 그린 일반 창).

## 훅 문구 후보 / Hook line options

| | 한국어 | English |
|---|---|---|
| **A (채택)** | 화면 공유 중인데, 비밀번호 메모가 떠 있다면? | Sharing your screen… with a password note open? |
| B | '제목 없음 (3)'… 그 비밀번호 어디 적었더라? | Untitled (3)… which tab had that password? |
| C | 방금 보낸 스크린샷에 메모장도 같이 찍혔어요. | That screenshot you just sent? Your notes are in it. |

A를 고른 이유: 누구나 겪을 법한 순간이고, 바로 이어지는 "캡처에 안 찍히는 창"과 한 줄로 이어짐. B는 탭 정리 문제라 핵심 기능과 거리가 있고, C는 상황 설명이 길어 3초 안에 안 읽힘.
Why A: a moment people recognize instantly, and it sets up the signature "hidden from capture" feature. B is about tab clutter (weaker link); C takes too long to read in 3 s.

## 장면표 / Shot list

| 시간 Time | 장면 Scene | 화면 Visual | 화면 글자(ko) | On-screen text (en) | 키 칩 Keys |
|---|---|---|---|---|---|
| 0:00–0:03.6 | 훅 Hook | 보라 배경화면 + 직접 그린 일반 메모장(특정 제품의 메뉴·상태 줄 없이 회색 점과 아이콘만). 비슷한 탭 5개(메모 1~5 / note 1–5), 본문에 가짜 비밀번호. 1.7초에 빨간 "화면 공유 중" 테두리, 2.6초 찰칵 플래시, 비밀번호 줄에 빨간 상자 + "다 보여요" | 화면 공유 중인데, 비밀번호 메모가 떠 있다면? | Sharing your screen… with a password note open? | — |
| 0:03.6–0:05 | 쉿 | 화면이 잉크색으로 어두워지고 복숭아색 "쉿." + 퍼지는 원 | 쉿. | Shh. | — |
| 0:05–0:07 | 로고 Logo | 자두색 그라데이션, 아이콘이 커지며 등장, "Hushpad" | 조용한 비밀 메모장 | A quiet notepad for private notes | — |
| 0:07–0:16 | 01 저장 버튼이 없어요 / No Save button | 실제 앱: 새 메모에 한 글자씩 입력되는 모습(실제 프레임 48~83장), 확대. 끝나면 상태 표시줄 "저장됨"에 링 + "자동 저장됨". 12.4초부터 디스크 파일 카드(파일 이름 + 16진수 + AES-256) | 저장 버튼은 없어요. 쓰면 바로 저장돼요 → 디스크에는 암호화된 파일로만 남아요 | There's no Save button. It saves as you type. → On disk, every note is AES-256 encrypted. | Ctrl+N |
| 0:16–0:27 | 02 캡처에 안 찍히는 창 / Hidden from screen capture | **나란히 두 화면.** 왼쪽 "내 화면": 바탕화면 + 문서 창 + Hushpad 창. 오른쪽 "스크린샷 · 화면 공유"(빨간 테두리): 같은 바탕화면인데 Hushpad 창이 없음. 19.3초 찰칵, 22초부터 그 자리에 점선 윤곽이 깜빡 | 내 화면에서는 그대로 보이는데 → 캡처하거나 화면을 공유하면 안 보여요 | You can see it on your screen, → but screenshots and screen shares can't. | — |
| 0:27–0:35 | 03 비밀 메모 / Secret notes | 실제 앱: 가림막이 덮인 비밀 메모 → 커서가 눌러 열림(가짜 키) → 확대. 31.4초 "30초 뒤 클립보드 비움" 카드(줄어드는 고리) | 비밀 메모는 열 때마다 가려져 있어요 → 복사한 내용은 30초 뒤 클립보드에서 지워져요 | Secret notes open hidden. Click to reveal. → Copy it, and the clipboard clears in 30 seconds. | Enter, Ctrl+C |
| 0:35–0:43 | 04 서식 그대로, 또는 글자만 / Copy rich or plain | 실제 앱: 서식 메모(굵게·색·목록). 카드 두 장: "붙여 넣으면 서식 그대로"(서식 렌더) / "붙여 넣으면 글자만"(고정폭 평문) | Ctrl+C로 복사하면 서식까지 그대로 → 글자만 필요하면 Ctrl+Shift+C | Ctrl+C copies it with the formatting. → Just the text? Ctrl+Shift+C. | Ctrl+C, Ctrl+Shift+C |
| 0:43–0:51 | 05 HTML·JSON 코드 메모 / Code notes | 어두운 테마. HTML 메모(줄 번호·색) → 한 줄 JSON → Ctrl+Alt+J 누름 → 정리된 JSON으로 바뀜 | HTML이나 JSON은 코드 메모에 붙여 두세요 → 한 줄로 엉킨 JSON은 Ctrl+Alt+J로 정리 | Paste HTML or JSON into a code note. → One-line JSON? Ctrl+Alt+J tidies it up. | Ctrl+Shift+N, Ctrl+Alt+J |
| 0:51–1:00 | 06 스크린샷과 짧은 녹화 / Screenshots and short recordings | 바탕화면이 어두워지고 커서가 영역을 끌어 고름(크기 표시) → 찰칵 → 실제 앱: 메모에 들어간 스크린샷 + 동영상 미리보기. 56.4초 동영상에 빨간 링 "REC ≤ 3:00" | 영역을 끌어서 찍으면 바로 메모에 들어가요 → 3분까지는 화면 녹화도 돼요 | Drag over an area, and the shot lands in your note. → Short screen recordings work too, up to 3 minutes. | Ctrl+Alt+S, Ctrl+Alt+R |
| 1:00–1:10 | 07 트레이에서도 되는 단축키 / Hotkeys that work from the tray | 바탕화면의 문서에서 한 줄 선택 → Ctrl+Alt+M → 오른쪽 아래 알림 "클립보드를 메모로 저장했어요 / 창은 열리지 않아요" → 실제 앱: 목록 맨 위에 새 메모(링) → Ctrl+K 찾기·명령 창(실제 화면) | Ctrl+Alt+M을 누르면 클립보드가 메모로 저장돼요 → 뭘 찾든 Ctrl+K | Ctrl+Alt+M saves whatever's on your clipboard as a note. → Looking for something? Ctrl+K. | Ctrl+Alt+M, Ctrl+K, Ctrl+Alt+N |
| 1:10–1:19 | 아웃트로 Outro | 자두색 배경, 아이콘, 태그라인, 주소 알약, "무료 · 오픈소스" 알약, 지원 OS 한 줄. 아래쪽은 종료 화면 요소 자리로 비워 둠 | 조용히 적고, 아무도 못 보게 / gdra.mycafe24.com/hushpad / 무료 · 오픈소스 / Windows 10/11 · macOS(Apple Silicon) | Write quietly. Seen by no one. / gdra.mycafe24.com/hushpad / Free & open source / Windows 10/11 · macOS (Apple Silicon) | — |

장면 사이는 0.35초 겹쳐 사라지기(cross-fade). 모든 움직임은 cubic ease-in-out / ease-out.
Scenes cross-fade over 0.35 s; all motion uses cubic easing.

## 쇼츠 / Shorts (shorts_ko.mp4 · shorts_en.mp4, 1080×1920, 30초)

| 시간 | 장면 |
|---|---|
| 0:00–0:06 | 훅(세로 배치) → 쉿 → 로고 |
| 0:06–0:14 | 02 캡처에 안 찍히는 창 — 위 "내 화면", 아래 "스크린샷 · 화면 공유" |
| 0:14–0:21 | 03 비밀 메모 — 가림막 열기 + 30초 클립보드 비움 |
| 0:21–0:27 | 01 저장 버튼이 없어요 — 입력 + 디스크 암호화 카드 |
| 0:27–0:30 | 아웃트로(태그라인, 주소, 무료 · 오픈소스, 지원 OS) |

## 소리 / Sound
- 0~3.6초(훅): 낮은 패드 한 화음만 아주 작게. 3.6초 화면이 어두워질 때 음악이 잦아들고 3.75초에 부드러운 "쉬—"(걸러 낸 잡음, 목소리 녹음 아님).
- 4.95초 로고와 함께 곡 시작: F장조 Fmaj7–Am7–Dm7–B♭maj7 반복, 패드 + 8분음표 플럭 + 베이스(둘째 마디부터). 끝은 Fmaj9로 맺고 마지막 3초 페이드아웃.
- 쇼츠는 같은 구성을 30초로(훅 시각은 6/7배: 쉬— 3.2초, 곡 시작 4.24초).

## 글 다듬기 원칙 / Copy rules applied
- 말하듯 짧게, 어미를 섞음(~돼요/~있어요/~세요/명사형). 번역투("~하는 것이 가능합니다", "~를 통해", "당신의") 없음.
- 과장어(혁신적인·강력한·완벽한·손쉽게·seamless·effortless 등)·느낌표·이모지 없음. 대시는 쓰지 않거나 최소.
- en·ja·zh 자막은 한국어 직역이 아니라 그 언어로 자연스럽게 따로 씀. 한 줄 길이: 영어 ≤42자, 일·중 ≤16자, 최대 2줄.
