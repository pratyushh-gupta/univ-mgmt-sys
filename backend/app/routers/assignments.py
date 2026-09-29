from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from ..core.dependencies import require_roles
from ..database.connection import get_db
from ..models import Assignment, CourseOffering, Enrollment, Faculty, Notification, Student, Submission, User
from ..schemas import AssignmentCreate, SubmissionCreate, SubmissionGrade
from ..services.domain import audit_event, commit_or_conflict, faculty_offering, faculty_profile, student_profile

router = APIRouter()


def assignment_json(row: Assignment) -> dict:
    return {"id": row.id, "course_offering_id": row.course_offering_id,
        "course_code": row.course_offering.course.code, "course_name": row.course_offering.course.name,
        "title": row.title, "description": row.description, "instructions": row.instructions,
        "due_date": row.due_date.isoformat(), "max_marks": float(row.max_marks), "status": row.status}


@router.get("/assignments")
def list_assignments(user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    query = db.query(Assignment)
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        query = query.filter(Assignment.faculty_id == profile.id)
    return [assignment_json(row) for row in query.order_by(Assignment.due_date).all()]


@router.post("/assignments", status_code=201)
def create_assignment(data: AssignmentCreate, request: Request,
                      user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    offering = db.get(CourseOffering, data.course_offering_id)
    if offering is None:
        raise HTTPException(status_code=404, detail="Course offering not found")
    faculty = offering.faculty
    if user.role == "faculty":
        faculty = faculty_profile(db, user)
        if offering.faculty_id != faculty.id:
            raise HTTPException(status_code=403, detail="You are not assigned to this course offering")
    if data.status not in {"draft", "published", "closed"}:
        raise HTTPException(status_code=422, detail="Invalid assignment status")
    row = Assignment(course_offering_id=offering.id, faculty_id=faculty.id, title=data.title,
        description=data.description, instructions=data.instructions, due_date=data.due_date,
        max_marks=data.max_marks, attachment_url=data.attachment_url, status=data.status)
    db.add(row)
    db.flush()
    if row.status == "published":
        for enrollment in offering.enrollments:
            if enrollment.status == "active":
                db.add(Notification(user_id=enrollment.student.user_id, title="Assignment posted",
                    message=f"A new assignment is available for {offering.course.code}: {row.title}.",
                    notification_type="assignment"))
    audit_event(db, user=user, action="assignment.create", entity_type="assignment", entity_id=row.id, request=request)
    commit_or_conflict(db)
    return assignment_json(row)


@router.post("/assignments/{assignment_id}/submissions", status_code=201)
def submit_assignment(assignment_id: int, data: SubmissionCreate, request: Request,
                      user: User = Depends(require_roles("student")), db: Session = Depends(get_db)):
    student = student_profile(db, user)
    assignment = db.get(Assignment, assignment_id)
    if assignment is None or assignment.status != "published":
        raise HTTPException(status_code=404, detail="Published assignment not found")
    enrolled = db.query(Enrollment).filter_by(student_id=student.id, course_offering_id=assignment.course_offering_id, status="active").first()
    if enrolled is None:
        raise HTTPException(status_code=403, detail="You are not enrolled in this course offering")
    if not (data.text_content and data.text_content.strip()) and not data.file_url:
        raise HTTPException(status_code=422, detail="Provide submission text or a file reference")
    row = db.query(Submission).filter_by(assignment_id=assignment.id, student_id=student.id).first()
    if row is None:
        row = Submission(assignment_id=assignment.id, course_offering_id=assignment.course_offering_id,
            student_id=student.id, status="submitted")
        db.add(row)
    row.text_content, row.file_url = data.text_content, data.file_url
    row.status, row.submitted_at = "submitted", datetime.now(timezone.utc)
    db.flush()
    audit_event(db, user=user, action="submission.submit", entity_type="submission", entity_id=row.id,
        details={"assignment_id": assignment.id}, request=request)
    commit_or_conflict(db)
    db.refresh(row)
    return {"id": row.id, "assignment_id": row.assignment_id, "status": row.status, "submitted_at": row.submitted_at.isoformat()}


@router.get("/assignments/{assignment_id}/submissions")
def list_submissions(assignment_id: int, user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        if assignment.faculty_id != profile.id:
            raise HTTPException(status_code=403, detail="You do not own this assignment")
    rows = db.query(Submission).filter_by(assignment_id=assignment.id).all()
    return [{"id": row.id, "student_id": row.student_id, "student_name": row.student.user.name,
        "status": row.status, "text_content": row.text_content, "file_url": row.file_url,
        "marks": float(row.marks) if row.marks is not None else None, "feedback": row.feedback} for row in rows]


@router.patch("/submissions/{submission_id}/grade")
def grade_submission(submission_id: int, data: SubmissionGrade, request: Request,
                     user: User = Depends(require_roles("admin", "faculty")), db: Session = Depends(get_db)):
    row = db.get(Submission, submission_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    if user.role == "faculty":
        profile = faculty_profile(db, user)
        if row.assignment.faculty_id != profile.id:
            raise HTTPException(status_code=403, detail="You do not own this assignment")
    if data.marks > row.assignment.max_marks:
        raise HTTPException(status_code=422, detail="Marks cannot exceed the assignment maximum")
    row.marks, row.feedback, row.status = data.marks, data.feedback, "graded"
    row.graded_at, row.graded_by = datetime.now(timezone.utc), user.id
    audit_event(db, user=user, action="submission.grade", entity_type="submission", entity_id=row.id,
        details={"assignment_id": row.assignment_id, "marks": str(data.marks)}, request=request)
    commit_or_conflict(db)
    return {"id": row.id, "status": row.status, "marks": float(row.marks)}
