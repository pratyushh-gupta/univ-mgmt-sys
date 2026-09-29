# FastAPI Backend

FastAPI + SQLAlchemy 2.x backend. Local development uses SQLite; PostgreSQL support can be configured later via `DATABASE_URL` without changing application code.

## Setup (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

API docs: http://localhost:8000/docs. The default `DATABASE_URL=sqlite:///./university.db` creates a local SQLite database from the backend working directory. Configure `JWT_SECRET`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `ENVIRONMENT`, and `CORS_ORIGINS` in the backend `.env`; it is loaded from the backend directory even when started elsewhere. Production requires an explicit, non-placeholder JWT secret of at least 32 characters. Tables initialize on startup, but demo users and sample data are seeded only in development. Never commit `.env`.

## Seeded development accounts

| Role | User ID | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Faculty | `F001` | `faculty123` |
| Student | `2024CS1042` | `student123` |

Change development passwords for any non-local environment.

New student and faculty passwords must contain at least 8 characters. Course creation rejects unknown faculty IDs; attendance and results accept only students enrolled in the selected course. Production deployments must provision real user accounts through a controlled administrative workflow; demo accounts are never seeded there.

## API endpoints

- `GET /health`
- `POST /auth/login`, `GET /auth/me`
- `GET/POST /students`, `DELETE /students/{student_id}` (Admin)
- `GET/POST /faculty`, `DELETE /faculty/{faculty_id}` (Admin)
- `GET/POST /courses`, `DELETE /courses/{code}` (writes require Admin)
- `GET /student/courses`, `/student/attendance`, `/student/results`, `/student/assignments` (Student)
- `GET /notices`
- `GET /faculty/courses`, `/faculty/roster/{course_code}` (Faculty)
- `POST /attendance`, `/results` (Faculty)
- `GET /admin/overview` (Admin)

Authentication failures return 401 and role failures return 403. Validation uses FastAPI's 422 responses; missing resources return 404; duplicates return 409. Unexpected server errors return a generic 500 while details remain in server logs.

The frontend calls the existing endpoints through `frontend/src/api`. Timetable, assignment submission, and related expanded workflows are not yet supported by this API. PostgreSQL deployment, Alembic, and the full database redesign are Phase 2 work.
