# Security

## Reporting a vulnerability

Please email **wind2sp@9rowpar.com** with the subject "Hushpad security" and describe the issue and how to reproduce it. Do not open a public issue for security problems. We aim to reply within 7 days.

보안 문제는 공개 이슈 대신 **wind2sp@9rowpar.com**으로 알려 주세요(제목: "Hushpad security").

## What Hushpad protects, and what it doesn't

**Protected**
- Notes, history snapshots, recordings and category names are stored only as encrypted files (AES-256-GCM, a random 256-bit data key).
- The data key is wrapped with a key derived from your passphrase (scrypt, N=2^16, r=8, p=1) and stored in `vault.json`. Without the passphrase, files copied from the vault folder (for example from a cloud sync service) can't be read.
- On each device the data key is cached for convenience: Windows DPAPI (current Windows user only) or the macOS login Keychain. Another Windows account or another computer needs the passphrase.
- The window is excluded from screenshots, screen recording and screen sharing (Windows 10 2004+: `SetWindowDisplayAffinity`; macOS: window sharing disabled — some macOS 15+ capture apps ignore this).
- Copies are marked so Windows clipboard history and cloud clipboard skip them; secret notes clear the clipboard after 30 seconds.

**Not protected**
- Anyone who can use your unlocked Windows/macOS account can open Hushpad without the passphrase (the key is cached for that account). Use Hushpad's lock (Ctrl+L / auto-lock) and lock your computer.
- Malware running as you (keyloggers, memory readers, screen readers that don't respect capture exclusion) can see what you see and type.
- Text you paste elsewhere leaves Hushpad's protection. Files you export are plain, unencrypted files.
- A weak passphrase can be guessed offline by anyone who gets `vault.json` and the note files. Use a long passphrase (minimum 8 characters, longer is better).
- If you forget the passphrase, nobody — including the developers — can recover the notes.
- The builds are not code-signed or notarized yet. Download only from https://github.com/wind2sp/hushpad/releases or https://gdra.mycafe24.com/hushpad/ and compare the SHA-256 shown there.

## Supported versions

Security fixes go into the latest release.
