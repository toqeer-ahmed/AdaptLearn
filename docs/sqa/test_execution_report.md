# Test Execution Report

> **Document Status**: Complete / Reconciled Quality Execution Record (Post-Corrective Commits 2–6)<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Standard Reference**: IEEE Std 1012 / SE431 SQA Rubric<br>
> **Execution Date**: November 21, 2026<br>
> **Lead Tester**: Toqeer Ahmed (Lead Engine Architect & SQA Engineer)<br>
> **Tested Commit Baseline**: `ad1ebd4` (Post Task COMMIT-06)

---

## 1. Test Execution Metadata

| Parameter | Details |
| :--- | :--- |
| **Execution Date** | November 21, 2026 |
| **Test Environment** | OS: Windows 11 (build 10.0.26200)<br>Python: 3.10.11 (tags/v3.10.11:7d4cc5a)<br>Pytest: 9.2.0 (pluggy 1.7.0, anyio 4.16.0)<br>Node.js: v20.x, Vite 8.3.8 |
| **Build / Commit Tested** | `ad1ebd4` (Post Task COMMIT-06 Verification) |
| **Test Suite Type** | Architecture / Security & Auth / Persistence / Unit / Integration / Cross-Module Regression / Smoke |
| **Command Executed** | `$env:PYTHONPATH='backend'; .\backend\venv\Scripts\pytest backend/tests -v` |
| **Execution Duration** | **35.39 seconds** |

---

## 2. Test Execution Summary

| Metric | Count | Percentage |
| :--- | :---: | :---: |
| **Total Automated Tests** | **150** | **100%** |
| **Passed** | **150** | **100%** |
| **Failed** | **0** | **0%** |
| **Blocked / Skipped** | **0** | **0%** |
| **Execution Rate** | **150 / 150** | **100%** |

### Suite Breakdown Across 14 Test Modules

| # | Suite Category | Target Test File | Tests | Passed | Failed | Duration | Requirements Covered |
| :-: | :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| 1 | **Architecture Isolation** | `backend/tests/architecture/test_layers.py` | 11 | 11 | 0 | 0.05s | NFR-05, NFR-15 (Pure engine isolation) |
| 2 | **Mastery Calculator (Unit)**| `backend/tests/unit/test_mastery_calculator.py` | 16 | 16 | 0 | 0.05s | FR-16, FR-20, TC-16-1..4 (Weighted math) |
| 3 | **Mastery Policy (Unit)** | `backend/tests/unit/test_mastery_policy.py` | 12 | 12 | 0 | 0.03s | FR-17, TC-17-1..4 (Boundary classifications) |
| 4 | **Recommendations (Unit)** | `backend/tests/unit/test_recommendation_strategy.py` | 18 | 18 | 0 | 0.06s | FR-18, FR-19, TC-18-1..6, CR-01 (Factory Method) |
| 5 | **Progress Service (Unit)** | `backend/tests/unit/test_progress_service.py` | 5 | 5 | 0 | 0.02s | FR-21, TC-21-1..2 (Completion %, pagination) |
| 6 | **Analytics Service (Unit)**| `backend/tests/unit/test_analytics_service.py` | 4 | 4 | 0 | 0.02s | FR-22, FR-23, FR-24, TC-24-2 (Deterministic stats) |
| 7 | **Authentication Contract (Unit)**| `backend/tests/unit/test_auth.py` | 18 | 18 | 0 | 0.12s | NFR-04, NFR-14, DEF-AUTH-001 (Preset token format) |
| 8 | **Security & Auth (Unit)** | `backend/tests/unit/test_security_auth.py` | 30 | 30 | 0 | 18.25s | FR-01, FR-02, NFR-03, NFR-04 (Signed JWT, Bcrypt) |
| 9 | **Storage & Persistence (Unit)**| `backend/tests/unit/test_persistence.py` | 9 | 9 | 0 | 0.40s | NFR-08, NFR-09, DEF-DATA-001 (Restart survival) |
| 10 | **Adaptive API (Integration)**| `backend/tests/integration/test_adaptive_api.py` | 7 | 7 | 0 | 1.56s | FR-16, FR-18, FR-20 (GET/PUT settings, recs) |
| 11 | **Progress API (Integration)**| `backend/tests/integration/test_progress_api.py` | 6 | 6 | 0 | 0.22s | FR-15, FR-21, NFR-06 (Dashboard, privacy) |
| 12 | **Analytics API (Integration)**| `backend/tests/integration/test_instructor_analytics_api.py` | 6 | 6 | 0 | 0.24s | FR-03, FR-22..24, TC-03-1, TC-22-2 (RBAC) |
| 13 | **Cross-Module Integration** | `backend/tests/integration/test_cross_module_integration.py` | 5 | 5 | 0 | 0.25s | End-to-end Quiz $\rightarrow$ Mastery $\rightarrow$ Analytics |
| 14 | **System Core Health** | `backend/tests/test_health.py` | 3 | 3 | 0 | 0.14s | REQ-SYS-001 (Root, health, schema) |
| **Total** | **Full Regression Suite** | **14 Test Modules** | **150** | **150** | **0** | **35.39s** | **100% Pass Rate** |

