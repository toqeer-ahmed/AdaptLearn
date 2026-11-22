# AdaptLearn — M1 and M4 Requirements Reconciliation & Technical Audit

**Document Reference:** `docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md`  
**Author / Lead:** Hiba Zulfiqar (`2023246`) — Lead for M1 (User/Course Management) & M4 (Personalized Learning Paths)  
**Stakeholders:** Toqeer Ahmed (Lead for M3 & M5), Mustajaab Ul Fida Qadri (Lead for M2)  
**Baseline Git Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f` (`fix(ci): resolve backend test collection failure`)  
**Audit Date:** November 21, 2026  
**Status:** Requirements Baseline & Pre-Implementation Architecture Audit  

---

## 1. Authoritative Requirement Sources

The requirements baseline for Module 1 and Module 4 is derived from the following project documents:

1. **AdaptLearn Milestone 1 Report (`SE423 / SE431`)**:
   * *Section 3.1, Table 2*: Functional Requirements baseline (defining original IDs `FR-01` through `FR-08` for M1, and `FR-17` through `FR-19` for M4).
   * *Section 2.3, Table 1*: Project Assumptions (`A-03` Admin-free accounts, `A-04` Self-enrollment, `A-05` Acyclic prerequisite graphs).
   * *Section 3.2, Table 3*: Non-Functional Requirements (`NFR-02` Salted bcrypt & JWT expiry, `NFR-03` Response time targets).
   * *Section 4.1 & 4.2*: Layered Architecture and Module Responsibilities (defining M4 as a read-only, stateless service).
   * *Section 5.1 & 5.2*: Domain Model and Service/Engine Class Diagrams.
   * *Section 11.2, Table 13*: Planned Test Cases (`TC-01` through `TC-08` for M1, `TC-18` through `TC-21` for M4).
2. **Repository Requirements Traceability Matrix (`docs/sqa/requirements_traceability_matrix.md`)**:
   * Maintained by Toqeer Ahmed post-Milestone 2; records implementation and test evidence for verified core and engine components.
3. **Cross-Module API Contracts (`docs/api.md`)**:
   * *Section 2*: Module 1 API Contracts (Auth, Course Management, Topic Hierarchy & Prerequisites).
   * *Section 4*: Module 3 Adaptive Engine Interface & Dataclasses.
   * *Section 5*: Module 4 Personalized Learning Paths Contract (`GET /courses/{id}/learning-path`).
4. **Architecture Decision Records (`docs/decisions.md`)**:
   * *Decision D1*: Domain Model and Pure Engine Isolation (NFR-05).
   * *Decision D5*: User Input Bounds and bcrypt 72-byte Limit.
   * *Decision D6*: SQLAlchemy 2.0 ORM with SQLite (dev) / PostgreSQL (target) Architecture.
   * *CR-01*: Factory Method Pattern for Recommendation Strategy.
5. **Cross-Module Integration Blockers (`docs/INTEGRATION_BLOCKERS.md`)**:
   * Formal defect record (`DEF-MOD-001`) logging the absence of genuine M1 and M2 code on `main`.

---

## 2. Requirement-ID Discrepancy Report

A critical discrepancy exists between the original Milestone 1 Report and the Milestone 2 repository RTM regarding requirement numbering. To ensure complete traceability and avoid ambiguity during testing, both ID mappings are formally documented below:

| Requirement Topic | M1 Report Table 2 ID | Repo RTM Table 2 ID | Scope & Terminology Differences | Confirmed Resolution |
| :--- | :---: | :---: | :--- | :--- |
| **User Registration** | `FR-01` | `FR-01` | Identical: Visitor registers student account with name, unique email, password. | Preserved as **FR-01**. |
| **User Sign-In / JWT** | `FR-02` | `FR-02` | Identical: Authenticate credentials, issue time-limited token, generic 401 error. | Preserved as **FR-02**. |
| **Server-Side RBAC** | `FR-03` | `FR-03` | Identical: Role checks on server; instructor restricted to own courses. | Preserved as **FR-03**. |
| **Course Enrollment** | `FR-07` | `FR-04` | **Conflict**: Numbered `FR-07` in M1 Report; renumbered to `FR-04` in Repo RTM. Repo RTM adds explicit course code enrollment mechanism. | Documented as **FR-07 (Report) / FR-04 (RTM)**. |
| **Course Lifecycle** | `FR-04` | `FR-05` | **Conflict**: Numbered `FR-04` in M1 Report; renumbered to `FR-05` in Repo RTM. Terminology matches (Create, Edit, Archive). | Documented as **FR-04 (Report) / FR-05 (RTM)**. |
| **Topic Management** | `FR-05` | `FR-06` | **Conflict**: Numbered `FR-05` in M1 Report; renumbered to `FR-06` in Repo RTM. Terminology matches (Add, Edit, Reorder, Remove). | Documented as **FR-05 (Report) / FR-06 (RTM)**. |
| **Topic Prerequisites**| `FR-06` | `FR-07` | **Conflict**: Numbered `FR-06` in M1 Report; renumbered to `FR-07` in Repo RTM. Terminology matches (Acyclic DAG, reject self-prereq). | Documented as **FR-06 (Report) / FR-07 (RTM)**. |
| **Enrolled Topic View**| `FR-08` | *Omitted* | **Conflict**: `FR-08` in M1 Report specifies viewing topics in order with prerequisites. In Repo RTM, `FR-08` was assigned to M2 (MCQ question management). | Preserved as **FR-08 (M1 Report)**. |
| **Topic Recommendations**| `FR-17` | `FR-18` | **Conflict**: Numbered `FR-17` in M1 Report; renumbered to `FR-18` in Repo RTM. Weak before Developing, Proficient excluded, prereq priority. | Documented as **FR-17 (Report) / FR-18 (RTM)**. |
| **Recommendation Reason**| `FR-18` | `FR-19` | **Conflict**: Numbered `FR-18` in M1 Report; renumbered to `FR-19` in Repo RTM. Explanatory pedagogical rationale. | Documented as **FR-18 (Report) / FR-19 (RTM)**. |
| **Cold-Start Starting**| `FR-19` | *Omitted* | **Conflict**: `FR-19` in M1 Report specifies prerequisite-free starting points for zero-data students. Omitted as separate row in Repo RTM. | Preserved as **FR-19 (M1 Report)**. |

---

## 3. Module 1: Comprehensive Audit & Implementation Evidence

### Detailed Capability Audit

```
                              Module 1 Status Breakdown
 ┌──────────────────────────────────────┬──────────────────────────────────────┐
 │ IMPLEMENTED & VERIFIED SUBCOMPONENT  │ MISSING / UNBUILT SUBCOMPONENT       │
 ├──────────────────────────────────────┼──────────────────────────────────────┤
 │ 1. User Registration (FR-01)         │ 1. Course Creation (FR-04 / FR-05)   │
 │ 2. User Authentication & JWT (FR-02) │ 2. Course Metadata Editing           │
 │ 3. Server-Side RBAC Guards (FR-03)   │ 3. Course Archiving                  │
 │ 4. Salted bcrypt Hashing (NFR-03)    │ 4. Topic Management (FR-05 / FR-06)  │
 │ 5. UserModel & UserRepository        │ 5. Topic Sequential Reordering       │
 │ 6. Decision D5 Input Bounds          │ 6. Prerequisite DAG & Cycles (FR-06) │
 │                                      │ 7. Course Discovery API (FR-07)      │
 │                                      │ 8. Student Enrollment API (FR-07)    │
 │                                      │ 9. Enrolled Topic Viewing (FR-08)    │
 └──────────────────────────────────────┴──────────────────────────────────────┘
