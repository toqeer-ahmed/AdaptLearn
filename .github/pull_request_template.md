## Pull Request Summary

### Description
<!-- Provide a clear, concise explanation of the changes introduced by this PR. -->

### Related Issue
<!-- Link the issue resolved by this PR (e.g., Closes #12, Addresses #15) -->
Closes #

---

### Module Affected
- [ ] **M1**: User & Course Management (Hiba)
- [ ] **M2**: Quiz & Assessment Engine (Mustajaab)
- [ ] **M3**: Adaptive Learning Engine (Toqeer)
- [ ] **M4**: Personalized Learning Paths (Hiba)
- [ ] **M5**: Progress Analytics / Dashboard (Toqeer)
- [ ] **Frontend**: Client UI / Components
- [ ] **Core / Infrastructure**: Config, Database, Routing, Docker

---

### Key Changes Made
- 
- 
- 

---

### Verification & Testing Performed
<!-- Describe the tests executed to verify these changes. -->
- [ ] Backend automated tests run and passed (`pytest -v`)
- [ ] Frontend build verified (`npm run build`)
- [ ] Manual endpoint / UI verification performed

**Test Output / Evidence:**
```text
<!-- Paste terminal test output or status summary here -->
```

---

### Architectural & Database Impact
- Does this PR modify database schemas or add new migrations? **[Yes / No]**
- Does this PR alter existing API contracts in `app/schemas/`? **[Yes / No]**
- If yes, describe the impact:

---

### Screenshots / UI Preview (If applicable)
<!-- Add before/after screenshots or terminal output for UI/API verification -->

---

### Author Pre-Submission Checklist
- [ ] My code adheres to the project's [CONTRIBUTING.md](../CONTRIBUTING.md) guidelines.
- [ ] I have not committed any secrets, `.env` files, or credentials.
- [ ] I have added/updated relevant unit tests.
- [ ] No extraneous files (`node_modules`, `venv`, `dist`, `.pytest_cache`) are staged.
- [ ] Branch is rebased and up to date with `main`.

---

### Reviewer Checklist (For Peer Reviewer)
- [ ] Code is clear, readable, and properly modularized.
- [ ] Pydantic validation schemas are used for input/output.
- [ ] Tests pass locally and cover happy/unhappy paths.
- [ ] No regression introduced to existing module contracts.

