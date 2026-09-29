from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint, Index, Integer, JSON, Numeric, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from ..database.base import Base


class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    __table_args__ = (
        ForeignKeyConstraint(["faculty_id", "course_offering_id"], ["course_offerings.faculty_id", "course_offerings.id"], ondelete="RESTRICT", name="fk_attendance_session_faculty_offering"),
        UniqueConstraint("id", "course_offering_id", name="uq_attendance_sessions_id_offering"),
        UniqueConstraint("course_offering_id", "session_date", "start_time", name="uq_attendance_session_period"),
        CheckConstraint("end_time IS NULL OR start_time IS NULL OR end_time > start_time", name="ck_attendance_session_times"),
        CheckConstraint("status IN ('draft', 'published', 'closed')", name="ck_attendance_session_status"),
        Index("ix_attendance_sessions_date", "session_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False, index=True)
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    topic: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published", server_default="published")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    records: Mapped[list["AttendanceRecord"]] = relationship(back_populates="session")
    course_offering: Mapped["CourseOffering"] = relationship(foreign_keys=[course_offering_id])


class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        ForeignKeyConstraint(["attendance_session_id", "course_offering_id"], ["attendance_sessions.id", "attendance_sessions.course_offering_id"], ondelete="RESTRICT", name="fk_attendance_records_session_offering"),
        ForeignKeyConstraint(["student_id", "course_offering_id"], ["enrollments.student_id", "enrollments.course_offering_id"], ondelete="RESTRICT", name="fk_attendance_records_enrollment"),
        UniqueConstraint("attendance_session_id", "student_id", name="uq_attendance_record_session_student"),
        CheckConstraint("status IN ('present', 'absent', 'late', 'excused')", name="ck_attendance_records_status"),
        Index("ix_attendance_records_student_status", "student_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    attendance_session_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    session: Mapped[AttendanceSession] = relationship(back_populates="records", foreign_keys=[attendance_session_id, course_offering_id])
    student: Mapped["Student"] = relationship()


class Assignment(Base):
    __tablename__ = "assignments"
    __table_args__ = (
        ForeignKeyConstraint(["faculty_id", "course_offering_id"], ["course_offerings.faculty_id", "course_offerings.id"], ondelete="RESTRICT", name="fk_assignments_faculty_offering"),
        UniqueConstraint("id", "course_offering_id", name="uq_assignments_id_offering"),
        CheckConstraint("max_marks > 0", name="ck_assignments_max_marks_positive"),
        CheckConstraint("status IN ('draft', 'published', 'closed')", name="ck_assignments_status"),
        Index("ix_assignments_offering_due", "course_offering_id", "due_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False, index=True)
    faculty_id: Mapped[int] = mapped_column(ForeignKey("faculty.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    instructions: Mapped[str | None] = mapped_column(Text)
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    attachment_url: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    submissions: Mapped[list["Submission"]] = relationship(back_populates="assignment")
    course_offering: Mapped["CourseOffering"] = relationship(foreign_keys=[course_offering_id])


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        ForeignKeyConstraint(["assignment_id", "course_offering_id"], ["assignments.id", "assignments.course_offering_id"], ondelete="RESTRICT", name="fk_submissions_assignment_offering"),
        ForeignKeyConstraint(["student_id", "course_offering_id"], ["enrollments.student_id", "enrollments.course_offering_id"], ondelete="RESTRICT", name="fk_submissions_enrollment"),
        UniqueConstraint("assignment_id", "student_id", name="uq_submissions_assignment_student"),
        CheckConstraint("status IN ('draft', 'submitted', 'late', 'graded', 'returned')", name="ck_submissions_status"),
        CheckConstraint("marks IS NULL OR marks >= 0", name="ck_submissions_marks_nonnegative"),
        Index("ix_submissions_student_status", "student_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    assignment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="RESTRICT"), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    file_url: Mapped[str | None] = mapped_column(String(1000))
    text_content: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    marks: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    feedback: Mapped[str | None] = mapped_column(Text)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    graded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assignment: Mapped[Assignment] = relationship(back_populates="submissions", foreign_keys=[assignment_id, course_offering_id])
    student: Mapped["Student"] = relationship()


class Exam(Base):
    __tablename__ = "exams"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="ck_exams_dates"),
        CheckConstraint("status IN ('draft', 'scheduled', 'completed', 'cancelled')", name="ck_exams_status"),
        UniqueConstraint("id", "semester_id", name="uq_exams_id_semester"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(40), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="RESTRICT"), nullable=False, index=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    semester: Mapped["Semester"] = relationship(back_populates="exams")
    schedules: Mapped[list["ExamSchedule"]] = relationship(back_populates="exam")


class ExamSchedule(Base):
    __tablename__ = "exam_schedules"
    __table_args__ = (
        ForeignKeyConstraint(["exam_id", "semester_id"], ["exams.id", "exams.semester_id"], ondelete="RESTRICT", name="fk_exam_schedules_exam_semester"),
        ForeignKeyConstraint(["course_offering_id", "semester_id"], ["course_offerings.id", "course_offerings.semester_id"], ondelete="RESTRICT", name="fk_exam_schedules_offering_semester"),
        UniqueConstraint("exam_id", "course_offering_id", name="uq_exam_schedules_exam_offering"),
        CheckConstraint("end_time > start_time", name="ck_exam_schedules_times"),
        UniqueConstraint("id", "course_offering_id", name="uq_exam_schedules_id_offering"),
        CheckConstraint("max_marks > 0", name="ck_exam_schedule_max_marks_positive"),
        Index("ix_exam_schedules_date", "exam_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_offering_id: Mapped[int] = mapped_column(Integer, nullable=False)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    room: Mapped[str | None] = mapped_column(String(80))
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False, default=Decimal("100"), server_default="100")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    exam: Mapped[Exam] = relationship(foreign_keys=[exam_id])
    course_offering: Mapped["CourseOffering"] = relationship(foreign_keys=[course_offering_id])


class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        ForeignKeyConstraint(["student_id", "course_offering_id"], ["enrollments.student_id", "enrollments.course_offering_id"], ondelete="RESTRICT", name="fk_results_enrollment"),
        ForeignKeyConstraint(["exam_schedule_id", "course_offering_id"], ["exam_schedules.id", "exam_schedules.course_offering_id"], ondelete="RESTRICT", name="fk_results_exam_schedule_offering"),
        UniqueConstraint("student_id", "course_offering_id", "assessment_name", name="uq_results_student_offering_assessment"),
        CheckConstraint("marks >= 0 AND max_marks > 0 AND marks <= max_marks", name="ck_results_marks_range"),
        CheckConstraint("grade_point >= 0 AND grade_point <= 10", name="ck_results_grade_point_range"),
        CheckConstraint("status IN ('draft', 'published')", name="ck_results_status"),
        Index("ix_results_offering_status", "course_offering_id", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    course_offering_id: Mapped[int] = mapped_column(ForeignKey("course_offerings.id", ondelete="RESTRICT"), nullable=False, index=True)
    exam_schedule_id: Mapped[int | None] = mapped_column(Integer)
    assessment_name: Mapped[str] = mapped_column(String(120), nullable=False)
    marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(8, 2), nullable=False)
    grade: Mapped[str | None] = mapped_column(String(4))
    grade_point: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft", server_default="draft")
    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    course_offering: Mapped["CourseOffering"] = relationship()
    student: Mapped["Student"] = relationship(primaryjoin="Student.id == foreign(Result.student_id)", viewonly=True)


class Notice(Base):
    __tablename__ = "notices"
    __table_args__ = (
        CheckConstraint("audience IN ('all', 'admin', 'faculty', 'student')", name="ck_notices_audience"),
        CheckConstraint("expires_at IS NULL OR published_at IS NULL OR expires_at > published_at", name="ck_notices_dates"),
        Index("ix_notices_published_audience", "is_published", "audience", "published_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    audience: Mapped[str] = mapped_column(String(20), nullable=False, default="all", server_default="all")
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id", ondelete="RESTRICT"))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_published: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read_created", "user_id", "is_read", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(40), nullable=False, default="general", server_default="general")
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="notifications")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_logs_entity", "entity_type", "entity_id"), Index("ix_audit_logs_user_created", "user_id", "created_at"))

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
