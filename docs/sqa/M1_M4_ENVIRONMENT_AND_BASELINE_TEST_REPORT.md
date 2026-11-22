# AdaptLearn — Environment Setup & Baseline Test Execution Report
## Modules: M1 (User & Course Management) & M4 (Personalized Learning Paths)

**Document Reference:** `docs/sqa/M1_M4_ENVIRONMENT_AND_BASELINE_TEST_REPORT.md`  
**Document Type:** Software Quality Assurance Environment & Baseline Test Verification Report  
**Author:** Hiba Zulfiqar (`2023246`) — Lead for M1 & M4  
**Target Reviewers / Approvers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Repository Baseline:** `https://github.com/toqeer-ahmed/AdaptLearn`  
**Git Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f` (`fix(ci): resolve backend test collection failure`)  
**Status:** **BASELINE TEST SUITE VERIFIED (150/150 PASSED — 100% GREEN)**  
**Date:** November 21, 2026  

---

## 1. Executive Summary

In accordance with SQA verification standards and project safety rules, a pristine local virtual environment was provisioned, verified, and used to execute the entire existing AdaptLearn backend test suite.

**Key Milestone Accomplishments:**
1. **Isolated Virtual Environment Established:** Created `backend/venv` using Python's standard `venv` module. Zero packages were installed globally.
2. **Official Dependencies Installed:** Installed all 32 direct and transitive dependencies from `backend/requirements.txt` via `pip`.
3. **100% Baseline Test Suite Pass:** Executed `pytest` across all 13 test modules; all **150 automated tests passed** in **24.45 seconds** with **0 failures**, **0 errors**, and **0 skipped tests**.
4. **Zero Source Code Invasions:** Confirmed via `git status --short` that no application source files or configuration files were touched or altered. `backend/venv` is cleanly ignored by `.gitignore`.

---

## 2. Supported Python Version & Host Environment Audit

### 2.1 Project-Documented Python Version Requirements
Authoritative project documentation and configuration files specify the following Python runtime constraints:

| Configuration Source | Line / Section | Documented Python Specification |
| :--- | :--- | :--- |
| `AdaptLearn/README.md` | Line 13, Line 74 | `Python 3.10+`, `Python: 3.10 or higher` |
| `backend/pyproject.toml` | Line 2 (`[tool.ruff]`) | `target-version = "py310"` |
| `.github/workflows/ci.yml` | Line 26 (`backend-test`) | `python-version: "3.10"` |
| `backend/requirements.txt` | Dependency bounds | `fastapi>=0.110.0,<1.0.0`, `sqlalchemy>=2.0.0,<3.0.0`, `pydantic>=2.6.0,<3.0.0`, `bcrypt>=4.1.0,<6.0.0` |

### 2.2 Host System Python Availability Audit
An exhaustive inspection of the host system's Python installations was performed using PowerShell and `winget`:

```powershell
# Commands Executed:
py -0p
Get-Command python* -All
winget list Python
```

**Host Inspection Findings:**
- **Host Python Launcher (`py -0p`):** `-V:3.14 * C:\Users\hiba2\AppData\Local\Programs\Python\Python314\python.exe`
- **Host Python Binary Version:** `Python 3.14.3 (64-bit)`
- **Available Installed Versions:** Only **Python 3.14.3** was present on the machine. Neither Python 3.10, 3.11, nor 3.12 was installed or detected in system directories or PATH.
- **Python 3.14 Compatibility Verdict:** While Python 3.10 is pinned in CI, Python 3.14.3 successfully resolved and downloaded official Windows wheels (`cp314` and stable `cp39-abi3` wheels) for all critical binary C extensions (`bcrypt-5.0.0-cp39-abi3-win_amd64.whl`, `sqlalchemy-2.1.9-cp314-cp314-win_amd64.whl`, `pydantic_core-2.50.5-cp314-cp314-win_amd64.whl`). No local C++ compilation was required, and the runtime behaves with full fidelity.

---

## 3. Virtual Environment Creation & Verification

### 3.1 Virtual Environment Provisioning
In strict accordance with `README.md` §2 ("Backend Setup"), the virtual environment was created directly inside `backend/`:

```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend"
python -m venv venv
```

- **Location:** `C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend\venv`
- **Isolation:** Completely self-contained; zero modifications made to global Python site-packages.
- **Git Status:** Fully ignored by `.gitignore` line 30 (`backend/venv/`).

### 3.2 Environment Runtime Verification

```powershell
.\venv\Scripts\python.exe --version
# Output: Python 3.14.3

