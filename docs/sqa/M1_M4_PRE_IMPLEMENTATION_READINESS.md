# AdaptLearn — M1 & M4 Pre-Implementation Readiness Report

**Document Reference:** `docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md`  
**Document Type:** Formal Software Quality Assurance Pre-Implementation Assessment  
**Author:** Hiba Zulfiqar (`2023246`) — Lead Architect & Requirements Engineer for M1 & M4  
**Module Scope:** Module 1 (User & Course Management) & Module 4 (Personalized Learning Paths)  
**Baseline Repository:** `https://github.com/toqeer-ahmed/AdaptLearn`  
**Repository Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f` (`fix(ci): resolve backend test collection failure`)  
**Target Reviewers / Approvers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Status:** **READY FOR TEAM SIGN-OFF — ZERO CODE MODIFICATIONS UNDERTAKEN**  
**Date:** November 21, 2026  

---

## 1. Executive Summary & Audit Purpose

This document provides a formal **Pre-Implementation Readiness Assessment** for **Module 1 (M1: User & Course Management)** and **Module 4 (M4: Personalized Learning Paths)** of the AdaptLearn project.

Prior to writing any production code, database migrations, or feature branches, software engineering best practices and SQA standards mandate a comprehensive readiness gate. This audit evaluates:
1. The exact state of the local and remote Git repository.
2. The compatibility of host development runtimes and package tooling.
3. The precise catalog of files to be created, modified, or preserved.
4. Cross-module regression risks (especially regarding M5 and M3 shared tables).
5. Team sign-off dependencies and governance agreements.
6. A phased, verifiable step-by-step implementation sequence.

### Pre-Implementation Readiness Verdict: **CONDITIONALLY READY (GATED ON RUNTIME SETUP & FORMAL SIGN-OFF)**

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                READINESS GATE MATRIX                                   │
├────────────────────────────────────────┬───────────┬───────────────────────────────────┤
│ Verification Area                      │ Status    │ Action Required Prior to Coding   │
├────────────────────────────────────────┼───────────┼───────────────────────────────────┤
│ 1. Git Repository State                │ VERIFIED  │ Working tree clean; audit docs ok │
│ 2. Requirements & Architecture Specs   │ VERIFIED  │ Reconciled in docs/sqa/           │
│ 3. Implementation File Plan            │ VERIFIED  │ 14 files identified & mapped      │
│ 4. Cross-Module Compatibility Strategy │ VERIFIED  │ Backward compatibility designed   │
│ 5. Branch & PR Strategy                │ VERIFIED  │ 2-stage feature branch pipeline   │
│ 6. Python Runtime Environment          │ ACTION    │ Host has 3.14; need 3.10-3.12 venv│
│ 7. Frontend Node.js Tooling            │ DEFERRED  │ Not blocking for backend M1/M4    │
│ 8. Team Architectural Sign-off         │ PENDING   │ Awaiting approval from leads      │
└────────────────────────────────────────┴───────────┴───────────────────────────────────┘
```

---

## 2. Repository State Verification

### 2.1 Git Audit Summary
An inspection of the local workspace `C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn` was conducted against the official upstream repository:

