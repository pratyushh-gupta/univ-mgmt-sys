from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import CourseOffering, Enrollment, Exam, ExamSchedule, Notification, Semester, User
from ..services.domain import faculty_offering, faculty_profile, student_profile
from ..schemas import ExamCreate, ExamScheduleCreate, ExamScheduleUpdate, ExamUpdate
from ..services.domain import audit_event, commit_or_conflict

router = APIRouter()


def schedule_json(row: ExamSchedule) -> dict:
    return {"id": row.id, "exam_id": row.exam_id, "course_offering_id": row.course_offering_id,
        "course_code": row.course_offering.course.code, "course_name": row.course_offering.course.name,
        "exam_name": row.exam.name, "exam_type": row.exam.exam_type, "semester_id": row.semester_id,
        "exam_date": row.exam_date.isoformat(), "start_time": row.start_time.isoformat(),
        "end_time": row.end_time.isoformat(), "room": row.room, "max_marks": float(row.max_marks),
        "status": row.exam.status}


def validate_schedule(db: Session, offering: CourseOffering, exam_date, start_time, end_time,
                      room: str | None, exclude_id: int | None = None) -> None:
    if end_time <= start_time:
        raise HTTPException(status_code=422, detail="Exam end time must follow start time")
    query = db.query(ExamSchedule).join(Exam, Exam.id == ExamSchedule.exam_id).filter(Exam.status != "cancelled",
        ExamSchedule.exam_date == exam_date,
        ExamSchedule.start_time < end_time, ExamSchedule.end_time > start_time)
    if exclude_id is not None:
        query = query.filter(ExamSchedule.id != exclude_id)
    for current in query.all():
        other = current.course_offering
        same_room = bool(room and current.room and room.strip().casefold() == current.room.strip().casefold())
        same_faculty = other.faculty_id == offering.faculty_id
        same_student = db.query(Enrollment.id).filter(Enrollment.status == "active",
            Enrollment.student_id.in_(db.query(Enrollment.student_id).filter_by(course_offering_id=offering.id, status="active")),
            Enrollment.course_offering_id == other.id).first() is not None
        if same_room or same_faculty or same_student:
            raise HTTPException(status_code=409, detail="Exam time conflicts with an existing room, faculty, or student schedule")


@router.get("/exams")
def list_exams(user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db),
               semester_id: int | None = None, exam_type: str | None = None):
    query = db.query(Exam)
    if semester_id is not None: query = query.filter(Exam.semester_id == semester_id)
    if exam_type: query = query.filter(Exam.exam_type.ilike(f"%{exam_type}%"))
    if user.role == "faculty":
        faculty_id = faculty_profile(db, user).id
        query = query.filter(Exam.id.in_(db.query(ExamSchedule.exam_id).join(CourseOffering).filter(CourseOffering.faculty_id == faculty_id)))
    return [{"id": row.id, "name": row.name, "exam_type": row.exam_type, "semester_id": row.semester_id,
        "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "status": row.status,
        "schedules": [schedule_json(schedule) for schedule in row.schedules]}
        for row in query.order_by(Exam.start_date).all()]


