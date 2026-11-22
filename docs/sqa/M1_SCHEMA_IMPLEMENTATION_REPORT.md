# AdaptLearn M1 — Stage 3: Pydantic Schemas & Validation Report
## Module 1: User & Course Management (DTOs, Validation Rules & Serialization)

**Document Reference:** `docs/sqa/M1_SCHEMA_IMPLEMENTATION_REPORT.md`  
**Document Type:** Software Quality Assurance Schema Implementation & Test Verification Report  
**Author:** Hiba Zulfiqar (`2023246`) — Lead for M1 (User & Course Management) & M4 (Personalized Learning Paths)  
**Target Reviewers / Approvers:** Toqeer Ahmed (`2023567`, M3/M5 Lead), Mustajaab Ul Fida Qadri (`2023728`, M2 Lead)  
**Git Branch:** `feature/m1-course-management`  
**Baseline Commit:** `fb4d3c55d56e6a6517e0dc86968ed5e2947bfa5f`  
**Focused Schema Test Suite:** **30/30 passed (100% green)**  
**Full Test Suite:** **190 passed, 0 failed, 0 skipped (100% green)**  
**Status:** **STAGE 3 COMPLETE — SCHEMAS IMPLEMENTED & FULLY VERIFIED**  
**Date:** November 21, 2026  

---

## 1. Executive Summary

In accordance with the repository architecture, Pydantic v2 conventions, and the approved technical decisions ([`M1_M4_TEAM_APPROVAL_PROPOSAL.md`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md)), the complete set of Pydantic request and response schemas for **Module 1 (User & Course Management)** has been implemented and tested.

