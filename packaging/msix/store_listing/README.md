# Microsoft Store 제출 자료

| 파일 | 내용 |
|---|---|
| `listing_ko.md` · `listing_en.md` | 한국어·영어 등록 정보 전체 (간단한 설명, 설명, 새로운 기능, 제품 기능 8개, 검색어, 스크린샷 설명, 저작권) |
| `listing_ja.md` · `listing_zh.md` | 일본어·중국어(간체) 등록 정보 (설명은 조금 짧게) |
| `screenshots/<언어>/*.png` | 1920×1080 데스크톱 스크린샷 5장씩 (Store 최소 1366×768). 가짜 메모만 넣은 시험용 보관 폴더에서 찍음 |

## 언어와 상관없는 칸

| Partner Center 칸 | 값 |
|---|---|
| 가격 및 사용 가능 여부 › 가격 | 무료 |
| 가격 및 사용 가능 여부 › 시장 | 모든 시장 (원하면 조정) |
| 속성 › 범주 | 생산성 (Productivity), 하위 범주 없음 |
| 속성 › 개인정보처리방침 URL | https://gdra.mycafe24.com/hushpad/privacy.html |
| 속성 › 웹 사이트 | https://gdra.mycafe24.com/hushpad/ |
| 속성 › 지원 연락처 정보 | https://github.com/wind2sp/hushpad/issues |
| 속성 › 시스템 요구 사항 | Windows 10 버전 2004(빌드 19041) 이상 또는 Windows 11, x64. 메모리·저장 공간은 일반 데스크톱 앱 수준 |
| 연령 등급 | IARC 설문: 폭력·성적 내용 없음, 사용자 간 소통 없음, 개인정보 공유 없음, 위치 사용 없음, 디지털 구매 없음 → 대부분 지역 3+ 예상 |
| 패키지 | `dist\Hushpad-<버전>.msix` (`packaging\msix\make_msix.py`로 만든 것, 서명 없이 올림) |
| 기기 제품군 | Windows 10/11 데스크톱 (매니페스트대로) |

## 제출 옵션 › 제한된 기능 설명 (runFullTrust)

영어로 적습니다.

> Hushpad is a Win32 desktop app (Python/Qt) packaged with MSIX. It needs runFullTrust to run as a regular desktop process: it keeps an icon in the notification area, registers system-wide hotkeys (RegisterHotKey) for quick notes and screenshots, excludes its own windows from screen capture (SetWindowDisplayAffinity), protects the local key with DPAPI, and reads and writes the user's chosen vault folder (Documents\Hushpad by default). It makes no network connections.

## 인증 참고 사항 (Notes for certification)

> No account or sign-in. On first launch the app asks for a vault folder (default Documents\Hushpad) and a passphrase of 8 or more characters; any test passphrase works. The app starts in the tray at sign-in through its StartupTask, which users can turn off in Settings > Apps > Startup or from the app's Security menu ("Open Windows startup settings…"). The window is intentionally hidden from screenshots and screen sharing (Capture menu > uncheck to show it). The app makes no network connections.

## 스크린샷

언어마다 같은 다섯 장입니다. 순서대로 올리세요.

1. `1-rich-light.png` — 서식 메모 (밝은 테마)
2. `2-code-dark.png` — JSON이 든 코드 메모 (어두운 테마)
3. `3-palette-dark.png` — Ctrl+K 찾기·명령
4. `4-secret-light.png` — 비밀 메모 가림막
5. `5-empty-dark.png` — 탭을 모두 닫은 첫 화면

창 안쪽(1280×720)을 150% 배율로 그린 것이라 제목 표시줄은 없습니다. 메모 내용은 모두 지어낸 예시(`sk-test-0000-EXAMPLE-ONLY`, `0000-1111-2222` 등)이며 실제 사용자 데이터는 쓰지 않았습니다.

## Store 로고 (선택)

Partner Center의 Store 로고(1:1 300×300 등)는 비워 두면 패키지 아이콘을 씁니다. 따로 올리려면 `assets\app_1024.png`를 줄여 쓰면 됩니다.

## Store 표시 이미지·트레일러 (언어별 목록 화면)
네 언어에 **같은 파일**을 올립니다(트레일러 영상·썸네일만 한국어판/영어판).

| 칸 | 파일 | 올리는 언어 |
|---|---|---|
| 2:3 포스터 아트 (1440×2160) | `art/poster_2x3_1440x2160.png` | 네 언어 모두 |
| 1:1 박스 아트 (2160×2160) | `art/box_1x1_2160x2160.png` | 네 언어 모두 |
| 16:9 수퍼히어로 아트 (3840×2160, 글자 없음) | `art/superhero_16x9_3840x2160.png` | 네 언어 모두 (트레일러를 맨 위에 띄우려면 필수) |
| 트레일러 영상 | `marketing/video/store_trailer/trailer_ko.mp4` | 한국어 |
| 〃 | `marketing/video/store_trailer/trailer_en.mp4` | 영어·일본어·중국어 |
| 트레일러 썸네일 (1920×1080) | `thumbnail_ko.png` / `thumbnail_en.png` (같은 폴더) | 영상과 같은 짝 |
| 선택 자막 (WebVTT) | `captions_ja.vtt`(일본어 목록), `captions_zh-Hans.vtt`(중국어 목록) | 영어 영상에 붙임 |

이미지 다시 만들기: `python packaging/msix/store_listing/make_store_art.py`, 트레일러 자료: `python marketing/video/store_trailer.py`
