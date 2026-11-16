# Hushpad 출시 홍보 조사 (2026-11-16)

조사만 했고, 어디에도 글·댓글·PR·포크·계정 생성은 하지 않았습니다.
기준 사실: 저장소 첫 커밋 2026-11-15(커밋 23개), 별 0개, 기여자 1명(회사), GPL-3.0-or-later, 서명 안 된 포터블 zip(Win x64 / macOS arm64), 영어 README 있음, `tests/`·GitHub Actions(`build-macos.yml`) 있음, 데이터는 `%APPDATA%`·`%LOCALAPPDATA%\Hushpad`(macOS `~/Library/Application Support/Hushpad`)에 저장(실행 파일 폴더가 아님).

> 공통 주의: 2026년 들어 여러 곳이 **AI로 만든 프로젝트·AI로 쓴 글**을 막거나 공개를 요구합니다(HN, r/opensource, Lissy93 awesome-privacy, 0PandaDEV awesome-windows, r/selfhosted). 글·PR 본문은 사람이 직접 쓰고, 개발 과정에 AI를 썼다면 요구하는 곳에서는 솔직하게 밝히는 편이 안전합니다.
> 표시: ✅ 1차 출처(공식 규칙)에서 확인 / ⚠️ 2차 출처나 미러라 게시 전에 공식 페이지 재확인 필요.

---

## 1. GitHub awesome 목록

