from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import CourseOffering, Enrollment, Exam, ExamSchedule, Notification, Semester, User
from ..services.domain import faculty_profile, student_profile
from ..schemas import ExamCreate, ExamScheduleCreate
from ..services.domain import audit_event, commit_or_conflict

router = APIRouter()


@router.get("/exams")
def list_exams(_: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    return [{"id": row.id, "name": row.name, "exam_type": row.exam_type, "semester_id": row.semester_id,
        "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "status": row.status}
        for row in db.query(Exam).all()]


@router.post("/exams", status_code=201)
def create_exam(data: ExamCreate, request: Request, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.get(Semester, data.semester_id) is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    if data.end_date < data.start_date:
        raise HTTPException(status_code=422, detail="Exam end date cannot precede its start date")
    row = Exam(**data.model_dump())
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="exam.create", entity_type="exam", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "name": row.name, "exam_type": row.exam_type, "semester_id": row.semester_id,
        "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "status": row.status}


@router.get("/exam-schedules")
def list_exam_schedules(user: User = Depends(require_roles("admin", "faculty", "student")), db: Session = Depends(get_db)):
    query = db.query(ExamSchedule)
    if user.role == "student":
        student = student_profile(db, user)
        query = query.join(Enrollment, Enrollment.course_offering_id == ExamSchedule.course_offering_id).filter(
            Enrollment.student_id == student.id, Enrollment.status == "active")
    elif user.role == "faculty":
        faculty = faculty_profile(db, user)
        query = query.join(CourseOffering).filter(CourseOffering.faculty_id == faculty.id)
    return [{"id": row.id, "exam_id": row.exam_id, "course_offering_id": row.course_offering_id,
        "course_code": row.course_offering.course.code, "exam_name": row.exam.name,
        "exam_date": row.exam_date.isoformat(), "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(), "room": row.room} for row in query.all()]


@router.get("/student/exams")
def student_exams(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    rows = db.query(ExamSchedule).join(Enrollment,
        Enrollment.course_offering_id == ExamSchedule.course_offering_id).filter(
        Enrollment.student_id == student.id, Enrollment.status == "active").order_by(ExamSchedule.exam_date).all()
    return [{"id": row.id, "course_code": row.course_offering.course.code, "course_name": row.course_offering.course.name,
        "exam_name": row.exam.name, "exam_type": row.exam.exam_type, "exam_date": row.exam_date.isoformat(),
        "start_time": row.start_time.isoformat(), "end_time": row.end_time.isoformat(), "room": row.room} for row in rows]


@router.post("/exam-schedules", status_code=201)
def create_exam_schedule(data: ExamScheduleCreate, request: Request,
                         user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    exam, offering = db.get(Exam, data.exam_id), db.get(CourseOffering, data.course_offering_id)
    if exam is None or offering is None:
        raise HTTPException(status_code=404, detail="Exam or course offering not found")
    if exam.semester_id != offering.semester_id:
        raise HTTPException(status_code=422, detail="Exam and course offering must use the same semester")
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=422, detail="Exam end time must follow start time")
    if not (exam.start_date <= data.exam_date <= exam.end_date):
        raise HTTPException(status_code=422, detail="Exam date must fall within the exam period")
    row = ExamSchedule(**data.model_dump(), semester_id=exam.semester_id)
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="exam_schedule.create", entity_type="exam_schedule", entity_id=row.id, request=request)
    for enrollment in offering.enrollments:
        if enrollment.status == "active":
            db.add(Notification(user_id=enrollment.student.user_id, title="Exam scheduled",
                message=f"{exam.name} for {offering.course.code} is scheduled on {data.exam_date.isoformat()}.",
                notification_type="exam"))
    commit_or_conflict(db)
    return {"id": row.id, "exam_id": row.exam_id, "course_offering_id": row.course_offering_id,
        "exam_date": row.exam_date.isoformat(), "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(), "room": row.room}
