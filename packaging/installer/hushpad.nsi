; Hushpad Windows 설치 프로그램 (NSIS 3, 유니코드).
;
; UI adapted from Omniweave's installer (github.com/wind2sp/omniweave, GPL-3.0, NINEROW partners), which is based on
; the Tauri 2.1.0 NSIS template (crates/tauri-bundler/src/bundle/windows/nsis/installer.nsi,
; https://github.com/tauri-apps/tauri, Apache-2.0 OR MIT, Copyright (c) 2017 - Present Tauri Programme within
; The Commons Conservancy). Everything Tauri-specific (WebView2, file associations, template fields) is removed.
;
; make_installer.py가 makensis에 /DVERSION=1.0.3 /DSRC=<dist\Hushpad> /DOUT=<setup.exe> /DICON=<app.ico>
; /DSIZE_KB=<앱 크기>를 넘긴다. 화면과 스위치는 README.md 참고.
;
;   설치      한 화면(설치) + 접힌 옵션(언어·폴더·바탕화면 바로가기) -> 진행 -> 마침(닫기 / Hushpad 시작)
;   /S        창 없음 (자동 업데이트: /S /WAITPID=<앱 pid> /RELAUNCH)
;   /P        작은 진행 창만 (묻는 것 없음)
;   제거      한 화면(제거할까요?) -> 진행 -> 마침, 같은 모양
;
; - 사용자 설치(관리자 권한 없음): %LOCALAPPDATA%\Programs\Hushpad. 시작 메뉴 바로가기, 바탕화면 바로가기는 옵션에서 고름.
; - 설정 › 앱에 제거 항목(HKCU). 제거해도 메모(보관 폴더)는 남긴다. 설정(%APPDATA%\Hushpad)·기억한 열쇠
;   (%LOCALAPPDATA%\Hushpad)는 제거 화면에서 고를 때만 지운다(기본은 남김, 조용한 제거는 늘 남김).
; - 자동 업데이트(hushpad_app/updater.py): 앱이 새 setup.exe를 받아 SHA-256을 확인한 뒤
;     Hushpad-win64-setup.exe /S /WAITPID=<앱 pid> /RELAUNCH
;   로 실행하고 끝난다. 설치 프로그램은 그 pid가 끝나기를 기다렸다가(최대 60초) 덮어쓰고, 끝나면 Hushpad를 다시 켠다.
; - Windows 시작할 때 실행(HKCU Run 'Hushpad')은 앱이 관리한다. 제거할 때는 이 설치 폴더를 가리킬 때만 지운다.
;
; 모든 것을 보통 Win32 컨트롤(nsDialogs + user32/gdi32 몇 개)로 그린다: 비트맵·추가 플러그인 없음. 좌표는 96 DPI 기준
; (DIP)이고 창 DPI로 늘리며, 글꼴도 그 DPI로 만든다.

Unicode true
ManifestDPIAware true
ManifestDPIAwareness PerMonitorV2
RequestExecutionLevel user
XPStyle on
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
!define PKEY "Software\NINEROW partners\Hushpad"     ; 설치 프로그램 언어를 기억
!define PKEY_PARENT "Software\NINEROW partners"

Name "${APP}"
OutFile "${OUT}"
InstallDir "$LOCALAPPDATA\Programs\${APP}"
InstallDirRegKey HKCU "${UKEY}" "InstallLocation"
BrandingText " "
ShowInstDetails nevershow
ShowUninstDetails nevershow

VIProductVersion "${VERSION}.0"
VIAddVersionKey /LANG=0 "ProductName" "${APP}"
VIAddVersionKey /LANG=0 "CompanyName" "${PUBLISHER}"
VIAddVersionKey /LANG=0 "FileDescription" "${APP} Setup"
VIAddVersionKey /LANG=0 "FileVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "ProductVersion" "${VERSION}"
VIAddVersionKey /LANG=0 "LegalCopyright" "(c) 2026 ${PUBLISHER} and Hushpad contributors. GPL-3.0-or-later"

!include "LogicLib.nsh"
!include "nsDialogs.nsh"
!include "WinMessages.nsh"
!include "FileFunc.nsh"
!include "WordFunc.nsh"
!include "StrFunc.nsh"
${UnStrLoc}

; 앱 아이콘이 설치·제거 프로그램 아이콘이고, 창도 그 아이콘(리소스 103)을 DPI에 맞는 정확한 크기로 그린다.
!ifdef ICON
  Icon "${ICON}"
  UninstallIcon "${ICON}"
!endif

; 언어 파일은 LANG_* 번호와 시스템 문구용. 창의 문구는 아래 HpStrings에 있다(창을 연 채 언어를 바꿀 수 있게 변수로).
LoadLanguageFile "${NSISDIR}\Contrib\Language files\English.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\Korean.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\Japanese.nlf"
LoadLanguageFile "${NSISDIR}\Contrib\Language files\SimpChinese.nlf"

; ---------------------------------------------------------------------------------------------------------------
; 시험용 빌드 (스크린샷). 설치·제거는 하지 않는다. README.md 참고.
;   /DSCREENSHOT_PAGE=welcome|progress|finish|unconfirm|unprogress|undone   /DFORCE_LANG=1042|1033|1041|2052
;   /DFORCE_KIND=0|1|2|3 (/DFORCE_OLDVER=1.0.2)   /DSCREENSHOT_OPTS (옵션을 편 채로 시작)
; ---------------------------------------------------------------------------------------------------------------
!ifdef SCREENSHOT_PAGE
  !if "${SCREENSHOT_PAGE}" == "welcome"
    !define HP_SHOT_WELCOME
  !else if "${SCREENSHOT_PAGE}" == "progress"
    !define HP_SHOT_SKIPWELCOME
    !define HP_SHOT_PROGRESS
  !else if "${SCREENSHOT_PAGE}" == "finish"
    !define HP_SHOT_SKIPWELCOME
  !else if "${SCREENSHOT_PAGE}" == "unconfirm"
    !define HP_SHOT_UN
  !else if "${SCREENSHOT_PAGE}" == "unprogress"
    !define HP_SHOT_UN
    !define HP_SHOT_UNSKIP
    !define HP_SHOT_UNPROGRESS
  !else if "${SCREENSHOT_PAGE}" == "undone"
    !define HP_SHOT_UN
    !define HP_SHOT_UNSKIP
  !else
    !error "SCREENSHOT_PAGE: welcome, progress, finish, unconfirm, unprogress or undone"
  !endif
!endif

; ---------------------------------------------------------------------------------------------------------------
; 모양. Hushpad 브랜드 색(assets/make_icon.py, 앱 화면): 자두 #7A3C93(밝은 #9B4DB5), 복숭아 #FFB38A(진한 #E0703F),
; 잉크 #1C1A1F. 위 띠는 자두빛이 도는 잉크, 본문은 흰색, 강한 색은 주 버튼·진행 막대·링크의 자두색 하나.
; 띠 아래 가는 선만 자두·밝은 자두·복숭아 세 색. SetCtlColors는 숫자를 그대로 써야 해서 쓰는 곳에 적는다:
;   띠 0x231A29, 띠 글자 0xF4EFF7, 띠 흐린 글자 0xC9BCD0, 본문 0xFFFFFF, 글자 0x1C1A1F, 글자2 0x4A4550,
;   글자3 0x6E6875, 주 버튼 0x7A3C93 (위에 올리면 0x8C47A8), 조용한 버튼 0xEFEDF2 (0xE3E0E8),
;   위험 0xC23B4A (0xA8303E), 링크 0x7A3C93 (0x5A2B6E), 구분선 0xE3E0E7, 가는 선 0x7A3C93 / 0x9B4DB5 / 0xFFB38A.
; ---------------------------------------------------------------------------------------------------------------
!define HP_W 560          ; 창 안쪽 너비
!define HP_HERO 132       ; 위 띠 높이
!define HP_BODY 184       ; 본문 높이 (옵션 접힘)
!define HP_OPTS 158       ; 옵션을 펴면 늘어나는 높이 (옵션은 버튼 아래에 있다)
!define HP_PAD 36         ; 좌우 여백
!define HP_TEXTW 488      ; 본문 글 너비 (HP_W - 2 * HP_PAD)
!define HP_FOOT 124       ; 본문 안 버튼 줄 위치
!define HP_BTN_H 38
!define HP_ANIM_MS 180    ; 옵션 펴기/접기: 창 높이가 이 시간 동안 부드럽게 바뀜
!define HP_PW 420         ; /P 창: 너비
!define HP_PHERO 76       ; /P: 아이콘 + 글 띠
!define HP_PBODY 36       ; /P: 진행 막대 줄
!ifdef SIZE_KB
  !define /math HP_SIZE_T ${SIZE_KB} + 1023
  !define /math HP_SIZE_MB ${HP_SIZE_T} / 1024
!endif
!define HP_STYLE_LABEL 0x50000180   ; WS_CHILD|WS_VISIBLE|SS_NOTIFY|SS_NOPREFIX
!define HP_STYLE_BTN 0x50000381     ; ... |SS_CENTER|SS_CENTERIMAGE
!define HP_STYLE_HERO 0x50004080    ; WS_CHILD|WS_VISIBLE|SS_NOPREFIX|SS_ENDELLIPSIS
!define HP_STYLE_ICON 0x50000203    ; WS_CHILD|WS_VISIBLE|SS_ICON|SS_CENTERIMAGE

