from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..models import User, Course, Enrollment, Attendance, Result, Assignment, Notice
from ..schemas import StudentCreate, FacultyCreate, CourseCreate, AttendanceRequest, ResultRequest
from ..core.security import hash_password
from ..core.dependencies import require_roles
from ..services.serializers import user_json

router = APIRouter()

@router.get("/admin/overview")
def admin_overview(_: User=Depends(require_roles("admin")),db: Session=Depends(get_db)):
    return {"students":db.query(User).filter_by(role="student").count(),
            "faculty":db.query(User).filter_by(role="faculty").count(),
            "courses":db.query(Course).count()}
