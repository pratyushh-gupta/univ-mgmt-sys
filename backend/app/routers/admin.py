from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..core.security import hash_password
from ..models import AdmissionApplication, AuditLog, Course, CourseOffering, Department, Enrollment, Faculty, Notice, Student, User
from ..schemas import AdminUserCreate
from ..services.domain import audit_event, commit_or_conflict
from ..services.serializers import user_json

router = APIRouter()


@router.get("/admin/users")
def admin_users(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return [user_json(user) for user in db.query(User).order_by(User.role, User.name).all()]


@router.post("/admin/users", status_code=201)
def create_admin_user(data: AdminUserCreate, request: Request,
                      actor: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    if db.query(User).filter((User.user_id == data.user_id) | (User.email == str(data.email))).first():
        raise HTTPException(status_code=409, detail="User ID or email address already exists")
    user = User(user_id=data.user_id, name=data.name, email=str(data.email),
        password_hash=hash_password(data.password), role="admin")
    db.add(user)
    db.flush()
    audit_event(db, user=actor, action="admin_user.create", entity_type="user", entity_id=user.id, request=request)
    commit_or_conflict(db, "User ID or email address already exists")
    return user_json(user)


@router.get("/admin/overview")
def admin_overview(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db)):
    return {
        "students": db.query(Student).filter_by(is_active=True).count(),
        "faculty": db.query(Faculty).filter_by(is_active=True).count(),
        "courses": db.query(Course).filter_by(is_active=True).count(),
        "active_courses": db.query(Course).filter_by(is_active=True).count(),
        "course_offerings": db.query(CourseOffering).filter_by(is_active=True).count(),
        "active_course_offerings": db.query(CourseOffering).filter_by(is_active=True).count(),
        "departments": db.query(Department).count(),
        "enrollments": db.query(Enrollment).filter_by(status="active").count(),
        "current_enrollments": db.query(Enrollment).filter_by(status="active").count(),
        "pending_admissions": db.query(AdmissionApplication).filter(AdmissionApplication.status.in_(("submitted", "under_review"))).count(),
        "recent_notices": [row.title for row in db.query(Notice).filter_by(is_published=True).order_by(Notice.created_at.desc()).limit(5).all()],
        "recent_audit_activity": [{"action": row.action, "entity_type": row.entity_type, "created_at": row.created_at.isoformat()}
                                  for row in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(5).all()],
    }
