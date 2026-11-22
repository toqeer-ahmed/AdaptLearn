# AdaptLearn M1 — Database & Model Impact Audit
## Comprehensive Architecture Inspection Prior to M1 Domain Model Implementation

**Document Reference:** `docs/sqa/M1_DATABASE_MODEL_IMPACT_AUDIT.md`  
**Document Type:** Software Quality Assurance Architecture & Database Impact Audit  
**Author:** Hiba Zulfiqar (`2023246`) — Lead for M1 (User & Course Management) & M4 (Personalized Learning Paths)  
**Target Reviewers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Git Branch:** `feature/m1-course-management`  
**Starting Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f` (`fix(ci): resolve backend test collection failure`)  
**Backend Test Baseline:** **150 passed, 0 failed, 0 skipped (100% green)**  
**Status:** **AUDIT COMPLETE — PENDING IMPLEMENTATION**  
**Date:** November 21, 2026  

---

## 1. Executive Summary

Prior to authoring the SQLAlchemy domain models for **Module 1 (User & Course Management)**, this audit performs an exhaustive static and dynamic inspection of the existing database schema, ORM declarations, cross-module consumers, and test dependencies across the AdaptLearn backend.

### Core Audit Findings
1. **Existing Tables Discovered**: The repository currently declares **8 persistent tables** across three model files (`app/models/user.py`, `app/models/adaptive.py`, `app/models/progress.py`), orchestrated by a shared `DeclarativeBase` in `app/db/base.py`.
2. **The `course_enrollments` Conflict (Decision D6)**: The table `course_enrollments` already exists in `app/models/progress.py` and is actively queried by `ProgressRepository`. SQLAlchemy does **not** permit two distinct classes on the same `DeclarativeBase` metadata to share a `__tablename__` without raising `InvalidRequestError`. M1 must coordinate ownership of this model without duplicate declarations.
3. **The `course_owners` Transition (Decision D7)**: Course ownership is currently tracked via an independent table `course_owners` (`CourseOwnerModel`) queried by `ProgressRepository.is_course_owner()` and seeded by 8+ integration/unit test files. Deleting this table or changing its behavior prematurely will break 15+ tests in M5 and cross-module integration suites.
4. **The `course_topics` Fixture in M3**: M3 defines `course_topics` (`CourseTopicModel`) in `app/models/adaptive.py` with a denormalized `prerequisites_json` TEXT column. M1's authoritative `topics` and `topic_prerequisites` tables will normalize this structure without colliding with `course_topics`.
5. **Zero Regression Guarantee**: A dual-source compatibility strategy for `ProgressRepository` and unified model registration in `app/models/__init__.py` is designed to guarantee that all 150 baseline tests remain 100% passing.

---

## 2. Existing Database Architecture & Model Inventory (Verified Facts)

All existing models inherit from `app.db.base.Base` (`DeclarativeBase`), conforming to SQLAlchemy 2.0 ORM conventions. The table below catalogs all existing models currently declared in the repository:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             EXISTING DATABASE ENTITY CATALOG                           │
├────┬────────────────────────────┬─────────────────────────────┬────────────────────────┤
│ #  │ Table Name                 │ ORM Class Name              │ Source File            │
├────┼────────────────────────────┼─────────────────────────────┼────────────────────────┤
│ 1  │ users                      │ UserModel                   │ app/models/user.py     │
│ 2  │ course_adaptive_settings   │ CourseSettingsModel         │ app/models/adaptive.py │
│ 3  │ student_topic_responses    │ StudentTopicResponseModel   │ app/models/adaptive.py │
│ 4  │ course_topics              │ CourseTopicModel            │ app/models/adaptive.py │
│ 5  │ course_enrollments         │ EnrollmentModel             │ app/models/progress.py │
│ 6  │ course_owners              │ CourseOwnerModel            │ app/models/progress.py │
│ 7  │ quiz_attempts              │ AttemptModel                │ app/models/progress.py │
│ 8  │ course_question_stats      │ QuestionStatsModel          │ app/models/progress.py │
└────┴────────────────────────────┴─────────────────────────────┴────────────────────────┘
```

### 2.1 Detailed Schema Breakdown of Relevant Models

