"""Business logic and domain services package.

Core domain rules, assessment scoring, adaptive recommendation algorithms,
and progress computation are organized into service modules here.
"""
from app.services.adaptive_service import (
    AdaptiveService,
    get_adaptive_service,
)
from app.services.analytics_service import (
    AnalyticsService,
    get_analytics_service,
)
from app.services.auth_service import (
    AuthService,
    get_auth_service,
)
from app.services.course_service import (
    CourseService,
    get_course_service,
)
from app.services.progress_service import (
    ProgressService,
    get_progress_service,
)

__all__ = [
    "AdaptiveService",
    "AnalyticsService",
    "AuthService",
    "CourseService",
    "ProgressService",
    "get_adaptive_service",
    "get_analytics_service",
    "get_auth_service",
    "get_course_service",
    "get_progress_service",
]
