"""
Field-level encryption for sensitive user data using Fernet (symmetric encryption).
Key is derived from Django SECRET_KEY so no separate key file is required.
"""
import base64
import hashlib
import json
from cryptography.fernet import Fernet

from django.conf import settings


def get_fernet():
    """Build a Fernet instance from Django SECRET_KEY."""
    key = settings.SECRET_KEY.encode("utf-8")
    digest = hashlib.sha256(key).digest()
    b64 = base64.urlsafe_b64encode(digest[:32])
    return Fernet(b64)


def encrypt_value(plain: str) -> str:
    if not plain:
        return ""
    f = get_fernet()
    return f.encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_value(cipher: str) -> str:
    if not cipher:
        return ""
    f = get_fernet()
    return f.decrypt(cipher.encode("ascii")).decode("utf-8")


def encrypt_json(data: dict) -> str:
    if not data:
        return encrypt_value("{}")
    return encrypt_value(json.dumps(data, ensure_ascii=False))


def decrypt_json(cipher: str) -> dict:
    if not cipher:
        return {}
    plain = decrypt_value(cipher)
    if not plain or plain == "{}":
        return {}
    return json.loads(plain)
