from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .database import engine, get_db
from .models import Base, UserDB
from .schemas import UserCreate, UserRead

app = FastAPI()
Base.metadata.create_all(bind=engine)

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Users ----------
@app.post("/api/users", response_model=UserRead, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.execute(
        select(UserDB).where(UserDB.email == payload.email)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="User already exists")
    user = UserDB(**payload.model_dump())
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    return user


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


# DELETE → cascades deletes bookings for that user
@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)