from datetime import date, datetime
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), index=True)
    department: Mapped[str | None] = mapped_column(String(120), nullable=True)
    semester: Mapped[int | None] = mapped_column(Integer, nullable=True)

class Course(Base):
    __tablename__ = "courses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150))
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    department: Mapped[str] = mapped_column(String(120))
    semester: Mapped[int] = mapped_column(Integer, default=1)

class Enrollment(Base):
    __tablename__ = "enrollments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    __table_args__ = (UniqueConstraint("student_id", "course_id"),)

class Attendance(Base):
    __tablename__ = "attendance"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(10))
    __table_args__ = (UniqueConstraint("student_id", "course_id", "date"),)

class Result(Base):
    __tablename__ = "results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    marks: Mapped[float] = mapped_column(Float)
    grade: Mapped[str] = mapped_column(String(3))
    point: Mapped[float] = mapped_column(Float)
    __table_args__ = (UniqueConstraint("student_id", "course_id"),)

class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    subject: Mapped[str] = mapped_column(String(150))
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"))
    due: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="Pending")

class Notice(Base):
    __tablename__ = "notices"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(2000))
    date: Mapped[date] = mapped_column(Date)
