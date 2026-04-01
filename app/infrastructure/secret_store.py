from __future__ import annotations

import base64
import hashlib
import os


def _key_material() -> bytes:
    raw = os.getenv("CS2_SECRET_KEY") or os.getenv("FLASK_SECRET_KEY") or "cs2tracker_dev_secret_change_me"
    return hashlib.sha256(raw.encode("utf-8")).digest()


def _stream_xor(data: bytes, key: bytes, nonce: bytes) -> bytes:
    out = bytearray(len(data))
    counter = 0
    offset = 0
    while offset < len(data):
        block = hashlib.sha256(key + nonce + counter.to_bytes(8, "big")).digest()
        take = min(len(block), len(data) - offset)
        for idx in range(take):
            out[offset + idx] = data[offset + idx] ^ block[idx]
        offset += take
        counter += 1
    return bytes(out)


def encrypt_secret(plain: str) -> tuple[str, str]:
    key = _key_material()
    nonce = os.urandom(16)
    cipher = _stream_xor(plain.encode("utf-8"), key, nonce)
    return base64.b64encode(cipher).decode("ascii"), base64.b64encode(nonce).decode("ascii")


def decrypt_secret(ciphertext_b64: str, nonce_b64: str) -> str | None:
    try:
        key = _key_material()
        nonce = base64.b64decode(nonce_b64)
        cipher = base64.b64decode(ciphertext_b64)
        plain = _stream_xor(cipher, key, nonce)
        return plain.decode("utf-8")
    except Exception:
        return None