### Key Milestones Accomplished
1. **Pydantic v2 Architecture:** Created [`backend/app/schemas/course.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/app/schemas/course.py) utilizing `BaseModel`, `Field`, `field_validator`, and `ConfigDict(from_attributes=True)` to enable seamless serialization directly from SQLAlchemy ORM entities.
2. **Comprehensive Coverage (9 Areas):**
   - Course Creation (`CourseCreate`)
   - Course Updates (`CourseUpdate`)
   - Course Responses (`CourseResponse`)
   - Course Listing (`CourseListResponse`)
   - Topic Creation (`TopicCreate`)
   - Topic Updates (`TopicUpdate`)
   - Topic Responses (`TopicResponse`, `TopicListResponse`)
   - Prerequisite Representation (`TopicPrerequisiteCreate`, `TopicPrerequisiteResponse`, `TopicReorderRequest`)
   - Enrollment Requests & Responses (`EnrollmentRequest`, `EnrollmentResponse`, `UserEnrollmentsResponse`)
3. **Rigorous Validation & Normalization:**
   - Course codes: Alphanumeric and hyphens/underscores (`r"^[A-Za-z0-9\-_]+$"`), length 3–50 chars, auto-normalized to uppercase and stripped of whitespace (Decision D1).
   - Topic ordering: Bounds validation (`ge=0`), batch reordering validation preventing duplicate topic IDs or duplicate order indices in payloads.
   - Prerequisites: Identifier validation (`ge=1`).
4. **100% Test Pass Rate:** 30 focused schema unit tests authored and passed in 0.19s; full regression suite of **190 tests passed** with zero regressions across M2, M3, and M5.

---

## 2. Implemented Schema Architecture & Validation Rules

```
                             M1 Pydantic Schema Ecosystem
 ┌─────────────────────────┐                            ┌─────────────────────────┐
 │      CourseCreate       │                            │       TopicCreate       │
 ├─────────────────────────┤                            ├─────────────────────────┤
 │ title (1-200 chars)     │                            │ title (1-200 chars)     │
 │ description (opt, 2000) │                            │ description (opt, 2000) │
 │ course_code (UQ, 3-50)  │◀── Decision D1             │ order_index (ge=0)      │
 └───────────┬─────────────┘                            └────────────┬────────────┘
             │                                                       │
             ▼                                                       ▼
 ┌─────────────────────────┐                            ┌─────────────────────────┐
 │     CourseResponse      │                            │      TopicResponse      │
 ├─────────────────────────┤                            ├─────────────────────────┤
 │ id (int), title (str)   │                            │ id, course_id, title    │
 │ course_code (str)       │                            │ order_index, is_active  │
 │ instructor_id (int)     │                            │ prereq_topic_ids (list) │
 │ is_archived (bool)      │◀── Decision D3             │ created_at, updated_at  │
 │ topic_count, enroll_cnt │                            └─────────────────────────┘
 └─────────────────────────┘                                         │
             ▲                                                       ▼
             │                                          ┌─────────────────────────┐
             │                                          │   TopicReorderRequest   │
             │                                          ├─────────────────────────┤
             │                                          │ topics: list[Reorder]   │
             │                                          │ (unique IDs & indices)  │
             │                                          └─────────────────────────┘
             ▼                                                       │
 ┌─────────────────────────┐                                         ▼
 │    EnrollmentRequest    │                            ┌─────────────────────────┐
 ├─────────────────────────┤                            │ TopicPrerequisiteCreate │
 │ course_code (3-50 chars)│                            ├─────────────────────────┤
 └───────────┬─────────────┘                            │ prereq_topic_id (ge=1)  │
             ▼                                          └─────────────────────────┘
 ┌─────────────────────────┐
 │   EnrollmentResponse    │
 ├─────────────────────────┤
 │ id, student_id, course_id│◀── Decision D6
 └─────────────────────────┘
```

### 2.1 Schema Catalog & Detailed Constraints

| Schema Class | Scope / Direction | Key Attributes & Types | Validation Rules & Bounds |
| :--- | :--- | :--- | :--- |
| `CourseCreate` | Request (POST /courses) | `title: str`<br>`description: str \| None`<br>`course_code: str` | Title: 1–200 chars, non-whitespace.<br>Code: 3–50 chars, regex `^[A-Za-z0-9\-_]+$`, normalized to uppercase.<br>Desc: max 2000 chars. |
| `CourseUpdate` | Request (PATCH /courses/{id}) | `title: str \| None`<br>`description: str \| None`<br>`is_archived: bool \| None` | Partial updates: title non-empty if provided.<br>`is_archived` supports course archiving (Decision D3). |
| `CourseResponse` | Response (GET /courses/{id}) | `id: int`, `title: str`, `course_code: str`, `instructor_id: int`, `is_archived: bool`, timestamps, `topic_count: int = 0`, `enrollment_count: int = 0` | `ConfigDict(from_attributes=True)` enables direct ORM deserialization. |
| `CourseListResponse` | Response (GET /courses) | `courses: list[CourseResponse]`<br>`total: int` | Top-level aggregation for course discovery. |
| `TopicCreate` | Request (POST /courses/{id}/topics) | `title: str`<br>`description: str \| None`<br>`order_index: int = 0` | Title: 1–200 chars, non-whitespace.<br>`order_index`: `ge=0` (zero-based sequential ordering). |
| `TopicUpdate` | Request (PATCH /topics/{id}) | `title: str \| None`<br>`description: str \| None`<br>`order_index: int \| None`<br>`is_active: bool \| None` | Partial updates: `order_index >= 0` if supplied. |
| `TopicResponse` | Response (GET /topics/{id}) | `id: int`, `course_id: int`, `title: str`, `order_index: int`, `is_active: bool`, `prerequisite_topic_ids: list[int]`, timestamps | Prerequisite IDs extracted as flat integer list for frontend/API consumers. |
| `TopicListResponse` | Response (GET /courses/{id}/topics) | `course_id: int`, `topics: list[TopicResponse]`, `total: int` | Sorted collection of course topics. |
| `TopicReorderItem` | Sub-schema | `topic_id: int` (`ge=1`), `order_index: int` (`ge=0`) | Individual topic repositioning directive. |
| `TopicReorderRequest`| Request (PUT /courses/{id}/topics/order) | `topics: list[TopicReorderItem]` | `min_length=1`. Validates that payload contains zero duplicate `topic_id`s and zero duplicate `order_index` positions. |
| `TopicPrerequisiteCreate`| Request (POST /topics/{id}/prerequisites) | `prerequisite_topic_id: int` | `ge=1`: Must be a valid positive topic ID. |
| `TopicPrerequisiteResponse`| Response | `id: int`, `topic_id: int`, `prerequisite_topic_id: int`, `created_at: datetime` | Confirmed dependency link. |
| `EnrollmentRequest` | Request (POST /courses/{id}/enroll) | `course_code: str` | Student self-enrollment code: 3–50 chars, auto-uppercased. |
| `EnrollmentResponse`| Response | `id: int`, `student_id: int`, `course_id: int` | Exact columns matching Decision D6. |
| `UserEnrollmentsResponse`| Response (GET /users/me/enrollments) | `student_id: int`, `enrolled_courses: list[CourseResponse]`, `total: int` | Student's enrolled course catalog. |

---

## 3. Modified and Created Files Catalog

| File Path | Action | Description |
| :--- | :---: | :--- |
| `backend/app/schemas/course.py` | **NEW** | Implementation of all 15 M1 Pydantic validation and serialization schemas. |
| `backend/app/schemas/__init__.py` | **MODIFIED** | Re-exports all M1 schemas for clean package-level importing. |
| `backend/tests/unit/test_course_schemas.py` | **NEW** | 30 comprehensive unit tests covering valid payloads, normalization, missing fields, regex rejections, and boundary cases. |

---

## 4. Test Verification & Boundary Case Matrix

The unit test suite [`backend/tests/unit/test_course_schemas.py`](file:///C:/Users/hiba2/Desktop/SQA-SCD%20Project/AdaptLearn/backend/tests/unit/test_course_schemas.py) was executed to verify every schema boundary:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              FOCUSED SCHEMA TEST MATRIX                                │
├────┬──────────────────────────────────────┬─────────────────────────────┬──────────┤
│ #  │ Test Scenario & Boundary Condition   │ Executed Test Method        │ Result   │
├────┼──────────────────────────────────────┼─────────────────────────────┼──────────┤
│ 1  │ Valid course creation & uppercase    │ test_course_create_valid    │ PASSED   │
│ 2  │ Optional description handling        │ test_course_create_desc...  │ PASSED   │
│ 3  │ Missing required fields rejection    │ test_course_create_missing..│ PASSED   │
│ 4  │ Whitespace-only title rejection      │ test_course_create_empty... │ PASSED   │
│ 5  │ Code boundary: length < 3 chars      │ test_course_create_inv[c]   │ PASSED   │
│ 6  │ Code boundary: length > 50 chars     │ test_course_create_inv[c*51]│ PASSED   │
│ 7  │ Code format: spaces rejected         │ test_course_create_inv[CS 1]│ PASSED   │
│ 8  │ Code format: special chars rejected  │ test_course_create_inv[CS@!]│ PASSED   │
│ 9  │ Code format: whitespace rejected     │ test_course_create_inv[   ] │ PASSED   │
│ 10 │ Partial course update validation     │ test_course_update_valid_...│ PASSED   │
│ 11 │ Course update empty title rejected   │ test_course_update_empty... │ PASSED   │
│ 12 │ CourseResponse default counts        │ test_course_response_ser... │ PASSED   │
│ 13 │ CourseListResponse aggregation       │ test_course_list_response   │ PASSED   │
│ 14 │ Valid topic creation & explicit order│ test_topic_create_valid     │ PASSED   │
│ 15 │ Topic order defaults to 0            │ test_topic_create_default...│ PASSED   │
│ 16 │ Topic negative order index rejected  │ test_topic_create_negative..│ PASSED   │
│ 17 │ Topic empty title rejected           │ test_topic_create_empty...  │ PASSED   │
│ 18 │ Topic partial update valid           │ test_topic_update_valid     │ PASSED   │
│ 19 │ Valid batch topic reordering         │ test_topic_reorder_req...   │ PASSED   │
│ 20 │ Duplicate topic_id in reorder payload│ test_topic_reorder_dup_id   │ PASSED   │
│ 21 │ Duplicate order_index in reorder req │ test_topic_reorder_dup_idx  │ PASSED   │
│ 22 │ Empty reorder list rejected          │ test_topic_reorder_empty... │ PASSED   │
│ 23 │ TopicResponse default prereq list    │ test_topic_response_defaults│ PASSED   │
│ 24 │ Valid prerequisite ID validation     │ test_prereq_create_valid    │ PASSED   │
│ 25 │ Prerequisite non-positive ID reject  │ test_prereq_create_non_pos..│ PASSED   │
│ 26 │ Prerequisite response serialization  │ test_prereq_response_ser... │ PASSED   │
│ 27 │ Enrollment request code uppercase    │ test_enrollment_request_val.│ PASSED   │
│ 28 │ Enrollment empty code rejected       │ test_enrollment_request_emp.│ PASSED   │
│ 29 │ EnrollmentResponse serialization     │ test_enrollment_response_ser│ PASSED   │
│ 30 │ UserEnrollmentsResponse aggregation  │ test_user_enrollments_resp  │ PASSED   │
└────┴──────────────────────────────────────┴─────────────────────────────┴──────────┘
```

### 4.1 Pytest Execution Logs

```powershell
cd backend
.\venv\Scripts\pytest.exe tests/unit/test_course_schemas.py -v
```
**Focused Schema Test Result:** `30 passed in 0.19s`

```powershell
cd backend
.\venv\Scripts\pytest.exe
```
**Full Regression Test Suite Result:** `190 passed, 8 warnings in 22.89s (100% Pass Rate)`

**Regression Evaluation:** Zero regressions in existing test modules (`test_layers.py`, `test_adaptive_api.py`, `test_cross_module_integration.py`, `test_progress_api.py`, `test_security_auth.py`).

---

## 5. Unresolved Issues & Observations

1. **Unresolved Issues:** **None.** All schemas conform strictly to Pydantic v2 conventions and handle edge-case validation gracefully.
2. **Layer Isolation:** In strict conformance with the prompt instructions, no repositories, application services, or FastAPI API endpoints were created or modified during this stage.

---

## 6. Current Git Working-Tree Status

```powershell
cd "C:\Users\hiba2\Desktop\SQA-SCD Project\AdaptLearn"
git status --short
```

```text
 M backend/app/models/__init__.py
 M backend/app/models/progress.py
 M backend/app/repositories/progress_repository.py
 M backend/app/schemas/__init__.py
?? backend/app/models/course.py
?? backend/app/schemas/course.py
?? backend/tests/unit/test_course_models.py
?? backend/tests/unit/test_course_schemas.py
?? docs/sqa/M1_DATABASE_MODEL_IMPACT_AUDIT.md
?? docs/sqa/M1_M4_ENVIRONMENT_AND_BASELINE_TEST_REPORT.md
?? docs/sqa/M1_M4_PRE_IMPLEMENTATION_READINESS.md
?? docs/sqa/M1_M4_REQUIREMENTS_RECONCILIATION.md
?? docs/sqa/M1_M4_TEAM_APPROVAL_PROPOSAL.md
?? docs/sqa/M1_M4_WORKSPACE_BASELINE.md
?? docs/sqa/M1_MODEL_IMPLEMENTATION_REPORT.md
?? docs/sqa/M1_SCHEMA_IMPLEMENTATION_REPORT.md
```

- **Branch:** `feature/m1-course-management`
- **Head Commit:** `fb4d3c5`
- Zero commits or pushes performed.

---

## 7. Conclusion & Next Stage

Stage 3 (Pydantic Schemas & Validation) is **100% complete and verified**. The project is ready for **Stage 4 (Data Access Repository in `backend/app/repositories/course_repository.py`)**.
