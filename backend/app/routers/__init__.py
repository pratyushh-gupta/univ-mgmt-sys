from fastapi import APIRouter
from .auth import router as auth_router
from .system import router as system_router
from .students import router as students_router
from .faculty import router as faculty_router
from .courses import router as courses_router
from .admin import router as admin_router

api_router = APIRouter()
for domain_router in (auth_router, system_router, students_router, faculty_router, courses_router, admin_router):
    api_router.include_router(domain_router)

__all__ = ["api_router"]
