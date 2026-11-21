# Software Risk Register

> **Document Status**: Active / Updated Baseline<br>
> **Project**: AdaptLearn<br>
> **Course**: Software Quality Assurance (SE431)<br>
> **Last Evaluated**: Sprint 2 / Milestone 2 Transition<br>
> **Evaluation Basis**: Real Implementation Status (150 Passing Automated Tests)

---

## 1. Risk Evaluation Criteria

### Probability Scale
- **High (H)**: Greater than 70% probability of occurrence.
- **Medium (M)**: 30% to 70% probability of occurrence.
- **Low (L)**: Less than 30% probability of occurrence.

### Impact Scale
- **High (H)**: Severe disruption to project schedule, core architecture, or grading criteria.
- **Medium (M)**: Moderate disruption requiring rework or alternative implementation.
- **Low (L)**: Minor inconvenience with negligible impact on core deliverables.

### Risk Level Matrix

| Probability \ Impact | Low (L) | Medium (M) | High (H) |
| :---: | :---: | :---: | :---: |
| **High (H)** | Medium | High | **Critical** |
| **Medium (M)** | Low | Medium | **High** |
| **Low (L)** | Low | Low | **Medium** |

---

## 2. Risk Log Table

| Risk ID | Description & Rationale | Probability | Impact | Risk Level | Mitigation Strategy | Owner | Status |
| :---: | :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| **RSK-001** | **Database environment inconsistency across team machines**<br>_Rationale_: Unit and integration tests currently execute successfully against isolated in-memory repository doubles. When transitioning to persistent PostgreSQL (required for NFR-01, NFR-08, NFR-09, and NFR-21), differing local PostgreSQL configurations or Docker daemon availability across Windows/macOS could cause environment drift. | Medium | High | **Medium** | Implemented SQLAlchemy 2.0 ORM with local SQLite file-backed repository storage (`adaptlearn.db`) in Task COMMIT-04, eliminating Docker requirement for local development/testing while maintaining dialect-agnostic PostgreSQL compatibility. | Core Lead | **Mitigated** |
| **RSK-002** | **Inter-module API contract misalignment (M2, M3, M5)**<br>_Rationale_: Previous risk was high before data models were implemented. With M3 and M5 schemas finalized, risk of interface mismatch during quiz-to-mastery handoff is substantially lowered but remains pending final M2 integration. | Low | High | **Medium** | Strict schema-first validation enforced via Pydantic models in `backend/app/schemas/` (`adaptive.py`, `progress.py`, `analytics.py`) and documented in `docs/api.md`. | Mustajaab / Toqeer | **Mitigated** |
| **RSK-003** | **Unintended credential or secret leak in public repository**<br>_Rationale_: Secret keys, JWT signatures, or database passwords committed to Git would compromise security (NFR-03, NFR-07). | Low | High | **Medium** | Strict `.gitignore` policy excluding `.env*` files; configuration loaded exclusively via Pydantic `BaseSettings` with safe defaults; pre-commit verification. | All Team Members | **Mitigated** |
| **RSK-004** | **Scope creep beyond semester timeline**<br>_Rationale_: Attempting excessive bonus features (e.g., complex distributed brokers, external LLM integration) risks jeopardizing mandatory rubric requirements. | Medium | Medium | **Medium** | Strictly enforce M1 baseline requirements (`docs/requirements.md`); reject features outside confirmed specifications; require formal Change Requests for additions. | Team Lead | **Open** |
| **RSK-005** | **Unapproved Change Requests (CR-01 Observer, CR-02 Background Jobs) blocking advanced rubric deliverables**<br>_Rationale_: Tasks M5 P-03 (asynchronous report generation jobs) and M5 P-04 (Observer pattern for analytics cache invalidation) depend on change requests CR-01 and CR-02, which remain in `Proposed` status in `docs/decisions.md`. In accordance with `AGENTS.md` Rules 5 & 8, implementation was halted at the approval gate. If team consensus or instructor approval is delayed, planned bonus deliverables cannot proceed. | Low | Medium | **Low** | Adopted and implemented GoF Factory Method pattern for recommendation strategies in Task COMMIT-05, directly satisfying the SE423 Creational Design Pattern rubric requirement without unapproved external dependencies. | Toqeer Ahmed | **Mitigated** |
| **RSK-006** | **Module dependency on M2 Quiz Attempt submission trigger for mastery recalculation**<br>_Rationale_: FR-16 specifies that mastery recalculation occurs after each submitted attempt. The M3 engine and recalculation service are fully implemented and verified, but live automated triggering depends on Module 2 (`QuizService.submit_attempt`) publishing the submission event or invoking the service. Delays in M2 delivery postpone end-to-end integration testing. | High | High | **High** | Materialized into verified integration blocker DEF-MOD-001 (documented in `docs/INTEGRATION_BLOCKERS.md`). Standalone endpoint `POST /courses/{id}/recalculate-mastery` and fixture tests remain active pending authentic M2 code from Mustajaab. | Mustajaab / Toqeer | **Occurred / Monitored** |
| **RSK-007** | **CLI test execution PYTHONPATH misconfiguration**<br>_Rationale_: Running `pytest` from the workspace root without explicitly setting `PYTHONPATH=backend` on Windows causes `ModuleNotFoundError: No module named 'app'`, leading to false-negative test failures during evaluation. | Medium | Low | **Low** | Document standard invocation commands (`$env:PYTHONPATH='backend'; pytest backend/tests`) in `docs/sqa/verification_validation_plan.md` and repository `README.md`. | Toqeer Ahmed | **Mitigated** |

---

## 3. Status Definitions

- **Open**: Active risk actively monitored; ongoing mitigation actions in place.
- **Mitigated**: Preventive measures executed; residual risk reduced to an acceptable operational threshold.
- **Occurred**: Risk materialized into an active issue or defect requiring escalation.
- **Closed**: Risk is no longer applicable to the project lifecycle.

---

## 4. Risk Review & Escalation Schedule

- **Sprint Reviews**: Risks re-evaluated at the close of every milestone transition.
- **Trigger-Based Escalation**: If any Open risk escalates to **Critical** (High Probability + High Impact), an immediate team sync is required within 24 hours to execute contingency plans.
