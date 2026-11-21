# AdaptLearn: Verified Pre-Fix Defect Baseline

> **Document Version**: 1.0.0  
> **Milestone**: Milestone 2 Release Candidate Corrective Baseline  
> **Course**: Software Quality Assurance (SE431) / Software Construction & Development (SE423)  
> **Standard Reference**: IEEE Std 1044 (Standard Classification for Software Anomalies) / IEEE Std 1012  
> **Lead Auditor**: Toqeer Ahmed (Lead Engine Architect & SQA Engineer, `u2023728@giki.edu.pk`)  
> **Date**: November 21, 2026  
> **Audit Baseline Commit**: `efeba33` (Working Tree Verification)

---

## 1. Executive Summary

This document establishes the official, verified **Pre-Fix Defect Baseline** for AdaptLearn prior to executing the fast-track corrective action batches defined in `docs/FINAL_03_BLOCKER_CLOSURE_PLAN.md`.

In strict adherence to `AGENTS.md` (Zero Fabrication Policy), this baseline records **only confirmed, physically verified anomalies** identified through direct source code inspection, test suite execution, and cross-module contract auditing. No artificial defects have been invented, and verified components (such as the pure Python adaptive engine algorithms, AST layer isolation, and static analysis cleanliness) are honestly reported as passing.

### Baseline Summary Metrics
- **Confirmed Active Defects**: **8 Defects**
  - **Critical (S1)**: 4 Defects (Token Format Mismatch, Unsigned Plaintext Tokens, Missing Registration/Login/Bcrypt, Missing M1/M2 Modules)
  - **Major (S2)**: 2 Defects (Ephemeral In-Memory Persistence, Simulated Frontend Assessment/Auth)
  - **Moderate (S3)**: 2 Defects (Unmet Creational Factory Method Rubric Requirement, SQA 82 vs. 87 Test Count Discrepancy)
  - **Minor (S4)**: 0 Defects
- **Automated Regression Baseline**: **87 passed automated tests** (100% pass rate in 3.79s)
- **Production Code Status**: Unmodified during baseline capture.

---

## 2. Confirmed Defect Summary Table (IEEE Std 1044)

| Defect ID | Description | Severity | Priority | Affected Requirement(s) | Affected File(s) | Status | Planned Fix Batch |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **DEF-AUTH-001** | Frontend preset token format mismatch (`dev-token-...` vs `token-...`) causing live HTTP 401 errors. | **S1 (Critical)** | **P1 (Immediate)** | NFR-04, NFR-14 | `frontend/src/context/presets.js`<br>`frontend/src/api/client.js`<br>`backend/app/core/auth.py` | **RESOLVED** | Batch A (COMMIT-02) |
| **DEF-AUTH-002** | Authentication credentials lack cryptographic signing, HMAC/RSA validation, and expiry checks. | **S1 (Critical)** | **P1 (Immediate)** | NFR-04, NFR-05 | `backend/app/core/security.py`<br>`backend/app/core/auth.py` | **RESOLVED** | Batch B (COMMIT-03) |
| **DEF-AUTH-003** | Missing user registration, login, and bcrypt password hashing backend endpoints. | **S1 (Critical)** | **P1 (Immediate)** | FR-01, FR-02, NFR-03 | `backend/app/api/v1/endpoints/auth.py`<br>`backend/app/core/security.py` | **RESOLVED** | Batch B (COMMIT-03) |
| **DEF-DATA-001** | Repositories rely on volatile in-memory dicts; 100% data loss across server restart; zero ACID transactions. | **S2 (Major)** | **P1 (Immediate)** | NFR-08, NFR-09 | `backend/app/repositories/adaptive_repository.py`<br>`backend/app/repositories/progress_repository.py` | **RESOLVED** | Batch C (COMMIT-04) |
| **DEF-MOD-001** | Missing Module 1 (Hiba) and Module 2 (Mustajaab) backend implementations on `main`. | **S1 (Critical)** | **P1 (Immediate)** | FR-01..FR-14 | `backend/app/api/v1/api.py` | **OPEN** | Batch D |
| **DEF-ARCH-001** | SE423 rubric requirement for Creational Design Pattern (Factory Method) is unmet (only dictionary lookup exists). | **S3 (Moderate)** | **P2 (High)** | SE423 Rubric | `backend/app/engine/recommendation_strategy.py` | **OPEN** | Batch B |
| **DEF-FE-001** | Frontend Assessment and Authentication views operate in simulated/preview mode with blocked backend endpoints. | **S2 (Major)** | **P2 (High)** | FR-01, FR-02, FR-08..FR-14 | `frontend/src/components/AssessmentView.jsx`<br>`frontend/src/components/AuthView.jsx` | **OPEN** | Batch A / Batch D |
| **DEF-DOC-001** | SQA documentation test count discrepancy: earlier documents cite 82 tests while execution reports cite 87 tests. | **S3 (Moderate)** | **P2 (High)** | IEEE Std 1012, SQA Rubric | `docs/sqa/requirements_traceability_matrix.md`<br>`docs/sqa/risk_register.md`<br>`docs/sqa/formal_inspection_report.md` | **OPEN** | Batch A |

