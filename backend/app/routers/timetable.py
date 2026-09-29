from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import ClassSchedule, CourseOffering, Enrollment, User
from ..schemas import ClassScheduleCreate
from ..services.domain import audit_event, commit_or_conflict, faculty_offering, faculty_profile, student_profile

router = APIRouter()


def schedule_json(row: ClassSchedule) -> dict:
    offering = row.course_offering
    return {"id": row.id, "course_offering_id": offering.id, "course_code": offering.course.code,
        "course_name": offering.course.name, "faculty": offering.faculty.user.name, "section": offering.section,
        "semester": offering.semester.name, "day_of_week": row.day_of_week,
        "start_time": row.start_time.isoformat(), "end_time": row.end_time.isoformat(),
        "room": row.room, "is_active": row.is_active}


@router.get("/class-schedules")
def list_schedules(user: User = Depends(require_roles("admin", "faculty", "student")), db: Session = Depends(get_db)):
    query = db.query(ClassSchedule).join(CourseOffering).filter(ClassSchedule.is_active.is_(True))
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        query = query.filter(CourseOffering.faculty_id == profile.id)
    elif user.role == "student":
        profile = student_profile(db, user)
        query = query.join(Enrollment, Enrollment.course_offering_id == CourseOffering.id).filter(
            Enrollment.student_id == profile.id, Enrollment.status == "active")
    return [schedule_json(row) for row in query.order_by(ClassSchedule.day_of_week, ClassSchedule.start_time).all()]


@router.post("/class-schedules", status_code=201)
def create_schedule(data: ClassScheduleCreate, request: Request,
                    user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, data.course_offering_id)
    if offering is None or not offering.is_active:
        raise HTTPException(status_code=404, detail="Active course offering not found")
    if user.role == "faculty":
        faculty_offering(db, user, offering.id)
    if data.end_time <= data.start_time:
        raise HTTPException(status_code=422, detail="Schedule end time must follow start time")
    candidates = db.query(ClassSchedule).join(CourseOffering).filter(
        ClassSchedule.is_active.is_(True), ClassSchedule.day_of_week == data.day_of_week,
        CourseOffering.semester_id == offering.semester_id,
        ClassSchedule.start_time < data.end_time, ClassSchedule.end_time > data.start_time).all()
    for existing in candidates:
        same_faculty = existing.course_offering.faculty_id == offering.faculty_id
        same_room = bool(data.room and existing.room and data.room.casefold() == existing.room.casefold())
        if same_faculty or same_room:
            raise HTTPException(status_code=409, detail="Faculty or room has a conflicting class schedule")
    row = ClassSchedule(**data.model_dump())
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="class_schedule.create", entity_type="class_schedule", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return schedule_json(row)


@router.delete("/class-schedules/{schedule_id}")
def deactivate_schedule(schedule_id: int, request: Request,
                        user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    row = db.get(ClassSchedule, schedule_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=404, detail="Active schedule not found")
    if user.role == "faculty":
        faculty_offering(db, user, row.course_offering_id)
    row.is_active = False
    audit_event(db, user=user, action="class_schedule.deactivate", entity_type="class_schedule", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "is_active": False}
