# Software Risk Register

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)  
> **Note**: Risks must be identified, evaluated, and updated throughout each sprint lifecycle.

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
- **Critical**: High Probability + High Impact
- **High**: High Probability + Medium Impact, or Medium Probability + High Impact
- **Medium**: Medium Probability + Medium Impact, or High Probability + Low Impact
- **Low**: Low Probability + Low/Medium Impact

---

## 2. Risk Log Table

| Risk ID | Description | Probability | Impact | Risk Level | Mitigation Strategy | Owner | Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: |
| *RSK-001* | *[Template: Database environment inconsistency across team machines]* | Medium | High | High | *Standardize on Docker Compose PostgreSQL or documented local PostgreSQL service configuration.* | Core Lead | *Open* |
| *RSK-002* | *[Template: Inter-module API contract misalignment between M2 and M3]* | Medium | High | High | *Enforce schema-first validation in `app/schemas/` before feature coding.* | Mustajaab / Toqeer | *Open* |
| *RSK-003* | *[Template: Unintended credential or secret leak in public repository]* | Low | High | Medium | *Enforce strict `.gitignore`, pre-commit verification, and never commit `.env`.* | All Team Members | *Mitigated* |
| *RSK-004* | *[Template: Scope creep beyond semester timeline]* | Medium | Medium | Medium | *Strictly adhere to M1-M5 core modular boundaries and milestone deadlines.* | Team | *Open* |

---

## 3. Status Definitions
- **Open**: Active risk being actively monitored.
- **Mitigated**: Preventive measures executed; residual risk within acceptable threshold.
- **Occurred**: Risk materialized into an active issue or defect.
- **Closed**: Risk no longer applicable to the project.

