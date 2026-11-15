# Hushpad 홍보 문구

> 아직 아무 곳에도 게시하지 않은 초안입니다. 올리기 전에 메인 개발자가 확인합니다.
> 사실만 씁니다. Hushpad는 무료 오픈소스(GPL-3.0-or-later)입니다. 사용자 수·후기·다른 제품 이름은 쓰지 않습니다.
> 행동 유도는 모두 홈페이지 https://gdra.mycafe24.com/hushpad/ ("지금 받기" · "Get it free")로 보냅니다. 파일은 GitHub 릴리스(https://github.com/wind2sp/hushpad/releases/latest)로 배포합니다.

고정 문구 (영상 팀과 같음)

| | 한국어 | English |
|---|---|---|
| 태그라인 | 조용히 적고, 아무도 못 보게 | Write quietly. Seen by no one. |
| 이름 | Hushpad(허시패드) = hush(쉿) + pad(메모장) | Hushpad = hush + pad |
| 플랫폼 | Windows 10·11 · Apple Silicon(M1 이후) Mac. Intel Mac용은 없음 | Windows 10 & 11 · Macs with Apple silicon (M1 or later). No Intel Mac build |
| 라이선스 | 무료 오픈소스 (GPL-3.0-or-later) | Free and open source (GPL-3.0-or-later) |
| 배포 형태 | GitHub 릴리스. Windows는 설치 없이 압축 풀고 실행하는 포터블 앱 | GitHub Releases. On Windows, a portable app: unzip and run |
| 언어 | 앱 화면 언어 선택(한국어·English·日本語·简体中文) | App UI in Korean, English, Japanese and Simplified Chinese |

---

# 한국어

## 한 줄 소개

쓰는 대로 저장되고 파일은 전부 암호화되는 Windows·macOS용 무료 메모장. Windows에서는 화면을 공유해도 이 창이 상대에게 보이지 않습니다.

## 헤드라인 후보

1. 조용히 적고, 아무도 못 보게
2. 메모장 탭에 적어 둔 API 키, 화면 공유 때 들킨 적 있나요?
3. Windows에서 화면을 공유해도 상대 화면엔 안 나오는 메모장

## 짧은 설명 (약 80자)

암호, API 키, 붙여넣기 전 HTML·JSON을 잠깐 적어 두는 메모장. 저장 버튼 없이 쓰는 대로 남고, Windows에서는 캡처나 화면 공유에 창이 찍히지 않습니다. Windows와 Mac에서 쓰는 무료 오픈소스입니다.

## 긴 설명

Windows 메모장 탭에 이것저것 적어 두는 사람이 많습니다. 서버 비밀번호, 테스트용 API 키, 고객사에 보낼 HTML 조각, 방금 복사한 주소 같은 것들이요. 편하긴 한데 탭이 서른 개쯤 쌓이면 제목이 다 "제목 없음"이라 찾을 수가 없고, PC가 갑자기 꺼지고 나면 내용이 남아 있는지 불안합니다. 회의에서 화면을 공유하다가 그 탭이 잠깐 비치기라도 하면 더 곤란하고요.

Hushpad는 그런 메모를 위해 만든 메모장입니다. 쓰는 동안 알아서 저장되고, 제목을 안 붙여도 만든 시각으로 구분됩니다. 모든 메모는 내가 고른 폴더 한 곳에 AES-256-GCM으로 암호화된 파일로 저장되므로, 그 폴더가 클라우드에 동기화돼도 내용은 읽히지 않습니다. 창은 스크린샷, 화면 녹화, 화상회의 화면 공유에 찍히지 않습니다. 내 모니터에는 보이는데 상대 화면에는 그 자리에 뒤쪽 화면이 나옵니다. (macOS 15 이상에서는 일부 화면 공유 프로그램이 이 설정을 무시할 수 있습니다.)

