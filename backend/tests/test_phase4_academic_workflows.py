from datetime import date, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.core.security import hash_password
from app.database.connection import engine, get_db
from app.main import app
from app.models import AcademicYear, Department, Semester, User


@pytest.fixture
def university_client():
    if engine.dialect.name != "postgresql":
        pytest.skip("Phase 4 integration tests require the configured PostgreSQL database")
    connection = engine.connect()
    outer_transaction = connection.begin()
    sessions = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False,
                            join_transaction_mode="create_savepoint")
    suffix = uuid4().hex[:10]
    login_id, password = f"T{suffix}", "PhaseFourTestPassword!"
    with sessions() as db:
        department = Department(code=f"T{suffix[:6]}", name=f"Test Department {suffix}")
        year = AcademicYear(name=f"2033-{suffix[:6]}", start_date=date(2033, 8, 1),
                            end_date=date(2034, 7, 31), is_active=True)
        db.add_all([department, year])
        db.flush()
        semester = Semester(academic_year_id=year.id, name="Test Semester", number=1,
                            start_date=date(2033, 8, 1), end_date=date(2033, 12, 31), is_active=True)
        admin = User(user_id=login_id, name="Phase 4 Admin", email=f"{login_id.lower()}@example.com",
                     password_hash=hash_password(password), role="admin")
        db.add_all([semester, admin])
        db.commit()

    def override_database():
        session = sessions()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_database
    try:
        with TestClient(app) as client:
            yield client, {"user_id": login_id, "password": password}, department.id, year.id, semester.id
    finally:
        app.dependency_overrides.clear()
        outer_transaction.rollback()
        connection.close()