```

#### 1. User Registration (`FR-01`)
* **Original ID:** `FR-01`
* **Description:** A visitor can register a student account with a name, unique email address, and password. Registration with an existing email is rejected.
* **Existing Implementation:**
  * Endpoint: `POST /api/v1/auth/register` in `backend/app/api/v1/endpoints/auth.py` (lines 28–46).
  * Service: `AuthService.register_user` in `backend/app/services/auth_service.py` (lines 23–45).
  * Storage: `UserRepository.create_user` in `backend/app/repositories/user_repository.py` (lines 48–66).
  * Model: `UserModel` in `backend/app/models/user.py` (`id`, `name`, `email`, `password_hash`, `role`, `is_active`).
  * Schema: `UserRegisterRequest` in `backend/app/schemas/auth.py` (Decision D5 bounds: name 1–100, email $\le 254$, password 8–72 bytes).
* **Related Tests:** `backend/tests/unit/test_security_auth.py::TestUserRegistrationApi` (7 tests: valid registration, duplicate email 409 rejection, whitespace name 422, short password 422, password hash exclusion).
* **Actual Verification Status:** **Implemented and Verified** (7/7 tests passed in CI).
* **Remaining Work:** None. Production-ready.

#### 2. User Authentication & Token Issuance (`FR-02`)
* **Original ID:** `FR-02`
* **Description:** A registered user can sign in with email and password and receives a time-limited access token. Invalid credentials are rejected without revealing which field was wrong.
* **Existing Implementation:**
  * Endpoint: `POST /api/v1/auth/login` in `backend/app/api/v1/endpoints/auth.py` (lines 49–73).
  * Service: `AuthService.authenticate_user` in `backend/app/services/auth_service.py` (lines 47–73).
  * Cryptography: `create_access_token` and `verify_password` in `backend/app/core/security.py` (lines 14–60).
  * Token Format: HMAC-SHA256 signed JWT with claims `sub`, `role`, `iat`, `exp` (60-minute lifetime).
* **Related Tests:** `backend/tests/unit/test_security_auth.py::TestUserLoginApi` (4 tests: valid login token issuance, generic 401 error message preventing user enumeration).
* **Actual Verification Status:** **Implemented and Verified** (4/4 tests passed in CI).
* **Remaining Work:** None. Production-ready.

#### 3. Role-Based Access Control (`FR-03`)
* **Original ID:** `FR-03`
* **Description:** Restricts operations to permitted roles. Instructor operations are refused for students; user without valid token is refused for protected operations. Instructors modify only their courses.
* **Existing Implementation:**
  * Dependencies: `get_current_user` and `require_role` in `backend/app/core/auth.py` (lines 32–163).
  * Principal Context: `CurrentUser(user_id=int, role=str)`.
  * Endpoint Guards: Applied in `analytics.py` (`require_role(["instructor"])`) and `progress.py` (`require_role(["student", "instructor"])`).
* **Related Tests:** `backend/tests/unit/test_auth.py` (18 tests), `backend/tests/integration/test_instructor_analytics_api.py::test_student_calling_instructor_endpoint_rejected_tc_03_1`.
* **Actual Verification Status:** **Implemented and Verified** (Role enforcement active; course ownership checks currently performed manually via M5's `ProgressRepository`).
* **Remaining Work:** Integrate course ownership checks directly into M1's `CourseService`.

#### 4. Course Creation, Editing, and Archiving (`FR-04` Report / `FR-05` RTM)
* **Original ID:** `FR-04` (Report) / `FR-05` (RTM)
* **Description:** An instructor can create, edit and archive a course. Archived courses are not offered for enrolment.
* **Existing Implementation:** **None**.
  * `backend/app/api/v1/api.py:19`: Router commented out (`# api_router.include_router(courses.router...)`).
  * `app/models/course.py`: Does not exist.
  * `app/services/course_service.py`: Does not exist.
  * `app/repositories/course_repository.py`: Does not exist.
