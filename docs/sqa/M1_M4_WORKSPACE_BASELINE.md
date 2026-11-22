# Workspace Baseline and Repository Verification Report
## Modules: M1 (User & Course Management) & M4 (Personalized Learning Paths)

**Document Reference:** `docs/sqa/M1_M4_WORKSPACE_BASELINE.md`  
**Auditor / Responsible Lead:** Hiba Zulfiqar (`2023246`) — Lead for M1 & M4  
**Date of Audit:** November 21, 2026  
**Repository URL:** `https://github.com/toqeer-ahmed/AdaptLearn`  
**Verification Target:** Task COMMIT-00 Workspace Baseline  

---

## 1. Repository and Remote Information

A full inspection of the local workspace environment was conducted on November 21, 2026.

* **Root Working Directory:** `C:\Users\hiba2\Desktop\SQA-SCD Project`
* **Local Repository Folder:** `C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn`
* **Repository Origin Remote URL:**
  ```
  origin  https://github.com/toqeer-ahmed/AdaptLearn.git (fetch)
  origin  https://github.com/toqeer-ahmed/AdaptLearn.git (push)
  ```
* **Remote Fetch Verification:** `git fetch origin` executed with zero network or protocol errors.
* **Workspace Isolation:** The cloned repository is cleanly isolated within `AdaptLearn/`. The parent directory `SQA-SCD Project` preserves the user's `.vscode` workspace configuration.

---

## 2. Current Branch and Commit