Var PassiveMode
Var WaitPid
Var Relaunch
Var DeleteDataState
Var HpDpi
Var HpX
Var HpY
Var HpCW
Var HpCH
Var HpT
Var HpFace
Var HpFontTitle
Var HpFontTag
Var HpFontHead
Var HpFontBody
Var HpFontSmall
Var HpFontBtn
Var HpFontUi
Var HpHeroIcon
Var HpHeroTitle
Var HpHeroTag
Var HpClientW
Var HpHeroH
Var HpBodyH
Var HpPageH
Var HpBrowseBtn
Var HpLocked
Var HpPlaced
Var HpDlg
Var HpBtnA
Var HpBtnAKind     ; 1 주 버튼, 3 위험(제거)
Var HpBtnB
Var HpLinkA
Var HpHot
Var HpOpt
Var HpReloading
Var HpKind         ; 0 새로 설치, 1 업데이트(옛 버전 설치됨), 2 같은 버전, 3 더 새 버전 설치됨
Var HpOldVer
Var HpDesktop
Var HpCombo
Var HpDirEdit
Var HpDeskCheck
Var HpDataCheck
; 문구 (HpStrings)
Var L_Caption
Var L_Tag
Var L_Head
Var L_Text
Var L_Meta
Var L_Go
Var L_Options
Var L_Lang
Var L_Dir
Var L_Change
Var L_DirLocked
Var L_Desktop
Var L_PickDir
Var L_BadDir
Var L_Working
Var L_Copying
Var L_Registering
Var L_DoneHead
Var L_DoneText
Var L_Launch
Var L_Close
Var L_Failed
Var L_Running
Var L_UnCaption
Var L_UnHead
Var L_UnText
Var L_UnData
Var L_UnGo
Var L_Cancel
Var L_UnWorking
Var L_UnDoneHead
Var L_UnDoneText
Var L_UpdWorking

; DIP -> 장치 픽셀
!macro HP_PX OUT V
  IntOp ${OUT} ${V} * $HpDpi
  IntOp ${OUT} ${OUT} / 96
!macroend

; 지금 페이지에 DIP 좌표로 nsDialogs 컨트롤
!macro HP_CTL OUT CLASS STYLE EXSTYLE X Y W H TEXT
  !insertmacro HP_PX $HpX ${X}
  !insertmacro HP_PX $HpY ${Y}
  !insertmacro HP_PX $HpCW ${W}
  !insertmacro HP_PX $HpCH ${H}
  nsDialogs::CreateControl ${CLASS} ${STYLE} ${EXSTYLE} $HpX $HpY $HpCW $HpCH "${TEXT}"
  Pop ${OUT}
!macroend

; 흰 본문 위 글
!macro HP_LABEL OUT X Y W H TEXT FONT
  !insertmacro HP_CTL ${OUT} STATIC ${HP_STYLE_LABEL} 0 ${X} ${Y} ${W} ${H} "${TEXT}"
  SendMessage ${OUT} ${WM_SETFONT} ${FONT} 1
!macroend

; 납작한 버튼으로 쓰는 static: 둥근 모서리, 칠한 바탕, 마우스 올림은 HpHoverTick이 처리
!macro HP_BUTTON OUT X Y W H TEXT
  !insertmacro HP_CTL ${OUT} STATIC ${HP_STYLE_BTN} 0 ${X} ${Y} ${W} ${H} "${TEXT}"
  SendMessage ${OUT} ${WM_SETFONT} $HpFontBtn 1
  IntOp $HpX $HpCW + 1
  IntOp $HpY $HpCH + 1
  !insertmacro HP_PX $HpT 8
  System::Call 'gdi32::CreateRoundRectRgn(i 0, i 0, i $HpX, i $HpY, i $HpT, i $HpT) p .s'
  Pop $HpT
  System::Call 'user32::SetWindowRgn(p ${OUT}, p $HpT, i 1)'
!macroend

; 본 창(위 띠)에 놓는 static, 페이지 대화상자 밖
!macro HP_HERO_CTL OUT STYLE X Y W H TEXT
  !insertmacro HP_PX $HpX ${X}
  !insertmacro HP_PX $HpY ${Y}
  !insertmacro HP_PX $HpCW ${W}
  !insertmacro HP_PX $HpCH ${H}
  System::Call 'user32::CreateWindowExW(i 0, w "STATIC", w "${TEXT}", i ${STYLE}, i $HpX, i $HpY, i $HpCW, i $HpCH, p $HWNDPARENT, p 0, p 0, p 0) p .s'
  Pop ${OUT}
!macroend

!macro HP_FONT OUT FACE PX WEIGHT
  IntOp $HpT ${PX} * $HpDpi
  IntOp $HpT $HpT / 96
  IntOp $HpT 0 - $HpT
  System::Call 'gdi32::CreateFontW(i $HpT, i 0, i 0, i 0, i ${WEIGHT}, i 0, i 0, i 0, i 1, i 0, i 0, i 5, i 0, w "${FACE}") p .s'
  Pop ${OUT}
!macroend

; 컨트롤 옮기기 (DIP)
!macro HP_PLACE HWND X Y W H
  !insertmacro HP_PX $HpX ${X}
  !insertmacro HP_PX $HpY ${Y}
  !insertmacro HP_PX $HpCW ${W}
  !insertmacro HP_PX $HpCH ${H}
  System::Call 'user32::SetWindowPos(p ${HWND}, p 0, i $HpX, i $HpY, i $HpCW, i $HpCH, i 0x14)'
!macroend

; 진행 줄 글 (조용한 설치에서도 무해)
!macro HP_STEP TEXT
  SetDetailsPrint textonly
  DetailPrint "${TEXT}"
  SetDetailsPrint none
!macroend

