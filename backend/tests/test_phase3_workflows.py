from datetime import date
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
        pytest.skip("Phase 3 integration tests require the configured PostgreSQL database")

    connection = engine.connect()
    outer_transaction = connection.begin()
    test_sessions = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False,
                                 join_transaction_mode="create_savepoint")

    def override_database():
        session = test_sessions()
        try:
            yield session
        finally:
            session.close()

    suffix = uuid4().hex[:10]
    login_id = f"T{suffix}"
    password = "PhaseThreeTestPassword!"
    with test_sessions() as db:
        department = Department(code=f"T{suffix[:6]}", name=f"Test Department {suffix}")
        year = AcademicYear(name=f"2032-{suffix[:6]}",
                            start_date=date(2032, 8, 1), end_date=date(2033, 7, 31), is_active=True)
        db.add_all([department, year])
        db.flush()
        semester = Semester(academic_year_id=year.id, name="Test Semester", number=1,
                            start_date=date(2032, 8, 1), end_date=date(2032, 12, 31), is_active=True)
        admin = User(user_id=login_id, name="Phase 3 Admin", email=f"{login_id.lower()}@example.com",
                     password_hash=hash_password(password), role="admin")
        db.add_all([semester, admin])
        db.commit()

    app.dependency_overrides[get_db] = override_database
    try:
        with TestClient(app) as client:
            yield client, {"user_id": login_id, "password": password}, department.id, year.id, semester.id
    finally:
        app.dependency_overrides.clear()
        outer_transaction.rollback()
        connection.close()


def test_admission_registration_and_authorization(university_client):
    client, admin_credentials, department_id, year_id, semester_id = university_client
    login = client.post("/auth/login", json=admin_credentials)
    assert login.status_code == 200
    admin = {"Authorization": f"Bearer {login.json()['access_token']}"}

    faculty_response = client.post("/faculty", headers=admin, json={
        "id": "FAC-ONE", "name": "Assigned Faculty", "email": "fac-one@example.com",
        "department_id": department_id, "employee_id": "EMP-ONE", "password": "FacultyPass123",
    })
    assert faculty_response.status_code == 201
    faculty_id = faculty_response.json()["faculty_id"]
    other_faculty = client.post("/faculty", headers=admin, json={
        "id": "FAC-TWO", "name": "Other Faculty", "email": "fac-two@example.com",
        "department_id": department_id, "employee_id": "EMP-TWO", "password": "FacultyPass123",
    })
    assert other_faculty.status_code == 201

    application = client.post("/admin/admissions", headers=admin, json={
        "applicant_name": "Approved Applicant", "email": "approved-applicant@example.com",
        "department_id": department_id, "academic_year_id": year_id, "intended_program": "Computer Science",
    })
    rejected = client.post("/admin/admissions", headers=admin, json={
        "applicant_name": "Rejected Applicant", "email": "rejected-applicant@example.com",
        "department_id": department_id, "academic_year_id": year_id, "intended_program": "Computer Science",
    })
    assert application.status_code == rejected.status_code == 201
    assert client.get("/admin/admissions?status=submitted&search=Applicant", headers=admin).json()["total"] == 2
    assert client.get(f"/admin/admissions/{application.json()['id']}", headers=admin).status_code == 200
    assert client.patch(f"/admin/admissions/{rejected.json()['id']}/review", headers=admin,
                        json={"status": "rejected"}).status_code == 422
    reject_result = client.patch(f"/admin/admissions/{rejected.json()['id']}/review", headers=admin,
                                 json={"status": "rejected", "rejection_reason": "Incomplete documents"})
    assert reject_result.status_code == 200
    assert reject_result.json()["rejection_reason"] == "Incomplete documents"

    student_login_id = f"STU-{uuid4().hex[:8]}"
    approved = client.patch(f"/admin/admissions/{application.json()['id']}/review", headers=admin, json={
        "status": "approved", "user_id": student_login_id,
        "initial_password": "ApprovedStudentPassword!", "semester_id": semester_id,
    })
    assert approved.status_code == 200
    assert "password" not in approved.text.lower()
    assert approved.json()["student_id"] is not None
    assert client.patch(f"/admin/admissions/{application.json()['id']}/review", headers=admin,
                        json={"status": "approved"}).status_code == 409

    course = client.post("/courses", headers=admin, json={
        "code": f"T{uuid4().hex[:8]}", "name": "Registration Test", "department_id": department_id, "credits": 3,
    })
    assert course.status_code == 201
    offering = client.post("/course-offerings", headers=admin, json={
        "course_id": course.json()["id"], "faculty_id": faculty_id, "semester_id": semester_id,
        "section": "A", "capacity": 1,
    })
    assert offering.status_code == 201

    student_login = client.post("/auth/login", json={
        "user_id": student_login_id, "password": "ApprovedStudentPassword!",
    })
    assert student_login.status_code == 200
    student = {"Authorization": f"Bearer {student_login.json()['access_token']}"}
    assert client.get("/student/dashboard", headers=student).status_code == 200
    assert client.get("/student/history", headers=student).status_code == 200
    assert client.get("/student/exams", headers=student).status_code == 200

    offering_id = offering.json()["id"]
    assert any(row["id"] == offering_id for row in client.get("/student/course-offerings", headers=student).json()["items"])
    enrolled = client.post("/student/enrollments", headers=student, json={"course_offering_id": offering_id})
    assert enrolled.status_code == 201
    assert client.post("/student/enrollments", headers=student, json={"course_offering_id": offering_id}).status_code == 409

    second_student = client.post("/students", headers=admin, json={
        "id": f"SECOND-{uuid4().hex[:8]}", "name": "Second Student", "email": f"second-{uuid4().hex[:10]}@example.com",
        "department_id": department_id, "semester_id": semester_id, "admission_year": 2032,
        "enrollment_number": f"EN{uuid4().hex[:12]}", "password": "SecondStudentPassword!",
    })
    assert second_student.status_code == 201
    second_login = client.post("/auth/login", json={
        "user_id": second_student.json()["user_id"], "password": "SecondStudentPassword!",
    })
    assert second_login.status_code == 200
    assert client.post("/student/enrollments", headers={"Authorization": f"Bearer {second_login.json()['access_token']}"},
                       json={"course_offering_id": offering_id}).status_code == 409

    faculty_login = client.post("/auth/login", json={"user_id": "FAC-ONE", "password": "FacultyPass123"})
    other_login = client.post("/auth/login", json={"user_id": "FAC-TWO", "password": "FacultyPass123"})
    assert faculty_login.status_code == other_login.status_code == 200
    faculty_headers = {"Authorization": f"Bearer {faculty_login.json()['access_token']}"}
    other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}
    assert len(client.get(f"/course-offerings/{offering_id}/roster", headers=faculty_headers).json()) == 1
    assert client.get(f"/course-offerings/{offering_id}/roster", headers=other_headers).status_code == 403

    dropped = client.delete(f"/student/enrollments/{enrolled.json()['id']}", headers=student)
    assert dropped.status_code == 200 and dropped.json()["status"] == "dropped"
    reactivated = client.post("/student/enrollments", headers=student, json={"course_offering_id": offering_id})
    assert reactivated.status_code == 201 and reactivated.json()["id"] == enrolled.json()["id"]
