from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..core.security import hash_password
from ..database.connection import get_db
from ..models import AttendanceRecord, AttendanceSession, CourseOffering, Department, Enrollment, ExamSchedule, Faculty, Notification, Result, Student, User
from ..schemas import AttendanceRequest, AttendanceSessionCreate, FacultyCreate, GradeResultBatch, GradeResultCreate, ResultItem, ResultRequest
from ..services.domain import audit_event, commit_or_conflict, faculty_offering, faculty_profile, grade_for
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
        "semester": offering.semester.name, "section": offering.section,
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
                         end_time, topic, records, db: Session):
    if offering.faculty.user_id != actor.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    if end_time and start_time and end_time <= start_time:
        raise HTTPException(status_code=422, detail="Session end time must follow its start time")
    student_ids = [record.student_id for record in records]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="Duplicate students are not allowed")
    allowed_statuses = {"present", "absent", "late", "excused"}
    if any(record.status not in allowed_statuses for record in records):
        raise HTTPException(status_code=422, detail="Unsupported attendance status")
    enrolled = {row[0]: row[1] for row in db.query(Student.user_id, Student.id).join(Enrollment).filter(
        Enrollment.course_offering_id == offering.id, Enrollment.status == "active").all()}
    enrolled_by_profile_id = {profile_id: profile_id for profile_id in enrolled.values()}
    missing = [student_id for student_id in student_ids
        if student_id not in enrolled and student_id not in enrolled_by_profile_id]
    if missing:
        raise HTTPException(status_code=400, detail=f"Student(s) not enrolled in offering: {', '.join(map(str, missing))}")
    faculty = faculty_profile(db, actor)
    attendance_session = db.query(AttendanceSession).filter_by(
        course_offering_id=offering.id, session_date=session_date, start_time=start_time).first()
    if attendance_session is None:
        attendance_session = AttendanceSession(course_offering_id=offering.id, faculty_id=faculty.id,
            session_date=session_date, start_time=start_time, end_time=end_time, topic=topic)
        db.add(attendance_session)
        db.flush()
    else:
        attendance_session.end_time = end_time
        attendance_session.topic = topic
    for record in records:
        profile_id = enrolled.get(record.student_id, enrolled_by_profile_id.get(record.student_id))
        row = db.query(AttendanceRecord).filter_by(attendance_session_id=attendance_session.id,
            student_id=profile_id).first()
        if row:
            row.status = record.status
            row.marked_at = datetime.now(timezone.utc)
        else:
            db.add(AttendanceRecord(attendance_session_id=attendance_session.id, course_offering_id=offering.id,
                student_id=profile_id, status=record.status))
    audit_event(db, user=actor, action="attendance.save", entity_type="attendance_session",
        entity_id=attendance_session.id, details={"record_count": len(records)}, request=request)
    commit_or_conflict(db, "Attendance session conflicts with a session or record already stored")
    return {"message": "Attendance saved", "attendance_session_id": attendance_session.id}


@router.post("/attendance/sessions", status_code=201)
def create_attendance_session(data: AttendanceSessionCreate, request: Request,
                              user: User = Depends(require_roles("faculty")), db: Session = Depends(get_db)):
    offering = faculty_offering(db, user, data.course_offering_id)
    return save_session_records(offering, user, request, data.session_date, data.start_time,
        data.end_time, data.topic, data.records, db)


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
    return [{"id": row.id, "session_date": row.session_date.isoformat(), "topic": row.topic,
        "start_time": row.start_time.isoformat() if row.start_time else None,
        "records": [{"student_id": r.student_id, "status": r.status} for r in row.records]} for row in query.all()]


def save_results_for_offering(offering: CourseOffering, actor: User, request: Request, assessment_name: str, results, db: Session):
    if offering.faculty.user_id != actor.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    student_ids = [item.student_id for item in results]
    if len(student_ids) != len(set(student_ids)):
        raise HTTPException(status_code=400, detail="Duplicate students are not allowed")
    enrolled = {row[0]: row[1] for row in db.query(Student.user_id, Student.id).join(Enrollment).filter(
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
                grade=grade, grade_point=points, status="draft")
            db.add(row)
        else:
            row.marks, row.max_marks, row.grade, row.grade_point = item.marks, item.max_marks, grade, points
            row.status, row.published_at, row.published_by = "draft", None, None
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
        "grade": row.grade, "grade_point": float(row.grade_point or 0), "status": row.status} for row in query.all()]


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
    if data.exam_schedule_id is not None and not db.query(ExamSchedule).filter_by(
            id=data.exam_schedule_id, course_offering_id=offering.id).first():
        raise HTTPException(status_code=422, detail="Exam schedule does not belong to this course offering")
    grade, points = grade_for(data.marks, data.max_marks)
    row = db.query(Result).filter_by(student_id=student.id, course_offering_id=offering.id,
        assessment_name=data.assessment_name).first()
    if row is None:
        row = Result(student_id=student.id, course_offering_id=offering.id, exam_schedule_id=data.exam_schedule_id,
            assessment_name=data.assessment_name, marks=data.marks, max_marks=data.max_marks,
            grade=grade, grade_point=points, status="draft")
        db.add(row)
    else:
        row.exam_schedule_id, row.marks, row.max_marks = data.exam_schedule_id, data.marks, data.max_marks
        row.grade, row.grade_point = grade, points
        row.status, row.published_at, row.published_by = "draft", None, None
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
        translated.append(ResultItem(student_id=student.user.user_id, marks=item.marks, max_marks=item.max_marks))
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