#### 1. `course_enrollments` (`EnrollmentModel` in `backend/app/models/progress.py`)
```python
class EnrollmentModel(Base):
    """Course enrollment records (FR-04, NFR-09)."""
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, nullable=False, index=True)
    course_id = Column(Integer, nullable=False, index=True)

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )
```
- **Primary Key:** `id` (Integer, autoincrement)
- **Attributes:** `student_id` (Integer, index), `course_id` (Integer, index)
- **Constraints:** Composite unique constraint `uq_student_course_enrollment` on `(student_id, course_id)`.
- **Foreign Keys:** None declared at the DDL level (logical foreign keys to `users.id` and `courses.id`).

#### 2. `course_owners` (`CourseOwnerModel` in `backend/app/models/progress.py`)
```python
class CourseOwnerModel(Base):
    """Course ownership mapping for instructors (NFR-05, NFR-06)."""
    __tablename__ = "course_owners"

    course_id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, nullable=False, index=True)
```
- **Primary Key:** `course_id` (Integer)
- **Attributes:** `instructor_id` (Integer, index)
- **Foreign Keys:** None declared at the DDL level.

#### 3. `course_topics` (`CourseTopicModel` in `backend/app/models/adaptive.py`)
```python
class CourseTopicModel(Base):
    """Course topic candidates and prerequisite graphs for recommendation strategy."""
    __tablename__ = "course_topics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, nullable=False, index=True)
    topic_id = Column(Integer, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    mastery_level = Column(String(30), nullable=False, default="Not Assessed")
    score = Column(Float, nullable=False, default=0.0)
    order_index = Column(Integer, nullable=False, default=0)
    prerequisites_json = Column(Text, nullable=False, default="[]")
```
- **Primary Key:** `id` (Integer, autoincrement)
- **Attributes:** `course_id`, `topic_id`, `name`, `mastery_level`, `score`, `order_index`, `prerequisites_json` (JSON-encoded string list of integers).

#### 4. `users` (`UserModel` in `backend/app/models/user.py`)
```python
class UserModel(Base):
    """User account entity (FR-01, FR-02, NFR-03)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(254), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'student' or 'instructor'
    is_active = Column(Boolean, nullable=False, default=True)
```

---

## 3. Cross-Module Consumption Audit (Verified Facts)

An exhaustive search across `backend/app` and `backend/tests` identifies all locations where existing course, ownership, and enrollment tables are consumed:

