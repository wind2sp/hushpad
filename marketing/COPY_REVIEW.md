# 홍보 문구 검수 (2026-11-15)

범위: `copy.md`(한국어·영어), `make_cards.py` 카드 문구(한국어·영어). `video/`는 건드리지 않았습니다.
사실(자동 저장, AES-256-GCM·scrypt·DPAPI, 캡처 제외, 단축키, 공개 전, "무료" 없음, Mac·언어 전환 "준비 중")은 그대로입니다.
`python make_cards.py`는 WARN 없이 끝났고(종료 코드 0), 문구가 바뀐 카드를 열어 넘침·어색한 줄바꿈이 없는지 확인했습니다.

## copy.md · 한국어 (10곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| 긴 설명 1단락 | 방금 복사한 주소 같은 것들요. | 같은 것들이요. | "것들요"는 비표준 축약 |
| 긴 설명 2단락 | 암호화된 파일로 남기 때문에 | 암호화된 파일로 저장되므로 | "남기"가 '남기다/남다'로 헷갈림 |
| 긴 설명 3단락 | 내보낼 때 Ctrl+Shift+C | 다른 곳에 붙일 때 Ctrl+Shift+C | "내보내기"는 앱의 다른 기능(파일 내보내기)과 혼동 |
| 긴 설명 3단락 | 방금 복사한 내용이 창도 뜨지 않은 채 새 메모가 됩니다 | 창을 띄우지 않고도 방금 복사한 내용이 새 메모가 됩니다 | 어순이 꼬인 문장 |
| 카드 06 캡션 | 붙여넣는 실수 | 붙여 넣는 실수 | 띄어쓰기 (홈페이지 표기와 통일) |
| 인스타그램 | Hushpad는 쓰는 대로 저장되고, 파일을 전부 암호화합니다 | 쓰는 대로 저장하고, … 암호화합니다 | 피동·능동이 한 문장에 섞임 |
| 스레드 1/5 | 이름은 hush(쉿)와 pad(메모장)를 붙였어요 | …를 붙여 지었어요 | 목적어와 서술어 호응 |
| 스레드 3/5 | 메모는 파일 하나씩 … 암호화해서 폴더 한 곳에 둡니다. / Dropbox 같은 동기화 폴더 | 메모는 하나씩 따로 파일로 만들어 … 암호화하고, 한 폴더에 모아 둡니다. / 동기화 폴더(Dropbox·OneDrive 등) | 어색한 "파일 하나씩", 특정 브랜드 하나만 쓰지 않음 |
| 메이커 소개글 | KEY=값 줄의 값만 복사를 지원합니다 | …JSON 정리(Ctrl+Alt+J)가 있고, KEY=값 줄에서는 값만 복사할 수 있습니다 | 명사 나열 + "~를 지원합니다" 번역투 |
| 보도자료 1단락 | Hushpad(허시패드)가 … 메모장을 곧 공개한다 | … 암호화 메모장 Hushpad(허시패드)가 곧 공개된다 | 제품이 자기 자신을 공개하는 주어 오류 |

## copy.md · English (3곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| Threads 3/5 | Put that folder in Dropbox if you like. | Sync it with Dropbox, OneDrive or similar if you like. | 브랜드 하나만 쓰지 않음 |
| Maker post | one too many screen shares made me build something better | after one too many nervous screen shares I built this | "something better"는 근거 없는 비교·상투어 |
| Long description | one-shortcut JSON cleanup | JSON cleanup on a shortcut | 억지 합성 형용사 |

## make_cards.py · 한국어 카드 (5곳)

| 카드 | 전 | 후 | 이유 |
|---|---|---|---|
| card_02 본문 | 만든 시각으로 구분돼 한 폴더에 모여요 | 만든 시각으로 구분되고, 모두 한 폴더에 모여요 | "구분돼 모여요"는 인과처럼 읽힘 |
| card_06 본문 | 값만 골라 복사할 수 있고요. | 값만 골라 복사할 수 있습니다. | 문장을 "~고요"로 끝내지 않음, "~요" 반복 완화 |
| card_07 본문 | 찍은 화면이 지금 메모에 들어갑니다 | 찍은 화면은 열린 메모에 바로 들어가요 | "지금 메모"가 어색 |
| card_08 보조 문구 | 창이 닫혀 있어도(트레이) 동작해요 | 창을 닫아도 트레이에서 동작해요 | 괄호 대신 문장으로 (첫 시안은 상자를 넘쳐 줄임) |
| link_card | 저장 버튼 없이 쓰고, 파일은 전부 암호화.\n화면을 공유해도 창이 안 보이는 메모장 | 저장 버튼 없이 쓰고 전부 암호화되는 메모장.\n화면을 공유해도 창이 보이지 않아요. | 명사형으로 끊긴 첫 줄 |

## make_cards.py · English cards (4곳)

| 카드 | 전 | 후 | 이유 |
|---|---|---|---|
| en/card_04 라벨 | 03 · Signature | 03 · Key feature | "Signature"는 이 자리에서 뜻이 모호함 |
| en/card_04 요점 | Capture without moving the window away | Capture without moving the window first | 자연스러운 표현 |
| en/card_06 본문 | messy JSON fixed with one shortcut | one shortcut to tidy messy JSON | 어색한 분사구 |
| en/card_07 설명 | are on your screen only —\nnever in the recording | show only on your screen,\nnever in the recording | 줄표(em dash) 습관 제거 |

## 손대지 않은 것
- 태그라인, 고정 문구 표, 해시태그, 15초 대본(한·영), X 글, 블로그 도입부: 이미 자연스러움
- 메이커 소개글의 "화면은 지금 한국어만 있고" 줄: 언어 전환 기능이 나오면 함께 고칠 줄
- 카드 08 알림 문구("클립보드를 메모로 저장했어요"): 앱 코드에 있는 실제 문구
