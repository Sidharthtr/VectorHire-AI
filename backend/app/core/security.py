"""
JWT + bcrypt helpers — the only place auth crypto lives.

What it does:
- hash_password / verify_password wrap bcrypt for the User.password_hash column.
- create_access_token issues a signed JWT with `sub` = user_id and an expiry.
- decode_token validates a token and returns the user_id (or None on failure).

Upstream (who imports this): app.api.deps (get_current_user dependency),
app.api.routes.auth_routes (signup / login endpoints).
Downstream (what this imports): python-jose (JWT encode/decode), passlib (bcrypt),
datetime for expiry math, app.core.settings for secret + algorithm + TTL.
"""
from __future__ import annotations

# datetime/timedelta: compute the `exp` claim relative to utcnow()
from datetime import datetime, timedelta
# Optional: decode_token returns Optional[str] — None signals invalid/expired
from typing import Optional

# jose: JWT encode/decode; JWTError is the catch-all for bad signature / expired token
from jose import JWTError, jwt
# CryptContext: passlib helper that picks bcrypt and handles hash migration ("deprecated=auto")
from passlib.context import CryptContext

# get_settings: pulls jwt_secret_key / jwt_algorithm / jwt_expire_minutes from .env
from app.core.settings import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    return _pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)


def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    settings = get_settings()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> Optional[str]:
    """Return the subject (user id) if the token is valid, else None."""
    settings = get_settings()
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload.get("sub")
    except JWTError:
        return None