!macro HP_SHARED un
  ; 언어: 지난번 설치에서 고른 것, 없으면 Windows 표시 언어, 그것도 아니면 영어.
  Function ${un}HpPickLanguage
    StrCpy $0 0
    System::Call 'kernel32::GetUserDefaultUILanguage() i .r0'
    IntOp $0 $0 & 0x3FF
    ${If} $0 = 0x12
      StrCpy $LANGUAGE 1042
    ${ElseIf} $0 = 0x11
      StrCpy $LANGUAGE 1041
    ${ElseIf} $0 = 0x04
      StrCpy $LANGUAGE 2052
    ${Else}
      StrCpy $LANGUAGE 1033
    ${EndIf}
    ReadRegStr $0 HKCU "${PKEY}" "Installer Language"
    ${If} $0 == 1042
    ${OrIf} $0 == 1033
    ${OrIf} $0 == 2052
    ${OrIf} $0 == 1041
      StrCpy $LANGUAGE $0
    ${EndIf}
    !ifdef FORCE_LANG
      StrCpy $LANGUAGE ${FORCE_LANG}
    !endif
  FunctionEnd

  ; 창의 문구. LangString이 아니라 변수라서 창을 연 채로 언어를 바꿀 수 있다.
  Function ${un}HpStrings
    ${If} $LANGUAGE == 1033
      StrCpy $HpFace "Segoe UI"
      StrCpy $L_Caption "Hushpad Setup"
      StrCpy $L_Tag "A quiet notepad that encrypts every note"
      StrCpy $L_Options "Install options"
      StrCpy $L_Lang "Language"
      StrCpy $L_Dir "Install location"
      StrCpy $L_Change "Change…"
      StrCpy $L_DirLocked "Hushpad is updated where it is installed now."
      StrCpy $L_Desktop "Create a desktop shortcut"
      StrCpy $L_PickDir "Choose a folder for Hushpad"
      StrCpy $L_BadDir "Enter the full path of a folder, for example D:\Apps\Hushpad."
      StrCpy $L_Copying "Copying files"
      StrCpy $L_Registering "Adding shortcuts"
      StrCpy $L_Launch "Start Hushpad"
      StrCpy $L_Close "Close"
      StrCpy $L_Failed "Hushpad could not be installed. Please try again."
      StrCpy $L_Running "Hushpad is running. Quit it from the tray icon (right-click › Quit), then click Retry."
      StrCpy $L_UnCaption "Uninstall Hushpad"
      StrCpy $L_UnHead "Uninstall Hushpad?"
      StrCpy $L_UnText "This removes the app and its shortcuts. Your notes (vault folder) stay."
      StrCpy $L_UnData "Also delete settings, automatic backups and the remembered passphrase"
      StrCpy $L_UnGo "Uninstall"
      StrCpy $L_Cancel "Cancel"
      StrCpy $L_UnWorking "Uninstalling…"
      StrCpy $L_UnDoneHead "Hushpad has been uninstalled"
      StrCpy $L_UnDoneText "Your notes are still in the vault folder. Thank you for using Hushpad."
      StrCpy $L_UpdWorking "Updating Hushpad…"
      ${If} $HpKind = 1
        StrCpy $L_Head "Ready to update"
        StrCpy $L_Text "Your notes and settings stay as they are."
        StrCpy $L_Meta "Version $HpOldVer → ${VERSION}"
        StrCpy $L_Go "Update"
        StrCpy $L_Working "Updating…"
        StrCpy $L_DoneHead "Update complete"
      ${ElseIf} $HpKind = 2
        StrCpy $L_Head "This version is already installed"
        StrCpy $L_Text "Reinstall to repair the app files. Notes and settings stay."
        StrCpy $L_Meta "Version ${VERSION}"
        StrCpy $L_Go "Reinstall"
        StrCpy $L_Working "Installing…"
        StrCpy $L_DoneHead "Installation complete"
      ${ElseIf} $HpKind = 3
        StrCpy $L_Head "A newer version is installed"
        StrCpy $L_Text "This replaces it with the older version below."
        StrCpy $L_Meta "Version $HpOldVer → ${VERSION}"
        StrCpy $L_Go "Install this version"
        StrCpy $L_Working "Installing…"
        StrCpy $L_DoneHead "Installation complete"
      ${Else}
        StrCpy $L_Head "Ready to install"
        StrCpy $L_Text "Installs for this account only. No administrator rights needed."
        !ifdef HP_SIZE_MB
          StrCpy $L_Meta "Version ${VERSION}  ·  About ${HP_SIZE_MB} MB"
        !else
          StrCpy $L_Meta "Version ${VERSION}"
        !endif
        StrCpy $L_Go "Install"
        StrCpy $L_Working "Installing…"
        StrCpy $L_DoneHead "Installation complete"
      ${EndIf}
      StrCpy $L_DoneText "You can open Hushpad from the Start menu at any time."
    ${ElseIf} $LANGUAGE == 2052
      StrCpy $HpFace "Microsoft YaHei UI"
      StrCpy $L_Caption "Hushpad 安装"
      StrCpy $L_Tag "加密每一条笔记的安静记事本"
      StrCpy $L_Options "安装选项"
      StrCpy $L_Lang "语言"
      StrCpy $L_Dir "安装位置"
      StrCpy $L_Change "更改…"
      StrCpy $L_DirLocked "将在当前安装位置更新 Hushpad。"
      StrCpy $L_Desktop "创建桌面快捷方式"
      StrCpy $L_PickDir "选择 Hushpad 的安装文件夹"
      StrCpy $L_BadDir "请输入文件夹的完整路径，例如 D:\Apps\Hushpad。"
      StrCpy $L_Copying "正在复制文件"
      StrCpy $L_Registering "正在添加快捷方式"
      StrCpy $L_Launch "启动 Hushpad"
      StrCpy $L_Close "关闭"
      StrCpy $L_Failed "无法安装 Hushpad，请重试。"
      StrCpy $L_Running "Hushpad 正在运行。请右键单击托盘图标并选择退出，然后点击“重试”。"
      StrCpy $L_UnCaption "卸载 Hushpad"
      StrCpy $L_UnHead "要卸载 Hushpad 吗？"
      StrCpy $L_UnText "将删除程序及其快捷方式，笔记（仓库文件夹）会保留。"
      StrCpy $L_UnData "同时删除设置、自动备份和此电脑记住的密码"
      StrCpy $L_UnGo "卸载"
      StrCpy $L_Cancel "取消"
      StrCpy $L_UnWorking "正在卸载…"
      StrCpy $L_UnDoneHead "Hushpad 已卸载"
      StrCpy $L_UnDoneText "笔记仍保留在仓库文件夹中。感谢您使用 Hushpad。"
      StrCpy $L_UpdWorking "正在更新 Hushpad…"
      ${If} $HpKind = 1
        StrCpy $L_Head "准备更新"
        StrCpy $L_Text "您的笔记和设置将保持不变。"
        StrCpy $L_Meta "版本 $HpOldVer → ${VERSION}"
        StrCpy $L_Go "更新"
        StrCpy $L_Working "正在更新…"
        StrCpy $L_DoneHead "更新完成"
      ${ElseIf} $HpKind = 2
        StrCpy $L_Head "已安装此版本"
        StrCpy $L_Text "重新安装可修复程序文件，笔记和设置会保留。"
        StrCpy $L_Meta "版本 ${VERSION}"
        StrCpy $L_Go "重新安装"
        StrCpy $L_Working "正在安装…"
        StrCpy $L_DoneHead "安装完成"
      ${ElseIf} $HpKind = 3
        StrCpy $L_Head "已安装较新的版本"
        StrCpy $L_Text "将用下面的旧版本替换它。"
        StrCpy $L_Meta "版本 $HpOldVer → ${VERSION}"
        StrCpy $L_Go "安装此版本"
        StrCpy $L_Working "正在安装…"
        StrCpy $L_DoneHead "安装完成"
      ${Else}
        StrCpy $L_Head "准备安装"
        StrCpy $L_Text "仅为当前用户安装，无需管理员权限。"
        !ifdef HP_SIZE_MB
          StrCpy $L_Meta "版本 ${VERSION}  ·  约 ${HP_SIZE_MB} MB"
        !else
          StrCpy $L_Meta "版本 ${VERSION}"
        !endif
        StrCpy $L_Go "安装"
        StrCpy $L_Working "正在安装…"
        StrCpy $L_DoneHead "安装完成"
      ${EndIf}
      StrCpy $L_DoneText "随时可以从“开始”菜单打开 Hushpad。"
    ${ElseIf} $LANGUAGE == 1041
      StrCpy $HpFace "Yu Gothic UI"
      StrCpy $L_Caption "Hushpad セットアップ"
      StrCpy $L_Tag "すべてのメモを暗号化する静かなメモ帳"
      StrCpy $L_Options "インストールオプション"
      StrCpy $L_Lang "言語"
      StrCpy $L_Dir "インストール先"
      StrCpy $L_Change "変更…"
      StrCpy $L_DirLocked "いまインストールされている場所でアップデートします。"
      StrCpy $L_Desktop "デスクトップにショートカットを作成"
      StrCpy $L_PickDir "Hushpad のインストール先フォルダーを選んでください"
      StrCpy $L_BadDir "フォルダーのフルパスを入力してください（例: D:\Apps\Hushpad）。"
      StrCpy $L_Copying "ファイルをコピーしています"
      StrCpy $L_Registering "ショートカットを追加しています"
      StrCpy $L_Launch "Hushpad を起動"
      StrCpy $L_Close "閉じる"
      StrCpy $L_Failed "Hushpad をインストールできませんでした。もう一度お試しください。"
      StrCpy $L_Running "Hushpad が実行中です。トレイアイコンを右クリックして終了してから［再試行］を押してください。"
      StrCpy $L_UnCaption "Hushpad のアンインストール"
      StrCpy $L_UnHead "Hushpad をアンインストールしますか？"
      StrCpy $L_UnText "アプリとショートカットを削除します。メモ（保管フォルダー）は残ります。"
      StrCpy $L_UnData "設定・自動バックアップ・この PC に記憶したパスワードも削除する"
      StrCpy $L_UnGo "アンインストール"
      StrCpy $L_Cancel "キャンセル"
      StrCpy $L_UnWorking "アンインストールしています…"
      StrCpy $L_UnDoneHead "アンインストールが完了しました"
      StrCpy $L_UnDoneText "メモは保管フォルダーに残っています。ご利用ありがとうございました。"
      StrCpy $L_UpdWorking "Hushpad をアップデートしています…"
      ${If} $HpKind = 1
        StrCpy $L_Head "アップデートの準備ができました"
        StrCpy $L_Text "メモと設定はそのまま残ります。"
        StrCpy $L_Meta "バージョン $HpOldVer → ${VERSION}"
        StrCpy $L_Go "アップデート"
        StrCpy $L_Working "アップデートしています…"
        StrCpy $L_DoneHead "アップデートが完了しました"
      ${ElseIf} $HpKind = 2
        StrCpy $L_Head "このバージョンはインストール済みです"
        StrCpy $L_Text "再インストールでアプリのファイルを修復します。メモと設定は残ります。"
        StrCpy $L_Meta "バージョン ${VERSION}"
        StrCpy $L_Go "再インストール"
        StrCpy $L_Working "インストールしています…"
        StrCpy $L_DoneHead "インストールが完了しました"
      ${ElseIf} $HpKind = 3
        StrCpy $L_Head "より新しいバージョンがインストールされています"
        StrCpy $L_Text "下の古いバージョンに置き換えます。"
        StrCpy $L_Meta "バージョン $HpOldVer → ${VERSION}"
        StrCpy $L_Go "このバージョンを入れる"
        StrCpy $L_Working "インストールしています…"
        StrCpy $L_DoneHead "インストールが完了しました"
      ${Else}
        StrCpy $L_Head "インストールの準備ができました"
        StrCpy $L_Text "このアカウントだけにインストールします。管理者権限は不要です。"
        !ifdef HP_SIZE_MB
          StrCpy $L_Meta "バージョン ${VERSION}  ·  約 ${HP_SIZE_MB} MB"
        !else
          StrCpy $L_Meta "バージョン ${VERSION}"
        !endif
        StrCpy $L_Go "インストール"
        StrCpy $L_Working "インストールしています…"
        StrCpy $L_DoneHead "インストールが完了しました"
      ${EndIf}
      StrCpy $L_DoneText "Hushpad はスタートメニューからいつでも開けます。"
    ${Else}
      StrCpy $HpFace "Malgun Gothic"
      StrCpy $L_Caption "Hushpad 설치"
      StrCpy $L_Tag "조용한 비밀 메모장 · 쓰는 대로 저장하고 모두 암호화"
      StrCpy $L_Options "설치 옵션"
      StrCpy $L_Lang "언어"
      StrCpy $L_Dir "설치 위치"
      StrCpy $L_Change "변경…"
      StrCpy $L_DirLocked "지금 설치된 위치에서 업데이트해요."
      StrCpy $L_Desktop "바탕화면에 바로가기 만들기"
      StrCpy $L_PickDir "Hushpad를 설치할 폴더를 골라 주세요"
      StrCpy $L_BadDir "폴더의 전체 경로를 적어 주세요. 예: D:\Apps\Hushpad"
      StrCpy $L_Copying "파일을 복사하는 중"
      StrCpy $L_Registering "바로가기를 만드는 중"
      StrCpy $L_Launch "Hushpad 시작"
      StrCpy $L_Close "닫기"
      StrCpy $L_Failed "Hushpad를 설치하지 못했어요. 다시 시도해 주세요."
      StrCpy $L_Running "Hushpad가 실행 중이에요. 트레이(시계 옆) 아이콘을 오른쪽 클릭해 종료한 뒤 [다시 시도]를 눌러 주세요."
      StrCpy $L_UnCaption "Hushpad 제거"
      StrCpy $L_UnHead "Hushpad를 제거할까요?"
      StrCpy $L_UnText "앱과 바로가기를 지워요. 메모(보관 폴더)는 그대로 남아요."
      StrCpy $L_UnData "설정, 자동 백업, 이 PC에 기억한 암호도 지우기"
      StrCpy $L_UnGo "제거"
      StrCpy $L_Cancel "취소"
      StrCpy $L_UnWorking "제거하는 중…"
      StrCpy $L_UnDoneHead "Hushpad를 제거했어요"
      StrCpy $L_UnDoneText "메모는 보관 폴더에 그대로 있어요. 그동안 써 주셔서 고마워요."
      StrCpy $L_UpdWorking "Hushpad를 업데이트하는 중…"
      ${If} $HpKind = 1
        StrCpy $L_Head "업데이트할 준비가 됐어요"
        StrCpy $L_Text "메모와 설정은 그대로 남아요."
        StrCpy $L_Meta "버전 $HpOldVer → ${VERSION}"
        StrCpy $L_Go "업데이트"
        StrCpy $L_Working "업데이트하는 중…"
        StrCpy $L_DoneHead "업데이트를 마쳤어요"
      ${ElseIf} $HpKind = 2
        StrCpy $L_Head "이 버전이 이미 설치돼 있어요"
        StrCpy $L_Text "다시 설치하면 앱 파일을 고쳐요. 메모와 설정은 그대로예요."
        StrCpy $L_Meta "버전 ${VERSION}"
        StrCpy $L_Go "다시 설치"
        StrCpy $L_Working "설치하는 중…"
        StrCpy $L_DoneHead "설치를 마쳤어요"
      ${ElseIf} $HpKind = 3
        StrCpy $L_Head "더 새 버전이 설치돼 있어요"
        StrCpy $L_Text "설치된 버전을 아래 버전으로 바꿔요."
        StrCpy $L_Meta "버전 $HpOldVer → ${VERSION}"
        StrCpy $L_Go "이 버전 설치"
        StrCpy $L_Working "설치하는 중…"
        StrCpy $L_DoneHead "설치를 마쳤어요"
      ${Else}
        StrCpy $L_Head "설치할 준비가 됐어요"
        StrCpy $L_Text "이 계정에만 설치하고 관리자 권한은 필요 없어요."
        !ifdef HP_SIZE_MB
          StrCpy $L_Meta "버전 ${VERSION}  ·  약 ${HP_SIZE_MB} MB"
        !else
          StrCpy $L_Meta "버전 ${VERSION}"
        !endif
        StrCpy $L_Go "설치"
        StrCpy $L_Working "설치하는 중…"
        StrCpy $L_DoneHead "설치를 마쳤어요"
      ${EndIf}
      StrCpy $L_DoneText "시작 메뉴에서 언제든 Hushpad를 열 수 있어요."
    ${EndIf}
  FunctionEnd

  Function ${un}HpFonts
    !insertmacro HP_FONT $HpFontHead $HpFace 20 700
    !insertmacro HP_FONT $HpFontBody $HpFace 14 400
    !insertmacro HP_FONT $HpFontSmall $HpFace 13 400
    !insertmacro HP_FONT $HpFontBtn $HpFace 14 600
    !insertmacro HP_FONT $HpFontTag $HpFace 14 400
    ; 앱 이름과 언어 목록(네 글자 체계)은 Segoe UI: CJK 글꼴이 이어 붙는다
    !insertmacro HP_FONT $HpFontTitle "Segoe UI Semibold" 28 400
    !insertmacro HP_FONT $HpFontUi "Segoe UI" 14 400
  FunctionEnd

  ; 본 창을 $HpClientW x ($HpHeroH + $HpBodyH) DIP로 맞추고 페이지 자리를 띠 아래에 둔다.
  ; 처음에는 NSIS가 놓은 자리의 가운데로, 그다음부터는 왼쪽 위 모서리를 그대로 둔다.
  Function ${un}HpLayout
    System::Call '*(i, i, i, i) p .r8'
    System::Call '*(i, i, i, i) p .r9'
    System::Call 'user32::GetWindowRect(p $HWNDPARENT, p r8)'
    System::Call 'user32::GetClientRect(p $HWNDPARENT, p r9)'
    System::Call '*$8(i .r0, i .r1, i .r2, i .r3)'
    System::Call '*$9(i, i, i .r4, i .r5)'
    System::Free $8
    System::Free $9
    IntOp $2 $2 - $0   ; 바깥 너비
    IntOp $3 $3 - $1   ; 바깥 높이
    IntOp $4 $2 - $4   ; 테두리 너비
    IntOp $5 $3 - $5   ; 테두리 높이
    IntOp $6 $HpHeroH + $HpBodyH
    !insertmacro HP_PX $6 $6
    !insertmacro HP_PX $7 $HpClientW
    IntOp $6 $6 + $5
    IntOp $7 $7 + $4
    ${If} $HpPlaced != 1
      IntOp $8 $2 - $7
      IntOp $8 $8 / 2
      IntOp $0 $0 + $8
      IntOp $8 $3 - $6
      IntOp $8 $8 / 2
      IntOp $1 $1 + $8
      StrCpy $HpPlaced 1
    ${EndIf}
    System::Call 'user32::SetWindowPos(p $HWNDPARENT, p 0, i r0, i r1, i r7, i r6, i 0x14)'
    ; 페이지는 보이는 본문보다 클 수 있다 (설치 화면은 접힌 옵션을 그 아래에 둔다)
    ${If} $HpPageH < $HpBodyH
      StrCpy $HpPageH $HpBodyH
    ${EndIf}
    GetDlgItem $0 $HWNDPARENT 1018
    !insertmacro HP_PLACE $0 0 $HpHeroH $HpClientW $HpPageH
  FunctionEnd

  ; 창 높이를 $HpHeroH + $HpBodyH로 HP_ANIM_MS 동안 부드럽게(ease-out cubic). 창만 커지거나 줄고 아래 페이지는 이미
  ; 그려져 있어 드러나거나 가려질 뿐이라 다시 만들지 않는다. Windows 애니메이션을 끄면 바로 바뀐다.
  !if "${un}" == ""
  Function ${un}HpAnimate
    System::Call '*(i, i, i, i) p .r8'
    System::Call 'user32::GetWindowRect(p $HWNDPARENT, p r8)'
    System::Call '*$8(i .r0, i .r1, i .r2, i .r3)'
    System::Call 'user32::GetClientRect(p $HWNDPARENT, p r8)'
    System::Call '*$8(i, i, i, i .r4)'
    System::Free $8
    IntOp $2 $2 - $0       ; 바깥 너비
    IntOp $3 $3 - $1       ; 바깥 높이
    IntOp $5 $3 - $4       ; 테두리 높이
    IntOp $6 $HpHeroH + $HpBodyH
    !insertmacro HP_PX $6 $6
    IntOp $6 $6 + $5       ; 목표 바깥 높이
    StrCpy $7 1
    System::Call 'user32::SystemParametersInfoW(i 0x1042, i 0, *i .r7, i 0)'   ; SPI_GETCLIENTAREAANIMATION
    ${If} $7 <> 0
      IntOp $9 $6 - $3     ; 움직일 거리
      System::Call 'kernel32::GetTickCount() i .r8'
      ${Do}
        System::Call 'kernel32::GetTickCount() i .r0'
        IntOp $0 $0 - $8
        ${If} $0 >= ${HP_ANIM_MS}
          ${Break}
        ${EndIf}
        IntOp $0 $0 * 1000
        IntOp $0 $0 / ${HP_ANIM_MS}
        IntOp $0 1000 - $0          ; u = 1 - t
        IntOp $1 $0 * $0
        IntOp $1 $1 / 1000
        IntOp $1 $1 * $0
        IntOp $1 $1 / 1000          ; u^3
        IntOp $1 1000 - $1          ; ease = 1 - (1 - t)^3
        IntOp $1 $9 * $1
        IntOp $1 $1 / 1000
        IntOp $1 $3 + $1
        System::Call 'user32::SetWindowPos(p $HWNDPARENT, p 0, i 0, i 0, i r2, i r1, i 0x16)'
        System::Call 'user32::RedrawWindow(p $HWNDPARENT, p 0, p 0, i 0x180)'   ; RDW_UPDATENOW|RDW_ALLCHILDREN
        System::Call 'kernel32::Sleep(i 1)'
      ${Loop}
    ${EndIf}
    System::Call 'user32::SetWindowPos(p $HWNDPARENT, p 0, i 0, i 0, i r2, i r6, i 0x16)'
  FunctionEnd
  !endif

  ; 기본 NSIS 창을 Hushpad 창으로: 어두운 제목 표시줄, 기본 버튼 숨김, 위에 브랜드 띠.
  Function ${un}HpInitWindow
    StrCpy $0 0
    System::Call 'user32::GetDpiForWindow(p $HWNDPARENT) i .r0'
    IntOp $HpDpi $0 + 0
    ${If} $HpDpi < 96
      System::Call 'user32::GetDC(p 0) p .r1'
      System::Call 'gdi32::GetDeviceCaps(p r1, i 90) i .r0'
      System::Call 'user32::ReleaseDC(p 0, p r1)'
      IntOp $HpDpi $0 + 0
    ${EndIf}
    ${If} $HpDpi < 96
      StrCpy $HpDpi 96
    ${EndIf}
    ; Windows 11은 제목 표시줄을 띠 색으로 그린다 (Windows 10은 자기 제목 표시줄; 둘 다 괜찮음). COLORREF = 0x00BBGGRR
    System::Call 'dwmapi::DwmSetWindowAttribute(p $HWNDPARENT, i 20, *i 1, i 4)'
    System::Call 'dwmapi::DwmSetWindowAttribute(p $HWNDPARENT, i 35, *i 0x00291A23, i 4)'
    System::Call 'dwmapi::DwmSetWindowAttribute(p $HWNDPARENT, i 36, *i 0x00F7EFF4, i 4)'
    SetCtlColors $HWNDPARENT 0xF4EFF7 0x231A29
    Push $HWNDPARENT
    Call ${un}HpClipChildren
    ; 기본 컨트롤(뒤로/다음/취소, 상표 글, 머리)은 지우지 않고 보이지 않는 곳으로 옮긴다: 다음 버튼이 기본 버튼으로
    ; 남아 Enter는 설치를, Esc·닫기는 취소를 그대로 한다.
    StrCpy $1 0
    ${Do}
      FindWindow $2 "" "" $HWNDPARENT $1
      ${If} $2 = 0
        ${Break}
      ${EndIf}
      System::Call 'user32::SetWindowPos(p r2, p 0, i -6000, i -6000, i 0, i 0, i 0x15)'
      StrCpy $1 $2
    ${Loop}
    Call ${un}HpStrings
    Call ${un}HpFonts
    ${If} $PassiveMode = 1
      StrCpy $HpClientW ${HP_PW}
      StrCpy $HpHeroH ${HP_PHERO}
      StrCpy $HpBodyH ${HP_PBODY}
      !insertmacro HP_HERO_CTL $HpHeroIcon ${HP_STYLE_ICON} 24 18 40 40 ""
      StrCpy $3 40
      !insertmacro HP_HERO_CTL $HpHeroTitle ${HP_STYLE_HERO} 80 14 316 26 "Hushpad"
      !insertmacro HP_HERO_CTL $HpHeroTag ${HP_STYLE_HERO} 80 40 316 22 "$L_UpdWorking"
      !insertmacro HP_FONT $0 "Segoe UI Semibold" 18 400
      SendMessage $HpHeroTitle ${WM_SETFONT} $0 1
    ${Else}
      StrCpy $HpClientW ${HP_W}
      StrCpy $HpHeroH ${HP_HERO}
      StrCpy $HpBodyH ${HP_BODY}
      !insertmacro HP_HERO_CTL $HpHeroIcon ${HP_STYLE_ICON} ${HP_PAD} 34 60 60 ""
      StrCpy $3 60
      !insertmacro HP_HERO_CTL $HpHeroTitle ${HP_STYLE_HERO} 116 34 400 40 "Hushpad"
      !insertmacro HP_HERO_CTL $HpHeroTag ${HP_STYLE_HERO} 117 74 410 22 "$L_Tag"
      SendMessage $HpHeroTitle ${WM_SETFONT} $HpFontTitle 1
      ; 띠 아래 가는 선: 자두 · 밝은 자두 · 복숭아
      IntOp $4 ${HP_W} * 56
      IntOp $4 $4 / 100
      IntOp $5 ${HP_W} * 22
      IntOp $5 $5 / 100
      IntOp $6 $4 + $5
      IntOp $7 ${HP_W} - $6
      !insertmacro HP_HERO_CTL $0 0x50000000 0 129 $4 3 ""
      SetCtlColors $0 0x7A3C93 0x7A3C93
      !insertmacro HP_HERO_CTL $0 0x50000000 $4 129 $5 3 ""
      SetCtlColors $0 0xB262CC 0xB262CC
      !insertmacro HP_HERO_CTL $0 0x50000000 $6 129 $7 3 ""
      SetCtlColors $0 0xFFB38A 0xFFB38A
    ${EndIf}
    SetCtlColors $HpHeroIcon 0xF4EFF7 0x231A29
    SetCtlColors $HpHeroTitle 0xF4EFF7 0x231A29
    SetCtlColors $HpHeroTag 0xC9BCD0 0x231A29
    SendMessage $HpHeroTag ${WM_SETFONT} $HpFontTag 1
    ; exe 자신의 아이콘 그룹에서 앱 아이콘을 장치 크기 그대로 읽는다
    !insertmacro HP_PX $3 $3
    System::Call 'kernel32::GetModuleHandleW(p 0) p .r1'
    System::Call 'user32::LoadImageW(p r1, p 103, i 1, i r3, i r3, i 0) p .r2'
    SendMessage $HpHeroIcon 0x170 $2 0   ; STM_SETICON
    StrCpy $HpPlaced 0
    Call ${un}HpLayout
  FunctionEnd

  ; 창 제목은 고른 언어를 따른다.
  Function ${un}HpCaption
    !if "${un}" == "un."
      SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$L_UnCaption"
    !else
      SendMessage $HWNDPARENT ${WM_SETTEXT} 0 "STR:$L_Caption"
    !endif
  FunctionEnd

  ; 본문을 채우는 페이지 대화상자를 시작한다.
  Function ${un}HpPage
    StrCpy $HpBtnA 0
    StrCpy $HpBtnB 0
    StrCpy $HpLinkA 0
    StrCpy $HpHot 0
    StrCpy $HpBtnAKind 1
    Call ${un}HpCaption
    Call ${un}HpLayout
    StrCpy $HpPageH 0
    nsDialogs::Create 1018
    Pop $HpDlg
    SetCtlColors $HpDlg 0x1C1A1F 0xFFFFFF
    Push $HpDlg
    Call ${un}HpClipChildren
  FunctionEnd

  ; WS_CLIPCHILDREN: 창이 바탕을 지울 때 컨트롤 위를 덮어 칠하지 않는다 (크기 바꿀 때 깜박임 없음).
  Function ${un}HpClipChildren
    Exch $0
    Push $1
    System::Call 'user32::GetWindowLongW(p r0, i -16) i .r1'
    IntOp $1 $1 | 0x02000000
    System::Call 'user32::SetWindowLongW(p r0, i -16, i r1)'
    Pop $1
    Pop $0
  FunctionEnd

  ; 납작한 버튼과 링크의 마우스 올림 색 (Win32 static에는 그런 상태가 없다).
  Function ${un}HpHoverTick
    System::Call 'user32::GetCursorPos(*l .r1)'
    System::Call 'user32::WindowFromPoint(l r1) p .r2'
    ${If} $2 <> $HpBtnA
    ${AndIf} $2 <> $HpBtnB
    ${AndIf} $2 <> $HpLinkA
      StrCpy $2 0
    ${EndIf}
    ${If} $2 = $HpHot
      Return
    ${EndIf}
    StrCpy $3 $HpHot
    StrCpy $HpHot $2
    ${If} $3 <> 0
      Push $3
      Push 0
      Call ${un}HpPaintButton
    ${EndIf}
    ${If} $2 <> 0
      Push $2
      Push 1
      Call ${un}HpPaintButton
    ${EndIf}
  FunctionEnd

  ; 스택: hwnd, hot(0/1)
  Function ${un}HpPaintButton
    Exch $1   ; hot
    Exch
    Exch $0   ; hwnd
    ${If} $0 = $HpBtnA
      ${If} $HpBtnAKind = 3
        ${If} $1 = 1
          SetCtlColors $0 0xFFFFFF 0xA8303E
        ${Else}
          SetCtlColors $0 0xFFFFFF 0xC23B4A
        ${EndIf}
      ${Else}
        ${If} $1 = 1
          SetCtlColors $0 0xFFFFFF 0x8C47A8
        ${Else}
          SetCtlColors $0 0xFFFFFF 0x7A3C93
        ${EndIf}
      ${EndIf}
    ${ElseIf} $0 = $HpBtnB
      ${If} $1 = 1
        SetCtlColors $0 0x1C1A1F 0xE3E0E8
      ${Else}
        SetCtlColors $0 0x1C1A1F 0xEFEDF2
      ${EndIf}
    ${ElseIf} $0 = $HpLinkA
      ${If} $1 = 1
        SetCtlColors $0 0x5A2B6E 0xFFFFFF
      ${Else}
        SetCtlColors $0 0x7A3C93 0xFFFFFF
      ${EndIf}
    ${EndIf}
    System::Call 'user32::InvalidateRect(p r0, p 0, i 1)'
    Pop $0
    Pop $1
  FunctionEnd

  ; 주 버튼: 숨긴 다음/설치/마침 버튼을 누른 것과 같다.
  Function ${un}HpNext
    SendMessage $HWNDPARENT ${WM_COMMAND} 1 0
  FunctionEnd

  !if "${un}" == "un."
    Function ${un}HpCancel
      SendMessage $HWNDPARENT ${WM_COMMAND} 2 0
    FunctionEnd
  !endif

  ; 아래 버튼 줄: 주 버튼은 오른쪽, 조용한 버튼은 그 왼쪽(있으면). $0 = 줄 위치(DIP), $1 = 주 버튼 너비,
  ; $2 = 조용한 버튼 너비(0 = 없음), $R1 / $R2 = 글.
  Function ${un}HpFooter
    IntOp $3 ${HP_W} - ${HP_PAD}
    IntOp $3 $3 - $1
    !insertmacro HP_BUTTON $HpBtnA $3 $0 $1 ${HP_BTN_H} "$R1"
    ${If} $2 > 0
      IntOp $3 $3 - 10
      IntOp $3 $3 - $2
      !insertmacro HP_BUTTON $HpBtnB $3 $0 $2 ${HP_BTN_H} "$R2"
      SetCtlColors $HpBtnB 0x1C1A1F 0xEFEDF2
      ${NSD_OnClick} $HpBtnB ${un}HpQuietClick
    ${EndIf}
    ${If} $HpBtnAKind = 3
      SetCtlColors $HpBtnA 0xFFFFFF 0xC23B4A
    ${Else}
      SetCtlColors $HpBtnA 0xFFFFFF 0x7A3C93
    ${EndIf}
    ${NSD_OnClick} $HpBtnA ${un}HpPrimaryClick
    ${NSD_CreateTimer} ${un}HpHoverTick 40
  FunctionEnd

  ; 페이지의 제목·글·작은 글. $R3 제목, $R4 글, $R5 작은 글("" = 없음)
  Function ${un}HpTexts
    !insertmacro HP_LABEL $0 ${HP_PAD} 26 ${HP_TEXTW} 30 "$R3" $HpFontHead
    SetCtlColors $0 0x1C1A1F 0xFFFFFF
    !insertmacro HP_LABEL $0 ${HP_PAD} 62 ${HP_TEXTW} 22 "$R4" $HpFontBody
    SetCtlColors $0 0x4A4550 0xFFFFFF
    ${If} $R5 != ""
      !insertmacro HP_LABEL $0 ${HP_PAD} 86 ${HP_TEXTW} 20 "$R5" $HpFontSmall
      SetCtlColors $0 0x6E6875 0xFFFFFF
    ${EndIf}
  FunctionEnd

  ; 진행 페이지: NSIS의 진행 대화상자(막대 + 상태 줄)를 다시 꾸미고 자세한 목록은 숨긴다.
  Function ${un}HpInstShow
    Call ${un}HpCaption
    ${If} $PassiveMode <> 1
      ; 옵션을 편 채였으면 접힌 높이로
      StrCpy $HpBodyH ${HP_BODY}
      Call ${un}HpLayout
    ${EndIf}
    FindWindow $HpDlg "#32770" "" $HWNDPARENT
    ; 기본 진행 대화상자는 자기 크기를 지키고 막대 말고도 여러 개가 있다: 본문을 채우게 하고 막대(1004)와
    ; 상태 줄(1006) 말고는(자세한 목록, 그 버튼, 아이콘) 보이지 않는 곳으로
    !insertmacro HP_PLACE $HpDlg 0 $HpHeroH $HpClientW $HpBodyH
    Push $HpDlg
    Call ${un}HpClipChildren
    StrCpy $1 0
    ${Do}
      FindWindow $2 "" "" $HpDlg $1
      ${If} $2 = 0
        ${Break}
      ${EndIf}
      System::Call 'user32::GetDlgCtrlID(p r2) i .r3'
      ${If} $3 <> 1004
      ${AndIf} $3 <> 1006
        System::Call 'user32::SetWindowPos(p r2, p 0, i -6000, i -6000, i 0, i 0, i 0x15)'
      ${EndIf}
      StrCpy $1 $2
    ${Loop}
    GetDlgItem $1 $HpDlg 1004
    GetDlgItem $2 $HpDlg 1006
    ; 납작한 막대: 테마·테두리 없음, 매끈하게, 브랜드 색
    System::Call 'uxtheme::SetWindowTheme(p r1, w "", w "")'
    System::Call 'user32::GetWindowLongW(p r1, i -16) i .r3'
    IntOp $3 $3 & 0xFF7FFFFF
    IntOp $3 $3 | 1
    System::Call 'user32::SetWindowLongW(p r1, i -16, i r3)'
    System::Call 'user32::SetWindowLongW(p r1, i -20, i 0)'
    SendMessage $2 ${WM_SETFONT} $HpFontSmall 1
    ${If} $PassiveMode = 1
      SetCtlColors $HpDlg 0xF4EFF7 0x231A29
      SendMessage $1 0x2001 0 0x00473A4C   ; PBM_SETBKCOLOR (0x4C3A47의 BGR)
      SendMessage $1 0x0409 0 0x008AB3FF   ; PBM_SETBARCOLOR 복숭아 (0xFFB38A의 BGR)
      !insertmacro HP_PLACE $1 24 8 372 4
      System::Call 'user32::SetWindowPos(p r2, p 0, i -6000, i -6000, i 0, i 0, i 0x15)'
    ${Else}
      SetCtlColors $HpDlg 0x1C1A1F 0xFFFFFF
      SetCtlColors $2 0x6E6875 0xFFFFFF
      SendMessage $1 0x2001 0 0x00F2EDEF   ; PBM_SETBKCOLOR (0xEFEDF2의 BGR)
      SendMessage $1 0x0409 0 0x00933C7A   ; PBM_SETBARCOLOR 자두 (0x7A3C93의 BGR)
      !insertmacro HP_PLACE $1 ${HP_PAD} 102 ${HP_TEXTW} 6
      !insertmacro HP_PLACE $2 ${HP_PAD} 64 ${HP_TEXTW} 22
      ; 페이지 제목
      !insertmacro HP_PX $HpX ${HP_PAD}
      !insertmacro HP_PX $HpY 26
      !insertmacro HP_PX $HpCW ${HP_TEXTW}
      !insertmacro HP_PX $HpCH 30
      !if "${un}" == "un."
        StrCpy $3 $L_UnWorking
      !else
        StrCpy $3 $L_Working
      !endif
      System::Call 'user32::CreateWindowExW(i 0, w "STATIC", w "$3", i ${HP_STYLE_HERO}, i $HpX, i $HpY, i $HpCW, i $HpCH, p $HpDlg, p 0, p 0, p 0) p .r3'
      SendMessage $3 ${WM_SETFONT} $HpFontHead 1
      SetCtlColors $3 0x1C1A1F 0xFFFFFF
    ${EndIf}
    System::Call 'user32::SetWindowPos(p r1, p 0, i 0, i 0, i 0, i 0, i 0x37)'   ; SWP_FRAMECHANGED|NOMOVE|NOSIZE|NOZORDER|NOACTIVATE
  FunctionEnd

  ; 시험용 빌드: 진행 막대를 중간쯤에 세워 둔다 (NSIS 막대 범위 0..30000)
  !ifdef SCREENSHOT_PAGE
  Function ${un}HpShotBar
    FindWindow $0 "#32770" "" $HWNDPARENT
    GetDlgItem $1 $0 1004
    SendMessage $1 0x0402 12600 0   ; PBM_SETPOS
  FunctionEnd
  !endif
