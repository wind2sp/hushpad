# Hushpad SNS 홍보 키트

올리는 것은 직접 해 주세요(계정 로그인 필요). 글은 그대로 붙여 넣으면 되고, 첨부 파일 경로를 함께 적었습니다.
홈페이지 링크: https://gdra.mycafe24.com/hushpad/ · GitHub: https://github.com/wind2sp/hushpad

## 0. 먼저 해 둘 것
- **인스타그램 프로필 링크**에 홈페이지 주소를 넣어 두세요(본문 링크는 눌리지 않아요).
- **유튜브를 가장 먼저** 올리세요. 영상 주소가 생기면 다른 채널 글에 함께 걸 수 있어요.

## 1. 올리는 순서

| 날짜 | 채널 | 무엇을 | 첨부 |
|---|---|---|---|
| 1일차 오전 | YouTube | 본편(한국어) + Shorts(한국어) | `video\hushpad_promo_ko.mp4`, `video\shorts_ko.mp4`, `video\thumbnail_ko.png` |
| 1일차 오전 | YouTube | 본편(영어) + Shorts(영어), 영어 채널에 따로 올리거나 같은 채널에 함께 | `video\hushpad_promo_en.mp4`, `video\shorts_en.mp4`, `video\thumbnail_en.png` |
| 1일차 낮 | Instagram | 캐러셀 9장 + 스토리 | `cards\card_01~09.png`, 스토리: `cards\story_cover.png` 또는 `video\shorts_ko.mp4`(릴스) |
| 1일차 낮 | Threads | 5개 연재 | 글마다 카드 1장 (아래 표) |
| 1일차 저녁 | X | 짧은 글 1개 | `cards\link_card.png` 또는 Shorts 영상 |
| 2일차 | LinkedIn(회사) | 출시 소식 | `cards\link_card.png` |
| 2~3일차 | 블로그(네이버·티스토리) | 도입부 + 화면 설명 + 유튜브 넣기 | `cards\` 카드, 본편 영상 링크 |
| 3일차 이후 | 영어 채널(있으면) | 영어 글 | `cards\en\` |

- 모든 파일은 `C:\build_temp\hushpad\marketing\` 아래에 있어요.
- 해시태그는 게시물당 5개 이하로만 쓰세요.

## 2. YouTube
제목·설명(챕터 포함)·태그·고정 댓글·종료 화면·Shorts 제목: `video\youtube.md`에 한국어·영어로 다 있어요.
자막: `video\subtitles\` (본편 한국어판에는 en·ja·zh-Hans, 영어판에는 ko·ja·zh-Hans를 올리기).
음악은 이미 들어 있어요.

## 3. Instagram (한국어)
캐러셀 순서: card_01 → card_09. 카드별 캡션이 필요하면 `copy.md`의 "카드별 캡션".
```
쉿, 조용히 적는 메모장을 만들었습니다.

메모장 탭에 서버 비밀번호나 테스트용 API 키를 적어 둔 적 있으시죠. 탭이 서른 개쯤 쌓이면 찾기도 어렵고, 화면을 공유하다 그 탭이 비치면 난감합니다.

Hushpad는 쓰는 대로 저장하고, 파일을 전부 암호화합니다. Windows에서는 화면 공유나 스크린샷에 창이 찍히지 않습니다.

Windows 10·11과 Apple Silicon Mac에서 쓰는 무료 오픈소스 앱입니다. 프로필 링크의 홈페이지에서 받을 수 있어요.

#허시패드 #Hushpad #메모장 #오픈소스 #생산성
```

## 4. Threads (한국어, 5개 연재)
`copy.md`의 "스레드(Threads) 연재 (5개 글)"를 순서대로 올리세요. 첨부: 1/5 card_01 · 2/5 card_02 · 3/5 card_03 · 4/5 card_04 · 5/5 card_09.
유튜브를 올렸다면 5/5 끝에 영상 주소를 한 줄 더해도 좋아요.

## 5. X (한국어)
```
Windows에서는 화면을 공유해도 상대에게 안 보이는 메모장을 만들었습니다. 쓰는 대로 저장되고 파일은 전부 암호화돼요. Mac판도 있는 무료 오픈소스입니다(macOS 15 이상에서는 일부 화면 공유 앱에 보일 수 있어요).
https://gdra.mycafe24.com/hushpad/
```

## 6. LinkedIn (회사 페이지 또는 개인)
```
나인로우파트너스가 Hushpad(허시패드)를 무료 오픈소스로 공개했습니다.

서버 비밀번호나 API 키를 메모장 탭에 잠깐 적어 두는 일은 어느 팀에서나 흔합니다. Hushpad는 그런 메모를 쓰는 동안 바로 저장하고, 메모 하나하나를 암호화된 파일로 만들어 한 폴더에 모아 둡니다. Windows에서는 창이 화면 공유와 스크린샷에 찍히지 않아, 회의 중에 메모를 띄워 둬도 내 모니터에만 보입니다.

- Windows 10·11, Apple Silicon Mac
- 설치 없이 압축만 풀면 실행, 계정·서버 없음
- 한국어·영어·일본어·중국어 화면
- GPL-3.0-or-later 오픈소스

홈페이지: https://gdra.mycafe24.com/hushpad/
소스 코드: https://github.com/wind2sp/hushpad
```

## 7. 블로그
`copy.md`의 "블로그(네이버·티스토리) 도입부 (약 600자)"로 시작하세요. 이어서 카드 02~08을 순서대로 넣어 화면을 설명하고, 본편 영상을 넣은 뒤 홈페이지 링크로 마무리하면 됩니다.

## 8. 영어 채널 (있을 때)
Instagram·Threads·X 영어 글은 `copy.md`의 English 부분에 있어요. 첨부는 `cards\en\`, 영상은 `video\*_en.mp4`.
LinkedIn 영어판:
```
NINEROW partners has released Hushpad, a free and open-source notepad for Windows and Apple silicon Macs.

A lot of teams jot server passwords and API keys into Notepad tabs "just for a minute". Hushpad saves those notes as you type and keeps each one as an encrypted file in a folder you choose. On Windows, its window doesn't show up in screen shares or screenshots, so a note you leave open during a call stays on your screen and off everyone else's.

- Windows 10/11 and Apple silicon Macs
- Portable: unzip and run, no account, no server
- UI in Korean, English, Japanese and Simplified Chinese
- Open source under GPL-3.0-or-later

Website: https://gdra.mycafe24.com/hushpad/
Source: https://github.com/wind2sp/hushpad
```

## 9. (선택) AI로 만들었다는 한 줄
밝히고 싶을 때 글 끝에 한 줄 더하세요.
- 한국어: `만드는 과정에서 AI(Claude)의 도움을 많이 받았습니다.`
- English: `We built it with a lot of help from AI (Claude).`

## 10. 올린 뒤
- 첫날은 댓글에 빨리 답해 주세요. 질문이 반복되면 홈페이지 FAQ나 GitHub Discussions로 옮겨 두면 좋아요.
- 버그 이야기는 GitHub 이슈(https://github.com/wind2sp/hushpad/issues/new/choose)로 안내하세요.
- 사용 후기를 받으면 다음 홍보 카드에 쓸 수 있어요. 카드에 싣기 전에 작성자에게 동의를 받으세요.
