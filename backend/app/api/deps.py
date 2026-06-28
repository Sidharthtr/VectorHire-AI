"""
FastAPI auth dependency — resolves the current User from a JWT bearer token.

What it does:
- Exposes get_current_user() to be used via Depends() in protected routes
- Decodes the Bearer JWT, looks up the User row, raises 401 on any failure
- Defines the OAuth2 scheme that points Swagger UI at /api/v1/auth/login

Upstream (who imports this): auth_routes.py (/auth/me), resume_routes.py
(upload + analyze), analysis_routes.py (history, chat) — every protected
endpoint pulls get_current_user from here.
Downstream (what this imports): db.session.get_db (request-scoped Session),
db.models.User (ORM row), core.security.decode_token (JWT verification).
"""
# Depends: marks a parameter as DI-resolved; HTTPException + status: raise typed 401s
from fastapi import Depends, HTTPException, status
# OAuth2PasswordBearer: extracts the "Authorization: Bearer <token>" header and tells Swagger UI which URL to use for login
from fastapi.security import OAuth2PasswordBearer
# Session: type hint for the SQLAlchemy session injected via Depends(get_db)
from sqlalchemy.orm import Session

# get_db: yields a request-scoped DB session so we can look up the user row
from app.db.session import get_db
# User: the ORM model we return after a successful token check
from app.db.models import User
# decode_token: verifies the JWT signature/exp and returns the user_id subject (or None)
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

_401 = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid or expired token",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = decode_token(token)
    if not user_id:
        raise _401
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise _401
    return user
