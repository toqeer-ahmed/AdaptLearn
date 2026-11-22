# Software Defect Log

> **Document Status**: Active Defect Tracking Baseline<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Standard Reference**: IEEE Std 1044 (Standard Classification for Software Anomalies)<br>
> **Current Active Defects**: **2 active defects (7 resolved)** *(Updated post Task HOTFIX-01: DEF-AUTH-001, DEF-AUTH-002, DEF-AUTH-003, DEF-DATA-001, DEF-ARCH-001, DEF-DOC-001, DEF-CI-001 resolved)*

---

## 1. Severity & Priority Classifications

In accordance with IEEE Std 1044, defects are categorized by technical impact (severity) and urgency of resolution (priority):

### Severity (Technical Impact)
- **Critical (S1)**: Complete system crash, calculation corruption, security/privacy breach (NFR-06), or violation of pure engine architecture isolation (NFR-05).
- **Major (S2)**: Primary functional requirement failing (e.g., incorrect mastery recalculation, prerequisite ordering inverted) with no workaround.
- **Moderate (S3)**: Secondary functionality impaired or unexpected behavior with a documented temporary workaround.
- **Minor (S4)**: Cosmetic discrepancy, documentation typo, or non-functional convention defect.

### Priority (Resolution Urgency)
- **P1 (Immediate)**: Blocker; must be fixed immediately prior to any merge or deployment.
- **P2 (High)**: Must be resolved within current milestone sprint before sign-off.
- **P3 (Normal)**: Scheduled for resolution during regular development cycle.
- **P4 (Low)**: Deferred to future maintenance sprint.

---

## 2. Defect Log Records

| Defect ID | Source & Finding Ref | Description | Severity | Priority | Affected File & Line | Assigned Owner | Resolution Status | CAPA Ref | Retest Evidence |
| :---: | :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :--- |
| **DEF-AUTH-001** | FINAL-03 Audit | Frontend/backend token format mismatch (`dev-token-...` vs `token-...`) causing live HTTP 401 errors. | S1 - Critical | P1 - Immediate | `frontend/src/context/presets.js`<br>`frontend/src/api/client.js`<br>`backend/app/core/auth.py:24` | Toqeer Ahmed | **RESOLVED** | CAPA-AUTH-001 | Verified by `backend/tests/unit/test_auth.py` (18/18 passed) |
| **DEF-AUTH-002** | FINAL-03 Audit | Auth credentials lack cryptographic signing, HMAC/RSA validation, and expiry checks (simulated regex). | S1 - Critical | P1 - Immediate | `backend/app/core/security.py`<br>`backend/app/core/auth.py` | Toqeer Ahmed | **RESOLVED** | CAPA-AUTH-002 | Verified by `backend/tests/unit/test_security_auth.py` (30/30 passed) |
| **DEF-AUTH-003** | FINAL-03 Audit | Missing backend user registration, login, and salted bcrypt password hashing endpoints. | S1 - Critical | P1 - Immediate | `backend/app/api/v1/endpoints/auth.py`<br>`backend/app/core/security.py` | Toqeer / Hiba | **RESOLVED** | CAPA-AUTH-003 | Verified by `backend/tests/unit/test_security_auth.py` (30/30 passed) |
| **DEF-DATA-001** | FINAL-03 Audit | Repositories rely on volatile in-memory dicts; 100% data loss across restart; zero ACID transactions. | S2 - Major | P1 - Immediate | `backend/app/repositories/adaptive_repository.py`<br>`backend/app/repositories/progress_repository.py` | Toqeer Ahmed | **RESOLVED** | CAPA-DATA-001 | Verified by `backend/tests/unit/test_persistence.py` (9/9 passed) |
| **DEF-MOD-001** | FINAL-03 Audit | Missing Module 1 (Hiba) and Module 2 (Mustajaab) backend implementations on `main` branch. | S1 - Critical | P1 - Immediate | `backend/app/api/v1/api.py:18-21` | Hiba / Mustajaab | **PARTIALLY RESOLVED** | CAPA-MOD-001 | Module 2 100% verified on `feature/m2-quiz-engine` (56/56 tests passing); awaiting Module 1 & `main` merge |
| **DEF-ARCH-001** | FINAL-03 Audit | SE423 rubric requirement for Creational Pattern (Factory Method) unmet (only dictionary lookup exists). | S3 - Moderate | P2 - High | `backend/app/engine/recommendation_strategy.py`<br>`backend/app/services/adaptive_service.py` | Toqeer Ahmed | **RESOLVED** | CAPA-ARCH-001 | Verified by `backend/tests/unit/test_recommendation_strategy.py` (18/18 passed) |
| **DEF-FE-001** | FINAL-03 Audit | Frontend Assessment and Authentication views operate in simulated/preview mode with blocked backend endpoints. | S2 - Major | P2 - High | `frontend/src/components/AssessmentView.jsx`<br>`frontend/src/components/AuthView.jsx` | Toqeer Ahmed | **OPEN** | CAPA-FE-001 | Awaiting Batch A/D fix |
| **DEF-DOC-001** | FINAL-03 Audit | SQA documentation test count discrepancy: earlier documents cite 82/87 tests instead of 150. | S3 - Moderate | P2 - High | `docs/sqa/requirements_traceability_matrix.md`<br>`docs/sqa/risk_register.md`<br>`docs/sqa/formal_inspection_report.md`<br>`docs/sqa/test_execution_report.md` | Toqeer Ahmed | **RESOLVED** | CAPA-DOC-001 | Verified in Task COMMIT-07 across all 14 test modules (150/150 passed) |
| **DEF-CI-001** | GitHub Actions CI | Missing tracked backend schema, service, endpoint, and test files in Git causing CI test collection crash (`ModuleNotFoundError: No module named 'app.schemas.adaptive'`). | S1 - Critical | P1 - Immediate | `backend/app/schemas/adaptive.py`<br>`backend/app/services/__init__.py` | Toqeer Ahmed | **RESOLVED** | CAPA-CI-001 | Verified by clean-checkout simulation passing all 150 tests |
| *[DEF-FND-001]* | FND-001 | *[Pending live Fagan inspection meeting with external faculty evaluator]* | S1/S2/S3/S4 | P1/P2/P3/P4 | `backend/app/engine/...` | Assignee | *Pending* | CAPA-001 | Awaiting inspection |