```
                               Cross-Module Model Consumption
┌───────────────────────┐         ┌─────────────────────────┐         ┌─────────────────────────┐
│ M1 (Course / Auth)    │         │ M5 (Progress/Analytics) │         │ M3 (Adaptive Engine)    │
│ - UserModel           │         │ - EnrollmentModel       │         │ - CourseTopicModel      │
│                       │         │ - CourseOwnerModel      │         │ - CourseSettingsModel   │
│                       │         │ - AttemptModel          │         │ - StudentResponseModel  │
└───────────┬───────────┘         └────────────┬────────────┘         └────────────┬────────────┘
            │                                  │                                   │
            ▼                                  ▼                                   ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                 ProgressRepository Methods                                    │
│ - enroll_student(student_id, course_id)        -> inserts into course_enrollments             │
│ - is_student_enrolled(student_id, course_id)   -> queries course_enrollments                  │
│ - get_course_enrolled_students(course_id)      -> selects student_id from course_enrollments  │
│ - set_course_owner(course_id, instructor_id)   -> inserts/updates course_owners               │
│ - is_course_owner(course_id, instructor_id)    -> queries course_owners                       │
└──────────────────────────────────────────────┬────────────────────────────────────────────────┘
                                               │
                                               ▼
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   API Endpoints Enforcing Ownership                           │
│ - app/api/v1/endpoints/analytics.py: _verify_instructor_course_access() -> is_course_owner() │
│ - app/api/v1/endpoints/progress.py: get_student_progress() -> is_student_enrolled()           │
│ - app/api/v1/endpoints/progress.py: get_student_progress() -> is_course_owner()               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Consumers of `EnrollmentModel` / `course_enrollments`

1. **Repository Layer (`backend/app/repositories/progress_repository.py`)**:
   - `clear()`: Line 61 deletes all records from `EnrollmentModel`.
   - `enroll_student(student_id, course_id)`: Line 67 checks existence; Line 69 instantiates `EnrollmentModel`.
   - `is_student_enrolled(student_id, course_id)`: Line 76 queries `EnrollmentModel` by `student_id` and `course_id`.
   - `get_course_enrolled_students(course_id)`: Line 81 queries `EnrollmentModel.student_id` for roster aggregation.
2. **Service Layer (`backend/app/services/analytics_service.py`)**:
   - Lines 45 & 94 call `progress_repo.get_course_enrolled_students(course_id)` to calculate cohort mastery distributions and student rosters.
3. **API Layer (`backend/app/api/v1/endpoints/progress.py`)**:
   - Line 57 enforces that a student requesting progress must be enrolled (`is_student_enrolled()`), returning `403 Forbidden` if false.
4. **Unit & Persistence Tests (`backend/tests/unit/test_persistence.py`)**:
   - Lines 153–164 test enrollment survival across database restart (`repo.enroll_student`, `repo.is_student_enrolled`, `repo.get_course_enrolled_students`).

### 3.2 Consumers of `CourseOwnerModel` / `course_owners`

1. **Repository Layer (`backend/app/repositories/progress_repository.py`)**:
   - `clear()`: Line 60 deletes all records from `CourseOwnerModel`.
   - `set_course_owner(course_id, instructor_id)`: Lines 87–93 insert or update ownership mapping.
   - `is_course_owner(course_id, instructor_id)`: Line 98 queries `CourseOwnerModel` and returns boolean comparison.
2. **API Layer (`backend/app/api/v1/endpoints/analytics.py`)**:
   - Line 40 in `_verify_instructor_course_access()` calls `repo.is_course_owner(course_id, user.user_id)`. If false, raises `403 Forbidden` (`"Instructor does not own this course"`).
3. **API Layer (`backend/app/api/v1/endpoints/progress.py`)**:
   - Lines 64 & 108 check `repo.is_course_owner(id, current_user.user_id)` before returning progress or attempt history to instructors.
4. **Integration & Security Test Suites**:
   - `tests/integration/test_instructor_analytics_api.py`: Lines 48, 71, 92, 118, 132 call `p_repo.set_course_owner()` to set up authorized instructor tests.
   - `tests/integration/test_cross_module_integration.py`: Lines 67 & 242 call `p_repo.set_course_owner()` for end-to-end lifecycle and cross-instructor privacy tests.
   - `tests/integration/test_progress_api.py`: Line 105 sets course ownership for attempt history queries.
   - `tests/unit/test_auth.py`: Line 136 sets course ownership for instructor token access tests.
   - `tests/unit/test_persistence.py`: Lines 155, 166, 167 verify course ownership persistence across restart.
   - `tests/unit/test_security_auth.py`: Lines 342 & 355 configure ownership in role authorization tests.

### 3.3 Consumers of `CourseTopicModel` / `course_topics`

1. **Repository Layer (`backend/app/repositories/adaptive_repository.py`)**:
   - `get_course_topics(course_id)`: Lines 101–118 query `CourseTopicModel` ordered by `order_index`.
   - `set_course_topics(course_id, topics, prerequisites)`: Lines 128–145 populate `CourseTopicModel` and encode `prerequisites_json`.
   - `get_course_prerequisites(course_id)`: Lines 150–155 deserialize `prerequisites_json`.
2. **Unit Tests (`backend/tests/unit/test_recommendation_strategy.py`)**:
   - Validates recommendation ranking algorithms using candidate topic inputs.

---

## 4. Proposed M1 Domain Model Design

In accordance with approved Decisions D1, D2, D3, D6, D7, and D10, the new M1 models will be located in `backend/app/models/course.py` and inherit from `app.db.base.Base`.

```
                              Proposed M1 Relational Entity Model
 ┌─────────────────────────┐           1:N           ┌─────────────────────────┐
 │       CourseModel       ├─────────────────────────┤       TopicModel        │
 │  (table: 'courses')     │                         │  (table: 'topics')      │
 ├─────────────────────────┤                         ├─────────────────────────┤
 │ id (PK, int)            │                         │ id (PK, int)            │
 │ title (varchar 200)     │                         │ course_id (FK -> course)│
 │ description (text)      │                         │ title (varchar 200)     │
 │ course_code (UQ, v50)   │                         │ description (text)      │
 │ instructor_id (FK->user)│                         │ order_index (int)       │
 │ is_archived (bool)      │                         │ is_active (bool)        │
 │ created_at (datetime)   │                         │ created_at (datetime)   │
 │ updated_at (datetime)   │                         │ updated_at (datetime)   │
 └───────────┬─────────────┘                         └────────────┬────────────┘
             │                                                    │
             │ 1:N                                                │ 1:N (Self-Ref DAG)
             ▼                                                    ▼
 ┌─────────────────────────┐                         ┌─────────────────────────┐
 │     EnrollmentModel     │                         │ TopicPrerequisiteModel  │
 │(table:'course_enroll')  │                         │(table:'topic_prereqs')  │
 ├─────────────────────────┤                         ├─────────────────────────┤
 │ id (PK, int)            │                         │ id (PK, int)            │
 │ student_id (FK->user)   │                         │ topic_id (FK->topic)    │
 │ course_id (FK->course)  │                         │ prereq_id (FK->topic)   │
 │ enrolled_at (datetime)  │                         │ created_at (datetime)   │
 └─────────────────────────┘                         └─────────────────────────┘
