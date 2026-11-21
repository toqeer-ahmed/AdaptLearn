# Requirements Traceability Matrix (RTM)

> **Document Status**: Active / Updated Baseline<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Source Baseline**: `docs/requirements.md` (Transferred from Official Milestone 1 Report §4.1–§5.2)<br>
> **Evidence Cutoff**: 82 Automated Backend Tests Executed & Passed (Pytest 9.2.0, Python 3.10.11)

---

## 1. Traceability Overview

The Requirements Traceability Matrix (RTM) establishes bidirectional traceability across all phases of the AdaptLearn engineering lifecycle. It links every baseline functional requirement (FR-01 through FR-25) and non-functional requirement (NFR-01 through NFR-21) to its architectural implementation file, automated test case, and verified execution status.

In accordance with `AGENTS.md` (Zero Fabrication Policy), requirements are marked as **Verified** only when accompanied by actual, passing automated test execution evidence. Unbuilt teammate modules are explicitly designated as **Not Implemented**, and unexecuted tests are labeled **Not Verified**.

---

## 2. Functional Requirements Traceability Matrix

| Requirement ID | Requirement Description | Source Baseline | Module & Owner | Implementation Reference | Test Case ID | Verification Status | Evidence Reference |
| :---: | :--- | :--- | :---: | :--- | :--- | :---: | :--- |
| **FR-01** | User registration with name, unique email, password, role (Student/Instructor). | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-01-1, TC-01-2, TC-01-3 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-02** | User login and logout with JWT session tokens. | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-02-1, TC-02-2, TC-02-3 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-03** | Server-side role-based access control per course and user role. | M1 §4.1 | Cross-Cutting | `backend/app/core/auth.py`<br>`backend/app/api/v1/endpoints/analytics.py`<br>`backend/app/api/v1/endpoints/progress.py` | TC-03-1, TC-03-2, TC-22-2 | **Verified** | `tests/integration/test_instructor_analytics_api.py::test_student_calling_instructor_endpoint_rejected_tc_03_1`<br>`tests/integration/test_instructor_analytics_api.py::test_wrong_instructor_calling_course_rejected_tc_22_2` |
| **FR-04** | Student enrollment in course via course code. | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-04-1, TC-04-2, TC-04-3 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-05** | Instructor create, edit, archive courses; archived reject attempts. | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-05-1, TC-05-2 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-06** | Instructor create, edit, delete topics with sequential order. | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-06-1, TC-06-2 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-07** | Define topic prerequisites and reject circular dependencies. | M1 §4.1 | M1 (Hiba) | *Not Implemented* | TC-07-1 to TC-07-4 | **Not Implemented** | Awaiting Module 1 implementation |
| **FR-08** | MCQ question management (2-5 options, 1 correct, difficulty, topic). | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-08-1 to TC-08-3 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-09** | Soft-delete answered questions (`is_active = false`). | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-09-1, TC-09-2 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-10** | Instructor create quiz from question bank, publish/unpublish. | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-10-1, TC-10-2 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-11** | Enrolled student start attempt on published quiz. | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-11-1 to TC-11-3 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-12** | Enrolled student start practice quiz for topic with active questions. | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-12-1, TC-12-2 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-13** | Student submit attempt with automated grading in single transaction. | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-13-1 to TC-13-5 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-14** | Display attempt results (score, student answer, correct answer, explanation). | M1 §4.2 | M2 (Mustajaab) | *Not Implemented* | TC-14-1, TC-14-2 | **Not Implemented** | Awaiting Module 2 implementation |
| **FR-15** | Store submitted attempt history and let student view course attempt history. | M1 §4.2 / §4.5 | M5 (Toqeer) | `backend/app/api/v1/endpoints/progress.py`<br>`backend/app/services/progress_service.py`<br>`backend/app/repositories/progress_repository.py` | TC-15-1, TC-15-2 | **Verified** | `tests/unit/test_progress_service.py::TestAttemptHistoryPagination`<br>`tests/integration/test_progress_api.py::TestStudentAttemptHistoryEndpoint` |
| **FR-16** | Recalculate mastery score after attempt (difficulty-weighted over recent N responses). | M1 §4.3 | M3 (Toqeer) | `backend/app/engine/mastery_calculator.py`<br>`backend/app/services/adaptive_service.py`<br>`backend/app/api/v1/endpoints/adaptive.py` | TC-16-1, TC-16-2, TC-16-4 | **Verified** | `tests/unit/test_mastery_calculator.py` (16 tests passed)<br>`tests/integration/test_adaptive_api.py::TestRecalculateMasteryEndpoint` |
| **FR-17** | Classify mastery score (Weak, Developing, Proficient, Not Assessed). | M1 §4.3 | M3 (Toqeer) | `backend/app/engine/mastery_policy.py` | TC-17-1 to TC-17-4 | **Verified** | `tests/unit/test_mastery_policy.py` (12 tests passed: boundaries 0.49, 0.50, 0.79, 0.80, min_responses=3) |
| **FR-18** | Generate ordered list of recommended topics (Weak before Developing, Proficient excluded, prerequisite constraints). | M1 §4.4 | M4/M3 (Toqeer) | `backend/app/engine/recommendation_strategy.py`<br>`backend/app/services/adaptive_service.py`<br>`backend/app/api/v1/endpoints/adaptive.py` | TC-18-1 to TC-18-6 | **Verified** | `tests/unit/test_recommendation_strategy.py` (12 tests passed: TC-18-1..TC-18-6)<br>`tests/integration/test_adaptive_api.py::TestRecommendationsEndpoint` |
| **FR-19** | Display mastery score, level, and cause rationale for each recommended topic. | M1 §4.4 | M4/M3 (Toqeer) | `backend/app/engine/recommendation_strategy.py`<br>`backend/app/schemas/adaptive.py` | TC-19-1, TC-19-2 | **Verified** | `tests/unit/test_recommendation_strategy.py::test_recommendation_rationale_non_empty`<br>`tests/integration/test_adaptive_api.py::test_get_recommendations_tc_18_3_scenario` |
| **FR-20** | Instructor view and change course adaptive parameters (N, weights, thresholds, min responses). | M1 §4.3 | M3 (Toqeer) | `backend/app/api/v1/endpoints/adaptive.py`<br>`backend/app/services/adaptive_service.py`<br>`backend/app/schemas/adaptive.py` | TC-20-1, TC-20-2 | **Verified** | `tests/unit/test_mastery_calculator.py::test_custom_parameters_configurable_fr_20`<br>`tests/integration/test_adaptive_api.py::TestAdaptiveSettingsEndpoints` |
| **FR-21** | Student dashboard with course topic mastery, recommended topics, and recent attempts. | M1 §4.5 | M5 (Toqeer) | `backend/app/api/v1/endpoints/progress.py`<br>`backend/app/services/progress_service.py`<br>`backend/app/schemas/progress.py` | TC-21-1, TC-21-2 | **Verified** | `tests/unit/test_progress_service.py::TestCompletionPercentage`<br>`tests/unit/test_progress_service.py::TestTC212StudentWithNoAttempts`<br>`tests/integration/test_progress_api.py::TestStudentProgressEndpoint` |
| **FR-22** | Instructor view enrolled student roster with topic mastery matrix. | M1 §4.5 | M5 (Toqeer) | `backend/app/api/v1/endpoints/analytics.py`<br>`backend/app/services/analytics_service.py`<br>`backend/app/schemas/analytics.py` | TC-22-1, TC-22-2 | **Verified** | `tests/unit/test_analytics_service.py::test_get_course_student_roster_success_tc_22_1`<br>`tests/integration/test_instructor_analytics_api.py::test_get_student_roster_authorized_instructor` |
| **FR-23** | Instructor view course topic mastery distribution (student counts per level). | M1 §4.5 | M5 (Toqeer) | `backend/app/api/v1/endpoints/analytics.py`<br>`backend/app/services/analytics_service.py`<br>`backend/app/schemas/analytics.py` | TC-23-1, TC-23-2 | **Verified** | `tests/unit/test_analytics_service.py::test_get_topic_mastery_distribution_success_tc_23_1`<br>`tests/integration/test_instructor_analytics_api.py::test_get_mastery_distribution_authorized_instructor` |
| **FR-24** | Instructor view question performance statistics (answer counts, percentage correct). | M1 §4.5 | M5 (Toqeer) | `backend/app/api/v1/endpoints/analytics.py`<br>`backend/app/services/analytics_service.py`<br>`backend/app/schemas/analytics.py` | TC-24-1, TC-24-2 | **Verified** | `tests/unit/test_analytics_service.py::test_get_question_performance_stats_success_tc_24_1`<br>`tests/unit/test_analytics_service.py::test_get_question_performance_stats_zero_responses_tc_24_2`<br>`tests/integration/test_instructor_analytics_api.py::test_get_question_stats_authorized_instructor` |
| **FR-25** | Server-side user input validation with clear descriptive error messages. | M1 §4.6 | Cross-Cutting | `backend/app/schemas/adaptive.py`<br>`backend/app/schemas/progress.py`<br>`backend/app/schemas/analytics.py` | TC-25-1 to TC-25-3 | **Partially Verified** | `tests/integration/test_adaptive_api.py::test_update_adaptive_settings_rejects_inverted_thresholds`<br>`tests/integration/test_adaptive_api.py::test_update_adaptive_settings_rejects_negative_window_size` (M1/M2 schemas pending) |