---

## 3. Detailed Test Module Breakdown

### 3.1 Architecture Isolation (`test_layers.py` — 11 Tests)
- `test_engine_directory_exists_and_contains_modules`: PASS
- `test_engine_files_have_zero_prohibited_imports[__init__.py]`: PASS
- `test_engine_files_have_zero_prohibited_imports[mastery_calculator.py]`: PASS
- `test_engine_files_have_zero_prohibited_imports[mastery_policy.py]`: PASS
- `test_engine_files_have_zero_prohibited_imports[recommendation_strategy.py]`: PASS
- `test_engine_files_do_not_escape_via_relative_imports[...]` (4 tests): PASS
- `test_scanner_flags_prohibited_framework_imports`: PASS
- `test_scanner_ignores_mentions_in_comments_and_docstrings`: PASS

### 3.2 Security, Cryptography & Auth (`test_security_auth.py` & `test_auth.py` — 48 Tests)
- **Password Hashing (NFR-03, Decision D5)**:
  - `test_hash_password_produces_bcrypt_hash`: PASS
  - `test_verify_password_correct_and_incorrect`: PASS
  - `test_password_hash_uniqueness_salt`: PASS
- **JWT Cryptographic Signing & Expiry (NFR-04)**:
  - `test_create_access_token_structure_and_claims`: PASS
  - `test_decode_access_token_valid`: PASS
  - `test_decode_access_token_expired_fails`: PASS
  - `test_decode_access_token_invalid_signature_fails`: PASS
  - `test_decode_access_token_missing_required_claims_fails`: PASS
- **Authentication Endpoints & RBAC (FR-01, FR-02, FR-03, NFR-05)**:
  - User registration (`POST /api/v1/auth/register`): 7 tests covering success, duplicates (409), and field bounds.
  - User login (`POST /api/v1/auth/login`): 4 tests covering valid login, non-existent email, invalid password, and generic 401 error.
  - Role-based access control & token tampering guards: 7 tests verifying spoofing rejection, expired token rejection, and role enforcement.
- **Frontend Token Alignment (`test_auth.py`)**:
  - 18 tests covering student/instructor persona tokens, case insensitivity, whitespace trimming, legacy token rejection, and authorized endpoint access.

### 3.3 Relational Storage & Restart Survival (`test_persistence.py` — 9 Tests)
- `test_course_settings_crud_and_survival_across_restart`: PASS (Custom parameters reloaded from physical SQLite DB after repository instance destroyed).
- `test_student_topic_responses_survival_across_restart`: PASS (Response history reloaded with preserved ordering, difficulty, and scores).
- `test_course_topics_and_prerequisites_survival_across_restart`: PASS (Topic directed acyclic graphs and prerequisites survive restart).
- `test_empty_database_defaults`: PASS (Default course settings returned when unconfigured).
- `test_enrollment_and_attempt_persistence`: PASS (Student course enrollments and paginated quiz attempts reload accurately).
- `test_question_stats_persistence_and_accumulation`: PASS (Question response counters and correct answer tallies persist).
- `test_user_persistence_and_seeding`: PASS (Default seed personas and created user records persist).
- `test_user_unique_constraint_enforcement`: PASS (Duplicate email persistence rejected by database integrity constraint).
- `test_restart_survival_across_repository_recreation`: PASS (Full multi-module restart simulation).