---

## 3. Detailed Baseline Defect Records

### DEF-AUTH-001: Frontend/Backend Token Format Mismatch (Live HTTP 401 Error)
- **Defect ID**: `DEF-AUTH-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S1 - Critical** (Breaks live frontend-to-backend communication out-of-the-box)
- **Priority**: **P1 - Immediate**
- **Affected File(s)**:
  - `frontend/src/context/presets.js` (lines 7, 14, 21)
  - `backend/app/core/auth.py` (lines 24, 45-51)
- **Traceable Requirement**: NFR-04 (Token-based Session Authorization), NFR-14 (Reliability)
- **Trigger Condition & Evidence**:
  - `frontend/src/context/presets.js` defines default student token as `'dev-token-student-101'` and instructor token as `'dev-token-instructor-1'`.
  - `frontend/src/api/client.js` sends header: `Authorization: Bearer dev-token-student-101`.
  - `backend/app/core/auth.py` tests header against regex: `re.compile(r"^Bearer\s+token-(\d+)-(student|instructor)$", re.IGNORECASE)`.
  - Because `dev-token-...` does not match `token-...`, regex fails (`None`), triggering:
    ```json
    HTTP/1.1 401 Unauthorized
    {"detail": "Invalid authentication token format. Expected: Bearer token-<id>-<role>"}
    ```
- **Expected Behavior**: Default frontend presets must supply tokens matching the backend token format so views load live data.
- **Actual Behavior**: Live student dashboard and instructor analytics views fail to load data on initial application start.
- **Planned Corrective Action (Batch A)**: Align `frontend/src/context/presets.js` tokens to `token-101-student` and `token-1-instructor`.
- **Resolution Status**: **RESOLVED** (Task COMMIT-02)
- **Resolution Verification**: Aligned `frontend/src/context/presets.js` and `frontend/src/api/client.js` tokens to `token-<id>-<role>`. Added 18 regression unit and integration tests in `backend/tests/unit/test_auth.py` verifying student and instructor preset tokens authenticate, legacy `dev-token` format is rejected with HTTP 401, and protected endpoints respond 200 OK. 105 total backend tests passed. Frontend build and oxlint clean.

---

### DEF-AUTH-002: Authentication Lacks Cryptographic Signing and Expiry Validation
- **Defect ID**: `DEF-AUTH-002`
- **Date Verified**: 2026-11-21
- **Severity**: **S1 - Critical** (Security vulnerability; trivial identity and role spoofing)
- **Priority**: **P1 - Immediate**
- **Affected File(s)**:
  - `backend/app/core/auth.py` (lines 27-56)
- **Traceable Requirement**: NFR-04 ("Sessions shall use signed tokens with an expiry time; requests with a missing, invalid or expired token shall be rejected"), NFR-05 (Server-side Access Control)
- **Trigger Condition & Evidence**:
  - `get_current_user()` extracts user identity and role solely by parsing groups from a plaintext regex string:
    ```python
    user_id = int(match.group(1))
    role = match.group(2).lower()
    return CurrentUser(user_id=user_id, role=role)
    ```
  - Zero cryptographic signature verification (no HMAC-SHA256, no RSA, no PyJWT).
  - Zero expiration timestamp (`exp`) enforcement.
  - Any HTTP client can elevate privileges to instructor or impersonate any student by forging the header `Authorization: Bearer token-99-instructor`.
- **Expected Behavior**: Bearer tokens must be cryptographically signed JWTs containing user claims and expiration timestamps, validated against a server secret key.
- **Actual Behavior**: Authentication is purely simulated via string pattern matching.
- **Planned Corrective Action (Batch B)**: Implement PyJWT encoding and decoding with secret key in `config.py`, maintaining backward compatibility for developer tokens.
- **Resolution Status**: **RESOLVED** (Task COMMIT-03)
- **Resolution Verification**: Implemented standard HS256 JWT encoding/decoding with 60-minute expiration in `backend/app/core/security.py` and validated against user repository in `backend/app/core/auth.py`. 30 automated security tests pass in `backend/tests/unit/test_security_auth.py`.

---

### DEF-AUTH-003: Missing User Registration, Login, and Password Hashing
- **Defect ID**: `DEF-AUTH-003`
- **Date Verified**: 2026-11-21
- **Severity**: **S1 - Critical** (Core functional requirement unbuilt)
- **Priority**: **P1 - Immediate**
- **Affected File(s)**:
  - `backend/app/api/v1/api.py` (line 18)
  - `backend/app/core/` (absence of password hashing utilities)
- **Traceable Requirement**: FR-01 (User Registration), FR-02 (User Login/Logout), NFR-03 (Bcrypt/Argon2 Salted Password Storage)
- **Trigger Condition & Evidence**:
  - `backend/app/api/v1/api.py` has `# api_router.include_router(users.router...)` commented out.
  - No `POST /api/v1/auth/register` or `POST /api/v1/auth/login` endpoint exists in the backend.
  - No password hashing module (bcrypt/passlib) is installed or imported in the backend.
