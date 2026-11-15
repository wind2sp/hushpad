Hushpad 공식 홈페이지 (정적 사이트) — 다른 제품 홈페이지와는 별개입니다.

올리는 곳: WinSCP 저장 접속 "gdra" (cafe24 FTP)의 /www/hushpad/  → https://gdra.mycafe24.com/hushpad/
이 폴더 "안의" 파일·폴더만 /www/hushpad/ 에 올립니다. /www 의 다른 폴더는 건드리지 않습니다.
.htaccess(숨김 파일)도 함께 올립니다. 404 안내는 /hushpad/404.html 기준입니다.
4개 언어: 한국어(/hushpad/, 기본) · 영어(/hushpad/en/) · 일본어(/hushpad/ja/) · 중국어 간체(/hushpad/zh/)


[운영]
config.json   버전·공개 여부·다운로드 주소·저작권. 정식 공개 때 이 파일만 고쳐서 다시 올리면 됩니다(모든 언어가 이 파일 하나를 씀).
              "public": true, "downloadUrl": GitHub 릴리스 zip 주소, "fileSize", "sha256",
              "releaseDate": 언어와 상관없는 날짜로 (예: "2026-12-01"). 공개 전에는 페이지의 언어별 "공개 준비 중" 문구가 보이고
              releaseDate 값은 쓰지 않습니다.
              "copyright": 바닥글 저작권 줄 (기본 "© 2026 NINEROW partners Co., Ltd.").
              public이 true가 되면 바닥글의 "GitHub 저장소"·"이슈 신고"가 repoUrl(·/issues) 링크로 바뀝니다.
index.html, download.html, en/ ja/ zh/   ← build-i18n.mjs가 만든 결과물 (직접 고치지 않음)
404.html      손으로 쓴 파일. 모든 언어 링크, 경로는 /hushpad/ 절대 경로.
assets/       css·js·그림 (외부 CDN·글꼴·분석 스크립트 없음)
              js/lang.js  언어 메뉴·첫 방문 언어 자동 선택 / js/site.js  config.json 반영


[다국어 — 문구 고치기·번역 추가]
원본(서버에 올리지 않음):
  _templates/index.html, download.html   페이지 틀. 문구 자리는 {{키}} (속성 안은 {{키|a}})
  _templates/partials/head.html, header.html, footer.html   공용 머리(메타·아이콘)·머리글(언어 메뉴)·바닥글
  i18n/ko.json en.json ja.json zh.json    모든 문구. 한국어(ko)가 기준 원문입니다.
  build-i18n.mjs                          템플릿 + 번역 → 언어별 HTML 생성 (Node 18 이상, 설치할 패키지 없음)

순서:
  1) i18n/ko.json 과 en/ja/zh.json 의 "같은 키"를 함께 고칩니다. 네 파일의 키 구조가 하나라도 다르면
     생성기가 어느 키인지 알려 주고 멈춥니다(배열 길이 포함 — FAQ 항목을 늘리면 네 언어 모두 늘려야 함).
  2) website 폴더에서:   node build-i18n.mjs
     확인만:             node build-i18n.mjs --check   (HTML이 번역과 다르면 exit 1)
  3) 바뀐 HTML(루트 index.html·download.html, en/ ja/ zh/ 안의 두 파일)을 올립니다.
  레이아웃을 바꿀 때는 _templates/ 를 고칩니다. 생성된 HTML을 직접 고치면 다음 생성 때 덮어써집니다.
  CSS·JS를 고쳤으면 build-i18n.mjs 의 ASSET_VERSION 숫자를 올리고 다시 생성합니다(.htaccess가 CSS·JS를 7일 캐시 →
  ?v=번호로 새 파일을 받게 함). 404.html 의 site.css?v= 숫자도 같이 올립니다.

언어 추가(예: 스페인어 es):
  build-i18n.mjs 의 LANGS 에 { code: 'es', dir: 'es' } 추가 → i18n/es.json (ko.json 복사 후 번역, meta.htmlLang·ogLocale·label·short 포함)
  → assets/js/lang.js 의 LANGS 에 es 추가 → 404.html 링크 추가 → 생성 → es/ 폴더 올리기.

번역 원칙: ko 문구는 승인된 원문. 다른 언어는 직역이 아니라 자연스러운 제품 문구로.
  "무료"라고 쓰지 않습니다(가격 미정). 앱 화면은 지금 한국어뿐이므로 en/ja/zh 다운로드 페이지에 그 사실을 한 줄(dl.uiNote)로 적고,
  앱 메뉴 이름을 인용할 때는 실제 한국어 메뉴 이름 + 괄호 번역으로 씁니다.