웹에서 복사한 표와 글꼴은 그대로 두고, 다른 곳에 붙일 때 Ctrl+Shift+C를 누르면 글자만 복사됩니다. HTML·JSON은 줄 번호가 붙는 코드 메모에 넣고, 엉킨 JSON은 단축키 하나로 정리합니다. 어디서든 Ctrl+Alt+S로 찍은 화면이 메모에 들어가고, Ctrl+Alt+M을 누르면 창을 띄우지 않고도 방금 복사한 내용이 새 메모가 됩니다.

계정도 서버도 없고, 실행 중에 인터넷에 연결하지 않습니다. GPL-3.0-or-later로 소스를 공개한 무료 프로그램이고, Windows 10·11과 Apple Silicon(M1 이후) Mac에서 동작합니다. Windows판은 설치 없이 압축을 풀어 바로 실행합니다. 앱 화면은 한국어·영어·일본어·중국어(간체) 중에서 고를 수 있습니다. 홈페이지에서 지금 받을 수 있습니다.

## 카드별 캡션

| 카드 | 파일 | 캡션 |
|---|---|---|
| 01 표지 | `cards/card_01.png` | 메모장 탭에 암호나 API 키를 적어 두는 분들을 위한 메모장을 만들었습니다. |
| 02 자동 저장 | `cards/card_02.png` | 저장 버튼이 없습니다. 제목이 없는 메모는 만든 시각으로 구분되고, 메모 하나가 파일 하나로 한 폴더에 쌓입니다. |
| 03 암호화 | `cards/card_03.png` | 파일을 열어 봐도 알아볼 수 없는 글자만 나옵니다. 비밀 메모는 열 때마다 가려져 있다가 눌러야 보이고요. |
| 04 캡처에 안 보이는 창 | `cards/card_04.png` | Windows에서는 화면 공유 중에 메모 창을 띄워 둬도 상대 화면에는 창 뒤의 화면만 나옵니다. macOS 15 이상에서는 일부 화면 공유 앱에 창이 보일 수 있어요. |
| 05 서식 또는 글자만 | `cards/card_05.png` | 웹에서 가져온 표는 그대로 두고, 메신저에 붙일 땐 Ctrl+Shift+C로 글자만 복사합니다. |
| 06 코드 메모 | `cards/card_06.png` | .env 줄에서 오른쪽 클릭하면 등호 뒤의 값만 복사됩니다. 키 이름까지 붙여 넣는 실수가 줄어요. |
| 07 스크린샷·녹화 | `cards/card_07.png` | Ctrl+Alt+S로 찍은 화면은 지금 열린 메모에 바로 들어갑니다. 녹화할 때 보이는 빨간 테두리와 버튼은 영상에 남지 않습니다. |
| 08 클립보드를 메모로 | `cards/card_08.png` | 복사해 둔 문장을 잃어버릴 것 같을 때 Ctrl+Alt+M. 창은 뜨지 않고 메모 목록 맨 위에 저장됩니다. |
| 09 마무리 | `cards/card_09.png` | 무료 오픈소스로 공개했습니다. Windows용과 Apple Silicon Mac용을 홈페이지에서 받을 수 있어요. |

## 인스타그램 (캐러셀 9장, 본문 링크는 클릭되지 않으므로 프로필 링크 안내)

```
쉿, 조용히 적는 메모장을 만들었습니다.

메모장 탭에 서버 비밀번호나 테스트용 API 키를 적어 둔 적 있으시죠. 탭이 서른 개쯤 쌓이면 찾기도 어렵고, 화면을 공유하다 그 탭이 비치면 난감합니다.

Hushpad는 쓰는 대로 저장하고, 파일을 전부 암호화합니다. Windows에서는 화면 공유나 스크린샷에 창이 찍히지 않습니다.

Windows 10·11과 Apple Silicon Mac에서 쓰는 무료 오픈소스 앱입니다. 프로필 링크의 홈페이지에서 받을 수 있어요.

#허시패드 #Hushpad #메모장 #오픈소스 #생산성
```

