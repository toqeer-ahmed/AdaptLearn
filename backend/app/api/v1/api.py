from fastapi import APIRouter

from app.api.v1.endpoints import adaptive, analytics, auth, health, progress

api_router = APIRouter()

# Core system endpoints
api_router.include_router(health.router, tags=["Health"])

# Module 1: Authentication & User Management (Hiba / Core)
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# Module 3: Adaptive Learning Engine (Toqeer)
api_router.include_router(adaptive.router, tags=["Adaptive Engine"])

# Module 5: Progress Analytics & Instructor Dashboard (Toqeer)
api_router.include_router(progress.router, tags=["Progress & Analytics"])
api_router.include_router(analytics.router, tags=["Instructor Analytics"])

# Placeholders for future team module routers:
# M1 (Hiba):      api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
# M2 (Mustajaab): api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
# M4 (Hiba):      api_router.include_router(learning_paths.router, prefix="/learning-paths", tags=["Learning Paths"])
