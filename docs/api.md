# AdaptLearn: Cross-Module API Contracts & Interface Specifications

> **Document Version**: 1.0.0
> **Date**: November 21, 2026
> **Source Documents**: M1 Report §4–§5, M2 Master Plan Section D
> **Status**: Specification Baseline (Interfaces requiring team agreement are explicitly flagged)

---

## 1. Global API Conventions

- **Base URL Prefix**: `/api/v1` (with root convenience redirects where documented)
- **Data Exchange**: JSON (`Content-Type: application/json`)
- **Authentication**: Bearer Token in HTTP Header: `Authorization: Bearer <token>`
- **Error Response Format** (Standardized via `app/core/errors.py`):
  ```json
  {
    "success": false,
    "error": {
      "code": 400,
      "message": "Human readable explanation",
      "details": []
    }
  }
  ```

---

## 2. Module 1: User & Course Management (Hiba)

### 2.1 Authentication & Profile
- `POST /api/v1/auth/register`
  - **Access**: Public
  - **Status**: **Implemented (Task COMMIT-03: Salted bcrypt password hashing & Decision D5 validation)**
  - **Request Body**:
    ```json
    {
      "name": "Toqeer Ahmed",
      "email": "toqeer@example.com",
      "password": "SecurePassword123",
      "role": "Student"
    }
    ```
  - **Constraints**: Name (1–100 chars), Email ($\le 254$ chars, valid format), Password (8–72 chars), Role (`"Student"` or `"Instructor"`).
  - **Responses**:
    - `201 Created`: Returns created user object (excluding password hash per NFR-03).
    - `400 Bad Request` / `422 Unprocessable Entity`: Input validation failed.
    - `409 Conflict`: Email address already registered.

- `POST /api/v1/auth/login`
  - **Access**: Public
  - **Status**: **Implemented (Task COMMIT-03: Signed JWT token issuance with 60-minute expiration)**
  - **Request Body**:
    ```json
    {
      "email": "toqeer@example.com",
      "password": "SecurePassword123"
    }
    ```
  - **Responses**:
    - `200 OK`: `{"access_token": "<jwt>", "token_type": "bearer", "user": {"id": 1, "name": "...", "email": "...", "role": "..."}}`
    - `401 Unauthorized`: Identical generic message for non-existent email or invalid password (`"Invalid email or password"` prevents user enumeration).

- `GET /api/v1/auth/me`
  - **Access**: Authenticated (`Authorization: Bearer <jwt>`)
  - **Status**: **Implemented (Task COMMIT-03: Current user profile verification)**
  - **Responses**:
    - `200 OK`: `{"id": 1, "name": "...", "email": "...", "role": "..."}`
    - `401 Unauthorized`: Missing, expired, invalid signature, or forged user ID.

### 2.2 Course Management
- `GET /api/v1/courses`
  - **Access**: Authenticated
  - **Responses**: `200 OK` — List of active courses. (Instructors see their authored courses; students see enrolled courses).
- `POST /api/v1/courses`
  - **Access**: Instructor Only
  - **Request Body**: `{"title": "Software QA", "description": "...", "strategy_name": "rule_based"}`
  - **Responses**: `201 Created`
- `PATCH /api/v1/courses/{id}`
  - **Access**: Course Owner Only (403 Forbidden for other instructors)
- `POST /api/v1/courses/{id}/archive`
  - **Access**: Course Owner Only. Sets `is_archived = true`. Archived courses reject new enrollments and quiz attempts.
- `POST /api/v1/courses/{id}/enroll`
  - **Access**: Student Only
  - **Request Body**: `{"course_code": "SE431-2026"}`
  - **Responses**: `200 OK` / `404 Not Found` (invalid code) / `409 Conflict` (already enrolled).

### 2.3 Topic Hierarchy & Prerequisites
- `GET /api/v1/courses/{id}/topics`
  - **Access**: Enrolled Students & Course Instructor
  - **Responses**: `200 OK` — Ordered topic list including sequence index and prerequisite topic IDs.