!macroend

!insertmacro HP_SHARED ""
!insertmacro HP_SHARED "un."

; ---------------------------------------------------------------------------------------------------------------
; 설치 페이지: 한 화면 -> 진행 -> 마침
; ---------------------------------------------------------------------------------------------------------------
Page custom HpWelcomeCreate HpWelcomeLeave
Page instfiles "" HpInstShow ""
Page custom HpFinishCreate HpFinishLeave

Function .onGUIInit
  Call HpInitWindow
FunctionEnd

; 설치 화면. 옵션(언어·폴더·바탕화면 바로가기)은 늘 버튼 아래에 만들어 두고, 펼쳤을 때만 창이 그만큼 커진다
; (HpAnimate). 페이지를 다시 만들지 않으니 깜박임이 없다.
Function HpWelcomeCreate
  ${If} $PassiveMode = 1
    Abort
  ${EndIf}
  !ifdef HP_SHOT_SKIPWELCOME
    Abort
  !endif
  StrCpy $HpReloading 0
  ${If} $HpOpt = 1
    IntOp $HpBodyH ${HP_BODY} + ${HP_OPTS}
  ${Else}
    StrCpy $HpBodyH ${HP_BODY}
  ${EndIf}
  IntOp $HpPageH ${HP_BODY} + ${HP_OPTS}
  Call HpPage
  StrCpy $R3 $L_Head
  StrCpy $R4 $L_Text
  StrCpy $R5 $L_Meta
  Call HpTexts

  ; 버튼 줄: 왼쪽에 옵션 펼치기, 오른쪽에 버튼 하나
  !insertmacro HP_CTL $HpLinkA STATIC 0x50000380 0 ${HP_PAD} ${HP_FOOT} 240 ${HP_BTN_H} ""
  SendMessage $HpLinkA ${WM_SETFONT} $HpFontBody 1
  SetCtlColors $HpLinkA 0x7A3C93 0xFFFFFF
  Call HpOptionsArrow
  ${NSD_OnClick} $HpLinkA HpToggleOptions
  StrCpy $0 ${HP_FOOT}
  StrCpy $1 148
  ${If} $LANGUAGE == 1041
  ${AndIf} $HpKind = 3
    StrCpy $1 200
  ${ElseIf} $LANGUAGE == 1033
  ${AndIf} $HpKind = 3
    StrCpy $1 180
  ${EndIf}
  StrCpy $2 0
  StrCpy $R1 $L_Go
  Call HpFooter

  ; 접힌 옵션
  !insertmacro HP_CTL $1 STATIC 0x50000000 0 ${HP_PAD} ${HP_BODY} ${HP_TEXTW} 1 ""
  SetCtlColors $1 0xE3E0E7 0xE3E0E7
  ; 언어
  !insertmacro HP_LABEL $1 ${HP_PAD} 206 120 24 "$L_Lang" $HpFontBody
  SetCtlColors $1 0x4A4550 0xFFFFFF
  !insertmacro HP_CTL $HpCombo COMBOBOX 0x50210003 0 160 202 220 200 ""
  SendMessage $HpCombo ${WM_SETFONT} $HpFontUi 1
  ${NSD_CB_AddString} $HpCombo "한국어"
  ${NSD_CB_AddString} $HpCombo "English"
  ${NSD_CB_AddString} $HpCombo "日本語"
  ${NSD_CB_AddString} $HpCombo "简体中文"
  ${If} $LANGUAGE == 1033
    SendMessage $HpCombo ${CB_SETCURSEL} 1 0
  ${ElseIf} $LANGUAGE == 1041
    SendMessage $HpCombo ${CB_SETCURSEL} 2 0
  ${ElseIf} $LANGUAGE == 2052
    SendMessage $HpCombo ${CB_SETCURSEL} 3 0
  ${Else}
    SendMessage $HpCombo ${CB_SETCURSEL} 0 0
  ${EndIf}
  ${NSD_OnChange} $HpCombo HpLanguageChanged
  ; 폴더
  !insertmacro HP_LABEL $1 ${HP_PAD} 246 120 24 "$L_Dir" $HpFontBody
  SetCtlColors $1 0x4A4550 0xFFFFFF
  ${If} $HpKind <> 0
    ; 이미 설치된 것은 그 자리에서 업데이트: 폴더는 회색 입력칸이 아니라 읽기 전용 글(긴 경로는 가운데를 …로)
    StrCpy $HpDirEdit 0
    StrCpy $HpBrowseBtn 0
    !insertmacro HP_CTL $1 STATIC 0x50008280 0 160 244 364 26 "$INSTDIR"   ; SS_PATHELLIPSIS|SS_CENTERIMAGE
    SendMessage $1 ${WM_SETFONT} $HpFontUi 1
    SetCtlColors $1 0x1C1A1F 0xFFFFFF
    !insertmacro HP_LABEL $1 160 270 364 20 "$L_DirLocked" $HpFontSmall
    SetCtlColors $1 0x6E6875 0xFFFFFF
  ${Else}
    !insertmacro HP_CTL $HpDirEdit EDIT 0x50010080 0x200 160 242 266 28 "$INSTDIR"
    SendMessage $HpDirEdit ${WM_SETFONT} $HpFontUi 1
    ${NSD_OnChange} $HpDirEdit HpDirChanged
    !insertmacro HP_CTL $HpBrowseBtn BUTTON 0x50010000 0 434 241 90 30 "$L_Change"
    SendMessage $HpBrowseBtn ${WM_SETFONT} $HpFontBody 1
    ${NSD_OnClick} $HpBrowseBtn HpBrowse
  ${EndIf}
  ; 바탕화면 바로가기
  ${If} $HpKind <> 0
    StrCpy $0 300
  ${Else}
    StrCpy $0 286
  ${EndIf}
  !insertmacro HP_CTL $HpDeskCheck BUTTON 0x50012C03 0 160 $0 364 26 "$L_Desktop"
  SendMessage $HpDeskCheck ${WM_SETFONT} $HpFontBody 1
  SetCtlColors $HpDeskCheck 0x1C1A1F 0xFFFFFF
  ${If} $HpDesktop = 1
    ${NSD_Check} $HpDeskCheck
  ${EndIf}
  ${NSD_OnClick} $HpDeskCheck HpDeskChanged
  Call HpOptionsEnable

  ; 언어를 바꾼 뒤에는 그리기를 잠근 채 페이지를 다시 만들었다: 한 번에 보여 준다
  ${If} $HpLocked = 1
    StrCpy $HpLocked 0
    System::Call 'user32::LockWindowUpdate(p 0)'
    System::Call 'user32::RedrawWindow(p $HWNDPARENT, p 0, p 0, i 0x585)'   ; ERASE|FRAME|INVALIDATE|ALLCHILDREN|UPDATENOW
  ${EndIf}
  nsDialogs::Show
