# Microsoft Store용 MSIX

zip 배포판과 같은 `dist\Hushpad\` 앱 폴더를 MSIX 패키지 하나로 묶습니다. zip 빌드는 바뀌지 않습니다.

## 만들기

```powershell
python build.py                       # dist\Hushpad\ 와 zip (자체 점검 포함)
python packaging\msix\make_msix.py    # dist\Hushpad-<버전>.msix
```

- 필요: Windows 10/11 SDK의 `makeappx.exe`·`makepri.exe` (`C:\Program Files (x86)\Windows Kits\10\bin\<버전>\x64`). 없으면 설치 방법을 알려 주고 멈춥니다.
- 패키지 버전은 `hushpad_app.__version__` 뒤에 `.0`을 붙입니다(1.0.0 → 1.0.0.0). Store는 네 번째 자리가 0이어야 합니다.
- 중간 결과는 `build\msix\`(`layout\` = 패키지에 들어가는 그대로, `pri\` = 아이콘·언어별 이름)에 남습니다.
- 서명하지 않습니다. Store에 올리면 Microsoft가 서명합니다.

### 들어가는 것

| 위치 | 내용 |
|---|---|
| `AppxManifest.xml` | `AppxManifest.template.xml`에 이름·게시자·버전을 채운 것 |
| `Hushpad\` | `dist\Hushpad\` 그대로 (LICENSE·NOTICE·THIRD_PARTY_NOTICES.md·licenses 포함) |
| `Assets\` | 앱 아이콘에서 만든 타일·로고 (배율 100/125/150/200/400, 작업 표시줄용 16/24/32/48/256). 40px 이하는 작은 크기용 단순한 그림 |
| `resources.pri` | 아이콘 배율 선택과 언어별 표시 이름·설명 (ko-KR 기본, en-US, ja-JP, zh-CN) |

### 매니페스트 요점

- 최소 Windows 10 2004(10.0.19041) — 캡처에서 창 숨기기가 여기부터 됩니다.
- 권한은 `runFullTrust` 하나뿐 (일반 데스크톱 앱으로 실행).
- 앱은 `Hushpad` 하나. 시작 작업(`HushpadStartup`, 처음부터 켜짐)은 같은 앱의 복사본 `Hushpad\HushpadStartup.exe`를 실행하고,
  앱은 이 이름으로 시작되면 창 없이 트레이로 뜹니다. (숨은 앱 항목 `AppListEntry="none"`은 Store에서 별도 허가가 필요해 쓰지 않습니다.)
- 앱은 패키지로 실행 중인지 스스로 알아내고(`GetCurrentPackageFullName`), 그때는 레지스트리 Run 키를 쓰지 않습니다.
  메뉴의 "Windows 시작할 때 실행" 체크 대신 **Windows 시작 프로그램 설정 열기…**가 나와 `설정 › 앱 › 시작 프로그램`을 엽니다.
- 설정(`%APPDATA%\Hushpad`)·백업·기억한 암호(`%LOCALAPPDATA%\Hushpad`)는 Windows가 패키지 전용 폴더
  (`%LOCALAPPDATA%\Packages\<패키지 이름>_<게시자 해시>\LocalCache\`)로 돌려 보관합니다. 앱을 제거하면 함께 지워집니다.
  보관 폴더(기본 `문서\Hushpad`)의 메모는 그대로 남습니다.

## Partner Center에서 받아 넣을 값

`Partner Center › 앱 및 게임 › Hushpad › 제품 관리 › 제품 ID`에 나오는 세 값을 `store_identity.json`에 넣습니다
(또는 `--name`·`--publisher`·`--publisher-display-name`으로 넘김).

| store_identity.json | Partner Center 표시 | 예 |
|---|---|---|
| `Name` | Package/Identity/Name | `12345KyeongjinHwang.Hushpad` |
| `Publisher` | Package/Identity/Publisher | `CN=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX` |
| `PublisherDisplayName` | Package/Properties/PublisherDisplayName | `Kyeongjin Hwang` (개인 계정의 게시자 표시 이름) |

값이 `TODO-from-Partner-Center`이면 만들 수는 있지만 Store에 올리면 거절됩니다(만들 때 경고가 나옵니다).

## 이 PC에서 설치해 보기 (선택)

패키지 모드 동작(시작 작업으로 트레이 시작, 설정 열기 메뉴, 레지스트리 안 건드림, 패키지 전용 폴더)은 설치해야만 확인할 수 있습니다.
둘 다 시스템을 바꾸는 일이니 필요할 때만 하고, 끝나면 되돌리세요.

### 방법 1: 개발자 모드에서 폴더째 등록 (서명 필요 없음)

1. `설정 › 시스템 › 개발자용 › 개발자 모드` 켜기
2. `python packaging\msix\make_msix.py` 실행 뒤
   ```powershell
   Add-AppxPackage -Register build\msix\layout\AppxManifest.xml
   ```
3. 되돌리기: `Get-AppxPackage *TODO-from-Partner-Center* | Remove-AppxPackage` (이름을 바꿨다면 그 이름), 개발자 모드 끄기

### 방법 2: 시험용 인증서로 서명한 .msix 설치

인증서의 주체(Subject)와 매니페스트의 Publisher가 정확히 같아야 합니다.

```powershell
# 1) 이 이름으로 패키지를 만든다
python packaging\msix\make_msix.py --publisher "CN=Hushpad Test"

