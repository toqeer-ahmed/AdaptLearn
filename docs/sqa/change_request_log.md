# Software Change Request (CR) Log

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)  
> **Purpose**: Formal tracking of scope, design, and architecture changes across sprints.

---

## 1. Change Control Process
1. **Submission**: Team member identifies need for modification to existing requirement, schema, or architecture.
2. **Impact Analysis**: Evaluate impact on timeline, dependent modules, database schema, and test cases.
3. **Team Review**: Review in team meeting or PR discussion.
4. **Approval**: Unanimous or team lead sign-off required prior to implementation.
5. **Traceability**: Update RTM and documentation upon completion.

---

## 2. Change Request Table

| Change ID | Reason for Change | Affected Requirement | Affected Module | Impact Analysis | Approval Status (Approved / Rejected / Pending) | Implementation Status (Pending / In Progress / Implemented / Verified) |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: |
| *[CR-001]* | *[Template: Switch from cookie auth to Bearer JWT token header]* | *REQ-M1-AUTH* | M1, Core | *Frontend needs auth header interceptor; backend security dependency updated.* | *Pending Review* | *Pending* |
| *[CR-002]* | *[Template: Add difficulty rating attribute to question bank schema]* | *REQ-M2-QUIZ* | M2, M3 | *Affects M2 question model and M3 difficulty matching service.* | *Pending Review* | *Pending* |

---

## 3. Detailed Change Request Template

When submitting a formal change request, copy and complete this block:

```markdown
### [CR-XXX]: Short Descriptive Title
- **Date Submitted**: YYYY-MM-DD
- **Requested By**: [Hiba / Mustajaab / Toqeer]
- **Affected Module(s)**: [M1 / M2 / M3 / M4 / M5 / Core / Architecture]
- **Affected Requirement(s)**: [REQ-ID]

#### Reason for Change
Explain why the change is necessary (e.g., technical limitation, requirement clarification, rubric alignment).

#### Proposed Modification
Describe the exact modification to specifications, interfaces, or code.

#### Impact Analysis
- **Architecture & Interfaces**: What schemas or endpoints change?
- **Database Schema**: Are database migrations required?
- **Dependent Modules**: Which teammate's module is impacted?
- **Schedule & Effort**: Estimated hours to implement and test.

#### Approval & Decision
- **Status**: Approved / Rejected / Deferred
- **Approved By**: [Team signatures]
- **Approval Date**: YYYY-MM-DD
- **Implementation Commit**: [Commit Hash once completed]
```