- **Expected Behavior**: Users can register with validated fields, passwords stored as salted bcrypt hashes, and log in to receive signed JWT tokens.
- **Actual Behavior**: Registration and login endpoints are completely missing from the backend.
- **Planned Corrective Action (Batch B / Batch D)**: Implement password hashing utilities and provide demo/real auth endpoints.
- **Resolution Status**: **RESOLVED** (Task COMMIT-03)
- **Resolution Verification**: Implemented bcrypt password hashing (12 rounds) in `app/core/security.py`, Decision D5 schema validation in `app/schemas/auth.py`, user persistence in `app/repositories/user_repository.py`, and endpoints in `app/api/v1/endpoints/auth.py` (`POST /register`, `POST /login`, `GET /me`). 30 security tests pass.

---

### DEF-DATA-001: Volatile In-Memory Storage & Total Data Loss Across Restart
- **Defect ID**: `DEF-DATA-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S2 - Major** (Data persistence and reliability defect)
- **Priority**: **P1 - Immediate**
- **Affected File(s)**:
  - `backend/app/repositories/adaptive_repository.py` (lines 20-28)
  - `backend/app/repositories/progress_repository.py` (lines 45-53)
- **Traceable Requirement**: NFR-08 (Atomic Transaction Reliability), NFR-09 (Referential Integrity), NFR-21 (Database Storage)
- **Trigger Condition & Evidence**:
  - Repositories store course adaptive settings, response histories, enrollments, attempts, and question statistics in Python in-memory dictionaries:
    ```python
    self._course_settings: dict[int, MasteryParameters] = {}
    self._student_responses: dict[tuple[int, int], list[ResponseRecord]] = {}
    self._attempts: dict[tuple[int, int], list[AttemptRecord]] = {}
    ```
  - Restarting Uvicorn clears all state. Any custom settings or recorded quiz attempts are permanently lost.
  - No SQL transactions (`commit`/`rollback`) exist; failure leaves state in undefined memory condition.
- **Expected Behavior**: Submitted attempts, settings, and progress records must persist across application restarts and execute in atomic transactions.
- **Actual Behavior**: Storage is 100% ephemeral and volatile in memory.
- **Planned Corrective Action (Batch C)**: Implement persistent SQLAlchemy ORM repository storage backed by SQLite for local development and testing, with PostgreSQL dialect compatibility.
- **Resolution Status**: **RESOLVED** (Task COMMIT-04)
- **Resolution Verification**: Implemented SQLAlchemy 2.0 ORM models in `backend/app/models/`, session management in `backend/app/db/session.py`, and refactored `AdaptiveRepository`, `ProgressRepository`, and `UserRepository` to execute atomic transactional database operations. Verified across 9 restart-survival and persistence tests in `backend/tests/unit/test_persistence.py`. 144 total backend tests pass.

---

### DEF-MOD-001: Missing Teammate Modules M1 and M2 on Main Branch
- **Defect ID**: `DEF-MOD-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S1 - Critical** (Platform integration gap)
- **Priority**: **P1 - Immediate**
- **Affected File(s)**:
  - `backend/app/api/v1/api.py` (lines 18-21)
  - `backend/app/models/` (empty `__init__.py`)
