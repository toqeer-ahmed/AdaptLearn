# AdaptLearn Architecture Overview

> **Status**: Living Architectural Specification  
> **Last Updated**: November 21, 2026  
> **Repository**: [https://github.com/toqeer-ahmed/AdaptLearn](https://github.com/toqeer-ahmed/AdaptLearn)  
> **Baseline Commit**: `5e56bf5` (`chore: initialize AdaptLearn project scaffold`)

---

## 1. System Vision & Context

AdaptLearn is an adaptive education platform created as a university semester project for Software Quality Assurance (SE431). The platform personalize student learning paths, administers automated assessments, dynamically adjusts content difficulty based on demonstrated mastery, and delivers progress analytics to students and instructors.

---

## 2. Current Implementation vs. Planned Target Architecture

To maintain engineering integrity, the system architecture is explicitly divided into what is **currently implemented** and what constitutes the **planned target architecture**.

### 2.1 Currently Implemented Architecture (Sprint 0 Baseline)
- **Monorepo Structure**: Decoupled `frontend/` and `backend/` directories residing in a single repository with independent dependency management.
- **Frontend**: A minimal React 19 application bundled with Vite. It renders a single-page landing interface with project metadata, module ownership summaries, and an interactive connectivity check that calls the backend health endpoint.
- **Backend**: A stateless FastAPI application served by Uvicorn. It includes:
  - Centralized environment configuration via Pydantic Settings (`app/core/config.py`).
  - Standardized JSON exception handlers for HTTP and validation errors (`app/core/errors.py`).
  - Modular API router structure with version prefixing (`/api/v1`).
  - Root and versioned health-check endpoints (`/health` and `/api/v1/health`) returning validated Pydantic schemas.
- **Database & Persistence**: **None currently implemented.** No database server is connected, no database drivers are installed, and no active persistence logic exists.
- **Testing**: Automated backend test suite using `pytest` and `fastapi.testclient.TestClient` verifying endpoint contracts.

### 2.2 Planned Target Architecture (Future Sprints)
- **Frontend**: A multi-view React Single-Page Application (SPA) with client-side routing, protected routes, role-based dashboards (student, instructor, admin), quiz interfaces, and analytics charts.
- **Backend**: A modular, multi-tier asynchronous REST API implementing business logic across five core academic modules.
- **Persistence**: PostgreSQL relational database managed via an ORM and version-controlled database migrations (Alembic).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        PLANNED SYSTEM TOPOLOGY                         │
│                                                                        │
│   ┌────────────────────────┐             ┌─────────────────────────┐   │
│   │   React Frontend       │   REST/HTTP │   FastAPI Backend       │   │
│   │   (Vite, JS, SPA)      │ ──────────> │   (Uvicorn, Python)     │   │
│   │   [Implemented:        │ <────────── │   [Implemented:         │   │
│   │    Landing Page +      │    JSON     │    Health Endpoints,    │   │
│   │    Health Checker]     │             │    CORS, Error Handlers]│   │
│   └────────────────────────┘             └────────────┬────────────┘   │
│                                                       │                │
│                                              Planned  │ Database       │
│                                              ORM Layer│ Driver         │
│                                                       ▼                │
│                                          ┌─────────────────────────┐   │
│                                          │   PostgreSQL Database   │   │
│                                          │   [STATUS: PLANNED,     │   │
│                                          │    NOT YET IMPLEMENTED] │   │
│                                          └─────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Stack Breakdown

| Layer | Component | Current Implementation | Planned Target |
| :--- | :--- | :--- | :--- |
| **Frontend** | Framework & Bundler | React `19.3.1`, Vite `8.3.8` | React SPA with client-side routing |
| | Language & Styling | JavaScript (ESM, JSX), Vanilla CSS3 | Modular CSS, chart libraries for analytics |
| | State & Network | Local component state (`useState`), native `fetch` | Dedicated state store (e.g. Context / Zustand), API client wrapper |
| **Backend** | Web Framework | FastAPI `0.162.5` | Multi-module RESTful API |
| | Server | Uvicorn `0.54.0` | Uvicorn production server |
| | Validation | Pydantic v2 (`2.14.4`), Pydantic Settings (`2.15.0`) | Comprehensive request/response DTO schemas |
| | Error Handling | Centralized JSON handlers for 4xx/5xx | Domain-specific exception hierarchy |
| **Persistence** | Database Engine | **None** (Stateless in-memory execution) | PostgreSQL (Relational) |
| | ORM / Query Layer | **None** (Package directories only) | SQLAlchemy 2.0 or SQLModel |
| | Migrations | **None** | Alembic schema migrations |
| **Testing** | Test Framework | Pytest `9.2.0`, HTTPX `0.28.1` | Unit, integration, and E2E test suites |

> [!IMPORTANT]
> **PostgreSQL Integration Status**: PostgreSQL is the planned relational database for AdaptLearn, but it is **not yet integrated**. No database tables, connection pools, or schema migrations currently exist in the codebase.

---

## 4. Planned Architectural Layers & Responsibilities

The AdaptLearn backend is organized into clear directory packages that establish the foundation for a layered architecture. The responsibilities of each planned layer are defined below:

```
backend/app/
├── api/             --> [Layer 1: API / Presentation Layer]
├── core/            --> [Cross-Cutting: Configuration, Security, Errors]
├── schemas/         --> [Data Contracts: Pydantic Validation Schemas]
├── services/        --> [Layer 2: Business Logic / Domain Services]
├── repositories/    --> [Layer 3: Data Access / Persistence Abstraction]
└── models/          --> [Layer 4: Relational Domain Models]
```

### 1. Presentation & API Layer (`app/api/`)
- **Status**: Implemented for health check; planned for module routers.
- **Responsibilities**:
  - Exposes RESTful HTTP routes partitioned by version (`api/v1/`).
  - Validates request parameters and payloads against Pydantic schemas.
  - Delegates all business processing directly to the service layer.
  - Formats and returns standardized HTTP responses and status codes.
  - Does **not** execute direct database queries or implement business algorithms.

### 2. Service Layer (`app/services/`)
- **Status**: Package initialized (`__init__.py` with docstrings); domain implementations planned.
- **Responsibilities**:
  - Contains core domain logic, algorithms, and business workflows.
  - Coordinates multi-step operations (e.g., grading a quiz, calculating mastery, generating a learning trajectory).
  - Remains decoupled from HTTP request objects and database drivers.
  - Interacts exclusively with repositories for data persistence and retrieval.

### 3. Repository Layer (`app/repositories/`)
- **Status**: Package initialized (`__init__.py` with docstrings); data access methods planned.
- **Responsibilities**:
  - Encapsulates database queries (CRUD operations) for individual entities.
  - Shields the service layer from ORM and database-specific query syntax.
  - Enables predictable unit testing by allowing repositories to be mocked.

### 4. Models Layer (`app/models/`)
- **Status**: Package initialized (`__init__.py` with docstrings); ORM entities planned.
- **Responsibilities**:
  - Defines database schema entities using an ORM (SQLAlchemy / SQLModel).
  - Specifies table structures, column constraints, indexes, foreign keys, and relationships.
  - Maps relational records to Python objects for repository interactions.

### 5. Schemas Layer (`app/schemas/`)
- **Status**: Implemented for health check (`HealthResponse`); planned for domain DTOs.
- **Responsibilities**:
  - Defines Pydantic data models for request validation and response serialization.
  - Enforces strict input validation and sanitization at the API boundary.
  - Decouples external API representations from internal database models.

### 6. Database Layer (PostgreSQL)
- **Status**: Planned (not yet connected).
- **Responsibilities**:
  - Provides ACID-compliant persistent relational storage.
  - Enforces referential integrity through foreign keys and unique constraints.

---

## 5. Team Modules & Domain Ownership

The planned functionality of AdaptLearn is partitioned across five distinct modules, owned by the three team members:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        ADAPTLEARN MODULE BOUNDARIES                    │
│                                                                        │
│   ┌──────────────────────────────┐   ┌──────────────────────────────┐  │
│   │ M1: User & Course Management │   │ M4: Personalized Learning    │  │
│   │ Lead: Hiba                   │   │     Paths                    │  │
│   │ Focus: Auth, Roles, Courses  │   │ Lead: Hiba                   │  │
│   └──────────────┬───────────────┘   │ Focus: Path Sequencing       │  │
│                  │                   └──────────────▲───────────────┘  │
│                  ▼                                  │                  │
│   ┌──────────────────────────────┐                  │                  │
│   │ M2: Quiz & Assessment Engine │                  │ Adaptive         │
│   │ Lead: Mustajaab              │                  │ Triggers         │
│   │ Focus: Questions, Grading    │                  │                  │
│   └──────────────┬───────────────┘                  │                  │
│                  │                                  │                  │
│                  ▼ Assessment Results               │                  │
│   ┌──────────────────────────────┐   ┌──────────────┴───────────────┐  │
│   │ M3: Adaptive Learning Engine │──>│ M5: Progress Analytics &     │  │
│   │ Lead: Toqeer                 │   │     Dashboard                │  │
│   │ Focus: Mastery, Difficulty   │   │ Lead: Toqeer                 │  │
│   └──────────────────────────────┘   │ Focus: Reports, Metrics      │  │
│                                      └──────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

| Module | Title | Lead | Scope & Planned Responsibilities |
| :--- | :--- | :--- | :--- |
| **M1** | User & Course Management | **Hiba** | User registration, authentication, role-based access control (Student, Instructor, Admin), profile management, course catalog, and enrollment. |
| **M2** | Quiz & Assessment Engine | **Mustajaab** | Question bank repository, quiz generation, answer submission processing, automated scoring, and question feedback. |
| **M3** | Adaptive Learning Engine | **Toqeer** | Dynamic difficulty adjustment algorithms, student mastery estimation, concept remediation triggers, and adaptive recommendation rules. |
| **M4** | Personalized Learning Paths | **Hiba** | Prerequisite dependency graph processing, customized curriculum sequencing, milestone tracking, and pacing guidance. |
| **M5** | Progress Analytics / Dashboard | **Toqeer** | Aggregation of performance metrics, mastery visual reporting, student progression tracking, and instructor analytical insights. |

---

## 6. Request-Response Flow: Current vs. Target

### 6.1 Currently Implemented Flow (Health Check Example)

The health check represents the only live request-response flow currently implemented in the codebase:

```
User (Browser)
    │
    ▼
[React UI: App.jsx] ── User clicks "Check /health Endpoint"
    │
    ▼ HTTP GET http://localhost:8000/health
[Uvicorn ASGI Server]
    │
    ▼ Passes request to FastAPI app instance (app/main.py)
[CORSMiddleware] ── Evaluates Origin header against settings.BACKEND_CORS_ORIGINS
    │
    ▼ Route Match: GET /health
[Endpoint Handler: root_health() in app/main.py or get_health() in health.py]
    │
    ▼ Instantiates Pydantic HealthResponse schema
[Schema: HealthResponse] ── Validates status, project, version, environment
    │
    ▼ Serializes to JSON with HTTP 200 OK
[HTTP Response: 200 OK] ── {"status":"healthy","project":"AdaptLearn","version":"0.1.0","environment":"development"}
    │
    ▼
[React UI: App.jsx] ── Updates healthStatus state and renders status card
```

### 6.2 Planned Target Flow (Example: Assessment Submission)

Once business modules and the database are implemented, requests will flow across all architectural layers:

```
React Client (Quiz View)
    │
    ▼ HTTP POST /api/v1/quizzes/{id}/submit (with JWT in Authorization header)
FastAPI Router (app/api/v1/endpoints/quizzes.py)
    │ ── Validates JWT & request payload against SubmissionSchema
    ▼
Quiz Service (app/services/quiz_service.py)
    │ ── Evaluates answers and calculates score
    ▼
Adaptive Engine Service (app/services/adaptive_service.py)
    │ ── Recalculates mastery score and adjusts difficulty level
    ▼
Quiz Repository (app/repositories/quiz_repository.py)
    │ ── Persists submission record and scores
    ▼
Database Layer (PostgreSQL)
    │ ── Executes SQL transactions, maintains referential integrity
    ▼
HTTP Response (200 OK with graded results and updated path recommendations)
```

---

## 7. Current Design Principles

The existing codebase adheres to fundamental engineering principles without introducing premature abstractions:

1. **Decoupled Architecture**: Frontend and backend are completely separate codebases, interacting solely over HTTP/JSON interfaces.
2. **Schema-First Validation**: All data traversing the API boundary is strictly validated and serialized using Pydantic v2 schemas (`app/schemas/`), preventing malformed payloads from reaching internal logic.
3. **Environment-Driven Configuration**: Configuration parameters are managed centrally via `BaseSettings` (`app/core/config.py`), reading from environment variables or `.env` files with secure defaults.
4. **Standardized Error Handling**: Centralized exception handlers in `app/core/errors.py` ensure client responses follow a predictable JSON schema during errors.
5. **No Premature Overengineering**: Complex design patterns (such as Strategy, Factory, Observer, or full Repository classes) are **not currently implemented** because no business features require them yet. Starter directories contain only package markers and docstrings to guide future development.

---

## 8. Architectural Decisions Pending Confirmation

The following design decisions must be confirmed through upcoming M1 and M2 requirements documents before implementation begins:

1. **ORM & Migration Framework**:
   - *Option A*: **SQLAlchemy 2.0** (Standard async ORM with explicit model-to-schema mapping).
   - *Option B*: **SQLModel** (Combines SQLAlchemy and Pydantic into unified models).
   - *Decision Point*: Evaluate whether model unification simplifies development for the team or if strict separation of ORM and DTO schemas is preferred for SQA grading.
2. **Database Development Setup**:
   - *Option A*: Native local PostgreSQL service on Windows.
   - *Option B*: Docker Compose container running PostgreSQL.
   - *Decision Point*: Confirm team environment consistency and whether Docker is required or optional for Sprint 1.
3. **Authentication Strategy (M1)**:
   - Token mechanism: JSON Web Tokens (JWT) signed with HMAC-SHA256 (`PyJWT` or `python-jose`).
   - Token transport: HTTP-only secure cookies vs. `Authorization: Bearer <token>` header.
   - Password hashing: `bcrypt` vs. `argon2` via `passlib`.
4. **Assessment Engine Architecture (M2)**:
   - Question structure: JSON-based flexible question payloads vs. discrete relational question/option tables.
   - Grading pipeline: Synchronous in-request grading vs. asynchronous background task execution.
5. **Client-Side Routing & State Management**:
   - Routing library selection: `react-router-dom` v6/v7.
   - Client state management: React built-in Context API vs. lightweight external store (`zustand`).