# 2) 시험용 코드 서명 인증서 (현재 사용자 저장소)
$cert = New-SelfSignedCertificate -Type Custom -Subject "CN=Hushpad Test" -KeyUsage DigitalSignature `
  -FriendlyName "Hushpad MSIX test" -CertStoreLocation Cert:\CurrentUser\My `
  -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3", "2.5.29.19={text}")
$pw = Read-Host -AsSecureString "pfx 암호"
Export-PfxCertificate -Cert $cert -FilePath $env:TEMP\hushpad-test.pfx -Password $pw
Export-Certificate -Cert $cert -FilePath $env:TEMP\hushpad-test.cer

# 3) 서명 (SDK의 signtool)
& "C:\Program Files (x86)\Windows Kits\10\bin\10.0.26100.0\x64\signtool.exe" sign /fd SHA256 `
  /f $env:TEMP\hushpad-test.pfx /p (Read-Host "pfx 암호") dist\Hushpad-1.0.0.msix

# 4) 이 PC가 인증서를 믿게 한다 (관리자 PowerShell)
Import-Certificate -FilePath $env:TEMP\hushpad-test.cer -CertStoreLocation Cert:\LocalMachine\TrustedPeople

# 5) 설치
Add-AppxPackage dist\Hushpad-1.0.0.msix
```

되돌리기: `Get-AppxPackage *TODO-from-Partner-Center* | Remove-AppxPackage`, `certlm.msc › 신뢰할 수 있는 사람`과
`certmgr.msc › 개인`에서 "Hushpad Test" 인증서 지우기, pfx·cer 파일 지우기.

### 설치 뒤 확인할 것

- [ ] 시작 메뉴에 "Hushpad"가 한 개만 보이고 아이콘이 깨지지 않는다 (트레이용 앱은 안 보여야 함)
- [ ] `⋯ › 보안`과 트레이 메뉴에 "Windows 시작 프로그램 설정 열기…"가 있고 누르면 `설정 › 앱 › 시작 프로그램`이 열린다
- [ ] 그 목록에 Hushpad가 켜져 있다 → 로그아웃 후 로그인하면 창 없이 트레이로 시작한다
- [ ] `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`에 Hushpad 값이 생기지 않는다
- [ ] 작업 표시줄에 고정한 아이콘과 실행 중인 창이 한 아이콘으로 묶인다
- [ ] 캡처 숨기기·전역 단축키·클립보드 기록 제외가 zip 버전과 똑같이 동작한다
- [ ] 앱을 제거해도 `문서\Hushpad`의 메모는 남는다

## Windows 앱 인증 키트(WACK)

Store가 올린 패키지를 자동으로 검사하지만, 미리 보려면 SDK의 `appcert.exe`(Windows App Certification Kit)로
검사할 수 있습니다. 데스크톱 앱 검사는 패키지를 실제로 설치하고 관리자 권한이 필요하므로, 시험용 PC나 가상 머신에서 하세요.

```powershell
& "C:\Program Files (x86)\Windows Kits\10\App Certification Kit\appcert.exe" test `
  -appxpackagepath dist\Hushpad-1.0.0.msix -reportoutputpath $env:TEMP\hushpad-wack.xml
```

## Store 등록 문구·스크린샷

`store_listing\` 폴더를 보세요.