## 스레드(Threads) 연재 (5개 글)

1/5
```
Windows 메모장 탭에 이런 거 쌓아 두는 분 계신가요. 서버 비번, 테스트 API 키, 보내기 직전의 HTML 조각.
저도 그랬고, 그래서 Hushpad라는 메모장을 만들었습니다. 이름은 hush(쉿)와 pad(메모장)를 붙여 지었어요.
```
(이미지: `cards/card_01.png`)

2/5
```
제일 먼저 정한 건 저장 버튼을 없애는 것이었습니다.
쓰는 동안 저장되고, 제목을 안 붙인 메모는 만든 시각으로 구분돼요. 탭 이름이 전부 "제목 없음"인 일은 없습니다.
```
(이미지: `cards/card_02.png`)

3/5
```
메모는 하나씩 따로 파일로 만들어 AES-256-GCM으로 암호화하고, 한 폴더에 모아 둡니다.
그 폴더를 동기화 폴더(Dropbox·OneDrive 등)에 넣어도, 파일을 열면 읽을 수 없는 글자만 보여요.
```
(이미지: `cards/card_03.png`)

4/5
```
가장 공들인 부분은 이겁니다. Windows에서는 Hushpad 창이 스크린샷과 화면 공유에 찍히지 않습니다.
화상회의 중에 메모를 띄워 둬도 상대 화면에는 창 뒤의 화면이 나와요. 일부러 보여 줄 때는 메뉴에서 끄면 됩니다.
Mac에서도 창 공유를 막지만, macOS 15 이상에서는 일부 화면 공유 앱에 창이 보일 수 있어요.
```
(이미지: `cards/card_04.png`)

5/5
```
Windows판은 압축만 풀면 되고, Mac은 Apple Silicon(M1 이후)용이 있습니다. 계정이나 서버는 없어요.
무료 오픈소스(GPL-3.0-or-later)로 공개했고, 홈페이지에서 받을 수 있습니다.
https://gdra.mycafe24.com/hushpad/
```
(이미지: `cards/card_09.png`)

## X (Twitter)

X는 한글을 2자로 세므로 아래 글은 가중치 기준 280 안에 들어갑니다.

```
Windows에서는 화면을 공유해도 상대에게 안 보이는 메모장을 만들었습니다. 쓰는 대로 저장되고 파일은 전부 암호화돼요. Mac판도 있는 무료 오픈소스입니다(macOS 15 이상에서는 일부 화면 공유 앱에 보일 수 있어요).
https://gdra.mycafe24.com/hushpad/
```

## 블로그(네이버·티스토리) 도입부 (약 600자)

```
메모장 탭이 서른 개쯤 열려 있는 PC를 자주 봅니다. 하나는 서버 비밀번호, 하나는 테스트용 API 키, 또 하나는 고객사에 보내기 직전의 HTML 조각이고요. 저장 안 해도 다시 켜면 남아 있으니 편하긴 한데, 탭 제목이 전부 "제목 없음"이라 원하는 걸 찾으려면 하나씩 눌러 봐야 합니다. PC가 갑자기 꺼진 날에는 내용이 그대로 있는지 확인하느라 마음이 급해지죠.

더 곤란한 건 화면을 공유할 때입니다. 회의 중에 창을 바꾸다 그 탭이 잠깐 비치면, 그 순간 적어 둔 키는 이미 상대 화면에 나간 뒤입니다.

그래서 Hushpad(허시패드)라는 메모장을 만들었습니다. hush(쉿)와 pad(메모장)를 합친 이름입니다. 쓰는 동안 저장되고, 메모는 전부 암호화된 파일로 폴더 한 곳에 모입니다. 그리고 Windows에서는 창 자체가 스크린샷과 화면 공유에 찍히지 않습니다. 내 모니터에서는 보이는데, 상대 화면에는 그 자리에 뒤쪽 화면이 나옵니다. Mac에서도 창 공유를 막지만 macOS 15 이상에서는 일부 화면 공유 프로그램에 보일 수 있습니다.

이 글에서는 Hushpad를 만들면서 정한 원칙과, 실제로 어떤 순간에 쓰는지 화면과 함께 정리해 보겠습니다. Hushpad는 무료 오픈소스로 공개했고, 홈페이지에서 Windows용과 Mac용을 받을 수 있습니다. 지금 이런 메모를 어디에 두고 계신지 댓글로 알려 주시면 다음 버전을 만드는 데 참고하겠습니다.
```