FunctionEnd

; 접혀 있으면 ▾, 펼쳐져 있으면 ▴
Function HpOptionsArrow
  ${If} $HpOpt = 1
    SendMessage $HpLinkA ${WM_SETTEXT} 0 "STR:$L_Options  ▴"
  ${Else}
    SendMessage $HpLinkA ${WM_SETTEXT} 0 "STR:$L_Options  ▾"
  ${EndIf}
FunctionEnd

; 접힌 옵션은 키보드 포커스를 받지 않는다 (보이지 않으니까).
Function HpOptionsEnable
  EnableWindow $HpCombo $HpOpt
  EnableWindow $HpDeskCheck $HpOpt
  ${If} $HpDirEdit <> 0
    EnableWindow $HpDirEdit $HpOpt
    EnableWindow $HpBrowseBtn $HpOpt
  ${EndIf}
FunctionEnd

Function HpPrimaryClick
  Call HpNext
FunctionEnd

Function HpQuietClick
  ; 마침 화면: 닫기
  Call HpNext
FunctionEnd

Function HpToggleOptions
  ${If} $HpOpt = 1
    StrCpy $HpOpt 0
    IntOp $HpBodyH ${HP_BODY} + 0
    Call HpOptionsArrow
    ; 가려지기 전에 포커스를 옵션 밖으로
    GetDlgItem $0 $HWNDPARENT 1
    System::Call 'user32::SetFocus(p r0)'
    Call HpAnimate
    Call HpOptionsEnable
  ${Else}
    StrCpy $HpOpt 1
    IntOp $HpBodyH ${HP_BODY} + ${HP_OPTS}
    Call HpOptionsArrow
    Call HpOptionsEnable
    Call HpAnimate
  ${EndIf}