---

## 3. Detailed Defect Records (IEEE 1044 Compliant)

### [DEF-AUTH-001]: Frontend/Backend Token Format Mismatch (Live HTTP 401 Error)
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `frontend/src/context/presets.js`, `frontend/src/api/client.js`, `backend/app/core/auth.py`
- **Severity**: S1 - Critical
- **Priority**: P1 - Immediate
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
The frontend presets in `frontend/src/context/presets.js` define preset tokens as `dev-token-student-101` and `dev-token-instructor-1`. The backend in `backend/app/core/auth.py` matches tokens against `re.compile(r"^Bearer\s+token-(\d+)-(student|instructor)$", re.I)`. When the frontend makes an API call, regex matching fails and returns HTTP 401 Unauthorized with `"Invalid authentication token format. Expected: Bearer token-<id>-<role>"`.

#### Requirement Violation
- NFR-04 (Token-based Session Authorization), NFR-14 (Reliability)

#### Expected Result
Default frontend personas should authenticate cleanly against the backend and render live dashboard data.

#### Actual Result
Live student dashboard and instructor analytics fail to load on clean startup due to HTTP 401 rejection.

#### Associated CAPA Reference
- `CAPA-AUTH-001` (Batch A fast-track closure)

#### Corrective Action Taken
1. **Frontend Alignment**:
   - Updated `frontend/src/context/presets.js` to define tokens strictly adhering to `token-<id>-<role>`:
     - `student` (ID: 101) $\rightarrow$ `token-101-student`
     - `instructor` (ID: 1) $\rightarrow$ `token-1-instructor`
     - `nonOwnerInstructor` (ID: 2) $\rightarrow$ `token-2-instructor`
   - Updated fallback authorization token in `frontend/src/api/client.js` from `'dev-token-student-101'` to `'token-101-student'`.
