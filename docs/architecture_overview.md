# AdaptLearn Architecture Overview

## 1. System Vision
AdaptLearn is an adaptive educational platform designed to personalize learning paths, administer intelligent assessments, and provide actionable analytics for students and educators.

## 2. Technology Stack
- **Frontend**: React (Vite), JavaScript, modern semantic CSS
- **Backend**: FastAPI (Python 3.10+), asynchronous REST API
- **Database (Planned)**: PostgreSQL (relational storage for users, courses, quiz submissions, and analytics)
- **Communication Protocol**: RESTful JSON over HTTP

## 3. Monorepo Organization
The project follows a clean, decoupled monorepo architecture:

```
AdaptLearn/
├── frontend/             # Client-side React application
│   ├── public/           # Static assets
│   ├── src/              # Application components, styles, and logic
│   └── package.json      # Frontend package configuration
├── backend/              # Server-side FastAPI application
│   ├── app/
│   │   ├── api/          # Route handlers partitioned by version
│   │   ├── core/         # Settings, configuration, and exception handlers
│   │   ├── models/       # Database ORM models (planned)
│   │   ├── repositories/ # Data access abstraction layer
│   │   ├── schemas/      # Pydantic request/response validation schemas
│   │   ├── services/     # Business logic and adaptive algorithms
│   │   └── main.py       # Application initialization and middleware
│   ├── tests/            # Automated backend tests (Pytest)
│   └── requirements.txt  # Python package specifications
├── docs/                 # Architectural specifications and documentation
├── tests/                # System-level and cross-module test documentation
├── .env.example          # Environment configuration template
├── .gitignore            # Git exclusion rules
└── README.md             # Project onboarding and developer guide
```

## 4. Module Decomposition & Ownership

| Module | Title | Lead | Focus Area |
| :--- | :--- | :--- | :--- |
| **M1** | User/Course Management | **Hiba** | Identity, authentication (JWT), role-based access (student, instructor, admin), course catalog, and enrollment. |
| **M2** | Quiz & Assessment Engine | **Mustajaab** | Question bank management, dynamic quiz generation, answer submission, scoring, and evaluation logic. |
| **M3** | Adaptive Learning Engine | **Toqeer** | Dynamic difficulty adjustment, knowledge mastery estimation, remediation rules, and recommendation triggers. |
| **M4** | Personalized Learning Paths | **Hiba** | Prerequisite graph processing, curriculum milestone generation, and personalized lesson sequencing. |
| **M5** | Progress Analytics/Dashboard | **Toqeer** | Aggregated student performance metrics, trend analysis, completion tracking, and instructor reporting. |

## 5. Architectural Principles
1. **Separation of Concerns**: UI rendering is strictly separated from business logic, and API routes delegate to modular services.
2. **Schema-First Validation**: All incoming requests and outgoing responses are strictly typed and validated using Pydantic schemas.
3. **Incremental Enhancement**: The foundation is intentionally lightweight to ensure clean evolution across sprints.

