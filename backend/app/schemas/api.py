from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator

class LoginRequest(BaseModel):
    user_id: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class StudentCreate(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str
    department: str
    semester: int = Field(ge=1)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

class FacultyCreate(BaseModel):
    id: str
    name: str
    department: str
    subject: str = ""
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value

class CourseCreate(BaseModel):
    code: str
    name: str
    faculty: str | None = None
    department: str
    semester: int = 1

class AttendanceItem(BaseModel):
    student_id: str
    status: str

class AttendanceRequest(BaseModel):
    course_code: str
    date: date
    records: list[AttendanceItem]

class ResultItem(BaseModel):
    student_id: str
    marks: float = Field(ge=0, le=100)

class ResultRequest(BaseModel):
    course_code: str
    results: list[ResultItem]
