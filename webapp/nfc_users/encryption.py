"""
Field-level encryption for sensitive data at rest.

- AES-256-GCM (authenticated encryption) is used for Patient and new data.
  Key: 32-byte SHA-256(SECRET_KEY). Stored format: base64(nonce || tag || ciphertext).
- Fernet (AES-128-CBC + HMAC-SHA256) remains for UserProfile backward compatibility.
Key material is derived from Django SECRET_KEY; do not commit production SECRET_KEY.
"""
import base64
import hashlib
import json
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from django.conf import settings

# ---- AES-256-GCM (industry-standard AEAD for Patient and new data) ----

def _get_aes256_key() -> bytes:
    """Derive a 256-bit key from SECRET_KEY."""
    key = settings.SECRET_KEY.encode("utf-8")
    return hashlib.sha256(key).digest()


def encrypt_value(plain: str) -> str:
    """Encrypt a string with AES-256-GCM. Returns base64(nonce || ciphertext_with_tag)."""
    if not plain:
        return ""
    key = _get_aes256_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ct = aesgcm.encrypt(nonce, plain.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ct).decode("ascii")


def decrypt_value(cipher: str) -> str:
    """Decrypt a string encrypted with encrypt_value (AES-256-GCM)."""
    if not cipher:
        return ""
    key = _get_aes256_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(cipher.encode("ascii"))
    nonce, ct_and_tag = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ct_and_tag, None).decode("utf-8")


def encrypt_json(data: dict | list) -> str:
    """Encrypt a dict or list as JSON with AES-256-GCM."""
    if not data:
        return encrypt_value("{}")
    return encrypt_value(json.dumps(data, ensure_ascii=False))


def decrypt_json(cipher: str) -> dict | list:
    """Decrypt and parse JSON (dict or list)."""
    if not cipher:
        return {} if isinstance(cipher, str) else []
    plain = decrypt_value(cipher)
    if not plain or plain == "{}":
        return {}
    try:
        out = json.loads(plain)
        return out if isinstance(out, (dict, list)) else {}
    except json.JSONDecodeError:
        return {}


# ---- Fernet (for UserProfile backward compatibility) ----

def get_fernet():
    """Build a Fernet instance from Django SECRET_KEY (UserProfile only)."""
    key = settings.SECRET_KEY.encode("utf-8")
    digest = hashlib.sha256(key).digest()
    b64 = base64.urlsafe_b64encode(digest[:32])
    return Fernet(b64)


def decrypt_value_fernet(cipher: str) -> str:
    """Decrypt legacy Fernet ciphertext (UserProfile)."""
    if not cipher:
        return ""
    f = get_fernet()
    return f.decrypt(cipher.encode("ascii")).decode("utf-8")


def encrypt_value_fernet(plain: str) -> str:
    """Encrypt with Fernet (UserProfile legacy)."""
    if not plain:
        return ""
    f = get_fernet()
    return f.encrypt(plain.encode("utf-8")).decode("ascii")