.\venv\Scripts\pip.exe --version
# Output: pip 25.3 from C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend\venv\Lib\site-packages\pip (python 3.14)
```

---

## 4. Dependency Installation Results

### 4.1 Installation Command
Dependencies were installed using the project's documented installation method:

```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend"
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 4.2 Installation Result: **SUCCESS (Exit Code 0)**
A total of **32 packages** (direct project requirements and their sub-dependencies) were successfully fetched and installed:

| Package Name | Installed Version | Requirement Source |
| :--- | :--- | :--- |
| `fastapi` | `0.165.0` | `fastapi>=0.110.0,<1.0.0` |
| `uvicorn` (standard) | `0.54.0` | `uvicorn[standard]>=0.28.0,<1.0.0` |
| `pydantic` | `2.14.4` | `pydantic>=2.6.0,<3.0.0` |
| `pydantic-core` | `2.50.5` | Transitive dependency of `pydantic` |
| `pydantic-settings` | `2.16.3` | `pydantic-settings>=2.2.0,<3.0.0` |
| `python-dotenv` | `1.2.4` | `python-dotenv>=1.0.0` |
| `pytest` | `9.2.0` | `pytest>=8.0.0` |
| `httpx` | `0.28.1` | `httpx>=0.27.0` |
| `pyjwt` | `2.15.1` | `pyjwt>=2.8.0,<3.0.0` |
| `bcrypt` | `5.0.0` | `bcrypt>=4.1.0,<6.0.0` |
| `sqlalchemy` | `2.1.9` | `sqlalchemy>=2.0.0,<3.0.0` |
| `starlette` | `1.10.0` | Transitive dependency of `fastapi` |
| `anyio` | `4.16.0` | Transitive dependency of `starlette` |
| `watchfiles` | `1.3.0` | Transitive dependency of `uvicorn[standard]` |
| `websockets` | `17.4` | Transitive dependency of `uvicorn[standard]` |
| `httptools` | `0.9.0` | Transitive dependency of `uvicorn[standard]` |
| `pyyaml` | `6.0.4` | Transitive dependency of `uvicorn[standard]` |

Zero errors were encountered. Zero dependency versions were relaxed or modified.

---

## 5. Baseline Backend Test Execution

### 5.1 Configured Test Command
The test suite was executed using the project's configured test runner and arguments:
- `backend/pyproject.toml` defines:
  ```toml
  [tool.pytest.ini_options]
  testpaths = ["tests"]
  pythonpath = ["."]
  addopts = "-v --strict-markers"
  ```
- Command executed:
  ```powershell
  cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend"
  .\venv\Scripts\pytest.exe
  ```

### 5.2 Test Execution Results Summary

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.2.0, pluggy-1.7.0
rootdir: C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn\backend
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.16.0
collected 150 items

