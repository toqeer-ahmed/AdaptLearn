# AdaptLearn Testing Framework

## Testing Philosophy
For the Software Quality Assurance (SE431) semester project, testing is a first-class citizen across all modules.

## Testing Layers

1. **Backend Unit & Integration Tests (`backend/tests/`)**
   - Built with `pytest` and `httpx` (`TestClient`).
   - Validates API endpoints, Pydantic schemas, and individual service algorithms.
   - Run tests with:
     ```powershell
     cd backend
     .\venv\Scripts\pytest
     ```

2. **Cross-Module & Integration Tests (`tests/`)**
   - High-level test plans, cross-module workflow tests (e.g., Quiz Submission -> Adaptive Engine Adjustment -> Progress Analytics Update).
   - End-to-end integration specifications.

3. **Frontend Component Tests (`frontend/`)**
   - UI unit and rendering tests to verify client stability.

## Module Test Plans (To be expanded in subsequent sprints)
- **M1 (Hiba)**: User authentication tests, course enrollment validations, permission boundary checks.
- **M2 (Mustajaab)**: Quiz scoring accuracy, boundary condition tests on question inputs.
- **M3 (Toqeer)**: Adaptive algorithm convergence, difficulty scaling validation.
- **M4 (Hiba)**: Path generation logic, circular prerequisite prevention.
- **M5 (Toqeer)**: Metric calculation correctness, aggregation performance.

