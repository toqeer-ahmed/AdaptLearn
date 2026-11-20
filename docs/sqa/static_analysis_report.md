# Static Analysis Report

> **Document Status**: Template  
> **Project**: AdaptLearn  
> **Course**: Software Quality Assurance (SE431)

---

## 1. Analysis Session Metadata

| Parameter | Details |
| :--- | :--- |
| **Execution Date** | *[YYYY-MM-DD - Template]* |
| **Commit Tested** | `5e56bf5` *(or current commit under analysis)* |
| **Target Directory** | `frontend/` and `backend/` |
| **Lead Analyst** | *[Hiba Zulfiqar / Mustajaab Ul Fida Qadri / Toqeer Ahmed]* |

---

## 2. Tools & Commands Executed

| Component | Tool & Version | Command Executed | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend** | Oxlint (`v1.90.0`) | `npx oxlint` | JavaScript/JSX syntax, dead code, common defects |
| **Backend** | Flake8 / Ruff *(Planned)* | `flake8 app tests` | Python style (PEP 8), unused imports, syntax errors |
| **Type Checking** | MyPy *(Planned)* | `mypy app` | Static typing and schema validation checks |

---

## 3. Analysis Summary Table

| Category | High / Error | Medium / Warning | Low / Convention | Total |
| :--- | :---: | :---: | :---: | :---: |
| **Frontend Code** | 0 | 0 | 0 | **0** |
| **Backend Code** | 0 | 0 | 0 | **0** |
| **Total Issues** | 0 | 0 | 0 | **0** |

---

## 4. Detailed Findings Log

| Finding ID | File Path & Line | Tool & Rule ID | Description | Severity (Error / Warning / Convention) | Fix Implemented | Status (Resolved / Pending / Suppressed) |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: |
| *[SA-001]* | *[backend/app/main.py:10]* | *[E302]* | *[Template: Expected 2 blank lines, found 1]* | Convention | *Applied PEP 8 spacing* | *Resolved* |

---

## 5. Tool Output Raw Log

```text
[Paste raw command line output from static analysis tools here]
```

---

## 6. Recommendations & Remaining Issues
- **Summary**: No critical static analysis defects currently reported.
- **Action Items**: Continue enforcing linter passes before each PR submission.

