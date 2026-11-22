# AdaptLearn: Architecture Decisions Record (ADR)

> **Document Version**: 1.0.0
> **Date**: November 21, 2026
> **Project**: AdaptLearn (SE423 / SE431)
> **Status Classifications**: `Proposed`, `Team-approved`, `Instructor-approved`, `Rejected`, `Superseded`
> **Rule**: No decision is marked as approved without documented team consensus or explicit instructor instruction.

---

## Decision Status Summary

| ID | Title | Affected Modules | Status | Primary Reason |
| :---: | :--- | :---: | :---: | :--- |
| **D1** | Domain Model & Engine Isolation | All Modules, Core | **Proposed** | Resolves M1 Appendix A; satisfies NFR-05 (pure engine isolation). |
| **D2** | Course Question Bank & Ordered Quiz Assembly | M2 (Mustajaab) | **Adopted / Implemented** | Supports course question bank (FR-08), ordered sequence (FR-10), and topic practice generation (FR-12) via `quiz_questions` join table. |
| **D3** | Question Structure & Single Correct Index | M2 (Mustajaab) | **Adopted / Implemented** | JSON options array (2–5 items) and zero-based integer `correct_option_index`; verified via `test_quiz_schemas.py`. |
| **D4** | Deterministic Recommendation Ordering | M3 (Toqeer), M4 (Hiba) | **Proposed** | Resolves FR-17 ambiguity on topic ordering after weak topics. |
| **D5** | User Input & Password String Bounds | M1 (Hiba), Core | **Adopted / Implemented** | Prevents bcrypt 72-byte truncation and DoS vulnerabilities; verified in Task COMMIT-03. |
| **D6** | SQLAlchemy 2.0 ORM & SQLite / PostgreSQL Architecture | All Modules, CI | **Adopted / Implemented** | Durable persistence across restarts (DEF-DATA-001); verified via `test_persistence.py` in Task COMMIT-04. |
| **D7** | Merge Commits Only (No Squash Merging) | All Modules, Git | **Proposed** | Preserves visible TDD red-green-refactor commit trail per guideline. |
| **CR-01** | Factory Method Pattern (Recommendation Strategy) | M3, M4 | **Adopted / Implemented** | Satisfies SE423 creational pattern rubric; implemented via `RecommendationStrategyCreator` and `RuleBasedStrategyCreator` in Task COMMIT-05. |
| **CR-02** | Background Concurrency Job for Reports | M5 (Toqeer), Core | **Proposed (Needs Confirmation)** | Satisfies SE423 concurrency rubric using `ThreadPoolExecutor`. |

---

## Detailed Decision Records

### D1: Domain Model & Engine Isolation
- **Status**: **Proposed** (Pending team review)
- **Affected Modules**: M1, M2, M3, M4, M5, Core
- **Context**: M1 Appendix A raised the question of whether database ORM models should be distinct from domain entities. Additionally, NFR-05 and NFR-15 mandate that business rules must remain separate from request handling and database access.
- **Decision**:
  1. ORM models in `app/domain/models.py` act as the persistence entities for repositories and services.
  2. The adaptive engine (`app/engine/`) uses plain Python dataclasses and functions. It imports **zero** FastAPI, SQLAlchemy, or Pydantic packages.
- **Impact**: An automated architectural test (`tests/architecture/test_layers.py`) will scan imports in `app/engine/` and fail if any web or database framework is imported.
- **Alternatives Considered**:
  - *Full Clean Architecture with duplicate entity classes*: Rejected due to high mapping boilerplate for a 3-student semester timeline.
  - *Importing SQLAlchemy models directly into engine*: Rejected because it tightly couples core algorithms to database sessions and breaks standalone unit testing.

---

### D2: Course Question Bank & Ordered Quiz Assembly
- **Status**: **Adopted / Implemented** (Confirmed by Mustajaab Ul Fida Qadri)
- **Affected Modules**: M2: Quiz and Assessment Engine
- **Context**: M1 described a "question bank" and required both instructor-authored quizzes (FR-10) and on-demand student practice quizzes for specific topics (FR-12). Storing questions strictly within one quiz prevents practice quiz generation from drawing existing topic questions.
- **Decision**: Questions belong to a course and topic (`course_id`, `topic_id` on `questions` table). Quizzes link to questions via an association table `quiz_questions` with explicit `sequence_order`.
- **Impact**: Enables question reuse across quizzes, supports dynamic topic-based practice quiz assembly (FR-12), preserves question authoring independent of quiz creation (FR-08), and allows soft-deletion safeguards based on attempt answer history (FR-09).
- **Implementation**: Enforced in `backend/app/models/quiz.py` (`QuestionModel`, `QuizModel`, `QuizQuestionModel`) and `backend/app/repositories/quiz_repository.py`. Verified by 9 unit tests in `backend/tests/unit/test_quiz_repository.py`.