2. **Regression Test Suite**:
   - Created `backend/tests/unit/test_auth.py` with 18 unit and integration test cases covering:
     - Student preset credential authentication.
     - Instructor and non-owner instructor preset authentication.
     - Case insensitivity and whitespace handling.
     - Rejection of legacy mismatch token format (`dev-token-...`) with HTTP 401.
     - Rejection of missing/empty Authorization header with HTTP 401.
     - Rejection of malformed tokens and unauthorized roles with HTTP 401.
     - End-to-end authorized API requests against protected endpoints (`/api/v1/courses/{id}/progress` and `/api/v1/courses/{id}/analytics/mastery-distribution`).

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: All 18 regression tests in `backend/tests/unit/test_auth.py` passed; full backend suite of 105 tests passed in 1.10s. Frontend `vite build` completed cleanly; `oxlint` reported 0 errors and 0 warnings.

---

### [DEF-AUTH-002]: Authentication Lacks Cryptographic Signing and Expiry Validation
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `backend/app/core/auth.py`
- **Severity**: S1 - Critical
- **Priority**: P1 - Immediate
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
`get_current_user` extracts `user_id` and `role` purely from regex capture groups from an unhashed plaintext bearer string. There is zero cryptographic signature validation, no secret key verification, and no expiration timestamp enforcement. Any client can forge any role or identity by modifying the authorization header.

#### Requirement Violation
- NFR-04 (Signed tokens with expiry time), NFR-05 (Server-side access control)

#### Expected Result
Tokens must be cryptographically signed JSON Web Tokens (JWT) verified against a secure secret key.

#### Actual Result
Tokens are simulated via plaintext string regex matching without cryptographic validity.

#### Associated CAPA Reference
- `CAPA-AUTH-002` (Batch B fast-track closure)

#### Corrective Action Taken
1. **Cryptographic JWT Implementation**:
   - Implemented standard JWT encoding and decoding in `backend/app/core/security.py` using `pyjwt` (HS256 algorithm) with mandatory 60-minute expiration.
   - Configured `JWT_SECRET_KEY` in `backend/app/core/config.py` using a secure 256-bit key.
2. **Server-Side Token Verification & Spoofing Prevention**:
   - Refactored `get_current_user` in `backend/app/core/auth.py` to validate JWT signatures, expiry timestamps, and required claims (`sub`, `role`, `exp`, `iat`).
   - Validates user identity and role against `UserRepository` to prevent user ID and role claim spoofing.
   - Guarded development fallback behind `settings.ALLOW_DEV_TOKENS=False` in production.

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: Verified by `backend/tests/unit/test_security_auth.py` (30/30 passed). Demonstrates rejection of invalid signatures, expired tokens, missing claims, malformed strings, and user/role spoofing.

---

### [DEF-AUTH-003]: Missing User Registration, Login, and Password Hashing Endpoints
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed / Hiba Zulfiqar
- **Module Affected**: `backend/app/api/v1/endpoints/auth.py`, `backend/app/services/auth_service.py`, `backend/app/repositories/user_repository.py`, `backend/app/core/security.py`
- **Severity**: S1 - Critical
- **Priority**: P1 - Immediate
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
No registration (`POST /api/v1/auth/register`) or login (`POST /api/v1/auth/login`) routes exist in the backend. `backend/app/api/v1/api.py` has the user/auth router mounts commented out. Passwords are never hashed using bcrypt or Argon2.

#### Requirement Violation
- FR-01 (User Registration), FR-02 (User Login/Logout), NFR-03 (Bcrypt/Argon2 Salted Hashes)

#### Expected Result
Backend provides registration and login endpoints that hash passwords using bcrypt and return signed session tokens.

#### Actual Result
Backend has zero authentication endpoints implemented.

#### Associated CAPA Reference
- `CAPA-AUTH-003` (Batch B / Batch D fast-track closure)

#### Corrective Action Taken
1. **Password Hashing (NFR-03, Decision D5)**:
   - Implemented `hash_password` and `verify_password` in `backend/app/core/security.py` using `bcrypt` with 12 rounds of salt.
   - Enforced 8 to 72 character bounds per Decision D5; passwords never logged or returned in responses.
