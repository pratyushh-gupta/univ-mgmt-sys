from datetime import date
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session
from .database import Base, engine, get_db
from .models import User, Course, Enrollment, Attendance, Result, Assignment, Notice
from .schemas import LoginRequest, StudentCreate, FacultyCreate, CourseCreate, AttendanceRequest, ResultRequest
from .auth import verify_password, create_token, hash_password, current_user, require_roles
from .seed import seed

app = FastAPI(title="University Management System API", version="1.0.0")

origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    with next(get_db()) as db:
        seed(db)

def user_json(u):
    return {"id": u.id, "user_id": u.user_id, "name": u.name, "email": u.email,
            "role": u.role, "department": u.department, "semester": u.semester}

def grade_for(m):
    if m >= 90: return "A+", 10
    if m >= 80: return "A", 9
    if m >= 70: return "B+", 8
    if m >= 60: return "B", 7
    if m >= 50: return "C", 6
    if m >= 40: return "D", 5
    return "F", 0

@app.get("/health")
def health(): return {"status": "ok"}

@app.post("/auth/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.user_id == data.user_id).first()
    if not u or not verify_password(data.password, u.password_hash):
        raise HTTPException(401, "Invalid user ID or password")
    return {"access_token": create_token(u), "token_type": "bearer", "user": user_json(u)}

@app.get("/auth/me")
def me(user=Depends(current_user)): return user_json(user)

@app.get("/students")
def students(_: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    return [user_json(u) for u in db.query(User).filter(User.role=="student").all()]

@app.post("/students")
def add_student(data: StudentCreate, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    if db.query(User).filter(User.user_id==data.id).first(): raise HTTPException(409, "Student ID already exists")
    u=User(user_id=data.id,name=data.name,email=data.email,password_hash=hash_password(data.password),
           role="student",department=data.department,semester=data.semester)
    db.add(u); db.commit(); db.refresh(u); return user_json(u)

@app.delete("/students/{student_id}")
def delete_student(student_id: str, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    u=db.query(User).filter(User.user_id==student_id,User.role=="student").first()
    if not u: raise HTTPException(404,"Student not found")
    db.delete(u); db.commit(); return {"message":"Student removed"}

@app.get("/faculty")
def faculty(_: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    return [user_json(u) for u in db.query(User).filter(User.role=="faculty").all()]

@app.post("/faculty")
def add_faculty(data: FacultyCreate, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    if db.query(User).filter(User.user_id==data.id).first(): raise HTTPException(409,"Faculty ID already exists")
    u=User(user_id=data.id,name=data.name,email=data.email,password_hash=hash_password(data.password),
           role="faculty",department=data.department)
    db.add(u); db.commit(); db.refresh(u); return user_json(u)

@app.delete("/faculty/{faculty_id}")
def delete_faculty(faculty_id: str, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    u=db.query(User).filter(User.user_id==faculty_id,User.role=="faculty").first()
    if not u: raise HTTPException(404,"Faculty not found")
    db.delete(u); db.commit(); return {"message":"Faculty removed"}

@app.get("/courses")
def courses(db: Session=Depends(get_db)):
    out=[]
    for c in db.query(Course).all():
        f=db.get(User,c.faculty_id) if c.faculty_id else None
        out.append({"code":c.code,"name":c.name,"faculty":f.name if f else None,
                    "department":c.department,"enrolled":db.query(Enrollment).filter_by(course_id=c.id).count(),
                    "semester":c.semester})
    return out

@app.post("/courses")
def add_course(data: CourseCreate, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    if db.query(Course).filter_by(code=data.code).first(): raise HTTPException(409,"Course code already exists")
    faculty=None
    if data.faculty: faculty=db.query(User).filter(User.name==data.faculty,User.role=="faculty").first()
    c=Course(code=data.code,name=data.name,faculty_id=faculty.id if faculty else None,
             department=data.department,semester=data.semester)
    db.add(c); db.commit(); db.refresh(c); return {"code":c.code,"name":c.name,"faculty":data.faculty,
                                                    "department":c.department,"enrolled":0}

@app.delete("/courses/{code}")
def delete_course(code: str, _: User=Depends(require_roles("admin")), db: Session=Depends(get_db)):
    c=db.query(Course).filter_by(code=code).first()
    if not c: raise HTTPException(404,"Course not found")
    db.delete(c); db.commit(); return {"message":"Course removed"}

@app.get("/student/courses")
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

@app.get("/student/attendance")
def student_attendance(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    courses=student_courses(user,db)
    overall=round(sum(c["attendance"] for c in courses)/len(courses)) if courses else 0
    return {"overall":overall,"courses":courses}

@app.get("/student/results")
def student_results(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    rows=db.query(Result,Course).join(Course,Course.id==Result.course_id).filter(Result.student_id==user.id).all()
    points=[r.point for r,_ in rows]
    return {"cgpa":round(sum(points)/len(points),2) if points else 0,
            "results":[{"subject":c.name,"grade":r.grade,"point":r.point,"marks":r.marks} for r,c in rows]}

@app.get("/student/assignments")
def student_assignments(user=Depends(require_roles("student")), db: Session=Depends(get_db)):
    ids=[x.course_id for x in db.query(Enrollment).filter_by(student_id=user.id).all()]
    return [{"title":a.title,"subject":a.subject,"due":a.due.isoformat(),"status":a.status} for a in db.query(Assignment).filter(Assignment.course_id.in_(ids)).all()]

@app.get("/notices")
def notices(db: Session=Depends(get_db)):
    return [{"title":n.title,"body":n.body,"date":n.date.isoformat()} for n in db.query(Notice).order_by(Notice.date.desc()).all()]

@app.get("/faculty/courses")
def faculty_courses(user=Depends(require_roles("faculty")), db: Session=Depends(get_db)):
    cs=db.query(Course).filter_by(faculty_id=user.id).all()
    return [{"code":c.code,"name":c.name,"department":c.department,
             "students":db.query(Enrollment).filter_by(course_id=c.id).count()} for c in cs]

@app.get("/faculty/roster/{course_code}")
def roster(course_code: str,user=Depends(require_roles("faculty")),db: Session=Depends(get_db)):
    c=db.query(Course).filter_by(code=course_code,faculty_id=user.id).first()
    if not c: raise HTTPException(404,"Course not found")
    rows=db.query(User).join(Enrollment,Enrollment.student_id==User.id).filter(Enrollment.course_id==c.id).all()
    return [{"id":s.user_id,"name":s.name} for s in rows]

@app.post("/attendance")
def save_attendance(data: AttendanceRequest,user=Depends(require_roles("faculty")),db: Session=Depends(get_db)):
    c=db.query(Course).filter_by(code=data.course_code,faculty_id=user.id).first()
    if not c: raise HTTPException(404,"Course not found")
    for item in data.records:
        s=db.query(User).filter_by(user_id=item.student_id,role="student").first()
        if not s or item.status not in ("present","absent"): continue
        row=db.query(Attendance).filter_by(student_id=s.id,course_id=c.id,date=data.date).first()
        if row: row.status=item.status
        else: db.add(Attendance(student_id=s.id,course_id=c.id,date=data.date,status=item.status))
    db.commit(); return {"message":"Attendance saved"}

@app.post("/results")
def save_results(data: ResultRequest,user=Depends(require_roles("faculty")),db: Session=Depends(get_db)):
    c=db.query(Course).filter_by(code=data.course_code,faculty_id=user.id).first()
    if not c: raise HTTPException(404,"Course not found")
    for item in data.results:
        s=db.query(User).filter_by(user_id=item.student_id,role="student").first()
        if not s: continue
        grade,point=grade_for(item.marks)
        row=db.query(Result).filter_by(student_id=s.id,course_id=c.id).first()
        if row: row.marks=item.marks; row.grade=grade; row.point=point
        else: db.add(Result(student_id=s.id,course_id=c.id,marks=item.marks,grade=grade,point=point))
    db.commit(); return {"message":"Results saved"}

@app.get("/admin/overview")
def admin_overview(_: User=Depends(require_roles("admin")),db: Session=Depends(get_db)):
    return {"students":db.query(User).filter_by(role="student").count(),
            "faculty":db.query(User).filter_by(role="faculty").count(),
            "courses":db.query(Course).count()}
