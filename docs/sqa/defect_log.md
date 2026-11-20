# Software Defect Log

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)  
> **Current Defect Count**: 0 active defects (Template)

---

## 1. Severity & Priority Classifications

### Severity (Technical Impact)
- **Critical (S1)**: Complete system crash, data loss, security compromise, or blocking of core functionality.
- **Major (S2)**: Primary module feature inoperable with no immediate workaround.
- **Moderate (S3)**: Secondary functionality impaired or unexpected behavior with an available workaround.
- **Minor (S4)**: Cosmetic, UI alignment, minor typo, or non-functional defect.

### Priority (Resolution Urgency)
- **P1 (Immediate)**: Must be fixed before any further merging or deployment.
- **P2 (High)**: Must be resolved within current sprint milestone.
- **P3 (Normal)**: Scheduled for resolution during regular development cycle.
- **P4 (Low)**: Resolved when time permits or deferred to future cleanup.

---

## 2. Defect Records

| Defect ID | Summary | Severity | Priority | Steps to Reproduce | Expected Result | Actual Result | Assigned Owner | Resolution | Retest Status |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- | :--- | :--- | :---: |
| *[DEF-001]* | *[Template: Sample defect summary]* | S2 | P2 | *1. Navigate to endpoint...<br>2. Submit payload...* | *HTTP 200 with result* | *HTTP 500 error* | *Assignee* | *Unresolved* | *Pending* |

---

## 3. Detailed Defect Entry Template

When logging a defect, copy and complete this entry block:

```markdown
### [DEF-XXX]: Short Descriptive Title
- **Date Reported**: YYYY-MM-DD
- **Reported By**: [Hiba / Mustajaab / Toqeer]
- **Assigned To**: [Owner]
- **Module Affected**: [M1 / M2 / M3 / M4 / M5 / Core / Frontend]
- **Severity**: S1 - Critical / S2 - Major / S3 - Moderate / S4 - Minor
- **Priority**: P1 - Immediate / P2 - High / P3 - Normal / P4 - Low
- **Environment**: OS: Windows 10/11 | Python: 3.10 | Node: 20
- **Build / Commit**: [Commit Hash]

#### Description & Steps to Reproduce
1. Step 1:
2. Step 2:
3. Step 3:

#### Expected Behavior
Describe what should have occurred.

#### Actual Behavior
Describe what actually happened (include HTTP code, logs, or UI errors).

#### Log / Evidence Traceback
```text
[Paste error log or traceback here]
```

#### Resolution Details
- **Resolution**: Fixed / Won't Fix / Duplicate / Cannot Reproduce
- **Fix Commit**: [Commit Hash]
- **Retest Result**: Pass / Fail (Verified by [Reviewer] on YYYY-MM-DD)
```

