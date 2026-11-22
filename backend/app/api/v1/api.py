from fastapi import APIRouter

from app.api.v1.endpoints import (
    adaptive,
    analytics,
    auth,
    courses,
    health,
    learning_paths,
    progress,
    quizzes,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(courses.router, tags=["Courses"])
api_router.include_router(quizzes.router, tags=["Quizzes & Question Bank"])
api_router.include_router(adaptive.router, tags=["Adaptive Engine"])
api_router.include_router(progress.router, tags=["Student Progress"])
api_router.include_router(analytics.router, tags=["Instructor Analytics"])
api_router.include_router(learning_paths.router, tags=["Learning Paths"])
api_router.include_router(health.router, tags=["Health"])
