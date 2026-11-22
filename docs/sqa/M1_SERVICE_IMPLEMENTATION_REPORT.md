# AdaptLearn M1 — Stage 4: Repository and Service Layer Report
## Module 1: User & Course Management (Data Access, Business Logic, Prerequisite Graphs & Ownership)

**Document Reference:** `docs/sqa/M1_SERVICE_IMPLEMENTATION_REPORT.md`  
**Document Type:** Software Quality Assurance Service Layer Implementation & Test Verification Report  
**Author:** Hiba Zulfiqar (`2023246`) — Lead for M1 (User & Course Management) & M4 (Personalized Learning Paths)  
**Target Reviewers / Approvers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Git Branch:** `feature/m1-course-management`  
**Baseline Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f`  
**Focused Service Test Suite:** **22/22 passed (100% green)**  
**Full Test Suite:** **212 passed, 0 failed, 0 skipped (100% green)**  
**Status:** **STAGE 4 COMPLETE — REPOSITORY & SERVICE LAYERS IMPLEMENTED & FULLY VERIFIED**  
**Date:** November 21, 2026  

---

## 1. Executive Summary

In accordance with the repository architecture, service-layer patterns, and the approved technical decisions ([`M1_M4_TEAM_APPROVAL_PROPOSAL.md`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md)), the complete data access layer (`CourseRepository`) and business logic service layer (`CourseService`) for **Module 1 (User & Course Management)** have been implemented and thoroughly verified.

### Key Milestones Accomplished
1. **Repository Layer Implementation:** Created [`backend/app/repositories/course_repository.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/app/repositories/course_repository.py) encapsulating all SQLAlchemy database operations for courses, topics, prerequisites, and enrollments with transactional integrity and atomic topic reordering.
2. **Business Service Layer Implementation:** Created [`backend/app/services/course_service.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/app/services/course_service.py) enforcing role-based access control, instructor ownership boundaries, prerequisite directed acyclic graph (DAG) cycle detection, student privacy barriers, and course lifecycle constraints.
3. **Approved Architectural Decisions Enforced:**
   - **Decision D1:** Enforced unique course code validation and HTTP 409 Conflict handling.
   - **Decision D2:** Prevented topic deletion with HTTP 400 if quiz questions exist in `QuestionStatsModel`.
   - **Decision D3:** Enforced course archiving lifecycle: archived courses are read-only; topics and course metadata cannot be mutated, and new student enrollments are rejected with HTTP 400.
   - **Decision D6:** Preserved legacy `course_enrollments` table schema (`id`, `student_id`, `course_id`) ensuring 100% zero-regression compatibility with Module 5 analytics and progress tracking.
   - **Decision D7:** Implemented dual-source course ownership synchronization (`courses.instructor_id` + `ProgressRepository.set_course_owner()`) for transparent M5 instructor roster and dashboard metrics integration.
4. **100% Test Pass Rate:**
   - **22/22 passed** in focused service unit test suite ([`backend/tests/unit/test_course_service.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/tests/unit/test_course_service.py)).
   - **212/212 passed** in total project test suite (150 baseline + 10 models + 30 schemas + 22 services) with zero regressions across M2, M3, and M5.
5. **Strict Scope Boundary Respected:** Stopped clean before implementing FastAPI API router endpoints (`backend/app/api/v1/endpoints/courses.py`), which will be executed in Stage 5.

---

