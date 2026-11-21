# Verification and Validation (V&V) Plan

> **Document Status**: Active / Reconciled Quality Baseline (Post Commits 2–6)<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Standard Reference**: IEEE Std 1012 (Standard for System, Software, and Hardware Verification and Validation)<br>
> **Current Evidence Baseline**: 150 Automated Backend Tests Executed & Passed

---

## 1. Objectives & Quality Philosophy

The primary objective of the AdaptLearn Verification and Validation (V&V) Plan is to establish a rigorous, repeatable quality assurance regime spanning all project milestones.

- **Verification ("Are we building the product right?")**: Ensures that each software artifact (requirements baseline, architectural layers, domain algorithms, API schemas, and test suites) strictly adheres to upstream specifications, architectural isolation rules (NFR-05), and coding standards.
- **Validation ("Are we building the right product?")**: Confirms that the integrated application fulfills educational needs, satisfies student learning progression and instructor analytics workflows, and satisfies the SE431 course evaluation criteria.

---

## 2. System Architecture & Scope

AdaptLearn follows a strict layered architecture with an isolated core domain:

```
[ HTTP Clients / Frontend UI ]
              │
              ▼
    [ API Routers (FastAPI) ]            <-- app/api/v1/endpoints/
              │
              ▼
   [ Application Services ]              <-- app/services/
        │              │
        ▼              ▼
[ Repositories ]   [ Adaptive Engine ]    <-- app/engine/ (Pure Python, Zero Frameworks)
        │
        ▼
   [ Database ]                          <-- SQLAlchemy / PostgreSQL
```

### Module Scope & Implementation Status

| Module | Scope & Core Responsibility | Owner | Current Implementation Status | Test Coverage Reference |
| :--- | :--- | :---: | :---: | :--- |
| **Core Infrastructure** | Configuration, health check, CORS, error handling. | Core Lead | Implemented | `backend/tests/test_health.py` (3 tests) |
| **Module 1 (M1)** | User registration, authentication, RBAC, course management. | Hiba | Not Implemented (Pending) | Auth guards stubbed for M3/M5 testing |
| **Module 2 (M2)** | Question bank, dynamic quizzes, grading, attempt submission. | Mustajaab | Not Implemented (Pending) | Attempt repository doubles created |
| **Module 3 (M3)** | Mastery calculation, policy classification, parameter settings. | Toqeer | **Completed & Verified** | Unit & Integration suites (44 tests) |
| **Module 4 (M4)** | Recommendation strategy, prerequisite constraints, rationales. | Toqeer / Hiba | **Completed & Verified** | Unit & Integration suites (15 tests) |
| **Module 5 (M5)** | Student dashboard, progress history, instructor analytics. | Toqeer | **Completed & Verified** | Unit & Integration suites (21 tests) |

---

## 3. Verification Levels & Structure

Testing is organized into distinct levels to isolate algorithmic defects, architectural violations, and integration regressions:

### Level 1: Pure Domain Unit Testing
- **Location**: `backend/tests/unit/`
- **Target**: Pure Python algorithms and isolated service business logic without external dependencies.
- **Executed Suites**:
  - `test_mastery_policy.py` (12 tests): Boundary values for Weak ($<0.50$), Developing ($[0.50, 0.79]$), Proficient ($\ge 0.80$), and Not Assessed ($< \text{min\_responses}$).
  - `test_mastery_calculator.py` (16 tests): Difficulty-weighted calculation ($\text{Easy}=1.0, \text{Medium}=1.5, \text{Hard}=2.0$), sliding window ($N=5$), parameter configurability (FR-20), and deterministic output.
  - `test_recommendation_strategy.py` (12 tests): Strategy pattern implementation, Weak before Developing prioritization, prerequisite satisfaction checking, and deterministic alphabetical tie-breaking.
  - `test_progress_service.py` (5 tests): Course completion percentage aggregation, empty attempt handling, and paginated history retrieval.
  - `test_analytics_service.py` (4 tests): Student roster matrix generation, topic mastery distribution aggregation, and zero-attempt question performance handling.

### Level 2: Architectural & Static Verification
- **Location**: `backend/tests/architecture/`
- **Target**: Structural conformance, layer boundary enforcement, and framework isolation.
- **Executed Suites**:
  - `test_layers.py` (11 tests): Automated Abstract Syntax Tree (AST) scanner dynamically discovering all modules in `backend/app/engine/`. Verifies NFR-05 by asserting zero imports of `fastapi`, `starlette`, `sqlalchemy`, `pydantic`, `requests`, `httpx`, or outer-layer application packages (`app.api`, `app.services`, `app.repositories`). Includes scanner reliability tests ensuring comments and docstrings are ignored.
  - **Static Analysis**: Ruff linting and formatting configured via `ruff.toml` enforcing PEP 8 standards (NFR-16).

### Level 3: API Integration Testing
- **Location**: `backend/tests/integration/`
- **Target**: FastAPI route handling, Pydantic schema validation, HTTP status codes, role-based access control, and multi-tenant data privacy.
- **Executed Suites**:
  - `test_adaptive_api.py` (7 tests): `GET/PUT /courses/{id}/adaptive-settings`, `GET /courses/{id}/recommendations`, `POST /courses/{id}/recalculate-mastery`.
  - `test_progress_api.py` (6 tests): `GET /courses/{id}/progress`, `GET /courses/{id}/attempts`, unauthorized access rejection (401), cross-student privacy enforcement (403), instructor viewing permissions.
  - `test_instructor_analytics_api.py` (6 tests): `GET /courses/{id}/analytics/mastery-distribution`, `GET /courses/{id}/analytics/student-roster`, `GET /courses/{id}/analytics/questions`, student role forbidden rejection (403), non-owner instructor rejection (403).

