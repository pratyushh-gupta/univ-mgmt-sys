from .academics import AcademicYear, Course, CourseOffering, Enrollment, Semester
from .identity import Department, Faculty, Student, User
from .learning import (
    Assignment,
    AttendanceRecord,
    AttendanceSession,
    AuditLog,
    Exam,
    ExamSchedule,
    Notice,
    Notification,
    Result,
    Submission,
)
from .lifecycle import AdmissionApplication, ClassSchedule

__all__ = [
    "AcademicYear", "Assignment", "AttendanceRecord", "AttendanceSession", "AuditLog",
    "Course", "CourseOffering", "Department", "Enrollment", "Exam", "ExamSchedule",
    "AdmissionApplication", "ClassSchedule", "Faculty", "Notice", "Notification", "Result", "Semester", "Student", "Submission", "User",
]