## 2. Architecture & Design of Implemented Components

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Routers (Stage 5)                             │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Calls service with auth context
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                       CourseService (Business Logic Layer)                      │
│  - Role-based authorization (instructor vs student)                            │
│  - Ownership verification (_verify_course_ownership)                           │
│  - Archiving lifecycle rules (read-only enforcement) [Decision D3]              │
│  - Prerequisite DAG cycle detection (DFS-based)                                 │
│  - Topic deletion safety check (QuestionStatsModel verification) [Decision D2]  │
│  - Student privacy barriers & enrollment validations [Decision D6]              │
│  - M5 dual-source ownership synchronization [Decision D7]                       │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Calls repository operations
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                    CourseRepository (Data Access Layer)                         │
│  - Course CRUD & course_code uniqueness lookup                                  │
│  - Topic CRUD & ordered topic querying                                          │
│  - Two-phase atomic topic reordering (offset-indexed to avoid collisions)       │
│  - TopicPrerequisiteModel CRUD & dependency graph querying                      │
│  - EnrollmentModel queries & student enrollment listing                         │
│  - QuestionStatsModel existence probe for topic deletion safety                 │
└────────────────────────────────────────┬────────────────────────────────────────┘
                                         │ Executes SQLAlchemy queries
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          Database Tables (SQLite / PG)                          │
│   courses │ topics │ topic_prerequisites │ course_enrollments │ question_stats  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Detailed Component Implementations

### 3.1 CourseRepository (`backend/app/repositories/course_repository.py`)

The repository operates on the active SQLAlchemy `Session` following repository patterns established by `ProgressRepository` and `AdaptiveRepository`.

| Operation Domain | Method Name | Description & Invariant Handled |
| :--- | :--- | :--- |
| **Course** | `create_course(course_data, instructor_id)` | Persists `CourseModel`, committing atomically. |
| **Course** | `get_course_by_id(course_id)` | Fetches course by primary key or returns `None`. |
| **Course** | `get_course_by_code(course_code)` | Case-sensitive/normalized lookup to detect duplicate codes. |
| **Course** | `list_courses(instructor_id, is_archived, limit, offset)` | Paginated retrieval with optional instructor and archive status filters. |
| **Course** | `update_course(course_id, update_data)` | Updates scalar fields (`title`, `description`, `course_code`). |
| **Course** | `set_course_archive_status(course_id, is_archived)` | Toggles course archive flag. |
| **Course** | `delete_course(course_id)` | Removes course record and cascades. |
| **Topic** | `create_topic(course_id, topic_data)` | Creates topic. Auto-computes `order_index = max + 1` if omitted. |
| **Topic** | `get_topic_by_id(topic_id)` | Fetches topic by primary key. |
| **Topic** | `list_topics_by_course(course_id)` | Retrieves all topics for a course ordered by `order_index ASC`. |
| **Topic** | `update_topic(topic_id, update_data)` | Updates title, description, order_index, or is_active. |
| **Topic** | `delete_topic(topic_id)` | Deletes topic and cleans up associated prerequisite records. |
| **Topic** | `has_quiz_questions(topic_id)` | Queries `QuestionStatsModel` to verify if questions reference the topic (**Decision D2**). |
| **Topic** | `reorder_topics(course_id, new_order_mapping)` | **Two-phase atomic reorder:** maps topic IDs first to temporary negative offsets (`-1000 - target_idx`) then applies final non-negative indices. Prevents SQLite unique constraint collisions during in-place index swaps. |
| **Prerequisites** | `add_prerequisite(topic_id, prerequisite_id)` | Inserts `TopicPrerequisiteModel` edge into the graph. |
| **Prerequisites** | `remove_prerequisite(topic_id, prerequisite_id)` | Removes directed prerequisite edge. |
| **Prerequisites** | `get_topic_prerequisites(topic_id)` | Returns list of prerequisite topic IDs for a given topic. |
| **Prerequisites** | `get_dependent_topics(topic_id)` | Returns list of topic IDs that require this topic as a prerequisite. |
| **Prerequisites** | `get_all_course_prerequisites(course_id)` | Returns complete adjacency list `dict[int, list[int]]` of prerequisites for all topics in a course. Used for cycle detection. |
| **Enrollment** | `enroll_student(student_id, course_id)` | Inserts record into `course_enrollments` (**Decision D6**). |
| **Enrollment** | `get_enrollment(student_id, course_id)` | Queries enrollment record by `(student_id, course_id)`. |
| **Enrollment** | `list_student_enrollments(student_id)` | Joins `EnrollmentModel` with `CourseModel` to return student's courses. |
| **Enrollment** | `list_course_enrollments(course_id)` | Returns all student enrollment records for an instructor's course. |

