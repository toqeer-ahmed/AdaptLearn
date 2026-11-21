"""Data access and repository layer package.

Database queries and persistence operations for each entity reside here,
keeping database interaction decoupled from business logic and controllers.
"""
from app.repositories.adaptive_repository import (
    AdaptiveRepository,
    get_adaptive_repository,
)
from app.repositories.progress_repository import (
    AttemptRecord,
    ProgressRepository,
    QuestionStatsRecord,
    get_progress_repository,
)
from app.repositories.user_repository import (
    UserRecord,
    UserRepository,
    get_user_repository,
)

__all__ = [
    "AdaptiveRepository",
    "AttemptRecord",
    "ProgressRepository",
    "QuestionStatsRecord",
    "UserRecord",
    "UserRepository",
    "get_adaptive_repository",
    "get_progress_repository",
    "get_user_repository",
]
