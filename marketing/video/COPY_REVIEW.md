# 영상 문구 검수 (2026-11-15)

범위: `subtitles/hushpad_promo.{ko,en,ja,zh-Hans}.srt`, `youtube.md`, `storyboard.md`, `render_video.py`의 화면 글자.
SRT는 `render_video.py`의 `TXT`에서 만들어지므로 `TXT`를 고친 뒤 `python render_video.py srt`로 다시 만들었습니다.
고치기 전 상태로 다시 만들면 원본과 바이트까지 같았고, 고친 뒤에도 자막 번호·시각은 그대로입니다. 줄 길이(영 42 / 한 22 / 일·중 16자, 최대 2줄)도 모두 지켰습니다.

## 화면 글자 + 자막 (render_video.py `TXT`)

| 키 | 언어 | 전 | 후 | 이유 |
|---|---|---|---|---|
| paste_rich / paste_plain | ko (화면 글자) | 붙여넣으면 서식 그대로 / 붙여넣으면 글자만 | 붙여 넣으면 서식 그대로 / 붙여 넣으면 글자만 | 띄어쓰기 오류. 홈페이지·홍보 문구 표기와 통일 |
| c3a | en | Secret notes open covered. Click to look. | Secret notes open hidden. Click to reveal. | "open covered", "Click to look"는 원어민이 보기에 어색함 |
| c3b | en | Copy one, and the clipboard clears in 30 s. | Copy it, and the clipboard clears in 30 seconds. | 자막 문장 속 "30 s" 약어, 가리키는 대상이 모호한 "one" |
| c3a | ja | 秘密メモは / 開くたびに隠れています | 秘密のメモは / 開くたびに伏せて表示 | 홈페이지 일본어(伏せて表示)와 통일. "隠れています"는 스스로 숨는 것처럼 읽힘 |
| c3a | zh | 秘密笔记 / 每次打开都是遮住的 | 机密笔记 / 每次打开都先遮住 | 홈페이지 용어(机密笔记)와 통일, 문장 다듬기 |
| c3b | zh | 复制以后， / 30 秒就从剪贴板清掉 | 复制后 30 秒， / 自动从剪贴板清除 | "清掉"는 너무 구어적이고, 의미 단위로 줄바꿈 |
| c5a | zh | HTML、JSON / 就放进代码笔记 | HTML、JSON / 放进代码笔记就行 | 앞 문장 없이 쓰인 "就" |
| c7a | zh | 剪贴板内容存成笔记 | 剪贴板直接存成笔记 | 핵심(창을 띄우지 않고 바로 저장)을 살림 |
| tag | zh | 安静地写， / 谁也看不见 | 安静记录， / 无人可见 | 승인된 중국어 태그라인(홈페이지)과 다름 → 통일 |
| soon | zh | 即将推出 | 即将发布 | 홈페이지 "即将发布"와 통일 |

ko·en 화면 글자 중 위 항목 말고는 고칠 곳이 없었습니다. 한국어 자막은 모두 자연스러워 그대로입니다(SRT 변화 없음).

## 다시 만든 영상
- `hushpad_promo_ko.mp4`(paste 라벨), `hushpad_promo_en.mp4`(c3a·c3b 자막)만 README 방법대로 다시 렌더링했습니다.
- `shorts_ko.mp4`와 썸네일은 바뀐 문구를 쓰지 않아 그대로 두었습니다.

## youtube.md

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| 한국어 설명 | HTML이나 JSON은 코드 메모에. 한 줄로 엉킨 JSON은 Ctrl+Alt+J로 정리돼요. | HTML이나 JSON은 코드 메모에 넣어 두고, 한 줄로 엉킨 JSON은 Ctrl+Alt+J로 정리해요. | 끊긴 문장 |
| 한국어 설명 | 3분까지의 화면 녹화(Ctrl+Alt+R)를 메모에 바로 넣어요 | 최대 3분짜리 화면 녹화(Ctrl+Alt+R)가 메모에 바로 들어가요 | "~까지의" 번역투 |
| 한국어 설명 | 트레이에 있어도 … 지금 클립보드가 메모로 저장돼요 | 창을 닫아 트레이에 있을 때도 … 클립보드 내용이 메모로 저장돼요 | 주어가 모호함 |
| 한국어 설명 | (영상 속 화면은 지금 버전이라 메뉴가 한국어예요.) | (영상 속 화면은 지금의 한국어 버전이에요.) | 합의한 표현(지금의 한국어 버전)으로 통일 |
| English description | Secret notes open covered | Secret notes open hidden | 자막과 통일 |
| English description | Ctrl+K finds anything. | Ctrl+K searches your notes and commands. | 과장("anything")을 사실대로 |
| English description | the current build, so its menus are in Korean | the current Korean build | 합의한 표현으로 통일 |

## storyboard.md

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| 머리말 | 앱 UI는 지금 한국어뿐이라… / The app UI is Korean-only for now | 영상 속 앱 화면은 지금의 한국어 버전이라…(앱 안 언어 전환은 준비 중) / The UI shown is the current Korean build | "한국어뿐"이라는 단정 대신 합의한 표현으로 |
| 장면 03 | (en) Secret notes open covered… 30 s. | Secret notes open hidden. Click to reveal. → …30 seconds. | 바뀐 화면 글자와 맞춤 |
| 장면 04 | 붙여넣으면 서식 그대로 / 붙여넣으면 글자만 | 붙여 넣으면 … | 바뀐 화면 글자와 맞춤 |

## 공개 문구로 바꿈 (2026-11-16, 영상팀)

앞선 검수 수정은 모두 그대로 두고, "곧 공개" 계열만 공개 문구로 바꿨습니다. `python render_video.py srt`로 다시 만들었고 자막 번호·시각은 그대로(20개, 바뀐 것은 19번 한 개).

| 키 | 언어 | 전 | 후 |
|---|---|---|---|
| soon → release (자막 19번) | ko | 곧 공개 / Windows · Mac 버전 준비 중 | 무료 오픈소스 앱이에요 / Windows와 macOS에서 받으세요 |
| | en | Coming soon for Windows and Mac | Free and open source, / for Windows and macOS. |
| | ja | 近日公開 / Windows・Mac版を準備中 | 無料のオープンソース / Windows・macOS対応 |
| | zh-Hans | 即将发布 / Windows、Mac 版准备中 | 免费开源 / 支持 Windows、macOS |
| soon_big → free_big (아웃트로 알약) | ko / en | 곧 공개 / Coming soon | 무료 · 오픈소스 / Free & open source |
| soon_small → free_small (아웃트로 한 줄) | ko / en | Windows · Mac 버전 준비 중 / Windows and Mac versions in the works | Windows 10/11 · macOS(Apple Silicon) / Windows 10/11 · macOS (Apple Silicon) |

`youtube.md`의 제목·설명·고정 댓글·쇼츠 제목도 공개 기준(무료·오픈소스, GPL-3.0-or-later, 받는 곳·GitHub 주소, Apple Silicon 전용, UI 4개 언어)으로 다시 썼습니다.