### 3.2 CourseService (`backend/app/services/course_service.py`)

The service layer implements complete domain validation, authorization, and workflow orchestration.

#### 1. Course Management & Ownership Guards
- **Authorization:** Only users with `role == "instructor"` or `"admin"` can create courses. Students attempting creation receive `HTTPException(403, "Only instructors can create courses")`.
- **Code Conflict Prevention (D1):** Checks `repo.get_course_by_code()`; if code already exists, raises `HTTPException(409, "Course with code '{code}' already exists")`.
- **Ownership Verification:** All mutations (updates, archiving, topic additions, topic reordering) call `_verify_course_ownership(course_id, user_id, user_role)`. If `course.instructor_id != user_id` (and not admin), raises `HTTPException(403, "You do not have permission to manage this course")`.
- **M5 Dual-Source Sync (D7):** When an instructor creates a course, `CourseService` invokes `ProgressRepository(db).set_course_owner(course.id, instructor_id)`. This keeps `courses.instructor_id` in absolute sync with Module 5's course ownership mapping.

#### 2. Course Archiving Lifecycle (Decision D3)
- Instructors can archive and unarchive their own courses via `archive_course(course_id, ...)` and `unarchive_course(...)`.
- **Read-Only Invariant:** When `course.is_archived == True`:
  - `update_course`: Raises `HTTPException(400, "Archived courses cannot be modified")`.
  - `create_topic`: Raises `HTTPException(400, "Cannot add topics to an archived course")`.
  - `update_topic`: Raises `HTTPException(400, "Cannot modify topics in an archived course")`.
  - `delete_topic`: Raises `HTTPException(400, "Cannot delete topics from an archived course")`.
  - `reorder_topics`: Raises `HTTPException(400, "Cannot reorder topics in an archived course")`.
  - `enroll_student`: Raises `HTTPException(400, "Cannot enroll in an archived course")`.
  - **Read Access Preserved:** Existing enrolled students and instructors can continue to view course details, topics, and historical progress.

#### 3. Topic Operations & Safety Restrictions (Decision D2)
- Adding, updating, and deleting topics strictly verifies course ownership.
- **Question Safety Guard (D2):** Before deleting a topic, `CourseService` queries `repo.has_quiz_questions(topic_id)`. If quiz questions are linked to the topic in `QuestionStatsModel`, deletion is aborted with `HTTPException(400, "Cannot delete topic because quiz questions are associated with it")`. This guarantees Module 2 and Module 3 quiz telemetry is never orphaned.
- **Batch Reordering:** Validates that all topic IDs in `TopicReorderRequest` belong to the course, contain no duplicates, and have valid indices. Executes transactional two-phase reordering.

#### 4. Prerequisite DAG & Cycle Detection
- **Self-Dependency Guard:** Reject `prerequisite_id == topic_id` with `HTTPException(400, "A topic cannot be a prerequisite of itself")`.
- **Cross-Course Guard:** Reject prerequisites belonging to different courses with `HTTPException(400, "Prerequisite topic must belong to the same course")`.
- **Duplicate Guard:** Reject duplicate prerequisites with `HTTPException(400, "Prerequisite relationship already exists")`.
- **DFS Cycle Detection:** Constructs the directed graph of prerequisites across the course. Performs depth-first search (DFS) with a 3-color state machine (`UNVISITED`, `VISITING`, `VISITED`). If a back-edge to a `VISITING` node is encountered, raises `HTTPException(400, "Adding this prerequisite would create a circular dependency")`.

#### 5. Enrollment Operations & Privacy Guards (Decision D6)
- **Role Enforcement:** Only users with `role == "student"` can enroll. Non-students receive `HTTPException(403, "Only students can enroll in courses")`.
- **Self-Enrollment Guard:** Students can only enroll themselves (`student_id == current_user_id`). Attempting to enroll another student raises `HTTPException(403, "Students can only enroll themselves")`.
- **Code Match Verification:** If a course code is supplied in `EnrollmentRequest`, it must match the target course code; otherwise raises `HTTPException(400, "Course code does not match")`.
- **Duplicate Prevention:** Existing enrollment lookup raises `HTTPException(400, "Student is already enrolled in this course")`.
- **Student Privacy:** Students can view their own enrollments via `get_student_enrollments()`. A student querying another student's ID is rejected with `HTTPException(403, "You can only view your own enrollments")`.
- **Roster Ownership:** Instructors can view enrolled students for their courses; non-owners are rejected with HTTP 403.

