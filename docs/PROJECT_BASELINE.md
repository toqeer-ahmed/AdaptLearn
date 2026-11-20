# AdaptLearn Project Baseline

> **Document Version**: 1.0.0  
> **Date**: November 20, 2026  
> **Repository**: [https://github.com/toqeer-ahmed/AdaptLearn](https://github.com/toqeer-ahmed/AdaptLearn)  
> **Initial Commit**: `5e56bf57a0a69741d569089657fdd84f0c13c352` (`5e56bf5 chore: initialize AdaptLearn project scaffold`)  
> **Current Branch**: `main`

---

## 1. Project Overview

AdaptLearn is an adaptive education platform created as a semester project for Software Quality Assurance (SE431). The system aims to provide personalized learning trajectories, dynamic quiz assessments, adaptive difficulty adjustments, and actionable progress analytics.

The project is structured as a decoupled monorepo containing a React frontend and a FastAPI backend, designed to communicate over a RESTful JSON API.

### Team Module Allocation

| Module | Title | Lead | Scope |
| :--- | :--- | :--- | :--- |
| **M1** | User & Course Management | **Hiba** | Identity, authentication, role-based authorization, and course management. |
| **M2** | Quiz & Assessment Engine | **Mustajaab** | Question bank management, dynamic assessment generation, and grading. |
| **M3** | Adaptive Learning Engine | **Toqeer** | Mastery modeling, adaptive difficulty rules, and remediation recommendations. |
| **M4** | Personalized Learning Paths | **Hiba** | Prerequisite graphs, curriculum sequencing, and milestone tracking. |
| **M5** | Progress Analytics / Dashboard | **Toqeer** | Mastery metrics, student progress tracking, and performance reporting. |

---

## 2. Current Technology Stack

### Frontend
- **Framework**: React 19 (`19.3.1`)
- **Build Tool / Bundler**: Vite (`8.3.8`)
- **Plugin**: `@vitejs/plugin-react` (`6.1.2`)
- **Language**: JavaScript (ES Modules, standard JSX; TypeScript not enabled)
- **Styling**: Vanilla CSS3 (Custom responsive design, CSS custom properties / variables)
- **Linter**: Oxlint (`oxlintrc.json`)

### Backend
- **Framework**: FastAPI (`0.162.5`)
- **ASGI Server**: Uvicorn (`0.54.0` with standard extras)
- **Validation & Typing**: Pydantic v2 (`2.14.4`)
- **Settings Management**: Pydantic Settings (`2.15.0`)
- **Environment Management**: Python-dotenv (`1.2.4`)
- **HTTP Client**: HTTPX (`0.28.1`)
- **Testing Framework**: Pytest (`9.2.0`)
- **Python Version**: Python 3.10.11

### Planned / Not Yet Installed
- **Database**: PostgreSQL (relational database engine)
- **ORM / Query Builder**: SQLAlchemy 2.0 / SQLModel (pending decision)
- **Migration Tool**: Alembic (pending decision)
- **Frontend Routing**: React Router (pending decision)

---

## 3. Actual Folder Structure

The repository filesystem currently contains the following files and directories:

```
AdaptLearn/
├── .env.example                                # Root environment variable template
├── .gitignore                                  # Git exclusion rules for Python, Node, env, IDE
├── README.md                                   # Project introduction, setup and run instructions
├── Team.pdf                                    # Course team allocation document (preserved)
├── docs/
│   ├── architecture_overview.md                # High-level architecture specification
│   └── PROJECT_BASELINE.md                     # This baseline documentation file
├── tests/
│   └── README.md                               # High-level integration and testing strategy
├── backend/
│   ├── .env.example                            # Backend-specific environment variable template
│   ├── requirements.txt                        # Python dependencies
│   ├── app/
│   │   ├── __init__.py                         # Application package root
│   │   ├── main.py                             # FastAPI app instance, CORS, routes & endpoints
│   │   ├── api/
│   │   │   ├── __init__.py                     # API package marker
│   │   │   └── v1/
│   │   │       ├── __init__.py                 # API v1 package marker
│   │   │       ├── api.py                      # Central v1 router mounting endpoints
│   │   │       └── endpoints/
│   │   │           ├── __init__.py             # Endpoints package marker
│   │   │           └── health.py               # GET /api/v1/health endpoint definition
│   │   ├── core/
│   │   │   ├── __init__.py                     # Core package marker
│   │   │   ├── config.py                       # Pydantic Settings loader (env-aware)
│   │   │   └── errors.py                       # Standardized JSON error handlers
│   │   ├── models/
│   │   │   └── __init__.py                     # Placeholder docstring for future DB ORM models
│   │   ├── repositories/
│   │   │   └── __init__.py                     # Placeholder docstring for data access layer
│   │   ├── schemas/
│   │   │   ├── __init__.py                     # Schemas package marker
│   │   │   └── health.py                       # Pydantic HealthResponse schema
│   │   └── services/
│   │       └── __init__.py                     # Placeholder docstring for business logic layer
│   └── tests/
│       ├── __init__.py                         # Tests package marker
│       └── test_health.py                      # Pytest tests for health and root endpoints
└── frontend/
    ├── .gitignore                              # Frontend-specific exclusion rules
    ├── .oxlintrc.json                          # Oxlint configuration
    ├── index.html                              # HTML template with page title
    ├── package.json                            # Node dependencies and scripts
    ├── package-lock.json                       # Exact lockfile for frontend dependencies
    ├── README.md                               # Vite/React boilerplate readme
    ├── vite.config.js                          # Vite configuration using @vitejs/plugin-react
    ├── public/
    │   ├── favicon.svg                         # Vite default favicon
    │   └── icons.svg                           # SVG symbols
    └── src/
        ├── App.css                             # Layout and component CSS styles
        ├── App.jsx                             # AdaptLearn starter landing page component
        ├── index.css                           # Global CSS variables and resets
        ├── main.jsx                            # React root render entry
        └── assets/
            ├── hero.png                        # Hero image asset
            ├── react.svg                       # React SVG asset
            └── vite.svg                        # Vite SVG asset
```

---

## 4. Frontend Implementation Currently Available

The frontend is a single-page React starter application with no routing:

- **`src/main.jsx`**: Bootstraps the React DOM using `ReactDOM.createRoot` and renders `<App />` within `React.StrictMode`.
- **`src/App.jsx`**:
  - Displays the project branding: **AdaptLearn — Adaptive Education Platform**.
  - Displays a sprint badge: **Sprint 0: Project Initialized**.
  - Summarizes the planned modules (M1 through M5) with assigned team leads.
  - Features an interactive **"Backend Connectivity Status"** card with a **"Check /health Endpoint"** button:
    - Queries `GET http://localhost:8000/health`.
    - Handles asynchronous loading, success, and error states.
    - Renders the returned JSON payload on success or displays an actionable error message if the backend is unreachable.
- **`src/App.css` & `src/index.css`**:
  - Implements custom CSS variables (`--primary`, `--bg-color`, `--card-bg`, etc.).
  - Responsive grid layout for module cards.
  - Zero external UI component libraries installed.

---

## 5. Backend Implementation Currently Available

The backend is an asynchronous FastAPI application organized into modular packages:

- **`app/main.py`**:
  - Instantiates `FastAPI` with OpenAPI metadata (`title="AdaptLearn"`, `version="0.1.0"`).
  - Mounts `CORSMiddleware` with configurable allowed origins (`settings.BACKEND_CORS_ORIGINS`).
  - Registers standardized exception handlers via `setup_exception_handlers(app)`.
  - Exposes root-level convenience endpoints (`/` and `/health`).
  - Mounts the versioned API router at `/api/v1`.
- **`app/core/config.py`**:
  - Implements `Settings(BaseSettings)` using `pydantic-settings`.
  - Configures default parameters: `PROJECT_NAME="AdaptLearn"`, `ENVIRONMENT="development"`, `DEBUG=True`, `API_V1_PREFIX="/api/v1"`, `BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]`.
  - Parses CORS origins whether provided as a JSON array string or a comma-separated list.
  - Reads `.env` automatically if present, with fallbacks to system environment variables and built-in defaults.
- **`app/core/errors.py`**:
  - Intercepts `StarletteHTTPException` to return a uniform `{ "success": false, "error": { "code": ..., "message": ... } }` structure.
  - Intercepts `RequestValidationError` (422) to return standardized validation error details.
- **`app/schemas/health.py`**:
  - Defines `HealthResponse(BaseModel)` with typed fields: `status: str`, `project: str`, `version: str`, `environment: str`.
- **`app/api/v1/api.py` & `endpoints/health.py`**:
  - Version 1 router registering `/health` under tag `"Health"`.
  - Contains documented extension points for future module routers (users, courses, quizzes, adaptive, learning-paths, analytics).
- **Module Architecture Placeholders**:
  - `app/models/__init__.py`, `app/repositories/__init__.py`, `app/services/__init__.py` exist with clear architectural docstrings explaining their planned responsibilities.

---

## 6. Existing API Endpoints

| HTTP Method | Path | Response Model | Description | Status |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | `dict` | API welcome message, documentation links, and operational status. | Active |
| `GET` | `/health` | `HealthResponse` | Root-level health check endpoint. | Active |
| `GET` | `/api/v1/health` | `HealthResponse` | Versioned V1 health check endpoint. | Active |
| `GET` | `/docs` | HTML | Interactive Swagger UI documentation. | Active |
| `GET` | `/redoc` | HTML | Interactive ReDoc documentation. | Active |
| `GET` | `/openapi.json` | JSON | Auto-generated OpenAPI 3.1.0 schema specification. | Active |

### Health Check Response Example
```json
{
  "status": "healthy",
  "project": "AdaptLearn",
  "version": "0.1.0",
  "environment": "development"
}
```

---

## 7. Existing Automated Tests

The test suite is located in `backend/tests/` and uses `pytest` with `fastapi.testclient.TestClient`.

### Test File: `backend/tests/test_health.py`
- `test_root_health_check`: Calls `GET /health`, asserts HTTP status `200`, verifies `status == "healthy"`, and confirms presence of `version` and `project`.
- `test_v1_health_check`: Calls `GET /api/v1/health`, asserts HTTP status `200`, verifies `status == "healthy"` and `project == "AdaptLearn"`.
- `test_root_welcome`: Calls `GET /`, asserts HTTP status `200`, verifies `project == "AdaptLearn"` and `status == "operational"`.

### Test Execution Command
```powershell
cd backend
.\venv\Scripts\pytest -v
```
**Verification Outcome**: 3 passed in 0.84s (0 failures).

---

## 8. Actual Environment Configuration

### Configuration Mechanism
- Configuration is loaded via `backend/app/core/config.py` using `pydantic-settings`.
- Values are read from environment variables or an optional `.env` file located in `backend/` or the root workspace.
- Defaults are coded to permit zero-configuration local execution out of the box.

### Configuration Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `PROJECT_NAME` | `"AdaptLearn"` | Application display name. |
| `ENVIRONMENT` | `"development"` | Current runtime environment (`development`, `staging`, `production`). |
| `DEBUG` | `True` | Debug mode toggle. |
| `API_V1_PREFIX` | `"/api/v1"` | URL path prefix for version 1 API endpoints. |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:5173", "http://127.0.0.1:5173"]` | Permitted client origins for CORS middleware. |

### Environment Files
- `.env.example` (at repository root): Committed template.
- `backend/.env.example`: Committed template for backend developers.
- `.env`: **Excluded** from Git via `.gitignore`. No active secret files currently exist on disk.

---

## 9. Current Git Branch and Initial Commit

- **Repository**: [https://github.com/toqeer-ahmed/AdaptLearn](https://github.com/toqeer-ahmed/AdaptLearn)
- **Active Branch**: `main`
- **Initial Commit Hash**: `5e56bf57a0a69741d569089657fdd84f0c13c352`
- **Short Hash**: `5e56bf5`
- **Commit Message**: `chore: initialize AdaptLearn project scaffold`
- **Sync Status**: Local `main` and remote `origin/main` are identical and synchronized.

---

## 10. Implementation Status

### Implemented and Verified
- [x] Monorepo folder structure (`frontend/`, `backend/`, `docs/`, `tests/`).
- [x] Root Git repository initialization and connection to GitHub remote.
- [x] Git ignore configurations covering Python venv, Node modules, build dist, IDE files, and secrets.
- [x] React 19 + Vite frontend scaffold with production build passing (`vite build`).
- [x] Frontend landing page with project branding and interactive `/health` connectivity checker.
- [x] FastAPI backend application with CORS middleware and standardized exception handlers.
- [x] Pydantic Settings configuration system with `.env.example` templates.
- [x] Root `/health` and versioned `/api/v1/health` endpoints returning operational JSON.
- [x] Root welcome `/` endpoint and OpenAPI documentation (`/docs`, `/redoc`).
- [x] Automated test suite in `backend/tests/test_health.py` passing 3/3 tests via `pytest`.
- [x] Live HTTP communication between Vite frontend and FastAPI backend verified locally.
- [x] Initial commit (`5e56bf5`) pushed to GitHub remote `origin/main`.

### Implemented but Not Fully Verified
- [ ] Cross-browser UI rendering validation (tested on Chrome/modern browser engine; full multi-browser test matrix pending).
- [ ] End-to-end frontend automated testing (Playwright or Cypress not yet introduced).

### Planned but Not Implemented
- [ ] PostgreSQL database connection and connection pool setup.
- [ ] Database ORM models (`backend/app/models/`).
- [ ] Database schema migrations using Alembic.
- [ ] Data repository abstraction implementations (`backend/app/repositories/`).
- [ ] Module 1: User authentication, registration, JWT tokens, RBAC, and course management (Hiba).
- [ ] Module 2: Question bank storage, quiz generation, grading, and submission processing (Mustajaab).
- [ ] Module 3: Adaptive algorithm, mastery score calculation, dynamic difficulty adjustments (Toqeer).
- [ ] Module 4: Learning path graphs, prerequisite checking, milestone tracking (Hiba).
- [ ] Module 5: Student progress tracking, mastery metric calculation, and dashboard analytics (Toqeer).
- [ ] Frontend client-side routing (React Router).
- [ ] Frontend authenticated state and dashboard UI views.
- [ ] CI/CD pipeline automation (GitHub Actions).

### Pending Architectural Decisions
1. **ORM Framework Selection**:
   - Decision pending between **SQLAlchemy 2.0 (async/sync)** and **SQLModel** (which merges Pydantic schemas with SQLAlchemy models).
2. **Database Execution Strategy for Development**:
   - Decision pending on whether local PostgreSQL will run via a native Windows service or containerized via Docker / Docker Compose.
3. **Authentication Mechanism**:
   - Password hashing algorithm (e.g. `passlib` with `bcrypt` or `argon2`) and JWT token lifecycle (access tokens, refresh tokens, cookie vs. Authorization header).
4. **Client State Management**:
   - Decision pending whether React context/hooks are sufficient for upcoming sprints or if a dedicated state store (Zustand) is needed.

---

## 11. Current Project Limitations

1. **Stateless Backend**: The API holds no persistent state; stopping the server resets all memory. No database queries can currently execute.
2. **Single-View Frontend**: The frontend only consists of a landing page and health checker; no navigation, auth protection, or role views exist.
3. **Mock Dependencies**: Models, repositories, and services directories contain only docstrings and package initializers without logic.
4. **No Automated CI**: Automated tests currently run locally via terminal commands; continuous integration checks on pull requests are not yet established.