## 메이커 소개글 (GeekNews·디스콰이엇 형식)

```
제목: Hushpad - Windows에서 캡처와 화면 공유에 찍히지 않는 암호화 메모장 (Mac판 포함, 오픈소스)

메모장 탭에 비밀번호, API 키, 붙여넣기 전 HTML·JSON을 쌓아 두는 습관 때문에 만들었습니다.

무엇을 하나요
- 저장 버튼이 없습니다. 0.6초 뒤 임시 파일에 쓰고 바꿔치기하는 방식이라 저장 도중 꺼져도 직전 내용이 남습니다. 10분마다 이전 버전도 쌓입니다.
- 메모 하나가 파일 하나(notes\20261115-143205-xxxx.own)이고, AES-256-GCM으로 암호화합니다. 열쇠는 scrypt로 암호에서 만들고, Windows에서는 DPAPI로 계정에 묶어, Mac에서는 키체인에 넣어 기억합니다.
- 창에 Windows의 캡처 제외 설정(Windows 10 2004 이상)을 걸어서 스크린샷, 녹화, 화면 공유에 나오지 않습니다. macOS에서는 창 공유를 끕니다. 메뉴에서 끌 수 있습니다.
- 서식 메모와 코드 메모가 따로 있습니다. 코드 메모에는 줄 번호, 색 구분, JSON 정리(Ctrl+Alt+J)가 있고, KEY=값 줄에서는 값만 복사할 수 있습니다.
- 전역 단축키: Ctrl+Alt+S 영역 캡처, Ctrl+Alt+R 화면 녹화(최대 3분, 녹화 테두리와 버튼 막대는 영상에 안 찍힘), Ctrl+Alt+M 클립보드를 메모로. Mac에서는 ⌃⌥S·⌃⌥R·⌃⌥M입니다.
- 복사한 내용은 Windows 클립보드 기록과 클라우드 클립보드에 남지 않도록 표시합니다.

만든 방식
- Python + PySide6(Qt), cryptography. 계정·서버·분석 스크립트 없이 오프라인으로 동작합니다.
- GPL-3.0-or-later 오픈소스: https://github.com/wind2sp/hushpad
- Windows판은 설치 없이 압축을 풀어 실행하는 포터블 앱입니다.

알아 둘 것
- Mac은 Apple Silicon(M1 이후)용만 있습니다. Intel Mac용은 없습니다.
- 코드 서명을 하지 않아 처음 실행할 때 경고가 뜹니다. Windows는 "추가 정보 › 실행", Mac은 오른쪽 클릭 › 열기로 엽니다.
- macOS 15 이상에서 ScreenCaptureKit을 쓰는 일부 캡처·화면 공유 프로그램은 창 숨기기를 무시할 수 있습니다.
- 앱 화면은 한국어·영어·일본어·중국어(간체) 중에서 고를 수 있습니다.
- 암호를 잊으면 되살릴 방법이 없습니다. 의도한 설계입니다.

피드백 받고 싶은 것: 이런 메모를 지금 어디에 두고 계신지, 캡처 제외가 오히려 불편한 상황이 있는지 궁금합니다.
홈페이지: https://gdra.mycafe24.com/hushpad/
```

## 보도자료형 3단락