### Level 4: Core System Health Testing
- **Location**: `backend/tests/test_health.py`
- **Target**: Application initialization, root endpoint, and health check readiness (3 tests).

---

## 4. Completed vs. Planned Verification Status

### A. Completed Verification (Evidence Baseline)
All 150 automated test cases pass cleanly with zero failures and zero regressions:

```text
====================== 150 passed, 8 warnings in 35.39s =======================
```

| Verification Area | Test Suite Location | Tests Count | Status | Associated Requirements |
| :--- | :--- | :---: | :---: | :--- |
| **Mastery Policy** | `backend/tests/unit/test_mastery_policy.py` | 12 | **Passed** | FR-17, NFR-10 |
| **Mastery Calculator** | `backend/tests/unit/test_mastery_calculator.py` | 16 | **Passed** | FR-16, FR-20, NFR-10 |
| **Recommendation Strategy** | `backend/tests/unit/test_recommendation_strategy.py` | 18 | **Passed** | FR-18, FR-19, NFR-10, CR-01 (Factory Method) |
| **Progress Service** | `backend/tests/unit/test_progress_service.py` | 5 | **Passed** | FR-15, FR-21 |
| **Analytics Service** | `backend/tests/unit/test_analytics_service.py` | 4 | **Passed** | FR-22, FR-23, FR-24 |
| **Authentication Contract** | `backend/tests/unit/test_auth.py` | 18 | **Passed** | NFR-04, NFR-14 (Preset tokens) |
| **Security & Cryptography** | `backend/tests/unit/test_security_auth.py` | 30 | **Passed** | FR-01, FR-02, NFR-03, NFR-04 (Signed JWT, Bcrypt) |
| **Relational Storage** | `backend/tests/unit/test_persistence.py` | 9 | **Passed** | NFR-08, NFR-09, DEF-DATA-001 (Restart survival) |
| **Architecture Isolation** | `backend/tests/architecture/test_layers.py` | 11 | **Passed** | NFR-05, NFR-11, NFR-15 (Pure engine) |
| **Adaptive API Integration** | `backend/tests/integration/test_adaptive_api.py` | 7 | **Passed** | FR-16, FR-18, FR-20, FR-25 |
| **Progress API Integration** | `backend/tests/integration/test_progress_api.py` | 6 | **Passed** | FR-15, FR-21, NFR-04, NFR-06 |
| **Analytics API Integration**| `backend/tests/integration/test_instructor_analytics_api.py` | 6 | **Passed** | FR-03, FR-22, FR-23, FR-24, NFR-05 |
| **Cross-Module Integration** | `backend/tests/integration/test_cross_module_integration.py` | 5 | **Passed** | Multi-module end-to-end pipeline |
| **Core Health Check** | `backend/tests/test_health.py` | 3 | **Passed** | REQ-SYS-001 |
| **Total Automated Tests** | — | **150** | **100% Pass** | Full Regression Suite |

### B. Planned Verification (Future Milestones)

| Planned Activity | Target Requirement | Mechanism & Tooling | Precondition / Blocker |
| :--- | :--- | :--- | :--- |
| **End-to-End User Journey Tests** | FR-01 through FR-24 | Playwright / Simulated User Flows | Requires full frontend and M1/M2 module completion |
| **Database Concurrency & Row Locking** | NFR-08, NFR-09 | Pytest with live PostgreSQL Docker container | Requires Docker setup and CR-02 approval |
| **Performance & Load Testing** | NFR-01, NFR-02 | Locust load test harness (50 concurrent users) | Requires persistent environment deployment |
| **Cross-Browser & Responsive Validation**| NFR-13 | Automated viewport testing down to 360px | Requires frontend UI delivery |
| **Peer Usability Walkthrough** | NFR-12 | Structured usability evaluation protocol | Requires frontend UI delivery |

---

## 5. Test Execution Instructions

### Windows (PowerShell)
To prevent `ModuleNotFoundError: No module named 'app'`, set `PYTHONPATH` before invoking pytest:

```powershell
# From project root:
$env:PYTHONPATH='backend'; .\backend\venv\Scripts\pytest backend/tests -v

# Run with line coverage report:
$env:PYTHONPATH='backend'; .\backend\venv\Scripts\pytest backend/tests --cov=backend/app --cov-report=term-missing
```

### Linux / macOS (Bash)
```bash
# From project root:
PYTHONPATH=backend ./backend/venv/bin/pytest backend/tests -v
```

---

## 6. Roles & Responsibilities

| Team Member | Verification & Validation Responsibilities |
| :--- | :--- |
| **Hiba Zulfiqar** | Author and verify Module 1 (Auth, User/Course Management) and Module 4 (Prerequisite Graphs); peer-review M2 and M3 pull requests. |
| **Mustajaab Ul Fida Qadri** | Author and verify Module 2 (Question Bank, Quizzes, Attempt Grading); peer-review M1 and M5 pull requests. |
| **Toqeer Ahmed** | Author and verify Module 3 (Adaptive Learning Engine) and Module 5 (Progress & Analytics); maintain AST architecture tests, CI/CD pipelines, and SQA quality documentation. |

---

## 7. Entry and Exit Criteria

### Entry Criteria for Pull Requests
1. Code passes Ruff static analysis checks (`ruff check .`) with zero errors.
2. Code builds cleanly without syntax errors or circular import dependencies.
3. Automated AST architecture test suite passes verifying pure engine isolation.

### Exit Criteria for Milestone Releases
1. 100% of implemented unit, integration, and architecture tests executed and passing.
2. Zero Critical (S1) or Major (S2) unresolved defects in the Defect Log.
3. All implemented functional and non-functional requirements linked in the RTM with verifiable test proof.
4. Formal technical inspection completed and signed off.
