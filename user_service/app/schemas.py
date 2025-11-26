# app/schemas.py
from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints


# ---------- Reusable type aliases ----------
NameStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
AgeInt = Annotated[int, Ge(18), Le(120)]

# ---------- Users ----------
class UserCreate(BaseModel):
    name: NameStr
    email: EmailStr
    age: AgeInt

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int

