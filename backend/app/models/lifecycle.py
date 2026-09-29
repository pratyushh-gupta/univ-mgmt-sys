from datetime import date, datetime, time

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class AdmissionApplication(Base):
    __tablename__ = "admission_applications"
    __table_args__ = (
        CheckConstraint("status IN ('submitted', 'under_review', 'approved', 'rejected', 'withdrawn')",
                        name="ck_admission_applications_status"),
        Index("ix_admission_applications_status_submitted", "status", "submitted_at"),
        Index("ix_admission_applications_department_year", "department_id", "academic_year_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    applicant_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str | None] = mapped_column(String(32))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    address: Mapped[str | None] = mapped_column(Text)
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False)
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.id", ondelete="RESTRICT"), nullable=False)
    intended_program: Mapped[str] = mapped_column(String(160), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="submitted", server_default="submitted")
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    student_id: Mapped[int | None] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    department: Mapped["Department"] = relationship()
    academic_year: Mapped["AcademicYear"] = relationship()
    reviewer: Mapped["User | None"] = relationship()
    student: Mapped["Student | None"] = relationship()


class ClassSchedule(Base):
    __tablename__ = "class_schedules"
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 1 AND 7", name="ck_class_schedule_weekday"),
        CheckConstraint("end_time > start_time", name="ck_class_schedule_times"),
        Index("ix_class_schedules_day_time", "day_of_week", "start_time", "end_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False, index=True)
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(80))
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    course_offering: Mapped["CourseOffering"] = relationship()