| # | 목록 | 별 / 최근 push | 들어갈 섹션 | 판정 |
|---|---|---|---|---|
| 1 | [jaywcjlove/awesome-mac](https://github.com/jaywcjlove/awesome-mac) | 118.6k / 2026-11-15 | Reading and Writing Tools › **Note-taking** | **GO** |
| 2 | [serhii-londar/open-source-mac-os-apps](https://github.com/serhii-londar/open-source-mac-os-apps) | 51.4k / 2026-10-31 | categories `notes` (+`security`) | **GO** |
| 3 | [tehtbl/awesome-note-taking](https://github.com/tehtbl/awesome-note-taking) | 1.0k / 2026-04-20 | Open Source › **Native GUI** | **GO** |
| 4 | [iCHAIT/awesome-macOS](https://github.com/iCHAIT/awesome-macOS) | 19.5k / 2026-10-21 | Applications › **Productivity** (또는 Security) | **GO** (채택률 낮음) |
| 5 | [0PandaDEV/awesome-windows](https://github.com/0PandaDEV/awesome-windows) | 3.2k / 2026-11-06 | **Note-taking** | **LATER** (별 50) |
| 6 | [pluja/awesome-privacy](https://github.com/pluja/awesome-privacy) | 20.3k / 2026-11-14 | **Notes and Tasks** | **LATER** (보안 도구 ≈1년) |
| 7 | [Lissy93/awesome-privacy](https://github.com/Lissy93/awesome-privacy) | 10.1k / 2026-11-14 | **Digital Notes** | **LATER** (안정판 4개월+, 별 100) |
| 8 | [darjeeling/awesome-kr-foss](https://github.com/darjeeling/awesome-kr-foss) | 63 / 2026-03-02 | **Tools** (또는 Python) | **LATER** (패키지 관리자 설치) |
| 9 | [sobolevn/awesome-cryptography](https://github.com/sobolevn/awesome-cryptography) | 7.2k / 2026-07-15 | Tools › Standalone | **NO** (암호 도구·라이브러리 목록, 메모 앱은 안 맞음) |
| 10 | [Awesome-Windows/Awesome](https://github.com/Awesome-Windows/Awesome) | 28.2k / 마지막 push 2024-07-31 | – | **NO** (저장소 페이지가 404, 2년 넘게 멈춤) |
| – | JesseTG/awesome-qt | 1.6k / archived | – | **NO** (보관됨) |
| – | Privacy Guides | – | – | **NO** (개발자 본인은 홍보 글을 못 올림, 아래 2장) |

별·push 날짜는 2026-11-16에 GitHub API로 확인.

### 1-1. awesome-mac — GO
- 규칙 ✅ ([CONTRIBUTING](https://github.com/jaywcjlove/awesome-mac/blob/master/docs/CONTRIBUTING.md)): 제안 하나당 PR 하나, 카테고리 안에서 **알파벳순**, `[List Name](link)` 형식(AP 제목 대소문자), 설명은 한 문장, 별·나이 기준 없음. AI 도움은 괜찮지만 같은 규칙을 따라야 함. **README.md·README-zh·README-ja·README-ko 4개를 같이 맞추는 것**이 권장됨(Hushpad는 ko/ja/zh를 다 지원하니 유리).
- 형식 예(기존 줄):
  `* [Joplin](https://joplinapp.org/) - Cross-platform open-source notepad with markdown support and to-do list management. [![Open-Source Software][OSS Icon]](https://github.com/laurent22/joplin) ![Freeware][Freeware Icon]`
- 서명 안 된 앱을 막는 규칙은 없음. 설명에 "Apple Silicon only"를 쓰는 것을 권장.

### 1-2. open-source-mac-os-apps — GO
- 규칙 ✅ ([CONTRIBUTING](https://github.com/serhii-londar/open-source-mac-os-apps/blob/master/CONTRIBUTING.md), [PR 템플릿](https://github.com/serhii-londar/open-source-mac-os-apps/blob/master/PULL_REQUEST_TEMPLATE.md)): README가 아니라 `applications.json`을 고침, PR당 하나, 설명은 마침표로 끝냄, 카테고리는 [categories.json](https://github.com/serhii-londar/open-source-mac-os-apps/blob/master/categories.json)에서 고름(`notes`, `security`, `productivity`). 받지 않는 경우: "최근 커밋 없음", "README가 불분명하거나 영어가 아님", 라이선스 없음. 체크리스트: 2년 안 커밋, 영어 README, 스크린샷.
- Python 앱도 실려 있음(Vorta, OnionShare, calibre 등).
- 형식 예(최근 `notes` 항목의 구조):
  `{"title": "...", "short_description": "....", "categories": ["notes", "productivity"], "repo_url": "https://github.com/...", "icon_url": "...", "screenshots": ["..."], "official_site": "...", "languages": ["swift"]}` → Hushpad는 `"languages": ["python"]`.

### 1-3. awesome-note-taking — GO
- 규칙 ✅ ([contributing.md](https://github.com/tehtbl/awesome-note-taking/blob/master/contributing.md)): 형식 ``- [icons] [Tool Name](URL) - Brief description ending with a period. `LICENSE` `Tech/Language` ``; 오픈소스면 SPDX 라이선스와 기술 스택 필수; 최근 12개월 안 커밋; 카테고리는 하나(Qt 앱 → **Native GUI**).
- 아이콘: 📕(DB·독자 형식으로 저장), 🔒(**종단간 암호화** 지원). Hushpad는 동기화가 없는 로컬 저장 시 암호화(at rest)라서 🔒를 붙이려면 PR에서 "로컬 암호화이고 E2EE 동기화는 아님"을 밝히거나 붙이지 않는 편이 정확.
- 형식 예: ``- 📕 [Cherrytree](http://www.giuspen.com/cherrytree) - A hierarchical note-taking app featuring rich text and syntax highlighting. `GPL-3.0` `Qt/C++` ``
  → Hushpad: `` `GPL-3.0-or-later` `Qt/Python` ``

### 1-4. iCHAIT/awesome-macOS — GO (채택률 낮음)
- 규칙 ✅ ([contributing.md](https://github.com/iCHAIT/awesome-macOS/blob/master/.github/contributing.md), [PR 템플릿](https://github.com/iCHAIT/awesome-macOS/blob/master/.github/PULL_REQUEST_TEMPLATE.md)): 알파벳순, 마침표, OSS 아이콘(소스 링크)·Freeware 아이콘, **Electron 금지**(Qt는 괜찮음), AI 래퍼 금지, **템플릿을 안 채우면 바로 닫음**. 추천이 더 필요한 PR에는 ["needs endorsement" 라벨](https://github.com/iCHAIT/awesome-macOS/pulls?q=is%3Apr+is%3Aopen+label%3A%22needs+endorsement%22)이 붙고 투표를 기다림 → 별이 0개면 오래 걸릴 수 있음.
- 형식 예: `- [Clipbara](https://github.com/mobrava/Clipbara) - Free Paste-like clipboard manager with pinboards, Quick Look previews, and one-click copying. [![Open-Source Software][OSS Icon]](https://github.com/mobrava/Clipbara) ![Freeware][Freeware Icon]`

### 1-5. 0PandaDEV/awesome-windows — LATER (별 50 + 30일)
- 규칙 ✅ ([CONTRIBUTING](https://github.com/0PandaDEV/awesome-windows/blob/main/CONTRIBUTING.md)): **GitHub 별 50개 이상**이고, 첫 커밋 후 30일 이상 지났거나 최근 30일 안에 커밋이 있어야 함. 알파벳순, `* [List Name](link)`, "awesome"해야 함, "Vibecoded slop"은 거절. README 머리말에 **AI로 만든 PR·기여 금지**가 적혀 있음 → 사람이 직접 PR을 쓸 것. "Add Application" 이슈 템플릿으로 제출하면 PR이 자동으로 만들어짐.
- 형식 예: `* [Joplin](https://joplinapp.org/) - Open-source note-taking app with Markdown support, cross-device sync and encryption. [![Open-Source Software][oss]](https://github.com/laurent22/joplin)`
- 현재 Windows용으로 큰 목록 중 유지되는 곳은 사실상 여기뿐(원조 Awesome-Windows/Awesome은 멈춤).

### 1-6. pluja/awesome-privacy — LATER (6개월 이상, 보안 도구는 약 1년)
- 규칙 ✅ ([Contributing.md](https://github.com/pluja/awesome-privacy/blob/main/misc/Contributing.md), [PR 템플릿](https://github.com/pluja/awesome-privacy/blob/main/.github/PULL_REQUEST_TEMPLATE.md)): "알리려는 곳이 아니라 오래 버틴 것을 싣는 곳"이라고 명시. **6개월 이상 꾸준한 작업**, 실제 사용자층(별 몇 개짜리 새 저장소는 "아직"), 계정 없이 쓰기, 텔레메트리 없음. **암호화를 다루는 보안 도구는 약 1년 이상**. 자체 제출은 **관계를 밝히면** 받고, 숨기면 닫음. 낮은 노력·AI 생성 제출은 검토 없이 닫음. `data/sections/*.yaml`을 고침(README는 생성됨), 설명은 마케팅 단어 없는 한 문장, PR은 월 단위로 몰아서 검토. 봇이 나이·커밋 이력·외부 기여자·자기 소유 여부를 검사함.
- 형식 예(YAML): `- name: Example` / `url: https://example.org` / `repo: https://github.com/example/example` / `description: What it is, plus the privacy property that matters.` (+ `platforms: [windows, macos]`, `tags: [no-account, offline]`)
- 기준 시점: 2027-05(6개월) 이상, 실제로는 **2027-11쯤(1년)**.

### 1-7. Lissy93/awesome-privacy — LATER (안정판 4개월 이상, 별 100개)
- 규칙 ✅ ([CONTRIBUTING](https://github.com/Lissy93/awesome-privacy/blob/main/.github/CONTRIBUTING.md)): 새로 만든 저장소는 안 되고 **첫 안정판(알파·베타 아님)이 4개월 이상** 지나야 함, 자동 검사에서 **별 100개 이상·저장소 4개월 이상·라이선스 있음**을 봄, `awesome-privacy.yml` 수정, PR 제목은 `Adds [software-name] to [section-name]`, 카테고리 **맨 아래에 추가**(알파벳순 아님), 설명 50–250자에 광고처럼 쓰지 말고 **단점도 적기**, 관계 공개 필수, 14일 안에 응답. **설명과 PR 본문은 사람이 쓸 것**(AI는 YAML 손질·번역 정도만, 많이 썼으면 밝힐 것). AI로 대부분 만들고 제대로 검토하지 않은 프로젝트는 싣지 않음.
- 형식 예(YAML): `- name: Standard Notes` / `url: https://standardnotes.com` / `github: standardnotes/app` / `openSource: true` / `description: | …`
- 기준 시점: 안정판 1.0 출시 후 4개월 + 별 100개.

### 1-8. awesome-kr-foss — LATER
- 조건 ✅ ([README](https://github.com/darjeeling/awesome-kr-foss)): 주요 작성자가 한국인이거나 한국 회사가 유지보수(충족), **CI·충분한 테스트·문서**, **그 플랫폼에 패키지 관리자가 있으면 그것으로 설치 가능해야 함** → winget 등록 뒤에 내는 것이 맞음. 규모(별 63)는 작지만 한국 개발자에게 보임.
- 형식 예: `- [fzf](https://github.com/junegunn/fzf) — ⚡ A command-line fuzzy finder. (junegunn Choi)` → 끝 괄호에 회사 이름 `(NINEROW partners)`.

---

## 2. 커뮤니티

| 채널 | 적합도 | 지금 올릴 수 있나 |
|---|---|---|
| Hacker News (Show HN) | **높음** | 가능. 단 새 계정은 Show HN 제한 ⚠️ |
| GeekNews (Show GN) | **높음** | 가능 |
| r/macapps | 중~높음 | 가능 ⚠️ |
| V2EX 分享创造 | 중~높음 | 가능 ⚠️ |
| Qiita / Zenn (기술 글) | 중 | 가능(제품 광고가 아니라 기술 글로) |
| Clien 자료실 | 중 | 가능 ⚠️ |
| Disquiet | 중 | 가능(계정 필요) |
| r/Python (Showcase) | 중 | 가능 ⚠️ |
| r/software, r/windows, r/QtFramework | 중 | 규칙 확인 못 함 ⚠️ |
| Product Hunt | 중~낮음 | 가능, 나중이 나음 |
| r/privacy | 중~낮음 | 개발자 규칙 따로 있음 ⚠️ |
| はてなブックマーク | 간접 | 직접 밀지 말 것 |
| OKKY, 루리웹, 뽐뿌 | 낮음 | 규칙 확인 못 함 |
| r/opensource | **안 됨** | 1년 유지·기여자 3명 이상·계정 1년 |
| r/selfhosted | **안 됨** | 서버 앱이 아님(새 프로젝트는 금요 메가스레드로만) |
| Privacy Guides 포럼 | **안 됨** | 개발자는 홍보 글을 못 올림 |

### Hacker News — Show HN (높음)
- 규칙 ✅ [Show HN 가이드](https://news.ycombinator.com/showhn.html): 제목은 `Show HN:`으로 시작, **바로 써 볼 수 있는 것**(가입·이메일 요구 없음, Hushpad는 충족), 직접 만들었고 토론에 응할 수 있어야 함, 블로그 글·랜딩 페이지·자잘한 업데이트는 안 됨, **지인에게 추천·댓글을 부탁하지 말 것**(voting ring).
- 규칙 ✅ [HN 가이드라인](https://news.ycombinator.com/newsguidelines.html): 대문자·느낌표로 제목 꾸미지 않기, 홍보 위주로 쓰지 않기, **"생성된 글이나 AI로 다듬은 글을 올리지 말 것"**(댓글), 자동 게시 금지.
- ⚠️ 2026-03 AI 스팸이 늘어 새 계정의 Show HN을 제한한다고 dang이 밝힘([요약](https://keydiscussions.com/2026/03/09/hacker-news-moves-toward-restricting-show-hn-posts-amid-the-ai-slop-wave/)) → **오래 활동한 계정으로** 올릴 것.
- 형식: 제목 예 `Show HN: Hushpad – an encrypted notepad that stays out of screenshots and screen shares` (80자 안팎, 최상급 표현 금지). URL은 **GitHub 저장소**(소스를 바로 볼 수 있어 신뢰가 큼). 올린 직후 작성자가 첫 댓글로 만든 이유, 위협 모델(DPAPI·Keychain 키 캐시, scrypt+AES-GCM), 한계(macOS 15+ 일부 캡처 앱, 서명 없음), 회사 소개를 짧게 적기.
- 시간: 미국 동부 평일 오전(한국 시간 밤 10시~자정)이 관행(공식 규칙 아님). 그 뒤 몇 시간은 댓글에 바로 답할 수 있게 비워 둘 것.
- 함정: "military-grade" 같은 마케팅 말투, 서명 안 된 바이너리를 두고 나오는 질문(재현 빌드·SHA256 안내를 준비), "왜 Electron이 아니라 Python이냐 / 왜 그냥 VeraCrypt가 아니냐" 같은 비교 질문.

### GeekNews — Show GN (높음)
- 규칙 ✅ [Show GN 안내](https://news.hada.io/blog/show), [가이드라인](https://news.hada.io/guidelines): **직접 써 볼 수 있는 것만**(블로그·랜딩·뉴스레터 안 됨), 만든 사람이거나 참여했어야 하고 질문에 답할 수 있어야 함, 제목 형식 **`서비스·프로젝트명 - 핵심 기능`**(Show 유형을 고르면 "Show GN:"이 붙음), 동기·수치·홍보 문구는 본문에, 본문에는 무엇인지·누가 어떻게 쓰는지·만든 이유·기존과의 차이·원하는 피드백을 **마케팅 말투 없이** 적기, 직접 만든 것임을 밝히기, **YouTube 링크 안 됨**, 추천 부탁·여러 프로젝트 연달아 올리기·같은 프로젝트 다시 올리기 안 됨(큰 업데이트도 예외 아님).
- 제목 예: `Hushpad - 화면 공유·스크린샷에 안 잡히는 암호화 메모장`
- 링크: GitHub 또는 홈페이지(한국어). 본문에 다운로드·SHA256·서명 없음 안내.
- 함정: 한 번밖에 못 올리니 **README·홈페이지·릴리스가 완성된 뒤** 올릴 것.

### Reddit
공통 ⚠️: reddit.com은 자동 조회가 막혀 각 서브레딧 사이드바를 직접 읽지 못했습니다. 아래는 2차 출처라 **올리기 전에 사이드바·고정 글을 직접 확인**해야 합니다. 일반 관행은 홍보 10% 이하, 링크만 올리지 말고 본문을 쓸 것, 계정 활동 이력.
- **r/opensource — 지금은 안 됨** ⚠️: 2026-10-24 새 규칙으로 AI를 쓴 프로젝트·AI가 만든 프로젝트 금지, **1년 이상 유지보수, 기여자 3명 이상, 게시 계정 1년 이상**([WinBuzzer](https://winbuzzer.com/2026/10/27/reddits-open-source-forum-bans-ai-assisted-projects-xcxwbn/), [Linux Magazine](https://www.linux-magazine.com/Online/News/r-opensource-Bans-AI-Assisted-and-AI-Related-Projects)).
- **r/selfhosted — 해당 없음** ⚠️: 자체 호스팅 앱이 아님. 3개월 안 된 새 프로젝트는 금요일 "New Project Megathread"에만 올릴 수 있고 따로 올린 글은 지움, AI 관여를 밝힐 것(2026-04 "Quarter 2 Update" 모더레이터 공지를 검색 결과 미러로 확인, 배경: [noted.lol](https://noted.lol/is-vibe-coding-killing-our-interest-in-new-self-hosted-apps-poll)).
- **r/macapps — 중~높음** ⚠️: 자기 홍보는 받되 태그·플레어를 달라는 안내가 미러에 있음. 최근 "저품질 vibe-coding 앱이 늘었다"는 PSA가 있어 반감이 있음. 제목에 `[Free][Open Source]`, 본문에 스크린샷·Apple Silicon 전용·서명 없음과 여는 방법·소스 링크. **Gatekeeper를 끄라고 안내하지 말고** 우클릭 › 열기만 안내.
- **r/privacy — 중~낮음** ⚠️: "Submission Rules for Developers"라는 별도 규칙이 있다는 것만 확인됨(내용은 못 봄). 소스 공개·관계 공개·위협 모델을 정확하게 쓸 것("스크린샷에 안 잡힘"을 과장하지 않기, 휴대폰 카메라·악성코드는 막지 못한다고 적기).
- **r/Python — 중(기술 측면)** ⚠️: Showcase 플레어 글에는 **본문 설명 + 소스 링크 필수**([flair 위키 미러](https://axebps-redlib.hf.space/r/Python/wiki/flair)). 제품 소개보다 "PySide6로 SetWindowDisplayAffinity·DPAPI를 쓴 방법" 같은 기술 이야기가 먹힘.
- **r/software, r/windows, r/QtFramework** ⚠️: 규칙을 확인하지 못함. r/software는 무료 프로그램 공유 글이 흔함. r/windows는 개발자 홍보를 주간 스레드로 모는 경우가 많으니 사이드바 확인.

### Product Hunt (중~낮음)
- ✅ [공식 Launch Guide](https://help.producthunt.com/en/collections/19793093-launch-guide)(목차: 어떤 제품이 Featured 되나, 홍보 방법과 피할 것, 다시 출시하기). 규칙을 어기면 Featured에서 빠지거나 지워지고 메이커가 영구 차단될 수 있음. ⚠️ 누구나 올릴 수 있고 hunter가 필요 없음, 한 달 전까지 예약 가능, 다시 출시는 큰 업데이트가 있을 때만(약 6개월)([요약](https://blog.innmind.com/how-to-launch-on-product-hunt-in-2026/)). **"upvote 해 달라"고 직접 부탁하면 안 됨.**
- 무료 OSS도 올릴 수 있지만 PH는 영어권 SaaS·준비된 홍보(갤러리·영상·첫 댓글)가 유리함. HN·GeekNews 반응을 보고 별·후기가 생긴 뒤에 내는 편이 나음.

### AlternativeTo — 디렉터리지만 커뮤니티 효과가 큼(3장)

### 한국
- **GeekNews**: 위 참고.
- **Disquiet (중)**: Product Hunt를 본뜬 한국 메이커 커뮤니티([소개](https://www.venturesquare.net/930900/)). 메이커로그("어떤 작업을 하고 있나요?") 글과 프로덕트 페이지가 있고 글쓰기에는 계정이 필요함([disquiet.io](https://disquiet.io/)). 프로덕트 등록 절차·규칙 문서는 못 찾음 ⚠️. 제작기("왜 화면 공유에 안 잡히는 메모장을 만들었나")를 메이커로그로 쓰는 방식이 맞음.
- **Clien (중)** ✅ [이용규칙](https://www.clien.net/service/board/rule/10707403): "일반 회원인 척 홍보 글을 쓰면 안 됨"(2-2), 바이럴·전문적인 판매·홍보(앱 포함)는 금지이고 관리자 허가나 **직접홍보 게시판**은 예외(2-3, 2026-05-18 추가). **자료실**(PC자료)에는 `[자작]`·`[오픈소스]` 말머리 글이 실제로 올라옴([자료실](https://www.clien.net/service/board/pds)), 이메일 인증이 필요함. → 회사 제품이므로 **회사가 만들었다고 밝히고** 자료실 PC자료에 `[오픈소스]`로 올리거나, 애매하면 직접홍보 게시판을 쓰거나 운영진에게 먼저 물어보기. 모두의공원·알뜰구매는 맞지 않음(알뜰구매는 할인 정보용).
- **OKKY (낮음)**: 개발자 커뮤니티지만 홍보 규칙 문서를 찾지 못함 ⚠️([OKKY 광고 안내 PDF](https://file.okky.kr/adguide/2021/1614322464281.pdf)는 유료 광고만 다룸). 기술 글이 아니면 굳이 올리지 않기.
- **루리웹·뽐뿌 (낮음)**: 일반 사용자 커뮤니티라 회사 제품 홍보로 보이기 쉬움. 조사 대상에서 뺌.

### 일본
- **Qiita (중)** ✅ [커뮤니티 가이드라인](https://help.qiita.com/ja/articles/qiita-community-guideline): 홍보·판매가 주목적인 글은 안 됨. 단 **자사·자작 기술 해설이 주목적이면 홍보로 보지 않음**. AI 사용은 되지만 내용을 확인하고 올릴 것.
- **Zenn (중)** ✅ [가이드라인](https://zenn.dev/guideline): 제품 홍보가 주목적인 글은 피하고, **홍보는 글 끝의 고정 메시지 정도**가 바람직함, AI는 써도 되지만 확인 없이 올리거나 마구 찍어내지 말 것, 직접 겪은 경험·고찰을 권장.
  → 글감 예: 「PySide6でスクリーンショット・画面共有に映らないウィンドウを作る(SetWindowDisplayAffinity / NSWindow.sharingType)」「DPAPIとKeychainでパスフレーズ鍵をキャッシュする」 + 끝에 Hushpad 링크 한 줄.
- **はてなブックマーク (간접)**: 공식 가이드라인 페이지를 찾지 못함 ⚠️. Qiita·Zenn 글이 북마크되며 퍼지는 구조라 **자기 북마크로 밀어 올리기·여러 계정 금지**를 전제로 하고 따로 하지 않기.

### 중국어권
- **V2EX 分享创造 (중~높음)** ✅ [노드 페이지](https://www.v2ex.com/go/create): "자신의 최신 작품을 올리라"는 작품 공유 노드. 별도 규칙은 페이지에 없음 ⚠️(사이트 전반에 새 계정 제한이 있을 수 있음). 중국어로 쓰고, 간체 UI 지원·macOS(Apple Silicon) 사용자가 많다는 점이 맞음. 제목 예: `[开源] Hushpad：不会被截图/录屏/屏幕共享看到的加密记事本(Windows/macOS)`. 본문에 GitHub·다운로드·만든 이유·회사 공개. 같은 글을 다시 올리지 않기.

---

## 3. 디렉터리·패키지 관리자

| 곳 | 요건 | 서명 안 된 포터블 zip | 품 | 판정 |
|---|---|---|---|---|
| **AlternativeTo** | 계정+이메일 인증, 영어 지원, 공개 출시 | 가능 | 낮음(대기 김) | **GO** |
| **winget** | 공식 출처의 버전 고정 URL, zip+nested `portable` 지원, 보안 검사 통과 | 형식상 가능(Defender 오탐 위험) | 중간 | **GO**(검사 위험) |
| **Softpedia** | 플랫폼별 제출 폼 ⚠️ | 가능 | 낮음 | GO ⚠️ |
| **MajorGeeks** | 이메일 제출, VM에서 직접 시험, 별 4개 이상 수준 | 가능 | 낮음 | GO(채택 불확실) |
| **Uptodown** | Developers Console, 편집팀 심사, 무료 | 가능 ⚠️ | 낮음~중간 | GO ⚠️ |
| **Scoop Extras** | 이슈 먼저, **별 100 이상 그리고/또는 포크 50**, 영어 UI | 가능 | 중간 | **LATER** |
| **Homebrew Cask** | 별 75(**본인 제출은 225**)/포크·워처 기준, 저장소 30일 이상, **Gatekeeper 통과** | **불가**(서명·공증 필요) | 높음 | **NO**(지금) |

### AlternativeTo — GO
- ✅ [FAQ](https://alternativeto.net/faq): 이메일 인증된 계정 → 사용자 메뉴 "Suggest new application" → 플랫폼·라이선스·설명·태그 입력. **영어 지원 필수**, 비공개·초대 전용 베타는 안 됨, 설명에 링크·이메일을 넣지 말 것(URL 칸 사용). 심사 대기열이 길어 기간을 약속하지 않고, **유료 우선 심사(1–2영업일)** 선택지가 있음(승인 보장은 아님). 다른 앱 페이지에서 "Contribute to this page › Suggest Alternatives"로 대안 등록, 대안은 주 기능이 같아야 함. 개발자 접근 권한을 신청할 수 있음.
- 대안으로 걸 대상(주 기능이 같은 것): Windows Notepad, Microsoft Sticky Notes, Standard Notes, Joplin, Simplenote, Notesnook, Apple Notes.
- 태그: privacy, encrypted, offline, portable, no-account, open source.

### winget (Windows Package Manager) — GO, 단 보안 검사 위험
- ✅ [정책](https://github.com/microsoft/winget-pkgs/blob/master/doc/Policies.md): MSIX·MSI·EXE 설치 파일은 **`.zip` 안에 넣어도 됨**, 스크립트 설치 파일 금지, 사용자 조작 없이 설치돼야 함, **보안 검사에서 하나라도 걸리면 앱이 정상이어도 받지 않음**(PUA 정책), URL은 공식 출처이고 **버전마다 고유한 URL**을 권장.
- ✅ [첫 기여 체크리스트](https://github.com/microsoft/winget-pkgs/blob/master/doc/FirstContribution.md): PR 하나에 패키지 버전 하나, 매니페스트 여러 파일(singleton 금지), 스키마 헤더, `winget validate --manifest`, 버전 고정 URL. 도구는 [wingetcreate](https://github.com/microsoft/winget-create)나 [Komac](https://github.com/russellbanks/Komac).
- ✅ [installer 스키마](https://github.com/microsoft/winget-pkgs/blob/master/doc/manifest/schema/1.28.0/installer.md): `InstallerType: zip` + `NestedInstallerType: portable` + `NestedInstallerFiles: - RelativeFilePath: Hushpad\Hushpad.exe` (`PortableCommandAlias`는 선택). 인기·별 기준은 문서에 없음. 코드 서명 의무도 문서에 없음.
- URL: `releases/latest/download/…`는 버전마다 바뀌므로 안 됨 → `releases/download/v1.0.0/Hushpad-win64.zip`처럼 태그가 들어간 URL을 쓸 것.
- 위험: 서명 안 된 PyInstaller exe는 Defender 오탐이 잦음([PyInstaller 논의](https://discuss.python.org/t/pyinstaller-false-positive/43171), [MS Q&A](https://learn.microsoft.com/en-us/answers/questions/4078397/where-executables-created-by-pyinstaller-are-being)). 오탐이 나면 [Microsoft 제출 포털](https://www.microsoft.com/en-us/wdsi/filesubmission)에 신고한 뒤 다시 시도.
- 데이터는 AppData에 있어 winget이 포터블 폴더를 지우거나 바꿔도 메모는 남음(좋음).

### Softpedia — GO ⚠️
- 공식 제출 페이지는 자동 조회가 막혀(403) 확인하지 못함. Windows·Mac·Linux·모바일별 제출 폼이 따로 있고 PAD 파일 폼도 있다는 2차 정보([블로그](https://ultimateprogrammingtutorials.blogspot.com/search/label/programs)). Softpedia는 자체 검사 후 "100% Clean" 배지를 붙임. 사이트 하단 "Submit"에서 직접 확인.

### MajorGeeks — GO(채택 불확실)
- ✅ [About/Contact](https://www.majorgeeks.com/content/page/aboutcontact_us.html): 파일 제출은 콘텐츠 담당 이메일로 받고, VMware에서 직접 시험하며, 약속한 대로 동작하고 별 4개 이상 받을 만한 소프트웨어를 실음. 이메일 발송은 사람이 직접 할 것.

### Uptodown — GO ⚠️
- 편집팀이 Developers Console로 제출된 앱을 심사, 개발자 게시 무료([CEO 인터뷰](https://www.pocketgamer.biz/uptodown-ceo-luis-hernndez-on-the-rise-of-alternative-app-stores)). Windows 프로그램 배포로 시작한 곳. Windows 제출 절차 문서는 못 찾음.

### Scoop Extras — LATER (별 100 / 포크 50)
- ✅ [Extras 패키지 요청 템플릿](https://github.com/ScoopInstaller/Extras/blob/master/.github/ISSUE_TEMPLATE/package-request.yml): "꽤 알려지고 널리 쓰임(GitHub이면 **별 100 이상 그리고/또는 포크 50 이상**)", 영어 UI(또는 영어 문서), 최신 안정판, 버전 고정 URL, 인기를 보여 주는 근거 필수. ✅ [Scoop 기여 가이드](https://github.com/ScoopInstaller/.github/blob/main/.github/CONTRIBUTING.md): **이슈 없이 낸 PR은 거의 받지 않음** → 이슈 승인 후 PR, 제목 `<app-name>: Add version <version>`, PR 뒤 `/verify` 댓글. GUI 앱은 Main이 아니라 Extras가 맞음([Main 기준](https://github.com/ScoopInstaller/Scoop/wiki/Criteria-for-including-apps-in-the-main-bucket)).
- 그 전에는 회사 자체 bucket(예: `wind2sp/scoop-bucket`)을 만드는 방법이 있음.

### Homebrew Cask — NO (지금)
- ✅ [Package Acceptance Policy](https://docs.brew.sh/Package-Acceptance-Policy): GitHub 프로젝트는 **포크 30·워처 30·별 75 중 하나 이상**, **저장소 소유자 본인 제출이면 90·90·225**, **30일 안 된 저장소는 보통 안 됨**.
- ✅ [Acceptable Casks](https://docs.brew.sh/Acceptable-Casks): Gatekeeper가 평가할 수 있는 앱은 **Homebrew의 Gatekeeper 검사를 통과해야 함**, SIP·Gatekeeper를 끄거나 우회해야 하는 앱은 안 됨. Apple Silicon 전용은 괜찮음(선언한 아키텍처에서만 동작하면 됨).
- Homebrew 5.0은 Gatekeeper 검사에 실패하는 cask를 **2026-09에 비활성화**하고 `--no-quarantine`을 없앤다고 발표([5.0.0](https://brew.sh/2025/11/12/homebrew-5.0.0), [6.0.0](https://brew.sh/2026/06/11/homebrew-6.0.0/)) → **Developer ID 서명 + 공증(연 $99)** 없이는 공식 cask가 불가능. 그 전에는 회사 tap(`wind2sp/homebrew-tap`)을 쓸 수 있지만, Gatekeeper 경고는 그대로 남음.

---

## 4. 추천 순서

**지금 바로(1–2주)**
1. **awesome 목록 PR 4개**: awesome-mac(4개 언어 README), open-source-mac-os-apps, awesome-note-taking, iCHAIT/awesome-macOS. 별·나이 기준이 없음. PR 본문은 사람이 쓰고 회사가 만들었다고 밝히기.
2. **GeekNews Show GN** 한 번(완성된 상태에서). 같은 주에 **Disquiet 메이커로그**와 **Clien 자료실 `[오픈소스]`**(회사 제작임을 밝힘).
3. **Show HN**: 오래 쓴 계정으로, GitHub 링크로, 작성자 첫 댓글에 위협 모델과 한계. 이어서 **r/macapps**(사이드바 확인 후).
4. **AlternativeTo 등록** + Standard Notes·Joplin·Windows Notepad 등에 대안으로 걸기.
5. **winget 매니페스트 PR**: 태그가 들어간 릴리스 URL로. 그 전에 exe를 VirusTotal·Defender로 확인하고, 오탐이면 MS에 신고. 덤으로 Softpedia·MajorGeeks·Uptodown 제출(품이 적음).

**곁가지로**: Qiita/Zenn 기술 글(일본어, 끝에 링크 한 줄), V2EX 分享创造(중국어), r/Python Showcase(기술 이야기).

**미룰 것**
- 0PandaDEV/awesome-windows → 별 50개.
- Scoop Extras → 별 100개 또는 포크 50개(그 전에는 자체 bucket).
- awesome-kr-foss → winget 등록 뒤.
- Lissy93/awesome-privacy → 1.0 안정판 후 4개월 + 별 100개.
- pluja/awesome-privacy → 6개월~1년, 실제 사용자층.
- Homebrew Cask → Developer ID 서명·공증 + 별 225개(본인 제출) + 30일.
- Product Hunt → 별·후기가 생긴 뒤 준비해서.
- r/opensource → 1년 유지·기여자 3명 이상·AI 관련 아님(사실상 먼 일).
- 안 맞음: r/selfhosted, Privacy Guides(개발자 홍보 금지), awesome-cryptography, Awesome-Windows/Awesome(멈춤).
