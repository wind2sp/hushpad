# Hushpad 홍보 영상 (marketing/video)

YouTube 기능 소개 영상과 그 주변 파일 모음입니다. 영상은 모두 코드로 그려서 만들었고, 외부 소스·스톡 이미지·음악은 쓰지 않았어요.

## 파일

| 파일 | 내용 |
|---|---|
| `hushpad_promo_ko.mp4` | 본편 한국어판. 1920×1080, 30fps, H.264, 79초, 자막(화면 글자) 포함, 소리 없음 |
| `hushpad_promo_en.mp4` | 본편 영어판. 같은 편집, 영어 화면 글자 |
| `shorts_ko.mp4` | 쇼츠 한국어판. 1080×1920, 30초 (훅 + 캡처 안 찍힘 + 비밀 메모 + 자동 저장·암호화) |
| `subtitles/hushpad_promo.{ko,en,ja,zh-Hans}.srt` | 본편 자막 파일. 화면 글자와 같은 시각 |
| `thumbnail_ko.png`, `thumbnail_en.png` | 1280×720 썸네일 |
| `storyboard.md` | 장면표(한/영), 훅 문구 후보 3개와 고른 이유 |
| `youtube.md` | 제목 후보, 설명(챕터 포함), 태그, 고정 댓글, 종료 화면 배치 |
| `render_video.py` | 영상·자막·썸네일을 만드는 스크립트 |
| `capture_shots.py` | 실제 Hushpad 화면을 일회용 시험 프로필에서 찍는 스크립트 → `shots/ko`, `shots/en` |
| `verify.py` | MP4를 Qt로 열어 길이·해상도·fps를 확인하고 프레임을 `qa/`에 뽑음 |
| `shots/` | 찍어 둔 앱 화면(가짜 예시 데이터만) |
| `qa/` | 확인용 정지 화면 |

## 왜 화면에 자막을 넣은 두 개 버전인가
- 이 영상은 소리가 없어서 화면 글자가 곧 내용입니다. YouTube 피드·홈에서는 소리 없이 자동 재생되고 자막(CC)은 기본으로 꺼져 있어서, 글자를 화면에 넣어 두어야 처음 3초에 뜻이 전달돼요.
- 대신 언어마다 파일이 하나씩 필요해서 한국어판·영어판 두 개를 만들었습니다.
- SRT 4개는 접근성·번역용입니다. 한국어판에는 en·ja·zh-Hans를, 영어판에는 ko·ja·zh-Hans를 올리면 됩니다(같은 편집이라 시간이 그대로 맞아요).
- 영상 속 앱 화면은 지금 버전이라 메뉴가 한국어예요. 영어판도 앱 메뉴는 한국어이고, 영어인 것은 화면 글자뿐입니다.

## 다시 만들기
PySide6 6.12(Qt Multimedia 포함)와 Hushpad 소스가 `C:\build_temp\hushpad`에 있어야 합니다. 창은 화면에 뜨지 않아요.

```
cd C:\build_temp\hushpad\marketing\video
python capture_shots.py                # 실제 앱 화면 다시 찍기 (선택, %TEMP%\hushpad_video_profile 에 새 시험 보관함을 만듦)
python render_video.py srt             # 자막 4개
python render_video.py thumbs          # 썸네일 2개
python render_video.py ko              # 본편 한국어 (약 2~4분)
python render_video.py en              # 본편 영어
python render_video.py shorts          # 쇼츠
python render_video.py stills ko 3 20  # 인코딩 없이 그 시각 화면만 qa\ 에 PNG로
python verify.py                       # 길이·해상도·fps 확인 + 프레임 추출
```
`python render_video.py all`은 위 자막·썸네일·영상을 한 번에 만듭니다.

- 문구는 `render_video.py` 위쪽 `TXT`에 언어별로 모여 있어요. 고치면 영상·자막을 다시 만드세요(자막 시간은 장면 길이에서 자동 계산).
- 장면 길이는 `timeline()`에서 바꿉니다.
- `capture_shots.py`는 사용자의 실제 보관 폴더를 건드리지 않습니다. `HUSHPAD_PROFILE`을 임시 폴더로 지정하고, 새 시험 보관함(암호 `test-pass-1234`)에 가짜 메모만 넣어서 찍어요.

## 음악
영상은 일부러 소리 없이 만들었습니다(사용권 있는 음악이 없어서). 넣고 싶으면:
1. YouTube 스튜디오 → 콘텐츠 → 영상 → **편집기** → **오디오** 트랙 → 'YouTube 오디오 보관함' 곡 중에서 고르기. 저작자 표시가 필요 없는 곡을 고르면 편합니다.
2. 또는 스튜디오 왼쪽 메뉴 **오디오 보관함**에서 받아서 편집 프로그램으로 넣어도 됩니다.
조용한 피아노나 로파이 계열이 "쉿." 분위기와 잘 맞아요.

## 업로드 확인 목록
- [ ] 한국어판 올리기: 제목·설명·태그는 `youtube.md` 한국어 부분
- [ ] 자막: 한국어판에 `en`, `ja`, `zh-Hans` SRT 추가(한국어 SRT는 선택)
- [ ] 영어판 올리기(또는 같은 채널에 영어 제목·설명 번역 추가)
- [ ] 썸네일: `thumbnail_ko.png` / `thumbnail_en.png`
- [ ] 설명 속 챕터 시간이 그대로인지(0:00, 0:16, 0:27, 0:43, 1:00) 미리보기에서 확인
- [ ] 종료 화면: 1:10부터, 구독(왼쪽 아래) + 영상/재생목록(오른쪽 아래)
- [ ] 고정 댓글 달기
- [ ] 오디오 보관함 음악 넣을지 결정
- [ ] 공개 범위: 처음엔 '일부 공개'로 올려 링크로 확인한 뒤 공개
- [ ] 쇼츠: `shorts_ko.mp4`, 제목 끝에 `#Shorts`, 본편을 관련 동영상으로 연결
- [ ] "무료"라는 말이 어디에도 없는지(가격 미정), 가짜 숫자·후기가 없는지 마지막으로 확인
