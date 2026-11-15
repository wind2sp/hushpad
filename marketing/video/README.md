# Hushpad 홍보 영상 (marketing/video)

YouTube 기능 소개 영상과 그 주변 파일 모음입니다. 영상·음악은 모두 코드로 만들었고, 외부 소스·스톡 이미지·음원 샘플은 쓰지 않았어요.

## 파일

| 파일 | 내용 |
|---|---|
| `hushpad_promo_ko.mp4` | 본편 한국어판. 1920×1080, 30fps, H.264 + AAC(배경 음악), 79초, 한국어 앱 화면 + 한국어 화면 글자 |
| `hushpad_promo_en.mp4` | 본편 영어판. 같은 편집, **영어 앱 화면** + 영어 화면 글자 |
| `shorts_ko.mp4`, `shorts_en.mp4` | 쇼츠. 1080×1920, 30초 (훅 + 캡처 안 찍힘 + 비밀 메모 + 자동 저장·암호화 + 아웃트로). 영어판은 영어 앱 화면 |
| `music/hushpad_bgm_main.wav`, `music/hushpad_bgm_shorts.wav` | 직접 합성한 배경 음악(79초 / 30초, 48 kHz 스테레오). MP4에 이미 들어 있음 |
| `subtitles/hushpad_promo.{ko,en,ja,zh-Hans}.srt` | 본편 자막 파일. 화면 글자와 같은 시각 |
| `thumbnail_ko.png`, `thumbnail_en.png` | 1280×720 썸네일 (영어판은 영어 앱 화면) |
| `storyboard.md` | 장면표(한/영), 훅 문구 후보와 고른 이유, 소리 구성 |
| `youtube.md` | 제목 후보, 설명(챕터·받는 곳·GitHub 포함), 태그, 고정 댓글, 종료 화면 배치 |
| `COPY_REVIEW.md` | 문구 검수 기록 |
| `render_video.py` | 영상·자막·썸네일을 만드는 스크립트 |
| `make_music.py` | 배경 음악 합성 (numpy·scipy) |
| `capture_shots.py` | 실제 Hushpad 화면을 일회용 시험 프로필에서 찍는 스크립트 → `shots/en`(기본), `shots/ko` |
| `verify.py` | MP4를 Qt로 열어 길이·해상도·fps·비트레이트·소리 트랙을 확인하고 프레임을 `qa/`에 뽑음. 소리는 풀어서 WAV와 어긋남·음량 비교 |
| `shots/` | 찍어 둔 앱 화면(가짜 예시 데이터만) |
| `qa/` | 확인용 정지 화면 (git에 안 올림) |

## 왜 화면에 자막을 넣은 언어별 버전인가
- 화면 글자가 곧 내용입니다. YouTube 피드·홈에서는 소리 없이 자동 재생되고 자막(CC)은 기본으로 꺼져 있어서, 글자를 화면에 넣어 두어야 처음 3초에 뜻이 전달돼요. 음악은 분위기용이라 일부러 작게(약 -18 LUFS) 넣었어요.
- 대신 언어마다 파일이 하나씩 필요해서 한국어판·영어판을 따로 만들었습니다. 영어판은 앱 UI도 영어로 바꿔서 찍었어요.
- SRT 4개는 접근성·번역용입니다. 한국어판에는 en·ja·zh-Hans를, 영어판에는 ko·ja·zh-Hans를 올리면 됩니다(같은 편집이라 시간이 그대로 맞아요).

## 다시 만들기
PySide6 6.12(Qt Multimedia 포함), numpy, scipy, 그리고 Hushpad 소스가 `C:\build_temp\hushpad`에 있어야 합니다. 창은 화면에 뜨지 않아요.