Execution Time: 24.45 seconds
Overall Result: 150 PASSED, 0 FAILED, 0 SKIPPED (100% Pass Rate)
Exit Code:      0
```

### 5.3 Detailed Breakdown by Test Suite

| Test File Path | Category | Total Tests | Passed | Failed | Skipped | Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `tests/architecture/test_layers.py` | Architecture Integrity | 11 | 11 | 0 | 0 | **PASS** |
| `tests/integration/test_adaptive_api.py` | Integration (M3 Adaptive) | 7 | 7 | 0 | 0 | **PASS** |
| `tests/integration/test_cross_module_integration.py` | Cross-Module E2E | 5 | 5 | 0 | 0 | **PASS** |
| `tests/integration/test_instructor_analytics_api.py` | Integration (M5 Analytics) | 6 | 6 | 0 | 0 | **PASS** |
| `tests/integration/test_progress_api.py` | Integration (M5 Progress) | 6 | 6 | 0 | 0 | **PASS** |
| `tests/unit/test_analytics_service.py` | Unit (Analytics Service) | 12 | 12 | 0 | 0 | **PASS** |
| `tests/unit/test_auth.py` | Unit (Authentication Core) | 13 | 13 | 0 | 0 | **PASS** |
| `tests/unit/test_mastery_calculator.py` | Unit (Mastery Math / EWMA) | 20 | 20 | 0 | 0 | **PASS** |
| `tests/unit/test_mastery_policy.py` | Unit (Mastery Policy) | 6 | 6 | 0 | 0 | **PASS** |
| `tests/unit/test_persistence.py` | Unit (Repositories & DB) | 12 | 12 | 0 | 0 | **PASS** |
| `tests/unit/test_progress_service.py` | Unit (Progress Calculations) | 10 | 10 | 0 | 0 | **PASS** |
| `tests/unit/test_recommendation_strategy.py` | Unit (Strategy / Factory) | 19 | 19 | 0 | 0 | **PASS** |
| `tests/unit/test_security_auth.py` | Unit (Security & RBAC) | 23 | 23 | 0 | 0 | **PASS** |
| **TOTALS** | — | **150** | **150** | **0** | **0** | **100% PASS** |

### 5.4 Warnings Captured During Execution
During execution, pytest reported 8 deprecation warnings (0 errors):
- **1x Starlette TestClient Notice:** `Using httpx with starlette.testclient is deprecated; install httpx2 instead.` (Raised by `fastapi.testclient`).
- **7x HTTP Status Code Deprecation Notice:** `'HTTP_422_UNPROCESSABLE_ENTITY' is deprecated. Use 'HTTP_422_UNPROCESSABLE_CONTENT' instead.` (Raised by `starlette._exception_handler.py` during validation error assertions).

*SQA Assessment:* These are non-blocking upstream framework deprecation warnings from Starlette/FastAPI that do not indicate application defects.

---

## 6. Final Git Working-Tree Verification

Following environment creation, dependency installation, and test suite execution, the repository status was inspected using `git status --short`:

```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn"
git status --short
```

**Git Status Output:**
```
?? docs/sqa/M1_M4_ENVIRONMENT_AND_BASELINE_TEST_REPORT.md
?? docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md
?? docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md
?? docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md
?? docs/sqa/M1_M4_WORKSPACE_BASELINE.md
```

### SQA Safety Rule Verification:
1. **Source Code Modifications:** **NONE** (Zero tracked application files modified or deleted).
2. **Virtual Environment Ignored:** `backend/venv` does **NOT** appear in `git status` because it is properly covered by `.gitignore`.
3. **Branch Integrity:** Still on branch `main` (`fb4d3c5`), synchronized with `origin/main`. No local or remote branches created or switched.
4. **Untracked Artifacts:** Only the intentional SQA audit and baseline report markdown documents exist as untracked files in `docs/sqa/`.

---

## 7. Remaining Blockers Before Implementation

With the Python environment operational and the 150-test baseline confirmed 100% green, only two operational gates remain before starting implementation:

1. **Formal Team Sign-off on Architecture Proposal:**
   - Review and sign-off on `docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md` by Toqeer Ahmed (`2023567`, M3/M5 lead) and Mustajaab Ul Fida Qadri (`2023728`, M2 lead), specifically approving:
     - M1 table ownership of `course_enrollments` while preserving M5 query compatibility.
     - Stateless dynamic evaluation for M4 learning paths.
2. **Branch Creation Authorization:**
   - User approval to create the dedicated feature branch:
     ```powershell
     git checkout -b feature/m1-course-management
     ```

---

## 8. Conclusion

The AdaptLearn backend development environment is **fully verified, isolated, and operational**. The baseline test suite of **150 tests passes cleanly**, establishing an indisputable software quality baseline. 

**Implementation of Module 1 and Module 4 remains paused pending team sign-off and branch creation approval.**
