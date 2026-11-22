# AdaptLearn M1 — Stage 2: Database Models Implementation Report
## Module 1: User & Course Management (Models, Constraints & Backward Compatibility)

**Document Reference:** `docs/sqa/M1_MODEL_IMPLEMENTATION_REPORT.md`  
**Document Type:** Software Quality Assurance Implementation & Test Verification Report  
**Author:** Hiba Zulfiqar (`2023246`) — Lead for M1 (User & Course Management) & M4 (Personalized Learning Paths)  
**Target Reviewers / Approvers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Git Branch:** `feature/m1-course-management`  
**Baseline Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f`  
**Focused Test Suite:** **10/10 passed (100% green)**  
**Full Test Suite:** **160 passed, 0 failed, 0 skipped (100% green)**  
**Status:** **STAGE 2 COMPLETE — MODELS IMPLEMENTED & FULLY VERIFIED**  
**Date:** November 21, 2026  

---

## 1. Executive Summary

In accordance with the verified database impact audit ([`M1_DATABASE_MODEL_IMPACT_AUDIT.md`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/docs/sqa/M1_DATABASE_MODEL_IMPACT_AUDIT.md)) and team-approved architectural decisions ([`M1_M4_TEAM_APPROVAL_PROPOSAL.md`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md)), the SQLAlchemy ORM domain models for **Module 1 (User & Course Management)** have been implemented and rigorously tested.

### Key Implementation Milestones
1. **Core Domain Entities Authoring:** Created `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, and reconciled `EnrollmentModel` in [`backend/app/models/course.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/app/models/course.py).
2. **Strict Adherence to Decision D6:** Retained the existing `course_enrollments` table schema `(id, student_id, course_id)` and composite uniqueness constraint unchanged. Re-exported `EnrollmentModel` in `backend/app/models/progress.py` to prevent SQLAlchemy `DeclarativeBase` duplicate table collisions.
3. **Dual-Source Course Ownership (Decision D7):** Updated `ProgressRepository.is_course_owner()` to verify `CourseModel.instructor_id` first, falling back to legacy `course_owners` fixtures.
4. **Prerequisite Graph Invariants Enforced:** Implemented self-prerequisite checks, cross-course isolation, and DFS cycle detection both at the model validation level and via database constraints.
5. **Zero Regressions Across All Modules:** Executed the entire test suite; all **150 baseline tests passed** alongside **10 new focused model unit tests** (**160 total passed tests**).

---

## 2. Implemented Database Models & Schema Decisions

```
                                M1 Relational Entity Architecture
 ┌─────────────────────────┐            1:N            ┌─────────────────────────┐
 │       CourseModel       ├───────────────────────────┤       TopicModel        │
 │    (table: 'courses')   │                           │    (table: 'topics')    │
 ├─────────────────────────┤                           ├─────────────────────────┤
 │ id (PK, int)            │                           │ id (PK, int)            │
 │ title (varchar 200)     │                           │ course_id (FK -> courses│
 │ description (text)      │                           │ title (varchar 200)     │
 │ course_code (UQ, v50)   │◀── Decision D1            │ description (text)      │
 │ instructor_id (FK->user)│◀── Decision D7            │ order_index (int)       │
 │ is_archived (bool)      │◀── Decision D3            │ is_active (bool)        │
 │ created_at (datetime)   │                           │ created_at (datetime)   │
 │ updated_at (datetime)   │                           │ updated_at (datetime)   │
 └───────────┬─────────────┘                           └────────────┬────────────┘
             │                                                      │
             │ 1:N                                                  │ 1:N (Self-Ref DAG)
             ▼                                                      ▼
 ┌─────────────────────────┐                           ┌─────────────────────────┐
 │     EnrollmentModel     │                           │ TopicPrerequisiteModel  │
 │(table: 'course_enroll') │◀── Decision D6            │(table: 'topic_prereqs') │
 ├─────────────────────────┤                           ├─────────────────────────┤
 │ id (PK, int)            │                           │ id (PK, int)            │
 │ student_id (FK->user)   │                           │ topic_id (FK->topics)   │
 │ course_id (FK->courses) │                           │ prereq_id (FK->topics)  │
 │                         │                           │ created_at (datetime)   │
 └─────────────────────────┘                           └─────────────────────────┘
```

### 2.1 Entity Details

#### 1. `CourseModel` (table `"courses"`)
- **Primary Key:** `id` (Integer, autoincrement, indexed).
- **Attributes:**
  - `title`: `String(200)`, nullable=False.
  - `description`: `Text`, nullable=True.
  - `course_code`: `String(50)`, nullable=False, unique=True, indexed (Decision D1).
  - `instructor_id`: `Integer`, ForeignKey(`"users.id"`), nullable=False, indexed (Decision D7).
  - `is_archived`: `Boolean`, nullable=False, default=False, indexed (Decision D3).
  - `created_at`: `DateTime`, default=UTC now.
  - `updated_at`: `DateTime`, onupdate=UTC now.
- **Relationships:**
  - `instructor`: Many-to-One to `UserModel`, backref `authored_courses`.
  - `topics`: One-to-Many to `TopicModel`, cascade delete-orphan, sorted by `order_index`.
  - `enrollments`: One-to-Many to `EnrollmentModel`, cascade delete-orphan.

#### 2. `TopicModel` (table `"topics"`)
- **Primary Key:** `id` (Integer, autoincrement, indexed).
- **Attributes:**
  - `course_id`: `Integer`, ForeignKey(`"courses.id"`, ondelete=`"CASCADE"`), nullable=False, indexed.
  - `title`: `String(200)`, nullable=False.
  - `description`: `Text`, nullable=True.
  - `order_index`: `Integer`, nullable=False, default=0, indexed.
  - `is_active`: `Boolean`, nullable=False, default=True.
  - `created_at` & `updated_at`: UTC timestamps.
- **Constraints:** Composite unique constraint `uq_course_topic_order` on `(course_id, order_index)` ensures sequential ordering consistency within each course.
- **Relationships:**
  - `course`: Many-to-One to `CourseModel`, back_populates `topics`.
  - `prerequisites`: One-to-Many to `TopicPrerequisiteModel` (edges where this topic is the dependent topic).
  - `required_by`: One-to-Many to `TopicPrerequisiteModel` (edges where this topic is the prerequisite).
- **Methods:** `add_prerequisite(prereq, session)` validates same-course and DAG cycle invariants before adding.

#### 3. `TopicPrerequisiteModel` (table `"topic_prerequisites"`)
- **Primary Key:** `id` (Integer, autoincrement).
- **Attributes:**
  - `topic_id`: `Integer`, ForeignKey(`"topics.id"`, ondelete=`"CASCADE"`), nullable=False, indexed.
  - `prerequisite_topic_id`: `Integer`, ForeignKey(`"topics.id"`, ondelete=`"CASCADE"`), nullable=False, indexed.
  - `created_at`: UTC timestamp.
- **Constraints:**
  - `uq_topic_prerequisite_edge`: Unique constraint on `(topic_id, prerequisite_topic_id)`.
  - `chk_no_self_prerequisite`: CheckConstraint `topic_id != prerequisite_topic_id`.
- **Validation:**
  - `@validates("prerequisite_topic_id")` and `@validates("topic_id")` raise `ValueError("A topic cannot be a prerequisite of itself.")`.
  - `validate_prerequisite_edge(session, topic_id, prerequisite_topic_id)` executes DFS traversal to prevent any circular dependency (direct or indirect) and enforces same-course membership.

#### 4. `EnrollmentModel` (table `"course_enrollments"`)
- **Conforms strictly to Decision D6:**
  - Table name: `"course_enrollments"`.
  - Columns: `id` (PK), `student_id` (FK to `users.id`), `course_id` (FK to `courses.id`).
  - Constraint: `UniqueConstraint("student_id", "course_id", name="uq_student_course_enrollment")`.
  - Re-exported in `backend/app/models/progress.py` to prevent duplicate DeclarativeBase table collision.

---

## 3. Modified and Created Files Catalog

| File Path | Status | Purpose & Description |
| :--- | :---: | :--- |
| `backend/app/models/course.py` | **NEW** | Authoritative declarations of `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, `EnrollmentModel`, and `validate_prerequisite_edge()`. |
| `backend/app/models/progress.py` | **MODIFIED** | Re-exports `EnrollmentModel` from `app.models.course` instead of declaring a duplicate table; preserves `CourseOwnerModel`. |
| `backend/app/models/__init__.py` | **MODIFIED** | Registers and exports `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, and `EnrollmentModel` with `Base.metadata`. |
| `backend/app/repositories/progress_repository.py` | **MODIFIED** | Upgrades `is_course_owner()` to dual-source resolution (checks `CourseModel.instructor_id` first, falls back to `CourseOwnerModel`). |
| `backend/tests/unit/test_course_models.py` | **NEW** | Comprehensive unit test suite covering all 10 required model testing scenarios. |

---

## 4. Test Verification & Traceability Matrix

The focused unit test suite [`backend/tests/unit/test_course_models.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/tests/unit/test_course_models.py) validates all 10 required testing areas:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FOCUSED MODEL TEST MATRIX                                 │
├────┬──────────────────────────────────────┬─────────────────────────────┬──────────┤
│ #  │ Test Requirement                     │ Executed Test Method        │ Result   │
├────┼──────────────────────────────────────┼─────────────────────────────┼──────────┤
│ 1  │ Course creation                      │ test_course_creation        │ PASSED   │
│ 2  │ Unique course code enforcement       │ test_unique_course_code_... │ PASSED   │
│ 3  │ Instructor ownership                 │ test_instructor_ownership   │ PASSED   │
│ 4  │ Topic creation and ordering          │ test_topic_creation_and_... │ PASSED   │
│ 5  │ Valid prerequisites                  │ test_valid_prerequisites    │ PASSED   │
│ 6  │ Self-prerequisite rejection          │ test_self_prerequisite_...  │ PASSED   │
│ 7  │ Circular dependency rejection        │ test_circular_dependency... │ PASSED   │
│ 8  │ Cross-course prerequisite rejection  │ test_cross_course_prereq... │ PASSED   │
│ 9  │ Enrollment compatibility             │ test_enrollment_compatib... │ PASSED   │
│ 10 │ Existing M2/M3/M5 model compatibility│ test_existing_m2_m3_m5...   │ PASSED   │
└────┴──────────────────────────────────────┴─────────────────────────────┴──────────┘
```

### 4.1 Pytest Execution Logs

```powershell
cd backend
.\venv\Scripts\pytest.exe tests/unit/test_course_models.py -v
```
**Focused Test Result:** `10 passed in 0.73s`

```powershell
cd backend
.\venv\Scripts\pytest.exe
```
**Full Regression Test Suite Result:** `160 passed, 8 warnings in 21.51s (100% Pass Rate)`

**Regression Assessment:** Zero regressions across M2 (Quiz Engine attempts), M3 (Adaptive Learning Engine), and M5 (Progress Analytics and Instructor Dashboard).

---

## 5. Unresolved Issues & Technical Observations

1. **Unresolved Issues:** **None.** All model definitions, relationships, constraints, and backward-compatibility layers function without error or failure.
2. **Upstream Deprecation Warnings:** 8 non-blocking framework deprecation warnings from Starlette (`StarletteDeprecationWarning: 'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated` and `fastapi.testclient: using httpx is deprecated`). These originate in external libraries and do not impact application correctness.
3. **Scope Control Confirmation:** No Pydantic schemas, application services, or FastAPI API routes were created or modified during this stage. Implementation was strictly confined to database models and their focused unit tests.

---

## 6. Current Git Working-Tree Status

```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn"
git status --short
```

```text
 M backend/app/models/__init__.py
 M backend/app/models/progress.py
 M backend/app/repositories/progress_repository.py
?? backend/app/models/course.py
?? backend/tests/unit/test_course_models.py
?? docs/sqa/M1_DATABASE_MODEL_IMPACT_AUDIT.md
?? docs/sqa/M1_M4_ENVIRONMENT_AND_BASELINE_TEST_REPORT.md
?? docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md
?? docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md
?? docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md
?? docs/sqa/M1_M4_WORKSPACE_BASELINE.md
?? docs/sqa/M1_MODEL_IMPLEMENTATION_REPORT.md
```

- **Branch:** `feature/m1-course-management`
- **Head Commit:** `fb4d3c5`
- **Commits / Pushes:** None authored.
- **Safety Rule Compliance:** Clean working state; untracked SQA documentation files preserved.

---

## 7. Conclusion

Stage 2 (Database Models Implementation) is **100% complete and verified**. The foundational data structures for Module 1 are firmly established, fully tested, and ready for Stage 3 (Pydantic Validation Schemas and Data Access Repositories).
