from datetime import date, datetime

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class AcademicYear(Base):
    __tablename__ = "academic_years"
    __table_args__ = (
        CheckConstraint("end_date > start_date", name="ck_academic_year_dates"),
        UniqueConstraint("name", name="uq_academic_years_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    semesters: Mapped[list["Semester"]] = relationship(back_populates="academic_year")


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (
        CheckConstraint("number > 0", name="ck_semesters_number_positive"),
        CheckConstraint("end_date > start_date", name="ck_semesters_dates"),
        UniqueConstraint("academic_year_id", "number", name="uq_semesters_year_number"),
        UniqueConstraint("academic_year_id", "name", name="uq_semesters_year_name"),
        UniqueConstraint("id", "academic_year_id", name="uq_semesters_id_year"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="semesters")
    students: Mapped[list["Student"]] = relationship(back_populates="semester")
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="semester")
    exams: Mapped[list["Exam"]] = relationship(back_populates="semester")


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        CheckConstraint("credits > 0", name="ck_courses_credits_positive"),
        UniqueConstraint("id", "department_id", name="uq_courses_id_department"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2000))
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    department: Mapped["Department"] = relationship(back_populates="courses")
    offerings: Mapped[list["CourseOffering"]] = relationship(back_populates="course")


class CourseOffering(Base):
    __tablename__ = "course_offerings"
    __table_args__ = (
        UniqueConstraint("course_id", "semester_id", "section", name="uq_offering_course_semester_section"),
        UniqueConstraint("id", "semester_id", name="uq_offerings_id_semester"),
        UniqueConstraint("faculty_id", "id", name="uq_offerings_faculty_id"),
        CheckConstraint("length(trim(section)) > 0", name="ck_offering_section_not_blank"),
        CheckConstraint("capacity IS NULL OR capacity > 0", name="ck_offering_capacity_positive"),
        Index("ix_offerings_faculty_semester", "faculty_id", "semester_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="RESTRICT"), nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False, index=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    section: Mapped[str] = mapped_column(String(20), nullable=False, default="A", server_default="A")
    capacity: Mapped[int | None] = mapped_column(Integer)
    room: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    course: Mapped[Course] = relationship(back_populates="offerings")
    faculty: Mapped["Faculty"] = relationship(back_populates="offerings")
    semester: Mapped[Semester] = relationship(back_populates="offerings")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course_offering")


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "course_offering_id", name="uq_enrollments_student_offering"),
        CheckConstraint("status IN ('active', 'completed', 'dropped', 'withdrawn')", name="ck_enrollments_status"),
        Index("ix_enrollments_offering_status", "course_offering_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False, index=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False, index=True)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    student: Mapped["Student"] = relationship(back_populates="enrollments")
    course_offering: Mapped[CourseOffering] = relationship(back_populates="enrollments")
