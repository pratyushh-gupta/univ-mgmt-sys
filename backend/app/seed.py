"""Idempotent development-only demo data seeder."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from .core.config import settings
from .core.security import hash_password
from .database.connection import SessionLocal
from .models import (
    AcademicYear, Assignment, AttendanceRecord, AttendanceSession, ClassSchedule, Course, CourseOffering,
    Department, Enrollment, Exam, ExamSchedule, Faculty, Notice, Notification, Result, Semester, Student,
    Submission, User,
)


def seed(db: Session) -> None:
    if settings.environment != "development":
        raise RuntimeError("Demo data can only be seeded when ENVIRONMENT=development")

    department = db.query(Department).filter_by(code="CSE").first()
    if department is None:
        department = Department(code="CSE", name="Computer Science", description="Development sample department")
        db.add(department)
        db.flush()
    engineering = db.query(Department).filter_by(code="ECE").first()
    if engineering is None:
        engineering = Department(code="ECE", name="Electronics Engineering", description="Development sample department")
        db.add(engineering)
        db.flush()

    academic_year = db.query(AcademicYear).filter_by(name="2026-2027").first()
    if academic_year is None:
        academic_year = AcademicYear(name="2026-2027", start_date=date(2026, 8, 1), end_date=date(2027, 7, 31), is_active=True)
        db.add(academic_year)
        db.flush()
    semester = db.query(Semester).filter_by(academic_year_id=academic_year.id, number=1).first()
    if semester is None:
        semester = Semester(academic_year_id=academic_year.id, name="Semester 1", number=1,
            start_date=date(2026, 8, 1), end_date=date(2026, 12, 20), is_active=True)
        db.add(semester)
        db.flush()
    semester_two = db.query(Semester).filter_by(academic_year_id=academic_year.id, number=2).first()
    if semester_two is None:
        semester_two = Semester(academic_year_id=academic_year.id, name="Semester 2", number=2,
            start_date=date(2027, 1, 1), end_date=date(2027, 7, 31), is_active=False)
        db.add(semester_two)
        db.flush()

    admin = db.query(User).filter_by(user_id="admin").first()
    if admin is None:
        admin = User(user_id="admin", name="Admin User", email="admin@university.edu",
            password_hash=hash_password("admin123"), role="admin")
        db.add(admin)

    faculty_user = db.query(User).filter_by(user_id="F001").first()
    if faculty_user is None:
        faculty_user = User(user_id="F001", name="Dr. Sharma", email="sharma@university.edu",
            password_hash=hash_password("faculty123"), role="faculty")
        db.add(faculty_user)
        db.flush()
    faculty = db.query(Faculty).filter_by(user_id=faculty_user.id).first()
    if faculty is None:
        faculty = Faculty(user_id=faculty_user.id, employee_id="F001", department_id=department.id, designation="Lecturer")
        db.add(faculty)
        db.flush()

    faculty_two_user = db.query(User).filter_by(user_id="F002").first()
    if faculty_two_user is None:
        faculty_two_user = User(user_id="F002", name="Dr. Mehta", email="mehta@university.edu",
            password_hash=hash_password("faculty456"), role="faculty")
        db.add(faculty_two_user)
        db.flush()
    faculty_two = db.query(Faculty).filter_by(user_id=faculty_two_user.id).first()
    if faculty_two is None:
        faculty_two = Faculty(user_id=faculty_two_user.id, employee_id="F002", department_id=engineering.id, designation="Assistant Professor")
        db.add(faculty_two)
        db.flush()

    student_user = db.query(User).filter_by(user_id="2024CS1042").first()
    if student_user is None:
        student_user = User(user_id="2024CS1042", name="Prem Kumar", email="prem@university.edu",
            password_hash=hash_password("student123"), role="student")
        db.add(student_user)
        db.flush()
    student = db.query(Student).filter_by(user_id=student_user.id).first()
    if student is None:
        student = Student(user_id=student_user.id, enrollment_number="2024CS1042", department_id=department.id,
            semester_id=semester.id, admission_year=2024)
        db.add(student)
        db.flush()

    student_two_user = db.query(User).filter_by(user_id="2024EE1001").first()
    if student_two_user is None:
        student_two_user = User(user_id="2024EE1001", name="Asha Verma", email="asha@university.edu",
            password_hash=hash_password("student456"), role="student")
        db.add(student_two_user)
        db.flush()
    student_two = db.query(Student).filter_by(user_id=student_two_user.id).first()
    if student_two is None:
        student_two = Student(user_id=student_two_user.id, enrollment_number="2024ECE1001", department_id=engineering.id,
            semester_id=semester.id, admission_year=2024)
        db.add(student_two)
        db.flush()

    courses = [
        ("CS401", "Operating Systems"),
        ("CS402", "Database Management"),
        ("CS403", "Software Engineering"),
    ]
    offerings = []
    for code, name in courses:
        course = db.query(Course).filter_by(code=code).first()
        if course is None:
            course = Course(code=code, name=name, department_id=department.id, credits=3)
            db.add(course)
            db.flush()
        offering = db.query(CourseOffering).filter_by(course_id=course.id, semester_id=semester.id, section="A").first()
        if offering is None:
            offering = CourseOffering(course_id=course.id, faculty_id=faculty.id, semester_id=semester.id, section="A")
            db.add(offering)
            db.flush()
        offerings.append(offering)
        if db.query(Enrollment).filter_by(student_id=student.id, course_offering_id=offering.id).first() is None:
            db.add(Enrollment(student_id=student.id, course_offering_id=offering.id))
    electronics = db.query(Course).filter_by(code="ECE401").first()
    if electronics is None:
        electronics = Course(code="ECE401", name="Digital Systems", department_id=engineering.id, credits=4)
        db.add(electronics)
        db.flush()
    electronics_offering = db.query(CourseOffering).filter_by(course_id=electronics.id, semester_id=semester.id, section="A").first()
    if electronics_offering is None:
        electronics_offering = CourseOffering(course_id=electronics.id, faculty_id=faculty_two.id,
            semester_id=semester.id, section="A", capacity=60)
        db.add(electronics_offering)
        db.flush()
    if not db.query(Enrollment).filter_by(student_id=student_two.id, course_offering_id=electronics_offering.id).first():
        db.add(Enrollment(student_id=student_two.id, course_offering_id=electronics_offering.id))

    if db.query(Assignment).filter_by(course_offering_id=offerings[0].id, title="Operating Systems Assignment").first() is None:
        assignment = Assignment(course_offering_id=offerings[0].id, faculty_id=faculty.id,
            title="Operating Systems Assignment", description="Development sample assignment",
            due_date=datetime.now(timezone.utc) + timedelta(days=14), max_marks=100, status="published",
            published_at=datetime.now(timezone.utc))
        db.add(assignment)
    else:
        assignment = db.query(Assignment).filter_by(course_offering_id=offerings[0].id,
            title="Operating Systems Assignment").first()
    if db.query(Submission).filter_by(assignment_id=assignment.id, student_id=student.id).first() is None:
        db.add(Submission(assignment_id=assignment.id, course_offering_id=offerings[0].id,
            student_id=student.id, text_content="Development sample submission metadata.", status="submitted",
            submitted_at=datetime.now(timezone.utc)))
    if db.query(Notice).filter_by(title="Welcome to the development portal").first() is None:
        db.add(Notice(title="Welcome to the development portal", content="This notice is development sample data.",
            author_id=admin.id, audience="all", is_published=True, published_at=datetime.now(timezone.utc)))
    exam = db.query(Exam).filter_by(name="Fall Midterm", semester_id=semester.id).first()
    if exam is None:
        exam = Exam(name="Fall Midterm", exam_type="midterm", semester_id=semester.id,
            start_date=date(2026, 10, 1), end_date=date(2026, 10, 31), status="scheduled")
        db.add(exam)
        db.flush()
    if not db.query(ExamSchedule).filter_by(exam_id=exam.id, course_offering_id=offerings[0].id).first():
        db.add(ExamSchedule(exam_id=exam.id, course_offering_id=offerings[0].id,
            semester_id=semester.id, exam_date=date(2026, 10, 12), start_time=time(10), end_time=time(12), room="Hall 1"))
    for session_date, status in ((date(2026, 9, 8), "present"), (date(2026, 9, 15), "absent")):
        attendance_session = db.query(AttendanceSession).filter_by(course_offering_id=offerings[0].id,
            session_date=session_date, start_time=time(9)).first()
        if attendance_session is None:
            attendance_session = AttendanceSession(course_offering_id=offerings[0].id, faculty_id=faculty.id,
                session_date=session_date, start_time=time(9), end_time=time(10), topic="Development sample class",
                status="published")
            db.add(attendance_session)
            db.flush()
        if db.query(AttendanceRecord).filter_by(attendance_session_id=attendance_session.id,
                student_id=student.id).first() is None:
            db.add(AttendanceRecord(attendance_session_id=attendance_session.id, course_offering_id=offerings[0].id,
                student_id=student.id, status=status))
    if db.query(ClassSchedule).filter_by(course_offering_id=offerings[0].id, day_of_week=1,
            start_time=time(9)).first() is None:
        db.add(ClassSchedule(course_offering_id=offerings[0].id, day_of_week=1, start_time=time(9),
            end_time=time(10), room="Engineering 101", is_active=True))
    result = db.query(Result).filter_by(student_id=student.id, course_offering_id=offerings[0].id,
        assessment_name="Development Midterm").first()
    if result is None:
        result = Result(student_id=student.id, course_offering_id=offerings[0].id,
            assessment_name="Development Midterm", marks=82, max_marks=100, grade="A", grade_point=9,
            status="published", published_at=datetime.now(timezone.utc), published_by=admin.id)
    final_result = db.query(Result).filter_by(student_id=student.id, course_offering_id=offerings[0].id,
        assessment_name="Development Final").first()
    if final_result is None:
        final_result = Result(student_id=student.id, course_offering_id=offerings[0].id,
            assessment_name="Development Final", marks=91, max_marks=100, grade="A+", grade_point=10,
            status="published", is_final=True, published_at=datetime.now(timezone.utc), published_by=admin.id)
        db.add(final_result)
        db.add(result)
    if not db.query(Notification).filter_by(user_id=student.user_id, title="Welcome to the portal").first():
        db.add(Notification(user_id=student.user_id, title="Welcome to the portal",
            message="Your development student account is ready.", notification_type="general"))
    if not db.query(Notification).filter_by(user_id=student_two.user_id, title="Welcome to the portal").first():
        db.add(Notification(user_id=student_two.user_id, title="Welcome to the portal",
            message="Your development student account is ready.", notification_type="general"))
    db.flush()
    attendance_rows = db.query(AttendanceRecord.status).filter_by(student_id=student.id,
        course_offering_id=offerings[0].id).all()
    attendance_count = len(attendance_rows)
    attended_count = sum(status in {"present", "late"} for (status,) in attendance_rows)
    if attendance_count and attended_count / attendance_count * 100 < settings.low_attendance_threshold_percent and not db.query(Notification).filter_by(user_id=student.user_id, title="Low attendance warning").first():
        db.add(Notification(user_id=student.user_id, title="Low attendance warning",
            message=f"Your attendance for CS401 is below the configured {settings.low_attendance_threshold_percent}% development warning threshold.",
            notification_type="low_attendance"))
    db.commit()


def main() -> None:
    if settings.environment != "development":
        raise SystemExit("Refusing to seed outside ENVIRONMENT=development")
    with SessionLocal() as db:
        seed(db)
    print("Development sample data is ready.")


if __name__ == "__main__":
    main()
