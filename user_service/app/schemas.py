# app/schemas.py
from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints


# ---------- Reusable type aliases ----------
NameStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
UsernameStr = Annotated[str, StringConstraints(min_length=3, max_length=50)]
PasswordStr = Annotated[str, StringConstraints(min_length=6, max_length=255)]
CodeStr = Annotated[str, StringConstraints(min_length=1, max_length=32)]
CourseNameStr = Annotated[str, StringConstraints(min_length=1, max_length=255)]
DescStr = Annotated[str, StringConstraints(min_length=0, max_length=2000)]
AgeInt = Annotated[int, Ge(18), Le(120)]
CreditsInt = Annotated[int, Ge(1), Le(120)]

# ---------- Users ----------
class UserCreate(BaseModel):
    name: NameStr
    username: UsernameStr
    email: EmailStr
    age: AgeInt
    password: PasswordStr      # Plain password (will be hashed)

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: NameStr
    username: UsernameStr
    email: EmailStr
    age: AgeInt

class UserLogin(BaseModel):
    username: UsernameStr
    password: PasswordStr

# ---------- Bookings ----------
class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    course_id: int

class BookingCreate(BaseModel):
    user_id: int
    course_id: int

class BookingCreateForUser(BaseModel):
    course_id: int

class BookingReadWithCourse(BookingRead):
    course: Optional["CourseRead"] = None

class UserReadWithBookings(UserRead):
    bookings: List[BookingRead] = []

# ---------- Courses ----------
class CourseCreate(BaseModel):
    code: CodeStr
    name: CourseNameStr

class CourseRead(CourseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int

class CourseReadWithBookings(CourseRead):
    bookings: List[BookingRead] = []