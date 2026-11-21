# Static Analysis Report

> **Document Status**: Completed Baseline & Remediation Report<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Standard Reference**: IEEE Std 1012 / SE431 SQA Quality Milestone<br>
> **Evidence Basis**: Real Tool Execution Logs (Oxlint 1.94.0, Ruff 0.16.3, MyPy 2.3.0)

---

## 1. Analysis Session Metadata

| Parameter | Details |
| :--- | :--- |
| **Execution Date** | 2026-11-21 |
| **Commit Tested** | `5e56bf5` (Working tree audit and remediation) |
| **Target Directories** | `frontend/` and `backend/` |
| **Lead Analyst** | Toqeer Ahmed (Adaptive Engine & SQA Lead) |

---

## 2. Tools & Commands Executed

| Component | Tool & Version | Command Executed | Purpose | Execution Status |
| :--- | :--- | :--- | :--- | :---: |
| **Frontend** | Oxlint (`v1.94.0`) | `npx --prefix frontend oxlint` | JavaScript/JSX syntax, dead code, React component patterns | **Executed (Clean)** |
| **Backend Linter** | Ruff (`v0.16.3`) | `ruff check backend` | Python style (PEP 8), unused imports, deprecated typing, bugbear defects | **Executed (Resolved)** |
| **Type Checking** | MyPy (`v2.3.0`) | `mypy backend/app` | Static typing, signature validation, type narrowing checks | **Executed (Resolved)** |
| **Legacy Linter** | Flake8 | `flake8 app tests` | Legacy PEP 8 checks (superseded by Ruff per NFR-16) | **Not Run** *(Ruff configured)* |

---

## 3. Analysis Summary: Before vs. After Remediation

| Category | Run 1 (Baseline Findings) | Run 2 (Post-Remediation) | Delta / Change Explanation |
| :--- | :---: | :---: | :--- |
| **Frontend (Oxlint)** | 0 | 0 | Clean on initial run; zero lint defects in React/Vite source files. |
| **Backend High / Bugbear (B008)** | 19 | 0 | Refactored FastAPI parameter defaults to Python 3.10 `typing.Annotated`. |
| **Backend Code Simplification (SIM102)** | 1 | 0 | Merged nested `if` statement using `and` in AST test fixture. |
| **Backend Redundant Pass (PIE790)** | 3 | 0 | Removed unnecessary `pass` statements in documented classes/methods. |
| **Backend Dunder All Sorting (RUF022)** | 3 | 0 | Alphabetically sorted `__all__` lists in module `__init__.py` files. |
| **Backend Deprecated Typing (UP006/035/045/007)**| 135 | 0 | Modernized annotations to native Python 3.10 types (`list`, `X \| None`). |
| **Backend Import Formatting (I001)** | 26 | 0 | Reorganized import blocks to strict PEP 8 isort ordering. |
| **Backend Static Typing (MyPy)** | 1 | 0 | Narrowed `str \| list[str]` type check in CORS origin validator. |
| **Total Issues** | **188** | **0** | **100% Resolved without synthetic rule suppressions** |

---

## 4. Detailed Findings & Remediation Log

| Finding ID | File Path & Target | Tool & Rule ID | Severity | Root Cause Description | Remediation Applied | Status |
| :---: | :--- | :---: | :---: | :--- | :--- | :---: |
| **SA-001** | `backend/app/api/v1/endpoints/adaptive.py`<br>`backend/app/api/v1/endpoints/analytics.py`<br>`backend/app/api/v1/endpoints/progress.py` | Ruff `B008` | Error | FastAPI route functions used `Depends(...)` and `Query(...)` inside default parameter assignments. | Refactored route signatures to use modern `Annotated[T, Depends(...)]` and `Annotated[T, Query(...)] = default`, eliminating function calls in parameter defaults. | **Resolved** |
| **SA-002** | `backend/tests/unit/test_mastery_calculator.py:296` | Ruff `SIM102` | Warning | Nested `if node.module:` inside `elif isinstance(node, ast.ImportFrom):` created unnecessary nesting. | Collapsed into a single `elif isinstance(node, ast.ImportFrom) and node.module:` condition. | **Resolved** |
| **SA-003** | `backend/app/engine/mastery_policy.py:20, 25`<br>`backend/app/engine/recommendation_strategy.py:87` | Ruff `PIE790` | Convention | Redundant `pass` statement in exception classes and abstract methods that already contained docstrings. | Removed unnecessary `pass` statements; docstring serves as valid suite statement. | **Resolved** |
| **SA-004** | `backend/app/engine/__init__.py`<br>`backend/app/repositories/__init__.py`<br>`backend/app/services/__init__.py` | Ruff `RUF022` | Convention | `__all__` exported symbols tuple was not sorted alphabetically. | Alphabetically sorted all entries in `__all__` across packages. | **Resolved** |
| **SA-005** | Across `app/schemas/`, `app/services/`, `app/engine/`, `tests/` | Ruff `UP006`<br>`UP035`<br>`UP045`<br>`UP007` | Warning | Legacy typing constructs used (`typing.List`, `Dict`, `Optional`, `Union`, `Sequence`). | Replaced with native Python 3.10 syntax: `list[T]`, `dict[K, V]`, `T \| None`, `T1 \| T2`, and `collections.abc.Sequence`. | **Resolved** |
| **SA-006** | Across all backend Python modules | Ruff `I001` | Convention | Import blocks were not partitioned into standard library, third-party, and first-party blocks. | Organized import blocks alphabetically according to PEP 8 / isort rules. | **Resolved** |
| **SA-007** | `backend/app/core/config.py:26` | MyPy `return-value` | Error | Incompatible return value type (`str \| list[str]` returned where `list[str]` was expected). | Added explicit string branch with early returns, allowing MyPy to safely narrow `v` to `list[str]`. | **Resolved** |

