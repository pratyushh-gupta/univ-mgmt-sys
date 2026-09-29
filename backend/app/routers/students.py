from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database.connection import get_db
from ..models import User, Course, Enrollment, Attendance, Result, Assignment, Notice
from ..schemas import StudentCreate, FacultyCreate, CourseCreate, AttendanceRequest, ResultRequest
from ..core.security import hash_password
from ..core.dependencies import require_roles
from ..services.serializers import user_json

router = APIRouter()

@router.get("/students")
def students(_: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    return [user_json(u) for u in db.query(User).filter(User.role=="student").all()]

@router.post("/students")
def add_student(data: StudentCreate, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    if db.query(User).filter(User.user_id==data.id).first(): raise HTTPException(409, "Student ID already exists")
    if db.query(User).filter(User.email==data.email).first(): raise HTTPException(409, "Email address already exists")
    u=User(user_id=data.id,name=data.name,email=data.email,password_hash=hash_password(data.password),
           role="student",department=data.department,semester=data.semester)
    db.add(u); db.commit(); db.refresh(u); return user_json(u)

@router.delete("/students/{student_id}")
def delete_student(student_id: str, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    u=db.query(User).filter(User.user_id==student_id,User.role=="student").first()
    if not u: raise HTTPException(404,"Student not found")
    db.delete(u); db.commit(); return {"message":"Student removed"}

@router.get("/student/courses")
def student_courses(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    rows=db.query(Course,Enrollment).join(Enrollment,Enrollment.course_id==Course.id).filter(Enrollment.student_id==user.id).all()
    out=[]
    for c,_ in rows:
        f=db.get(User,c.faculty_id) if c.faculty_id else None
        total=db.query(Attendance).filter_by(student_id=user.id,course_id=c.id).count()
        present=db.query(Attendance).filter_by(student_id=user.id,course_id=c.id,status="present").count()
        out.append({"code":c.code,"name":c.name,"faculty":f.name if f else None,
                    "attendance":round(present/total*100) if total else 0})
    return out

@router.get("/student/attendance")
def student_attendance(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    courses=student_courses(user,db)
    overall=round(sum(c["attendance"] for c in courses)/len(courses)) if courses else 0
    return {"overall":overall,"courses":courses}

@router.get("/student/results")
def student_results(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    rows=db.query(Result,Course).join(Course,Course.id==Result.course_id).filter(Result.student_id==user.id).all()
    points=[r.point for r,_ in rows]
    return {"cgpa":round(sum(points)/len(points),2) if points else 0,
            "results":[{"subject":c.name,"grade":r.grade,"point":r.point,"marks":r.marks} for r,c in rows]}

@router.get("/student/assignments")
def student_assignments(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    ids=[x.course_id for x in db.query(Enrollment).filter_by(student_id=user.id).all()]
    return [{"title":a.title,"subject":a.subject,"due":a.due.isoformat(),"status":a.status} for a in db.query(Assignment).filter(Assignment.course_id.in_(ids)).all()]