2. **User Persistence**:
   - Created `backend/app/repositories/user_repository.py` managing `UserRecord` entities and seeding default personas.
3. **Authentication Business Logic & Endpoints**:
   - Created `backend/app/schemas/auth.py` with strict Pydantic v2 validation.
   - Created `backend/app/services/auth_service.py` with duplicate email rejection (HTTP 409) and generic login failure handling (HTTP 401).
   - Created `backend/app/api/v1/endpoints/auth.py` exposing `POST /register`, `POST /login`, and `GET /me`.
   - Mounted auth router on `/api/v1/auth` in `backend/app/api/v1/api.py`.

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: Verified by 30 security tests in `backend/tests/unit/test_security_auth.py` and 135 total backend tests passing. Endpoint contracts documented in `docs/api.md`.

---

### [DEF-DATA-001]: Volatile In-Memory Repositories & Total Data Loss Across Restart
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `backend/app/repositories/adaptive_repository.py`, `backend/app/repositories/progress_repository.py`
- **Severity**: S2 - Major
- **Priority**: P1 - Immediate
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
All application entities (course settings, attempts, question stats, student responses) reside in Python dictionary structures (`self._course_settings`, `self._attempts`). Restarting Uvicorn clears all state. No ACID transactions (`commit`/`rollback`) or row locks exist.

#### Requirement Violation
- NFR-08 (Single Transaction Attempt Submission), NFR-09 (Referential Integrity), NFR-21 (Persistence)

#### Expected Result
Submitted quiz attempts, student progress records, and course settings must persist across server restarts.

#### Actual Result
All data is lost upon server reload or restart.

#### Associated CAPA Reference
- `CAPA-DATA-001` (Batch C fast-track closure)

#### Corrective Action Taken
1. **SQLAlchemy 2.0 ORM Integration**:
   - Added `sqlalchemy>=2.0.0,<3.0.0` dependency to `backend/requirements.txt`.
   - Created `backend/app/db/base.py` (`DeclarativeBase`) and `backend/app/db/session.py` providing dialect-agnostic engine creation, session factory (`SessionLocal`), and `init_db()` startup hook.
2. **Declarative Persistence Models**:
   - Created `backend/app/models/adaptive.py` (`CourseSettingsModel`, `StudentTopicResponseModel`, `CourseTopicModel`).
   - Created `backend/app/models/progress.py` (`EnrollmentModel`, `CourseOwnerModel`, `AttemptModel`, `QuestionStatsModel`).
   - Created `backend/app/models/user.py` (`UserModel`).
   - Registered all models with `Base.metadata` in `backend/app/models/__init__.py`.
3. **Persistent Transactional Repositories**:
   - Refactored `AdaptiveRepository`, `ProgressRepository`, and `UserRepository` to execute queries and transactional commits/rollbacks via SQLAlchemy sessions.
   - Maintained 100% backward compatibility for all public method signatures, domain dataclass return types (`MasteryParameters`, `ResponseRecord`, `TopicRecommendationInput`, `AttemptRecord`, `QuestionStatsRecord`), and caller contracts.
   - Seeded default personas (`student@adaptlearn.edu`, `instructor@adaptlearn.edu`) upon database initialization.
4. **App Startup Hook**:
   - Updated `backend/app/main.py` lifespan handler to invoke `init_db()` ensuring all tables exist before serving HTTP traffic.
5. **Restart Survival & Concurrency Tests**:
   - Authored comprehensive test suite in `backend/tests/unit/test_persistence.py` demonstrating data persistence across repository instance destruction and recreation against physical SQLite database files.

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: All 9 persistence tests in `backend/tests/unit/test_persistence.py` passed; 144 total backend tests passing. State reload verified on disk with zero data loss.

---

### [DEF-MOD-001]: Missing Teammate Modules M1 and M2 on Main Branch
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Hiba Zulfiqar / Mustajaab Ul Fida Qadri
- **Module Affected**: `backend/app/api/v1/api.py`, `backend/app/models/`
- **Severity**: S1 - Critical
- **Priority**: P1 - Immediate
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
Neither Hiba (M1/M4) nor Mustajaab (M2) has pushed code to the repository. The router mounts in `api.py` are commented out, and database models in `app/models/` are empty docstrings.