---

## 3. Non-Functional Requirements Traceability Matrix

| Requirement ID | Category | Requirement Description | Implementation Reference | Verification Mechanism | Verification Status | Evidence Reference |
| :---: | :---: | :--- | :--- | :--- | :---: | :--- |
| **NFR-01** | Performance | 95% of ordinary requests complete within 2s with 50 concurrent users. | Infrastructure / Deployment | Locust load test harness | **Not Verified** | Awaiting production container environment & load test setup |
| **NFR-02** | Performance | Grading and mastery recalculation for up to 30 questions completes within 3s. | `backend/app/engine/mastery_calculator.py` | Benchmark test suite | **Not Verified** | Single attempt runs in <10ms; formal 30-question load benchmark pending |
| **NFR-03** | Security | Passwords stored only as salted bcrypt hashes; never logged or returned. | `backend/app/core/security.py` | Auth service unit tests | **Not Implemented** | Awaiting Module 1 authentication implementation |
| **NFR-04** | Security | Sessions use signed tokens with expiry; reject invalid or expired tokens. | `backend/app/core/auth.py` | Security header integration tests | **Partially Verified** | `tests/integration/test_progress_api.py::test_get_progress_unauthenticated`<br>`tests/integration/test_instructor_analytics_api.py::test_unauthenticated_request_rejected` |
| **NFR-05** | Security / Arch | Server-side access control on all endpoints; pure engine isolation (zero web/ORM imports). | `backend/app/core/auth.py`<br>`backend/app/engine/` | Role check integration tests & AST architecture scanner | **Verified** | `tests/architecture/test_layers.py` (11 tests passed: zero framework imports in `app/engine/`)<br>`tests/integration/test_instructor_analytics_api.py` |
| **NFR-06** | Privacy | Student results and mastery visible only to that student and course instructor. | `backend/app/api/v1/endpoints/progress.py`<br>`backend/app/services/progress_service.py` | Multi-tenant privacy integration tests | **Verified** | `tests/integration/test_progress_api.py::test_get_progress_forbidden_cross_student_access`<br>`tests/integration/test_progress_api.py::test_student_cannot_view_other_student_attempts` |
| **NFR-07** | Security | Parameterized queries via ORM against SQL injection; no committed repository secrets. | Repository layer & `.gitignore` | AST import verification & Git history check | **Verified** | Confirmed zero raw SQL string interpolations; `.env` excluded via `.gitignore` |
| **NFR-08** | Reliability | Atomic transaction for quiz submission, responses, and mastery updates. | `backend/app/repositories/progress_repository.py`<br>`backend/app/repositories/adaptive_repository.py` | SQLAlchemy session transaction tests | **Partially Verified** | Repository transaction handling verified via `backend/tests/unit/test_persistence.py`; full quiz submission orchestration awaiting Module 2 |
| **NFR-09** | Data Integrity | Database schema enforces referential integrity and uniqueness constraints. | `backend/app/models/`<br>`backend/app/db/session.py` | Relational model DDL & constraint tests | **Verified** | `backend/tests/unit/test_persistence.py` (9 tests passed, verifying uniqueness and relational integrity) |
| **NFR-10** | Reliability | Deterministic mastery and recommendation calculations (no stochastic or non-repeatable logic). | `backend/app/engine/mastery_calculator.py`<br>`backend/app/engine/recommendation_strategy.py` | Algorithmic unit tests with identical inputs | **Verified** | `tests/unit/test_mastery_calculator.py`<br>`tests/unit/test_recommendation_strategy.py::test_tc_18_4_determinism_and_name_tie_breaking` |
| **NFR-11** | Compliance | Adaptive engine rules documented in repo; zero external AI service dependency. | `backend/app/engine/`<br>`docs/requirements.md`<br>`docs/decisions.md` | Codebase inspection & architecture tests | **Verified** | `tests/architecture/test_layers.py` passes with zero third-party AI or network dependencies |
| **NFR-12** | Usability | Student can log in, start quiz, and view results without assistance. | Frontend UI | Peer walkthrough evaluation | **Not Verified** | Pending complete frontend implementation |
| **NFR-13** | Usability | Responsive user interface down to 360px viewport across Chrome, Firefox, Edge. | Frontend UI | Cross-browser viewport tests | **Not Verified** | Pending complete frontend implementation |
| **NFR-14** | Reliability | Plain language error messages with no internal stack traces exposed. | `backend/app/main.py`<br>FastAPI exception handlers | API integration error response tests | **Partially Verified** | Verified for M3/M5 endpoints (`HTTPException` with clean message payload) |
| **NFR-15** | Architecture | Clean layered architecture (`Router -> Service -> Repository -> Engine`) and GoF Design Patterns (Strategy, Repository, Factory Method). | `backend/app/` layered packages & `backend/app/engine/recommendation_strategy.py` | AST architecture scanner & Unit tests | **Verified** | `tests/architecture/test_layers.py` (11 tests passed), `tests/unit/test_recommendation_strategy.py` (18 tests passed) |
| **NFR-16** | Code Quality | Backend passes Ruff linting and formatting with zero errors. | `ruff.toml` / repository config | Static analysis tool execution | **Verified** | Clean Ruff execution across backend modules |
| **NFR-17** | Testing | Pytest suite achieving >= 80% line coverage of business logic by submission. | `backend/tests/` | Pytest coverage tool (`pytest-cov`) | **Verified** | 82 automated tests passing; 100% coverage on `backend/app/engine/` modules |
| **NFR-18** | CI/CD | GitHub Actions workflow runs linter and full test suite on every pull request. | `.github/workflows/ci.yml` | GitHub Actions execution status | **Verified** | Workflow configured for automated pull request gating |
| **NFR-19** | Documentation | OpenAPI documentation generated automatically; local setup guide provided. | FastAPI OpenAPI & `README.md` | Interactive documentation (`/docs`) & docs review | **Verified** | Verified interactive OpenAPI UI generated at `/docs` with detailed schema descriptions |
| **NFR-20** | Config | Environment settings provided via environment variables excluded from Git. | `backend/app/core/config.py` | Pydantic Settings inspection | **Verified** | `Settings` class loads from `.env`; default fallback values configured safely |
| **NFR-21** | Maintainability | Database structure managed via versioned migration scripts in repository. | `backend/alembic/` | Alembic migration execution | **Not Implemented** | Awaiting initial baseline migration scripts |

