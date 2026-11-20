# AdaptLearn

> **Adaptive Education Platform**  
> Semester Project for Software Quality Assurance (SE431)

AdaptLearn is an intelligent, personalized education platform designed to adapt learning materials, quizzes, and progression paths to individual student capabilities while delivering actionable mastery analytics.

---

## Technology Stack

- **Frontend**: React (Vite), JavaScript, Vanilla CSS (Modern, responsive, beginner-friendly)
- **Backend**: FastAPI (Python 3.10+), Pydantic v2, Uvicorn
- **Database (Planned)**: PostgreSQL
- **Architecture**: Monorepo with decoupled frontend and backend communicating via RESTful JSON APIs
- **Testing**: Pytest (Backend)

---

## Team & Module Ownership

| Module | Title | Lead | Scope |
| :--- | :--- | :--- | :--- |
| **M1** | User & Course Management | **Hiba** | User registration, authentication, RBAC, course creation & enrollment. |
| **M2** | Quiz & Assessment Engine | **Mustajaab** | Question banks, test generation, grading, submission processing. |
| **M3** | Adaptive Learning Engine | **Toqeer** | Mastery estimation, difficulty adjustment, remediation logic. |
| **M4** | Personalized Learning Paths | **Hiba** | Adaptive curriculum sequencing, prerequisite graphs, milestone tracking. |
| **M5** | Progress Analytics / Dashboard | **Toqeer** | Student performance visualization, mastery reports, instructor insights. |

---

## Project Structure

```
AdaptLearn/
├── frontend/               # React client application (Vite)
│   ├── public/             # Static web assets
│   ├── src/
│   │   ├── assets/         # Images, icons
│   │   ├── App.jsx         # Starter landing page & health check
│   │   ├── App.css         # Application component styles
│   │   ├── index.css       # Global design variables & reset
│   │   └── main.jsx        # React root mounting
│   ├── index.html          # HTML entry template
│   ├── package.json        # Node dependencies and scripts
│   └── vite.config.js      # Vite build configuration
├── backend/                # FastAPI application
│   ├── app/
│   │   ├── api/            # API routers (v1 endpoints)
│   │   ├── core/           # Configuration, settings & error handling
│   │   ├── models/         # Database models (for future ORM integration)
│   │   ├── repositories/   # Data access abstraction layer
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # Core business logic & adaptive engine
│   │   └── main.py         # Application entry point & CORS
│   ├── tests/              # Backend test suite (pytest)
│   ├── .env.example        # Backend environment template
│   └── requirements.txt    # Python dependencies
├── docs/                   # Documentation and architecture diagrams
│   └── architecture_overview.md
├── tests/                  # Integration testing overview and plans
│   └── README.md
├── .env.example            # Root environment variable template
├── .gitignore              # Git ignore rules for Python, Node, & IDEs
└── README.md               # Main project documentation
```

---

## Prerequisites

Before starting, ensure the following are installed on your machine:
- **Node.js**: `v18.0.0` or higher ([Download Node.js](https://nodejs.org/))
- **Python**: `3.10` or higher ([Download Python](https://www.python.org/))
- **Git**: ([Download Git](https://git-scm.com/))

---

## Local Setup & Run Guide (Windows)

### 1. Frontend Setup

1. Open PowerShell or Command Prompt and navigate to `frontend`:
   ```powershell
   cd frontend
   ```
2. Install npm dependencies:
   ```powershell
   npm install
   ```
3. Start the development server:
   ```powershell
   npm run dev
   ```
4. Open your browser and navigate to:
   ```
   http://localhost:5173
   ```

---

### 2. Backend Setup

1. Open a new PowerShell terminal and navigate to `backend`:
   ```powershell
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
   *(If script execution is disabled in PowerShell, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

3. Install the dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
4. Start the FastAPI development server:
   ```powershell
   uvicorn app.main:app --reload --port 8000
   ```
5. The API is now running at:
   ```
   http://localhost:8000
   ```

---

## Health Check Verification

You can verify that the backend is running properly through any of the following methods:

### 1. Web Browser
- Root Health Check: [http://localhost:8000/health](http://localhost:8000/health)
- API V1 Health Check: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- Interactive Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
- Interactive ReDoc Documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

Expected JSON Response:
```json
{
  "status": "healthy",
  "project": "AdaptLearn",
  "version": "0.1.0",
  "environment": "development"
}
```

### 2. PowerShell Command Line
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

### 3. Automated Pytest Suite
Run the automated backend tests:
```powershell
cd backend
.\venv\Scripts\pytest
```

### 4. Frontend UI Button
Open [http://localhost:5173](http://localhost:5173) in your browser and click the **"Check /health Endpoint"** button to confirm live frontend-to-backend communication.

---

## Git Workflow & Best Practices

- Work on feature branches corresponding to your module:
  - `feature/m1-user-auth`
  - `feature/m2-quiz-engine`
  - `feature/m3-adaptive-engine`
  - `feature/m4-learning-paths`
  - `feature/m5-analytics-dashboard`
- Never commit secrets or `.env` files.
- Always run the tests before submitting pull requests.