```

### 4.1 Detailed Code Specification for `backend/app/models/course.py`

```python
"""SQLAlchemy ORM models for Module 1: User & Course Management.

Conforms to Decisions D1, D2, D3, D6, D7, D10.
"""
from datetime import datetime, timezone
from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base


class CourseModel(Base):
    """Authoritative course entity (FR-04, FR-05, Decisions D1, D3, D7)."""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    course_code = Column(String(50), nullable=False, unique=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_archived = Column(Boolean, nullable=False, default=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    instructor = relationship("UserModel", backref="authored_courses")
    topics = relationship(
        "TopicModel",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="TopicModel.order_index",
    )
    enrollments = relationship(
        "EnrollmentModel",
        back_populates="course",
        cascade="all, delete-orphan",
    )


class TopicModel(Base):
    """Authoritative course topic entity (FR-06, FR-07, Decisions D2, D10)."""
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False, default=0, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("CourseModel", back_populates="topics")
    prerequisites = relationship(
        "TopicPrerequisiteModel",
        foreign_keys="TopicPrerequisiteModel.topic_id",
        back_populates="topic",
        cascade="all, delete-orphan",
    )
    required_by = relationship(
        "TopicPrerequisiteModel",
        foreign_keys="TopicPrerequisiteModel.prerequisite_topic_id",
        back_populates="prerequisite_topic",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "order_index", name="uq_course_topic_order"),
    )


class TopicPrerequisiteModel(Base):
    """Directed edge representing prerequisite dependencies between topics (FR-08, FR-09)."""
    __tablename__ = "topic_prerequisites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    prerequisite_topic_id = Column(Integer, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    topic = relationship("TopicModel", foreign_keys=[topic_id], back_populates="prerequisites")
    prerequisite_topic = relationship("TopicModel", foreign_keys=[prerequisite_topic_id], back_populates="required_by")

    __table_args__ = (
        UniqueConstraint("topic_id", "prerequisite_topic_id", name="uq_topic_prerequisite_edge"),
        CheckConstraint("topic_id != prerequisite_topic_id", name="chk_no_self_prerequisite"),
    )


class EnrollmentModel(Base):
    """Student course enrollment record conforming to Decision D6.
    
    Adopts exact table name and columns required by M5 ProgressRepository.
    """
    __tablename__ = "course_enrollments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True)
    enrolled_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Relationships
    course = relationship("CourseModel", back_populates="enrollments")
    student = relationship("UserModel", backref="course_enrollments")

    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment"),
    )
