"""Auth router: POST /api/auth/register, POST /api/auth/login, GET /api/auth/me.

Issues a JWT bearer token on login/register. The frontend stores this token
and sends it as `Authorization: Bearer <token>` on subsequent requests.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.schemas import RegisterIn, LoginIn, TokenOut, UserOut

logger = logging.getLogger("resq-ai.auth")
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=201)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = models.User(
        name=payload.name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info("New user registered: %s (%s)", user.email, user.role)
    token = create_access_token(user)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    logger.info("User logged in: %s (%s)", user.email, user.role)
    token = create_access_token(user)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
