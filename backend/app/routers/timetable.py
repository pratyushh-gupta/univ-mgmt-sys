from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import ClassSchedule, CourseOffering, Enrollment, Semester, User
from ..schemas import ClassScheduleCreate, ClassScheduleUpdate
from ..services.domain import audit_event, commit_or_conflict, faculty_offering, faculty_profile, student_profile

router = APIRouter()


def validate_no_conflicts(db: Session, offering: CourseOffering, day: int, start_time, end_time,
                          room: str | None, exclude_id: int | None = None) -> None:
    if end_time <= start_time:
        raise HTTPException(status_code=422, detail="Schedule end time must follow start time")
    query = db.query(ClassSchedule).join(CourseOffering).filter(
        ClassSchedule.is_active.is_(True), ClassSchedule.day_of_week == day,
        ClassSchedule.start_time < end_time, ClassSchedule.end_time > start_time)
    query = query.join(Semester, Semester.id == CourseOffering.semester_id).filter(
        Semester.start_date <= offering.semester.end_date, Semester.end_date >= offering.semester.start_date)
    if exclude_id is not None: query = query.filter(ClassSchedule.id != exclude_id)
    my_students = db.query(Enrollment.student_id).filter_by(course_offering_id=offering.id, status="active")
    for existing in query.all():
        other = existing.course_offering
        same_faculty = other.faculty_id == offering.faculty_id
        same_room = bool(room and existing.room and room.strip().casefold() == existing.room.strip().casefold())
        same_cohort = db.query(Enrollment.id).filter(Enrollment.course_offering_id == other.id,
            Enrollment.status == "active", Enrollment.student_id.in_(my_students)).first() is not None
        if same_faculty or same_room or same_cohort:
            raise HTTPException(status_code=409, detail="Faculty, room, or enrolled student cohort has a conflicting class schedule")


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
    validate_no_conflicts(db, offering, data.day_of_week, data.start_time, data.end_time, data.room)
    row = ClassSchedule(**data.model_dump())
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="class_schedule.create", entity_type="class_schedule", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return schedule_json(row)


@router.patch("/class-schedules/{schedule_id}")
def update_schedule(schedule_id: int, data: ClassScheduleUpdate, request: Request,
                    user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    row = db.get(ClassSchedule, schedule_id)
    if row is None or not row.is_active:
        raise HTTPException(status_code=404, detail="Active schedule not found")
    if user.role == "faculty": faculty_offering(db, user, row.course_offering_id)
    changes = data.model_dump(exclude_unset=True)
    proposed_offering = db.get(CourseOffering, changes.get("course_offering_id", row.course_offering_id))
    if proposed_offering is None or not proposed_offering.is_active:
        raise HTTPException(status_code=404, detail="Active course offering not found")
    if user.role == "faculty": faculty_offering(db, user, proposed_offering.id)
    proposed = {"day": changes.get("day_of_week", row.day_of_week),
        "start_time": changes.get("start_time", row.start_time), "end_time": changes.get("end_time", row.end_time),
        "room": changes.get("room", row.room)}
    validate_no_conflicts(db, proposed_offering, **proposed, exclude_id=row.id)
    for key, value in changes.items(): setattr(row, key, value)
    audit_event(db, user=user, action="class_schedule.update", entity_type="class_schedule", entity_id=row.id, request=request)
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