#### Requirement Violation
- FR-01 through FR-14 (User Management, Course Management, Question Authoring, Quiz Taking)

#### Expected Result
Integrated multi-module backend with M1, M2, M3, M4, and M5 active on `main`.

#### Actual Result
Module 1 is absent from the Git repository. Module 2 was initially absent from `main`.

#### Associated CAPA Reference
- `CAPA-MOD-001` (Batch D fast-track closure)

#### Corrective Action Taken (Module 2 — Mustajaab Ul Fida Qadri)
1. **Relational Models (`backend/app/models/quiz.py`)**:
   - Implemented `QuestionModel`, `QuizModel`, `QuizQuestionModel`, and `AttemptAnswerModel` registered with `Base.metadata`.
2. **Persistent Repository (`backend/app/repositories/quiz_repository.py`)**:
   - Implemented question CRUD, soft-delete check (`AttemptAnswerModel` check), ordered quiz assembly, and active practice question filtering.
3. **Pydantic v2 Schemas (`backend/app/schemas/quiz.py`)**:
   - Implemented strict input validation and student-safe response projection stripping answers and explanations prior to submission.
4. **Service & Atomic Transaction (`backend/app/services/quiz_service.py`)**:
   - Implemented question authoring, quiz lifecycle, and single atomic database transaction persisting attempt summary, attempt answers, question performance stats (FR-24), and adaptive topic responses (FR-16).
5. **REST API Endpoints (`backend/app/api/v1/endpoints/quizzes.py`)**:
   - Exposed all quiz management, practice generation, and taking/scoring endpoints with RBAC enforcement.
6. **Automated Verification Suite (56 Automated Tests)**:
   - `backend/tests/unit/test_quiz_repository.py` (9 passed)
   - `backend/tests/unit/test_quiz_schemas.py` (18 passed)
   - `backend/tests/unit/test_quiz_service.py` (14 passed)
   - `backend/tests/unit/test_quiz_scoring.py` (11 passed, white-box basis path testing)
   - `backend/tests/integration/test_quiz_api.py` (4 passed)

#### Resolution & Verification
- **Status**: **PARTIALLY RESOLVED** (Module 2 100% verified on `feature/m2-quiz-engine`; Module 1 pending)
- **Verified Date**: 2026-11-21
- **Verification Evidence**: All 56 Module 2 tests passing in 8.5s; 83/83 total regression tests passing. Zero regressions across existing persistence and recommendation strategy suites.

---

### [DEF-ARCH-001]: Absence of Creational Design Pattern (Factory Method)
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `backend/app/engine/recommendation_strategy.py`
- **Severity**: S3 - Moderate
- **Priority**: P2 - High
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
The SE423 rubric requires at least 3 design patterns, including at least one creational pattern. Currently, only the Strategy pattern (`RecommendationStrategy`) and Repository pattern exist. Instantiation is handled by a simple dictionary lookup helper rather than a formal GoF Factory Method hierarchy.

#### Requirement Violation
- SE423 Course Rubric (Design Pattern Requirements)

#### Expected Result
Formal GoF Factory Method pattern implemented with abstract creator and concrete creator classes.

#### Actual Result
Only a flat dictionary lookup helper `get_recommendation_strategy()` exists.

#### Associated CAPA Reference
- `CAPA-ARCH-001` (Batch B fast-track closure)

#### Corrective Action Taken
1. **Abstract Creator Abstraction**:
   - Created `RecommendationStrategyCreator(ABC)` in `backend/app/engine/recommendation_strategy.py` declaring the abstract factory method `create_strategy() -> RecommendationStrategy` and template method `recommend()`.
2. **Concrete Creator**:
   - Created `RuleBasedStrategyCreator(RecommendationStrategyCreator)` in `backend/app/engine/recommendation_strategy.py` overriding `create_strategy()` to instantiate `RuleBasedRecommendationStrategy`.