* **Related Tests:** Blocked: `TC-04-1`, `TC-04-2`, `TC-05-1`, `TC-05-2`.
* **Actual Verification Status:** **Not Implemented**.
* **Remaining Work:** Complete implementation of `CourseModel`, `CourseRepository`, `CourseService`, and `/api/v1/courses` endpoints.

#### 5. Topic Management & Sequential Ordering (`FR-05` Report / `FR-06` RTM)
* **Original ID:** `FR-05` (Report) / `FR-06` (RTM)
* **Description:** An instructor can add, edit, reorder and remove topics in a course they teach.
* **Existing Implementation:** **None**.
  * Note: `app/models/adaptive.py` contains `CourseTopicModel`, but it is an M3 fixture table storing static mastery scores, not an M1 topic management entity.
* **Related Tests:** Blocked: `TC-06-1`, `TC-06-2`.
* **Actual Verification Status:** **Not Implemented**.
* **Remaining Work:** Implement `TopicModel`, atomic topic reordering logic (`PUT /courses/{id}/topics/order`), and topic CRUD endpoints.

#### 6. Prerequisite Relationships & Cycle Prevention (`FR-06` Report / `FR-07` RTM)
* **Original ID:** `FR-06` (Report) / `FR-07` (RTM)
* **Description:** An instructor can define that a topic requires another topic of the same course. System rejects self-prerequisites and circular prerequisite dependencies.
* **Existing Implementation:** **None**.
  * Prerequisite data is currently simulated in M3 via a serialized JSON string `prerequisites_json = "[]"` on `CourseTopicModel`. No cycle-checking algorithm or validation exists.
