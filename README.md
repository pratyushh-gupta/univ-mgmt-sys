# University Management System

University Management System with a FastAPI/SQLAlchemy backend and React/Vite frontend. Phase 1 keeps SQLite for local development and organizes the current API and authentication layers. PostgreSQL, Alembic migrations, and the expanded academic data model are reserved for Phase 2.

## Backend setup (Windows PowerShell)

```powershell
cd backend
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

The backend listens on http://localhost:8000 and API docs are at http://localhost:8000/docs. SQLite is the default (`DATABASE_URL=sqlite:///./university.db`). Database tables are initialized on startup; demo accounts and sample data are seeded only when `ENVIRONMENT=development`. Production requires an explicit non-placeholder `JWT_SECRET` of at least 32 characters and does not seed demo data. Never commit `.env`.

## Frontend setup (Windows PowerShell)

```powershell
cd frontend
npm ci
Copy-Item .env.example .env
npm run dev
```

Vite starts at http://localhost:5173. Configure the backend URL with `VITE_API_URL` (default http://localhost:8000).

## Authentication

The frontend submits the account ID and password to `POST /auth/login`, stores the returned bearer token in browser local storage, and restores the user session from `GET /auth/me`. Backend dependencies enforce authentication and Admin, Faculty, and Student roles. Logout removes the saved token. Seeded development accounts are documented in [backend/README.md](backend/README.md).

Some dashboard content depends on services not represented by the current API (including timetables and phone numbers); these are labeled in the UI instead of supplied as fake records. PostgreSQL/Alembic and database expansion are later-phase work.
