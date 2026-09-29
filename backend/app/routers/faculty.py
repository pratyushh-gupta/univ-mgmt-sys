from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..core.security import hash_password
from ..database.connection import get_db
from ..models import AttendanceRecord, AttendanceSession, CourseOffering, Department, Enrollment, ExamSchedule, Faculty, Notification, Result, Student, User
from ..schemas import AttendanceRequest, AttendanceSessionCreate, AttendanceSessionUpdate, FacultyCreate, GradeResultBatch, GradeResultCreate, ResultItem, ResultRequest
from ..services.domain import LOW_ATTENDANCE_THRESHOLD_PERCENT, audit_event, commit_or_conflict, faculty_offering, faculty_profile, grade_for
from ..services.serializers import user_json

router = APIRouter()


def faculty_json(profile: Faculty) -> dict:
    return user_json(profile.user) | {"faculty_id": profile.id, "employee_id": profile.employee_id,
        "department": profile.department.name, "department_id": profile.department_id,
        "designation": profile.designation, "phone": profile.phone}


@router.get("/faculty")
def list_faculty(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [faculty_json(row) for row in db.query(Faculty).filter_by(is_active=True).all()]


@router.post("/faculty", status_code=201)
def create_faculty(data: FacultyCreate, request: Request, actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(User).filter((User.user_id == data.id) | (User.email == str(data.email))).first():
        raise HTTPException(status_code=409, detail="User ID or email address already exists")
    if db.query(Faculty).filter_by(employee_id=data.employee_id).first():
        raise HTTPException(status_code=409, detail="Employee ID already exists")
    if db.get(Department, data.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    user = User(user_id=data.id, name=data.name, email=str(data.email), password_hash=hash_password(data.password), role="faculty")
    db.add(user)
    db.flush()
    profile = Faculty(user_id=user.id, employee_id=data.employee_id, department_id=data.department_id,
                      designation=data.designation, phone=data.phone)
    db.add(profile)
    audit_event(db, user=actor, action="faculty.create", entity_type="faculty", entity_id=data.id, request=request)
    commit_or_conflict(db, "User or faculty profile conflicts with existing data")
    db.refresh(profile)
    return faculty_json(profile)


@router.delete("/faculty/{faculty_id}")
def deactivate_faculty(faculty_id: str, request: Request, actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    profile = db.query(Faculty).join(User).filter(User.user_id == faculty_id, Faculty.is_active.is_(True)).first()
    if profile is None:
        raise HTTPException(status_code=404, detail="Faculty not found")
    profile.is_active = False
    profile.user.is_active = False
    audit_event(db, user=actor, action="faculty.deactivate", entity_type="faculty", entity_id=profile.id, request=request)
    commit_or_conflict(db)
    return {"message": "Faculty deactivated"}


@router.get("/faculty/courses")
def faculty_courses(user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    profile = faculty_profile(db, user)
    offerings = db.query(CourseOffering).filter_by(faculty_id=profile.id).all()
    return [{"id": offering.id, "offering_id": offering.id, "code": offering.course.code,
        "name": offering.course.name, "department": offering.course.department.name,
        "semester": offering.semester.name, "semester_id": offering.semester_id, "section": offering.section,
        "students": db.query(Enrollment).filter_by(course_offering_id=offering.id, status="active").count()}
        for offering in offerings]


def roster_for(offering: CourseOffering, db: Session) -> list[dict]:
    rows = db.query(Student).join(Enrollment).filter(
        Enrollment.course_offering_id == offering.id, Enrollment.status == "active", Student.is_active.is_(True)).all()
    return [{"id": row.user.user_id, "student_id": row.id, "name": row.user.name,
        "enrollment_number": row.enrollment_number} for row in rows]


@router.get("/course-offerings/{offering_id}/roster")
def offering_roster(offering_id: int, user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    return roster_for(faculty_offering(db, user, offering_id), db)


@router.get("/faculty/roster/{course_code}")
def legacy_roster(course_code: str, user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    profile = faculty_profile(db, user)
    offering = db.query(CourseOffering).join(CourseOffering.course).filter(
        CourseOffering.faculty_id == profile.id, CourseOffering.course.has(code=course_code)).first()
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    return roster_for(offering, db)


def save_session_records(offering: CourseOffering, actor: User, request: Request, session_date, start_time,
                         end_time, topic, records, db: Session, status="published", existing_session=None):
    if offering.faculty.user_id != actor.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    if end_time and start_time and end_time <= start_time:
        raise HTTPException(status_code=422, detail="Session end time must follow its start time")
    if status not in {"draft", "published", "closed"}:
        raise HTTPException(status_code=422, detail="Invalid attendance session status")
    student_ids = [record.student_id for record in records]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="Duplicate students are not allowed")
    allowed_statuses = {"present", "absent", "late", "excused"}
    if any(record.status not in allowed_statuses for record in records):
        raise HTTPException(status_code=422, detail="Unsupported attendance status")
    enrolled_ids = db.query(Student.id).join(Enrollment).filter(
        Enrollment.course_offering_id == offering.id, Enrollment.status == "active").all()
    enrolled = {student_id: student_id for (student_id,) in enrolled_ids}
    missing = [student_id for student_id in student_ids if student_id not in enrolled]
    if missing:
        raise HTTPException(status_code=400, detail=f"Student(s) not enrolled in offering: {', '.join(map(str, missing))}")
    faculty = faculty_profile(db, actor)
    attendance_session = existing_session or db.query(AttendanceSession).filter_by(
        course_offering_id=offering.id, session_date=session_date, start_time=start_time).first()
    if attendance_session is None:
        attendance_session = AttendanceSession(course_offering_id=offering.id, faculty_id=faculty.id,
            session_date=session_date, start_time=start_time, end_time=end_time, topic=topic, status=status)
        db.add(attendance_session)
        db.flush()
    else:
        attendance_session.end_time = end_time
        attendance_session.topic = topic
        attendance_session.status = status
    for record in records:
        profile_id = enrolled[record.student_id]
        row = db.query(AttendanceRecord).filter_by(attendance_session_id=attendance_session.id,
            student_id=profile_id).first()
        if row:
            row.status = record.status
            row.marked_at = datetime.now(timezone.utc)
        else:
            db.add(AttendanceRecord(attendance_session_id=attendance_session.id, course_offering_id=offering.id,
                student_id=profile_id, status=record.status))
    db.flush()
    if attendance_session.status == "published":
        for profile_id in set(enrolled.values()):
            stats = db.query(AttendanceRecord.status).join(AttendanceSession,
                AttendanceRecord.attendance_session_id == AttendanceSession.id).filter(
                    AttendanceRecord.student_id == profile_id, AttendanceRecord.course_offering_id == offering.id,
                    AttendanceSession.status == "published", AttendanceRecord.status.in_(("present", "absent", "late"))).all()
            total = len(stats)
            attended = sum(status in {"present", "late"} for (status,) in stats)
            if total and attended / total * 100 < LOW_ATTENDANCE_THRESHOLD_PERCENT:
                profile = db.get(Student, profile_id)
                exists = db.query(Notification.id).filter(Notification.user_id == profile.user_id,
                    Notification.notification_type == "low_attendance", Notification.message.ilike(f"%{offering.course.code}%")).first()
                if exists is None:
                    db.add(Notification(user_id=profile.user_id, title="Low attendance warning",
                        message=f"Your attendance for {offering.course.code} is below {LOW_ATTENDANCE_THRESHOLD_PERCENT}%.",
                        notification_type="low_attendance"))
    audit_event(db, user=actor, action="attendance.save", entity_type="attendance_session",
        entity_id=attendance_session.id, details={"record_count": len(records)}, request=request)
    commit_or_conflict(db, "Attendance session conflicts with a session or record already stored")
    return {"message": "Attendance saved", "attendance_session_id": attendance_session.id}


@router.post("/attendance/sessions", status_code=201)
def create_attendance_session(data: AttendanceSessionCreate, request: Request,
                              user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    offering = faculty_offering(db, user, data.course_offering_id)
    return save_session_records(offering, user, request, data.session_date, data.start_time,
        data.end_time, data.topic, data.records, db, data.status)


@router.put("/attendance/sessions/{session_id}")
def update_attendance_session(session_id: int, data: AttendanceSessionUpdate, request: Request,
                              user: User = Depends(require_roles("faculty", "admin")), db: Session = Depends(get_db)):
    row = db.get(AttendanceSession, session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Attendance session not found")
    offering = db.get(CourseOffering, row.course_offering_id)
    if user.role == "faculty":
        faculty_offering(db, user, offering.id)
    collision = db.query(AttendanceSession).filter(AttendanceSession.course_offering_id == offering.id,
        AttendanceSession.session_date == data.session_date, AttendanceSession.start_time == data.start_time,
        AttendanceSession.id != row.id).first()
    if collision:
        raise HTTPException(status_code=409, detail="Another session already uses this date and start time")
    return save_session_records(offering, user, request, data.session_date, data.start_time, data.end_time,
        data.topic, data.records, db, data.status, row)


@router.post("/attendance")
def save_attendance(data: AttendanceRequest, request: Request,
                    user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    profile = faculty_profile(db, user)
    offering = db.get(CourseOffering, data.course_offering_id) if data.course_offering_id else db.query(CourseOffering).join(
        CourseOffering.course).filter(CourseOffering.faculty_id == profile.id,
        CourseOffering.course.has(code=data.course_code)).first()
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if offering.faculty_id != profile.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    return save_session_records(offering, user, request, data.date, data.start_time, data.end_time, data.topic, data.records, db)


@router.get("/attendance/sessions/{offering_id}")
def attendance_sessions(offering_id: int, user: User = Depends(require_roles("faculty", "admin")), db: Session = Depends(get_db)):
    query = db.query(AttendanceSession).filter_by(course_offering_id=offering_id)
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        if not db.query(CourseOffering).filter_by(id=offering_id, faculty_id=profile.id).first():
            raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    return [{"id": row.id, "course_offering_id": row.course_offering_id, "session_date": row.session_date.isoformat(), "topic": row.topic,
        "status": row.status, "end_time": row.end_time.isoformat() if row.end_time else None,
        "start_time": row.start_time.isoformat() if row.start_time else None,
        "records": [{"student_id": r.student_id, "status": r.status} for r in row.records]} for row in query.order_by(AttendanceSession.session_date.desc()).all()]


@router.get("/course-offerings/{offering_id}/attendance-summary")
def offering_attendance_summary(offering_id: int, user: User = Depends(require_roles("faculty", "admin")),
                                db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, offering_id)
    if offering is None: raise HTTPException(status_code=404, detail="Course offering not found")
    if user.role == "faculty": faculty_offering(db, user, offering_id)
    students = db.query(Student).join(Enrollment).filter(Enrollment.course_offering_id == offering_id,
        Enrollment.status == "active", Student.is_active.is_(True)).order_by(Student.enrollment_number).all()
    summary = []
    for student in students:
        records = db.query(AttendanceRecord.status).join(AttendanceSession,
            AttendanceRecord.attendance_session_id == AttendanceSession.id).filter(
                AttendanceRecord.student_id == student.id, AttendanceSession.course_offering_id == offering_id,
                AttendanceSession.status == "published", AttendanceRecord.status.in_(("present", "absent", "late"))).all()
        total = len(records)
        attended = sum(status in {"present", "late"} for (status,) in records)
        percent = round(attended / total * 100, 2) if total else None
        summary.append({"student_id": student.id, "enrollment_number": student.enrollment_number,
            "name": student.user.name, "total_sessions": total, "attended_sessions": attended,
            "absent_sessions": sum(status == "absent" for (status,) in records), "attendance": percent,
            "low_attendance": percent is not None and percent < LOW_ATTENDANCE_THRESHOLD_PERCENT})
    return {"course_offering_id": offering_id, "threshold_percent": LOW_ATTENDANCE_THRESHOLD_PERCENT,
        "students": summary}


@router.get("/admin/attendance")
def admin_attendance(department_id: int | None = None, semester_id: int | None = None,
                     course_offering_id: int | None = None, faculty_id: int | None = None,
                     student_id: int | None = None, page: int = Query(1, ge=1),
                     page_size: int = Query(50, ge=1, le=200),
                     _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    query = db.query(AttendanceRecord).join(AttendanceSession,
        AttendanceRecord.attendance_session_id == AttendanceSession.id).join(CourseOffering,
        AttendanceRecord.course_offering_id == CourseOffering.id)
    if student_id is not None: query = query.filter(AttendanceRecord.student_id == student_id)
    if course_offering_id is not None: query = query.filter(CourseOffering.id == course_offering_id)
    if faculty_id is not None: query = query.filter(CourseOffering.faculty_id == faculty_id)
    if semester_id is not None: query = query.filter(CourseOffering.semester_id == semester_id)
    if department_id is not None: query = query.join(CourseOffering.course).filter(CourseOffering.course.has(department_id=department_id))
    total = query.count()
    counts = dict(query.with_entities(AttendanceRecord.status, func.count(AttendanceRecord.id)).group_by(AttendanceRecord.status).all())
    valid_total = sum(counts.get(status, 0) for status in ("present", "absent", "late"))
    attended_total = counts.get("present", 0) + counts.get("late", 0)
    rows = query.order_by(AttendanceSession.session_date.desc(), AttendanceRecord.student_id).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [{"id": r.id, "student_id": r.student_id, "student": r.student.user.name,
        "enrollment_number": r.student.enrollment_number, "course_offering_id": r.course_offering_id,
        "course_code": r.session.course_offering.course.code, "course": r.session.course_offering.course.name,
        "faculty_id": r.session.course_offering.faculty_id, "faculty": r.session.course_offering.faculty.user.name,
        "semester_id": r.session.course_offering.semester_id, "session_id": r.attendance_session_id,
        "date": r.session.session_date.isoformat(), "topic": r.session.topic, "session_status": r.session.status, "status": r.status}
        for r in rows], "total": total, "page": page, "page_size": page_size,
        "summary": {"present": counts.get("present", 0), "absent": counts.get("absent", 0),
            "late": counts.get("late", 0), "attendance_percent": round(attended_total / valid_total * 100, 2) if valid_total else None}}


@router.get("/admin/attendance/sessions/{session_id}")
def admin_attendance_session(session_id: int, _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(AttendanceSession, session_id)
    if row is None: raise HTTPException(status_code=404, detail="Attendance session not found")
    return {"id": row.id, "course_offering_id": row.course_offering_id, "course_code": row.course_offering.course.code,
        "session_date": row.session_date.isoformat(), "topic": row.topic, "status": row.status,
        "records": [{"student_id": r.student_id, "student": r.student.user.name, "status": r.status} for r in row.records]}


def save_results_for_offering(offering: CourseOffering, actor: User, request: Request, assessment_name: str, results, db: Session):
    if offering.faculty.user_id != actor.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    student_ids = [item.student_id for item in results]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="Duplicate students are not allowed")
    enrolled = {row[0]: row[1] for row in db.query(User.user_id, Student.id).join(User, User.id == Student.user_id).join(Enrollment).filter(
        Enrollment.course_offering_id == offering.id, Enrollment.status == "active").all()}
    missing = sorted(set(student_ids) - set(enrolled))
    if missing:
        raise HTTPException(status_code=400, detail=f"Student(s) not enrolled in offering: {', '.join(missing)}")
    for item in results:
        if item.marks > item.max_marks:
            raise HTTPException(status_code=422, detail="Marks cannot exceed the assessment maximum")
        grade, points = grade_for(item.marks, item.max_marks)
        row = db.query(Result).filter_by(student_id=enrolled[item.student_id], course_offering_id=offering.id,
            assessment_name=assessment_name).first()
        if row is None:
            row = Result(student_id=enrolled[item.student_id], course_offering_id=offering.id,
                assessment_name=assessment_name, marks=item.marks, max_marks=item.max_marks,
                grade=grade, grade_point=points, status="draft", is_final=getattr(item, "is_final", False))
            db.add(row)
        else:
            row.marks, row.max_marks, row.grade, row.grade_point = item.marks, item.max_marks, grade, points
            row.status, row.published_at, row.published_by = "draft", None, None
            row.is_final = getattr(item, "is_final", False)
    audit_event(db, user=actor, action="results.save", entity_type="result",
        details={"offering_id": offering.id, "assessment_name": assessment_name, "record_count": len(results)}, request=request)
    commit_or_conflict(db, "Result conflicts with a record already stored")
    return {"message": "Results saved as draft"}


@router.post("/results")
def save_results(data: ResultRequest, request: Request,
                 user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    profile = faculty_profile(db, user)
    offering = db.get(CourseOffering, data.course_offering_id) if data.course_offering_id else db.query(CourseOffering).join(
        CourseOffering.course).filter(CourseOffering.faculty_id == profile.id,
        CourseOffering.course.has(code=data.course_code)).first()
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if offering.faculty_id != profile.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    return save_results_for_offering(offering, user, request, data.assessment_name, data.results, db)


@router.get("/results")
def list_results(user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    query = db.query(Result)
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        query = query.filter(Result.course_offering_id.in_(
            db.query(CourseOffering.id).filter_by(faculty_id=profile.id)))
    return [{"id": row.id, "student_id": row.student_id, "student_name": row.student.user.name,
        "course_offering_id": row.course_offering_id, "course_code": row.course_offering.course.code,
        "assessment_name": row.assessment_name, "marks": float(row.marks), "max_marks": float(row.max_marks),
        "grade": row.grade, "grade_point": float(row.grade_point or 0), "status": row.status,
        "is_final": row.is_final, "semester": row.course_offering.semester.name,
        "academic_year": row.course_offering.semester.academic_year.name,
        "credits": row.course_offering.course.credits} for row in query.all()]


@router.post("/results/grade", status_code=201)
def create_result(data: GradeResultCreate, request: Request,
                  user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, data.course_offering_id)
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if user.role == "faculty":
        faculty_offering(db, user, offering.id)
    student = db.get(Student, data.student_id)
    if student is None or not db.query(Enrollment).filter_by(student_id=data.student_id,
            course_offering_id=offering.id, status="active").first():
        raise HTTPException(status_code=400, detail="Student is not actively enrolled in this course offering")
    if data.marks > data.max_marks:
        raise HTTPException(status_code=422, detail="Marks cannot exceed the assessment maximum")
    if data.exam_schedule_id is not None:
        schedule = db.query(ExamSchedule).filter_by(id=data.exam_schedule_id, course_offering_id=offering.id).first()
        if schedule is None:
            raise HTTPException(status_code=422, detail="Exam schedule does not belong to this course offering")
        if data.max_marks > schedule.max_marks:
            raise HTTPException(status_code=422, detail="Maximum marks cannot exceed the scheduled exam maximum")
    grade, points = grade_for(data.marks, data.max_marks)
    row = db.query(Result).filter_by(student_id=student.id, course_offering_id=offering.id,
        assessment_name=data.assessment_name).first()
    if row is None:
        row = Result(student_id=student.id, course_offering_id=offering.id, exam_schedule_id=data.exam_schedule_id,
            assessment_name=data.assessment_name, marks=data.marks, max_marks=data.max_marks,
            grade=grade, grade_point=points, status="draft", is_final=data.is_final)
        db.add(row)
    else:
        row.exam_schedule_id, row.marks, row.max_marks = data.exam_schedule_id, data.marks, data.max_marks
        row.grade, row.grade_point = grade, points
        row.status, row.published_at, row.published_by = "draft", None, None
        row.is_final = data.is_final
    db.flush()
    audit_event(db, user=user, action="results.grade", entity_type="result", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "grade": row.grade, "grade_point": float(row.grade_point), "status": row.status}


@router.post("/results/batch")
def create_result_batch(data: GradeResultBatch, request: Request,
                        user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, data.course_offering_id)
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if user.role == "faculty":
        faculty_offering(db, user, offering.id)
    if len({item.student_id for item in data.results}) != len(data.results):
        raise HTTPException(status_code=400, detail="Duplicate students are not allowed")
    translated = []
    for item in data.results:
        if item.marks > item.max_marks:
            raise HTTPException(status_code=422, detail="Marks cannot exceed the assessment maximum")
        student = db.get(Student, item.student_id)
        if student is None or not db.query(Enrollment).filter_by(student_id=item.student_id,
                course_offering_id=offering.id, status="active").first():
            raise HTTPException(status_code=400, detail=f"Student {item.student_id} is not enrolled in this offering")
        translated.append(ResultItem(student_id=student.user.user_id, marks=item.marks, max_marks=item.max_marks,
            is_final=item.is_final))
    if user.role == "faculty" and offering.faculty_id != faculty_profile(db, user).id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    return save_results_for_offering(offering, user, request, data.assessment_name, translated, db)


@router.post("/results/{result_id}/publish")
def publish_result(result_id: int, request: Request, user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    row = db.get(Result, result_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Result not found")
    if user.role == "faculty":
        faculty_offering(db, user, row.course_offering_id)
    notify_student = row.status != "published"
    row.status, row.published_at, row.published_by = "published", datetime.now(timezone.utc), user.id
    if notify_student:
        db.add(Notification(user_id=row.student.user_id, title="Result published",
            message=f"Your {row.assessment_name} result for {row.course_offering.course.code} is now available.",
            notification_type="result"))
    audit_event(db, user=user, action="results.publish", entity_type="result", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "status": row.status}
