from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import optional_user, require_roles
from ..database.connection import get_db
from ..models import AuditLog, Department, Faculty, Notice, Notification, Student, User
from ..schemas import NoticeCreate
from ..services.domain import audit_event, commit_or_conflict, faculty_profile

router = APIRouter()


def notice_json(row: Notice) -> dict:
    published = row.published_at.isoformat() if row.published_at else None
    return {"id": row.id, "title": row.title, "content": row.content, "body": row.content,
        "author_id": row.author_id, "audience": row.audience, "department_id": row.department_id,
        "published_at": published, "date": published or row.created_at.isoformat(),
        "expires_at": row.expires_at.isoformat() if row.expires_at else None, "is_published": row.is_published}


@router.get("/notices")
def list_notices(user: User | None = Depends(optional_user), db: Session = Depends(get_db)):
    now = datetime.now(timezone.utc)
    query = db.query(Notice).filter(Notice.is_published.is_(True), Notice.published_at.is_not(None),
        Notice.published_at <= now, (Notice.expires_at.is_(None) | (Notice.expires_at > now)))
    if user is None:
        query = query.filter(Notice.audience == "all", Notice.department_id.is_(None))
    else:
        department_id = None
        if user.role == "student":
            profile = db.query(Student).filter_by(user_id=user.id).first()
            department_id = profile.department_id if profile else None
        elif user.role == "faculty":
            profile = db.query(Faculty).filter_by(user_id=user.id).first()
            department_id = profile.department_id if profile else None
        query = query.filter(Notice.audience.in_(("all", user.role)))
        if user.role != "admin":
            query = query.filter((Notice.department_id.is_(None)) | (Notice.department_id == department_id))
    return [notice_json(row) for row in query.order_by(Notice.published_at.desc()).all()]


@router.post("/notices", status_code=201)
def create_notice(data: NoticeCreate, request: Request,
                  user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    if data.audience not in {"all", "admin", "faculty", "student"}:
        raise HTTPException(status_code=422, detail="Invalid notice audience")
    if data.department_id is not None and db.get(Department, data.department_id) is None:
        raise HTTPException(status_code=404, detail="Department not found")
    if user.role == "faculty":
        department_id = faculty_profile(db, user).department_id
        if data.department_id not in (None, department_id) or data.audience == "admin":
            raise HTTPException(status_code=403, detail="Faculty may publish notices only to their department or all users")
    now = datetime.now(timezone.utc)
    row = Notice(title=data.title, content=data.content, author_id=user.id, audience=data.audience,
        department_id=data.department_id, expires_at=data.expires_at,
        is_published=data.is_published, published_at=now if data.is_published else None)
    db.add(row)
    db.flush()
    audit_event(db, user=user, action="notice.create", entity_type="notice", entity_id=row.id, request=request)
    if row.is_published:
        recipients = db.query(User).filter(User.is_active.is_(True))
        if row.audience != "all": recipients = recipients.filter(User.role == row.audience)
        users = recipients.all()
        for recipient in users:
            if row.department_id is not None:
                if recipient.role == "student":
                    profile = db.query(Student).filter_by(user_id=recipient.id).first()
                elif recipient.role == "faculty":
                    profile = db.query(Faculty).filter_by(user_id=recipient.id).first()
                else:
                    profile = None
                if recipient.role != "admin" and (profile is None or profile.department_id != row.department_id):
                    continue
            db.add(Notification(user_id=recipient.id, title=f"University notice: {row.title}",
                message=row.content, notification_type="notice"))
    commit_or_conflict(db)
    return notice_json(row)


@router.get("/notifications")
def my_notifications(user: User = Depends(require_roles("admin", "faculty", "student")), db: Session = Depends(get_db)):
    rows = db.query(Notification).filter_by(user_id=user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return [{"id": row.id, "title": row.title, "message": row.message, "type": row.notification_type,
        "is_read": row.is_read, "created_at": row.created_at.isoformat(),
        "read_at": row.read_at.isoformat() if row.read_at else None} for row in rows]


@router.patch("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, user: User = Depends(require_roles("admin", "faculty", "student")),
                           db: Session = Depends(get_db)):
    row = db.query(Notification).filter_by(id=notification_id, user_id=user.id).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    row.is_read, row.read_at = True, datetime.now(timezone.utc)
    commit_or_conflict(db)
    return {"id": row.id, "is_read": row.is_read, "read_at": row.read_at.isoformat()}


@router.get("/admin/audit-logs")
def audit_logs(_: User = Depends(require_roles("admin")), db: Session = Depends(get_db), limit: int = 100):
    limit = max(1, min(limit, 500))
    rows = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [{"id": row.id, "user_id": row.user_id, "action": row.action, "entity_type": row.entity_type,
        "entity_id": row.entity_id, "details": row.details, "ip_address": row.ip_address,
        "created_at": row.created_at.isoformat()} for row in rows]
