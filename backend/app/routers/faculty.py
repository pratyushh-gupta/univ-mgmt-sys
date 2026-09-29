from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..core.security import hash_password
from ..database.connection import get_db
from ..models import Attendance, Course, Enrollment, Result, User
from ..schemas import AttendanceRequest, FacultyCreate, ResultRequest
from ..services.serializers import user_json

router = APIRouter()


def grade_for(marks: float) -> tuple[str, int]:
    if marks >= 90:
        return "A+", 10
    if marks >= 80:
        return "A", 9
    if marks >= 70:
        return "B+", 8
    if marks >= 60:
        return "B", 7
    if marks >= 50:
        return "C", 6
    if marks >= 40:
        return "D", 5
    return "F", 0


def get_owned_course(course_code: str, faculty: User, db: Session) -> Course:
    course = db.query(Course).filter_by(code=course_code).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if course.faculty_id != faculty.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course")
    return course


def validate_course_students(course: Course, student_ids: list[str], db: Session) -> None:
    if not student_ids:
        raise HTTPException(status_code=400, detail="At least one student record is required")
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="Duplicate student IDs are not allowed")

    enrolled_ids = {
        row[0]
        for row in (
            db.query(User.user_id)
            .join(Enrollment, Enrollment.student_id == User.id)
            .filter(Enrollment.course_id == course.id, User.role == "student")
            .all()
        )
    }
    invalid_ids = sorted(set(student_ids) - enrolled_ids)
    if invalid_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Student(s) are not enrolled in course {course.code}: {', '.join(invalid_ids)}",
        )


@router.get("/faculty")
def faculty(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [user_json(user) for user in db.query(User).filter(User.role == "faculty").all()]


@router.post("/faculty")
def add_faculty(
    data: FacultyCreate,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.user_id == data.id).first():
        raise HTTPException(status_code=409, detail="Faculty ID already exists")
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=409, detail="Email address already exists")
    user = User(
        user_id=data.id,
        name=data.name,
        email=data.email,
        password_hash=hash_password(data.password),
        role="faculty",
        department=data.department,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user_json(user)


@router.delete("/faculty/{faculty_id}")
def delete_faculty(
    faculty_id: str,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(user_id=faculty_id, role="faculty").first()
    if user is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    db.delete(user)
    db.commit()
    return {"message": "Faculty removed"}


@router.get("/faculty/courses")
def faculty_courses(user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    courses = db.query(Course).filter_by(faculty_id=user.id).all()
    return [
        {
            "code": course.code,
            "name": course.name,
            "department": course.department,
            "students": db.query(Enrollment).filter_by(course_id=course.id).count(),
        }
        for course in courses
    ]


@router.get("/faculty/roster/{course_code}")
def roster(
    course_code: str,
    user: User = Depends(require_roles("faculty")),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter_by(code=course_code, faculty_id=user.id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    students = (
        db.query(User)
        .join(Enrollment, Enrollment.student_id == User.id)
        .filter(Enrollment.course_id == course.id, User.role == "student")
        .all()
    )
    return [{"id": student.user_id, "name": student.name} for student in students]


@router.post("/attendance")
def save_attendance(
    data: AttendanceRequest,
    user: User = Depends(require_roles("faculty")),
    db: Session = Depends(get_db),
):
    course = get_owned_course(data.course_code, user, db)
    if any(record.status not in {"present", "absent"} for record in data.records):
        raise HTTPException(status_code=400, detail="Attendance status must be present or absent")
    validate_course_students(course, [record.student_id for record in data.records], db)

    for record in data.records:
        student = db.query(User).filter_by(user_id=record.student_id, role="student").first()
        attendance = db.query(Attendance).filter_by(
            student_id=student.id, course_id=course.id, date=data.date
        ).first()
        if attendance:
            attendance.status = record.status
        else:
            db.add(Attendance(
                student_id=student.id,
                course_id=course.id,
                date=data.date,
                status=record.status,
            ))
    db.commit()
    return {"message": "Attendance saved"}


@router.post("/results")
def save_results(
    data: ResultRequest,
    user: User = Depends(require_roles("faculty")),
    db: Session = Depends(get_db),
):
    course = get_owned_course(data.course_code, user, db)
    validate_course_students(course, [result.student_id for result in data.results], db)

    for item in data.results:
        student = db.query(User).filter_by(user_id=item.student_id, role="student").first()
        grade, point = grade_for(item.marks)
        result = db.query(Result).filter_by(student_id=student.id, course_id=course.id).first()
        if result:
            result.marks = item.marks
            result.grade = grade
            result.point = point
        else:
            db.add(Result(
                student_id=student.id,
                course_id=course.id,
                marks=item.marks,
                grade=grade,
                point=point,
            ))
    db.commit()
    return {"message": "Results saved"}
