"""Password hashing and access-token helpers."""
import hashlib
import hmac
import secrets
import time

import jwt
from jwt import PyJWTError

from .config import settings

JWT_ISSUER = "bioworkspace"


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    n, r, p = 2**14, 8, 1
    digest = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=n, r=r, p=p, dklen=32)
    return f"scrypt${n}${r}${p}${salt.hex()}${digest.hex()}"


def verify_password(password: str, password_hash: str | None) -> bool:
    if not password_hash:
        return False
    try:
        algorithm, n, r, p, salt_hex, expected_hex = password_hash.split("$", 5)
        if algorithm != "scrypt" or (int(n), int(r), int(p)) != (2**14, 8, 1):
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=int(n), r=int(r), p=int(p), dklen=len(expected),
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, OverflowError):
        return False


def create_access_token(user_id: int) -> str:
    now = int(time.time())
    return jwt.encode(
        {"iss": JWT_ISSUER, "aud": JWT_ISSUER, "sub": str(user_id), "iat": now, "exp": now + settings.jwt_expiry_minutes * 60},
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_access_token(token: str) -> dict | None:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=JWT_ISSUER,
            audience=JWT_ISSUER,
            options={"require": ["iss", "aud", "sub", "iat", "exp"]},
        )
        if not claims["sub"].isdigit():
            return None
        return claims
    except (PyJWTError, KeyError, TypeError, ValueError):
        return None