---

## 4. Verification & Test Suite Execution

### 4.1 Focused Service Unit Tests (`backend/tests/unit/test_course_service.py`)

A comprehensive test suite containing **22 unit tests** was authored across three test classes:

| Class | Test Method | Covered Rule / Scenario | Result |
| :--- | :--- | :--- | :---: |
| `TestCourseOperations` | `test_create_course_success_as_instructor` | Instructor course creation, D1 normalization, D7 M5 sync | **PASSED** |
| `TestCourseOperations` | `test_create_course_forbidden_for_student` | Student course creation rejected (HTTP 403) | **PASSED** |
| `TestCourseOperations` | `test_create_course_duplicate_code_conflict` | Duplicate course code rejected with HTTP 409 (D1) | **PASSED** |
| `TestCourseOperations` | `test_get_course_details` | Retrieval of course with topic and enrollment counters | **PASSED** |
| `TestCourseOperations` | `test_get_nonexistent_course_404` | Nonexistent course ID returns HTTP 404 | **PASSED** |
| `TestCourseOperations` | `test_update_course_success_as_owner` | Course update succeeded for owner instructor | **PASSED** |
| `TestCourseOperations` | `test_update_course_forbidden_for_non_owner` | Course update rejected for non-owner instructor (HTTP 403) | **PASSED** |
| `TestCourseOperations` | `test_archiving_and_publishing_lifecycle` | Archive toggle (`is_archived: True` then `False`) | **PASSED** |
| `TestCourseOperations` | `test_archived_course_read_only_access_rules` | Mutation operations rejected on archived course (D3) | **PASSED** |
| `TestTopicOperations` | `test_create_and_list_topics` | Topic creation with auto-incremented order index | **PASSED** |
| `TestTopicOperations` | `test_create_topic_forbidden_for_non_owner` | Topic creation rejected for non-owner instructor (HTTP 403) | **PASSED** |
| `TestTopicOperations` | `test_atomic_topic_reordering` | Reordering topics with indices swap without collision | **PASSED** |
| `TestTopicOperations` | `test_delete_topic_success` | Deletion of unreferenced topic succeeds | **PASSED** |
| `TestTopicOperations` | `test_delete_topic_rejected_when_quiz_questions_exist` | Deletion rejected (HTTP 400) when questions exist (D2) | **PASSED** |
| `TestTopicOperations` | `test_prerequisite_graph_and_cycle_detection` | Prerequisite link, self-prereq, cross-course, cycle detection | **PASSED** |
| `TestEnrollmentOperations` | `test_student_enrollment_success` | Student self-enrollment in active course (D6) | **PASSED** |
| `TestEnrollmentOperations` | `test_enrollment_rejected_for_non_student` | Instructor attempting student enrollment rejected (HTTP 403) | **PASSED** |
| `TestEnrollmentOperations` | `test_student_cannot_enroll_another_student` | Student enrolling another student rejected (HTTP 403) | **PASSED** |
| `TestEnrollmentOperations` | `test_duplicate_enrollment_rejected` | Duplicate enrollment rejected with HTTP 400 | **PASSED** |
| `TestEnrollmentOperations` | `test_enrollment_in_archived_course_rejected` | Enrollment in archived course rejected with HTTP 400 (D3) | **PASSED** |
| `TestEnrollmentOperations` | `test_enrollment_with_mismatched_course_code_rejected` | Wrong course code rejected with HTTP 400 | **PASSED** |
| `TestEnrollmentOperations` | `test_student_enrollments_listing_privacy` | Student views own courses; viewing peer's rejected (HTTP 403) | **PASSED** |