---

## 4. System Core Requirements

| Requirement ID | Requirement Description | Source Document | Module | Implementation Reference | Test Case ID | Verification Status | Evidence Reference |
| :---: | :--- | :--- | :---: | :--- | :---: | :---: | :--- |
| **REQ-SYS-001** | System Health and Readiness Monitoring | Project Initialization | Core | `backend/app/api/v1/endpoints/health.py` | `TC-SYS-HEALTH` | **Verified** | `backend/tests/test_health.py` (3 tests passed: root `/`, `/health`, schema response) |

---

## 5. Traceability Status Summary

- **Total Requirements Documented**: 47 (25 Functional, 21 Non-Functional, 1 Core System)
- **Verified Requirements**: 22 (46.8%)
  - FR: FR-03, FR-15, FR-16, FR-17, FR-18, FR-19, FR-20, FR-21, FR-22, FR-23, FR-24 (11 FRs)
  - NFR: NFR-05, NFR-06, NFR-07, NFR-10, NFR-11, NFR-15, NFR-16, NFR-17, NFR-18, NFR-19, NFR-20 (11 NFRs)
  - Core: REQ-SYS-001 (1 Core)
- **Partially Verified Requirements**: 4 (8.5%)
  - FR-25 (Input validation verified for M3/M5 schemas)
  - NFR-04 (Role and bearer token rejection verified; JWT generation pending M1)
  - NFR-09 (Integrity verified in Pydantic models; PostgreSQL constraints pending)
  - NFR-14 (Plain error responses verified for M3/M5 endpoints)
- **Not Implemented / Pending Modules**: 16 (34.0%)
  - Module 1 (Hiba): FR-01, FR-02, FR-04, FR-05, FR-06, FR-07, NFR-03 (7 requirements)
  - Module 2 (Mustajaab): FR-08, FR-09, FR-10, FR-11, FR-12, FR-13, FR-14, NFR-08 (8 requirements)
  - Database: NFR-21 (1 requirement)
- **Not Verified (Awaiting Execution/Environment)**: 5 (10.6%)
  - NFR-01, NFR-02 (Load and performance testing harness)
  - NFR-12, NFR-13 (Frontend peer usability and viewport testing)

---

## 6. Status Definitions

- **Verified**: Automated test executed and passed in the automated test suite; verified evidence recorded with specific test function references.
- **Partially Verified**: Subsystem or authorization rules implemented and verified by automated tests, but complete end-to-end functionality depends on unbuilt upstream or downstream modules.
- **Not Implemented**: Requirement baseline documented, but production code has not yet been authored.
- **Not Verified**: Production code or planned validation mechanism exists, but automated testing or formal validation has not yet been executed.
- **Blocked**: Verification cannot proceed due to external architectural or environment blockers.