- **Upstream Remote:** `https://github.com/toqeer-ahmed/AdaptLearn.git`
- **Current Active Branch:** `main`
- **Branch Synchronization:** In sync with `origin/main` (`Your branch is up to date with 'origin/main'`).
- **Latest Commit Hash:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f`
- **Commit Message:** `fix(ci): resolve backend test collection failure`
- **Existing Local Branches:** `main`
- **Existing Remote Branches:** `origin/HEAD -> origin/main`, `origin/main`
- **Feature Branches:** None currently created. Neither `feature/m1-course-management` nor `feature/m4-learning-paths` exists locally or on remote.

### 2.2 Working-Tree Status and Untracked Audit Documents
The Git working tree has zero staged or unstaged modifications to existing tracked files. Exactly four SQA audit documents exist in `docs/sqa/` as **untracked** files:

| File Path | Status | Purpose / Description |
| :--- | :--- | :--- |
| `docs/sqa/M1_M4_WORKSPACE_BASELINE.md` | Untracked | Host environment baseline, repo structure, and test suite audit |
| `docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md` | Untracked | Formal gap analysis reconciling M1 Report with code and docs |
| `docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md` | Untracked | 10 architectural decisions and 5 cross-module integration contracts |
| `docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md` | Untracked | This pre-implementation readiness and environment checklist |

> [!IMPORTANT]
> **Safety Rule Compliance**: In strict adherence to our safety protocol, no files have been committed, staged, reset, or pushed to GitHub. These audit documents remain safely in the local filesystem awaiting formal team consensus before branch creation.

---

## 3. Development Environment Verification

### 3.1 Host Runtime Audit
Inspection of the Windows host environment reveals the following configuration:

```powershell
Host Python Launcher:  -V:3.14 * Python 3.14 (64-bit)
Host Python Binary:    C:\Users\hiba2\AppData\Local\Programs\Python\Python314\python.exe
Host Python Version:   Python 3.14.3
Node.js Status:        'node' is not recognized as an internal or external command
npm Status:            'npm' is not recognized as an internal or external command
Active VirtualEnv:     None detected (backend/venv does not exist)
```

### 3.2 Compatibility Analysis

#### Backend Python Runtime:
- **Project Baseline Specification:** 
  - `.github/workflows/ci.yml` sets up `python-version: "3.10"`.
  - `backend/pyproject.toml` configures Ruff with `target-version = "py310"`.
  - Project documentation specifies Python 3.10 – 3.12 compatibility.
- **Python 3.14 Risks:**
  - Python 3.14 is currently an experimental/early release.
  - Critical project dependencies specified in `backend/requirements.txt`:
    - `bcrypt>=4.1.0,<6.0.0`
    - `sqlalchemy>=2.0.0,<3.0.0`
    - `pydantic>=2.6.0,<3.0.0` (relies on `pydantic-core`)
    - `greenlet` (SQLAlchemy dependency)
  - Many compiled C/Rust extensions do not have pre-built binary wheels for Python 3.14 on Windows. Attempting to build them locally requires Microsoft Visual C++ Build Tools and often fails due to internal C-API changes in Python 3.14.
- **Recommended Action:**
  - Install **Python 3.11** or **Python 3.12** on the host machine, or test whether wheels install cleanly under 3.14 in an isolated virtual environment.
  - A project-specific virtual environment (`backend/venv`) MUST be used to isolate dependencies from the global system Python.

#### Frontend Node.js Tooling:
- **Status:** Node.js and npm are absent from system PATH.
- **Impact Assessment:**
  - The frontend (`frontend/src/`) is a React + Vite application requiring Node.js 20 (`node-version: "20"` in CI).
  - **Crucial SQA Distinction:** M1 (User & Course Management) and M4 (Personalized Learning Paths) core assignments consist of backend database models, repositories, business logic services, Pydantic schemas, and FastAPI REST endpoints.
  - **Conclusion:** Lack of Node.js is **NOT a blocker** for M1/M4 backend development, unit testing, or API integration testing. Frontend build verification (`npm run build`) can be executed once Node.js LTS is installed or verified automatically by the GitHub Actions CI pipeline on push.

---

## 4. Required Setup Actions & Remediation

To establish a safe local development environment without breaking existing work or polluting the global operating system:

### Step 1: Install Python 3.11 or 3.12 (Recommended)
Download and install Python 3.11 or 3.12 from python.org (ensure "Add Python to PATH" is checked).  
*Alternative fallback:* If restricted to Python 3.14, attempt wheel installation in a test virtual environment.

### Step 2: Initialize Backend Virtual Environment
Run the following commands from the project root:
```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend"
python -m venv venv
```

### Step 3: Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### Step 4: Upgrade Pip and Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 5: Execute Baseline Regression Test Suite
Before introducing any new lines of code, execute the existing test suite:
```powershell
pytest -v
```
**Acceptance Criterion:** All **150 existing tests** must pass with 0 failures, 0 errors, and 0 warnings.

---

## 5. Comprehensive Implementation File Plan

The following table details every file to be created or modified for Module 1 and Module 4:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FILE IMPLEMENTATION CATALOG                               │
├────┬────────────────────────────────────────────────┬──────────┬──────────┬────────────┤
│ #  │ File Path                                      │ Module   │ Layer    │ Action     │
├────┼────────────────────────────────────────────────┼──────────┼──────────┼────────────┤
│ 1  │ backend/app/models/course.py                   │ M1       │ Model    │ CREATE     │
│ 2  │ backend/app/models/__init__.py                 │ M1/M4    │ Model    │ MODIFY     │
│ 3  │ backend/app/schemas/course.py                  │ M1       │ Schema   │ CREATE     │
│ 4  │ backend/app/repositories/course_repository.py  │ M1       │ Repo     │ CREATE     │
│ 5  │ backend/app/services/course_service.py         │ M1       │ Service  │ CREATE     │
│ 6  │ backend/app/api/v1/endpoints/courses.py        │ M1       │ API      │ CREATE     │
│ 7  │ backend/app/api/v1/api.py                      │ M1/M4    │ Router   │ MODIFY     │
│ 8  │ backend/tests/unit/test_course_models.py       │ M1       │ Test     │ CREATE     │
│ 9  │ backend/tests/unit/test_course_service.py      │ M1       │ Test     │ CREATE     │
│ 10 │ backend/tests/integration/test_courses_api.py  │ M1       │ Test     │ CREATE     │
│ 11 │ backend/app/schemas/learning_path.py           │ M4       │ Schema   │ CREATE     │
│ 12 │ backend/app/services/learning_path_service.py  │ M4       │ Service  │ CREATE     │
│ 13 │ backend/app/api/v1/endpoints/learning_paths.py │ M4       │ API      │ CREATE     │
│ 14 │ backend/tests/unit/test_learning_path_service. │ M4       │ Test     │ CREATE     │
│ 15 │ backend/tests/integration/test_learning_paths_ │ M4       │ Test     │ CREATE     │
└────┴────────────────────────────────────────────────┴──────────┴──────────┴────────────┘
```