FunctionEnd

; 언어가 바뀌면 페이지의 모든 글과 글꼴이 바뀌므로 페이지를 다시 만든다 — 새 페이지가 다 될 때까지 그리기를 잠가
; (HpWelcomeCreate가 푼다) 컨트롤이 하나씩 나타나지 않고 한 번에 보이게.
Function HpLanguageChanged
  SendMessage $HpCombo ${CB_GETCURSEL} 0 0 $0
  ${If} $0 = 1
    StrCpy $LANGUAGE 1033
  ${ElseIf} $0 = 2
    StrCpy $LANGUAGE 1041
  ${ElseIf} $0 = 3
    StrCpy $LANGUAGE 2052
  ${Else}
    StrCpy $LANGUAGE 1042
  ${EndIf}
  System::Call 'user32::LockWindowUpdate(p $HWNDPARENT)'
  StrCpy $HpLocked 1
  Call HpStrings
  Call HpFonts
  SendMessage $HpHeroTag ${WM_SETTEXT} 0 "STR:$L_Tag"
  SendMessage $HpHeroTag ${WM_SETFONT} $HpFontTag 0
  StrCpy $HpReloading 1
  ${NSD_KillTimer} HpHoverTick
  SendMessage $HWNDPARENT 0x408 0 0   ; WM_NOTIFY_OUTER_NEXT, 0 = 이 페이지를 다시