언어 자동 선택 규칙(assets/js/lang.js):
  - 루트(한국어) 페이지에 처음 온 방문자만 navigator.languages로 한 번 고릅니다: ko → 그대로, ja/zh/en → 해당 폴더, 그 밖 → en.
  - 헤더 언어 메뉴로 고르면 localStorage("hushpad-lang")에 기억하고, 그 뒤로 루트에 오면 그 언어를 따릅니다(자동 판단 안 함).
  - 자동 이동은 "hushpad-lang-auto" 기록을 먼저 남긴 뒤에만 일어나므로 두 번 다시 일어나지 않습니다.
  - 하위 언어 페이지·404는 절대 이동시키지 않습니다. 봇·미리보기, 사이트 안에서 온 이동, 저장소를 못 쓰는 브라우저는 이동하지 않습니다.
  - JS가 없어도 모든 페이지는 완성된 정적 HTML이고, 언어 메뉴(<details>)도 그냥 링크라 동작합니다.
  - 브라우저 언어 기준이며 IP(국가)로는 고르지 않습니다(정적 호스팅에서는 불가).


[올리는 파일 / 올리지 않는 파일]
올림:   .htaccess, index.html, download.html, 404.html, config.json, site.webmanifest,
        favicon.ico, favicon-32.png, apple-touch-icon.png, assets/ 전체, en/ ja/ zh/ 폴더
안 올림: README.txt, make_site_assets.py, build-i18n.mjs, _templates/, i18n/
        (실수로 올려도 .htaccess가 막습니다: 파일은 FilesMatch 거부, 폴더는 RewriteRule 404)


[그림 다시 만들기]
앱 아이콘을 바꾸면:  python website/make_site_assets.py   (favicon, icon-*.png, og-image.png)
앱 화면 그림(app-light.png, app-dark.png)은 테스트 메모로 찍은 것입니다(한국어 화면 — en/ja/zh 대체 텍스트에 그렇게 적음).


[다국어 작업에서 적용한 교훈 — 다른 제품 홈페이지를 만들며 겪은 시행착오에서]
  1. 원본 하나: 템플릿 + 언어별 JSON + 생성기. 키 구조(배열 길이까지) 불일치·남은 {{키}}가 있으면 생성 중단, --check 모드.
  2. 하위 언어 폴더의 상대 경로: 모든 공용 자원은 {{_root}}(루트 "" / 하위 "../")로 붙임.
     config.json은 루트에 하나만 두고 site.js가 <html data-root>를 보고 data-root + "config.json"을 읽음.
  3. hreflang: 모든 페이지에 4개 언어 + x-default(=한국어 루트)를 서로 똑같이, 절대 주소로. canonical·og:url·og:image도 절대 주소
     (원래 og:image가 상대 경로라 SNS 미리보기가 그림을 못 찾을 수 있었음 — 함께 고침). og:locale + og:locale:alternate.
  4. 첫 방문 자동 이동의 되돌이 고리 방지: 루트에서만, 한 번만, 이동 전에 기록, 하위 페이지는 이동 안 함,
     같은 사이트에서 온 이동·봇은 제외, localStorage는 try/catch, 저장 불가면 아예 이동 안 함(매번 튕기는 문제 방지).
  5. 수동 선택 기억: 언어 메뉴 링크에 data-setlang → 클릭 때 저장. 메뉴는 <details>라 JS 없이도, 키보드로도 동작. Esc·바깥 클릭으로 닫힘.
  6. CJK 줄바꿈: keep-all은 한국어에만. 일본어·중국어에 keep-all을 걸면 띄어쓰기가 없어 문장이 통째로 넘침 →
     word-break: normal + line-break: strict, 일본어 제목은 auto-phrase(지원 브라우저). 375px 폭에서 가로 넘침 없음 확인.
  7. 언어별 글꼴 스택(외부 글꼴 없이 시스템 글꼴): ja "Hiragino Sans","Yu Gothic UI","Meiryo" / zh "PingFang SC","Microsoft YaHei".
  8. 앱 UI 언어를 사실대로: 앱이 한국어뿐이라는 것을 숨기지 않음(다운로드 페이지 한 줄, FAQ의 메뉴 이름 인용).
  9. CSS·JS 캐시: ?v=ASSET_VERSION. 생성 원본 폴더·스크립트는 .htaccess로 차단.
  10. (이번에 새로 발견) 일본어 글꼴은 \ 를 ¥ 로 그려 C:\ 경로가 깨져 보임 → code 글꼴을 Cascadia Mono/Consolas로 고정.
  11. charset 메타는 <head> 맨 앞(1024바이트 안)에 — 긴 한국어·일본어 메타가 앞에 오면 인코딩 판별이 늦어질 수 있음.
