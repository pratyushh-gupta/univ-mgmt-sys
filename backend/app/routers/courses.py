from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import AcademicYear, Course, CourseOffering, Department, Enrollment, Faculty, Notification, Semester, Student, User
from ..schemas import AcademicYearCreate, BulkEnrollmentCreate, CourseCreate, CourseOfferingCreate, CourseUpdate, DepartmentCreate, EnrollmentCreate, OfferingUpdate, SemesterCreate, StudentEnrollmentCreate
from ..services.domain import audit_event, commit_or_conflict, faculty_profile, student_profile

router = APIRouter()


@router.get("/departments")
def departments(db: Session = Depends(get_db)):
    return [{"id": row.id, "name": row.name, "code": row.code, "description": row.description}
        for row in db.query(Department).order_by(Department.name).all()]


@router.post("/departments", status_code=201)
def create_department(data: DepartmentCreate, request: Request,
                      user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = Department(name=data.name.strip(), code=data.code.strip().upper(), description=data.description)
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="department.create", entity_type="department", entity_id=row.id, request=request)
    commit_or_conflict(db, "Department code or name already exists")
    return {"id": row.id, "name": row.name, "code": row.code, "description": row.description}


@router.delete("/departments/{department_id}")
def delete_department(department_id: int, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(Department, department_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Department not found")
    db.delete(row)
    commit_or_conflict(db, "Department is still referenced and cannot be deleted")
    return {"message": "Department removed"}


@router.get("/academic-years")
def academic_years(db: Session = Depends(get_db)):
    return [{"id": row.id, "name": row.name, "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(), "is_active": row.is_active} for row in db.query(AcademicYear).all()]


@router.post("/academic-years", status_code=201)
def create_academic_year(data: AcademicYearCreate, request: Request,
                         user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.end_date <= data.start_date:
        raise HTTPException(status_code=422, detail="Academic year end date must follow its start date")
    row = AcademicYear(**data.model_dump())
    if row.is_active:
        db.query(AcademicYear).update({AcademicYear.is_active: False})
        db.query(Semester).update({Semester.is_active: False})
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="academic_year.create", entity_type="academic_year", entity_id=row.id, request=request)
    commit_or_conflict(db, "Academic year already exists")
    return {"id": row.id, "name": row.name, "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "is_active": row.is_active}


@router.get("/semesters")
def semesters(db: Session = Depends(get_db)):
    return [{"id": row.id, "academic_year_id": row.academic_year_id, "academic_year": row.academic_year.name,
        "name": row.name, "number": row.number, "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat(), "is_active": row.is_active} for row in db.query(Semester).all()]


@router.post("/semesters", status_code=201)
def create_semester(data: SemesterCreate, request: Request,
                    user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    year = db.get(AcademicYear, data.academic_year_id)
    if year is None:
        raise HTTPException(status_code=404, detail="Academic year not found")
    if data.end_date <= data.start_date or data.start_date < year.start_date or data.end_date > year.end_date:
        raise HTTPException(status_code=422, detail="Semester dates must be valid and within the academic year")
    row = Semester(**data.model_dump())
    if row.is_active:
        db.query(Semester).update({Semester.is_active: False})
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="semester.create", entity_type="semester", entity_id=row.id, request=request)
    commit_or_conflict(db, "Semester name or number already exists for this academic year")
    return {"id": row.id, "academic_year_id": row.academic_year_id, "name": row.name, "number": row.number,
        "start_date": row.start_date.isoformat(), "end_date": row.end_date.isoformat(), "is_active": row.is_active}


def course_json(course: Course, db: Session) -> dict:
    return {"id": course.id, "code": course.code, "name": course.name, "description": course.description,
        "credits": course.credits, "department_id": course.department_id, "department": course.department.name,
        "enrolled": db.query(Enrollment).join(CourseOffering).filter(
            CourseOffering.course_id == course.id, Enrollment.status == "active").count()}


@router.get("/courses")
def list_courses(search: str | None = None, department_id: int | None = None,
                 active_only: bool = True, page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
                 db: Session = Depends(get_db)):
    query = db.query(Course)
    if active_only:
        query = query.filter_by(is_active=True)
    if department_id:
        query = query.filter_by(department_id=department_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((Course.code.ilike(term)) | (Course.name.ilike(term)))
    total = query.count()
    rows = query.order_by(Course.code).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [course_json(row, db) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/courses", status_code=201)
def create_course(data: CourseCreate, request: Request,
                  user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.get(Department, data.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    row = Course(**data.model_dump())
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="course.create", entity_type="course", entity_id=row.id, request=request)
    commit_or_conflict(db, "Course code already exists")
    db.refresh(row)
    return course_json(row, db)


@router.get("/courses/{course_id}")
def get_course(course_id: int, db: Session = Depends(get_db)):
    row = db.get(Course, course_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course_json(row, db)


@router.patch("/courses/{course_id}")
def update_course(course_id: int, data: CourseUpdate, request: Request,
                  user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(Course, course_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    updates = data.model_dump(exclude_unset=True)
    if updates.get("department_id") not in (None, row.department_id) and row.offerings:
        raise HTTPException(status_code=409, detail="Course department cannot change after offerings have been created")
    if updates.get("department_id") is not None and db.get(Department, updates["department_id"]) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    for key, value in updates.items():
        setattr(row, key, value)
    audit_event(db, user=user, action="course.update", entity_type="course", entity_id=row.id, request=request)
    commit_or_conflict(db, "Course update conflicts with existing academic records")
    return course_json(row, db)


@router.delete("/courses/{code}")
def deactivate_course(code: str, request: Request, user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.query(Course).filter_by(code=code, is_active=True).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Course not found")
    row.is_active = False
    audit_event(db, user=user, action="course.deactivate", entity_type="course", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"message": "Course deactivated"}


def offering_json(row: CourseOffering, db: Session) -> dict:
    return {"id": row.id, "course_id": row.course_id, "code": row.course.code, "name": row.course.name,
        "faculty_id": row.faculty_id, "faculty": row.faculty.user.name, "semester_id": row.semester_id,
        "semester": row.semester.name, "section": row.section, "capacity": row.capacity, "room": row.room,
        "department_id": row.course.department_id, "department": row.course.department.name,
        "students": db.query(Enrollment).filter_by(course_offering_id=row.id, status="active").count(),
        "is_active": row.is_active}


@router.get("/course-offerings")
def list_offerings(user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db),
                   search: str | None = None, department_id: int | None = None, semester_id: int | None = None,
                   academic_year_id: int | None = None, active_only: bool = True,
                   page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    query = db.query(CourseOffering)
    if active_only:
        query = query.filter_by(is_active=True)
    if department_id or search:
        query = query.join(CourseOffering.course)
        if department_id:
            query = query.filter(Course.department_id == department_id)
        if search:
            term = f"%{search.strip()}%"
            query = query.filter((Course.code.ilike(term)) | (Course.name.ilike(term)))
    if semester_id:
        query = query.filter(CourseOffering.semester_id == semester_id)
    if academic_year_id:
        query = query.join(CourseOffering.semester).filter(Semester.academic_year_id == academic_year_id)
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        query = query.filter_by(faculty_id=profile.id)
    total = query.count()
    rows = query.order_by(CourseOffering.id).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [offering_json(row, db) for row in rows], "total": total, "page": page, "page_size": page_size}


@router.post("/course-offerings", status_code=201)
def create_offering(data: CourseOfferingCreate, request: Request,
                    user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    course, faculty, semester = db.get(Course, data.course_id), db.get(Faculty, data.faculty_id), db.get(Semester, data.semester_id)
    if course is None or not course.is_active:
        raise HTTPException(status_code=404, detail="Active course not found")
    if faculty is None or not faculty.is_active:
        raise HTTPException(status_code=404, detail="Active faculty profile not found")
    if semester is None:
        raise HTTPException(status_code=404, detail="Semester not found")
    if course.department_id != faculty.department_id:
        raise HTTPException(status_code=422, detail="Faculty and course must belong to the same department")
    row = CourseOffering(**data.model_dump())
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="course_offering.create", entity_type="course_offering", entity_id=row.id, request=request)
    commit_or_conflict(db, "This course offering already exists")
    return offering_json(row, db)


@router.patch("/course-offerings/{offering_id}")
def update_offering(offering_id: int, data: OfferingUpdate, request: Request,
                    user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(CourseOffering, offering_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    updates = data.model_dump(exclude_unset=True)
    faculty_id = updates.get("faculty_id", row.faculty_id)
    semester_id = updates.get("semester_id", row.semester_id)
    faculty = db.get(Faculty, faculty_id)
    semester = db.get(Semester, semester_id)
    if faculty is None or not faculty.is_active or semester is None:
        raise HTTPException(status_code=422, detail="An active faculty profile and valid semester are required")
    if faculty.department_id != row.course.department_id:
        raise HTTPException(status_code=422, detail="Faculty and course must belong to the same department")
    if "capacity" in updates and updates["capacity"] is not None:
        enrolled_count = db.query(Enrollment).filter_by(course_offering_id=row.id, status="active").count()
        if updates["capacity"] < enrolled_count:
            raise HTTPException(status_code=409, detail="Capacity cannot be lower than current enrollment")
    for key, value in updates.items():
        setattr(row, key, value)
    audit_event(db, user=user, action="course_offering.update", entity_type="course_offering", entity_id=row.id, request=request)
    commit_or_conflict(db, "Course offering conflicts with existing schedules or enrollments")
    return offering_json(row, db)


@router.get("/course-offerings/{offering_id}/students")
def offering_students(offering_id: int, user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, offering_id)
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if user.role == "faculty" and offering.faculty.user_id != user.id:
        raise HTTPException(status_code=403, detail="You are not assigned to this offering")
    rows = db.query(Enrollment).filter_by(course_offering_id=offering_id).order_by(Enrollment.enrolled_at.desc()).all()
    return [{"enrollment_id": row.id, "student_id": row.student_id, "user_id": row.student.user.user_id,
             "name": row.student.user.name, "enrollment_number": row.student.enrollment_number, "status": row.status}
            for row in rows]


@router.get("/enrollments")
def list_enrollments(user: User = Depends(require_roles("admin", "student", "faculty")), db: Session = Depends(get_db),
                     student_id: int | None = None, offering_id: int | None = None,
                     status: str | None = None, search: str | None = None,
                     page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    query = db.query(Enrollment)
    if user.role == "student":
        query = query.filter_by(student_id=student_profile(db, user).id)
    elif user.role == "faculty":
        query = query.join(CourseOffering).filter(CourseOffering.faculty_id == faculty_profile(db, user).id)
    elif student_id:
        query = query.filter_by(student_id=student_id)
    if offering_id:
        query = query.filter_by(course_offering_id=offering_id)
    if status:
        query = query.filter_by(status=status)
    if search:
        term = f"%{search.strip()}%"
        query = query.join(Enrollment.student).join(Student.user).filter(
            Student.enrollment_number.ilike(term) | User.name.ilike(term) | User.user_id.ilike(term))
    total = query.count()
    rows = query.order_by(Enrollment.enrolled_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": row.id, "student_id": row.student_id, "student": row.student.user.name,
        "course_offering_id": row.course_offering_id, "course_code": row.course_offering.course.code,
        "status": row.status, "enrolled_at": row.enrolled_at.isoformat()} for row in rows],
        "total": total, "page": page, "page_size": page_size}


@router.post("/enrollments", status_code=201)
def create_enrollment(data: EnrollmentCreate, request: Request,
                      user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    student = db.get(Student, data.student_id)
    offering = db.query(CourseOffering).filter_by(id=data.course_offering_id).with_for_update().first()
    if student is None or not student.is_active or not student.user.is_active:
        raise HTTPException(status_code=404, detail="Active student profile not found")
    if offering is None or not offering.course.is_active:
        raise HTTPException(status_code=404, detail="Active course offering not found")
    if student.department_id != offering.course.department_id:
        raise HTTPException(status_code=422, detail="Student and course offering must belong to the same department")
    if student.semester_id != offering.semester_id:
        raise HTTPException(status_code=422, detail="Student and course offering must belong to the same current semester")
    if not offering.is_active:
        raise HTTPException(status_code=409, detail="This course offering is closed")
    if offering.capacity and db.query(Enrollment).filter_by(course_offering_id=offering.id, status="active").count() >= offering.capacity:
        raise HTTPException(status_code=409, detail="Course offering is at capacity")
    row = db.query(Enrollment).filter_by(student_id=student.id, course_offering_id=offering.id).first()
    if row and row.status in {"active", "completed"}:
        raise HTTPException(status_code=409, detail="Student already has an active or completed enrollment")
    if row:
        row.status = "active"
    else:
        row = Enrollment(student_id=student.id, course_offering_id=offering.id)
        db.add(row)
    db.flush()
    audit_event(db, user=user, action="enrollment.create", entity_type="enrollment", entity_id=row.id, request=request)
    db.add(Notification(user_id=student.user_id, title="Enrollment successful",
        message=f"You are enrolled in {offering.course.code} — {offering.course.name}.", notification_type="enrollment"))
    commit_or_conflict(db, "Student is already enrolled in this course offering")
    return {"id": row.id, "student_id": row.student_id, "course_offering_id": row.course_offering_id, "status": row.status}


@router.post("/enrollments/bulk", status_code=201)
def bulk_enroll(data: BulkEnrollmentCreate, request: Request,
                user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    offering = db.query(CourseOffering).filter_by(id=data.course_offering_id).with_for_update().first()
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    if not offering.is_active:
        raise HTTPException(status_code=409, detail="This course offering is closed")
    unique_ids = list(dict.fromkeys(data.student_ids))
    students = db.query(Student).filter(Student.id.in_(unique_ids), Student.is_active.is_(True),
        Student.user.has(is_active=True)).all()
    if len(students) != len(unique_ids):
        raise HTTPException(status_code=422, detail="Every student must exist and be active")
    if any(student.department_id != offering.course.department_id for student in students):
        raise HTTPException(status_code=422, detail="Students and course offering must belong to the same department")
    if any(student.semester_id != offering.semester_id for student in students):
        raise HTTPException(status_code=422, detail="Every student must be assigned to the offering's current semester")
    existing_rows = db.query(Enrollment).filter(Enrollment.course_offering_id == offering.id,
        Enrollment.student_id.in_(unique_ids)).all()
    if any(row.status in {"active", "completed"} for row in existing_rows):
        raise HTTPException(status_code=409, detail="One or more students are already enrolled")
    active_count = db.query(Enrollment).filter_by(course_offering_id=offering.id, status="active").count()
    reactivations = [row for row in existing_rows if row.status in {"dropped", "withdrawn"}]
    already_recorded = {row.student_id for row in existing_rows}
    new_students = [student for student in students if student.id not in already_recorded]
    if offering.capacity is not None and active_count + len(reactivations) + len(new_students) > offering.capacity:
        raise HTTPException(status_code=409, detail="Course offering does not have enough available seats")
    for row in reactivations:
        row.status = "active"
    rows = [Enrollment(student_id=student.id, course_offering_id=offering.id) for student in new_students]
    db.add_all(rows)
    db.flush()
    for row in [*reactivations, *rows]:
        audit_event(db, user=user, action="enrollment.create", entity_type="enrollment", entity_id=row.id, request=request)
        db.add(Notification(user_id=row.student.user_id, title="Enrollment successful",
                            message=f"You are enrolled in {offering.course.code} — {offering.course.name}.",
                            notification_type="enrollment"))
    commit_or_conflict(db, "One or more enrollments conflict with existing records")
    all_rows = [*reactivations, *rows]
    return {"created": len(all_rows), "enrollment_ids": [row.id for row in all_rows]}


@router.delete("/enrollments/{enrollment_id}")
def withdraw_enrollment(enrollment_id: int, request: Request,
                        user: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(Enrollment, enrollment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Enrollment not found")
    if row.status != "active":
        raise HTTPException(status_code=409, detail="Only active enrollments can be dropped")
    row.status = "dropped"
    db.add(Notification(user_id=row.student.user_id, title="Course dropped",
        message=f"Your enrollment in {row.course_offering.course.code} was dropped.", notification_type="enrollment"))
    audit_event(db, user=user, action="enrollment.withdraw", entity_type="enrollment", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "status": row.status}


@router.get("/student/course-offerings")
def available_offerings(user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    if student.semester_id is None:
        return {"academic_year": None, "semester": None, "items": []}
    semester = db.get(Semester, student.semester_id)
    rows = db.query(CourseOffering).join(CourseOffering.course).filter(
        CourseOffering.semester_id == semester.id, Course.department_id == student.department_id).all()
    items = []
    for row in rows:
        active_count = db.query(Enrollment).filter_by(course_offering_id=row.id, status="active").count()
        enrollment = db.query(Enrollment).filter_by(student_id=student.id, course_offering_id=row.id).first()
        items.append({"id": row.id, "course_id": row.course_id, "code": row.course.code, "name": row.course.name,
            "credits": row.course.credits, "faculty": row.faculty.user.name, "section": row.section,
            "academic_year": semester.academic_year.name, "semester": semester.name,
            "capacity": row.capacity, "enrolled": active_count,
            "available_seats": max(row.capacity - active_count, 0) if row.capacity is not None else None,
            "enrollment_status": enrollment.status if enrollment else None,
            "enrollment_id": enrollment.id if enrollment else None,
            "is_full": row.capacity is not None and active_count >= row.capacity,
            "is_closed": not row.is_active or not row.course.is_active})
    return {"academic_year": semester.academic_year.name, "semester": semester.name, "items": items}


@router.post("/student/enrollments", status_code=201)
def student_enroll(data: StudentEnrollmentCreate, request: Request,
                   user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    offering = db.query(CourseOffering).filter_by(id=data.course_offering_id).with_for_update().first()
    if not student.is_active:
        raise HTTPException(status_code=403, detail="Inactive students cannot enroll")
    if offering is None or not offering.is_active or not offering.course.is_active:
        raise HTTPException(status_code=409, detail="Course offering is unavailable")
    if student.semester_id != offering.semester_id:
        raise HTTPException(status_code=422, detail="Offering is not in your current semester")
    if student.department_id != offering.course.department_id:
        raise HTTPException(status_code=422, detail="Offering is outside your department")
    enrollment = db.query(Enrollment).filter_by(student_id=student.id, course_offering_id=offering.id).first()
    if enrollment and enrollment.status in {"active", "completed"}:
        raise HTTPException(status_code=409, detail="You already have an active or completed enrollment")
    count = db.query(Enrollment).filter_by(course_offering_id=offering.id, status="active").count()
    if offering.capacity is not None and count >= offering.capacity:
        raise HTTPException(status_code=409, detail="Course offering is full")
    if enrollment:
        enrollment.status = "active"
    else:
        enrollment = Enrollment(student_id=student.id, course_offering_id=offering.id)
        db.add(enrollment)
    db.flush()
    audit_event(db, user=user, action="enrollment.create", entity_type="enrollment", entity_id=enrollment.id, request=request)
    db.add(Notification(user_id=user.id, title="Enrollment successful",
                        message=f"You are enrolled in {offering.course.code} — {offering.course.name}.",
                        notification_type="enrollment"))
    commit_or_conflict(db, "Enrollment conflicts with an existing record")
    return {"id": enrollment.id, "status": enrollment.status}


@router.delete("/student/enrollments/{enrollment_id}")
def student_drop(enrollment_id: int, request: Request,
                 user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    row = db.query(Enrollment).filter_by(id=enrollment_id, student_id=student.id, status="active").first()
    if row is None:
        raise HTTPException(status_code=404, detail="Active enrollment not found")
    row.status = "dropped"
    audit_event(db, user=user, action="enrollment.drop", entity_type="enrollment", entity_id=row.id, request=request)
    db.add(Notification(user_id=user.id, title="Course dropped",
        message=f"Your enrollment in {row.course_offering.course.code} was dropped.", notification_type="enrollment"))
    commit_or_conflict(db)
    return {"id": row.id, "status": row.status}
