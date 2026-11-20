from fastapi import APIRouter
from app.api.v1.endpoints import health

api_router = APIRouter()

# Core system endpoints
api_router.include_router(health.router, tags=["Health"])

# Placeholders for future team module routers:
# M1 (Hiba):      api_router.include_router(users.router, prefix="/users", tags=["Users"])
#                 api_router.include_router(courses.router, prefix="/courses", tags=["Courses"])
# M2 (Mustajaab): api_router.include_router(quizzes.router, prefix="/quizzes", tags=["Quizzes"])
# M3 (Toqeer):    api_router.include_router(adaptive.router, prefix="/adaptive", tags=["Adaptive Engine"])
# M4 (Hiba):      api_router.include_router(learning_paths.router, prefix="/learning-paths", tags=["Learning Paths"])
# M5 (Toqeer):    api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

