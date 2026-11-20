# Verification and Validation (V&V) Plan

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)  
> **Standard Reference**: IEEE Std 1012 (Software Verification and Validation)

---

## 1. Objectives

- **Verification ("Are we building the product right?")**: Ensure each software artifact (requirements, design, source code, tests) complies with architectural constraints, coding standards, and upstream specifications.
- **Validation ("Are we building the right product?")**: Ensure the delivered application satisfies end-user needs, semester project rubric criteria, and learning trajectory requirements.

---

## 2. Scope

### In-Scope Modules
- **Core Infrastructure**: Configuration, CORS, error handling, Docker/deployment.
- **Module 1 (M1)**: User registration, authentication, RBAC, and course management (Hiba).
- **Module 2 (M2)**: Question banks, dynamic quiz generation, grading, and scoring (Mustajaab).
- **Module 3 (M3)**: Mastery score calculation, difficulty adjustment, and adaptive engine (Toqeer).
- **Module 4 (M4)**: Prerequisite graphs, learning paths, and curriculum sequencing (Hiba).
- **Module 5 (M5)**: Progress tracking, analytics aggregation, and dashboard reporting (Toqeer).

---

## 3. Verification Methods

| Method | Application Area | Tool / Mechanism | Frequency |
| :--- | :--- | :--- | :--- |
| **Peer Code Reviews** | All Pull Requests | GitHub PR Template | Every PR before merge |
| **Formal Technical Inspections** | Architecture, design specs | Fagan Inspection Process | Milestone deliverables |
| **Static Code Analysis** | Backend & Frontend code | Oxlint, Flake8, Ruff | Local and CI pipeline |
| **Unit Testing** | Services, algorithms, schemas | Pytest, React Testing Library | Every build |
| **API Contract Verification** | REST endpoints | Pydantic Schema validations | Automated on test suite |

---

## 4. Validation Methods

| Method | Focus | Validation Mechanism |
| :--- | :--- | :--- |
| **End-to-End User Journey Tests** | Student quiz taking and learning path progression | Simulated user flows |
| **Rubric Compliance Audits** | SE431 course requirements | Traceability Matrix audits |
| **Adaptive Logic Scenarios** | Student difficulty escalation / remediation | Synthetic student performance profiles |

---

## 5. Roles & Responsibilities

| Team Member | Verification & Validation Responsibility |
| :--- | :--- |
| **Hiba Zulfiqar** | Lead validation for M1 User/Course management and M4 Learning Paths; peer review M2 and M3 PRs. |
| **Mustajaab Ul Fida Qadri** | Lead validation for M2 Quiz & Assessment Engine; peer review M1 and M5 PRs. |
| **Toqeer Ahmed** | Lead validation for M3 Adaptive Engine and M5 Analytics Dashboard; manage CI/CD pipeline and SQA reports. |

---

## 6. Entry and Exit Criteria

### Entry Criteria for Testing Phases
1. Code compiles without errors (`npm run build` passes).
2. Backend starts cleanly and passes basic health check (`/health` returns 200).
3. Pull Request has no merge conflicts with `main`.

### Exit Criteria for Milestone Completion
1. 100% of planned test cases executed.
2. 0 Critical (S1) or Major (S2) unresolved defects in Defect Log.
3. All requirements mapped in RTM marked as **Verified**.
4. Formal inspection report approved and signed off.

---

## 7. Evidence Requirements
All V&V activities must produce tangible evidence stored in `docs/sqa/`:
- Test execution outputs (`test_execution_report.md`).
- Inspection logs and sign-offs (`formal_inspection_report.md`).
- Static analysis logs (`static_analysis_report.md`).
- Verified requirement entries (`requirements_traceability_matrix.md`).

---

## 8. Requirement Mapping Process
1. Each functional requirement is assigned a permanent identifier (`REQ-MX-YYY`).
2. Test cases are developed with matching tags (`TC-MX-YYY`).
3. Successful test runs update the RTM status to **Verified** with links to test execution reports.

