# Contributing to AdaptLearn

Welcome to the **AdaptLearn** semester project for Software Quality Assurance (SE431).  
This document defines our team collaboration standards, Git workflow, testing practices, and cross-module integration rules.

---

## 1. Team & Module Ownership

| Member | Assigned Modules | Focus Scope |
| :--- | :--- | :--- |
| **Hiba Zulfiqar** | **M1**: User/Course Management<br>**M4**: Personalized Learning Paths | User registration, authentication, RBAC, course catalog, prerequisite graphs, and curriculum sequencing. |
| **Mustajaab Ul Fida Qadri** | **M2**: Quiz & Assessment Engine | Question banks, test generation, answer grading, submission processing, and scoring logic. |
| **Toqeer Ahmed** | **M3**: Adaptive Learning Engine<br>**M5**: Progress Analytics & Dashboard | Mastery estimation, dynamic difficulty adjustment, student analytics, dashboard reporting, and metrics. |

---

## 2. Branch Naming Convention

Always create a new branch from an updated `main` branch. Use one of the following prefixes:

| Branch Type | Format | Example |
| :--- | :--- | :--- |
| **Feature** | `feature/<module>-<short-description>` | `feature/m1-user-registration`<br>`feature/m2-quiz-submission`<br>`feature/m3-adaptive-difficulty` |
| **Bug Fix** | `fix/<short-description>` | `fix/cors-header-origins`<br>`fix/quiz-score-calculation` |
| **Documentation** | `docs/<short-description>` | `docs/update-architecture-overview`<br>`docs/api-contracts` |
| **Testing** | `test/<short-description>` | `test/m1-auth-test-suite`<br>`test/m2-quiz-engine-tests` |

### Creating a Feature Branch
```powershell
# 1. Ensure your local main is up to date
git checkout main
git pull origin main

# 2. Create and switch to your feature branch
git checkout -b feature/m1-user-registration
```

---

## 3. Commit Message Convention

We follow a lightweight **Conventional Commits** format. Each commit message must start with a lowercase type prefix followed by a concise description:

```
<type>: <short imperative description>
```

| Type | Purpose | Example |
| :--- | :--- | :--- |
| `feat:` | A new feature or endpoint | `feat(m1): add user registration endpoint and schema` |
| `fix:` | A bug fix | `fix(m2): correct boundary check on quiz timer` |
| `test:` | Adding or updating automated tests | `test(m3): add unit tests for mastery calculation algorithm` |
| `docs:` | Documentation changes only | `docs: update setup guide with powershell execution policy` |
| `chore:` | Routine maintenance, config, dependencies | `chore: update pydantic settings dependency` |
| `refactor:` | Code restructuring without feature or bug changes | `refactor(core): extract cors configuration into separate helper` |

---

## 4. Pull Request (PR) Process

1. **Keep PRs Focused**: One feature or bug fix per PR. Avoid bundling multiple module changes together.
2. **Synchronize with Main**: Before opening a PR, rebase or merge the latest `main` into your feature branch:
   ```powershell
   git checkout feature/m1-user-registration
   git pull origin main
   ```
3. **Open PR against `main`**: Push your branch to GitHub and open a pull request using the provided **PR template**.
4. **Link the Related Issue**: Use keywords like `Closes #12` or `Addresses #15` in the PR description.
5. **Code Review**: At least **one team member** must review and approve the PR before it is merged.
6. **No Broken Builds**: All automated tests (`pytest`) and frontend build checks (`npm run build`) must pass.

---

## 5. Code Review Expectations

When reviewing a teammate's PR:
- **Functionality**: Does the code fulfill the acceptance criteria of the task?
- **Schema & Validation**: Are inputs and outputs validated using Pydantic schemas in `app/schemas/`?
- **Testing**: Are automated unit tests included in `backend/tests/` or `frontend/`?
- **Security Check**: Confirm that **no passwords, tokens, API keys, or `.env` files** are included in the diff.
- **Tone & Communication**: Provide constructive, polite, and specific feedback. Approve once suggestions are addressed.

---

## 6. Local Development Setup (Windows)

### Prerequisites
- **Node.js**: v18.0.0+
- **Python**: 3.10+
- **Git**

### Running the Frontend
```powershell
cd frontend
npm install
npm run dev
```
- Available at: `http://localhost:5173`

### Running the Backend
```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
- Available at: `http://localhost:8000`
- Swagger Docs: `http://localhost:8000/docs`
- Health Endpoint: `http://localhost:8000/health`

---

## 7. How to Run Tests

Before submitting any code for review, run all local verification tests:

### Backend Automated Tests (Pytest)
```powershell
cd backend
.\venv\Scripts\pytest -v
```
All tests must pass (`PASSED`).

### Frontend Production Build Verification
```powershell
cd frontend
npm run build
```
The bundle must compile cleanly without syntax errors or unhandled warnings.

---

## 8. Avoiding Secrets & Sensitive Files

- **Never commit `.env` files**: Real passwords, database connection strings, and secret keys must remain in your local `.env`.
- **Use `.env.example`**: If you introduce a new environment variable, add it with a dummy/placeholder value to `.env.example` and `backend/.env.example`.
- **Check `git status` before committing**: Always inspect modified and untracked files:
  ```powershell
  git status
  ```
  Ensure `node_modules`, `venv`, `dist`, or `.env` are never staged.

---

## 9. Cross-Module Integration Coordination

As AdaptLearn grows, modules will interconnect (e.g., M2 Quiz Engine sends scores to M3 Adaptive Engine, which updates M4 Learning Paths and M5 Analytics).

To avoid merge conflicts and architectural divergence:
1. **Contract-First Communication**: Before implementing inter-module API calls, define the request/response data contracts in `backend/app/schemas/`.
2. **Shared Core Modification**: If you need to modify shared infrastructure (`backend/app/core/`, `backend/app/main.py`, or database configurations), inform the team in group chat before making the change.
3. **Independent Module Routers**: Keep your endpoints isolated within your module router (e.g., `app/api/v1/endpoints/<module>.py`) and mount them through `app/api/v1/api.py`.
4. **Preserve M1 Foundation**: All modules rely on M1 user authentication; coordinate with Hiba when defining authenticated endpoints requiring student/instructor context.

---

## 10. Reporting Bugs & Requesting Features

- Use GitHub Issues to log bugs, feature requests, and sprint tasks.
- Select the appropriate template:
  - **Bug Report**: For unexpected behavior or broken functionality.
  - **Feature Request**: For proposing new capabilities or API endpoints.
  - **Task**: For tracking sprint items and module milestones.