```

---

## 5. Files Requiring Modification & Creation

To implement the M1 models safely without regressions in M5 or other modules, the following files are impacted:

| # | File Path | Status | Description of Required Action |
| :-: | :--- | :---: | :--- |
| 1 | `backend/app/models/course.py` | **NEW** | Create authoritative `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, and reconciled `EnrollmentModel`. |
| 2 | `backend/app/models/progress.py` | **MODIFY** | Re-export `EnrollmentModel` from `app.models.course` instead of defining a duplicate table. Retain `CourseOwnerModel` during transition. |
| 3 | `backend/app/models/__init__.py` | **MODIFY** | Export `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, `EnrollmentModel` from `app.models.course`. |
| 4 | `backend/app/repositories/progress_repository.py` | **MODIFY** | Update `is_course_owner()` and `set_course_owner()` to use dual-source resolution (check `CourseModel` first, fallback to `CourseOwnerModel`). |
| 5 | `backend/app/db/session.py` | **VERIFIED** | `init_db()` imports `app.models` and calls `Base.metadata.create_all()`. Automatically picks up new M1 tables. |
| 6 | `backend/tests/unit/test_course_models.py` | **NEW** | Comprehensive unit test suite for M1 models, relationships, cascading deletes, unique constraints, and check constraints. |

---

## 6. Technical Impact & Backward Compatibility Analysis

### 6.1 Solving the `course_enrollments` Table Conflict (Decision D6)
- **The Issue:** `app/models/progress.py` currently defines `class EnrollmentModel(Base): __tablename__ = "course_enrollments"`. If `app/models/course.py` also declares `class EnrollmentModel(Base): __tablename__ = "course_enrollments"`, SQLAlchemy's `DeclarativeBase` raises an immediate `InvalidRequestError: Table 'course_enrollments' is already defined for this MetaData instance`.
- **The Solution:** 
  1. Define the authoritative `EnrollmentModel` in `app/models/course.py` with the exact existing columns: `id`, `student_id`, `course_id`, plus optional metadata `enrolled_at`.
  2. In `app/models/progress.py`, remove the duplicate class declaration and alias the model:
     ```python
     # Backward-compatible re-export for Module 5
     from app.models.course import EnrollmentModel
     ```
  3. This eliminates table definition collisions, preserves exact attribute names (`student_id`, `course_id`), and leaves all existing M5 repository methods completely functional.

### 6.2 Safe Transition for Course Ownership (Decision D7)
- **The Issue:** Existing tests in `test_cross_module_integration.py`, `test_instructor_analytics_api.py`, `test_progress_api.py`, `test_auth.py`, and `test_persistence.py` directly call `progress_repo.set_course_owner(course_id=..., instructor_id=...)` and assert on `is_course_owner()`. If `course_owners` is removed, all these tests will fail because they test M5 without first creating full M1 course entities.
- **The Solution (Dual-Source Query Resolution):**
  Update `ProgressRepository.is_course_owner()` to check `CourseModel` first, and seamlessly fall back to `CourseOwnerModel`:
  ```python
  def is_course_owner(self, course_id: int, instructor_id: int) -> bool:
      with self.session_factory() as session:
          # Check authoritative M1 CourseModel first
          course = session.query(CourseModel).filter_by(id=course_id).first()
          if course is not None:
              return course.instructor_id == instructor_id
          # Fallback to legacy M5 fixture table during transition
          row = session.query(CourseOwnerModel).filter_by(course_id=course_id).first()
          return row.instructor_id == instructor_id if row else False
  ```
  And update `ProgressRepository.set_course_owner()`:
  ```python
  def set_course_owner(self, course_id: int, instructor_id: int) -> None:
      with self.session_factory() as session:
          # Sync to legacy fixture table to satisfy existing tests
          row = session.query(CourseOwnerModel).filter_by(course_id=course_id).first()
          if not row:
              session.add(CourseOwnerModel(course_id=course_id, instructor_id=instructor_id))
          else:
              row.instructor_id = instructor_id
          session.commit()
  ```
  **Result:** Zero existing tests break. New M1 courses automatically enforce ownership via `CourseModel.instructor_id`.

### 6.3 Preserving M3's `course_topics` Fixture
- M3's `AdaptiveRepository` reads from `course_topics` with `prerequisites_json`.
- M1 creates tables `topics` and `topic_prerequisites`.
- Because table names are distinct, M1 models will **not** collide with M3's tables.
- In Milestone 4, `LearningPathService` will read M1's normalized `topics` and `topic_prerequisites` directly, allowing M3's legacy fixture to be phased out when M3 is refactored.

---

## 7. Database Initialization & Migration Implications

### 7.1 Table Creation Mechanics
- AdaptLearn currently uses **dynamic table creation** via `init_db()` in `backend/app/db/session.py`:
  ```python
  def init_db(target_engine=None) -> None:
      import app.models  # Registers all models with Base.metadata
      e = target_engine or engine
      Base.metadata.create_all(bind=e)
  ```
- No Alembic migration tool is configured in `backend/` (no `alembic.ini` or `migrations/` directory).
- When `app.models.__init__.py` imports `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, and `EnrollmentModel`, `Base.metadata.create_all()` will automatically generate:
  - `CREATE TABLE IF NOT EXISTS courses (...)`
  - `CREATE TABLE IF NOT EXISTS topics (...)`
  - `CREATE TABLE IF NOT EXISTS topic_prerequisites (...)`
  - `CREATE TABLE IF NOT EXISTS course_enrollments (...)`