### 3.4 Recommendation Strategy & Factory Method (`test_recommendation_strategy.py` — 18 Tests)
- M1 Section 9.3 Scenarios (TC-18-1..TC-18-6): 6 tests (Weak before Developing, Proficient excluded, prerequisite priority, deterministic alphabetical tie-breaking, Developing before Not Assessed, empty list on all proficient).
- Boundary & Prerequisite Handling: 4 tests (proficient prerequisites, external prereq override, recommendation limits, rationales).
- Strategy Pattern Interchangeability: 2 tests.
- **GoF Factory Method Pattern (CR-01, DEF-ARCH-001)**: 6 tests:
  - `test_creator_abstraction_cannot_be_instantiated`: PASS
  - `test_rule_based_creator_returns_expected_strategy`: PASS
  - `test_creator_recommend_delegates_to_factory_method_product`: PASS
  - `test_polymorphic_subclass_creator`: PASS
  - `test_get_strategy_creator_resolution`: PASS
  - `test_get_recommendation_strategy_delegates_through_creator`: PASS

### 3.5 Computational Mastery & Services (`test_mastery_calculator.py`, `test_mastery_policy.py`, `test_progress_service.py`, `test_analytics_service.py` — 37 Tests)
- Mastery calculations (FR-16, TC-16-1..4): 16 tests covering weighted proportion math, sliding window ($N=5$), configurability (FR-20), immutability.
- Policy boundary classifications (FR-17, TC-17-1..4): 12 tests (Weak $<0.50$, Developing $0.50-0.79$, Proficient $\ge 0.80$, Not Assessed $<3$ responses).
- Progress & Analytics Services (FR-21..24): 9 tests (completion percentage, empty courses, roster matrices, mastery distribution, question answering stats).

### 3.6 API Integration & Core Health (27 Tests)
- `test_adaptive_api.py` (7 tests): GET/PUT adaptive parameters, recommendations, recalculate mastery.
- `test_progress_api.py` (6 tests): Student progress dashboard, attempt history pagination, 401 unauthenticated, 403 cross-student privacy.
- `test_instructor_analytics_api.py` (6 tests): Mastery distribution, student roster, question performance, 403 student rejection, 403 non-owner rejection.
- `test_cross_module_integration.py` (5 tests): Full student quiz $\rightarrow$ mastery recalculation $\rightarrow$ progress dashboard $\rightarrow$ instructor analytics.
- `test_health.py` (3 tests): Root `/`, `/health`, and `/api/v1/health`.

---

## 4. Test Environment Verification Log

```text
============================= test session starts =============================
platform win32 -- Python 3.10.11, pytest-9.2.0, pluggy-1.7.0 -- D:\Study Material\Seven Semester\Software Quality Assurance SE431\Project\backend\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Study Material\Seven Semester\Software Quality Assurance SE431\Project\backend
configfile: pyproject.toml
plugins: anyio-4.16.0
collecting ... collected 150 items

backend\tests\architecture\test_layers.py ...........                    [  7%]
backend\tests\integration\test_adaptive_api.py .......                   [ 12%]
backend\tests\integration\test_cross_module_integration.py .....         [ 15%]
backend\tests\integration\test_instructor_analytics_api.py ......        [ 19%]
backend\tests\integration\test_progress_api.py ......                    [ 23%]
backend\tests\test_health.py ...                                         [ 25%]
backend\tests\unit\test_analytics_service.py ....                        [ 28%]
backend\tests\unit\test_auth.py ..................                       [ 40%]
backend\tests\unit\test_mastery_calculator.py ................           [ 50%]
backend\tests\unit\test_mastery_policy.py ............                   [ 58%]
backend\tests\unit\test_persistence.py .........                         [ 64%]
backend\tests\unit\test_progress_service.py .....                        [ 68%]
backend\tests\unit\test_recommendation_strategy.py ..................    [ 80%]
backend\tests\unit\test_security_auth.py ..............................  [100%]

====================== 150 passed, 8 warnings in 35.39s =======================
```

---

## 5. Sign-off & Conclusion
- **Execution Evaluation**: All **150 automated tests** execute cleanly with a **100% pass rate** in **35.39 seconds**.
- **Quality Standard Compliance**: Fully satisfies NFR-03 (salted bcrypt hashing), NFR-04 (signed JWT tokens), NFR-05 (pure engine isolation), NFR-08 (persistent transactional repositories), NFR-09 (referential integrity), NFR-10 (deterministic calculations), and NFR-17 (comprehensive automated test coverage).
- **QA Sign-off**: Verified and certified by Toqeer Ahmed (Lead Engine Architect & SQA Engineer).
