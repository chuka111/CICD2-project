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

@app.get("/health")
def health():
    return {"status": "ok"}

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



# ---------- Bookings ----------
@app.post("/api/bookings", response_model=BookingRead, status_code=201)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)):
    user = db.get(UserDB, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    course = db.get(CourseDB, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    booking = BookingDB(**payload.model_dump())
    db.add(booking)
    commit_or_rollback(db, "Booking already exists")
    db.refresh(booking)
    return booking


@app.get("/api/bookings", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_db)):
    stmt = select(BookingDB).order_by(BookingDB.id)
    return db.execute(stmt).scalars().all()


@app.get("/api/bookings/{booking_id}", response_model=BookingReadWithCourse)
def get_booking_with_course(booking_id: int, db: Session = Depends(get_db)):
    stmt = (
        select(BookingDB)
        .where(BookingDB.id == booking_id)
        .options(selectinload(BookingDB.course))
    )
    booking = db.execute(stmt).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking



# ---------- Nested Routes ----------
@app.get("/api/users/{user_id}/bookings", response_model=list[BookingRead])
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    stmt = select(BookingDB).where(BookingDB.user_id == user_id)
    result = db.execute(stmt)
    rows = result.scalars().all()
    return rows


@app.post("/api/users/{user_id}/bookings", response_model=BookingRead, status_code=201)
def create_user_booking(user_id: int, payload: BookingCreateForUser, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    course = db.get(CourseDB, payload.course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    booking = BookingDB(
        user_id=user_id,
        course_id=payload.course_id
    )
    db.add(booking)
    commit_or_rollback(db, "Booking creation failed")
    db.refresh(booking)
    return booking



# ---------- Users ----------
@app.get("/api/users", response_model=list[UserRead])
def list_users(db: Session = Depends(get_db)):
    stmt = select(UserDB).order_by(UserDB.id)
    result = db.execute(stmt)
    users = result.scalars().all()
    return users


@app.get("/api/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/api/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def add_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = UserDB(
        name=payload.name,
        username=payload.username,
        email=payload.email,
        age=payload.age,
        password_hash=payload.password
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="User already exists")
    return user


# DELETE → cascades deletes bookings for that user
@app.delete("/api/users/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(UserDB, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)