* **Related Tests:** Blocked: `TC-07-1` to `TC-07-4`.
* **Actual Verification Status:** **Not Implemented**.
* **Remaining Work:** Implement `TopicPrerequisiteModel`, DFS graph cycle-detection algorithm in `CourseService.add_prerequisite`, and `POST /topics/{id}/prerequisites` endpoint.

#### 7. Course Discovery & Student Enrollment (`FR-07` Report / `FR-04` RTM)
* **Original ID:** `FR-07` (Report) / `FR-04` (RTM)
* **Description:** A student can view available courses and enrol in a course.
* **Existing Implementation:** **Partially Implemented (Database / Repository Only)**.
  * Model: `EnrollmentModel` exists in `backend/app/models/progress.py` (table `course_enrollments`).
  * Repository: `ProgressRepository` contains helper methods `enroll_student()`, `is_student_enrolled()`.
  * Public API: **Missing**. No `GET /api/v1/courses` or `POST /api/v1/courses/{id}/enroll` endpoint exists.
* **Related Tests:** Internal helper verified via `test_persistence.py` and `test_cross_module_integration.py`. Student-facing API is untested.
* **Actual Verification Status:** **Partially Implemented**.
* **Remaining Work:** Expose student course discovery and enrollment endpoints with course-code verification.

#### 8. Enrolled Topic & Prerequisite Viewing (`FR-08` Report)
* **Original ID:** `FR-08` (Report)
* **Description:** An enrolled student can view the topics of the course, in course order, together with their prerequisites.
* **Existing Implementation:** **None**.
* **Related Tests:** None.
* **Actual Verification Status:** **Not Implemented**.
* **Remaining Work:** Implement `GET /api/v1/courses/{id}/topics` with enrolled student authorization.

---

## 4. Module 4: Comprehensive Audit & Implementation Evidence

### Detailed Capability Audit

```
                              Module 4 Status Breakdown
 ┌──────────────────────────────────────┬──────────────────────────────────────┐
 │ IMPLEMENTED & VERIFIED SUBCOMPONENT  │ MISSING / UNBUILT SUBCOMPONENT       │
 ├──────────────────────────────────────┼──────────────────────────────────────┤
 │ 1. RecommendationStrategy Interface  │ 1. LearningPath Router (/courses/id) │
 │ 2. RuleBasedRecommendationStrategy   │ 2. LearningPathService coordinator   │
 │ 3. GoF Factory Method Pattern (CR-01)│ 3. LearningPath Pydantic Schemas     │
 │ 4. Prerequisite ranking constraints  │ 4. Full curriculum roadmap traversal │
 │ 5. Alphabetical tie-breaking (NFR-10)│ 5. Boolean is_unlocked evaluation    │
 │ 6. Rationale string generator (FR-18)│ 6. Descriptive locked_reason string  │
 │ 7. Cold-start zero-attempt handling  │ 7. Authenticated student integration │
 └──────────────────────────────────────┴──────────────────────────────────────┘
```