@router.post("/exams", status_code=201)
def create_exam(data: ExamCreate, request: Request, user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    if db.get(Semester, data.semester_id) is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    if data.end_date < data.start_date:
        raise HTTPException(status_code=422, detail="Exam end date cannot precede its start date")
    if data.exam_type.casefold() not in {"internal", "midterm", "final"}:
        raise HTTPException(status_code=422, detail="Exam type must be Internal, Midterm, or Final")
    offering = None
    schedule_data = None
    if data.course_offering_id is not None:
        offering = db.get(CourseOffering, data.course_offering_id)
        if offering is None or not offering.is_active or offering.semester_id != data.semester_id:
            raise HTTPException(status_code=422, detail="Course offering must belong to the selected semester")
        if user.role == "faculty": faculty_offering(db, user, offering.id)
        if None in (data.exam_date, data.start_time, data.end_time):
            raise HTTPException(status_code=422, detail="A course offering exam requires a date and start/end times")
        if not (data.start_date <= data.exam_date <= data.end_date):
            raise HTTPException(status_code=422, detail="Exam date must fall within the exam period")
        validate_schedule(db, offering, data.exam_date, data.start_time, data.end_time, data.room)
        schedule_data = {"course_offering_id": offering.id, "semester_id": offering.semester_id,
            "exam_date": data.exam_date, "start_time": data.start_time, "end_time": data.end_time,
            "room": data.room, "max_marks": data.max_marks}
    row = Exam(name=data.name, exam_type=data.exam_type.casefold(), semester_id=data.semester_id,
        start_date=data.start_date, end_date=data.end_date, status="scheduled" if offering else "draft")
    db.add(row)
    db.flush()
    if schedule_data:
        scheduled = ExamSchedule(exam_id=row.id, **schedule_data)
        db.add(scheduled)
        db.flush()
        for enrollment in offering.enrollments:
            if enrollment.status == "active":
                db.add(Notification(user_id=enrollment.student.user_id, title="Exam scheduled",
                    message=f"{row.name} for {offering.course.code} is scheduled on {scheduled.exam_date.isoformat()}.",
                    notification_type="exam"))
    audit_event(db, user=user, action="exam.create", entity_type="exam", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "name": row.name, "exam_type": row.exam_type, "semester_id": row.semester_id,
        "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "status": row.status}


@router.patch("/exams/{exam_id}")
def update_exam(exam_id: int, data: ExamUpdate, request: Request,
                user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(Exam, exam_id)
    if row is None: raise HTTPException(status_code=404, detail="Exam not found")
    if data.status not in {"draft", "scheduled", "completed", "cancelled"}:
        raise HTTPException(status_code=422, detail="Invalid exam status")
    if data.status == "scheduled" and not row.schedules:
        raise HTTPException(status_code=409, detail="An exam needs a schedule before it can be scheduled")
    was_scheduled = row.status == "scheduled"
    row.status = data.status
    if was_scheduled and row.status == "cancelled":
        for schedule in row.schedules:
            for enrollment in schedule.course_offering.enrollments:
                if enrollment.status == "active":
                    db.add(Notification(user_id=enrollment.student.user_id, title="Exam cancelled",
                        message=f"{row.name} for {schedule.course_offering.course.code} has been cancelled.",
                        notification_type="exam"))
    audit_event(db, user=user, action="exam.update", entity_type="exam", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "status": row.status}


@router.get("/exam-schedules")
def list_exam_schedules(user: User = Depends(require_roles("admin", "faculty", "student")), db: Session = Depends(get_db),
                        semester_id: int | None = None, course_offering_id: int | None = None):
    query = db.query(ExamSchedule).join(Exam, Exam.id == ExamSchedule.exam_id)
    if semester_id is not None: query = query.filter(ExamSchedule.semester_id == semester_id)
    if course_offering_id is not None: query = query.filter(ExamSchedule.course_offering_id == course_offering_id)
    if user.role == "student":
        student = student_profile(db, user)
        query = query.join(Enrollment, Enrollment.course_offering_id == ExamSchedule.course_offering_id).filter(
            Enrollment.student_id == student.id, Enrollment.status == "active", Exam.status == "scheduled")
    elif user.role == "faculty":
        faculty = faculty_profile(db, user)
        query = query.join(CourseOffering, CourseOffering.id == ExamSchedule.course_offering_id).filter(CourseOffering.faculty_id == faculty.id)
    return [schedule_json(row) for row in query.order_by(ExamSchedule.exam_date, ExamSchedule.start_time).all()]


@router.get("/student/exams")
def student_exams(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    rows = db.query(ExamSchedule).join(Exam, Exam.id == ExamSchedule.exam_id).join(Enrollment,
        Enrollment.course_offering_id == ExamSchedule.course_offering_id).filter(
        Enrollment.student_id == student.id, Enrollment.status == "active", Exam.status == "scheduled").order_by(ExamSchedule.exam_date).all()
    return [{"id": row.id, "course_code": row.course_offering.course.code, "course_name": row.course_offering.course.name,
        "exam_name": row.exam.name, "exam_type": row.exam.exam_type, "exam_date": row.exam_date.isoformat(),
        "start_time": row.start_time.isoformat(), "end_time": row.end_time.isoformat(), "room": row.room} for row in rows]


@router.post("/exam-schedules", status_code=201)
def create_exam_schedule(data: ExamScheduleCreate, request: Request,
                         user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    exam, offering = db.get(Exam, data.exam_id), db.get(CourseOffering, data.course_offering_id)
    if exam is None or offering is None:
        raise HTTPException(status_code=404, detail="Exam or course offering not found")
    if exam.semester_id != offering.semester_id:
        raise HTTPException(status_code=422, detail="Exam and course offering must use the same semester")
    if user.role == "faculty": faculty_offering(db, user, offering.id)
    validate_schedule(db, offering, data.exam_date, data.start_time, data.end_time, data.room)
    if not (exam.start_date <= data.exam_date <= exam.end_date):
        raise HTTPException(status_code=422, detail="Exam date must fall within the exam period")
    row = ExamSchedule(**data.model_dump(), semester_id=exam.semester_id)
    db.add(row)
    db.flush()
    exam.status = "scheduled"
    audit_event(db, user=user, action="exam_schedule.create", entity_type="exam_schedule", entity_id=row.id, request=request)
    for enrollment in offering.enrollments:
        if enrollment.status == "active":
            db.add(Notification(user_id=enrollment.student.user_id, title="Exam scheduled",
                message=f"{exam.name} for {offering.course.code} is scheduled on {data.exam_date.isoformat()}.",
                notification_type="exam"))
    commit_or_conflict(db)
    return schedule_json(row)


@router.patch("/exam-schedules/{schedule_id}")
def update_exam_schedule(schedule_id: int, data: ExamScheduleUpdate, request: Request,
                         user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    row = db.get(ExamSchedule, schedule_id)
    if row is None: raise HTTPException(status_code=404, detail="Exam schedule not found")
    offering = db.get(CourseOffering, row.course_offering_id)
    if user.role == "faculty": faculty_offering(db, user, offering.id)
    changes = data.model_dump(exclude_unset=True)
    proposed = {"exam_date": changes.get("exam_date", row.exam_date), "start_time": changes.get("start_time", row.start_time),
        "end_time": changes.get("end_time", row.end_time), "room": changes.get("room", row.room)}
    exam = row.exam
    if not (exam.start_date <= proposed["exam_date"] <= exam.end_date):
        raise HTTPException(status_code=422, detail="Exam date must fall within the exam period")
    validate_schedule(db, offering, **proposed, exclude_id=row.id)
    changed = any(getattr(row, key) != value for key, value in proposed.items())
    for key, value in changes.items(): setattr(row, key, value)
    if changed:
        for enrollment in offering.enrollments:
            if enrollment.status == "active":
                db.add(Notification(user_id=enrollment.student.user_id, title="Exam schedule updated",
                    message=f"The schedule for {exam.name} ({offering.course.code}) has changed.",
                    notification_type="exam"))
    audit_event(db, user=user, action="exam_schedule.update", entity_type="exam_schedule", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return schedule_json(row)