```
cd C:\build_temp\hushpad\marketing\video
python capture_shots.py                # 영어 앱 화면 다시 찍기 (선택). ko도 다시 찍으려면: python capture_shots.py en ko
python make_music.py                   # 배경 음악 WAV 2개 (약 1분)
python render_video.py srt             # 자막 4개
python render_video.py thumbs          # 썸네일 2개
python render_video.py ko              # 본편 한국어 (약 3~5분)
python render_video.py en              # 본편 영어
python render_video.py shorts_ko       # 쇼츠 한국어 (shorts 만 써도 같음)
python render_video.py shorts_en       # 쇼츠 영어
python render_video.py stills en 3 20  # 인코딩 없이 그 시각 화면만 qa\ 에 PNG로 (shorts_ko·shorts_en도 됨)
python verify.py                       # 확인 + 프레임 추출
```
- `python render_video.py all`은 자막·썸네일·영상 4개를 한 번에 만듭니다. 음악 없는 MP4가 필요하면 뒤에 `--silent`를 붙이세요.
- 문구는 `render_video.py` 위쪽 `TXT`에 언어별로 모여 있어요. 고치면 영상·자막을 다시 만드세요(자막 시간은 장면 길이에서 자동 계산).
- 장면 길이는 `timeline()`에서 바꿉니다. 훅 길이를 바꾸면 `make_music.py`의 `SPECS`도 맞춰야 "쉬—" 소리와 곡 시작이 화면과 맞아요.
- `capture_shots.py`는 사용자의 실제 보관 폴더를 건드리지 않습니다. `HUSHPAD_PROFILE`을 임시 폴더(`%TEMP%\hushpad_video_profile`)로 지정하고, 새 시험 보관함(암호 `test-pass-1234`)에 가짜 메모만 넣어서 찍어요. 개발용(python) 실행이라 '시작할 때 실행' 등록도 건드리지 않습니다.

## 화질 (인코딩)
- Qt(PySide6 6.12)의 FFmpeg에는 Windows Media Foundation 인코더(`h264_mf`)만 들어 있어요(libx264·QSV 없음). 비트레이트를 14·30 Mbps, CBR·ABR·품질 최고로 바꿔 봐도 이 영상에서는 **약 4~5 Mbps**에서 멈춥니다(품질 100이 상한, 프로필은 Constrained Baseline). H.265를 요청해도 H.264로 돌아가요.
- 대신 원본 프레임과 비교한 PSNR(Y)이 **약 47 dB**라 눈으로는 원본과 구분되지 않습니다. 화면이 대부분 정지·천천히 움직이는 그래픽이라 그 정도 비트로 충분해요. YouTube가 어차피 다시 인코딩합니다.
- 더 높은 비트레이트가 꼭 필요하면 ffmpeg(libx264)로 다시 인코딩해야 하는데, 이 PC에는 없어서 하지 않았어요.

## 음악
- `make_music.py`가 numpy로 파형을 직접 계산해 만든 곡이라 샘플·루프·외부 음원이 없습니다(저작권 문제 없음, 저작자 표시 필요 없음).
- 84 BPM, F장조. 훅 동안은 낮은 화음만 → 화면이 어두워질 때 잦아들고 "쉬—"(걸러 낸 잡음) → 로고와 함께 곡 시작 → 끝 3초 페이드아웃.
- 음량: 통합 약 -18 LUFS, 트루 피크 -6 dBTP 이하. MP4에는 AAC-LC 192 kbps로 들어가요.
- 음악을 바꾸고 싶으면: `--silent`로 무음 MP4를 만든 뒤 YouTube 스튜디오 → 편집기 → 오디오에서 오디오 보관함 곡을 고르면 됩니다.

## 업로드 확인 목록
- [ ] 한국어판 올리기: 제목·설명·태그는 `youtube.md` 한국어 부분
- [ ] 자막: 한국어판에 `en`, `ja`, `zh-Hans` SRT 추가(한국어 SRT는 선택)
- [ ] 영어판 올리기(또는 같은 채널에 영어 제목·설명 번역 추가)
- [ ] 썸네일: `thumbnail_ko.png` / `thumbnail_en.png`
- [ ] 설명 속 챕터 시간이 그대로인지(0:00, 0:16, 0:27, 0:43, 1:00) 미리보기에서 확인
- [ ] 설명의 받는 곳(https://gdra.mycafe24.com/hushpad/)·GitHub(https://github.com/wind2sp/hushpad) 링크가 열리는지, 홈페이지에 Windows·macOS 파일이 실제로 올라와 있는지
- [ ] 종료 화면: 1:10부터, 구독(왼쪽 아래) + 영상/재생목록(오른쪽 아래)
- [ ] 고정 댓글 달기
- [ ] 소리 크기: 휴대폰 스피커로 한 번 들어 보고 자막보다 튀지 않는지
- [ ] 공개 범위: 처음엔 '일부 공개'로 올려 링크로 확인한 뒤 공개
- [ ] 쇼츠: `shorts_ko.mp4`·`shorts_en.mp4`, 제목 끝에 `#Shorts`, 본편을 관련 동영상으로 연결
- [ ] 가짜 숫자·후기가 없는지, "곧 공개" 같은 옛 문구가 남지 않았는지 마지막으로 확인
