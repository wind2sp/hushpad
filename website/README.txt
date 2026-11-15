Hushpad 공식 홈페이지 (정적 사이트) — Omniweave 홈페이지와는 별개입니다.

올리는 곳: WinSCP 저장 접속 "gdra" (cafe24 FTP)의 /www/hushpad/  → https://gdra.mycafe24.com/hushpad/
이 폴더 "안의" 파일·폴더만 /www/hushpad/ 에 올립니다. /www 의 다른 폴더(예: Omniweave)는 건드리지 않습니다.
.htaccess(숨김 파일)도 함께 올립니다. 404 안내는 /hushpad/404.html 기준입니다.

[운영]
config.json   버전·공개 여부·다운로드 주소. 정식 공개 때 이 파일만 고쳐서 다시 올리면 됩니다.
              "public": true, "downloadUrl": GitHub 릴리스 zip 주소, "fileSize", "sha256", "releaseDate"
index.html    소개 페이지 / download.html 다운로드 / 404.html
assets/       css·js·그림 (외부 CDN·글꼴·분석 스크립트 없음)

[그림 다시 만들기]
앱 아이콘을 바꾸면:  python website/make_site_assets.py   (favicon, icon-*.png, og-image.png)
앱 화면 그림(app-light.png, app-dark.png)은 테스트 메모로 찍은 것입니다.

[올리지 않는 파일]  README.txt, make_site_assets.py (올려도 .htaccess가 막음)
