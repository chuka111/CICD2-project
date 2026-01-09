# app/schemas.py
from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints


# ---------- Reusable type aliases ----------
NameStr = Annotated[str, StringConstraints(min_length=1, max_length=100)]
AgeInt = Annotated[int, Ge(18), Le(120)]
UsernameStr = Annotated[str, StringConstraints(min_length=3, max_length=50)]
PasswordStr = Annotated[str, StringConstraints(min_length=6, max_length=255)]

# ---------- Users ----------

class UserRegister(BaseModel):
    name: NameStr
    email: EmailStr
    username: UsernameStr
    password: PasswordStr

class UserLogin(BaseModel):
    username: UsernameStr
    password: PasswordStr

class TokenRead(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: NameStr
    email: EmailStr
    username: UsernameStr