* **Active Local Branch:** `main`
* **Tracking Remote Branch:** `origin/main`
* **Synchronization Status:** `Your branch is up to date with 'origin/main'`
* **Latest Commit Hash (HEAD):** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f`
* **Commit Author:** `toqeer-ahmed <atoqeer759@gmail.com>`
* **Commit Date:** `Sat Nov 21 12:18:48 2026 +0500`
* **Commit Summary:** `fix(ci): resolve backend test collection failure`
* **Commit History Audit:** Total 11 commits on `main`. Zero divergent commits (`ahead 0, behind 0`).

---

## 3. Working-Tree Status

* **Status:** Clean (`nothing to commit, working tree clean`).
* **Uncommitted Changes:** 0 files modified, staged, or deleted.
* **Untracked Files:** 0 untracked files present in repository tree.
* **Stashes (`git stash list`):** 0 stashes.
* **Feature Branches (`git branch -a`):**
  * Local: `* main`
  * Remote: `remotes/origin/HEAD -> origin/main`, `remotes/origin/main`
  * *Finding*: Zero teammate feature branches exist locally or on remote (e.g., no `feature/m1-*` or `feature/m4-*` currently created).

---

## 4. Project Structure

The verified monorepo directory layout is organized as follows:

```
AdaptLearn/
├── .github/
│   ├── ISSUE_TEMPLATE/       # Bug report, feature request, task templates
│   ├── workflows/ci.yml      # Automated GitHub Actions test workflow
│   └── pull_request_template.md
├── backend/
│   ├── app/
│   │   ├── api/v1/           # API router endpoints (auth, adaptive, progress, analytics, health)
│   │   ├── core/             # Configuration, security (bcrypt/JWT), errors, auth guards
│   │   ├── db/               # SQLAlchemy DeclarativeBase, session factory (session.py)
│   │   ├── engine/           # Pure computational engine (NFR-05: mastery, recommendation)
│   │   ├── models/           # Relational ORM models (user, progress, adaptive)
│   │   ├── repositories/     # Data access abstraction layer
│   │   ├── schemas/          # Pydantic v2 validation contracts
│   │   ├── services/         # Business logic services
│   │   └── main.py           # Application entry point, lifespan, CORS middleware
│   ├── tests/
│   │   ├── architecture/     # AST import layer isolation tests (test_layers.py)
│   │   ├── integration/      # Cross-module API integration tests
│   │   └── unit/             # Engine, service, security, and persistence unit tests
│   ├── pyproject.toml        # Ruff linter config & Pytest options
│   ├── requirements.txt      # Python runtime & test dependencies
│   └── .env.example
├── docs/
│   ├── sqa/                  # SQA logs, RTM, defect log, test execution reports
│   ├── api.md                # Cross-module API contracts
│   ├── architecture_overview.md
│   ├── decisions.md          # Architecture Decision Records (ADRs D1–D7)
│   ├── INTEGRATION_BLOCKERS.md
│   └── PROJECT_BASELINE.md
├── frontend/
│   ├── public/               # Favicon and icons SVG
│   ├── src/                  # React 19 source (App.jsx, client.js, presets.js)
│   ├── package.json          # Vite and React dependencies
│   └── vite.config.js
├── tests/
│   └── README.md             # High-level test philosophy documentation
├── CONTRIBUTING.md           # Collaboration standards, branch conventions, PR rules
└── README.md                 # Main project overview and setup guide
```

---

## 5. Technology Stack & Tooling

### Backend Stack
* **Language / Runtime:** Python (Target: Python 3.10+; Host currently runs Python 3.14.3)
* **API Framework:** FastAPI (`0.162.5`) with ASGI server Uvicorn (`0.54.0`)
* **Data Validation:** Pydantic v2 (`2.14.4`) & Pydantic Settings (`2.15.0`)
* **Persistence Layer:** SQLAlchemy 2.0 (`2.0.x`) with SQLite file storage (`adaptlearn.db`) in development, dialect-compatible with target PostgreSQL
* **Security & Auth:** PyJWT (`2.8.x`) for HMAC-SHA256 tokens; bcrypt (`4.1.x`) with 12-round salt
* **Test Suite:** Pytest (`8.x` / `9.x`), HTTPX (`0.27.x`+) TestClient

### Frontend Stack
* **Library:** React 19 (`19.3.1`) & React-DOM (`19.3.1`)
* **Build Bundler:** Vite (`8.3.6`+) with `@vitejs/plugin-react`
* **Linter:** Oxlint (`1.90.0`)
* **Styling:** Modern Vanilla CSS3 with CSS custom properties

---

## 6. Existing Module Implementation Status

```
                                Backend Module Status Matrix
 ┌───────────────────────────┬──────────────────────────────────┬──────────────────────┐
 │ Module & Ownership        │ Implemented Components           │ Missing Components   │
 ├───────────────────────────┼──────────────────────────────────┼──────────────────────┤
 │ M1: User & Course         │ Auth API (/auth/register, login) │ Course CRUD & archive│
 │     (Hiba Zulfiqar)       │ UserModel & UserRepository       │ Topic CRUD & order   │
 │                           │ Role-based access control (RBAC) │ Prerequisite DAG     │
 │                           │ Salted bcrypt password hashing   │ Course enrollment API│
 ├───────────────────────────┼──────────────────────────────────┼──────────────────────┤
 │ M2: Quiz & Assessment     │ None                             │ Question bank        │
 │     (Mustajaab Qadri)     │                                  │ Quiz authoring       │
 │                           │                                  │ Attempt grading      │
 ├───────────────────────────┼──────────────────────────────────┼──────────────────────┤
 │ M3: Adaptive Engine       │ MasteryCalculator (sliding N)    │ Automated submission │
 │     (Toqeer Ahmed)        │ MasteryPolicy thresholds         │ trigger from M2      │
 │                           │ RecommendationStrategy (Factory) │                      │
 │                           │ CourseSettingsModel & Repos      │                      │
 ├───────────────────────────┼──────────────────────────────────┼──────────────────────┤
 │ M4: Learning Paths        │ Recommendation engine strategy   │ LearningPathService  │
 │     (Hiba Zulfiqar)       │ (app/engine/recommendation_*)   │ LearningPath router  │
 │                           │                                  │ (/courses/id/path)   │
 │                           │                                  │ LearningPath schemas │
 ├───────────────────────────┼──────────────────────────────────┼──────────────────────┤
 │ M5: Progress Analytics    │ ProgressService & AnalyticsServ  │ Direct real-time quiz│
 │     (Toqeer Ahmed)        │ ProgressRepository & models      │ stream from M2       │
 │                           │ Student progress dashboard       │                      │
 │                           │ Instructor cohort analytics      │                      │
 └───────────────────────────┴──────────────────────────────────┴──────────────────────┘
