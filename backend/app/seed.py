from datetime import date, timedelta
from sqlalchemy.orm import Session
from .models import User, Course, Enrollment, Assignment, Notice
from .auth import hash_password

def seed(db: Session):
    if db.query(User).count():
        return
    admin = User(user_id="admin", name="Admin User", email="admin@university.edu",
                 password_hash=hash_password("admin123"), role="admin")
    faculty = User(user_id="F001", name="Dr. Sharma", email="sharma@university.edu",
                   password_hash=hash_password("faculty123"), role="faculty",
                   department="Computer Science")
    student = User(user_id="2024CS1042", name="Prem Kumar", email="prem@university.edu",
                   password_hash=hash_password("student123"), role="student",
                   department="Computer Science", semester=4)
    db.add_all([admin, faculty, student]); db.flush()

    courses = [
        Course(code="CS401", name="Operating Systems", faculty_id=faculty.id, department="Computer Science", semester=4),
        Course(code="CS402", name="Database Management", faculty_id=faculty.id, department="Computer Science", semester=4),
        Course(code="CS403", name="Software Engineering", faculty_id=faculty.id, department="Computer Science", semester=4),
        Course(code="CS404", name="Computer Networks", faculty_id=faculty.id, department="Computer Science", semester=4),
        Course(code="CS405", name="Web Technologies", faculty_id=faculty.id, department="Computer Science", semester=4),
        Course(code="CS406", name="Data Structures", faculty_id=faculty.id, department="Computer Science", semester=4),
    ]
    db.add_all(courses); db.flush()
    db.add_all([Enrollment(student_id=student.id, course_id=c.id) for c in courses])
    db.add_all([
        Assignment(title="Operating Systems Assignment", subject="Operating Systems", course_id=courses[0].id, due=date(2026,9,5)),
        Assignment(title="University Management System", subject="Software Engineering", course_id=courses[2].id, due=date(2026,9,7)),
        Assignment(title="Database Normalization", subject="Database Management", course_id=courses[1].id, due=date(2026,9,10), status="Submitted"),
    ])
    db.add_all([
        Notice(title="Mid-Semester Examination Schedule", body="The mid-semester examination schedule has been published.", date=date(2026,9,2)),
        Notice(title="Project Submission Deadline", body="All students must submit their Software Engineering project before the deadline.", date=date(2026,9,1)),
        Notice(title="Library Timing Updated", body="The university library will remain open until 8:00 PM.", date=date(2026,8,30)),
    ])
    db.commit()
