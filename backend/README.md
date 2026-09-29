# FastAPI Backend

FastAPI with SQLAlchemy 2.x, PostgreSQL (`postgresql+psycopg2`) and Alembic. SQLite URLs remain supported for isolated development/test databases. The backend loads `backend/.env` from its own directory, regardless of the shell's working directory.

## Setup and run

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Fill in the local PostgreSQL URL and a private JWT_SECRET in .env.
alembic upgrade head
python run.py
```

Do not print or commit `.env`. `.env.example` contains only placeholders. Production must supply an explicit JWT secret; placeholder and development secrets are rejected. Production never seeds sample accounts.

## Migrations

Run Alembic commands from this directory so the project's configuration and environment are loaded:

```powershell
alembic upgrade head
alembic current
alembic history
alembic downgrade -1
```

When models change, generate a candidate with `alembic revision --autogenerate -m "description"`, review it, and then apply it. `Base.metadata.create_all()` is not used at application startup.

## Development data

With `ENVIRONMENT=development` and the schema migrated, startup seeds a small idempotent local dataset. To run the seeder explicitly, use `python -m app.seed`. It refuses to run outside development. These records and their sample passwords are for local development only; do not reuse them outside an isolated development database.

## Domain entities

Authentication `User` records are separated from one-to-one `Student` and `Faculty` profiles. Academic structure uses `Department`, `AcademicYear`, and `Semester`; admissions use `AdmissionApplication`; teaching is represented by `Course` and `CourseOffering`; `Enrollment` links students to offerings and preserves dropped history. `ClassSchedule` provides timetable foundations. Attendance uses session and record tables. Assignments have submissions and grading; exams have schedules; results store assessment marks and publication state. Notices, per-user notifications, and audit events have dedicated tables.

## API surface

- `/auth`, `/admin`
- `/departments`, `/academic-years`, `/semesters`
- `/students`, `/faculty`, `/courses`, `/course-offerings`, `/enrollments`
- `/attendance`, `/assignments`, `/submissions`, `/exams`, `/exam-schedules`, `/results`
- `/notices`, `/notifications`

Phase 3 also provides `/admin/admissions` for application review and student creation, `/student/course-offerings` and `/student/enrollments` for registration and drops, `/student/dashboard`, `/student/history`, `/student/exams`, and `/timetable`. Admin lists support search and pagination. Course offering enrollment enforces active student/course/offer status, department and semester compatibility, and capacity.

Legacy Phase 1 student/faculty/course and attendance/result paths remain available where their meanings can be mapped to the new relations. Student-visible results include only published records. Timetable entries are a schedule foundation; automatic timetable generation and direct binary file storage are not implemented. Submission file references store metadata/URLs only. Assignment grading and result entry remain faculty workflows; no unsupported grading or attendance summaries are synthesized.

## Tests

Install test dependencies with `pip install -r requirements-dev.txt`, then run `python -m pytest -q` from `backend/`. The Phase 3 integration test requires PostgreSQL configured through `DATABASE_URL`; it skips on SQLite. Use a disposable development/test database because it exercises migrations and API workflows. The latest schema revision is `f54c14450324` (parent `80d2893ee48c`). `npm run lint` and `npm run build` are run from `frontend/`.
