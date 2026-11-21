# Software Defect Log

> **Document Status**: Active Defect Tracking Baseline<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Standard Reference**: IEEE Std 1044 (Standard Classification for Software Anomalies)<br>
> **Current Active Defects**: **7 active defects (1 resolved)** *(Updated post Task COMMIT-02: DEF-AUTH-001 resolved)*

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
| **DEF-AUTH-002** | FINAL-03 Audit | Auth credentials lack cryptographic signing, HMAC/RSA validation, and expiry checks (simulated regex). | S1 - Critical | P1 - Immediate | `backend/app/core/auth.py:27-56` | Toqeer Ahmed | **OPEN** | CAPA-AUTH-002 | Awaiting Batch B fix |
| **DEF-AUTH-003** | FINAL-03 Audit | Missing backend user registration, login, and salted bcrypt password hashing endpoints. | S1 - Critical | P1 - Immediate | `backend/app/api/v1/api.py:18`<br>`backend/app/core/` | Toqeer / Hiba | **OPEN** | CAPA-AUTH-003 | Awaiting Batch B/D fix |
| **DEF-DATA-001** | FINAL-03 Audit | Repositories rely on volatile in-memory dicts; 100% data loss across restart; zero ACID transactions. | S2 - Major | P1 - Immediate | `backend/app/repositories/adaptive_repository.py`<br>`backend/app/repositories/progress_repository.py` | Toqeer Ahmed | **OPEN** | CAPA-DATA-001 | Awaiting Batch C fix |
| **DEF-MOD-001** | FINAL-03 Audit | Missing Module 1 (Hiba) and Module 2 (Mustajaab) backend implementations on `main` branch. | S1 - Critical | P1 - Immediate | `backend/app/api/v1/api.py:18-21` | Hiba / Mustajaab | **OPEN** | CAPA-MOD-001 | Awaiting Batch D merge |
| **DEF-ARCH-001** | FINAL-03 Audit | SE423 rubric requirement for Creational Pattern (Factory Method) unmet (only dictionary lookup exists). | S3 - Moderate | P2 - High | `backend/app/engine/recommendation_strategy.py:230-254` | Toqeer Ahmed | **OPEN** | CAPA-ARCH-001 | Awaiting Batch B fix |
| **DEF-FE-001** | FINAL-03 Audit | Frontend Assessment and Authentication views operate in simulated/preview mode with blocked backend endpoints. | S2 - Major | P2 - High | `frontend/src/components/AssessmentView.jsx`<br>`frontend/src/components/AuthView.jsx` | Toqeer Ahmed | **OPEN** | CAPA-FE-001 | Awaiting Batch A/D fix |
| **DEF-DOC-001** | FINAL-03 Audit | SQA documentation test count discrepancy: earlier documents cite 82 tests while execution reports cite 87 tests. | S3 - Moderate | P2 - High | `docs/sqa/requirements_traceability_matrix.md`<br>`docs/sqa/risk_register.md`<br>`docs/sqa/formal_inspection_report.md` | Toqeer Ahmed | **OPEN** | CAPA-DOC-001 | Awaiting Batch A fix |
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

#### Resolution & Verification
- **Status**: **OPEN**

---

### [DEF-AUTH-003]: Missing User Registration, Login, and Password Hashing Endpoints
- **Date Reported**: 2026-11-21
- **Reported By**: Toqeer Ahmed (Lead SQA Engineer)
- **Source**: FINAL-03 Critical Blocker Audit
- **Assigned To**: Toqeer Ahmed / Hiba Zulfiqar
- **Module Affected**: `backend/app/api/v1/api.py`, `backend/app/core/`
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

#### Resolution & Verification
- **Status**: **OPEN**

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

#### Resolution & Verification
- **Status**: **OPEN**

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
Modules 1 and 2 are absent from the Git repository.

#### Associated CAPA Reference
- `CAPA-MOD-001` (Batch D fast-track closure)

#### Resolution & Verification
- **Status**: **OPEN**

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

#### Resolution & Verification
- **Status**: **OPEN**

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

#### Associated CAPA Reference
- `CAPA-DOC-001` (Batch A fast-track closure)

#### Resolution & Verification
- **Status**: **OPEN**

---

## 4. Defect Metrics & Current Quality Summary

- **Total Defects Logged**: **8**
- **Open Defects**: **8**
- **Closed / Verified Defects**: **0**
- **Automated Regression Status**: **87 passed in 3.79s (100% pass rate)**
- **Static Analysis Status**: 0 errors, 0 warnings (Ruff, Oxlint, MyPy clean)
- **Inspection Dependency**: Formal Fagan package prepared (`docs/sqa/formal_inspection_report.md`); live meeting pending external faculty assignment.
