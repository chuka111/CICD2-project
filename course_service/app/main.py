from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError


from .database import engine, SessionLocal
from .models import Base, UserDB, CourseDB, BookingDB
from .schemas import (
    UserCreate, UserRead, UserLogin, UserReadWithBookings,
    CourseCreate, CourseRead, CourseReadWithBookings,
    BookingCreate, BookingRead, BookingCreateForUser, BookingReadWithCourse
)

app = FastAPI()
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def commit_or_rollback(db: Session, error_msg: str):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail=error_msg)

# ---------- Courses ----------
@app.post("/api/courses", response_model=CourseRead, status_code=201)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    db_course = CourseDB(**course.model_dump())
    db.add(db_course)
    commit_or_rollback(db, "Course already exists")
    db.refresh(db_course)
    return db_course

@app.get("/api/courses", response_model=list[CourseRead])
def list_courses(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    stmt = select(CourseDB).order_by(CourseDB.id).limit(limit).offset(offset)
    result = db.execute(stmt)
    rows = result.scalars().all()
    return rows

@app.get("/api/courses/{course_id}", response_model=CourseRead)
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.get(CourseDB, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course