FunctionEnd

Function HpDirChanged
  ${NSD_GetText} $HpDirEdit $INSTDIR
FunctionEnd

Function HpDeskChanged
  ${NSD_GetState} $HpDeskCheck $0
  ${If} $0 = ${BST_CHECKED}
    StrCpy $HpDesktop 1
  ${Else}
    StrCpy $HpDesktop 0
  ${EndIf}
FunctionEnd

Function HpBrowse
  nsDialogs::SelectFolderDialog "$L_PickDir" "$INSTDIR"
  Pop $0
  ${If} $0 == error
  ${OrIf} $0 == ""
    Return
  ${EndIf}
  ; 기본 폴더 페이지처럼: 고른 상위 폴더에는 앱 폴더 이름을 붙인다
  ${GetFileName} $0 $1
  ${If} $1 != "${APP}"
    StrCpy $0 "$0\${APP}"
    ; "C:\" + 이름이면 "C:\\Hushpad"가 되므로
    ${WordReplace} $0 "\\" "\" "+" $0
  ${EndIf}
  StrCpy $INSTDIR $0
  ${NSD_SetText} $HpDirEdit $INSTDIR
FunctionEnd

Function HpWelcomeLeave
  ${If} $HpReloading = 1
    StrCpy $HpReloading 0
    ${NSD_KillTimer} HpHoverTick
    Return
  ${EndIf}
  ${If} $INSTDIR == ""
    ; 폴더 칸을 비웠으면 아무것도 안 하는 대신 기본 위치로
    StrCpy $INSTDIR "$LOCALAPPDATA\Programs\${APP}"
    ${NSD_SetText} $HpDirEdit $INSTDIR
    Abort
  ${EndIf}
  ; 전체 경로만 (D:\... 또는 \\server\...): "C"나 "Apps\x"는 지금 폴더 기준으로 깔리게 된다
  StrCpy $1 $INSTDIR 2 1
  StrCpy $2 $INSTDIR 2
  ${If} $1 != ":\"
  ${AndIf} $2 != "\\"
    MessageBox MB_ICONINFORMATION|MB_OK "$L_BadDir"
    System::Call 'user32::SetFocus(p $HpDirEdit)'
    Abort
  ${EndIf}
  ${NSD_KillTimer} HpHoverTick
FunctionEnd

Function HpFinishCreate
  ${If} $PassiveMode = 1
    Abort
  ${EndIf}
  StrCpy $HpBodyH ${HP_BODY}
  Call HpPage
  StrCpy $R3 $L_DoneHead
  StrCpy $R4 $L_DoneText
  StrCpy $R5 ""
  Call HpTexts
  StrCpy $0 ${HP_FOOT}
  StrCpy $1 168
  StrCpy $2 96
  StrCpy $R1 $L_Launch
  StrCpy $R2 $L_Close
  Call HpFooter
  ${NSD_OnClick} $HpBtnA HpLaunchClick
  nsDialogs::Show
FunctionEnd

Function HpLaunchClick
  !ifndef SCREENSHOT_PAGE
    Exec '"$INSTDIR\${EXE}"'
  !endif
  Call HpNext
FunctionEnd

Function HpFinishLeave
  ${NSD_KillTimer} HpHoverTick
FunctionEnd

Function .onInstFailed
  ${IfNot} ${Silent}
  ${AndIf} $PassiveMode <> 1
    MessageBox MB_ICONEXCLAMATION|MB_OK "$L_Failed"
  ${EndIf}
FunctionEnd

; 이미 설치된 것: 0 없음, 1 옛 버전(업데이트), 2 같은 버전, 3 더 새 버전. 폴더는 그 자리 그대로.
Function HpDetectExisting
  StrCpy $HpKind 0
  StrCpy $HpOldVer ""
  ReadRegStr $0 HKCU "${UKEY}" "UninstallString"
  ${If} $0 != ""
    ReadRegStr $HpOldVer HKCU "${UKEY}" "DisplayVersion"
    ${If} $HpOldVer == ""
      StrCpy $HpKind 1
    ${Else}
      ${VersionCompare} "${VERSION}" $HpOldVer $0   ; 0 같음, 1 이 설치 프로그램이 더 새것, 2 설치된 것이 더 새것
      ${If} $0 = 0
        StrCpy $HpKind 2
      ${ElseIf} $0 = 2
        StrCpy $HpKind 3
      ${Else}
        StrCpy $HpKind 1
      ${EndIf}
    ${EndIf}
  ${EndIf}
  !ifdef FORCE_KIND
    StrCpy $HpKind ${FORCE_KIND}
    !ifdef FORCE_OLDVER
      StrCpy $HpOldVer "${FORCE_OLDVER}"
    !endif
  !endif
