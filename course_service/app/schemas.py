# app/schemas.py
from typing import Annotated, Optional, List
from annotated_types import Ge, Le
from pydantic import BaseModel, EmailStr, ConfigDict, StringConstraints


# ---------- Reusable type aliases ----------
CodeStr = Annotated[str, StringConstraints(min_length=1, max_length=32)]
CourseNameStr = Annotated[str, StringConstraints(min_length=1, max_length=255)]

# ---------- Courses ----------
class CourseCreate(BaseModel):
    code: CodeStr
    name: CourseNameStr

class CourseRead(CourseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int