- `POST /api/v1/courses/{id}/topics`
  - **Access**: Course Owner Only
  - **Request Body**: `{"title": "Unit Testing", "order_index": 1}`
- `PUT /api/v1/courses/{id}/topics/order`
  - **Access**: Course Owner Only
  - **Request Body**: `{"topic_ids": [3, 1, 2]}` (updates `order_index` sequence)
- `POST /api/v1/topics/{id}/prerequisites`
  - **Access**: Course Owner Only
  - **Request Body**: `{"prerequisite_topic_id": 2}`
  - **Validation**:
    - `400 Bad Request`: Prerequisite belongs to a different course.
    - `409 Conflict`: Self-prerequisite (`id == prerequisite_topic_id`) or circular dependency (detected via cycle check algorithm).

---

## 3. Module 2: Quiz & Assessment Engine (Mustajaab)

### 3.1 Quiz & Question Authoring
- `POST /api/v1/courses/{id}/quizzes`
  - **Access**: Course Owner Only
  - **Request Body**: `{"title": "Quiz 1: Boundary Analysis", "topic_id": 1, "is_practice": false}`
  - **Responses**: `201 Created`
- `POST /api/v1/quizzes/{id}/questions`
  - **Access**: Course Owner Only
  - **Request Body**:
    ```json
    {
      "statement": "What is the minimum number of tests for 2-boundary value analysis?",
      "options": ["2 tests", "4 tests", "6 tests"],
      "correct_option_index": 1,
      "difficulty": "Medium",
      "explanation": "Standard 2-boundary analysis tests min and max points."
    }
    ```
  - **Constraints (D3)**: `len(options)` between 2 and 5; `0 <= correct_option_index < len(options)`.
  - *Status*: **Requires Mustajaab's confirmation on D2 (1:N question ownership) and D3.**
- `DELETE /api/v1/questions/{id}`
  - **Access**: Course Owner Only
  - **Rules (FR-09)**: If the question has existing attempt records, it cannot be deleted; it is flagged `is_active = false`.
- `POST /api/v1/quizzes/{id}/publish`
  - **Access**: Course Owner Only. Students can only see and attempt published quizzes (FR-10).

### 3.2 Quiz Taking & Attempt Submission
- `GET /api/v1/quizzes/{id}`
  - **Access**: Enrolled Student
  - **Responses**: `200 OK` — Returns quiz title and array of questions **without** `correct_option_index` or `explanation`.
- `POST /api/v1/quizzes/{id}/attempts`
  - **Access**: Enrolled Student
  - **Request Body**:
    ```json
    {
      "answers": [
        {"question_id": 101, "selected_option_index": 1},
        {"question_id": 102, "selected_option_index": 0}
      ]
    }
    ```
  - **Behavior & Transaction Boundary (NFR-08)**:
    - Executed in a single atomic database transaction.
    - Locks the student's mastery records using `SELECT ... FOR UPDATE` (TC-31).
    - Grades answers against stored `correct_option_index`.
    - Updates M3 mastery scores for all covered topics.
    - Saves `quiz_attempts` and `attempt_answers`.
    - Publishes `AttemptSubmitted` event to `EventBus` **after transaction commit**.
  - **Responses**: `201 Created` — Returns score and attempt summary.
- `GET /api/v1/attempts/{id}`
  - **Access**: Attempt Owner & Course Instructor Only
  - **Responses**: `200 OK` — Detailed result: overall score, per-topic score, student selection, correct answer, and explanations (FR-14).

---

## 4. Module 3: Adaptive Learning Engine (Toqeer)

### 4.1 Internal Engine Interface (Pure Python / NFR-05)
The adaptive engine exposes domain dataclasses and pure functions independent of FastAPI and SQLAlchemy:

```python
# Dataclasses
@dataclass(frozen=True)
class MasteryParameters:
    window_size: int = 5           # N most recent attempts
    easy_weight: float = 1.0
    medium_weight: float = 1.5
    hard_weight: float = 2.0
    weak_threshold: float = 0.50
    proficient_threshold: float = 0.80
    min_responses: int = 3

@dataclass(frozen=True)
class TopicMasteryStatus:
    topic_id: int
    score: float                   # 0.0 to 1.0
    level: str                     # "Weak", "Developing", "Proficient", "Not Assessed"
    response_count: int

@dataclass(frozen=True)
class Recommendation:
    topic_id: int
    topic_title: str
    mastery_level: str
    rationale: str
```

- `MasteryCalculator.calculate_topic_score(responses: list[ResponseRecord], params: MasteryParameters) -> float`
- `MasteryCalculator.classify_level(score: float, response_count: int, params: MasteryParameters) -> str`
- `RecommendationStrategy.recommend(context: RecommendationContext) -> list[Recommendation]`

### 4.2 HTTP Endpoints
- `GET /api/v1/courses/{id}/recommendations`
  - **Access**: Enrolled Student
  - **Responses**: `200 OK` — Ordered list of up to 3 recommended topics with pedagogical rationale (FR-18, FR-19).
- `GET /api/v1/courses/{id}/adaptive-settings`
  - **Access**: Course Owner Only
  - **Responses**: `200 OK` — Current course adaptive parameters (`N`, weights, thresholds).
- `PUT /api/v1/courses/{id}/adaptive-settings`
  - **Access**: Course Owner Only
  - **Request Body**: Partial update for adaptive parameters (FR-20). Applies to future recalculations.

---

## 5. Module 4: Personalized Learning Paths (Hiba)

- `GET /api/v1/courses/{id}/learning-path`
  - **Access**: Enrolled Student
  - **Responses**: `200 OK`
    ```json
    {
      "course_id": 1,
      "path": [
        {
          "topic_id": 1,
          "title": "Syntax & Variables",
          "status": "Proficient",
          "is_unlocked": true
        },
        {
          "topic_id": 2,
          "title": "Conditionals",
          "status": "Weak",
          "is_unlocked": true,
          "is_recommended": true
        },
        {
          "topic_id": 3,
          "title": "Loops",
          "status": "Not Assessed",
          "is_unlocked": false,
          "locked_reason": "Prerequisite 'Conditionals' not yet Proficient"
        }
      ]
    }
    ```
  - *Status*: **Requires alignment with Hiba on prerequisite evaluation logic.**

---

## 6. Module 5: Progress Analytics & Instructor Dashboard (Toqeer)

### 6.1 Student Progress Views
- `GET /api/v1/courses/{id}/progress`
  - **Access**: Enrolled Student
  - **Responses**: `200 OK`
    - Course completion percentage (percentage of topics marked Proficient).
    - Topic breakdown with current mastery scores and levels.
    - Recent quiz attempts and scores.

### 6.2 Instructor Analytics Views
- `GET /api/v1/courses/{id}/analytics/mastery-distribution`
  - **Access**: Course Owner Only
  - **Responses**: `200 OK` — For each topic, count of students at Weak, Developing, Proficient, and Not Assessed (FR-23).
- `GET /api/v1/courses/{id}/analytics/student-roster`
  - **Access**: Course Owner Only
  - **Responses**: `200 OK` — Enrolled students list with per-topic mastery scores (FR-22).
- `GET /api/v1/courses/{id}/analytics/questions`
  - **Access**: Course Owner Only
  - **Responses**: `200 OK` — Question statistics: total times answered, percentage correct (FR-24).

### 6.3 Background Concurrency Report Jobs (CR-02)
- `POST /api/v1/courses/{id}/reports`
  - **Access**: Course Owner Only
  - **Request Body**: `{"report_type": "full_course_analytics"}`
  - **Responses**: `202 Accepted` — `{"job_id": "job_uuid_123", "status": "PENDING"}`
- `GET /api/v1/reports/{job_id}`
  - **Access**: Job Requester Only
  - **Responses**:
    - `200 OK`: `{"job_id": "...", "status": "COMPLETED", "completed_at": "...", "result": { ... }}`
    - `200 OK`: `{"job_id": "...", "status": "RUNNING", "progress": 45}`
  - *Status*: **Requires team confirmation on CR-02.**