- **Traceable Requirement**: FR-01..FR-07 (Module 1 - Hiba), FR-08..FR-14 (Module 2 - Mustajaab)
- **Trigger Condition & Evidence**:
  - `git branch -a` shows only `main` and `remotes/origin/main`.
  - Neither Hiba nor Mustajaab has committed or pushed code to the repository.
  - Routers for `users`, `courses`, `quizzes`, and `learning_paths` remain commented-out placeholders in `api.py`.
- **Expected Behavior**: Full multi-module integration across M1, M2, M3, M4, and M5 on `main`.
- **Actual Behavior**: Modules 1 and 2 are absent from the Git tree.
- **Planned Corrective Action (Batch D)**: Coordinate with Hiba and Mustajaab to push feature branches and merge into `main`.

---

### DEF-ARCH-001: Absence of Creational Design Pattern (Factory Method)
- **Defect ID**: `DEF-ARCH-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S3 - Moderate** (Rubric compliance gap)
- **Priority**: **P2 - High**
- **Affected File(s)**:
  - `backend/app/engine/recommendation_strategy.py` (lines 230-254)
  - `docs/decisions.md` (CR-01)
- **Traceable Requirement**: SE423 Rubric ($\ge 3$ design patterns including $\ge 1$ creational pattern)
- **Trigger Condition & Evidence**:
  - Codebase contains Strategy pattern (`RecommendationStrategy`) and Repository pattern (`AdaptiveRepository`), but creational instantiation is handled solely by a flat dictionary lookup helper `get_recommendation_strategy()`.
  - No formal GoF Factory Method hierarchy (abstract `Creator` with abstract `factory_method()`, concrete `Creators`) exists.
  - CR-01 proposed Factory Method, but remains in `Proposed` status.
- **Expected Behavior**: A formal GoF Creational Design Pattern implemented in code to satisfy the rubric.
- **Actual Behavior**: Creational pattern requirement is unmet.
- **Planned Corrective Action (Batch B)**: Implement formal `RecommendationStrategyFactory` and `RecommendationStrategyCreator` classes.

---

### DEF-FE-001: Frontend Assessment and Auth Views in Simulated/Blocked Mode
- **Defect ID**: `DEF-FE-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S2 - Major** (User experience and demo completeness)
- **Priority**: **P2 - High**
- **Affected File(s)**:
  - `frontend/src/components/AssessmentView.jsx` (lines 3-45)
  - `frontend/src/components/AuthView.jsx` (lines 48-54)
- **Traceable Requirement**: FR-01, FR-02, FR-08..FR-14
- **Trigger Condition & Evidence**:
  - `AuthView.jsx` validates forms on the client but displays feedback: *"Backend POST /api/v1/auth/register is currently BLOCKED pending Module 1 delivery by Hiba."*
  - `AssessmentView.jsx` presents static preview questions and displays feedback: *"Question authoring UI is ready. Backend POST /api/v1/quizzes/{id}/questions is BLOCKED pending Module 2 delivery by Mustajaab."*
