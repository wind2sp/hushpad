# "Windows의 PC 보호" 경고 없애기 — 초보자 안내서

Hushpad를 인터넷에서 받아 실행하면 "Windows의 PC 보호 / 알 수 없는 게시자" 창이 뜹니다. 서명이 없는 새 프로그램이라서입니다.
두 가지를 함께 진행합니다.

| | A. Microsoft Store | B. SignPath 무료 코드 서명 |
|---|---|---|
| 효과 | **Store에서 설치하면 경고가 아예 없음**, 업데이트도 Store가 해 줌 | 홈페이지·GitHub에서 받는 zip에 서명이 붙음("알 수 없는 게시자" → "SignPath Foundation"), 경고는 사용자가 늘면 줄어듦 |
| 비용 | 무료(개인 계정) | 무료(오픈소스 지원) |
| 직접 하실 일 | 개인 개발자 계정 만들기, 본인 확인, 연령 등급 설문, 제출 버튼 | 신청서 제출, 2단계 인증 켜기, 승인 후 비밀값 등록, 배포 때마다 승인 클릭 |
| 제가 하는 일 | Store용 포장(MSIX), 설명·스크린샷, 앱의 Store 대응 | GitHub 자동 빌드(완료), 서명 단계 연결, 정책 문구 게시 |
| 걸리는 시간 | 본인 확인 보통 당일~며칠 + 앱 심사 보통 1~3일 | 심사 기간 안내 없음(며칠~몇 주), 새 프로젝트는 거절될 수도 있음 |

> 화면의 버튼 이름은 Microsoft·SignPath가 바꿀 수 있어요. 아래와 조금 다르면 비슷한 이름을 찾으시면 됩니다. 막히면 화면을 캡처해서 보여 주세요.

---

## A. Microsoft Store

> Store에는 **개인 계정**으로 올립니다. 앱 정보·저작권 표시는 지금처럼 나인로우파트너스(주)로 두고, Store의 게시자 이름만 개인 이름으로 보여요.
> 계정 종류(개인/회사)는 만든 뒤 바꿀 수 없어요. 나중에 회사로 옮기려면 회사 계정을 새로 만들어 앱을 넘기면 됩니다.

### A-1. 준비물 (5분)
- **개인 Microsoft 계정**: 평소 쓰시는 Microsoft 계정(Outlook·Xbox·Windows 로그인 계정 등)이면 됩니다. 없으면 https://signup.live.com 에서 만드세요.
- **신분증**: 본인 확인에 씁니다(주민등록증·운전면허증·여권 중 하나). 휴대폰 카메라로 신분증과 얼굴을 찍는 단계가 나올 수 있어요.

### A-2. 개인 개발자 계정 만들기 (10분)
1. https://storedeveloper.microsoft.com 에 들어갑니다.
2. **Get started**(시작하기)를 누르고 A-1의 Microsoft 계정으로 로그인합니다.
3. 계정 종류에서 **Individual(개인)**을 고릅니다.
4. 나라는 **대한민국**, 이름·주소·연락처를 신분증과 같게 적습니다. (주소·전화는 Microsoft 확인용이고 Store에 공개되지 않아요.)
5. **Publisher display name(게시자 표시 이름)**: `Kyeongjin Hwang` 을 권장합니다. Store의 앱 이름 아래에 이 이름이 보여요. 다른 사람이 이미 쓰는 이름은 고를 수 없어요.
6. 본인 확인 안내가 나오면 따라 합니다(신분증 촬영, 얼굴 촬영).
7. 약관에 동의하고 완료합니다. 결제 단계가 나오지 않으면 정상입니다(무료).

### A-3. 본인 확인 결과 보기 (보통 당일~며칠)
1. https://partner.microsoft.com/dashboard 에 들어가 로그인합니다.
2. 오른쪽 위 톱니바퀴(⚙) › **Account settings**에서 계정 상태를 봅니다.
3. Microsoft에서 메일이 오면 안내대로 처리합니다. 확인이 끝나면 다음 단계로 갑니다.

### A-4. 앱 이름 예약 (5분) — 본인 확인 중에도 할 수 있어요
1. Partner Center › **Apps and games**(앱 및 게임) › **+ New product**(새 제품) › **MSIX or PWA app**을 고릅니다.
2. 이름에 `Hushpad` 를 입력하고 **Check availability** › **Reserve product name**(이름 예약).
   - 이미 누가 쓰고 있다고 나오면 `Hushpad - 조용한 비밀 메모장` 처럼 바꿔 예약하고 알려 주세요.
3. 예약한 앱 화면 왼쪽 메뉴 **Product management**(제품 관리) › **Product identity**(제품 ID)를 엽니다.
4. 아래 세 줄을 **그대로 복사해서 저에게 보내 주세요.** Store용 포장에 넣어야 하는 값이에요(비밀번호 같은 비밀값이 아니라 공개되는 정보예요).
   - `Package/Identity/Name`
   - `Package/Identity/Publisher` (CN=로 시작하는 긴 값)
   - `Package/Properties/PublisherDisplayName`