#### 1. Pure Computational Recommendation Engine (`FR-17` / `FR-18`)
* **Original ID:** `FR-17`, `FR-18` (Report) / `FR-18`, `FR-19` (RTM)
* **Existing Implementation:**
  * Engine Module: `backend/app/engine/recommendation_strategy.py` (375 lines of pure Python, zero outer framework imports).
  * Strategy Interface: `RecommendationStrategy(ABC)` with abstract method `recommend()`.
  * Concrete Strategy: `RuleBasedRecommendationStrategy`:
    * Step 1: Filters out all `Proficient` topics (FR-18, TC-18-2).
    * Step 2: Identifies available candidates whose unmastered prerequisites have already been placed (TC-18-3).
    * Step 3: Selects best topic using deterministic tuple: `(LEVEL_PRIORITY, score, name.lower(), topic_id)`.
    * Step 4: Generates human-readable pedagogical rationale string (`_generate_rationale`).
  * Creational Design Pattern (SE423 Rubric CR-01): `RecommendationStrategyCreator` (abstract creator) and `RuleBasedStrategyCreator` (concrete creator) with factory function `get_strategy_creator()`.
* **Related Tests:** `backend/tests/unit/test_recommendation_strategy.py` (18 passing unit tests verifying TC-18-1 through TC-18-6, tie-breaking, rationale formatting, and factory instantiation).
* **Actual Verification Status:** **Implemented and Verified** (18/18 tests passed).
* **Remaining Work:** None in computational engine. Complete.

#### 2. Dedicated Learning Path Router & Service (`docs/api.md` §5)
* **Specification Target:** `GET /api/v1/courses/{id}/learning-path`
* **Existing Implementation:** **None**.
  * `backend/app/api/v1/api.py:21`: Router commented out (`# api_router.include_router(learning_paths.router...)`).
  * `app/services/learning_path_service.py`: Does not exist.
  * `app/schemas/learning_path.py`: Does not exist.
  * Current Workaround: Recommendations are exposed via M3's `GET /api/v1/courses/{id}/recommendations` in `adaptive.py`, but that endpoint:
    * Returns only a flat list of recommended topics (not the full sequenced curriculum).
    * Oromits authentication guards (`CurrentUser` dependency is absent).
    * Hardcodes `student_id = 1` and reads static scores from fixture table `course_topics`.
* **Related Tests:** None for the dedicated learning-path endpoint.
* **Actual Verification Status:** **Not Implemented**.
* **Remaining Work:**
  * Implement `TopicPathItem` and `LearningPathResponse` schemas.
  * Implement `LearningPathService` executing the two-phase hybrid traversal:
    * *Phase 1*: Traverse M1 topic DAG in `order_index` order; evaluate prerequisite satisfaction to assign `is_unlocked` and `locked_reason`.
    * *Phase 2*: Pass unlocked non-Proficient topics to `RuleBasedRecommendationStrategy` to tag `is_recommended = true`.
  * Implement and mount router `backend/app/api/v1/endpoints/learning_paths.py`.

---

## 5. Cross-Module Dependencies & Consumer Audit

An exhaustive inspection of imports and repository queries across the codebase reveals the following dependency topology:

```
                                  Codebase Dependency Topology
 ┌───────────────────────────┬──────────────────────────────────┬─────────────────────────────┐
 │ Data / Entity             │ Current Defining File & Model    │ Actual Codebase Consumers   │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ User Account & Identity   │ app/models/user.py               │ - app/services/auth_service │
 │                           │ (UserModel, table 'users')       │ - app/core/auth.py (JWT)    │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ Course Ownership          │ app/models/progress.py           │ - app/api/v1/analytics.py   │
 │                           │ (CourseOwnerModel,               │ - app/repositories/progress │
 │                           │  table 'course_owners')          │ - test_instructor_analytics │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ Course Enrollment         │ app/models/progress.py           │ - app/api/v1/progress.py    │
 │                           │ (EnrollmentModel,                │ - app/api/v1/analytics.py   │
 │                           │  table 'course_enrollments')     │ - app/repositories/progress │
 │                           │                                  │ - test_cross_module_integ   │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ Course Topics & Prereqs   │ app/models/adaptive.py           │ - app/services/adaptive_serv│
 │                           │ (CourseTopicModel,               │ - app/services/progress_serv│
 │                           │  table 'course_topics')          │ - app/services/analytics_ser│
 │                           │                                  │ - app/repositories/adaptive │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ Student Response History  │ app/models/adaptive.py           │ - app/services/adaptive_serv│
 │                           │ (StudentTopicResponseModel)      │ - app/repositories/adaptive │
 ├───────────────────────────┼──────────────────────────────────┼─────────────────────────────┤
 │ Quiz Attempts & Answers   │ app/models/progress.py           │ - app/services/progress_serv│
 │                           │ (AttemptModel,                   │ - app/repositories/progress │
 │                           │  table 'quiz_attempts')          │ - test_progress_api.py      │
 └───────────────────────────┴──────────────────────────────────┴─────────────────────────────┘
```

### Critical Findings on Inter-Module Couplings

1. **`CourseOwnerModel` Coupling**:
   * Defined in `app/models/progress.py` (M5).
   * Consumers: `analytics.py` (lines 49, 83, 116) and `ProgressRepository.is_course_owner()`.
   * *Risk*: If M1 introduces `CourseModel` with column `instructor_id` and drops `course_owners`, M5's instructor analytics endpoints will immediately crash with database errors.
   * *Required Solution*: `CourseModel.instructor_id` must become authoritative, and `ProgressRepository.is_course_owner()` must be redirected to query `CourseModel` (or alias it).
2. **`EnrollmentModel` Coupling**:
   * Defined in `app/models/progress.py` (table `course_enrollments`).
   * Consumers: `progress.py`, `analytics.py`, and `ProgressRepository`.
   * *Risk*: If M1 creates a new enrollment table with a different name (e.g. `enrollments`), M5 progress checks will fail.
   * *Required Solution*: M1 must adopt the exact table name `course_enrollments` and columns `(id, student_id, course_id)`.
3. **`CourseTopicModel` Monolith in M3**:
   * Defined in `app/models/adaptive.py` (table `course_topics`).
   * Stores static mock scores and stringified JSON prerequisites (`prerequisites_json = "[]"`).
   * Consumers: Queried by `AdaptiveService`, `ProgressService`, and `AnalyticsService`.
   * *Required Solution*: M1 will implement genuine relational entities `TopicModel` (`topics`) and `TopicPrerequisiteModel` (`topic_prerequisites`). `AdaptiveRepository` will be updated to read from M1's `TopicModel`.

---

## 6. M1 and M4 Requirements Traceability Matrix

This matrix includes **only original requirement IDs** and documents their verified implementation status in the codebase.

