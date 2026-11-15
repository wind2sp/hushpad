# Hushpad — 조용한 비밀 메모장

**Hushpad(허시패드)** = hush(쉿, 조용히) + pad(메모장).
임시 기록, 붙여넣기 전 보관, 암호·API 키, HTML·JSON, 스크린샷·짧은 녹화를 한곳에 조용히 담아 둡니다.
모든 내용은 자동 저장·암호화되고, 창은 다른 프로그램의 캡처·화면 공유에 보이지 않습니다.

**무료 오픈소스 (GPL-3.0-or-later)** · 홈페이지 https://gdra.mycafe24.com/hushpad/

## 받기
| | 파일 | 지원 |
|---|---|---|
| Windows | [Hushpad-win64.zip](https://github.com/wind2sp/hushpad/releases/latest/download/Hushpad-win64.zip) | Windows 10(2004 이상)·11, 64비트 |
| macOS | [Hushpad-macos-arm64.zip](https://github.com/wind2sp/hushpad/releases/latest/download/Hushpad-macos-arm64.zip) | Apple Silicon(M1 이후). **Intel Mac용은 없습니다** |

- 설치 과정이 없는 포터블 앱입니다. zip을 풀고 `Hushpad.exe`(macOS는 `Hushpad.app`)를 실행하면 처음에 보관 폴더와 암호(8자 이상)를 정합니다.
- 서명하지 않은 앱이라 Windows는 "PC 보호" 창에서 **추가 정보 › 실행**, macOS는 처음 한 번 **오른쪽 클릭 › 열기**가 필요합니다.
- 처음 실행하면 "Windows 시작할 때 실행"(macOS: 로그인할 때 실행)이 켜집니다. 트레이(메뉴 막대) 아이콘 오른쪽 클릭으로 끌 수 있어요.
- 받은 파일이 맞는지는 릴리스 페이지의 SHA-256 값과 비교해 확인하세요 (Windows: `Get-FileHash 파일.zip`, macOS: `shasum -a 256 파일.zip`).

## 언어
- 한국어 · English · 日本語 · 简体中文. `⋯ › 보기 › 언어`에서 바꾸고, **지금 다시 시작**을 누르면 열린 메모를 모두 저장한 뒤 다시 켜집니다.
- 기본은 **시스템 따라가기**: 운영체제 언어가 위 넷 중 하나면 그 언어, 아니면 영어(번체 중국어도 아직은 영어). 설정 파일의 `"language"`에 저장됩니다.
- 날짜·"5분 전" 같은 시각도 언어에 맞춰 보입니다. 단축키는 언어와 상관없이 같습니다.
- 일본어·중국어에서는 그 언어에 맞는 글꼴(Yu Gothic UI·Meiryo / Microsoft YaHei, macOS는 Hiragino Sans / PingFang SC)을 먼저 씁니다.
- 일본어·중국어에서는 Qt 기본 단추(OK·Cancel 등)도 그 언어로 바뀝니다. 한국어 화면은 예전 그대로입니다.

## 저장
- 저장 버튼이 없습니다. 쓰는 즉시(0.6초 뒤) 자동 저장되고, 저장할 때 임시 파일에 쓴 뒤 바꿔치기해서 저장 도중 꺼져도 이전 내용이 남습니다.
- 모든 메모는 **보관 폴더 한 곳**에 메모 1개 = 파일 1개(`notes\20261115-143205-xxxx.own`)로, 만든 시각을 이름으로 저장됩니다.
- 10분마다 이전 버전이 쌓입니다(메모마다 최근 40개) → `메모 › 이전 버전 보기` (Ctrl+Shift+H).
- 하루 한 번 이 PC의 `%LOCALAPPDATA%\Hushpad\backups`(macOS: `~/Library/Application Support/Hushpad/backups`)에 메모(`notes\`)·금고 파일·분류를 zip으로 백업합니다(14일치, 암호화된 상태 그대로). 동영상(`media\`)과 이전 버전(`history\`)은 크기 때문에 백업에 넣지 않습니다.

## 암호화·다른 프로그램과 안 섞이게
- 파일 내용은 AES-256으로 암호화됩니다. 다른 프로그램·검색 색인·클라우드가 파일을 읽어도 내용을 알 수 없습니다.
- 이 PC에서는 암호를 처음 한 번만 넣습니다(Windows는 DPAPI로 Windows 계정에 묶어, macOS는 로그인 키체인에 기억). 다른 계정이나 다른 PC에서는 풀 수 없습니다.
- **여러 PC에서 같이 쓰기**: 보관 폴더를 Dropbox·OneDrive 안에 두고, 다른 PC에서도 같은 폴더를 고른 다음 같은 암호를 넣으면 됩니다. 다른 PC에서 고친 내용은 3초 안에 반영되고, 양쪽에서 동시에 고치면 이 PC 쪽 내용이 "(충돌 사본)"으로 따로 저장됩니다.
- 복사한 내용은 Windows 클립보드 기록(Win+V)·클라우드 클립보드에 남지 않습니다(`보안` 메뉴에서 끌 수 있음).
- **비밀 메모**(🔒): 목록에 첫 줄이 보이지 않고, 복사하면 클립보드 관리 프로그램도 못 보며 30초 뒤 클립보드를 비웁니다.
- Hushpad 창은 다른 프로그램의 스크린샷·화면 녹화·화면 공유에 보이지 않습니다(`캡처` 메뉴에서 끌 수 있음).
- ⚠ 암호를 잊으면 아무도 되살릴 수 없습니다. `파일 › 내보내기`로 만든 파일은 암호화되지 않은 일반 파일입니다.

## 두 종류의 메모
| | 서식 메모 (Ctrl+N) | 텍스트 메모 (Ctrl+Shift+N) |
|---|---|---|
| 용도 | 웹·워드에서 복사한 내용, 이미지, 스크린샷, 동영상 | HTML·JSON·코드·API 키 |
| 붙여넣기 | 서식 그대로 (Ctrl+Shift+V는 텍스트만) | 언제나 텍스트만 |
| 기타 | `보기 › 텍스트만 보기`(Ctrl+T) | 줄 번호, 색 구분, 자동 들여쓰기, JSON 정리(Ctrl+Alt+J) |

서식 메모도 '텍스트만' 버전을 늘 함께 가지고 있어서, 밖으로 보낼 때 고를 수 있습니다:
Ctrl+C 서식 포함 복사 · **Ctrl+Shift+C 텍스트만 복사** · Ctrl+Alt+C 메모 전체(서식) · Ctrl+Alt+Shift+C 메모 전체(텍스트).

## 탭과 목록
- 목록을 한 번 누르면 **미리보기 탭**(◌, 다른 메모를 누르면 그 자리에 바뀜)으로 열리고, 고치거나 두 번 누르면 고정 탭이 됩니다 → 탭이 쌓이지 않습니다.
- 탭을 닫아도 메모는 목록에 남습니다. 아무것도 안 쓴 새 메모만 닫을 때 사라집니다.
- 이름을 안 정하면 탭에 `첫 줄 · 11-15 14:32`(만든 때)로 보여 비슷한 제목이 구분됩니다. 이름은 F2 또는 탭 두 번 클릭.
- 분류: 메모를 왼쪽 분류로 끌어다 놓거나 Ctrl+M. 📌 고정(Ctrl+P), 🗑 휴지통(되살리기 가능).
- 합치기: 목록에서 Ctrl/Shift로 여러 개 고르고 Ctrl+Shift+M (만든 순서대로 이어 붙이고 원래 메모는 휴지통으로 옮길지 묻습니다).
- 찾기: Ctrl+E 목록 전체에서, Ctrl+F/Ctrl+H 지금 메모에서 찾기·바꾸기.
- `파일 › Windows 메모장 탭 가져오기`: 메모장에 열려 있는 탭(저장 안 한 것 포함)을 복사해 옵니다. 메모장 쪽은 건드리지 않습니다.
- 파일(txt·json·html·그림)을 목록에 끌어다 놓으면 메모로 가져옵니다.

## 스크린샷·화면 녹화
- 📷 **Ctrl+Alt+S**(어디서든) / Ctrl+Shift+S: 영역을 끌어서 고르면(Enter = 화면 전체) 지금 서식 메모에 넣고 클립보드에도 복사합니다.
- 🎬 **Ctrl+Alt+R**(어디서든) / Ctrl+Shift+R: 영역을 고르면 녹화 시작(최대 3분). 빨간 테두리와 ⏸·⏹ 버튼 막대는 화면에 보이지만 녹화에는 찍히지 않습니다.
  다시 Ctrl+Alt+R 또는 ⏹ 저장으로 끝내면 미리보기 그림이 메모에 들어가고, 두 번 클릭하면 재생됩니다.
  동영상은 암호화되어 보관 폴더 `media\`에 저장되고, 재생할 때는 메모리에서 풀어 재생합니다. 녹화하는 동안만 이 PC의 임시 폴더(`%LOCALAPPDATA%\Hushpad\tmp`)에 암호화 전 파일이 잠깐 생기고, 끝나면 바로 지웁니다(비정상 종료로 남으면 다음 실행 때 지웁니다).
- Hushpad 창은 캡처에 안 찍히므로 창을 치우지 않고 그대로 찍어도 됩니다.

## 어디서든 쓰는 단축키 (트레이에 있어도 동작)
| 단축키 | 하는 일 |
|---|---|
| Ctrl+Alt+N | 새 메모 (창을 앞으로) |
| Ctrl+Alt+M | **지금 클립보드를 메모로 저장** — 창을 띄우지 않고 조용히 (글·이미지·HTML) |
| Ctrl+Alt+S / Ctrl+Alt+R | 스크린샷 / 화면 녹화 |

창을 닫으면 트레이(작업 표시줄 오른쪽)에 남습니다. 완전히 끝내려면 Ctrl+Q 또는 트레이 메뉴 › 끝내기.
처음 실행할 때 "Windows 시작할 때 실행"이 켜집니다. 트레이 아이콘 오른쪽 클릭이나 `⋯ › 보안`에서 끄고 켤 수 있어요(창 닫으면 트레이에 남기도 같은 메뉴).

## 편하게 쓰는 기능
- **Ctrl+K 찾기·명령**: 메모 제목·내용과 모든 명령을 한 곳에서 찾아 Enter로 실행.
- **잠금 Ctrl+L**: 보관 폴더 암호로만 열림. `⋯ › 보안`에서 자리 비우면(5·10·30분) / Windows 잠글 때 자동 잠금.
- **비밀 메모 가림막**: 비밀 메모는 열 때마다 내용이 가려져 있고, 눌러야 보입니다(옆 사람·화면 공유 대비).
- **값만 복사**: 코드 메모에서 `API_KEY=sk-…`, `"token": "…"` 줄을 오른쪽 클릭 → "이 줄 값만 복사".
- **스마트 분류**: 오늘 고친 메모 / 30일 넘게 안 본 메모(정리용).
- **항상 위에 Ctrl+Alt+T**: 다른 프로그램에 옮겨 적을 때 창을 위에 고정.
- **테마**: `⋯ › 보기 › 테마` — 시스템 따라가기·밝게·어둡게.

## macOS
같은 코드가 macOS에서도 돌도록 OS마다 다른 부분을 `hushpad_app\plat\`(win.py · mac.py · base.py)에 모았습니다. Windows 동작은 그대로입니다.

| 기능 | Windows | macOS |
|---|---|---|
| 이 PC에 암호 기억 | DPAPI (`%LOCALAPPDATA%\Hushpad\keys.json`) | 로그인 키체인 (서비스 `Hushpad`, `/usr/bin/security`) |
| 캡처·화면 공유에서 창 숨기기 | SetWindowDisplayAffinity | NSWindow 공유 끔(sharingType = None) |
| 어디서든 쓰는 단축키 | Ctrl+Alt+S/R/N/M | ⌃⌥S/R/N/M (Control+Option, Carbon 단축키) |
| 시작할 때 실행 | 레지스트리 Run 키 | `~/Library/LaunchAgents/com.hushpad.app.plist` (다음 로그인부터) |
| 클립보드 기록에서 빼기 | Win+V 기록·클라우드 제외 형식 | `org.nspasteboard.TransientType`/`ConcealedType` 표시 |
| 설정·백업 폴더 | `%APPDATA%`·`%LOCALAPPDATA%\Hushpad` | `~/Library/Application Support/Hushpad` |
| 메모장 탭 가져오기, Windows 잠글 때 함께 잠그기, 제목 표시줄 색 | 있음 | 없음(메뉴에서 숨김). 제목 표시줄은 밝게/어둡게만 맞춤 |

- 앱 안 단축키는 같은 키를 쓰고, macOS에서는 Qt가 Ctrl을 ⌘로 바꿉니다(메뉴·툴팁·팔레트 표시도 ⌘ 기호로).
- **화면 기록 권한**: 스크린샷·녹화를 처음 하면 macOS가 권한을 묻습니다. 거절했거나 화면이 비어 찍히면
  `시스템 설정 › 개인정보 보호 및 보안 › 화면 및 시스템 오디오 기록`에서 Hushpad를 켜고 다시 시작하라고 안내합니다.
- ⚠ **캡처 숨기기의 한계**: macOS 15 이상에서 ScreenCaptureKit을 쓰는 일부 캡처·화면 공유 프로그램은 창의 공유 끔 설정을 무시하고 Hushpad 창을 찍을 수 있습니다. Windows만큼 믿지 마세요.
- 클립보드 표시는 PySide6에 `QUtiMimeConverter`가 있을 때만 붙습니다(없으면 그냥 복사). Maccy·Raycast·Alfred처럼 nspasteboard.org 약속을 따르는 클립보드 관리 프로그램만 이 표시를 존중합니다. 비밀 메모 30초 뒤 지우기는 그대로 동작합니다.
- **서명·공증 안 됨**: 받은 `Hushpad.app`을 처음 열 때 "확인되지 않은 개발자" 경고가 뜨면 Finder에서 오른쪽 클릭 › 열기(또는 `시스템 설정 › 개인정보 보호 및 보안`의 "그래도 열기"). Apple Developer ID(연 99달러)로 서명하고 공증(notarize)하면 이 경고 없이 열리고, 키체인·화면 기록 권한도 앱 업데이트 뒤에 다시 묻지 않습니다.
- macOS 빌드는 GitHub의 Mac(Apple Silicon)에서 만들고 자체 점검(키체인 포함)을 통과합니다. 캡처 숨기기·단축키·화면 기록 권한처럼 화면이 필요한 기능은 실제 Mac에서 아직 충분히 확인하지 못했습니다. 문제가 있으면 이슈로 알려 주세요.

## 개발
- 실행: `python hushpad_main.py` · 점검: `python hushpad_main.py --selftest` (결과 `%TEMP%\hushpad_selftest.txt` — 번역 문구 목록 네 개가 서로 맞는지도 검사)
- 다른 OS 흉내: `python tests/sim_platform.py darwin` / `linux`
- 빌드: `python build.py` → Windows `dist\Hushpad\Hushpad.exe`, macOS `dist/Hushpad.app` (빌드 후 자체 점검까지)
- macOS 빌드는 GitHub Actions `build-macos`를 손으로 실행(Run workflow)합니다(push에는 돌지 않음). `macos-latest`(Apple Silicon)에서 `Hushpad-macos-arm64.zip`을 만들어 초안 릴리스 `mac-build`에 올립니다. Intel Mac 빌드는 만들지 않습니다.
- 필요: Python 3.14와 `requirements.txt`의 고정 버전(PySide6 6.12, cryptography 48, Pillow, PyInstaller) — macOS 기능은 ctypes로 시스템 라이브러리를 직접 부름
- 빌드는 쓰지 않는 Qt 가상 키보드·QML·소프트웨어 OpenGL을 빼고, `LICENSE`·`NOTICE`·`THIRD_PARTY_NOTICES.md`·`licenses\`를 함께 넣습니다.
- 구성: `hushpad_app\` — crypto(암호), store(저장), editors(편집기), capture(캡처·녹화), window(주 창), notepad_import, i18n(번역), plat(OS별 기능)
- 번역: 화면 문구는 모두 `tr("열쇠")`로 `hushpad_app\locales\{ko,en,ja,zh}.json`에서 가져옵니다. 문구를 더하면 네 파일에 같은 열쇠를 넣으세요(`열쇠@mac`은 macOS에서만 쓰는 문구). 언어별 화면: `docs\i18n\`

## 라이선스

- **무료 오픈소스, [GPL-3.0-or-later](LICENSE)** (GNU 일반 공중 사용 허가서 3판 또는 그 이후 판). 소프트웨어는 "있는 그대로" 제공되며 어떠한 보증도 하지 않습니다. 수정본을 배포할 때는 같은 라이선스로 소스 코드를 함께 공개해야 합니다.
- © 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad contributors — 자세한 내용은 [NOTICE](NOTICE).
- Hushpad 이름과 아이콘은 상표입니다. GPL 3판 7조 (e)에 따라 라이선스는 이름·아이콘 사용 권한을 주지 않습니다. 수정본은 다른 이름과 아이콘을 써 주세요.
- 함께 배포하는 오픈소스(Qt for Python·Qt — LGPL-3.0, cryptography, OpenSSL 등)와 출처는 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)에 있습니다.

## English (short)

Hushpad is a quiet, private notepad for Windows and macOS (Apple Silicon). Notes save as you type, every note is encrypted (AES-256-GCM, scrypt-derived vault key, cached per device with DPAPI / the macOS Keychain), and the window is hidden from screenshots and screen sharing. Rich notes take images, screenshots and short screen recordings; code notes are for HTML/JSON and keys. The UI comes in Korean, English, Japanese and Simplified Chinese.

- Download: [Windows](https://github.com/wind2sp/hushpad/releases/latest/download/Hushpad-win64.zip) · [macOS (Apple Silicon)](https://github.com/wind2sp/hushpad/releases/latest/download/Hushpad-macos-arm64.zip). Portable, no installer, unsigned (Windows: "More info › Run anyway"; macOS: right-click › Open). No Intel Mac build.
- Run from source: `pip install -r requirements.txt`, then `python hushpad_main.py`. Build: `python build.py`.
- License: GPL-3.0-or-later. © 2026 NINEROW partners Co., Ltd. (나인로우파트너스(주)) and Hushpad contributors. See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
