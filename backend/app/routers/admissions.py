from datetime import datetime, timezone
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..core.security import hash_password
from ..database.connection import get_db
from ..models import AcademicYear, AdmissionApplication, AuditLog, Department, Notification, Semester, Student, User
from ..schemas import AdmissionCreate, AdmissionReview
from ..services.domain import audit_event, commit_or_conflict

router = APIRouter()


def application_json(row: AdmissionApplication) -> dict:
    return {
        "id": row.id, "applicant_name": row.applicant_name, "email": row.email,
        "phone": row.phone, "date_of_birth": row.date_of_birth.isoformat() if row.date_of_birth else None,
        "address": row.address, "department_id": row.department_id, "department": row.department.name,
        "academic_year_id": row.academic_year_id, "academic_year": row.academic_year.name,
        "intended_program": row.intended_program, "status": row.status,
        "submitted_at": row.submitted_at.isoformat(),
        "reviewed_at": row.reviewed_at.isoformat() if row.reviewed_at else None,
        "reviewed_by": row.reviewed_by, "rejection_reason": row.rejection_reason,
        "student_id": row.student_id,
    }


@router.get("/admin/admissions")
def list_admissions(
    status: str | None = None, department_id: int | None = None,
    search: str | None = None, page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    _: User = Depends(require_roles("admin")), db: Session = Depends(get_db),
):
    query = db.query(AdmissionApplication)
    if status:
        query = query.filter(AdmissionApplication.status == status)
    if department_id:
        query = query.filter(AdmissionApplication.department_id == department_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter((AdmissionApplication.applicant_name.ilike(term)) | (AdmissionApplication.email.ilike(term)))
    total = query.count()
    rows = query.order_by(AdmissionApplication.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [application_json(row) for row in rows], "total": total, "page": page,
            "page_size": page_size, "pages": ceil(total / page_size) if total else 0}


@router.post("/admin/admissions", status_code=201)
def create_admission(data: AdmissionCreate, request: Request,
                     actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.get(Department, data.department_id) is None or db.get(AcademicYear, data.academic_year_id) is None:
        raise HTTPException(status_code=404, detail="Department or academic year not found")
    values = data.model_dump()
    values["email"] = str(data.email)
    row = AdmissionApplication(**values)
    db.add(row)
    db.flush()
    audit_event(db, user=actor, action="admission.create", entity_type="admission", entity_id=row.id, request=request)
    commit_or_conflict(db, "Admission application could not be created")
    return application_json(row)


@router.get("/admin/admissions/{application_id}")
def get_admission(application_id: int, _: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    row = db.get(AdmissionApplication, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Admission application not found")
    return application_json(row)


def _new_enrollment_number(db: Session, year_name: str, department: Department) -> str:
    year_prefix = year_name[:4] if year_name[:4].isdigit() else str(datetime.now().year)
    prefix = f"{year_prefix}{department.code.upper()}"
    existing = db.query(Student.enrollment_number).filter(Student.enrollment_number.like(f"{prefix}%")).all()
    numbers = [int(value[len(prefix):]) for (value,) in existing
               if value[len(prefix):].isdigit()]
    next_number = max(numbers, default=0) + 1
    candidate = f"{prefix}{next_number:04d}"
    while db.query(Student.id).filter_by(enrollment_number=candidate).first():
        next_number += 1
        candidate = f"{prefix}{next_number:04d}"
    return candidate


@router.patch("/admin/admissions/{application_id}/review")
def review_admission(application_id: int, data: AdmissionReview, request: Request,
                     actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if data.status not in {"under_review", "approved", "rejected"}:
        raise HTTPException(status_code=422, detail="Review status must be under_review, approved, or rejected")
    row = db.get(AdmissionApplication, application_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Admission application not found")
    if row.status not in {"submitted", "under_review"}:
        raise HTTPException(status_code=409, detail="This application has already been finalized")

    if data.status == "rejected" and not (data.rejection_reason and data.rejection_reason.strip()):
        raise HTTPException(status_code=422, detail="A rejection reason is required")
    if data.status == "approved":
        if not data.user_id or not data.initial_password:
            raise HTTPException(status_code=422, detail="Approval requires a new login ID and initial password")
        if len(data.initial_password.encode("utf-8")) > 72:
            raise HTTPException(status_code=422, detail="Initial password must not exceed 72 UTF-8 bytes")
        if db.query(User).filter((User.user_id == data.user_id) | (User.email == row.email)).first():
            raise HTTPException(status_code=409, detail="Applicant email or requested login ID is already in use")
        semester = db.get(Semester, data.semester_id) if data.semester_id else None
        if semester is None or semester.academic_year_id != row.academic_year_id:
            raise HTTPException(status_code=422, detail="Select a semester from the application's academic year")
        number = data.enrollment_number or _new_enrollment_number(db, row.academic_year.name, row.department)
        if db.query(Student.id).filter_by(enrollment_number=number).first():
            raise HTTPException(status_code=409, detail="Enrollment number is already in use")
        user = User(user_id=data.user_id, name=row.applicant_name, email=row.email,
                    password_hash=hash_password(data.initial_password), role="student")
        db.add(user)
        db.flush()
        student = Student(user_id=user.id, enrollment_number=number, department_id=row.department_id,
                          semester_id=semester.id, admission_year=int(row.academic_year.name[:4]),
                          date_of_birth=row.date_of_birth, phone=row.phone, address=row.address)
        db.add(student)
        db.flush()
        row.student_id = student.id
        notification = Notification(user_id=user.id, title="Admission approved",
                                    message="Your admission has been approved. Your student account is ready.",
                                    notification_type="admission")
        db.add(notification)
    row.status = data.status
    row.reviewed_by = actor.id
    row.reviewed_at = datetime.now(timezone.utc)
    row.rejection_reason = data.rejection_reason.strip() if data.status == "rejected" and data.rejection_reason else None
    audit_event(db, user=actor, action=f"admission.{data.status}", entity_type="admission",
                entity_id=row.id, details={"student_id": row.student_id}, request=request)
    commit_or_conflict(db, "Admission review conflicts with existing records")
    return application_json(row)
