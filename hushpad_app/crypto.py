"""암호화.

- 메모 파일: AES-256-GCM (zlib 압축 후 암호화). 열쇠(데이터 키)는 무작위 32바이트.
- 데이터 키는 사용자 암호로 만든 열쇠(scrypt)로 감싸서 데이터 폴더의 vault.json에 둔다.
  → 같은 데이터 폴더(예: Dropbox)를 쓰는 다른 PC에서도 같은 암호로 열 수 있다.
- 이 PC에서는 데이터 키를 Windows DPAPI(현재 Windows 사용자 전용)로 감싸 로컬에 기억해 두므로
  매번 암호를 묻지 않는다. 다른 Windows 계정·다른 PC·다른 프로그램은 이 키를 풀 수 없다.
"""
from __future__ import annotations

import base64
import ctypes
import json
import os
import uuid
import zlib
from ctypes import wintypes
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


# ---------------------------------------------------------------- DPAPI
class _BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


_crypt32 = ctypes.windll.crypt32
_kernel32 = ctypes.windll.kernel32
_crypt32.CryptProtectData.argtypes = [ctypes.POINTER(_BLOB), wintypes.LPCWSTR, ctypes.POINTER(_BLOB),
                                      ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_BLOB)]
_crypt32.CryptProtectData.restype = wintypes.BOOL
_crypt32.CryptUnprotectData.argtypes = [ctypes.POINTER(_BLOB), ctypes.c_void_p, ctypes.POINTER(_BLOB),
                                        ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(_BLOB)]
_crypt32.CryptUnprotectData.restype = wintypes.BOOL
_kernel32.LocalFree.argtypes = [ctypes.c_void_p]
_kernel32.LocalFree.restype = ctypes.c_void_p
_ENTROPY = b"Hushpad-local-key-v1"


def _blob(data: bytes):
    buf = (ctypes.c_ubyte * max(1, len(data))).from_buffer_copy(data or b"\0")
    return _BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte))), buf


def _dpapi(data: bytes, protect: bool) -> bytes:
    src, b1 = _blob(data)
    ent, b2 = _blob(_ENTROPY)
    out = _BLOB()
    if protect:
        ok = _crypt32.CryptProtectData(ctypes.byref(src), "Hushpad", ctypes.byref(ent), None, None, 1,
                                       ctypes.byref(out))
    else:
        ok = _crypt32.CryptUnprotectData(ctypes.byref(src), None, ctypes.byref(ent), None, None, 1,
                                         ctypes.byref(out))
    if not ok:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(out.pbData, out.cbData)
    finally:
        _kernel32.LocalFree(ctypes.cast(out.pbData, ctypes.c_void_p))


def dpapi_protect(data: bytes) -> bytes:
    return _dpapi(data, True)


def dpapi_unprotect(data: bytes) -> bytes:
    return _dpapi(data, False)


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


def vault_id(folder: Path) -> str:
    return json.loads(vault_path(folder).read_text("utf-8"))["vault_id"]


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
    kek = _kek(passphrase, _unb64(k["salt"]), k["n"], k["r"], k["p"])
    try:
        return unseal(kek, _unb64(doc["wrapped_key"]), b"vault")
    except DecryptError as e:
        raise BadPassphrase() from e


def change_passphrase(folder: Path, key: bytes, new_passphrase: str) -> None:
    _write_vault(folder, vault_id(folder), key, new_passphrase)


# ---------------------------------------------------------------- 이 PC에 키 기억
def _local_keys_file() -> Path:
    if os.environ.get("HUSHPAD_PROFILE"):
        return Path(os.environ["HUSHPAD_PROFILE"]) / "local" / "keys.json"
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Hushpad" / "keys.json"


def remember_key(vid: str, key: bytes) -> None:
    f = _local_keys_file()
    f.parent.mkdir(parents=True, exist_ok=True)
    try:
        doc = json.loads(f.read_text("utf-8"))
    except Exception:
        doc = {}
    doc[vid] = _b64(dpapi_protect(key))
    f.write_text(json.dumps(doc), "utf-8")


def recall_key(vid: str) -> bytes | None:
    try:
        doc = json.loads(_local_keys_file().read_text("utf-8"))
        return dpapi_unprotect(_unb64(doc[vid]))
    except Exception:
        return None


def forget_key(vid: str) -> None:
    f = _local_keys_file()
    try:
        doc = json.loads(f.read_text("utf-8"))
        doc.pop(vid, None)
        f.write_text(json.dumps(doc), "utf-8")
    except Exception:
        pass