### Detailed File Specifications

#### Module 1: User & Course Management
1. `backend/app/models/course.py` (NEW):
   - Classes: `CourseModel` (table `courses`), `TopicModel` (table `topics`), `TopicPrerequisiteModel` (table `topic_prerequisites`), `EnrollmentModel` (table `course_enrollments`).
   - Foreign Keys: `courses.instructor_id -> users.id`, `topics.course_id -> courses.id`, `topic_prerequisites.(topic_id, prerequisite_topic_id) -> topics.id`, `course_enrollments.user_id -> users.id`, `course_enrollments.course_id -> courses.id`.
   - Constraints: Unique constraint on `course_code`, composite unique on `(course_id, order_index)`, composite unique on `(user_id, course_id)`.

2. `backend/app/models/__init__.py` (MODIFIED):
   - Export new models: `CourseModel`, `TopicModel`, `TopicPrerequisiteModel`, `EnrollmentModel`.

3. `backend/app/schemas/course.py` (NEW):
   - Pydantic DTOs: `CourseCreate`, `CourseUpdate`, `CourseResponse`, `TopicCreate`, `TopicUpdate`, `TopicResponse`, `TopicReorderItem`, `TopicReorderRequest`, `TopicPrerequisiteCreate`, `EnrollmentCreate`, `EnrollmentResponse`.

4. `backend/app/repositories/course_repository.py` (NEW):
   - Class: `CourseRepository`.
   - Methods: `create_course()`, `get_course_by_id()`, `get_course_by_code()`, `list_courses()`, `update_course()`, `archive_course()`, `create_topic()`, `get_topic_by_id()`, `get_course_topics()`, `reorder_topics()`, `add_prerequisite()`, `remove_prerequisite()`, `get_prerequisites()`, `enroll_student()`, `get_enrollment()`, `list_user_enrollments()`, `is_enrolled()`.

5. `backend/app/services/course_service.py` (NEW):
   - Class: `CourseService`.
   - Responsibilities: Role validation (instructor vs student), course ownership checks, business rules (archived course updates disallowed, duplicate enrollment prevention), DAG cycle detection algorithm (DFS cycle check on prerequisite graphs).

