# University Management System

FastAPI + SQLAlchemy backend and React/Vite frontend for the university portal. The Phase 3 implementation uses relational PostgreSQL models and Alembic migrations. SQLite URLs remain available for isolated local use, but the workflow integration tests require PostgreSQL. The application does not create its production schema at startup.

## Backend setup

From PowerShell:

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# Set DATABASE_URL and JWT_SECRET in backend/.env before starting.
alembic upgrade head
python run.py
```

The `.env.example` uses a PostgreSQL URL with a replace-me password placeholder. Keep real local credentials and JWT secrets in the ignored `backend/.env`; never commit it. The expected local database is `university_management` on localhost. SQLite can be selected with `DATABASE_URL=sqlite:///./university.db`.

On development startup, the backend runs an idempotent sample-data seed after confirming a migration has been applied. Seed manually with `python -m app.seed` from `backend/`. Production startup never seeds demo accounts. Tables are created and changed only through migrations.

The development seed includes demo accounts: admin `admin` / `admin123`; faculty `F001` / `faculty123` and `F002` / `faculty456`; students `2024CS1042` / `student123` and `2024EE1001` / `student456`. These weak demo credentials are only for an isolated development database. Never expose them or reuse them in a deployed environment.

## Migration workflow

Run commands from `backend/`:

```powershell
alembic upgrade head
alembic current
alembic history
alembic downgrade -1
```

After changing models, create a reviewed migration with `alembic revision --autogenerate -m "describe the schema change"`, inspect the generated revision, then apply `alembic upgrade head`. Do not use `Base.metadata.create_all()` for production schema management.

## Frontend setup

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Set `VITE_API_URL` in `frontend/.env` when the backend does not use `http://localhost:8000`.

## Architecture

- `backend/app/core/`: settings, JWT security, authorization dependencies.
- `backend/app/database/`: SQLAlchemy base, engine, and request-scoped sessions.
- `backend/app/models/`: authentication identity, academic structure, teaching offerings, and learning records.
- `backend/app/routers/`: authenticated API routes; domain checks are shared through services.
- `backend/app/services/`: grading, audit, ownership checks, and serializers.
- `backend/alembic/`: versioned schema migrations.
- `frontend/src/api/`: shared authenticated API client; pages do not use `mockData.js` as a data source.

Principal entities include User, Student, Faculty, Department, AcademicYear, Semester, AdmissionApplication, Course, CourseOffering, Enrollment, ClassSchedule, AttendanceSession/AttendanceRecord, Assignment/Submission, Exam/ExamSchedule, Result, Notice, Notification, and AuditLog. Phase 3 adds the admission review-to-student workflow, course offering lifecycle and capacity-aware enrollment, academic history, student/faculty schedules and rosters, and lifecycle notifications. Unsupported timetable, submission file storage, and grading summaries are not fabricated.

The Phase 3 schema revision is `f54c14450324` (parent `80d2893ee48c`). Apply it with `alembic upgrade head` from `backend/`.

## Checks

```powershell
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
alembic upgrade head
cd ..\frontend
npm run lint
npm run build
```

The integration suite uses the PostgreSQL database configured by `DATABASE_URL` and rolls its test data back. Do not point it at a shared or production database. Unimplemented workflows should show unavailable states instead of fabricated data.
