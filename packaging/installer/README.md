# Hushpad Windows 설치 프로그램

`hushpad.nsi`(NSIS 3, 유니코드)와 그것을 만드는 `make_installer.py`.

```
python build.py                                  # dist\Hushpad\ (PyInstaller onedir)
python packaging\installer\make_installer.py     # dist\Hushpad-win64-setup.exe (+ .sha256)
```

화면은 Omniweave 설치 프로그램의 한 화면 UI를 옮겨 온 것이다(GPL-3.0, 같은 회사). 그 바탕은 Tauri 2.1 NSIS
템플릿(Apache-2.0 OR MIT, Tauri Programme)이고, Tauri·WebView2·파일 연결 부분은 모두 뺐다. 비트맵이나 추가
플러그인 없이 nsDialogs와 user32/gdi32 호출로만 그리며, 좌표는 96 DPI 기준이라 125·150·200%에서도 또렷하다.

## 화면

| 화면 | 내용 |
|---|---|
| 설치 | 어두운 띠(아이콘·Hushpad·한 줄 소개) + 자두·밝은 자두·복숭아 가는 선, 흰 본문(제목·설명·버전과 크기), 자두색 [설치] 버튼. 왼쪽 "설치 옵션 ▾"을 누르면 창이 부드럽게 늘어나 언어·설치 위치(변경…)·바탕화면 바로가기가 보인다 |
| 진행 | 같은 창, 납작한 자두색 막대와 단계 글(파일 복사 → 바로가기) |
| 마침 | "설치를 마쳤어요" + [닫기] [Hushpad 시작] |
| 제거 | "Hushpad를 제거할까요?" + 설정·자동 백업·기억한 암호도 지우기(기본 꺼짐) + [취소] [제거] → 진행 → 마침 |

- 언어: 한국어·English·日本語·简体中文. 지난번에 고른 언어(`HKCU\Software\NINEROW partners\Hushpad`의
  `Installer Language`), 없으면 Windows 표시 언어, 그 밖에는 영어. 설치 옵션에서 바꿀 수 있다.
- 이미 설치돼 있으면(`HKCU\...\Uninstall\Hushpad`의 `DisplayVersion`) 업데이트 / 같은 버전 다시 설치 / 더 새 버전을
  이 버전으로 바꾸기 화면이 되고, 설치 위치는 그 자리로 고정된다.
- 바탕화면 바로가기는 옵션에서 고를 때만(이미 있으면 켠 채로 시작). 조용한 설치는 만들지 않는다.

## 스위치

| 스위치 | 뜻 |
|---|---|
| `/S` | 창 없이 설치(또는 제거). 실행 중인 Hushpad 때문에 파일을 못 바꾸면 약 20초 다시 시도한 뒤 그만둔다 |
| `/WAITPID=<pid>` | 그 프로세스가 끝나기를 기다린다(최대 60초, 창 없음) |
| `/RELAUNCH` | 설치가 끝나면 `$INSTDIR\Hushpad.exe`를 켠다 |
| `/P` | 묻는 것 없이 작은 진행 창만 보인다 |
| `/D=<폴더>` | 설치 위치(맨 끝에) |

자동 업데이트(`hushpad_app/updater.py`)는 `Hushpad-win64-setup.exe /S /WAITPID=<앱 pid> /RELAUNCH`로 실행한다.
제거 프로그램은 `Uninstall Hushpad.exe`(조용히: `/S`). 메모(보관 폴더)는 어떤 경우에도 지우지 않고,
`HKCU\...\Run`의 `Hushpad` 값은 이 설치 폴더를 가리킬 때만 지운다.

## 시험용 빌드 (스크린샷)

아무것도 설치·제거하지 않는 빌드. 키 입력 없이 띄워서 `PrintWindow`로 찍는다.

```
python packaging\installer\make_installer.py --out %TEMP%\shot.exe /DSCREENSHOT_PAGE=welcome /DFORCE_LANG=1033
```

- `/DSCREENSHOT_PAGE=welcome|progress|finish|unconfirm|unprogress|undone` — 그 화면에서 멈춘다. `un…`은
  `shot.exe /S /D=<임시 폴더>`로 제거 프로그램만 쓰게 한 뒤 `"<임시 폴더>\Uninstall Hushpad.exe" _?=<임시 폴더>`로 띄운다.
- `/DFORCE_LANG=1042|1033|1041|2052`, `/DFORCE_KIND=0|1|2|3` + `/DFORCE_OLDVER=1.0.2`, `/DSCREENSHOT_OPTS`(옵션 펼침).