### A-5. 제출 (30분) — 제가 포장 파일과 문구를 드린 뒤
예약한 앱 화면에서 **Start your submission**(제출 시작)을 누르면 항목들이 나옵니다.
1. **Pricing and availability**(가격 및 사용 가능성): 가격 **Free(무료)**, 시장은 **모든 시장**(원하면 일부만).
2. **Properties**(속성): 카테고리 **Productivity(생산성)**, 개인정보 처리방침 URL `https://gdra.mycafe24.com/hushpad/privacy.html`, 지원 URL `https://github.com/wind2sp/hushpad/issues`.
3. **Age ratings**(연령 등급): 설문에 답합니다. Hushpad는 폭력·성인 내용·채팅·위치 공유·구매 기능이 없으니 대부분 "아니요"입니다. 끝나면 보통 **3세 이상(3+)** 등급이 나옵니다.
4. **Packages**(패키지): 제가 드리는 `Hushpad-1.0.0.0.msix` 파일을 끌어다 놓습니다. 자동 검사가 통과하는지 기다립니다.
5. **Store listings**(Store 목록): 언어별로 설명·짧은 설명·기능·스크린샷을 넣습니다. 제가 언어별 파일로 정리해 드려요(`packaging\msix\store_listing\`).
6. **Submission options**(제출 옵션): 비워 둬도 됩니다. 단, "이 앱은 runFullTrust 권한을 쓰는 이유" 칸이 나오면 다음을 붙여 넣으세요:
   `Hushpad is a desktop note app built with Qt. It needs full trust to register global hotkeys, exclude its window from screen capture (SetWindowDisplayAffinity), and read Windows Notepad tabs that the user chooses to import.`
7. **Submit to the Store**(Store에 제출). 심사는 보통 1~3일입니다. 결과는 메일로 옵니다.

### A-6. 등록이 끝나면
- Store 주소(예: `https://apps.microsoft.com/detail/...`)를 알려 주시면 홈페이지 다운로드 버튼과 README에 "Microsoft Store에서 받기"를 추가하겠습니다.
- 다음 버전부터는 새 `.msix` 파일만 올려 다시 제출하면 됩니다.

---

## B. SignPath Foundation 무료 코드 서명

### B-0. 먼저 알아 둘 것
- 서명자 이름은 **"SignPath Foundation"**으로 표시돼요(본인·회사 이름이 나오진 않아요). 내 이름으로 서명하려면 유료 인증서가 필요해요.
- 승인은 재단의 판단이에요. 공개한 지 얼마 안 된 프로젝트는 "평판이 더 쌓인 뒤 다시 신청하라"는 답을 받을 수 있어요. 그래도 신청해 두면 손해는 없어요.
- 서명돼도 경고가 즉시 사라진다는 보장은 없어요. 받은 사람이 늘면 점점 사라집니다.

### B-1. GitHub 2단계 인증 켜기 (5분) — SignPath 필수 조건
1. GitHub에 **wind2sp**로 로그인 › 오른쪽 위 프로필 사진 › **Settings**.
2. 왼쪽 **Password and authentication** › **Two-factor authentication** › **Enable two-factor authentication**.
3. 휴대폰 인증 앱(Microsoft Authenticator, Google Authenticator 등)으로 QR 코드를 찍고, 나오는 6자리 숫자를 입력합니다.
4. **복구 코드(Recovery codes)를 꼭 내려받아 안전한 곳에 보관**하세요. 휴대폰을 잃어버리면 이 코드로만 들어갈 수 있어요.

### B-2. 신청서 내기 (15분)
1. https://signpath.org/apply 에 들어갑니다.
2. 신청서 칸에는 아래를 참고해서 적으세요(영어로 적는 게 좋아요).

| 칸(예상) | 적을 내용 |
|---|---|
| Project name | `Hushpad` |
| Repository URL | `https://github.com/wind2sp/hushpad` |
| Homepage / download page | `https://gdra.mycafe24.com/hushpad/` |
| License | `GPL-3.0-or-later` |
| Description | `Hushpad is a free, open-source notepad for Windows and macOS. Notes save as you type and are stored as encrypted files (AES-256-GCM). On Windows the window is excluded from screenshots and screen sharing. It has no account, no server and makes no network connections.` |
| Build system | `GitHub Actions (workflow: .github/workflows/build-windows.yml), PyInstaller` |
| Artifacts to sign | `Hushpad.exe inside Hushpad-win64.zip (portable). Bundled upstream OSS DLLs (Qt/PySide6 LGPL-3.0, FFmpeg LGPL-2.1+, Python) stay unsigned.` |
| Maintainers / contact | 이름과 회사 메일(wind2sp@9rowpar.com) |

3. 제출하면 확인 메일이 옵니다. 답장을 기다립니다.

### B-3. 승인 메일을 받으면 (20분)
1. 메일 안내대로 **SignPath 계정**을 만들고, SignPath에서도 **2단계 인증**을 켭니다.
2. SignPath가 알려 주는 **Organization ID**를 확인하고, SignPath 화면에서 **API Token**을 하나 만듭니다.
3. GitHub 저장소 › **Settings** › **Secrets and variables** › **Actions** › **New repository secret**에서 다음 두 개를 등록합니다.
   - 이름 `SIGNPATH_API_TOKEN`, 값: 방금 만든 API 토큰
   - 이름 `SIGNPATH_ORGANIZATION_ID`, 값: Organization ID
   (이 값들은 비밀값이에요. 저에게 보내지 말고 GitHub에만 넣어 주세요.)
4. 저에게 "등록했다"고만 알려 주세요. 제가 빌드에 서명 단계를 연결하고, README·홈페이지 다운로드 페이지에 SignPath가 요구하는 **코드 서명 정책** 문구를 넣겠습니다.

### B-4. 배포할 때마다 (1분)
GitHub에서 Windows 빌드를 돌리면 SignPath에 **서명 요청**이 갑니다. SignPath 메일이나 화면에서 **Approve(승인)**를 누르면 서명된 파일이 만들어집니다.

---

## 지금 이 PC에서만 경고를 안 보려면
받은 zip 파일을 **풀기 전에** 오른쪽 클릭 › **속성** › 아래쪽 **차단 해제**에 체크 › **확인**. 그 뒤 풀면 경고가 뜨지 않아요(이 PC에서만 해당).
