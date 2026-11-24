; Hushpad Windows 설치 프로그램 (NSIS 3, 유니코드).
; make_installer.py가 makensis에 /DVERSION=1.0.3 /DSRC=<dist\Hushpad> /DOUT=<setup.exe> /DICON=<app.ico>를 넘긴다.
;
; - 사용자 설치(관리자 권한 없음): %LOCALAPPDATA%\Programs\Hushpad. 시작 메뉴 바로가기, 바탕화면 바로가기는 마지막 화면에서 고름.
; - 설정 › 앱에 제거 항목(HKCU). 제거해도 메모(보관 폴더)·설정(%APPDATA%\Hushpad)·기억한 열쇠(%LOCALAPPDATA%\Hushpad)는 남긴다.
; - 자동 업데이트(hushpad_app/updater.py): 앱이 새 setup.exe를 받아 SHA-256을 확인한 뒤
;     Hushpad-win64-setup.exe /S /WAITPID=<앱 pid> /RELAUNCH
;   로 실행하고 끝난다. 설치 프로그램은 그 pid가 끝나기를 기다렸다가 덮어쓰고, 끝나면 Hushpad를 다시 켠다.
; - Windows 시작할 때 실행(HKCU Run 'Hushpad')은 앱이 관리한다. 제거할 때는 이 설치 폴더를 가리킬 때만 지운다.

Unicode true
ManifestDPIAware true
RequestExecutionLevel user
SetCompressor /SOLID lzma

!ifndef VERSION
  !error "VERSION is required"
!endif
!ifndef SRC
  !error "SRC is required"
!endif
!ifndef OUT
  !define OUT "Hushpad-win64-setup.exe"
!endif

!define APP "Hushpad"
!define EXE "Hushpad.exe"
!define UNINST "Uninstall Hushpad.exe"
!define PUBLISHER "NINEROW partners Co., Ltd."
!define UKEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\Hushpad"
!define RUNKEY "Software\Microsoft\Windows\CurrentVersion\Run"

Name "${APP}"
OutFile "${OUT}"
InstallDir "$LOCALAPPDATA\Programs\${APP}"
InstallDirRegKey HKCU "${UKEY}" "InstallLocation"
BrandingText "${APP} ${VERSION}"

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=0 "ProductName" "${APP}"
VIAddVersionKey /LANG=0 "CompanyName" "${PUBLISHER}"
VIAddVersionKey /LANG=0 "FileDescription" "${APP} Setup"
VIAddVersionKey /LANG=0 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "LegalCopyright" "(c) 2026 ${PUBLISHER} and Hushpad contributors. GPL-3.0-or-later"

!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "FileFunc.nsh"
!include "StrFunc.nsh"
${UnStrLoc}

!ifdef ICON
  !define MUI_ICON "${ICON}"
  !define MUI_UNICON "${ICON}"
!endif
!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE}"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_NOTCHECKED
!define MUI_FINISHPAGE_SHOWREADME_TEXT "$(DESKTOP_SHORTCUT)"
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION MakeDesktopShortcut

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; 언어: Windows 표시 언어를 따라 고른다 (없으면 첫 번째 = 영어)
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "Korean"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "SimpChinese"

LangString RUNNING ${LANG_ENGLISH} "Hushpad is running. Quit it from the tray icon (right-click › Quit), then click Retry."
LangString RUNNING ${LANG_KOREAN} "Hushpad가 실행 중이에요. 트레이(시계 옆) 아이콘을 오른쪽 클릭해 종료한 뒤 [다시 시도]를 눌러 주세요."
LangString RUNNING ${LANG_JAPANESE} "Hushpad が実行中です。トレイアイコンを右クリックして終了してから［再試行］を押してください。"
LangString RUNNING ${LANG_SIMPCHINESE} "Hushpad 正在运行。请右键单击托盘图标并选择退出，然后点击“重试”。"
LangString DESKTOP_SHORTCUT ${LANG_ENGLISH} "Create a desktop shortcut"
LangString DESKTOP_SHORTCUT ${LANG_KOREAN} "바탕화면에 바로가기 만들기"
LangString DESKTOP_SHORTCUT ${LANG_JAPANESE} "デスクトップにショートカットを作成"
LangString DESKTOP_SHORTCUT ${LANG_SIMPCHINESE} "创建桌面快捷方式"

Var WaitPid
Var Relaunch

