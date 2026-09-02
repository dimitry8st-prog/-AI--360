from fastapi import APIRouter

from app.web.routes.auth import router as auth_router
from app.web.routes.courses import router as courses_router
from app.web.routes.enrollments import router as enrollments_router
from app.web.routes.health import router as health_router
from app.web.routes.pages import router as pages_router
from app.web.routes.progress import router as progress_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(pages_router)
api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(enrollments_router)
api_router.include_router(progress_router)