```
캡처와 화면 공유에 보이지 않는 암호화 메모장 Hushpad(허시패드)가 무료 오픈소스로 공개됐다. Hushpad는 비밀번호, API 키, 붙여넣기 전의 HTML·JSON처럼 잠깐 적어 두지만 남에게 보여서는 안 되는 메모를 위해 만든 프로그램이다. 이름은 '쉿'을 뜻하는 hush와 메모장을 뜻하는 pad를 합쳐 지었다.

Hushpad에는 저장 버튼이 없다. 내용은 쓰는 동안 저장되고, 모든 메모는 사용자가 고른 폴더 한 곳에 AES-256-GCM으로 암호화된 파일로 남는다. 프로그램 창은 Windows의 캡처 제외 기능과 macOS의 창 공유 끔 설정을 써서 스크린샷, 화면 녹화, 화상회의 화면 공유에 나타나지 않는다. 다만 macOS 15 이상에서는 일부 화면 공유 프로그램이 이 설정을 무시할 수 있다. 이 밖에 웹 서식을 유지하거나 글자만 골라 복사하는 기능, 줄 번호와 JSON 정리를 지원하는 코드 메모, 어디서든 쓰는 스크린샷(Ctrl+Alt+S)·화면 녹화(Ctrl+Alt+R)·클립보드 저장(Ctrl+Alt+M) 단축키를 갖췄다.

Hushpad는 계정과 서버 없이 오프라인으로 동작하며, Windows 10·11과 Apple Silicon(M1 이후) Mac을 지원한다. Windows판은 설치 없이 압축을 풀어 실행하는 포터블 앱이다. 앱 화면은 한국어·영어·일본어·중국어(간체)를 지원한다. 소스 코드는 GPL-3.0-or-later 라이선스로 GitHub(https://github.com/wind2sp/hushpad)에 공개되어 있고, 내려받기와 설치 안내는 홈페이지(https://gdra.mycafe24.com/hushpad/)에 있다.
```

## 해시태그 (게시물당 5개 이하)

- 기본: `#허시패드 #Hushpad #메모장 #오픈소스 #생산성`
- 보안 주제: `#허시패드 #메모장 #정보보안 #재택근무`
- 개발 주제: `#허시패드 #개발자 #JSON #사이드프로젝트`

## 15초 엘리베이터 스크립트 (말로 읽기, 약 15초)

```
메모장 탭에 비밀번호나 API 키 적어 두시죠? 화면 공유하다 그게 비치면 곤란하잖아요.
Hushpad는 파일을 전부 암호화하고, Windows에서는 창이 화면 공유에 아예 안 찍힙니다.
조용히 적고, 아무도 못 보게. 지금 무료로 받을 수 있어요.
```

---

# English

## One-line pitch

A free, open-source notepad for Windows and Mac that encrypts every note and, on Windows, doesn't show up when you share your screen.

## Headline options

1. Write quietly. Seen by no one.
2. Your API keys don't belong in a Notepad tab you might screen-share.
3. The notepad your screen share can't see (on Windows).

## Short description (~25 words)

For the passwords, API keys and half-finished JSON you jot down for a minute. It saves as you type, and on Windows the window stays out of screenshots and screen shares. Free and open source, for Windows and Mac.

## Long description

A lot of us treat Notepad tabs as a scratch drawer: a server password, a test API key, a chunk of HTML you're about to send to a client. It works until you have thirty tabs all called "Untitled", your PC restarts and you're not sure what survived, or you share your screen in a meeting and that tab flashes by.

Hushpad is a notepad built for exactly that kind of note. It saves while you type, and notes you never named are labeled by when you created them. Every note is a separate file in one folder you choose, encrypted with AES-256-GCM, so even if that folder syncs to the cloud, the contents stay unreadable. The window itself is excluded from screenshots, screen recordings and video-call screen sharing. You see it on your monitor; everyone else sees whatever is behind it. (On macOS 15 and later, some screen-sharing apps can ignore this setting.)