- **Expected Behavior**: Interactive assessment taking and authentication forms connect to live backend endpoints.
- **Actual Behavior**: Both views operate in simulated preview mode.
- **Planned Corrective Action (Batch A / Batch D)**: Provide demo submission endpoints and integrate M1/M2 when landed.

---

### DEF-DOC-001: SQA Documentation Test Count Discrepancy (82 vs. 87 Tests)
- **Defect ID**: `DEF-DOC-001`
- **Date Verified**: 2026-11-21
- **Severity**: **S3 - Moderate** (Document consistency defect)
- **Priority**: **P2 - High**
- **Affected File(s)**:
  - `docs/sqa/requirements_traceability_matrix.md` (line 7, section 5)
  - `docs/sqa/risk_register.md` (line 7)
  - `docs/sqa/formal_inspection_report.md` (line 64)
  - `docs/sqa/defect_log.md` (line 7, line 85)
- **Traceable Requirement**: IEEE Std 1012 (Verification & Traceability Consistency)
- **Trigger Condition & Evidence**:
  - Documents authored during SQA-01..04 record an **82-test cutoff**.
  - Task INT-01 added 5 cross-module integration tests in `test_cross_module_integration.py`, bringing the actual suite to **87 tests**.
  - `test_execution_report.md`, `FINAL_M2_AUDIT.md`, and `M2_SUBMISSION_PACKAGE.md` record **87 tests**, creating an internal document contradiction.
- **Expected Behavior**: All quality documents cite the identical, accurate automated test count.
- **Actual Behavior**: Earlier SQA documents report 82 tests, out of sync with actual 87 tests.
- **Planned Corrective Action (Batch A)**: Synchronize test count to 87 across all SQA documentation.

---

## 4. Unconfirmed / Non-Defect Items (Verified Clean)

To prevent false defect logging, the following components were audited and confirmed **not defective**:
1. **Mathematical Accuracy of Adaptive Engine**: `MasteryCalculator` and `MasteryPolicy` formulas strictly match M1 Section 9.2 specifications. All 28 unit tests pass without errors.
2. **Pure Engine Isolation (NFR-05)**: The AST architecture scanner (`test_layers.py`) confirms that `backend/app/engine/` contains zero prohibited framework imports (`FastAPI`, `SQLAlchemy`, `Pydantic`).
3. **Static Analysis Compliance (NFR-16)**: Ruff (Python style and bugbear), MyPy (strict type checking across 31 source files), and Oxlint (15 frontend files) pass with **0 errors and 0 warnings**.
4. **Authorization Logic (NFR-06)**: When given appropriate role tokens, route handlers strictly enforce multi-tenant student privacy (403 Forbidden for cross-student access) and course ownership (403 Forbidden for cross-instructor access).

---

## 5. Baseline Test Execution Evidence

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.2.0, pluggy-1.7.0 -- D:\Study Material\Seven Semester\Software Quality Assurance SE431\Project\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Study Material\Seven Semester\Software Quality Assurance SE431\Project\backend
configfile: pyproject.toml
plugins: anyio-4.16.0
collecting ... collected 87 items

backend\tests\architecture\test_layers.py ...........                    [ 12%]
backend\tests\integration\test_adaptive_api.py .......                   [ 20%]
backend\tests\integration\test_cross_module_integration.py .....         [ 26%]
backend\tests\integration\test_instructor_analytics_api.py ......        [ 33%]
backend\tests\integration\test_progress_api.py ......                    [ 40%]
backend\tests\test_health.py ...                                         [ 43%]
backend\tests\unit\test_analytics_service.py ....                        [ 48%]
backend\tests\unit\test_mastery_calculator.py ................           [ 66%]
backend\tests\unit\test_mastery_policy.py ............                   [ 80%]
backend\tests\unit\test_progress_service.py .....                        [ 86%]
backend\tests\unit\test_recommendation_strategy.py ............          [100%]

======================= 87 passed, 2 warnings in 3.79s ========================
```

---
*Baseline Defect Document certified by Toqeer Ahmed (Lead Engine Architect & SQA Engineer).*