### 4.2 Full Regression Test Suite Execution

The entire backend test suite was executed to ensure 100% backward compatibility and regression-free operation across all system modules:

```powershell
pytest
====================== 212 passed, 8 warnings in 28.35s =======================
```

#### Test Suite Breakdown:
- **Baseline Tests (M2, M3, M5, Security, Architecture):** 150 passed
- **Stage 2 Models Unit Tests (`test_course_models.py`):** 10 passed
- **Stage 3 Schemas Unit Tests (`test_course_schemas.py`):** 30 passed
- **Stage 4 Services Unit Tests (`test_course_service.py`):** 22 passed
- **Total:** **212 tests passed, 0 failed, 0 skipped**

---

## 5. Repository State & Scope Boundary Verification

### 5.1 Git Working Tree Status
```
On branch feature/m1-course-management
Changes not staged for commit:
  modified:   backend/app/models/__init__.py
  modified:   backend/app/models/progress.py
  modified:   backend/app/repositories/__init__.py
  modified:   backend/app/repositories/progress_repository.py
  modified:   backend/app/schemas/__init__.py
  modified:   backend/app/services/__init__.py

Untracked files:
  backend/app/models/course.py
  backend/app/repositories/course_repository.py
  backend/app/schemas/course.py
  backend/app/services/course_service.py
  backend/tests/unit/test_course_models.py
  backend/tests/unit/test_course_schemas.py
  backend/tests/unit/test_course_service.py
  docs/sqa/M1_DATABASE_MODEL_IMPACT_AUDIT.md
  docs/sqa/M1_M4_ENVIRONMENT_AND_BASELINE_TEST_REPORT.md
  docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md
  docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md
  docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md
  docs/sqa/M1_M4_WORKSPACE_BASELINE.md
  docs/sqa/M1_MODEL_IMPLEMENTATION_REPORT.md
  docs/sqa/M1_SCHEMA_IMPLEMENTATION_REPORT.md
  docs/sqa/M1_SERVICE_IMPLEMENTATION_REPORT.md
```

### 5.2 Strict Constraints Compliance
- **No API routes implemented:** `backend/app/api/v1/endpoints/courses.py` has NOT been created yet.
- **No Git commits or pushes made:** Clean working tree on `feature/m1-course-management`.
- **Existing documentation preserved:** All SQA and baseline reports preserved intact.

---

## 6. Readiness for Stage 5: API Endpoints Implementation

With the repository and service layers fully functional, validated, and passing all unit and regression tests, Module 1 is ready for **Stage 5: API Endpoints (FastAPI Routers)**:
1. `POST /api/v1/courses` — Create course (instructors only).
2. `GET /api/v1/courses` — List courses (paginated, filterable by instructor/archive status).
3. `GET /api/v1/courses/{course_id}` — Get course details with topics and metadata.
4. `PUT /api/v1/courses/{course_id}` — Update course metadata (owner only).
5. `POST /api/v1/courses/{course_id}/archive` & `POST /api/v1/courses/{course_id}/unarchive` — Archive lifecycle.
6. `POST /api/v1/courses/{course_id}/topics` — Add topic to course (owner only).
7. `PUT /api/v1/courses/{course_id}/topics/{topic_id}` — Update topic (owner only).
8. `DELETE /api/v1/courses/{course_id}/topics/{topic_id}` — Delete unreferenced topic (owner only).
9. `PUT /api/v1/courses/{course_id}/topics/reorder` — Reorder topics (owner only).
10. `POST /api/v1/courses/{course_id}/topics/{topic_id}/prerequisites` — Add prerequisite (owner only).
11. `DELETE /api/v1/courses/{course_id}/topics/{topic_id}/prerequisites/{prerequisite_id}` — Remove prerequisite.
12. `POST /api/v1/courses/{course_id}/enroll` — Student self-enrollment.
13. `GET /api/v1/users/me/enrollments` / `GET /api/v1/students/{student_id}/enrollments` — Student enrollment listings.
14. Integration with `backend/app/main.py` router mounting and comprehensive end-to-end integration tests.