Pasted formatting stays intact, and Ctrl+Shift+C copies plain text when you need it. Code notes get line numbers and JSON cleanup on a shortcut, and you can right-click an API_KEY=… line to copy just the value. Ctrl+Alt+S drops a screenshot into the open note, and Ctrl+Alt+M turns whatever's on your clipboard into a new note without opening a window.

No account, no server, and it doesn't go online while it runs. Hushpad is free and open source under GPL-3.0-or-later, and runs on Windows 10 and 11 and on Macs with Apple silicon (M1 or later). On Windows it's portable: unzip and run, nothing to install. The app UI comes in Korean, English, Japanese and Simplified Chinese. You can download it now from the homepage.

## Card captions

| Card | File | Caption |
|---|---|---|
| 01 Cover | `cards/en/card_01.png` | We built a notepad for the things you shouldn't keep in a Notepad tab. |
| 02 Auto-save | `cards/en/card_02.png` | No save button. Untitled notes are labeled by creation time, and each one is its own file in a single folder. |
| 03 Encryption | `cards/en/card_03.png` | Open a note file in anything else and you get noise. Secret notes stay veiled until you click. |
| 04 Invisible to capture | `cards/en/card_04.png` | On Windows: mid-call, notes open on your screen. On theirs, just whatever is behind the window. (On macOS 15 and later, some screen-sharing apps can still show it.) |
| 05 Format or text | `cards/en/card_05.png` | Keep the table you pasted from the web. Ctrl+Shift+C when you only want the words. |
| 06 Code notes | `cards/en/card_06.png` | Right-click a .env line and copy only what's after the equals sign. |
| 07 Screenshots & clips | `cards/en/card_07.png` | Ctrl+Alt+S puts a screenshot straight into your note. The red recording frame never makes it into the video. |
| 08 Clipboard to note | `cards/en/card_08.png` | Copied something you'll need later? Ctrl+Alt+M. It's a note now, and nothing popped up. |
| 09 Closing | `cards/en/card_09.png` | Free and open source. Get it on the homepage for Windows or an Apple silicon Mac. |

Note: the app screens on the English cards show the English UI, rendered from a test profile with made-up notes.

## Instagram

```
Shh. We made a quieter notepad.

If your Notepad tabs hold server passwords and test API keys, you know the moment: you share your screen and one of them flashes by.

Hushpad encrypts every file, and on Windows its window doesn't show up in screenshots or screen shares.

Free and open source, for Windows 10 and 11 and Apple silicon Macs. Get it from the link in bio.

#Hushpad #opensource #productivity #privacy #devtools
```

## Threads (5 posts)

1/5
```
Confession: my Notepad tabs used to be full of server passwords, test API keys and half-written HTML.
So I built Hushpad. Hush + pad.
```

2/5
```
First decision: no save button.
It saves while you type, and untitled notes get labeled with when you made them. No more twelve tabs called "Untitled".
```

3/5
```
Each note is its own file, encrypted with AES-256-GCM, in one folder you pick.
Sync it with Dropbox, OneDrive or similar if you like. Open a file and all you'll see is noise.
```

4/5
```
The part I care about most: on Windows, the Hushpad window doesn't show up in screenshots or screen shares.
On a call, it's on your monitor and invisible on theirs. You can switch that off when you actually want to show a note.
The Mac build blocks window sharing too, but on macOS 15 and later some screen-sharing apps can still see it.
```

5/5
```
Portable on Windows, nothing to install. There's a build for Apple silicon Macs too. No account.
It's free and open source (GPL-3.0-or-later). Get it here:
https://gdra.mycafe24.com/hushpad/
```

## X (Twitter)

```
I built a notepad that doesn't show up when you share your screen on Windows. Every note is encrypted, and there's no account to make. Free and open source, with a Mac build too (on macOS 15+, some screen-sharing apps can still see it).
https://gdra.mycafe24.com/hushpad/
```

## Maker post (Show HN / Product Hunt style)

