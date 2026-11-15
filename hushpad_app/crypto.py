"""암호화.

- 메모 파일: AES-256-GCM (zlib 압축 후 암호화). 열쇠(데이터 키)는 무작위 32바이트.
- 데이터 키는 사용자 암호로 만든 열쇠(scrypt)로 감싸서 데이터 폴더의 vault.json에 둔다.
  → 같은 데이터 폴더(예: Dropbox)를 쓰는 다른 PC에서도 같은 암호로 열 수 있다.
- 이 PC에서는 데이터 키를 Windows DPAPI(현재 Windows 사용자 전용) 또는 macOS 키체인에 기억해 두므로
  매번 암호를 묻지 않는다 (plat 모듈). 다른 계정·다른 PC는 이 키를 풀 수 없다.
"""
from __future__ import annotations

import base64
import json
import os
import re
import uuid
import zlib
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

MAGIC = b"OWN1"
VAULT_FILE = "vault.json"


class BadPassphrase(Exception):
    pass


class DecryptError(Exception):
    pass


# ---------------------------------------------------------------- AES-GCM
def seal(key: bytes, data: bytes, aad: bytes = b"note") -> bytes:
    nonce = os.urandom(12)
    return MAGIC + nonce + AESGCM(key).encrypt(nonce, zlib.compress(data, 6), aad)


def unseal(key: bytes, blob: bytes, aad: bytes = b"note") -> bytes:
    if blob[:4] != MAGIC or len(blob) < 4 + 12 + 16:
        raise DecryptError("형식이 다른 파일")
    try:
        return zlib.decompress(AESGCM(key).decrypt(blob[4:16], blob[16:], aad))
    except (InvalidTag, zlib.error) as e:
        raise DecryptError("복호화 실패") from e


# ---------------------------------------------------------------- 금고(vault)
def _b64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


def _unb64(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))


def _kek(passphrase: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return Scrypt(salt=salt, length=32, n=n, r=r, p=p).derive(passphrase.encode("utf-8"))


def vault_path(folder: Path) -> Path:
    return Path(folder) / VAULT_FILE


def vault_exists(folder: Path) -> bool:
    return vault_path(folder).is_file()


_VID = re.compile(r"^[0-9a-f]{32}$")


def vault_id(folder: Path) -> str:
    vid = json.loads(vault_path(folder).read_text("utf-8"))["vault_id"]
    if not isinstance(vid, str) or not _VID.match(vid):   # 키 저장소 명령에 들어가므로 형식을 엄격히
        raise ValueError("invalid vault_id")
    return vid


def _check_kdf(k: dict) -> None:
    """공유 폴더의 vault.json을 믿지 않고 범위를 확인 (지나치게 크거나 약한 값 거부)."""
    n, r, p = int(k["n"]), int(k["r"]), int(k["p"])
    if not (2 ** 14 <= n <= 2 ** 22 and n & (n - 1) == 0 and 1 <= r <= 32 and 1 <= p <= 16):
        raise ValueError("unsupported KDF parameters")


def _write_vault(folder: Path, vid: str, key: bytes, passphrase: str) -> None:
    salt = os.urandom(16)
    n, r, p = 2 ** 16, 8, 1
    kek = _kek(passphrase, salt, n, r, p)
    doc = {
        "app": "Hushpad", "v": 1, "vault_id": vid,
        "kdf": {"name": "scrypt", "n": n, "r": r, "p": p, "salt": _b64(salt)},
        "wrapped_key": _b64(seal(kek, key, b"vault")),
    }
    Path(folder).mkdir(parents=True, exist_ok=True)
    tmp = vault_path(folder).with_name(".~vault.tmp")
    tmp.write_text(json.dumps(doc, indent=1), "utf-8")
    os.replace(tmp, vault_path(folder))


def create_vault(folder: Path, passphrase: str) -> bytes:
    key = os.urandom(32)
    _write_vault(folder, uuid.uuid4().hex, key, passphrase)
    return key


def unlock_vault(folder: Path, passphrase: str) -> bytes:
    doc = json.loads(vault_path(folder).read_text("utf-8"))
    k = doc["kdf"]
    _check_kdf(k)
    kek = _kek(passphrase, _unb64(k["salt"]), int(k["n"]), int(k["r"]), int(k["p"]))
    try:
        return unseal(kek, _unb64(doc["wrapped_key"]), b"vault")
    except DecryptError as e:
        raise BadPassphrase() from e


def change_passphrase(folder: Path, key: bytes, new_passphrase: str) -> None:
    _write_vault(folder, vault_id(folder), key, new_passphrase)


# ---------------------------------------------------------------- 이 PC에 키 기억
# Windows: DPAPI로 감싸 %LOCALAPPDATA%\Hushpad\keys.json / macOS: 로그인 키체인 / 그 밖: 기억하지 않음
def remember_key(vid: str, key: bytes) -> None:
    from . import plat
    plat.key_remember(vid, key)


def recall_key(vid: str) -> bytes | None:
    from . import plat
    try:
        return plat.key_recall(vid)
    except Exception:
        return None


def forget_key(vid: str) -> None:
    from . import plat
    plat.key_forget(vid)
