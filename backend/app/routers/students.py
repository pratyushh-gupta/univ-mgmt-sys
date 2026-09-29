from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..core.security import hash_password
from ..database.connection import get_db
from ..models import Assignment, AttendanceRecord, AttendanceSession, CourseOffering, Department, Enrollment, ExamSchedule, Notification, Notice, Result, Semester, Student, Submission, User
from ..schemas import StudentCreate, StudentUpdate
from ..services.domain import LOW_ATTENDANCE_THRESHOLD_PERCENT, audit_event, commit_or_conflict, student_profile
from ..services.serializers import user_json

router = APIRouter()


def student_json(row: Student) -> dict:
    semester = row.semester
    return user_json(row.user) | {"student_id": row.id, "enrollment_number": row.enrollment_number,
            "department_id": row.department_id, "department": row.department.name,
            "semester_id": row.semester_id, "semester": semester.number if semester else None,
            "semester_name": semester.name if semester else None,
            "academic_year_id": semester.academic_year_id if semester else None,
            "academic_year": semester.academic_year.name if semester else None,
            "admission_year": row.admission_year, "phone": row.phone, "address": row.address,
            "active": row.is_active}


@router.get("/students")
def list_students(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db),
                 search: str | None = None, department_id: int | None = None,
                 admission_year: int | None = None, academic_year_id: int | None = None,
                 semester_id: int | None = None, active_only: bool = True,
                 page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    query = db.query(Student).join(Student.user)
    if active_only:
        query = query.filter(Student.is_active.is_(True), User.is_active.is_(True))
    if department_id:
        query = query.filter(Student.department_id == department_id)
    if admission_year:
        query = query.filter(Student.admission_year == admission_year)
    if semester_id:
        query = query.filter(Student.semester_id == semester_id)
    if academic_year_id:
        query = query.join(Student.semester).filter(Semester.academic_year_id == academic_year_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((User.name.ilike(term)) | (User.email.ilike(term)) |
            (User.user_id.ilike(term)) | (Student.enrollment_number.ilike(term)))
    total = query.count()
    rows = query.order_by(Student.enrollment_number).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [student_json(row) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/students", status_code=201)
def create_student(data: StudentCreate, request: Request, actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(User).filter((User.user_id == data.id) | (User.email == str(data.email))).first():
        raise HTTPException(status_code=409, detail="User ID or email address already exists")
    if db.query(Student).filter_by(enrollment_number=data.enrollment_number).first():
        raise HTTPException(status_code=409, detail="Enrollment number already exists")
    if db.get(Department, data.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    if data.semester_id and db.get(Semester, data.semester_id) is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    user = User(user_id=data.id, name=data.name, email=str(data.email), password_hash=hash_password(data.password), role="student")
    db.add(user)
    db.flush()
    student = Student(user_id=user.id, enrollment_number=data.enrollment_number, department_id=data.department_id,
                      semester_id=data.semester_id, admission_year=data.admission_year, phone=data.phone, address=data.address)
    db.add(student)
    audit_event(db, user=actor, action="student.create", entity_type="student", entity_id=data.id, request=request)
    commit_or_conflict(db, "User or student profile conflicts with existing data")
    db.refresh(student)
    return student_json(student)


@router.delete("/students/{student_id}")
def deactivate_student(student_id: str, request: Request, actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    student = db.query(Student).join(User).filter(User.user_id == student_id, Student.is_active.is_(True)).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    # Deactivate accounts and profiles; preserve enrollments and academic history.
    student.is_active = False
    student.user.is_active = False
    audit_event(db, user=actor, action="student.deactivate", entity_type="student", entity_id=student.id, request=request)
    commit_or_conflict(db)
    return {"message": "Student deactivated"}


@router.get("/students/{student_id}")
def get_student(student_id: str, _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.query(Student).join(User).filter(User.user_id == student_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return student_json(row)


@router.patch("/students/{student_id}")
def update_student(student_id: str, data: StudentUpdate, request: Request,
                   actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.query(Student).join(User).filter(User.user_id == student_id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Student not found")
    changes = data.model_dump(exclude_unset=True)
    if "department_id" in changes and changes["department_id"] is not None and db.get(Department, changes["department_id"]) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    if "semester_id" in changes and changes["semester_id"] is not None:
        semester = db.get(Semester, changes["semester_id"])
        if semester is None:
            raise HTTPException(status_code=404, detail="Semester not found")
    for key, value in changes.items():
        if key == "is_active":
            row.is_active = value
            row.user.is_active = value
        else:
            setattr(row, key, value)
    audit_event(db, user=actor, action="student.update", entity_type="student", entity_id=row.id, request=request)
    commit_or_conflict(db, "Student update conflicts with existing records")
    return student_json(row)


def academic_history(student: Student, db: Session) -> list[dict]:
    rows = db.query(Enrollment).filter_by(student_id=student.id).order_by(Enrollment.enrolled_at.desc()).all()
    history = []
    for enrollment in rows:
        offering = enrollment.course_offering
        results = db.query(Result).filter_by(student_id=student.id, course_offering_id=offering.id).all()
        history.append({"semester": offering.semester.name, "academic_year": offering.semester.academic_year.name,
            "course_code": offering.course.code, "course_name": offering.course.name,
            "credits": offering.course.credits, "section": offering.section, "status": enrollment.status,
            "results": [{"assessment_name": result.assessment_name, "marks": float(result.marks),
                "max_marks": float(result.max_marks), "grade": result.grade, "status": result.status}
                for result in results if result.status == "published"]})
    return history


@router.get("/students/{student_id}/history")
def admin_student_history(student_id: str, _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    student = db.query(Student).join(User).filter(User.user_id == student_id).first()
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return academic_history(student, db)


@router.get("/student/history")
def own_academic_history(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    return academic_history(student_profile(db, user), db)


@router.get("/student/dashboard")
def student_dashboard(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    enrollments = db.query(Enrollment).filter_by(student_id=student.id, status="active").all()
    offering_ids = [row.course_offering_id for row in enrollments]
    attendance = db.query(AttendanceRecord).join(AttendanceSession,
        AttendanceRecord.attendance_session_id == AttendanceSession.id).filter(
            AttendanceRecord.student_id == student.id, AttendanceSession.status == "published",
            AttendanceRecord.status.in_(("present", "absent", "late"))).all()
    attendance_total = len(attendance)
    attendance_present = sum(record.status in {"present", "late"} for record in attendance)
    submitted_ids = select(Submission.assignment_id).filter_by(student_id=student.id)
    pending_assignments = db.query(Assignment).filter(Assignment.course_offering_id.in_(offering_ids or [-1]),
        Assignment.status == "published", Assignment.due_date >= datetime.now(timezone.utc),
        ~Assignment.id.in_(submitted_ids)).count()
    today = date.today()
    upcoming = db.query(ExamSchedule).filter(ExamSchedule.course_offering_id.in_(offering_ids or [-1]),
        ExamSchedule.exam_date >= today).order_by(ExamSchedule.exam_date).limit(5).all()
    recent_results = db.query(Result).filter_by(student_id=student.id, status="published")\
        .order_by(Result.published_at.desc()).limit(5).all()
    unread = db.query(Notification).filter_by(user_id=user.id, is_read=False).count()
    semester = student.semester
    return {
        "student": student_json(student),
        "current_academic_year": semester.academic_year.name if semester else None,
        "current_semester": semester.name if semester else None,
        "enrolled_course_count": len(enrollments),
        "attendance_summary": {"present": attendance_present, "total": attendance_total,
                               "percentage": round(attendance_present / attendance_total * 100) if attendance_total else 0},
        "pending_assignments": pending_assignments,
        "upcoming_exams": [{"name": row.exam.name, "course_code": row.course_offering.course.code,
            "exam_date": row.exam_date.isoformat(), "start_time": row.start_time.isoformat(), "room": row.room}
            for row in upcoming],
        "recent_results": [{"course_code": row.course_offering.course.code, "assessment_name": row.assessment_name,
            "marks": float(row.marks), "max_marks": float(row.max_marks), "grade": row.grade}
            for row in recent_results],
        "unread_notifications": unread,
    }


@router.get("/student/profile")
def own_student_profile(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    profile = student_profile(db, user)
    return user_json(user) | {"enrollment_number": profile.enrollment_number, "admission_year": profile.admission_year,
        "department": profile.department.name, "department_id": profile.department_id,
        "semester": profile.semester.number if profile.semester else None,
        "semester_name": profile.semester.name if profile.semester else None,
        "academic_year": profile.semester.academic_year.name if profile.semester else None,
        "phone": profile.phone, "address": profile.address}


@router.get("/student/courses")
def student_courses(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    profile = student_profile(db, user)
    rows = db.query(Enrollment, CourseOffering).join(CourseOffering).filter(
        Enrollment.student_id == profile.id, Enrollment.status == "active").all()
    output = []
    for enrollment, offering in rows:
        total = db.query(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceRecord.student_id == profile.id, AttendanceSession.course_offering_id == offering.id,
            AttendanceSession.status == "published", AttendanceRecord.status.in_(("present", "absent", "late"))).count()
        present = db.query(AttendanceRecord).join(AttendanceSession).filter(
            AttendanceRecord.student_id == profile.id, AttendanceSession.course_offering_id == offering.id,
            AttendanceSession.status == "published", AttendanceRecord.status.in_(("present", "late"))).count()
        output.append({"id": offering.id, "code": offering.course.code, "name": offering.course.name,
            "faculty": offering.faculty.user.name, "department": offering.course.department.name,
            "semester": offering.semester.name, "section": offering.section,
            "attendance": round(present / total * 100) if total else 0})
    return output


@router.get("/student/attendance")
def student_attendance(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    profile = student_profile(db, user)
    enrollments = db.query(Enrollment).join(CourseOffering).filter(
        Enrollment.student_id == profile.id, Enrollment.status.in_(("active", "completed"))).all()
    courses, semesters = [], {}
    for enrollment in enrollments:
        offering = enrollment.course_offering
        records = db.query(AttendanceRecord).join(AttendanceSession,
            AttendanceRecord.attendance_session_id == AttendanceSession.id).filter(
                AttendanceRecord.student_id == profile.id, AttendanceRecord.course_offering_id == offering.id,
                AttendanceSession.status == "published", AttendanceRecord.status.in_(("present", "absent", "late"))).all()
        total = len(records)
        attended = sum(record.status in {"present", "late"} for record in records)
        absent = sum(record.status == "absent" for record in records)
        percent = round(attended / total * 100, 2) if total else None
        item = {"id": offering.id, "course_offering_id": offering.id, "code": offering.course.code,
            "name": offering.course.name, "semester": offering.semester.name,
            "academic_year": offering.semester.academic_year.name, "total_sessions": total,
            "attended_sessions": attended, "absent_sessions": absent, "attendance": percent,
            "low_attendance": percent is not None and percent < LOW_ATTENDANCE_THRESHOLD_PERCENT}
        courses.append(item)
        key = (offering.semester_id, offering.semester.name, offering.semester.academic_year.name)
        accumulator = semesters.setdefault(key, {"total": 0, "attended": 0, "absent": 0})
        accumulator["total"] += total
        accumulator["attended"] += attended
        accumulator["absent"] += absent
    total = sum(item["total_sessions"] for item in courses)
    attended = sum(item["attended_sessions"] for item in courses)
    semester_summaries = []
    for (semester_id, name, year), counts in sorted(semesters.items()):
        percent = round(counts["attended"] / counts["total"] * 100, 2) if counts["total"] else None
        semester_summaries.append({"semester_id": semester_id, "semester": name, "academic_year": year,
            "total_sessions": counts["total"], "attended_sessions": counts["attended"],
            "absent_sessions": counts["absent"], "attendance": percent,
            "low_attendance": percent is not None and percent < LOW_ATTENDANCE_THRESHOLD_PERCENT})
    overall = round(attended / total * 100, 2) if total else None
    return {"overall": overall, "threshold_percent": LOW_ATTENDANCE_THRESHOLD_PERCENT,
        "total_sessions": total, "attended_sessions": attended, "absent_sessions": sum(c["absent_sessions"] for c in courses),
        "low_attendance": overall is not None and overall < LOW_ATTENDANCE_THRESHOLD_PERCENT,
        "courses": courses, "semesters": semester_summaries}


@router.get("/student/results")
def student_results(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    profile = student_profile(db, user)
    rows = db.query(Result).filter_by(student_id=profile.id, status="published").order_by(Result.published_at.desc()).all()
    final_by_offering = {}
    for row in rows:
        if row.is_final and row.grade_point is not None and row.max_marks > 0 and row.marks >= 0 and row.marks <= row.max_marks:
            final_by_offering.setdefault(row.course_offering_id, row)
    by_semester = {}
    credits_total = points_total = 0
    for row in final_by_offering.values():
        semester = row.course_offering.semester
        item = by_semester.setdefault(semester.id, {"semester_id": semester.id, "semester": semester.name,
            "academic_year": semester.academic_year.name, "credits": 0, "weighted_points": 0})
        credits = row.course_offering.course.credits
        item["credits"] += credits
        item["weighted_points"] += float(row.grade_point) * credits
        credits_total += credits
        points_total += float(row.grade_point) * credits
    semester_results = [{**item, "sgpa": round(item["weighted_points"] / item["credits"], 2) if item["credits"] else None}
        for item in sorted(by_semester.values(), key=lambda value: (value["academic_year"], value["semester"]))]
    return {"cgpa": round(points_total / credits_total, 2) if credits_total else None,
        "sgpa_by_semester": semester_results,
        "results": [{"course_offering_id": row.course_offering_id,
            "semester": row.course_offering.semester.name, "academic_year": row.course_offering.semester.academic_year.name,
            "subject": row.course_offering.course.name, "course_code": row.course_offering.course.code,
            "assessment": row.assessment_name, "is_final": row.is_final, "grade": row.grade,
            "point": float(row.grade_point) if row.grade_point is not None else None, "marks": float(row.marks),
            "max_marks": float(row.max_marks), "credits": row.course_offering.course.credits} for row in rows]}


@router.get("/student/assignments")
def student_assignments(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    profile = student_profile(db, user)
    rows = db.query(Assignment, Enrollment).join(Enrollment, Enrollment.course_offering_id == Assignment.course_offering_id).filter(
        Enrollment.student_id == profile.id, Enrollment.status == "active", Assignment.status == "published").all()
    result = []
    now = datetime.now(timezone.utc)
    for assignment, _ in rows:
        submission = db.query(Submission).filter(
            Submission.assignment_id == assignment.id, Submission.student_id == profile.id,
            ).first()
        result.append({"id": assignment.id, "title": assignment.title, "subject": assignment.course_offering.course.name,
            "course_code": assignment.course_offering.course.code,
            "published_at": assignment.published_at.isoformat() if assignment.published_at else None,
            "due": assignment.due_date.isoformat(), "status": submission.status if submission else "not_submitted",
            "max_marks": float(assignment.max_marks), "marks": float(submission.marks) if submission and submission.marks is not None else None,
            "feedback": submission.feedback if submission else None,
            "text_content": submission.text_content if submission else None,
            "late": bool(submission and submission.status == "late" or not submission and assignment.due_date < now)})
    return result