| Requirement ID | Description | Existing Files & Artifacts | Related Tests | Implementation Status | Remaining Work |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **FR-01** | User registration with name, unique email, password, role | `app/api/v1/endpoints/auth.py`<br>`app/services/auth_service.py`<br>`app/repositories/user_repository.py`<br>`app/models/user.py`<br>`app/schemas/auth.py` | `backend/tests/unit/test_security_auth.py::TestUserRegistrationApi` (7 tests) | **Implemented and Verified** | None. Complete. |
| **FR-02** | User login and token generation with generic 401 error | `app/api/v1/endpoints/auth.py`<br>`app/services/auth_service.py`<br>`app/core/security.py`<br>`app/schemas/auth.py` | `backend/tests/unit/test_security_auth.py::TestUserLoginApi` (4 tests) | **Implemented and Verified** | None. Complete. |
| **FR-03** | Server-side role-based access control per course and role | `app/core/auth.py`<br>`app/api/v1/endpoints/analytics.py`<br>`app/api/v1/endpoints/progress.py` | `tests/unit/test_auth.py` (18 tests)<br>`test_instructor_analytics_api.py::test_student_calling_instructor_endpoint_rejected_tc_03_1` | **Implemented and Verified** | Integrate course ownership validation directly into M1 `CourseService`. |
| **FR-04** | Instructor create, edit, archive courses *(FR-05 in RTM)* | *None* (router placeholder in `api.py:19`) | Blocked: `TC-04-1`, `TC-04-2`, `TC-05-1`, `TC-05-2` | **Not Implemented** | Author `CourseModel`, `CourseRepository`, `CourseService`, and `/courses` endpoints. |
| **FR-05** | Instructor add, edit, reorder, remove topics *(FR-06 in RTM)* | *None* | Blocked: `TC-06-1`, `TC-06-2` | **Not Implemented** | Author `TopicModel`, atomic sequential reordering service, and topic CRUD endpoints. |
| **FR-06** | Define topic prerequisites and reject circular dependencies *(FR-07 in RTM)* | *None* | Blocked: `TC-07-1` to `TC-07-4` | **Not Implemented** | Author `TopicPrerequisiteModel`, DFS graph cycle-detection algorithm, and prerequisite endpoint. |
| **FR-07** | Student view available courses and enrol in a course *(FR-04 in RTM)* | `app/models/progress.py` (`EnrollmentModel`)<br>`app/repositories/progress_repository.py` | `test_persistence.py`<br>`test_cross_module_integration.py` (helper methods only) | **Partially Implemented** | Expose public `GET /courses` catalog and `POST /courses/{id}/enroll` endpoint. |
| **FR-08** | Enrolled student view topics in course order with prerequisites | *None* | *None* | **Not Implemented** | Author `GET /courses/{id}/topics` with enrolled authorization check. |
| **FR-17** | Prerequisite-aware topic recommendations (Weak before Developing, Proficient excluded) *(FR-18 in RTM)* | `app/engine/recommendation_strategy.py`<br>`app/services/adaptive_service.py` | `backend/tests/unit/test_recommendation_strategy.py` (12 tests) | **Implemented and Verified (Engine)** | Expose full curriculum learning path view (`GET /courses/{id}/learning-path`). |
| **FR-18** | Display mastery score, level, and cause rationale for each recommended topic *(FR-19 in RTM)* | `app/engine/recommendation_strategy.py`<br>`app/schemas/adaptive.py` | `backend/tests/unit/test_recommendation_strategy.py::test_recommendation_rationale_non_empty` | **Implemented and Verified (Engine)** | Format and attach rationales in `LearningPathResponse`. |
| **FR-19** | Recommend prerequisite-free topics as suggested starting points for zero-data students | `app/engine/recommendation_strategy.py` (handled via fallback tie-breaking) | `backend/tests/unit/test_recommendation_strategy.py` | **Implemented and Verified (Engine)** | Format cold-start starting-point rationale in `LearningPathResponse`. |

---

## 7. Database Ownership Risks & Mitigation Strategies

```
                                Relational Migration Plan
 ┌───────────────────────┬─────────────────────────────────────────────────────┐
 │ Identified Risk       │ Architectural Mitigation Strategy                   │
 ├───────────────────────┼─────────────────────────────────────────────────────┤
 │ 1. Breaking M5 Course │ Create CourseModel in app/models/course.py with     │
 │    Ownership Checks   │ column 'instructor_id'. Update ProgressRepository   │
 │                       │ is_course_owner() to query 'courses' table.         │
 ├───────────────────────┼─────────────────────────────────────────────────────┤
 │ 2. Enrollment Table   │ Adopt exact table name 'course_enrollments' and     │
 │    Collision          │ columns (id, student_id, course_id). Move model     │
 │                       │ declaration to M1 without altering SQL DDL.         │
 ├───────────────────────┼─────────────────────────────────────────────────────┤
 │ 3. Prerequisite Graph │ Enforce DFS cycle check in CourseService prior to   │
 │    Recursion / Cycles │ commit. Add UniqueConstraint(topic_id, prereq_id)    │
 │                       │ and CheckConstraint(topic_id != prereq_id).         │
 ├───────────────────────┼─────────────────────────────────────────────────────┤
 │ 4. Stateless M4       │ M4 introduces ZERO database tables. Dynamically     │
 │    Architecture       │ derives learning paths on request (M1 Report §4.2). │
 └───────────────────────┴─────────────────────────────────────────────────────┘
```