```
Title: Hushpad – an open-source, encrypted notepad that's invisible to screenshots and screen sharing on Windows (Mac build too)

I kept passwords, API keys and pre-paste JSON in Notepad tabs, and after one too many nervous screen shares I built this.

What it does
- No save button. Writes go to a temp file and get swapped in, so a crash mid-save leaves the previous version. Snapshots every 10 minutes.
- One note = one file, encrypted with AES-256-GCM. The key is derived from your passphrase with scrypt and cached per Windows account via DPAPI, or in the Keychain on a Mac.
- The window uses Windows' capture exclusion (Windows 10 2004+), so it doesn't appear in screenshots, recordings or screen shares. On macOS it turns off window sharing. There's a toggle for when you want it visible.
- Rich notes and code notes. Code notes have line numbers, highlighting, JSON tidy (Ctrl+Alt+J) and "copy just the value" for KEY=value lines.
- Global hotkeys: Ctrl+Alt+S area screenshot, Ctrl+Alt+R screen recording (up to 3 min; the recording frame and controls aren't captured), Ctrl+Alt+M clipboard to note. On a Mac: ⌃⌥S, ⌃⌥R, ⌃⌥M.
- Copies are flagged so they stay out of Windows clipboard history and cloud clipboard.

How it's built
- Python, PySide6 (Qt), cryptography. No account, no server, no analytics, works offline.
- GPL-3.0-or-later: https://github.com/wind2sp/hushpad
- Portable on Windows: unzip and run.

Good to know
- The Mac build is for Apple silicon (M1 or later) only. There's no Intel Mac build.
- The builds aren't code-signed, so you'll see a warning on first launch. On Windows, use "More info › Run anyway"; on a Mac, right-click › Open.
- On macOS 15 and later, some capture and screen-sharing apps that use ScreenCaptureKit can ignore the window's sharing setting.
- The app UI comes in Korean, English, Japanese and Simplified Chinese.
- Forget your passphrase and the notes are gone. That's on purpose.

I'd love to hear where you keep this kind of note now, and whether capture exclusion would ever get in your way.
https://gdra.mycafe24.com/hushpad/
```

## Press-style announcement (3 paragraphs)

```
Hushpad is a free, open-source notepad for Windows and Mac designed for short-lived but sensitive notes such as passwords, API keys and snippets of HTML or JSON waiting to be pasted. Its name combines "hush" and "pad", and its main promise is in the tagline: write quietly, seen by no one.

Hushpad has no save button. Notes are saved as they are written and stored as individual files, encrypted with AES-256-GCM, in a single folder of the user's choice. The app window uses Windows' capture exclusion and macOS's window sharing setting, so it does not appear in screenshots, screen recordings or screen sharing during video calls. On macOS 15 and later, some screen-sharing apps can ignore this setting. Other features include copying with or without formatting, code notes with line numbers and JSON cleanup, and system-wide shortcuts for screenshots (Ctrl+Alt+S), screen recording (Ctrl+Alt+R) and saving the clipboard as a note (Ctrl+Alt+M).

Hushpad runs offline with no account or server. It supports Windows 10 and 11, where it runs as a portable app with no installation, and Macs with Apple silicon (M1 or later). The app UI is available in Korean, English, Japanese and Simplified Chinese. The source code is published on GitHub (https://github.com/wind2sp/hushpad) under GPL-3.0-or-later, and downloads and setup steps are at https://gdra.mycafe24.com/hushpad/.
```

## Hashtags (5 or fewer per post)

- Default: `#Hushpad #opensource #productivity #privacy #devtools`
- Dev angle: `#Hushpad #devtools #buildinpublic #indiedev`
- Security angle: `#Hushpad #privacy #infosec #remotework`

## 15-second elevator script (spoken)

```
Ever kept an API key in a Notepad tab, then shared your screen? Hushpad encrypts every note, and on Windows its window simply doesn't show up in screen shares or screenshots. Write quietly. Seen by no one. It's free to download now.
```