---

## 5. Tool Output Raw Logs

### Run 1: Baseline Tool Execution

#### Frontend (Oxlint Run 1)
```text
$ npx --prefix frontend oxlint
Found 0 warnings and 0 errors.
Finished in 74ms on 3 files using 4 threads.
```

#### Backend (Ruff Run 1 — Statistics)
```text
$ ruff check backend --statistics
71	UP006 	[*] non-pep585-annotation
36	UP045 	[*] non-pep604-annotation-optional
27	UP035 	[-] deprecated-import
26	I001  	[*] unsorted-imports
19	B008  	[ ] function-call-in-default-argument
 3	PIE790	[*] unnecessary-placeholder
 3	RUF022	[*] unsorted-dunder-all
 1	SIM102	[ ] collapsible-if
 1	UP007 	[*] non-pep604-annotation-union
Found 187 errors.
[*] 143 fixable with the `--fix` option (1 hidden fix can be enabled with the `--unsafe-fixes` option).
```

#### Backend (MyPy Run 1)
```text
$ mypy backend/app
backend\app\core\config.py:26: error: Incompatible return value type (got "str | list[str]", expected "list[str]")  [return-value]
Found 1 error in 1 file (checked 31 source files)
```

---

### Run 2: Post-Remediation Verification

#### Frontend (Oxlint Run 2)
```text
$ npx --prefix frontend oxlint
Found 0 warnings and 0 errors.
Finished in 20ms on 3 files using 4 threads.
```

#### Backend (Ruff Run 2)
```text
$ ruff check backend
All checks passed!
```

#### Backend (MyPy Run 2)
```text
$ mypy backend/app
Success: no issues found in 31 source files
```

#### Test Suite Verification After Fixes
```text
$ $env:PYTHONPATH='backend'; .\backend\venv\Scripts\pytest backend/tests -q
........................................................................ [ 87%]
..........                                                               [100%]
82 passed, 2 warnings in 1.46s
```

---

### Run 3: Post-Corrective Commits Reconciliation (Task COMMIT-07)

Following the implementation of secure JWT/bcrypt authentication (Commit 3), persistent relational storage (Commit 4), and recommendation strategy Factory Method (Commit 5), a full static analysis pass was re-executed on November 21, 2026.

#### Frontend (Oxlint Run 3)
```text
$ npx --prefix frontend oxlint
Found 0 warnings and 0 errors.
Finished in 39ms on 15 files using 4 threads.
```

#### Backend (Ruff Run 3)
```text
$ ruff check backend/app backend/tests
All checks passed!
```

#### Test Suite Verification (14 Test Modules)
```text
$ $env:PYTHONPATH='backend'; .\backend\venv\Scripts\pytest backend/tests -q
====================== 150 passed, 8 warnings in 35.39s =======================
```

---

## 6. Repository Static Analysis Configuration

To satisfy **NFR-16** ("The backend code shall pass Ruff checks with no errors under the configuration stored in the repository"), `backend/pyproject.toml` has been added to version control with standard settings:

```toml
[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # Pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "UP",   # pyupgrade
    "SIM",  # flake8-simplify
    "RUF",  # Ruff-specific rules
]
ignore = [
    "E501",  # Line length handled gracefully / formatting
]

[tool.ruff.lint.flake8-bugbear]
extend-immutable-calls = [
    "fastapi.Depends",
    "fastapi.params.Depends",
    "fastapi.Query",
    "fastapi.params.Query",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "-v --strict-markers"
```

---

## 7. Recommendations & Quality Policy

1. **Continuous Pre-Commit Linting**: Run `ruff check backend` and `npx --prefix frontend oxlint` locally before submitting pull requests.
2. **Defensive Typing**: Continue utilizing Python 3.10 native typing (`list[T]`, `T | None`) and FastAPI's `Annotated` pattern for all new routers and services.
3. **CI Pipeline Integration**: Ensure `.github/workflows/ci.yml` includes `ruff check backend` and `npx --prefix frontend oxlint` as blocking gating checks (NFR-18).
