# 홈페이지 문구 검수 (2026-11-15)

범위: `i18n/ko.json`·`en.json`·`ja.json`·`zh.json`, `404.html`. 키 구조는 그대로이고, `node build-i18n.mjs` 생성과 `--check` 모두 통과했습니다.
404.html은 고칠 곳이 없어 그대로 두었습니다. 사실(자동 저장, 암호화 방식, 캡처 제외, 단축키, 공개 전, "무료" 표현 없음, 앱 한국어 안내 줄)은 바꾸지 않았습니다.

## 한국어 (24곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| index.description | 자동 저장되고, 모든 메모가 암호화되며, 스크린샷·화면 공유에도 보이지 않는 Windows 메모장 | 자동으로 저장되고 모든 메모가 암호화되는 Windows 메모장. 창은 스크린샷과 화면 공유에도 찍히지 않습니다. | "~되고, ~되며, ~않는" 3연속 수식을 두 문장으로 |
| lead | 저장 버튼 없이 바로 기록되고 / 보이지 않아요 | 저장 버튼을 누르지 않아도 쓰는 대로 남고 / 찍히지 않아요 | "기록되다"보다 일상어, 캡처 맥락에 맞는 동사 |
| pains.p | 남아 있는 탭이 편하지만 | 남아 있는 탭은 편하지만 | 대조 문장이라 "은"이 자연스러움 |
| pains.a1 | 미리보기 탭이라 눌러 봐도 탭이 쌓이지 않아요 | 한 번 누르면 미리보기 탭으로 열려서 이것저것 눌러 봐도… | 원리를 구체적으로, "~요" 연속 줄임 |
| pains.a2·a3 | 남겨요. … 그대로예요. / 저장돼요. … 지워져요. | 남깁니다. … 그대로예요. / 저장됩니다. … 지워져요. | 문장 끝 "~요" 반복 완화 |
| feat.lock | 다른 프로그램·검색 색인·클라우드가 내용을 읽지 못합니다 | 알아볼 수 없는 글자뿐이에요. 다른 프로그램이나 검색 색인, 클라우드도… | 가운뎃점 나열 대신 문장으로 |
| feat.hide | 스크린샷·화면 녹화·화상회의 화면 공유에 … 내 눈에만 보입니다 | 스크린샷을 찍어도, 화면을 녹화하거나 화상회의에서 공유해도 … 내 화면에서만 보입니다 | "화면" 중복, 명사 나열 해소 |
| feat.copy | …한 번이면 글자만. 두 버전을 늘 함께 가지고 있어요. | …한 번으로 글자만 복사해요. 서식 메모는 글자만 담긴 버전도 늘 함께 갖고 있습니다. | 끊긴 문장 완성, "두 버전"이 무엇인지 분명히 |
| feat.code | JSON 정리 한 번에. … 값만 복사도 돼요. | JSON도 한 번에 정리됩니다. … 값만 복사할 수 있어요. | 명사형 종결·어색한 "복사도 돼요" |
| feat.shot | 어디서든 Ctrl+Alt+S 영역 캡처, Ctrl+Alt+R 화면 녹화. | 다른 프로그램을 쓰다가도 Ctrl+Alt+S로 영역을 캡처하고 Ctrl+Alt+R로 화면을 녹화합니다. | 실제 쓰는 상황으로, 조사 살림 |
| feat.folder | 오래 안 본 메모만 모아 정리도. | 오래 안 본 메모만 모아서 정리할 수도 있어요. | "~도."로 끝나는 미완성 문장 |
| feat.sync | 파일 하나라 충돌이 적어요 | 파일 하나여서 충돌이 잘 나지 않습니다 | "~요" 연속 완화 |
| feat.search | 한 칸에서 찾아 Enter로 실행. | 입력칸 하나에서 찾고 Enter로 바로 실행합니다. | 명사형 종결 |
| capture.p | 창 자리는 그 뒤 화면으로 채워집니다 / 캡처 버튼을 눌러도 돼요 | 창이 있던 자리에는 그 뒤의 화면이 찍힙니다 / 캡처해도 돼요 | 수동 표현과 군더더기 정리 |
| capture.s3 | 메뉴에서 한 번에 해제. | 메뉴에서 한 번만 누르면 됩니다. | 명사형 종결, 제목(끌 수 있어요)과 중복 피함 |
| keys.p | 창이 닫혀 있어도(트레이) | 창을 닫아 트레이에 있을 때도 | 괄호 대신 문장으로 |
| faq 암호 분실 | 열 수 없게 만든 것이라서요 | 열 수 없게 만들었기 때문입니다 | 어색한 "것이라서요" |
| dl.hash.p | `</code> 으로` | `</code>을 실행해` | 조사 앞 띄어쓰기 오류, 받침(zip) 맞춤 |
| 그 밖 | nameLine 줄표, 스크린샷 대체 텍스트, 단축키 k2, 지울 때 괄호 | 마침표, "색으로 구분되어", "클립보드 내용을", "암호화된 채로" | 작은 다듬기 |