6. `backend/app/api/v1/endpoints/courses.py` (NEW):
   - FastAPI Router endpoints:
     - `POST /courses` — Create course (`instructor` only).
     - `GET /courses` — Discover / list courses (public or authenticated).
     - `GET /courses/{id}` — Get course details by ID.
     - `PATCH /courses/{id}` — Update course title/desc (author instructor only).
     - `POST /courses/{id}/archive` — Archive course (author instructor only).
     - `POST /courses/{id}/enroll` — Enroll student in course (`student` only).
     - `GET /courses/{id}/topics` — List topics for a course ordered by `order_index`.
     - `POST /courses/{id}/topics` — Create topic (`instructor` only).
     - `PUT /courses/{id}/topics/order` — Reorder topics sequentially (`instructor` only).
     - `POST /topics/{id}/prerequisites` — Add prerequisite relationship (`instructor` only, DAG validation).
     - `DELETE /topics/{id}/prerequisites/{prerequisite_id}` — Remove prerequisite.

7. `backend/app/api/v1/api.py` (MODIFIED):
   - Register `courses.router` under prefix `/courses` with tags `["courses"]`.
   - Register `learning_paths.router` under prefix `/learning-paths` with tags `["learning-paths"]`.

8. `backend/tests/unit/test_course_models.py` (NEW):
   - Unit tests verifying SQLAlchemy model instantiations, relationships, cascade deletes, and constraints.

9. `backend/tests/unit/test_course_service.py` (NEW):
   - Unit tests verifying DAG cycle detection (direct A->B->A, indirect A->B->C->A, self-prerequisite A->A), topic reordering validation, enrollment business rules.

10. `backend/tests/integration/test_courses_api.py` (NEW):
    - FastAPI TestClient integration tests covering full HTTP request/response lifecycles, JWT auth, RBAC (403 for unauthorized roles), and validation errors.

---

#### Module 4: Personalized Learning Paths
11. `backend/app/schemas/learning_path.py` (NEW):
    - Pydantic DTOs: `TopicStatusEnum` (`COMPLETED`, `IN_PROGRESS`, `UNLOCKED`, `LOCKED`, `RECOMMENDED`), `LearningPathTopicResponse`, `LearningPathResponse`, `NextTopicRecommendationResponse`.

12. `backend/app/services/learning_path_service.py` (NEW):
    - Class: `LearningPathService`.
    - Architecture: **Stateless dynamic evaluation engine** (Decision D3).
    - Logic:
      1. Fetch course topics and prerequisite DAG from `CourseRepository`.
      2. Fetch student's mastery records from M3 (`AdaptiveRepository.get_mastery()`).
      3. For each topic: evaluate whether all prerequisite topics have reached mastery threshold ($\ge 0.70$ or `is_mastered == True`).
      4. Classify topic state (`COMPLETED` if mastery $\ge 0.85$, `IN_PROGRESS` if $0.0 <$ mastery $< 0.85$, `UNLOCKED` if prerequisites met, `LOCKED` if prerequisites missing).
      5. Delegate primary recommendation to `RecommendationStrategy.recommend_next_topic()` or select lowest `order_index` unlocked topic.
      6. Return comprehensive `LearningPathResponse`.

13. `backend/app/api/v1/endpoints/learning_paths.py` (NEW):
    - FastAPI Router endpoints:
      - `GET /learning-paths/courses/{course_id}/my-path` — Current authenticated student's personalized path.
      - `GET /learning-paths/courses/{course_id}/users/{user_id}` — Instructor view of a specific student's path.
      - `GET /learning-paths/courses/{course_id}/next-topic` — Quick recommendation for the student's next learning topic.

14. `backend/tests/unit/test_learning_path_service.py` (NEW):
    - Unit tests covering prerequisite unlocking logic, mastery thresholds, linear progression fallback, and edge cases (0% mastery, 100% course completion).

15. `backend/tests/integration/test_learning_paths_api.py` (NEW):
    - End-to-end integration tests verifying path generation with mock/real M1 courses and M3 mastery records.

---

