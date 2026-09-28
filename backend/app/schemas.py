from datetime import date
from pydantic import BaseModel, EmailStr, Field

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
    password: str = "student123"

class FacultyCreate(BaseModel):
    id: str
    name: str
    department: str
    subject: str = ""
    email: EmailStr
    password: str = "faculty123"

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
