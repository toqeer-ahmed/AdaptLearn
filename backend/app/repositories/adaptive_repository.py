"""Repository layer for adaptive learning data access (AdaptLearn M3).

Requirements Traceability:
- FR-16: Retrieve student response history for topic recalculations.
- FR-20: Persist and retrieve course-specific adaptive parameters.
- NFR-07: Parameterized queries / ORM mapping.
- NFR-08: Transactional integrity and persistence across restarts.
- Decision D6: SQLAlchemy 2.0 ORM with PostgreSQL-compatible architecture.
"""
import json

from sqlalchemy.orm import Session, sessionmaker

from app.db.session import SessionLocal, init_db
from app.engine.mastery_calculator import MasteryParameters, ResponseRecord
from app.engine.recommendation_strategy import TopicRecommendationInput
from app.models.adaptive import CourseSettingsModel, CourseTopicModel, StudentTopicResponseModel
from app.models.course import TopicModel, TopicPrerequisiteModel


class AdaptiveRepository:
    """SQLAlchemy persistent repository managing adaptive course settings and response history.

    Replaces volatile Python dictionaries with ACID-compliant SQLite/PostgreSQL storage.
    Guarantees state survival across process recreation and server restarts.
    """

    def __init__(self, session_factory: sessionmaker[Session] | None = None) -> None:
        self.session_factory = session_factory or SessionLocal
        init_db()

    def clear(self) -> None:
        """Reset repository state (used for test isolation)."""
        with self.session_factory() as session:
            session.query(StudentTopicResponseModel).delete()
            session.query(CourseTopicModel).delete()
            session.query(CourseSettingsModel).delete()
            session.commit()

    def get_course_settings(self, course_id: int) -> MasteryParameters:
        """Retrieve course adaptive parameters; returns M1 baseline defaults if not set."""
        with self.session_factory() as session:
            row = session.query(CourseSettingsModel).filter_by(course_id=course_id).first()
            if row is None:
                return MasteryParameters()
            return MasteryParameters(
                window_size=row.window_size,
                easy_weight=row.easy_weight,
                medium_weight=row.medium_weight,
                hard_weight=row.hard_weight,
                weak_threshold=row.weak_threshold,
                proficient_threshold=row.proficient_threshold,
                min_responses=row.min_responses,
            )

    def save_course_settings(self, course_id: int, params: MasteryParameters) -> MasteryParameters:
        """Persist updated adaptive parameters for a course."""
        with self.session_factory() as session:
            row = session.query(CourseSettingsModel).filter_by(course_id=course_id).first()
            if row is None:
                row = CourseSettingsModel(course_id=course_id)
                session.add(row)

            row.window_size = params.window_size
            row.easy_weight = params.easy_weight
            row.medium_weight = params.medium_weight
            row.hard_weight = params.hard_weight
            row.weak_threshold = params.weak_threshold
            row.proficient_threshold = params.proficient_threshold
            row.min_responses = params.min_responses

            session.commit()
            return params

    def get_student_topic_responses(self, student_id: int, topic_id: int) -> list[ResponseRecord]:
        """Retrieve historical responses for a student in a topic in insertion order."""
        with self.session_factory() as session:
            rows = (
                session.query(StudentTopicResponseModel)
                .filter_by(student_id=student_id, topic_id=topic_id)
                .order_by(StudentTopicResponseModel.id.asc())
                .all()
            )
            return [ResponseRecord(difficulty=r.difficulty, is_correct=r.is_correct) for r in rows]

    def append_student_response(self, student_id: int, topic_id: int, record: ResponseRecord) -> None:
        """Record an attempt response for a student in a topic (TC-16-4)."""
        with self.session_factory() as session:
            row = StudentTopicResponseModel(
                student_id=student_id,
                topic_id=topic_id,
                difficulty=record.difficulty,
                is_correct=record.is_correct,
            )
            session.add(row)
            session.commit()

    def get_course_topics(self, course_id: int) -> list[TopicRecommendationInput]:
        """Retrieve all topic candidates for a course.

        Dual-Source Resolution (GAP-03):
        1. Authoritative: Queries canonical M1 TopicModel and TopicPrerequisiteModel.
        2. Fallback: Queries legacy CourseTopicModel ONLY when no canonical M1 topic records
           exist for this course.
        Note: If canonical topic records exist but are all inactive, returns [] without falling back.
        """
        with self.session_factory() as session:
            # Check if ANY canonical M1 topic records exist for this course
            canonical_exists = (
                session.query(TopicModel.id)
                .filter_by(course_id=course_id)
                .first()
                is not None
            )

            if canonical_exists:
                # Retrieve active canonical topics ordered by order_index, then id
                active_topics = (
                    session.query(TopicModel)
                    .filter_by(course_id=course_id, is_active=True)
                    .order_by(TopicModel.order_index.asc(), TopicModel.id.asc())
                    .all()
                )
                if not active_topics:
                    return []

                active_topic_ids = [t.id for t in active_topics]
                active_id_set = set(active_topic_ids)

                # Query prerequisites for active topics
                prereq_rows = (
                    session.query(TopicPrerequisiteModel)
                    .filter(TopicPrerequisiteModel.topic_id.in_(active_topic_ids))
                    .all()
                )
                prereq_map: dict[int, list[int]] = {tid: [] for tid in active_topic_ids}
                for p in prereq_rows:
                    if p.prerequisite_topic_id in active_id_set:
                        prereq_map[p.topic_id].append(p.prerequisite_topic_id)

                result: list[TopicRecommendationInput] = []
                for t in active_topics:
                    result.append(
                        TopicRecommendationInput(
                            topic_id=t.id,
                            name=t.title,
                            mastery_level="Not Assessed",
                            score=0.0,
                            prerequisites=tuple(sorted(prereq_map.get(t.id, []))),
                        )
                    )
                return result

            # Fallback: Check legacy course_topics table
            legacy_rows = (
                session.query(CourseTopicModel)
                .filter_by(course_id=course_id)
                .order_by(CourseTopicModel.order_index.asc(), CourseTopicModel.id.asc())
                .all()
            )
            result = []
            for r in legacy_rows:
                prereqs = tuple(json.loads(r.prerequisites_json)) if r.prerequisites_json else ()
                result.append(
                    TopicRecommendationInput(
                        topic_id=r.topic_id,
                        name=r.name,
                        mastery_level=r.mastery_level or "Not Assessed",
                        score=r.score or 0.0,
                        prerequisites=prereqs,
                    )
                )
            return result

    def set_course_topics(
        self,
        course_id: int,
        topics: list[TopicRecommendationInput],
        prerequisites: dict[int, set[int]] | None = None,
    ) -> None:
        """Populate course topics and prerequisite graph atomically in one transaction."""
        with self.session_factory() as session:
            session.query(CourseTopicModel).filter_by(course_id=course_id).delete()
            for idx, t in enumerate(topics):
                if prerequisites and t.topic_id in prerequisites:
                    prereq_list = sorted(list(prerequisites[t.topic_id]))
                else:
                    prereq_list = list(t.prerequisites) if t.prerequisites else []

                row = CourseTopicModel(
                    course_id=course_id,
                    topic_id=t.topic_id,
                    name=t.name,
                    mastery_level=getattr(t, "mastery_level", "Not Assessed"),
                    score=getattr(t, "score", 0.0),
                    order_index=idx,
                    prerequisites_json=json.dumps(prereq_list),
                )
                session.add(row)
            session.commit()

    def get_course_prerequisites(self, course_id: int) -> dict[int, set[int]]:
        """Retrieve course prerequisite mapping (topic_id -> set of prerequisite IDs).

        Dual-Source Resolution (GAP-03):
        1. Authoritative: Queries canonical M1 TopicPrerequisiteModel for active topics.
        2. Fallback: Queries legacy CourseTopicModel ONLY when no canonical M1 topic records exist.
        Note: If canonical topic records exist but are all inactive, returns {} without falling back.
        """
        with self.session_factory() as session:
            canonical_exists = (
                session.query(TopicModel.id)
                .filter_by(course_id=course_id)
                .first()
                is not None
            )

            if canonical_exists:
                active_topics = (
                    session.query(TopicModel)
                    .filter_by(course_id=course_id, is_active=True)
                    .order_by(TopicModel.order_index.asc(), TopicModel.id.asc())
                    .all()
                )
                if not active_topics:
                    return {}

                active_topic_ids = [t.id for t in active_topics]
                active_id_set = set(active_topic_ids)

                prereq_rows = (
                    session.query(TopicPrerequisiteModel)
                    .filter(TopicPrerequisiteModel.topic_id.in_(active_topic_ids))
                    .all()
                )
                result: dict[int, set[int]] = {tid: set() for tid in active_topic_ids}
                for p in prereq_rows:
                    if p.prerequisite_topic_id in active_id_set:
                        result[p.topic_id].add(p.prerequisite_topic_id)
                return result

            # Fallback: Query legacy course_topics table
            rows = session.query(CourseTopicModel).filter_by(course_id=course_id).all()
            result = {}
            for r in rows:
                prereq_list = json.loads(r.prerequisites_json) if r.prerequisites_json else []
                result[r.topic_id] = set(prereq_list)
            return result


# Global singleton instance for dependency injection
_global_adaptive_repo: AdaptiveRepository | None = None


def get_adaptive_repository() -> AdaptiveRepository:
    """FastAPI dependency provider for AdaptiveRepository."""
    global _global_adaptive_repo
    if _global_adaptive_repo is None:
        _global_adaptive_repo = AdaptiveRepository()
    return _global_adaptive_repo