## 6. Cross-Module Risks and Mitigation Strategies

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                               CROSS-MODULE RISK MATRIX                                 │
├────┬─────────────────────────────┬──────────┬──────────────────────────────────────────┤
│ ID │ Risk Description            │ Severity │ SQA Mitigation Strategy                  │
├────┼─────────────────────────────┼──────────┼──────────────────────────────────────────┤
│ R1 │ course_enrollments conflict │ HIGH     │ Keep table name identical; reuse columns │
│ R2 │ course_owners duplication   │ HIGH     │ Forward M5 queries to courses.instructor │
│ R3 │ Zero mastery cold-start     │ MEDIUM   │ M4 handles empty M3 records gracefully   │
│ R4 │ Topic ID foreign keys in M2 │ MEDIUM   │ Maintain integer primary key on topics.id│
│ R5 │ Circular prerequisite lock  │ HIGH     │ Mandatory cycle prevention in M1 service │
└────┴─────────────────────────────┴──────────┴──────────────────────────────────────────┘
```

### Risk R1: `course_enrollments` Table Ownership Conflict
- **Details:** Module 5 (`ProgressRepository` in `app/repositories/progress_repository.py`) already reads and writes to a table named `course_enrollments` defined in `app/models/progress.py`.
- **Mitigation:** M1's `EnrollmentModel` will adopt the exact same table name (`course_enrollments`) and schema (`id`, `user_id`, `course_id`, `enrolled_at`, `is_active`). During Phase 1, M1 will assume primary ownership of this entity, ensuring zero database schema drift and 100% backward compatibility for M5's 150 passing tests.

### Risk R2: `course_owners` Fixture vs Authoritative `courses.instructor_id`
- **Details:** M5's `ProgressRepository.is_course_owner()` checks whether an instructor owns a course by querying the temporary `course_owners` table.
- **Mitigation:** When M1's `CourseModel` is implemented, `is_course_owner()` will be updated to query `CourseModel.instructor_id == instructor_id`. To guarantee zero test breakage during transition, `app/models/progress.py`'s `CourseOwnerModel` will be preserved or aliased until all M5 tests are reconciled.

### Risk R3: Student Cold-Start in M4 (Zero Mastery Records in M3)
- **Details:** When a student enrolls in a course, they have 0 quiz attempts and M3 returns an empty list of mastery records.
- **Mitigation:** M4's `LearningPathService` must explicitly treat missing mastery as `score = 0.0, is_mastered = False`. Root topics (topics with 0 prerequisites) will immediately evaluate to `UNLOCKED` and the first topic will be marked `RECOMMENDED`. No HTTP 500 or null pointer exceptions will occur.

### Risk R4: M2 Assessment Module Topic Referencing
- **Details:** M2 (Assessment Module) links quizzes to topics via `topic_id`.
- **Mitigation:** M1's `TopicModel.id` is explicitly defined as `Integer, primary_key=True, autoincrement=True`. M2 can cleanly reference `topics.id` via standard SQLAlchemy foreign keys without structural incompatibility.

### Risk R5: Circular Dependency Deadlock in Prerequisites
- **Details:** If an instructor defines Topic A requiring Topic B, and Topic B requiring Topic A, a student could never unlock either topic, locking the learning path permanently.
- **Mitigation:** M1's `CourseService` enforces a strict Depth-First Search (DFS) cycle-detection algorithm prior to persisting any prerequisite relation. Any cycle creation attempt immediately raises `HTTP 400 Bad Request` with error code `PREREQUISITE_CYCLE_DETECTED`.

---

## 7. Approval Dependencies & Sign-Off Matrix

Before any Git feature branch is created or merged, formal alignment must be signed off by module owners according to the governance rules in `CONTRIBUTING.md`:

| Decision Reference | Scope / Description | Required Approvers | Status |
| :--- | :--- | :--- | :--- |
| **Decision D1** | M1 Authoritative Models (`courses`, `topics`, `prerequisites`, `enrollments`) | Hiba Zulfiqar, Toqeer Ahmed | PENDING |
| **Decision D2** | M1/M5 `course_enrollments` shared table reconciliation | Hiba Zulfiqar, Toqeer Ahmed | PENDING |
| **Decision D3** | M4 Stateless Dynamic Path Generation Architecture | Hiba Zulfiqar, Toqeer Ahmed | PENDING |
| **Decision D4** | M1 REST API Contracts (`/api/v1/courses`) | Hiba Zulfiqar, Toqeer Ahmed, Mustajaab | PENDING |
| **Decision D5** | M4 REST API Contracts (`/api/v1/learning-paths`) | Hiba Zulfiqar, Toqeer Ahmed, Mustajaab | PENDING |
| **Decision D6** | Python runtime environment standardization (3.11/3.12) | Team consensus | PENDING |

---

## 8. Git Branch Workflow Strategy

To prevent merge conflicts and isolate work cleanly, implementation will follow a two-stage sequential branch workflow:

```
main (commit fb4d3c5)
 │
 ├──▶ git checkout -b feature/m1-course-management
 │     │
 │     ├── [Phase 1: M1 Models, Schemas, Repositories]
 │     ├── [Phase 2: M1 Services, Cycle Check, APIs]
 │     ├── [Phase 3: M1 Unit & Integration Tests]
 │     │
 │     ▼ (PR Review & Merge into main)
