"""
Simple JWT issue/verify for doctor login. Uses SECRET_KEY.
"""
import time
from django.conf import settings
import jwt

JWT_ALGORITHM = "HS256"
ACCESS_EXPIRY_SECONDS = 60 * 60 * 24  # 24 hours


def make_access_token(user_id: int, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + ACCESS_EXPIRY_SECONDS,
        "iat": int(time.time()),
        "type": "access",
    }
    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[JWT_ALGORITHM],
        )
    except jwt.InvalidTokenError:
        return None