3. **Creator Registry & Dependency Inversion**:
   - Implemented `STRATEGY_CREATORS` registry and `get_strategy_creator()` resolver.
   - Refactored `AdaptiveService` in `backend/app/services/adaptive_service.py` to depend on `RecommendationStrategyCreator` abstraction.
4. **Unit & Architecture Testing**:
   - Authored unit test suite in `backend/tests/unit/test_recommendation_strategy.py` (`TestFactoryMethodPattern`) covering instantiation guards, polymorphic creators, creator delegation, and registry resolution.

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: Verified by 18 unit tests in `backend/tests/unit/test_recommendation_strategy.py` (all passed in 0.06s) and 150 total backend tests. AST layer scanner confirmed zero forbidden imports in `app/engine/`.

---

### [DEF-FE-001]: Frontend Assessment and Auth Views in Simulated/Blocked Mode
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `frontend/src/components/AssessmentView.jsx`, `frontend/src/components/AuthView.jsx`
- **Severity**: S2 - Major
- **Priority**: P2 - High
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
`AuthView.jsx` validates registration/login on the client but reports that backend endpoints are BLOCKED. `AssessmentView.jsx` displays static preview questions and blocks question authoring submission.

#### Requirement Violation
- FR-01, FR-02, FR-08..FR-14

#### Expected Result
Frontend views connect to live functional backend APIs.

#### Actual Result
Views operate in preview/blocked simulation mode.

#### Associated CAPA Reference
- `CAPA-FE-001` (Batch A / Batch D fast-track closure)

#### Resolution & Verification
- **Status**: **OPEN**

---

### [DEF-DOC-001]: SQA Documentation Test Count Discrepancy (82 vs. 87 Tests)
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed
- **Module Affected**: `docs/sqa/requirements_traceability_matrix.md`, `risk_register.md`, `formal_inspection_report.md`
- **Severity**: S3 - Moderate
- **Priority**: P2 - High
- **Target Baseline Commit**: `efeba33`

#### Description & Trigger Condition
Documents authored during SQA-01..04 state an 82-test evidence baseline. Task INT-01 added 5 cross-module integration tests, bringing the verified suite to 87 tests. Later documents cite 87 tests, creating an internal documentation inconsistency.

#### Requirement Violation
- IEEE Std 1012 (Verification & Traceability Consistency)

#### Expected Result
All quality documents cite the identical, accurate automated test count (87 passed tests).

#### Actual Result
Earlier SQA documents report 82 tests, out of sync with actual 87 tests.

#### Corrective Action Taken
1. Executed full automated regression suite verifying exact test distribution across 14 test modules (150 tests total).
2. Updated all upstream and downstream SQA documentation (`requirements_traceability_matrix.md`, `test_execution_report.md`, `verification_validation_plan.md`, `risk_register.md`, `formal_inspection_report.md`) to cite the verified 150-test evidence baseline.
3. Aligned RTM status and test execution reports with verified post-fix implementation artifacts.

#### Resolution & Verification
- **Status**: **RESOLVED**
- **Verified Date**: 2026-11-21
- **Verification Evidence**: All SQA documents synchronized to cite 150 automated passing tests; verified by Pytest run (`150 passed in 35.39s`).

---

## 4. Defect Metrics & Current Quality Summary

- **Total Baseline Defects Logged**: **8**
- **Open Defects**: **2** (`DEF-MOD-001` missing teammate modules, `DEF-FE-001` frontend quiz view blocked)
- **Closed / Verified Defects**: **6** (`DEF-AUTH-001`, `DEF-AUTH-002`, `DEF-AUTH-003`, `DEF-DATA-001`, `DEF-ARCH-001`, `DEF-DOC-001`)
- **Pending External Inspection**: **1** (`DEF-FND-001` awaiting live Fagan meeting)
- **Automated Regression Status**: **150 passed in 35.39s (100% pass rate across 14 test modules)**
- **Static Analysis Status**: 0 errors, 0 warnings (Ruff check clean, Oxlint clean across 15 files)
- **Inspection Dependency**: Formal Fagan package prepared (`docs/sqa/formal_inspection_report.md`); live meeting pending external faculty assignment.