FunctionEnd

Function .onInit
  ${GetParameters} $R0
  StrCpy $PassiveMode 0
  ClearErrors
  ${GetOptions} $R0 "/P" $0
  ${IfNot} ${Errors}
    StrCpy $PassiveMode 1
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/WAITPID=" $WaitPid
  ${If} ${Errors}
    StrCpy $WaitPid ""
  ${EndIf}
  ClearErrors
  ${GetOptions} $R0 "/RELAUNCH" $0
  ${If} ${Errors}
    StrCpy $Relaunch "0"
  ${Else}
    StrCpy $Relaunch "1"
  ${EndIf}
  ; 언어 고르기 창은 없다 (업데이트가 질문에서 멈추면 안 됨): 기억한 언어나 시스템 언어, 바꾸려면 설치 옵션에서.
  Call HpPickLanguage
  Call HpDetectExisting
  Call HpStrings
  ; 바탕화면 바로가기: 이미 있으면 켠 채로, 아니면 끈 채로 시작
  StrCpy $HpDesktop 0
  ${If} ${FileExists} "$DESKTOP\${APP}.lnk"
    StrCpy $HpDesktop 1
  ${EndIf}
  StrCpy $HpOpt 0
  !ifdef SCREENSHOT_OPTS
    StrCpy $HpOpt 1
  !endif
FunctionEnd

; 앱이 끝나기를 기다린다 (자동 업데이트). 창 없이, 최대 60초.
Function WaitForApp
  ${If} $WaitPid != ""
    IntOp $0 $WaitPid + 0
    ${If} $0 > 0
      System::Call 'kernel32::OpenProcess(i 0x00100000, i 0, i r0) p .r1'   ; SYNCHRONIZE
      ${If} $1 <> 0
        System::Call 'kernel32::WaitForSingleObject(p r1, i 60000) i .r2'
        System::Call 'kernel32::CloseHandle(p r1)'
      ${EndIf}
    ${EndIf}
  ${EndIf}
FunctionEnd

; 설치 폴더의 Hushpad.exe를 지울 수 있을 때까지 (실행 중이면 끄라고 안내). 조용한 설치면 잠깐씩 다시 시도(약 20초).
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
      MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "$L_Running" IDRETRY retry
      Quit
    give_up:
      Abort
  done:
FunctionEnd

Section "Install"
!ifdef SCREENSHOT_PAGE
  ; 시험용 빌드: 아무것도 설치하지 않는다
  !ifdef HP_SHOT_UN
    SetOutPath "$INSTDIR"
    WriteUninstaller "$INSTDIR\${UNINST}"
  !endif
  !ifdef HP_SHOT_PROGRESS
    !insertmacro HP_STEP "$L_Copying"
    Call HpShotBar
    Sleep 120000
  !endif
!else
  Call WaitForApp
  Call EnsureNotRunning
  !insertmacro HP_STEP "$L_Copying"
  SetOutPath "$INSTDIR"
  RMDir /r "$INSTDIR\_internal"          ; 지난 버전의 남은 파일이 섞이지 않게
  File /r "${SRC}\*.*"
  WriteUninstaller "$INSTDIR\${UNINST}"

  !insertmacro HP_STEP "$L_Registering"
  CreateShortcut "$SMPROGRAMS\${APP}.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  ; 바탕화면 바로가기: 설치 옵션에서 고를 때만 (조용한 설치·/P는 만들지 않는다)
  ${IfNot} ${Silent}
  ${AndIf} $PassiveMode <> 1
  ${AndIf} $HpDesktop = 1
    CreateShortcut "$DESKTOP\${APP}.lnk" "$INSTDIR\${EXE}" "" "$INSTDIR\${EXE}" 0
  ${EndIf}

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
  ; 고른 언어를 기억 (다음 설치·제거 화면)
  WriteRegStr HKCU "${PKEY}" "Installer Language" $LANGUAGE
  ; GetSize가 상태 줄에 남긴 글을 단계 글로 되돌린다
  !insertmacro HP_STEP "$L_Registering"

  ${If} $Relaunch == "1"
    Exec '"$INSTDIR\${EXE}"'
  ${EndIf}
!endif
  ; 진행 페이지는 저절로 닫힌다: /P는 거기서 끝나고, 창은 마침 화면으로 넘어간다.
  SetAutoClose true
SectionEnd

; ---------------------------------------------------------------------------------------------------------------
; 제거 페이지: 묻기 -> 진행 -> 마침
; ---------------------------------------------------------------------------------------------------------------
UninstPage custom un.HpConfirmCreate un.HpConfirmLeave
UninstPage instfiles "" un.HpInstShow ""
UninstPage custom un.HpDoneCreate un.HpDoneLeave

Function un.onGUIInit
  Call un.HpInitWindow
FunctionEnd

Function un.HpConfirmCreate
  ${If} $PassiveMode = 1
    Abort
  ${EndIf}
  !ifdef HP_SHOT_UNSKIP
    Abort
  !endif
  StrCpy $HpBodyH ${HP_BODY}
  Call un.HpPage
  StrCpy $R3 $L_UnHead
  StrCpy $R4 $L_UnText
  StrCpy $R5 ""
  Call un.HpTexts
  !insertmacro HP_CTL $HpDataCheck BUTTON 0x50012C03 0 ${HP_PAD} 88 ${HP_TEXTW} 26 "$L_UnData"
  SendMessage $HpDataCheck ${WM_SETFONT} $HpFontBody 1
  SetCtlColors $HpDataCheck 0x1C1A1F 0xFFFFFF
  StrCpy $HpBtnAKind 3
  StrCpy $0 ${HP_FOOT}
  StrCpy $1 128
  ${If} $LANGUAGE == 1041
    StrCpy $1 160
  ${EndIf}
  StrCpy $2 96
  ${If} $LANGUAGE == 1041
    StrCpy $2 110
  ${EndIf}
  StrCpy $R1 $L_UnGo
  StrCpy $R2 $L_Cancel
  Call un.HpFooter
  nsDialogs::Show
FunctionEnd

Function un.HpPrimaryClick
  Call un.HpNext
FunctionEnd

Function un.HpQuietClick
  ; 묻는 화면: 취소 (마침 화면에는 조용한 버튼이 없다)
  Call un.HpCancel
FunctionEnd

Function un.HpConfirmLeave
  ${NSD_KillTimer} un.HpHoverTick
  ${NSD_GetState} $HpDataCheck $0
  ${If} $0 = ${BST_CHECKED}
    StrCpy $DeleteDataState 1
  ${Else}
    StrCpy $DeleteDataState 0
  ${EndIf}
FunctionEnd

Function un.HpDoneCreate
  ${If} $PassiveMode = 1
    Abort
  ${EndIf}
  StrCpy $HpBodyH ${HP_BODY}
  Call un.HpPage
  StrCpy $R3 $L_UnDoneHead
  StrCpy $R4 $L_UnDoneText
  StrCpy $R5 ""
  Call un.HpTexts
  StrCpy $0 ${HP_FOOT}
  StrCpy $1 128
  StrCpy $2 0
  StrCpy $R1 $L_Close
  Call un.HpFooter
  nsDialogs::Show
FunctionEnd

Function un.HpDoneLeave
  ${NSD_KillTimer} un.HpHoverTick
FunctionEnd

Function un.onInit
  ${GetParameters} $R0
  StrCpy $PassiveMode 0
  ClearErrors
  ${GetOptions} $R0 "/P" $0
  ${IfNot} ${Errors}
    StrCpy $PassiveMode 1
  ${EndIf}
  StrCpy $DeleteDataState 0
  StrCpy $HpKind 0
  ; 설치할 때 고른 언어, 없으면 시스템 언어. 묻는 창 없음
  Call un.HpPickLanguage
  Call un.HpStrings
FunctionEnd

Function un.EnsureNotRunning
  IfFileExists "$INSTDIR\${EXE}" 0 done
  retry:
    ClearErrors
    Delete "$INSTDIR\${EXE}"
    IfErrors 0 done
    IfSilent give_up
    MessageBox MB_RETRYCANCEL|MB_ICONEXCLAMATION "$L_Running" IDRETRY retry
    Quit
    give_up:
      Abort
  done:
FunctionEnd

Section "Uninstall"
  SetDetailsPrint none
!ifdef SCREENSHOT_PAGE
  ; 시험용 빌드: 아무것도 지우지 않는다
  !ifdef HP_SHOT_UNPROGRESS
    Call un.HpShotBar
    Sleep 120000
  !endif
!else
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
  DeleteRegValue HKCU "${PKEY}" "Installer Language"
  DeleteRegKey /ifempty HKCU "${PKEY}"
  DeleteRegKey /ifempty HKCU "${PKEY_PARENT}"
  ; 설정·기억한 열쇠: 제거 화면에서 고른 때만 (조용한 제거는 늘 남긴다). 메모(보관 폴더)는 절대 건드리지 않는다.
  ${If} $DeleteDataState = 1
    SetShellVarContext current
    RMDir /r "$APPDATA\${APP}"
    RMDir /r "$LOCALAPPDATA\${APP}"
  ${EndIf}
!endif
  ; 진행 페이지는 저절로 닫히고 마침 화면으로 넘어간다.
  SetAutoClose true
SectionEnd
