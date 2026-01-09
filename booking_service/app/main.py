import aio_pika
import asyncio
import json
import httpx, os
import time
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .database import engine, get_db
from .models import Base, BookingDB
from .schemas import BookingCreate, BookingRead


app = FastAPI(title="Booking Service")
Base.metadata.create_all(bind=engine)


# ---------- Service URLs ----------
USER_SERVICE_BASE = os.getenv("USER_SERVICE_BASE", "http://user_service:8000")
COURSE_SERVICE_BASE = os.getenv("COURSE_SERVICE_BASE", "http://course_service:8000")

# ---------- RabbitMQ ----------
RABBIT_URL = os.getenv("RABBIT_URL")
BOOKING_QUEUE = os.getenv("BOOKING_QUEUE", "bookings_queue")



# ---------- Circuit Breaker ----------
class CircuitBreaker:
    def __init__(self, failure_threshold=3, reset_timeout=20):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failure_count = 0
        self.opened_at = None

    def is_open(self):
        if self.opened_at is None:
            return False

        if time.time() - self.opened_at >= self.reset_timeout:
            self.failure_count = 0
            self.opened_at = None
            return False

        return True

    def record_success(self):
        self.failure_count = 0
        self.opened_at = None

    def record_failure(self):
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.opened_at = time.time()


course_cb = CircuitBreaker()


# ---------- Helper functions ----------
def fetch_user(user_id):
    url = f"{USER_SERVICE_BASE}/api/users/{user_id}"

    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="User Service unavailable")

    if r.status_code == 404:
        raise HTTPException(status_code=404, detail="User not found")

    if r.status_code >= 400:
        raise HTTPException(status_code=502, detail="User Service error")

    return r.json()


def fetch_course(course_id):
    if course_cb.is_open():
        raise HTTPException(status_code=503, detail="Course Service unavailable")

    url = f"{COURSE_SERVICE_BASE}/api/courses/{course_id}"

    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(url)
    except httpx.RequestError:
        course_cb.record_failure()
        raise HTTPException(status_code=503, detail="Course Service unavailable")

    if r.status_code == 404:
        course_cb.record_success()
        raise HTTPException(status_code=404, detail="Course not found")

    if r.status_code >= 400:
        course_cb.record_failure()
        raise HTTPException(status_code=503, detail="Course Service unavailable")

    course_cb.record_success()
    return r.json()


# ---------- RabbitMQ publisher ----------
async def publish_booking(payload):
    connection = await aio_pika.connect_robust(RABBIT_URL)
    channel = await connection.channel()

    message = aio_pika.Message(
        body=json.dumps(payload).encode("utf-8")
    )

    await channel.default_exchange.publish(
        message,
        routing_key=BOOKING_QUEUE
    )

    await connection.close()


def notify_booking_confirmed(booking_id, user_id, course_id):
    if not RABBIT_URL:
        return

    payload = {
        "booking_id": booking_id,
        "user_id": user_id,
        "course_id": course_id,
        "status": "confirmed"
    }

    try:
        asyncio.run(publish_booking(payload))
    except Exception:
        return


# ---------- Bookings ----------
@app.post("/api/bookings", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    fetch_user(payload.user_id)
    fetch_course(payload.course_id)

    booking = BookingDB(
        user_id=payload.user_id,
        course_id=payload.course_id,
        status="confirmed"
    )

    db.add(booking)
    try:
        db.commit()
        db.refresh(booking)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Booking already exists")

    background_tasks.add_task(
        notify_booking_confirmed,
        booking.id,
        booking.user_id,
        booking.course_id
    )

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "course_id": booking.course_id,
        "status": booking.status,
        "created_at": booking.created_at.isoformat()
    }


@app.get("/api/bookings", response_model=list[BookingRead])
def list_bookings(db: Session = Depends(get_db)):
    stmt = select(BookingDB).order_by(BookingDB.id)
    rows = db.execute(stmt).scalars().all()

    return [
        {
            "id": b.id,
            "user_id": b.user_id,
            "course_id": b.course_id,
            "status": b.status,
            "created_at": b.created_at.isoformat()
        }
        for b in rows
    ]


@app.get("/api/bookings/{booking_id}", response_model=BookingRead)
def get_booking(booking_id: int, db: Session = Depends(get_db)):
    booking = db.get(BookingDB, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "course_id": booking.course_id,
        "status": booking.status,
        "created_at": booking.created_at.isoformat()
    }