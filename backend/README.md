# UniPortal FastAPI Backend

Backend for the existing `univ-mgmt-sys` React/Vite project.

## Stack
- FastAPI
- SQLAlchemy 2.x
- SQLite by default
- JWT authentication
- Role-based authorization
- CORS for Vite (`http://localhost:5173`)

## Run

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux

python run.py
```

API docs: http://localhost:8000/docs

## Seeded accounts

| Role | User ID | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Faculty | `F001` | `faculty123` |
| Student | `2024CS1042` | `student123` |

## Main endpoints

- `POST /auth/login`
- `GET /auth/me`
- `GET/POST/DELETE /students`
- `GET/POST/DELETE /faculty`
- `GET/POST/DELETE /courses`
- `GET /student/courses`
- `GET /student/attendance`
- `GET /student/results`
- `GET /student/assignments`
- `GET /notices`
- `GET /faculty/courses`
- `GET /faculty/roster/{course_code}`
- `POST /attendance`
- `POST /results`

The frontend currently uses mock data, so its components still need to be switched from `src/data/mockData.js` to these API endpoints.