```

---

## 7. Previous Audit Discrepancies & Resolutions

1. **Workspace Location**: Previous audit recorded the local workspace as empty. *Resolution*: Repository `AdaptLearn` is now cleanly cloned into `C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn`.
2. **Module Allocation**: The Milestone 1 Report title page listed a draft team table. *Resolution*: Section 4.3 (Table 5) of the report, the GitHub README, and `docs/PROJECT_BASELINE.md` confirm that **Hiba Zulfiqar owns M1 and M4**.
3. **Database Schema Duplication**: M5 created `CourseOwnerModel` and `EnrollmentModel` in `app/models/progress.py` to facilitate testing. *Resolution*: M1 will own `CourseModel` and normalized `course_enrollments`, ensuring backward compatibility for M5's queries.
4. **M4 Endpoint Status**: Existing code exposes topic recommendations via M3's `/courses/{id}/recommendations`, but lacks the full sequenced curriculum path endpoint (`GET /courses/{id}/learning-path` per `docs/api.md` §5).

---

## 8. Test Execution Results & Baseline Verification

* **Command Executed:** `python -m pytest` / `.\backend\venv\Scripts\pytest`
* **Execution Status:** **BLOCKED (Environment Dependency Missing)**
* **Exit Code:** `1`
* **Error Output:**
  ```
  C:\Users\hiba2\AppData\Local\Programs\Python\Python314\python.exe: No module named pytest
  ```
* **Root Cause:**
  1. A dedicated Python virtual environment (`backend/venv`) does not yet exist.
  2. The system-level Python interpreter (`Python 3.14.3`) does not have `pytest`, `fastapi`, `pydantic`, `sqlalchemy`, or `httpx` installed in its global site-packages.
* **Documented CI Baseline Reference:**
  * While local execution is pending virtual environment creation, the verified CI execution log in `docs/sqa/test_execution_report.md` on commit `fb4d3c5` confirms:
    * **Total Tests:** 150 automated tests across 14 test modules.
    * **Passed:** 150 passed.
    * **Failed:** 0 failed.
    * **Duration:** 1.34s in CI container.

---

## 9. Environment Problems & Deficiencies

1. **Python Virtual Environment Missing:** `backend/venv` has not been initialized. Running backend tests or starting the Uvicorn server requires creating the virtual environment and installing `backend/requirements.txt`.
2. **Node.js / npm Not Detected in Host PATH:**
   * Running `node --version` and `npm --version` fails with command not found.
   * `README.md` specifies Node.js `v18.0.0+` is required for the React/Vite frontend. Frontend build checks (`npm run build`) cannot execute locally until Node.js is installed or added to the system PATH.
3. **Python Runtime Version Discrepancy:**
   * The host runs `Python 3.14.3`.
   * Project documentation specifies `Python 3.10+` (CI runs Python 3.11). Certain binary wheel packages (such as `bcrypt` or `pydantic-core`) may require a C compiler if pre-built wheels are not available for Python 3.14.

---

## 10. Recommended Next Steps

1. **Safety Confirmation:** The workspace is structurally sound, clean, and completely synchronized with `origin/main` (`fb4d3c5`). Application code has remained untouched.
2. **Action Gate:** Request user approval to:
   * Create a local Python virtual environment in `backend/venv`.
   * Install verified dependencies via `pip install -r backend/requirements.txt`.
   * Run the local test suite to achieve local green verification (150 tests).
3. **Branching Plan:** Once baseline test verification passes, create the official M1 feature branch:
   ```powershell
   git checkout -b feature/m1-course-management
   ```
