import httpx, os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import engine, get_db
from .models import Base, CourseDB
from .schemas import CourseCreate, CourseRead

app = FastAPI()
Base.metadata.create_all(bind=engine)

BOOKING_SERVICE_BASE = os.getenv("BOOKING_SERVICE_BASE", "http://booking_service:8000")

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

# ---------- Courses ----------
@app.post("/api/courses", response_model=CourseRead, status_code=201)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    exists = db.execute(
        select(CourseDB).where(CourseDB.code == course.code)).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=409, detail="Course already exists")
    new_course = CourseDB(**course.model_dump())
    db.add(new_course)
    try:
        db.commit()
        db.refresh(new_course)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Course already exists")
    return new_course

@app.get("/api/courses", response_model=list[CourseRead])
def list_courses(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(CourseDB).order_by(CourseDB.id)
    rows = db.execute(stmt).scalars().all()
    return rows

@app.get("/api/courses/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@app.get("/api/courses/{course_id}/bookings")
def get_course_bookings(course_id: int):
    url = f"{BOOKING_SERVICE_BASE}/api/bookings?course_id={course_id}"

    with httpx.Client(timeout=5.0) as client:
        r = client.get(url)

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="Booking Service error")

    return r.json()
