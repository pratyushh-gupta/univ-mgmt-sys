from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    user_id: str
    password: str


class AdminUserCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=12, max_length=72)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class DepartmentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=20)
    description: str | None = None


class AcademicYearCreate(BaseModel):
    name: str = Field(min_length=4, max_length=30)
    start_date: date
    end_date: date
    is_active: bool = False


class SemesterCreate(BaseModel):
    academic_year_id: int
    name: str = Field(min_length=1, max_length=40)
    number: int = Field(gt=0)
    start_date: date
    end_date: date
    is_active: bool = False


class StudentCreate(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    department_id: int
    semester_id: int | None = None
    admission_year: int = Field(ge=1900, le=2200)
    enrollment_number: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class StudentUpdate(BaseModel):
    department_id: int | None = None
    semester_id: int | None = None
    admission_year: int | None = Field(default=None, ge=1900, le=2200)
    phone: str | None = Field(default=None, max_length=32)
    address: str | None = None
    is_active: bool | None = None


class AdmissionCreate(BaseModel):
    applicant_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=32)
    date_of_birth: date | None = None
    address: str | None = None
    department_id: int
    academic_year_id: int
    intended_program: str = Field(min_length=1, max_length=160)


class AdmissionReview(BaseModel):
    status: str
    rejection_reason: str | None = None
    user_id: str | None = Field(default=None, min_length=1, max_length=50)
    initial_password: str | None = Field(default=None, min_length=12, max_length=72)
    enrollment_number: str | None = Field(default=None, min_length=1, max_length=50)
    semester_id: int | None = None


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    credits: int | None = Field(default=None, gt=0)
    department_id: int | None = None
    is_active: bool | None = None


class OfferingUpdate(BaseModel):
    faculty_id: int | None = None
    semester_id: int | None = None
    section: str | None = Field(default=None, min_length=1, max_length=20)
    capacity: int | None = Field(default=None, gt=0)
    room: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None


class BulkEnrollmentCreate(BaseModel):
    student_ids: list[int] = Field(min_length=1, max_length=200)
    course_offering_id: int


class ClassScheduleCreate(BaseModel):
    course_offering_id: int
    day_of_week: int = Field(ge=1, le=7)
    start_time: time
    end_time: time
    room: str | None = Field(default=None, max_length=80)


class FacultyCreate(BaseModel):
    id: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    department_id: int
    employee_id: str = Field(min_length=1, max_length=50)
    designation: str | None = Field(default=None, max_length=120)
    password: str = Field(min_length=8, max_length=72)
    phone: str | None = Field(default=None, max_length=32)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must not exceed 72 UTF-8 bytes")
        return value


class CourseCreate(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    department_id: int
    description: str | None = None
    credits: int = Field(default=3, gt=0)


class CourseOfferingCreate(BaseModel):
    course_id: int
    faculty_id: int
    semester_id: int
    section: str = Field(default="A", min_length=1, max_length=20)
    capacity: int | None = Field(default=None, gt=0)
    room: str | None = Field(default=None, max_length=80)


class EnrollmentCreate(BaseModel):
    student_id: int
    course_offering_id: int


class StudentEnrollmentCreate(BaseModel):
    course_offering_id: int


class AttendanceItem(BaseModel):
    student_id: str
    status: str


class AttendanceRequest(BaseModel):
    course_code: str
    date: date
    records: list[AttendanceItem] = Field(min_length=1)
    course_offering_id: int | None = None
    start_time: time | None = None
    end_time: time | None = None
    topic: str | None = None


class AttendanceRecordInput(BaseModel):
    student_id: int
    status: str


class AttendanceSessionCreate(BaseModel):
    course_offering_id: int
    session_date: date
    start_time: time | None = None
    end_time: time | None = None
    topic: str | None = None
    records: list[AttendanceRecordInput] = Field(default_factory=list)


class ResultItem(BaseModel):
    student_id: str
    marks: Decimal = Field(ge=0)
    max_marks: Decimal = Field(default=Decimal("100"), gt=0)


class ResultRequest(BaseModel):
    course_code: str
    results: list[ResultItem] = Field(min_length=1)
    course_offering_id: int | None = None
    assessment_name: str = Field(default="Final", min_length=1, max_length=120)


class AssignmentCreate(BaseModel):
    course_offering_id: int
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    instructions: str | None = None
    due_date: datetime
    max_marks: Decimal = Field(gt=0)
    attachment_url: str | None = Field(default=None, max_length=1000)
    status: str = "published"


class SubmissionCreate(BaseModel):
    text_content: str | None = None
    file_url: str | None = Field(default=None, max_length=1000)


class SubmissionGrade(BaseModel):
    marks: Decimal = Field(ge=0)
    feedback: str | None = None


class ExamCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    exam_type: str = Field(min_length=1, max_length=40)
    semester_id: int
    start_date: date
    end_date: date


class ExamScheduleCreate(BaseModel):
    exam_id: int
    course_offering_id: int
    exam_date: date
    start_time: time
    end_time: time
    room: str | None = Field(default=None, max_length=80)


class NoticeCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    audience: str = "all"
    department_id: int | None = None
    expires_at: datetime | None = None
    is_published: bool = True


class GradeResultCreate(BaseModel):
    student_id: int
    course_offering_id: int
    assessment_name: str = Field(min_length=1, max_length=120)
    marks: Decimal = Field(ge=0)
    max_marks: Decimal = Field(gt=0)
    exam_schedule_id: int | None = None


class ResultPublish(BaseModel):
    is_published: bool = True


class GradeResultItem(BaseModel):
    student_id: int
    marks: Decimal = Field(ge=0)
    max_marks: Decimal = Field(gt=0)


class GradeResultBatch(BaseModel):
    course_offering_id: int
    assessment_name: str = Field(min_length=1, max_length=120)
    results: list[GradeResultItem] = Field(min_length=1)
