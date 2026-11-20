# Requirements Traceability Matrix (RTM)

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)  
> **Note**: This matrix will be formally populated following review of the official M1 deliverables and course requirements specifications.

---

## 1. Traceability Overview
The Requirements Traceability Matrix (RTM) ensures bidirectional traceability from user and functional requirements through architectural design, implementation, and automated test verification.

---

## 2. Traceability Matrix Table

| Requirement ID | Requirement Description | Source Document | Module | Implementation Reference | Test Case ID | Verification Status | Evidence Reference |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| *[REQ-M1-XXX]* | *[Template: User Registration]* | *M1 Specification* | M1 | `backend/app/api/v1/endpoints/users.py` | `TC-AUTH-001` | *Pending* | *Not yet executed* |
| *[REQ-M2-XXX]* | *[Template: Quiz Submission]* | *M2 Specification* | M2 | `backend/app/api/v1/endpoints/quizzes.py` | `TC-QUIZ-001` | *Pending* | *Not yet executed* |
| *[REQ-M3-XXX]* | *[Template: Adaptive Difficulty]* | *M3 Specification* | M3 | `backend/app/services/adaptive_service.py` | `TC-ADAPT-001` | *Pending* | *Not yet executed* |
| *[REQ-M4-XXX]* | *[Template: Learning Path Graph]* | *M4 Specification* | M4 | `backend/app/services/path_service.py` | `TC-PATH-001` | *Pending* | *Not yet executed* |
| *[REQ-M5-XXX]* | *[Template: Analytics Aggregation]* | *M5 Specification* | M5 | `backend/app/services/analytics_service.py` | `TC-ANLYT-001` | *Pending* | *Not yet executed* |
| *[REQ-SYS-001]* | System Health Monitoring | Project Initialization | Core | `backend/app/api/v1/endpoints/health.py` | `TC-SYS-HEALTH` | **Verified** | `backend/tests/test_health.py` |

---

## 3. Status Definitions
- **Pending**: Requirement documented; implementation or testing not yet started.
- **In Progress**: Code or test cases actively under development.
- **Verified**: Automated test executed and passed; evidence recorded in test logs.
- **Failed**: Verification test executed and failed; logged in Defect Log.
- **Blocked**: Verification cannot proceed due to prerequisite blockers.