- In SQLite development and automated testing (`pytest` in-memory/tempfile SQLite), tables are created cleanly on startup.

---

## 8. SQA Risk Register & Mitigation Matrix

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MODEL IMPACT RISK REGISTER                                │
├────┬─────────────────────────────┬──────────┬──────────────────────────────────────────┤
│ ID │ Risk Description            │ Severity │ SQA Verification & Mitigation Action     │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R1 │ MetaData collision on       │ CRITICAL │ Define EnrollmentModel in app.models.    │
│    │ course_enrollments table    │          │ course and alias in app.models.progress  │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R2 │ ProgressRepository break-   │ HIGH     │ Implement dual-source query logic in     │
│    │ age on is_course_owner()    │          │ is_course_owner() (CourseModel + legacy) │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R3 │ Attribute naming mismatch:  │ HIGH     │ Retain student_id column name on         │
│    │ student_id vs user_id       │          │ EnrollmentModel for M5 compatibility     │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R4 │ Circular topic prerequisite │ HIGH     │ Enforce CheckConstraint on DB level and  │
│    │ graph locks learning path   │          │ DFS cycle detection in CourseService     │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R5 │ Foreign key cascade deletes │ MEDIUM   │ Configure ondelete="CASCADE" on topics   │
│    │ orphan student attempts     │          │ and prerequisites; restrict if attempts  │
└────┴─────────────────────────────┴──────────┴──────────────────────────────────────────┘
```

---

## 9. Recommended Implementation Sequence for Stage 2 & 3

To guarantee zero regressions throughout development:

```
Step 1: Create backend/app/models/course.py
        - Declare CourseModel, TopicModel, TopicPrerequisiteModel, EnrollmentModel.
        - Run ruff / static check.

Step 2: Update backend/app/models/progress.py
        - Replace local EnrollmentModel declaration with: from app.models.course import EnrollmentModel.
        - Retain CourseOwnerModel.

Step 3: Update backend/app/models/__init__.py
        - Export CourseModel, TopicModel, TopicPrerequisiteModel, EnrollmentModel.

Step 4: Update backend/app/repositories/progress_repository.py
        - Implement dual-source check in is_course_owner() (checks CourseModel, then CourseOwnerModel).

Step 5: Execute Regression Test Suite
        - Run: .\venv\Scripts\pytest.exe
        - Verify: All 150 baseline tests pass with 0 failures.

Step 6: Author backend/tests/unit/test_course_models.py
        - Write 15+ unit tests verifying model creation, foreign keys, cascades, uniqueness.
        - Run pytest -> 165+ tests pass.
```

---

## 10. Audit Conclusion

The database architecture inspection is **complete**. The path to implementing the M1 domain models in `backend/app/models/course.py` is fully mapped with explicit technical safeguards protecting M5 and M3.

**Zero application source code has been altered during this audit.**  
**Ready for user instruction to proceed to Step 1 (authoring `backend/app/models/course.py`).**