---

### D3: Question Authoring Constraints & Single Correct Index
- **Status**: **Adopted / Implemented** (Confirmed by Mustajaab Ul Fida Qadri)
- **Affected Modules**: M2: Quiz and Assessment Engine
- **Context**: FR-08 specifies 2 to 5 options with "exactly one correct option." TC-09 tests validation bounds.
- **Decision**:
  1. Options are stored as a JSON array of strings (minimum length 2, maximum length 5).
  2. Correct answer is represented as a single zero-based integer `correct_option_index` (`0 <= correct_option_index < len(options)`).
- **Impact**: Pydantic v2 schemas reject out-of-bounds indices and option counts $<2$ or $>5$ before persistence. Student-safe schemas strip `correct_option_index` and `explanation` prior to submission.
- **Implementation**: Enforced in `backend/app/schemas/quiz.py` (`QuestionCreate`, `QuestionStudentSafe`, `QuizStudentSafeResponse`) and `backend/app/models/quiz.py`. Verified by 18 boundary tests in `backend/tests/unit/test_quiz_schemas.py`.

---

### D4: Deterministic Recommendation Ordering
- **Status**: **Proposed** (Requires Hiba & Toqeer's confirmation)
- **Affected Modules**: M3: Adaptive Learning Engine, M4: Personalized Learning Paths
- **Context**: FR-18 specifies that Weak topics must appear before Developing topics, and Proficient topics are never recommended. M1 Section 9.3 and TC-18-3/TC-18-4 specify alphabetical name tie-breaking and place Not Assessed topics after Developing topics, noting this is subject to confirmation.
- **Baseline Behavior (M1 §9.3 & TC-18-1..TC-18-6)**:
  1. Candidates: Non-Proficient topics only.
  2. Availability: Candidate is available when all unmastered prerequisites are placed.
  3. Precedence: Weak $\rightarrow$ Developing $\rightarrow$ Not Assessed.
  4. Tie-breaking: Lower score first, then alphabetical by topic name (`topic.name`).
- **Proposed Modification (D4)**:
  1. Ordering precedence: **Weak** topics (lowest score first) $\rightarrow$ **Developing** topics (lowest score first).
  2. **Proficient** topics are never recommended.
  3. An **Unassessed** topic appears only when required as an unmet prerequisite for a weak/developing topic, or under FR-19 (first course topics with no prerequisites).
  4. Ties are broken deterministically by course topic sequence number (`topic.order_index`).
- **Impact**: Satisfies NFR-10 (deterministic calculations). Ensures repeatable automated tests.
- **Alternatives Considered**:
  - *Interleaving unassessed topics with weak topics*: Rejected because pedagogical priority demands remediating identified weaknesses before introducing unassessed material.

---

### D5: User Input & Password String Length Bounds
- **Status**: **Adopted / Implemented** (Verified in Task COMMIT-03)
- **Affected Modules**: M1: User & Course Management, Core
- **Context**: M1 defined required fields for registration (FR-01) but did not specify string length constraints. Passlib/bcrypt has a hard maximum of 72 bytes.
- **Decision**:
  - Password: 8 to 72 characters.
  - Full Name: 1 to 100 characters.
  - Email Address: Maximum 254 characters (RFC 5321 standard), validated against standard email regex.
- **Impact**: Pydantic schemas enforce bounds on `POST /auth/register` and `POST /auth/login`. Prevents bcrypt truncation bugs and input DoS. Verified by 30 security tests in `backend/tests/unit/test_security_auth.py`.
- **Implementation**: Enforced in `backend/app/schemas/auth.py` and `backend/app/core/security.py`.
- **Alternatives Considered**:
  - *No upper limit on password*: Vulnerable to bcrypt silent truncation (bytes beyond 72 ignored) and regex DoS.

---

### D6: SQLAlchemy 2.0 ORM & Persistent Relational Storage (SQLite / PostgreSQL Compatible)
- **Status**: **Adopted / Implemented** (Verified in Task COMMIT-04)
- **Affected Modules**: All Modules, CI, Local Development
- **Context**: Repositories originally used ephemeral in-memory dictionaries, losing 100% of data across server restarts (DEF-DATA-001). Furthermore, NFR-08 and NFR-09 mandate transaction boundaries and referential integrity.
- **Decision**:
  1. Implement synchronous SQLAlchemy 2.0 ORM declarative models across all persistent entities in `backend/app/models/`.
  2. Implement centralized session management in `backend/app/db/session.py` with automatic table creation via `init_db()` during application lifespan startup.
  3. Default to SQLite (`sqlite:///./adaptlearn.db`) for zero-dependency local development, rapid unit/integration testing, and offline grading.
  4. Write all models and repository operations using standard dialect-agnostic SQLAlchemy 2.0 constructs so switching to PostgreSQL requires only setting the `DATABASE_URL` environment variable (e.g., `postgresql+psycopg://...`).
- **Impact**: Resolves DEF-DATA-001 with 100% restart survival. Preserves strict NFR-05 isolation (pure engine has zero SQLAlchemy imports). Verified by 9 restart-survival and persistence tests in `backend/tests/unit/test_persistence.py`.
- **Alternatives Considered**:
  - *PostgreSQL-only with mandatory Docker*: Rejected as sole option because local evaluator/student environments may lack running Docker daemons; SQLite provides an identical ORM interface without external infrastructure hurdles.
  - *JSON file store or Pickle*: Rejected due to lack of ACID transactions, lack of concurrent write locking, and lack of schema constraints.

---

### D7: Merge Commits Only (No Squash Merging)
- **Status**: **Proposed** (Requires repository owner configuration on GitHub)
- **Affected Modules**: Git Workflow, SQA Process
- **Context**: The official course rubric requires a visible, authentic Test-Driven Development (TDD) trail showing red-green-refactor cycles.
- **Decision**:
  1. All feature pull requests must be integrated using merge commits (`git merge --no-ff`).
  2. Squash merging will be disabled in GitHub repository settings.
- **Impact**: Every individual `test:`, `feat:`, and `refactor:` commit remains preserved in the permanent `main` git history.
- **Alternatives Considered**:
  - *Squash and merge*: Rejected because it collapses the TDD commit trail into a single commit, eliminating evidence of test-first development.

---

## Change Requests (CR)

### CR-01: Factory Method Creational Pattern for Recommendation Strategies
- **Status**: **Adopted / Implemented** (Verified in Task COMMIT-05)
- **Origin**: SE423 Milestone 2 Rubric Mandate ($\ge 3$ design patterns including $\ge 1$ creational pattern).
- **Rationale**: M1 §7.3 initially omitted formal creational patterns. To satisfy the SE423 rubric requirement for a genuine creational design pattern without overengineering:
  1. We introduce the **Factory Method** pattern:
     - Abstract Creator: `RecommendationStrategyCreator` declaring abstract factory method `create_strategy() -> RecommendationStrategy` and template method `recommend()`.
     - Concrete Creator: `RuleBasedStrategyCreator` overriding `create_strategy()` to instantiate and return `RuleBasedRecommendationStrategy`.
     - Creator Registry: `STRATEGY_CREATORS` mapping identifiers to concrete creator types, accessed via `get_strategy_creator()`.
  2. Client Abstraction: `AdaptiveService` depends on `RecommendationStrategyCreator` (injected or resolved via `get_strategy_creator()`), delegating object creation through the factory method.
- **Impact**: Fully satisfies the SE423 Creational Design Pattern requirement (resolves DEF-ARCH-001). Preserves pure engine domain isolation (NFR-05). Backward compatible with existing callers. Verified by 18 unit tests in `backend/tests/unit/test_recommendation_strategy.py`.
- **Alternatives Considered**:
  - *Flat dictionary lookup function*: Rejected because it does not satisfy the GoF Factory Method pattern required by the rubric (DEF-ARCH-001).
  - *Abstract Factory*: Rejected as overengineering since recommendation strategies do not produce families of related products.

---

### CR-02: Introduce Background Concurrency Job for Report Exports
- **Status**: **Proposed (Requires Instructor / Team Confirmation)**
- **Origin**: SE423 Concurrency Rubric Requirement.
- **Rationale**: The course guideline requires at least one genuine concurrent operation with a documented thread-safety strategy matching the code. M1 contained no background tasks.
- **Decision**:
  1. Add an asynchronous report generation capability for instructors (M5).
  2. When an instructor requests a heavy course analytics export (`POST /courses/{id}/reports`), the request spawns a task via a managed `ThreadPoolExecutor` and immediately returns a `job_id` (`202 Accepted`).
  3. A `report_jobs` database table tracks status (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
  4. Thread safety is achieved by giving each worker thread its own isolated database session and using thread-safe queues.
- **Impact Analysis**:
  - *Code*: Adds `backend/app/jobs/job_runner.py` and `backend/app/jobs/report_job.py`.
  - *Endpoints*: Adds `POST /courses/{id}/reports` and `GET /reports/{job_id}`.
  - *Rubric*: Directly provides concrete evidence for the SE423 Concurrency grading criteria.
