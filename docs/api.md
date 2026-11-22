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
  - **Query Params**: `instructor_id` (optional int), `is_archived` (optional bool), `enrolled` (optional bool)
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` — `CourseListResponse` containing `courses: list[CourseResponse]` and `total: int`.
- `POST /api/v1/courses`
  - **Access**: Instructor Only
  - **Status**: **Implemented & Verified** (Stage 5: Task COMMIT-04, Decisions D1, D7)
  - **Request Body**: `{"title": "Software QA", "description": "...", "course_code": "SQA-423-2026"}`
  - **Responses**:
    - `201 Created`: Returns `CourseResponse` with uppercase normalized code.
    - `400 Bad Request` / `422 Unprocessable Entity`: Invalid title or course code.
    - `403 Forbidden`: Authenticated user is not an instructor.
    - `409 Conflict`: Course code is already registered.
- `GET /api/v1/courses/{id}`
  - **Access**: Authenticated
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Responses**: `200 OK` / `403 Forbidden` (archived course historical access restricted to enrolled students and owner) / `404 Not Found`.
- `PUT /api/v1/courses/{id}` & `PATCH /api/v1/courses/{id}`
  - **Access**: Course Owner Only (403 Forbidden for other instructors)
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` / `400 Bad Request` (cannot modify archived courses, Decision D3).
- `POST /api/v1/courses/{id}/archive`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Responses**: `200 OK` — Sets `is_archived = true`. Archived courses reject new enrollments and modifications.
- `POST /api/v1/courses/{id}/publish` & `POST /api/v1/courses/{id}/unarchive`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Responses**: `200 OK` — Sets `is_archived = false`.
- `POST /api/v1/courses/{id}/enroll`
  - **Access**: Student Only
  - **Status**: **Implemented & Verified** (Stage 5, Decisions D3, D6)
  - **Request Body**: `{"course_code": "SQA-423-2026"}` (optional verification)
  - **Responses**:
    - `200 OK`: `{"id": 1, "student_id": 101, "course_id": 1}`
    - `400 Bad Request`: Invalid/mismatched course code or course is archived.
    - `403 Forbidden`: Non-student principal or enrolling another student.
    - `409 Conflict`: Student is already enrolled.
- `GET /api/v1/courses/{id}/enrollment`
  - **Access**: Authenticated
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` (returns enrollment record) / `404 Not Found` (user is not enrolled).
- `GET /api/v1/courses/enrolled` & `GET /api/v1/users/me/enrollments`
  - **Access**: Student Only
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` — `UserEnrollmentsResponse` listing all courses the student is enrolled in.
- `GET /students/{student_id}/enrollments`
  - **Access**: Authenticated (Privacy NFR-06: Student can only view own; 403 Forbidden otherwise)
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` / `403 Forbidden`.
- `GET /api/v1/courses/{id}/students`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` — `list[int]` of enrolled student IDs.

