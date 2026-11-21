"""Business logic and domain services package.

Core domain rules, assessment scoring, adaptive recommendation algorithms,
and progress computation are organized into service modules here.
"""
from app.services.auth_service import (
    AuthService,
    get_auth_service,
)

# Safely import services with resilience to uncommitted teammate files
try:
    from app.services.quiz_service import (
        QuizService,
        get_quiz_service,
    )
except ImportError:
    QuizService = None  # type: ignore
    get_quiz_service = None  # type: ignore

try:
    from app.services.adaptive_service import (
        AdaptiveService,
        get_adaptive_service,
    )
except ImportError:
    AdaptiveService = None  # type: ignore
    get_adaptive_service = None  # type: ignore

try:
    from app.services.analytics_service import (
        AnalyticsService,
        get_analytics_service,
    )
except ImportError:
    AnalyticsService = None  # type: ignore
    get_analytics_service = None  # type: ignore

try:
    from app.services.progress_service import (
        ProgressService,
        get_progress_service,
    )
except ImportError:
    ProgressService = None  # type: ignore
    get_progress_service = None  # type: ignore

__all__ = [
    "AdaptiveService",
    "AnalyticsService",
    "AuthService",
    "ProgressService",
    "QuizService",
    "get_adaptive_service",
    "get_analytics_service",
    "get_auth_service",
    "get_progress_service",
    "get_quiz_service",
]
