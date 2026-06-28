"""
Authentication routes — registration, login, and "who am I".

What it does:
- POST /auth/register — create an account (hashes password), return a JWT
- POST /auth/login    — verify email+password, return a JWT
- GET  /auth/me       — return the current authenticated user's profile

Upstream (who imports this): main.py mounts router under /api/v1, so the
public paths are /api/v1/auth/*. Frontend lib/api.ts hits these to obtain
the bearer token it stores for subsequent calls.
Downstream (what this imports): db.session.get_db + db.models.User for
persistence, core.security for hashing/JWT, api.deps.get_current_user for
the /me guard.
"""
from __future__ import annotations

# APIRouter: groups /auth/* routes; Depends: DI for DB + current user; HTTPException+status: typed 4xx errors
from fastapi import APIRouter, Depends, HTTPException, status
# BaseModel: declares request/response payload schemas with automatic validation
from pydantic import BaseModel
# Session: type hint for the SQLAlchemy session resolved via Depends(get_db)
from sqlalchemy.orm import Session

# get_db: request-scoped DB session used to query/insert User rows
from app.db.session import get_db
# User: ORM model written on /register and read on /login + /me
from app.db.models import User
# Password + JWT helpers: bcrypt hash/verify for storage, JWT mint on successful auth
from app.core.security import hash_password, verify_password, create_access_token
# get_current_user: protects /me by resolving the User from the Bearer token
from app.api.deps import get_current_user
# get_logger: structured logging for register/login events
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new account and return a JWT."""
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user = User(email=request.email, password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(f"Registered new user: {user.email}")
    return TokenResponse(access_token=create_access_token(subject=user.id))


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Verify credentials and return a JWT."""
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    logger.info(f"User logged in: {user.email}")
    return TokenResponse(access_token=create_access_token(subject=user.id))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user."""
    return UserResponse(id=current_user.id, email=current_user.email)
