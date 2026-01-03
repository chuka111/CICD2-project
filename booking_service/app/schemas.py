from typing import Annotated
from annotated_types import Ge
from pydantic import BaseModel, ConfigDict


# ---------- Reusable types ----------
IdInt = Annotated[int, Ge(1)]


# ---------- Bookings ----------
class BookingCreate(BaseModel):
    user_id: IdInt
    course_id: IdInt


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    course_id: int
    status: str
    created_at: str
