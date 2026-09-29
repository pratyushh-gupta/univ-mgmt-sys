from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import AuditLog, CourseOffering, Faculty, Student, User
from ..core.config import settings

GRADE_BOUNDARIES = (
    (Decimal("90"), "A+", Decimal("10")),
    (Decimal("80"), "A", Decimal("9")),
    (Decimal("70"), "B+", Decimal("8")),
    (Decimal("60"), "B", Decimal("7")),
    (Decimal("50"), "C", Decimal("6")),
    (Decimal("40"), "D", Decimal("5")),
    (Decimal("0"), "F", Decimal("0")),
)
LOW_ATTENDANCE_THRESHOLD_PERCENT = settings.low_attendance_threshold_percent


def grade_for(marks: Decimal, max_marks: Decimal) -> tuple[str, Decimal]:
    percentage = marks * Decimal("100") / max_marks
    for cutoff, grade, points in GRADE_BOUNDARIES:
        if percentage >= cutoff:
            return grade, points
    return "F", Decimal("0")


def student_profile(db: Session, user: User) -> Student:
    profile = db.query(Student).filter_by(user_id=user.id, is_active=True).first()
    if profile is None:
        raise HTTPException(status_code=403, detail="Student profile is unavailable")
    return profile


def faculty_profile(db: Session, user: User) -> Faculty:
    profile = db.query(Faculty).filter_by(user_id=user.id, is_active=True).first()
    if profile is None:
        raise HTTPException(status_code=403, detail="Faculty profile is unavailable")
    return profile


def faculty_offering(db: Session, user: User, offering_id: int) -> CourseOffering:
    profile = faculty_profile(db, user)
    offering = db.query(CourseOffering).filter_by(id=offering_id, faculty_id=profile.id).first()
    if offering is None:
        raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    return offering


def audit_event(db: Session, *, user: User | None, action: str, entity_type: str, entity_id: object = None,
                details: dict | None = None, request=None) -> None:
    # Callers must only include non-sensitive details; credentials and tokens are never logged.
    db.add(AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        details=details,
        ip_address=request.client.host if request and request.client else None,
        created_at=datetime.now(timezone.utc),
    ))


def commit_or_conflict(db: Session, detail: str = "The change conflicts with existing data") -> None:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail=detail) from exc