### 2.3 Topic Hierarchy & Prerequisites
- `GET /api/v1/courses/{id}/topics`
  - **Access**: Authenticated (Enrolled Students & Course Owner; archived view restricted to enrolled/owner)
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` — `TopicListResponse` ordered by `order_index ASC`.
- `POST /api/v1/courses/{id}/topics`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Request Body**: `{"title": "Unit Testing", "order_index": 1, "description": "..."}`
  - **Responses**: `201 Created` / `400 Bad Request` (if course is archived) / `403 Forbidden`.
- `GET /api/v1/topics/{id}` & `GET /api/v1/courses/{course_id}/topics/{id}`
  - **Access**: Authenticated
  - **Status**: **Implemented & Verified** (Stage 5)
  - **Responses**: `200 OK` / `404 Not Found`.
- `PUT /api/v1/topics/{id}` & `PATCH /api/v1/topics/{id}`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Responses**: `200 OK` / `400 Bad Request` (if course is archived) / `403 Forbidden` / `404 Not Found`.
- `DELETE /api/v1/topics/{id}` & `DELETE /api/v1/courses/{course_id}/topics/{id}`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decisions D2, D3)
  - **Responses**:
    - `200 OK`: `{"status": "success", "message": "Topic ... deleted successfully"}`
    - `400 Bad Request`: If course is archived OR topic is referenced by quiz questions in `QuestionStatsModel` (Decision D2).
    - `403 Forbidden`: Non-owner instructor.
    - `404 Not Found`: Nonexistent topic.
- `PUT /api/v1/courses/{id}/topics/order` & `PUT /api/v1/courses/{id}/topics/reorder`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, Decision D3)
  - **Request Body**: `{"topic_ids": [3, 1, 2]}` or `{"topics": [{"topic_id": 3, "order_index": 0}, ...]}`
  - **Responses**: `200 OK` — `TopicListResponse` with atomically updated order indices.
- `POST /api/v1/topics/{id}/prerequisites` & `POST /api/v1/courses/{course_id}/topics/{id}/prerequisites`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, FR-08, FR-09)
  - **Request Body**: `{"prerequisite_topic_id": 2}`
  - **Validation**:
    - `201 Created`: Prerequisite relationship established.
    - `400 Bad Request`: Self-prerequisite (`id == prerequisite_topic_id`), cross-course prerequisite, or circular prerequisite dependency (DFS cycle detection algorithm).
    - `403 Forbidden`: Non-owner instructor.
- `DELETE /api/v1/topics/{id}/prerequisites/{prerequisite_id}`
  - **Access**: Course Owner Only
  - **Status**: **Implemented & Verified** (Stage 5, FR-08)
  - **Responses**: `200 OK` / `403 Forbidden` / `404 Not Found`.

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

### 5.1 Personalized Course Learning Path
- `GET /api/v1/courses/{id}/learning-path`
  - **Access**: 
    - **Enrolled Student**: Can only view their own path (NFR-06).
    - **Course Owner (Instructor)**: Can view their own path or supply `?student_id=<id>` to inspect a specific student's path (Decision 5).
  - **Query Parameters**:
    - `student_id` (optional, integer): Target student ID (instructor only override).
  - **Status Codes**:
    - `200 OK`: Learning path successfully generated.
    - `401 Unauthorized`: Missing or invalid Bearer JWT token.
    - `403 Forbidden`: Student not enrolled, student attempting to view another student's path, or instructor not course owner.
    - `404 Not Found`: Course ID does not exist.
  - **Responses**: `200 OK`
    ```json
    {
      "course_id": 1,
      "student_id": 101,
      "total_topics": 3,
      "unlocked_count": 2,
      "completed_count": 1,
      "completion_percentage": 33.33,
      "path": [
        {
          "topic_id": 1,
          "title": "Syntax & Variables",
          "description": "Foundational Python syntax",
          "order_index": 0,
          "status": "Proficient",
          "score": 0.90,
          "is_unlocked": true,
          "is_recommended": false,
          "locked_reason": null,
          "prerequisite_topic_ids": [],
          "rationale": null
        },
        {
          "topic_id": 2,
          "title": "Conditionals",
          "description": "Branching and boolean logic",
          "order_index": 1,
          "status": "Weak",
          "score": 0.35,
          "is_unlocked": true,
          "is_recommended": true,
          "locked_reason": null,
          "prerequisite_topic_ids": [1],
          "rationale": "Topic is Weak (score: 0.35) and requires reinforcement."
        },
        {
          "topic_id": 3,
          "title": "Loops",
          "description": "For and while loops",
          "order_index": 2,
          "status": "Not Assessed",
          "score": 0.0,
          "is_unlocked": false,
          "is_recommended": false,
          "locked_reason": "Prerequisite 'Conditionals' not yet Proficient (current level: Weak)",
          "prerequisite_topic_ids": [2],
          "rationale": null
        }
      ]
    }
    ```
  - *Status*: **Implemented & Fully Verified (FR-18, FR-19, FR-20, FR-25).**

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