---

## 8. Test Coverage Gaps & SQA Action Plan

1. **Local Test Execution Block**: Local test execution is blocked pending creation of `backend/venv` and installation of `requirements.txt`. (CI baseline confirms 150 automated tests pass).
2. **Missing Integration Tests for Unbuilt M1 Features**:
   * Course creation and duplicate course code rejection.
   * Course owner security guard (Instructor A modifying Instructor B's course).
   * Topic sequential reordering transactional integrity.
   * Prerequisite cycle detection (self-prerequisite, 2-node cycle, multi-node cycle).
   * Student enrollment in archived course rejection.
3. **Missing Integration Tests for M4 Learning Path**:
   * Cold start with zero attempts: prerequisite-free topics unlocked with starting-point rationale.
   * Prerequisite satisfaction: topic unlocks when prerequisite reaches `Proficient`.
   * Unmet prerequisite: topic remains locked with descriptive `locked_reason`.
   * Unauthenticated and unenrolled access rejection (HTTP 401 / 403).

---

## 9. Unresolved Questions for Team Consensus

* **Decision 1: Prerequisite Unlocking Band (Hiba & Toqeer)**:
  * *Status*: Unresolved.
  * *Options*: Does a prerequisite unlock dependent topics when reaching **`Proficient` ($\ge 0.80$)** or **`Developing` ($\ge 0.50$)**?
  * *Architectural Recommendation*: Adopt **`Proficient` ($\ge 0.80$)** to align with mastery learning principles and `docs/api.md` §5.
* **Decision 2: Course Code Generation (Hiba & Team)**:
  * *Status*: Unresolved.
  * *Options*: Instructor-chosen string (e.g., `SE423-2026`) vs system-generated random code.
  * *Architectural Recommendation*: Allow instructor to provide an alphanumeric course code, enforced with a unique database index.
* **Decision 3: Topic Deletion Policy (Hiba & Mustajaab)**:
  * *Status*: Unresolved.
  * *Options*: Hard delete cascade vs restricted deletion (`400 Bad Request` if questions/attempts exist).
  * *Architectural Recommendation*: Enforce restricted deletion to preserve historical student assessment records.

---

## 10. Recommended Implementation Sequence

```
Phase 1: Environment & Virtualenv Setup
 └── 1. Create backend/venv and install requirements.txt ($env:PYTHONPATH='backend'; pytest backend/tests).
 └── 2. Confirm all 150 baseline tests pass locally.

Phase 2: M1 Relational Foundations (Branch: feature/m1-course-management)
 └── 3. Create app/models/course.py (CourseModel, TopicModel, TopicPrerequisiteModel, EnrollmentModel).
 └── 4. Create app/schemas/course.py (Pydantic request/response schemas).
 └── 5. Implement app/repositories/course_repository.py with DFS cycle-detection query.
 └── 6. Implement app/services/course_service.py enforcing ownership, acyclic rules, and enrollment.
 └── 7. Implement app/api/v1/endpoints/courses.py and mount in api.py.
 └── 8. Write unit and integration tests (test_course_models.py, test_courses_api.py).

Phase 3: M4 Learning Path Integration (Branch: feature/m4-learning-paths)
 └── 9. Create app/schemas/learning_path.py (TopicPathItem, LearningPathResponse).
 └── 10. Implement app/services/learning_path_service.py (Two-phase hybrid DAG traversal & strategy delegation).
 └── 11. Implement app/api/v1/endpoints/learning_paths.py (GET /courses/{id}/learning-path).
 └── 12. Mount router in api.py and write integration tests (test_learning_paths_api.py).

Phase 4: Regression Verification & PR Submission
 └── 13. Run full test suite (ensure 180+ tests pass with zero regressions).
 └── 14. Verify NFR-05 layer isolation via tests/architecture/test_layers.py.
 └── 15. Submit PR for team code review per CONTRIBUTING.md.
```