Function .onInit
  ${GetParameters} $0
  ClearErrors
  ${GetOptions} $0 "/WAITPID=" $WaitPid
  ${If} ${Errors}
    StrCpy $WaitPid ""
  ${EndIf}
  ClearErrors
  ${GetOptions} $0 "/RELAUNCH" $1
  ${If} ${Errors}
    StrCpy $Relaunch "0"
  ${Else}
    StrCpy $Relaunch "1"
  ${EndIf}
FunctionEnd

; 앱이 끝나기를 기다린다 (자동 업데이트). 창 없이 PowerShell Wait-Process.
Function WaitForApp
  ${If} $WaitPid != ""
    nsExec::Exec 'powershell.exe -NoProfile -NonInteractive -Command "Wait-Process -Id $WaitPid -Timeout 60 -ErrorAction SilentlyContinue"'
    Pop $0
  ${EndIf}
FunctionEnd

; 설치 폴더의 Hushpad.exe를 지울 수 있을 때까지 (실행 중이면 끄라고 안내). 조용한 설치면 잠깐씩 다시 시도.
Function EnsureNotRunning
  IfFileExists "$INSTDIR\${EXE}" 0 done
  StrCpy $1 0
  retry:
    ClearErrors
    Delete "$INSTDIR\${EXE}"
    IfErrors 0 done
    IntOp $1 $1 + 1
    IfSilent 0 ask
      IntCmp $1 40 0 0 give_up
      Sleep 500
      Goto retry
    ask:
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "$(RUNNING)" IDRETRY retry
      Quit
    give_up:
      Abort
  done:
FunctionEnd

Section "Install"
  Call WaitForApp
  Call EnsureNotRunning
  SetOutPath "$INSTDIR"
  RMDir /r "$INSTDIR\_internal"          ; 지난 버전의 남은 파일이 섞이지 않게
  File /r "${SRC}\*.*"
  WriteUninstaller "$INSTDIR\${UNINST}"

  CreateShortcut "$SMPROGRAMS\${APP}.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0

  WriteRegStr HKCU "${UKEY}" "DisplayName" "${APP}"
  WriteRegStr HKCU "${UKEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "${UKEY}" "Publisher" "${PUBLISHER}"
  WriteRegStr HKCU "${UKEY}" "DisplayIcon" "$INSTDIR\${EXE},0"
  WriteRegStr HKCU "${UKEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "${UKEY}" "UninstallString" '"$INSTDIR\${UNINST}"'
  WriteRegStr HKCU "${UKEY}" "QuietUninstallString" '"$INSTDIR\${UNINST}" /S'
  WriteRegStr HKCU "${UKEY}" "URLInfoAbout" "https://gdra.mycafe24.com/hushpad/"
  WriteRegStr HKCU "${UKEY}" "HelpLink" "https://github.com/wind2sp/hushpad/issues"
  WriteRegDWORD HKCU "${UKEY}" "NoModify" 1
  WriteRegDWORD HKCU "${UKEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD HKCU "${UKEY}" "EstimatedSize" $0

  ${If} $Relaunch == "1"
    Exec '"$INSTDIR\${EXE}"'
  ${EndIf}
SectionEnd

Function MakeDesktopShortcut
  CreateShortcut "$DESKTOP\${APP}.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
FunctionEnd

Function un.EnsureNotRunning
  IfFileExists "$INSTDIR\${EXE}" 0 done
  retry:
    ClearErrors
    Delete "$INSTDIR\${EXE}"
    IfErrors 0 done
    IfSilent give_up
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "$(RUNNING)" IDRETRY retry
    Quit
    give_up:
      Abort
  done:
FunctionEnd

Section "Uninstall"
  Call un.EnsureNotRunning
  ; Windows 시작할 때 실행 — 이 설치 폴더의 Hushpad를 가리킬 때만 지운다 (zip판 등 다른 곳의 Hushpad는 건드리지 않음)
  ReadRegStr $0 HKCU "${RUNKEY}" "${APP}"
  ${If} $0 != ""
    ${UnStrLoc} $1 $0 "$INSTDIR\" ">"
    ${If} $1 != ""
      DeleteRegValue HKCU "${RUNKEY}" "${APP}"
    ${EndIf}
  ${EndIf}
  Delete "$SMPROGRAMS\${APP}.lnk"
  Delete "$DESKTOP\${APP}.lnk"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\${EXE}"
  Delete "$INSTDIR\${UNINST}"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\NOTICE"
  Delete "$INSTDIR\THIRD_PARTY_NOTICES.md"
  RMDir /r "$INSTDIR\licenses"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "${UKEY}"
SectionEnd
