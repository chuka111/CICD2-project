import os
import time
import httpx

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from passlib.context import CryptContext
from jose import jwt

from .database import engine, get_db
from .models import Base, UserDB
from .schemas import UserRead, UserRegister, UserLogin, TokenRead


app = FastAPI(title="User Service")
Base.metadata.create_all(bind=engine)


BOOKING_SERVICE_BASE = os.getenv("BOOKING_SERVICE_BASE", "http://booking_service:8000")

JWT_SECRET = os.getenv("JWT_SECRET", "dev_secret_change_me")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)


def make_token(user_id, email):
    now = int(time.time())
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + (JWT_EXPIRE_MINUTES * 60),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Auth ----------
@app.post("/api/auth/register", response_model=UserRead, status_code=201)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing_email = db.execute(
        select(UserDB).where(UserDB.email == payload.email)
    ).scalar_one_or_none()

    if existing_email:
        raise HTTPException(status_code=409, detail="Email already in use")

    user = UserDB(
        name=payload.name,
        email=payload.email,
        password_hash=pwd_context.hash(payload.password),
    )

    db.add(user)
    commit_or_rollback(db, "User already exists")
    db.refresh(user)
    return user


@app.post("/api/auth/login", response_model=TokenRead)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.execute(
        select(UserDB).where(UserDB.email == payload.email)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = make_token(user.id, user.email)
    return {"access_token": token, "token_type": "bearer"}


# ---------- Users ----------
@app.get("/api/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/api/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    stmt = select(UserDB).order_by(UserDB.id)
    rows = db.execute(stmt).scalars().all()
    return rows


@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/users/{user_id}/bookings")
def get_user_bookings(user_id: int):
    url = f"{BOOKING_SERVICE_BASE}/api/bookings?user_id={user_id}"

    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Booking Service unavailable")

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="Booking Service error")

    return r.json()