def test_attendance_assignment_exam_result_and_timetable_workflows(university_client):
    client, admin_credentials, department_id, year_id, semester_id = university_client
    admin_login = client.post("/auth/login", json=admin_credentials)
    assert admin_login.status_code == 200
    admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    suffix = uuid4().hex[:8]
    faculty_id, outsider_id = f"FAC-{suffix}", f"OUT-{suffix}"
    student_id, outsider_student_id = f"STU-{suffix}", f"OTH-{suffix}"
    for login_id, label in ((faculty_id, "Assigned"), (outsider_id, "Unassigned")):
        response = client.post("/faculty", headers=admin, json={"id": login_id, "name": f"{label} Faculty",
            "email": f"{login_id.lower()}@example.com", "department_id": department_id,
            "employee_id": f"EMP-{login_id}", "password": "FacultyPassword123"})
        assert response.status_code == 201
    for login_id, enrollment in ((student_id, f"EN-{suffix}"), (outsider_student_id, f"OUTEN-{suffix}")):
        response = client.post("/students", headers=admin, json={"id": login_id, "name": login_id,
            "email": f"{login_id.lower()}@example.com", "department_id": department_id,
            "semester_id": semester_id, "admission_year": 2032, "enrollment_number": enrollment,
            "password": "StudentPassword123"})
        assert response.status_code == 201
    faculty_login = client.post("/auth/login", json={"user_id": faculty_id, "password": "FacultyPassword123"})
    outsider_login = client.post("/auth/login", json={"user_id": outsider_id, "password": "FacultyPassword123"})
    student_login = client.post("/auth/login", json={"user_id": student_id, "password": "StudentPassword123"})
    other_student_login = client.post("/auth/login", json={"user_id": outsider_student_id, "password": "StudentPassword123"})
    faculty = {"Authorization": f"Bearer {faculty_login.json()['access_token']}"}
    outsider = {"Authorization": f"Bearer {outsider_login.json()['access_token']}"}
    student = {"Authorization": f"Bearer {student_login.json()['access_token']}"}
    other_student = {"Authorization": f"Bearer {other_student_login.json()['access_token']}"}
    student_profile_id = client.get("/auth/me", headers=student).json()["student_id"]
    other_profile_id = client.get("/auth/me", headers=other_student).json()["student_id"]

    course = client.post("/courses", headers=admin, json={"code": f"P4-{suffix}", "name": "Operations",
        "department_id": department_id, "credits": 3}).json()
    offering = client.post("/course-offerings", headers=admin, json={"course_id": course["id"],
        "faculty_id": client.get("/auth/me", headers=faculty).json()["faculty_id"],
        "semester_id": semester_id, "section": "A"}).json()
    assert client.post("/enrollments", headers=admin, json={"student_id": student_profile_id,
        "course_offering_id": offering["id"]}).status_code == 201

    session_date = date.today().isoformat()
    attendance = client.post("/attendance/sessions", headers=faculty, json={"course_offering_id": offering["id"],
        "session_date": session_date, "start_time": "09:00", "end_time": "10:00", "topic": "Review",
        "records": [{"student_id": student_profile_id, "status": "present"}]})
    assert attendance.status_code == 201
    session_id = attendance.json()["attendance_session_id"]
    assert client.post("/attendance/sessions", headers=outsider, json={"course_offering_id": offering["id"],
        "session_date": session_date, "records": [{"student_id": student_profile_id, "status": "absent"}]}).status_code == 403
    assert client.put(f"/attendance/sessions/{session_id}", headers=faculty, json={"session_date": session_date,
        "start_time": "09:00", "end_time": "10:00", "topic": "Reviewed", "records": [
            {"student_id": student_profile_id, "status": "absent"}]}).status_code == 200
    assert client.put(f"/attendance/sessions/{session_id}", headers=outsider, json={"session_date": session_date,
        "records": [{"student_id": student_profile_id, "status": "present"}]}).status_code == 403
    assert client.post("/attendance/sessions", headers=faculty, json={"course_offering_id": offering["id"],
        "session_date": session_date, "records": [{"student_id": student_profile_id, "status": "present"},
        {"student_id": student_profile_id, "status": "absent"}]}).status_code == 400
    assert client.get("/admin/attendance", headers=admin, params={"department_id": department_id}).json()["total"] == 1
    assert client.get(f"/course-offerings/{offering['id']}/attendance-summary", headers=faculty).json()["students"][0]["attendance"] == 0
    assert client.get(f"/course-offerings/{offering['id']}/attendance-summary", headers=outsider).status_code == 403
    assert client.get("/admin/attendance", headers=student).status_code == 403
    assert client.get("/student/attendance", headers=student).json()["courses"][0]["absent_sessions"] == 1
    assert client.get("/student/attendance", headers=other_student).json()["total_sessions"] == 0
    assert any(row["type"] == "low_attendance" for row in client.get("/notifications", headers=student).json())
    assert client.get("/notifications", headers=other_student).json() == []

    due_date = (date.today() + timedelta(days=10)).isoformat() + "T23:59:00+00:00"
    assignment = client.post("/assignments", headers=faculty, json={"course_offering_id": offering["id"],
        "title": "Operations report", "due_date": due_date, "max_marks": 20, "status": "published"})
    assert assignment.status_code == 201
    assignment_id = assignment.json()["id"]
    assert any(row["id"] == assignment_id for row in client.get("/student/assignments", headers=student).json())
    assert client.get("/student/assignments", headers=other_student).json() == []
    assert client.put(f"/assignments/{assignment_id}/submissions/draft", headers=student,
        json={"text_content": "Draft"}).status_code == 200
    submitted = client.post(f"/assignments/{assignment_id}/submissions", headers=student,
        json={"text_content": "Final work"})
    assert submitted.status_code == 201
    assert client.post(f"/assignments/{assignment_id}/submissions", headers=student,
        json={"text_content": "Duplicate"}).status_code == 409
    assert client.get(f"/assignments/{assignment_id}/submissions", headers=outsider).status_code == 403
    assert client.patch(f"/submissions/{submitted.json()['id']}/grade", headers=outsider,
        json={"marks": 18}).status_code == 403
    graded = client.patch(f"/submissions/{submitted.json()['id']}/grade", headers=faculty,
        json={"marks": 18, "feedback": "Good work"})
    assert graded.status_code == 200
    assert client.get("/student/assignments", headers=student).json()[0]["marks"] == 18

    exam_date = (date.today() + timedelta(days=15)).isoformat()
    exam = client.post("/exams", headers=faculty, json={"name": "Internal 1", "exam_type": "internal",
        "semester_id": semester_id, "start_date": exam_date, "end_date": exam_date,
        "course_offering_id": offering["id"], "exam_date": exam_date, "start_time": "09:00",
        "end_time": "10:00", "room": f"R-{suffix}", "max_marks": 50})
    assert exam.status_code == 201
    assert any(row["exam_name"] == "Internal 1" for row in client.get("/student/exams", headers=student).json())
    assert client.get("/notifications", headers=student).json()
    assert client.post("/exams", headers=outsider, json={"name": "Other", "exam_type": "final",
        "semester_id": semester_id, "start_date": exam_date, "end_date": exam_date,
        "course_offering_id": offering["id"], "exam_date": exam_date, "start_time": "09:00",
        "end_time": "10:00"}).status_code == 403
    other_course = client.post("/courses", headers=admin, json={"code": f"P4X-{suffix}", "name": "Other Operations",
        "department_id": department_id, "credits": 3}).json()
    outsider_profile_id = client.get("/auth/me", headers=outsider).json()["faculty_id"]
    other_offering = client.post("/course-offerings", headers=admin, json={"course_id": other_course["id"],
        "faculty_id": outsider_profile_id, "semester_id": semester_id, "section": "B"}).json()
    overlap_exam = client.post("/exams", headers=admin, json={"name": "Room conflict", "exam_type": "midterm",
        "semester_id": semester_id, "start_date": exam_date, "end_date": exam_date,
        "course_offering_id": other_offering["id"], "exam_date": exam_date, "start_time": "09:30",
        "end_time": "10:30", "room": f"R-{suffix}"})
    assert overlap_exam.status_code == 409

    result = client.post("/results/batch", headers=faculty, json={"course_offering_id": offering["id"],
        "assessment_name": "Final", "results": [{"student_id": student_profile_id, "marks": 45,
        "max_marks": 50, "is_final": True}]})
    assert result.status_code == 200, result.text
    assert client.get("/student/results", headers=student).json()["cgpa"] is None
    assert client.get("/student/results", headers=student).json()["results"] == []
    assert client.post("/results/batch", headers=faculty, json={"course_offering_id": offering["id"],
        "assessment_name": "Invalid marks", "results": [{"student_id": student_profile_id, "marks": 51,
        "max_marks": 50}]}).status_code == 422
    assert client.post("/results/batch", headers=faculty, json={"course_offering_id": offering["id"],
        "assessment_name": "Not enrolled", "results": [{"student_id": other_profile_id, "marks": 20,
        "max_marks": 50}]}).status_code == 400
    assert client.post("/results/batch", headers=outsider, json={"course_offering_id": offering["id"],
        "assessment_name": "Final", "results": [{"student_id": student_profile_id, "marks": 45,
        "max_marks": 50, "is_final": True}]}).status_code == 403
    rows = client.get("/results", headers=faculty).json()
    result_id = next(row["id"] for row in rows if row["assessment_name"] == "Final" and row["student_id"] == student_profile_id)
    assert client.post(f"/results/{result_id}/publish", headers=faculty).status_code == 200
    student_results = client.get("/student/results", headers=student).json()
    assert student_results["cgpa"] == 10.0
    assert student_results["sgpa_by_semester"][0]["sgpa"] == 10.0

    schedule = client.post("/class-schedules", headers=faculty, json={"course_offering_id": offering["id"],
        "day_of_week": 1, "start_time": "11:00", "end_time": "12:00", "room": f"T-{suffix}"})
    assert schedule.status_code == 201
    assert client.patch(f"/class-schedules/{schedule.json()['id']}", headers=faculty,
        json={"start_time": "12:00", "end_time": "12:00"}).status_code == 422
    assert client.post("/class-schedules", headers=faculty, json={"course_offering_id": offering["id"],
        "day_of_week": 1, "start_time": "11:30", "end_time": "12:30", "room": f"Other-{suffix}"}).status_code == 409
    assert client.post("/class-schedules", headers=admin, json={"course_offering_id": other_offering["id"],
        "day_of_week": 1, "start_time": "11:30", "end_time": "12:30", "room": f"T-{suffix}"}).status_code == 409
    assert client.get("/class-schedules", headers=student).json()
    assert client.get("/notifications", headers=other_student).json() == []