main (updated with M1)
 │
 └──▶ git checkout -b feature/m4-learning-paths
       │
       ├── [Phase 4: M4 Schemas, Path Service, APIs]
       ├── [Phase 5: M4 Unit & Integration Tests]
       │
       ▼ (PR Review & Merge into main)
main (fully integrated M1 + M4)
```

1. **Branch 1: `feature/m1-course-management`**
   - Created from latest `main`.
   - Delivers M1: Course CRUD, topic ordering, prerequisite cycle check, student enrollment.
   - Verification: All 150 legacy tests + ~25 new M1 tests must pass cleanly.
   - Code Review: Toqeer Ahmed (Lead M3/M5) approves PR.
   - Merged into `main`.

2. **Branch 2: `feature/m4-learning-paths`**
   - Created from updated `main` (which now contains M1).
   - Delivers M4: Learning path service, prerequisite evaluation, dynamic recommendations.
   - Verification: All legacy tests + M1 tests + ~20 new M4 tests must pass cleanly.
   - Code Review: Toqeer Ahmed and Mustajaab Ul Fida Qadri approve PR.
   - Merged into `main`.

---

## 9. Phased Implementation Sequence (11 Stages)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                             11-STAGE IMPLEMENTATION ROADMAP                            │
├───────┬─────────────────────────────────────────────────┬──────────────────────────────┤
│ Stage │ Activity Description                            │ Validation Milestone         │
├───────┼─────────────────────────────────────────────────┼──────────────────────────────┤
│ 01    │ Environment Setup (Python 3.11/3.12 venv)       │ pytest passes 150/150 tests  │
│ 02    │ Branch creation: feature/m1-course-management   │ git branch confirmed         │
│ 03    │ Author M1 Models (app/models/course.py)         │ SQLAlchemy schema validation │
│ 04    │ Author M1 Schemas (app/schemas/course.py)       │ Pydantic serialization tests │
│ 05    │ Author M1 Repository (course_repository.py)     │ Database CRUD unit tests     │
│ 06    │ Author M1 Service (DAG cycle check logic)       │ Cycle detection unit tests   │
│ 07    │ Author M1 Endpoints (app/api/v1/courses.py)     │ API integration tests pass   │
│ 08    │ PR Review & Merge M1 into main                  │ CI passes all tests on main  │
│ 09    │ Branch creation: feature/m4-learning-paths      │ git branch confirmed         │
│ 10    │ Author M4 Schemas, Service & Endpoints          │ Path calculation unit tests  │
│ 11    │ PR Review & Final Merge M4 into main            │ Full system regression pass  │
└───────┴─────────────────────────────────────────────────┴──────────────────────────────┘
```

---

## 10. Outstanding Pre-Implementation Blockers & Sign-Off Checklist

Before Stage 02 can commence, the following two operational items must be resolved:

1. **Python Virtual Environment Creation:**
   - Establish an isolated Python 3.11/3.12 virtual environment on the host machine and verify that all 150 existing tests pass (`pytest -v`).
2. **Formal Team Sign-Off:**
   - Confirmation from Toqeer Ahmed (`2023567`) regarding the `course_enrollments` / `course_owners` backward-compatibility approach.
   - Confirmation from Mustajaab Ul Fida Qadri (`2023728`) regarding M2 topic foreign key referencing.

**Readiness Status:** The architectural blueprints, requirements trace, and SQA safeguards are **100% complete**. Implementation is ready to proceed upon team approval and runtime environment setup.