## English (7곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| lead | saved instantly, with no save button, and every note is encrypted into a single folder | saved as you go, no save button needed. Every note is encrypted and kept in one folder… | "encrypted into a folder"는 어색한 직역 |
| pains.a3 | anything you copy is cleared… | anything you copy **from them** is cleared… | 사실 정정: 30초 삭제는 비밀 메모만 해당 |
| pains.a1 | Preview tabs mean clicking around… | A single click opens a preview tab, so browsing around… | 원리를 구체적으로 |
| feat.copy | Both versions are always kept together. | Rich notes always keep a plain-text version alongside. | 무엇의 "두 버전"인지 불분명 |
| sec.s3 | The key is remembered by tying it… | Hushpad remembers the key by tying it… | 수동태 정리 |
| capture.s3, feat.search | switch it off from the menu in one step / And Ctrl+Alt+M… | one click in the menu turns it off / press Enter to run it | 딱딱한 표현, 문두 And 정리 |

## 日本語 (8곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| ctaMore | どこが違うの？ | ほかのメモ帳との違い | です・ます 페이지에 반말 버튼 |
| sec.h2 | どうやって守られるの？ | メモを守るしくみ | 반말 의문형 제목 |
| feat.hide | 見えるのはあなただけです | 見えるのは自分の画面だけです | 「あなた」는 번역투 |
| feat.copy | ふたつのバージョンを常に一緒に持っています | 書式付きメモは、文字だけの版もいつも一緒に保存しています | 직역 문장, 주어 불분명 |
| feat.code | JSON の整形もワンステップ | JSON もすぐに整形できます | 가타카나 남용·명사형 종결 |
| capture.p | 背後の画面で埋められます | その後ろの画面が映ります | 수동 직역 |
| capture.s3 | ワンステップで解除 | すぐに解除 | 가타카나 줄임 |
| feat.folder | 整理することも。 | 整理することもできます。 | 미완성 문장 |

## 简体中文 (11곳)

| 위치 | 전 | 후 | 이유 |
|---|---|---|---|
| footer.tagline | 无需保存按钮即可自动保存、所有笔记均加密的 Windows 记事本 | 一款不用手动保存、所有笔记都加密存放的 Windows 记事本 | 긴 관형어, 번역 느낌 |
| index.description | 无需保存按钮即可自动保存，…，窗口不会出现在截图和屏幕共享中的 Windows 记事本 | 自动保存、所有笔记加密的 Windows 记事本，窗口不会出现在… | 지나치게 긴 수식 구조 |
| feat.code / feat.search | JSON 一键格式化 / 一键把剪贴板内容存为笔记 | JSON 也能马上格式化 / 按 Ctrl+Alt+M 还能直接把… | 상투어 "一键" 제거 |
| faq 탭 가져오기 | 通过 菜单 › … 不会改动 Windows 记事本本身 | 用 菜单 › … Windows 记事本本身不受影响 | "通过" 번역투 |
| feat.lock | 即使打开文件也无法辨认 | 直接打开文件，也只能看到一堆乱码 | 구체적인 장면으로 |
| feat.copy | 导出时… 两种版本始终同时保留 | 要贴到别处时… 富文本笔记始终附带一份纯文本版本 | "导出"는 다른 기능과 혼동, 뜻 분명히 |
| sec.s3·s4 | 绑定到…来记住 / 会被标记 | 会与…绑定并记住 / 会加上标记 | 어색한 어순, 被 수동 |
| pains.a1, capture.s3 | 预览标签页让你随手点开 / 一步即可关闭 | 单击打开的是预览标签页 / 点一下就能关闭 | 자연스러운 구어 |

## 손대지 않은 것
- 승인된 태그라인(조용히 적고, 아무도 못 보게 / 각 언어 대응 문구), 제목의 "Hushpad — …" 구분 기호
- en/ja/zh `dl.uiNote`(앱 화면은 한국어뿐) — 언어 전환 기능이 나오면 직접 고칠 줄
- 404.html — 자연스러워 수정 없음
