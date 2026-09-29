from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import Course, Enrollment, Notice, User
from ..schemas import CourseCreate

router = APIRouter()


def course_response(course: Course, faculty: User | None, db: Session) -> dict:
    return {
        "code": course.code,
        "name": course.name,
        "faculty": faculty.name if faculty else None,
        "department": course.department,
        "enrolled": db.query(Enrollment).filter_by(course_id=course.id).count(),
        "semester": course.semester,
    }


@router.get("/courses")
def courses(db: Session = Depends(get_db)):
    return [
        course_response(course, db.get(User, course.faculty_id) if course.faculty_id else None, db)
        for course in db.query(Course).all()
    ]


@router.post("/courses")
def add_course(
    data: CourseCreate,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if db.query(Course).filter_by(code=data.code).first():
        raise HTTPException(status_code=409, detail="Course code already exists")

    faculty_name = data.faculty.strip() if data.faculty else ""
    faculty = None
    if faculty_name:
        faculty = db.query(User).filter_by(name=faculty_name, role="faculty").first()
        if faculty is None:
            raise HTTPException(status_code=400, detail="The supplied faculty member was not found")

    course = Course(
        code=data.code,
        name=data.name,
        faculty_id=faculty.id if faculty else None,
        department=data.department,
        semester=data.semester,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    persisted_faculty = db.get(User, course.faculty_id) if course.faculty_id else None
    return {
        "code": course.code,
        "name": course.name,
        "faculty": persisted_faculty.name if persisted_faculty else None,
        "department": course.department,
        "enrolled": 0,
    }


@router.delete("/courses/{code}")
def delete_course(
    code: str,
    _: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    course = db.query(Course).filter_by(code=code).first()
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    db.delete(course)
    db.commit()
    return {"message": "Course removed"}


@router.get("/notices")
def notices(db: Session = Depends(get_db)):
    return [
        {"title": notice.title, "body": notice.body, "date": notice.date.isoformat()}
        for notice in db.query(Notice).order_by(Notice.date.desc()).all()
    ]
