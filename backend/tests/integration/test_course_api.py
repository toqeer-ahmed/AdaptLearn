"""Integration tests for Module 1: Course and Topic Management API Endpoints.

Requirements Traceability:
- FR-04: Course creation, unique course codes, instructor ownership.
- FR-05: Course lifecycle, editing, and archiving.
- FR-06: Topic creation, retrieval, sequential ordering.
- FR-07: Sequential topic reordering with transactional integrity.
- FR-08: Topic prerequisite relationships and dependencies.
- FR-09: Prerequisite graph integrity and cycle detection.
- FR-10: Student course enrollment.
- Decisions: D1 (course code uppercase/alphanumeric), D2 (topic deletion restriction),
             D3 (archiving lifecycle), D6 (enrollment table adoption), D7 (instructor ownership).
- Non-Functional:
  - NFR-04: Bearer token authentication on all protected endpoints.
  - NFR-05: Server-side role & ownership access control.
  - NFR-06: Student privacy protection — students cannot access other students' records.
"""

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.db.session import SessionLocal
from app.main import app
from app.models.progress import QuestionStatsModel
from app.repositories.course_repository import get_course_repository
from app.repositories.progress_repository import get_progress_repository
from app.repositories.user_repository import get_user_repository


@pytest.fixture(autouse=True)
def clean_repositories():
    """Reset repository stores and clean database tables before and after each test."""
    u_repo = get_user_repository()
    p_repo = get_progress_repository()
    c_repo = get_course_repository()

    u_repo.seed_default_users()
    c_repo.clear()
    p_repo.clear()

    # Seed second student (Bob, ID 102) for privacy tests
    if not u_repo.get_by_id(102):
        u_repo.create_user(
            name="Bob Student",
            email="bob@student.adaptlearn.edu",
            password_hash=hash_password("Password123!"),
            role="student",
        )

    yield

    c_repo.clear()
    p_repo.clear()


@pytest.fixture
def client():
    """FastAPI test client instance."""
    return TestClient(app)


@pytest.fixture
def instructor1_auth():
    """Auth header for Instructor Ada Lovelace (ID 1, Owner)."""
    token = create_access_token({"sub": "1", "role": "instructor"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def instructor2_auth():
    """Auth header for Instructor Alan Turing (ID 2, Non-Owner)."""
    token = create_access_token({"sub": "2", "role": "instructor"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student1_auth():
    """Auth header for Student Alice (ID 101)."""
    token = create_access_token({"sub": "101", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def student2_auth():
    """Auth header for Student Bob (ID 102)."""
    token = create_access_token({"sub": "102", "role": "student"})
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# 1. Course Management Endpoint Tests (FR-04, FR-05, Decisions D1, D3, D7)
# =============================================================================


class TestCourseManagementApi:
    """Integration test suite for course management API endpoints."""

    def test_create_course_success_as_instructor(self, client, instructor1_auth):
        """Instructor can create a course; returns 201 and normalized uppercase course code (D1)."""
        payload = {
            "title": "Software Quality Assurance",
            "description": "Comprehensive SQA principles and verification",
            "course_code": "sqa-423-2026",
        }
        response = client.post("/api/v1/courses", json=payload, headers=instructor1_auth)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] > 0
        assert data["title"] == "Software Quality Assurance"
        assert data["course_code"] == "SQA-423-2026"  # Uppercase normalized (D1)
        assert data["instructor_id"] == 1
        assert data["is_archived"] is False
        assert data["topic_count"] == 0
        assert data["enrollment_count"] == 0

    def test_create_course_unauthenticated_fails_401(self, client):
        """Missing Authorization header returns 401 Unauthorized."""
        payload = {"title": "Test Course", "course_code": "TC-101"}
        response = client.post("/api/v1/courses", json=payload)
        assert response.status_code == 401

    def test_create_course_forbidden_for_student_403(self, client, student1_auth):
        """Student attempting to create a course receives 403 Forbidden."""
        payload = {"title": "Student Course", "course_code": "SC-101"}
        response = client.post("/api/v1/courses", json=payload, headers=student1_auth)
        assert response.status_code == 403

    def test_create_course_duplicate_code_conflict_409(self, client, instructor1_auth):
        """Duplicate course code returns 409 Conflict (Decision D1)."""
        payload = {"title": "Course 1", "course_code": "DUP-CODE"}
        res1 = client.post("/api/v1/courses", json=payload, headers=instructor1_auth)
        assert res1.status_code == 201

        res2 = client.post("/api/v1/courses", json=payload, headers=instructor1_auth)
        assert res2.status_code == 409
        assert "already registered" in res2.json()["error"]["message"]

    def test_create_course_validation_failure_422(self, client, instructor1_auth):
        """Invalid course code (< 3 chars) returns 422 Unprocessable Entity."""
        payload = {"title": "Short Code", "course_code": "AB"}
        response = client.post("/api/v1/courses", json=payload, headers=instructor1_auth)
        assert response.status_code == 422

    def test_course_title_length_boundaries(self, client, instructor1_auth):
        """Course title of 200 characters succeeds; 201 characters fails with 422."""
        title_200 = "A" * 200
        res_valid = client.post(
            "/api/v1/courses",
            json={"title": title_200, "course_code": "TITLE-200"},
            headers=instructor1_auth,
        )
        assert res_valid.status_code == 201
        assert res_valid.json()["title"] == title_200

        title_201 = "A" * 201
        res_invalid = client.post(
            "/api/v1/courses",
            json={"title": title_201, "course_code": "TITLE-201"},
            headers=instructor1_auth,
        )
        assert res_invalid.status_code == 422

    def test_list_and_get_courses(self, client, instructor1_auth, student1_auth):
        """List courses with instructor and archive filtering."""
        c1 = client.post(
            "/api/v1/courses",
            json={"title": "Course A", "course_code": "CRS-A"},
            headers=instructor1_auth,
        ).json()
        c2 = client.post(
            "/api/v1/courses",
            json={"title": "Course B", "course_code": "CRS-B"},
            headers=instructor1_auth,
        ).json()

        # List all active courses
        list_res = client.get("/api/v1/courses", headers=student1_auth)
        assert list_res.status_code == 200
        courses = list_res.json()["courses"]
        assert len(courses) >= 2
        course_ids = [c["id"] for c in courses]
        assert c1["id"] in course_ids
        assert c2["id"] in course_ids

        # Get specific course details
        get_res = client.get(f"/api/v1/courses/{c1['id']}", headers=student1_auth)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == c1["id"]

    def test_get_course_not_found_404(self, client, instructor1_auth):
        """Requesting nonexistent course returns 404 Not Found."""
        response = client.get("/api/v1/courses/99999", headers=instructor1_auth)
        assert response.status_code == 404

    def test_update_course_as_owner(self, client, instructor1_auth):
        """Owner instructor can update course title and description via PUT and PATCH."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Original Title", "course_code": "UPD-CRS"},
            headers=instructor1_auth,
        ).json()

        # PUT update
        put_res = client.put(
            f"/api/v1/courses/{course['id']}",
            json={"title": "Updated Title", "description": "New description"},
            headers=instructor1_auth,
        )
        assert put_res.status_code == 200
        assert put_res.json()["title"] == "Updated Title"
        assert put_res.json()["description"] == "New description"

        # PATCH update
        patch_res = client.patch(
            f"/api/v1/courses/{course['id']}",
            json={"title": "Patched Title"},
            headers=instructor1_auth,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["title"] == "Patched Title"

    def test_update_course_forbidden_for_non_owner_403(
        self, client, instructor1_auth, instructor2_auth
    ):
        """Non-owner instructor attempting to update course receives 403 Forbidden."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Owner Course", "course_code": "OWN-CRS"},
            headers=instructor1_auth,
        ).json()

        response = client.put(
            f"/api/v1/courses/{course['id']}",
            json={"title": "Hacked Title"},
            headers=instructor2_auth,
        )
        assert response.status_code == 403

    def test_archive_and_publish_course_lifecycle(self, client, instructor1_auth, instructor2_auth):
        """Course archiving and unarchiving lifecycle (Decision D3)."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Lifecycle Course", "course_code": "LIFECYCLE-1"},
            headers=instructor1_auth,
        ).json()

        # Non-owner cannot archive (403)
        res_forbidden = client.post(
            f"/api/v1/courses/{course['id']}/archive", headers=instructor2_auth
        )
        assert res_forbidden.status_code == 403

        # Owner archives course
        res_archived = client.post(
            f"/api/v1/courses/{course['id']}/archive", headers=instructor1_auth
        )
        assert res_archived.status_code == 200
        assert res_archived.json()["is_archived"] is True

        # Archived course rejects metadata modifications (Decision D3, 400 Bad Request)
        res_edit = client.put(
            f"/api/v1/courses/{course['id']}",
            json={"title": "New Title When Archived"},
            headers=instructor1_auth,
        )
        assert res_edit.status_code == 400
        assert (
            "Cannot edit title or description of an archived course"
            in res_edit.json()["error"]["message"]
        )

        # Owner unarchives course
        res_publish = client.post(
            f"/api/v1/courses/{course['id']}/publish", headers=instructor1_auth
        )
        assert res_publish.status_code == 200
        assert res_publish.json()["is_archived"] is False

    def test_archived_course_visibility_policy(
        self, client, instructor1_auth, instructor2_auth, student1_auth, student2_auth
    ):
        """Archived course read-only access is restricted to enrolled students & owner (Decision D3)."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Archived Vis", "course_code": "ARCH-VIS-1"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]

        # Student 1 enrolls while active
        enroll_res = client.post(
            f"/api/v1/courses/{cid}/enroll",
            json={"course_code": "ARCH-VIS-1"},
            headers=student1_auth,
        )
        assert enroll_res.status_code == 200

        # Owner archives course
        client.post(f"/api/v1/courses/{cid}/archive", headers=instructor1_auth)

        # Enrolled student can still view course (200 OK)
        res_student1 = client.get(f"/api/v1/courses/{cid}", headers=student1_auth)
        assert res_student1.status_code == 200

        # Owner instructor can still view course (200 OK)
        res_owner = client.get(f"/api/v1/courses/{cid}", headers=instructor1_auth)
        assert res_owner.status_code == 200

        # Non-enrolled student is rejected (403 Forbidden)
        res_student2 = client.get(f"/api/v1/courses/{cid}", headers=student2_auth)
        assert res_student2.status_code == 403

        # Non-owner instructor is rejected (403 Forbidden)
        res_inst2 = client.get(f"/api/v1/courses/{cid}", headers=instructor2_auth)
        assert res_inst2.status_code == 403


# =============================================================================
# 2. Topic Management Endpoint Tests (FR-06, FR-07, Decisions D2, D3)
# =============================================================================


class TestTopicManagementApi:
    """Integration test suite for topic creation, ordering, updates, and deletion."""

    def test_create_and_list_topics(self, client, instructor1_auth, student1_auth):
        """Add topics to a course and retrieve them ordered sequentially."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Topic Course", "course_code": "TOP-CRS"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]

        t1 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Intro", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t2 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Advanced", "order_index": 1},
            headers=instructor1_auth,
        ).json()

        assert t1["id"] > 0
        assert t2["id"] > 0

        # List topics ordered
        list_res = client.get(f"/api/v1/courses/{cid}/topics", headers=student1_auth)
        assert list_res.status_code == 200
        topics = list_res.json()["topics"]
        assert len(topics) == 2
        assert topics[0]["title"] == "Intro"
        assert topics[1]["title"] == "Advanced"

    def test_create_topic_in_archived_course_rejected_400(self, client, instructor1_auth):
        """Cannot add topics to an archived course (400 Bad Request, Decision D3)."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Archived Course", "course_code": "TOP-ARCH"},
            headers=instructor1_auth,
        ).json()
        client.post(f"/api/v1/courses/{course['id']}/archive", headers=instructor1_auth)

        response = client.post(
            f"/api/v1/courses/{course['id']}/topics",
            json={"title": "Late Topic", "order_index": 0},
            headers=instructor1_auth,
        )
        assert response.status_code == 400
        assert "Cannot add topics to an archived course" in response.json()["error"]["message"]

    def test_update_topic_as_owner(self, client, instructor1_auth, instructor2_auth):
        """Owner can update topic; non-owner is rejected with 403."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Course", "course_code": "UPD-TOP-CRS"},
            headers=instructor1_auth,
        ).json()
        topic = client.post(
            f"/api/v1/courses/{course['id']}/topics",
            json={"title": "Old Name", "order_index": 0},
            headers=instructor1_auth,
        ).json()

        # Non-owner fails
        res_forbidden = client.put(
            f"/api/v1/topics/{topic['id']}", json={"title": "Hacked"}, headers=instructor2_auth
        )
        assert res_forbidden.status_code == 403

        # Owner succeeds
        res_ok = client.put(
            f"/api/v1/topics/{topic['id']}", json={"title": "New Name"}, headers=instructor1_auth
        )
        assert res_ok.status_code == 200
        assert res_ok.json()["title"] == "New Name"

    def test_atomic_topic_reordering(self, client, instructor1_auth):
        """Reorder topics atomically using both topic_ids format and topics list format."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Reorder Course", "course_code": "REORD-CRS"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]
        t1 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "T1", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t2 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "T2", "order_index": 1},
            headers=instructor1_auth,
        ).json()
        t3 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "T3", "order_index": 2},
            headers=instructor1_auth,
        ).json()

        # Reorder via topic_ids format (docs/api.md §2.3)
        res_order = client.put(
            f"/api/v1/courses/{cid}/topics/order",
            json={"topic_ids": [t3["id"], t1["id"], t2["id"]]},
            headers=instructor1_auth,
        )
        assert res_order.status_code == 200
        topics = res_order.json()["topics"]
        assert topics[0]["id"] == t3["id"]
        assert topics[1]["id"] == t1["id"]
        assert topics[2]["id"] == t2["id"]

    def test_delete_topic_success_and_safety_checks(self, client, instructor1_auth):
        """Unreferenced topic deletes successfully; topic with quiz questions rejects with 400 (D2)."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Del Course", "course_code": "DEL-CRS"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]
        t_free = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Free Topic", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t_linked = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Linked Topic", "order_index": 1},
            headers=instructor1_auth,
        ).json()

        # Simulate quiz question referencing t_linked in QuestionStatsModel (Decision D2)
        with SessionLocal() as db:
            q_stat = QuestionStatsModel(
                course_id=cid,
                question_id=901,
                question_text="Sample SQA Question",
                topic_id=t_linked["id"],
                topic_name="Linked Topic",
                difficulty="Medium",
                times_answered=5,
                correct_count=4,
            )
            db.add(q_stat)
            db.commit()

        # Attempt to delete t_linked -> 400 Bad Request
        del_linked_res = client.delete(f"/api/v1/topics/{t_linked['id']}", headers=instructor1_auth)
        assert del_linked_res.status_code == 400
        assert (
            "Cannot delete topic referenced by existing quiz questions"
            in del_linked_res.json()["error"]["message"]
        )

        # Delete unreferenced t_free -> 200 OK
        del_free_res = client.delete(f"/api/v1/topics/{t_free['id']}", headers=instructor1_auth)
        assert del_free_res.status_code == 200

    def test_delete_topic_cascades_prerequisite_edges(self, client, instructor1_auth):
        """Deleting a topic cleanly cascades its incoming and outgoing prerequisite edges."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Cascade Course", "course_code": "CAS-CRS"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]
        t1 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Topic A", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t2 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Topic B", "order_index": 1},
            headers=instructor1_auth,
        ).json()

        # Add prerequisite edge: T2 requires T1
        client.post(
            f"/api/v1/topics/{t2['id']}/prerequisites",
            json={"prerequisite_topic_id": t1["id"]},
            headers=instructor1_auth,
        )

        # Delete T1 (the prerequisite)
        del_res = client.delete(f"/api/v1/topics/{t1['id']}", headers=instructor1_auth)
        assert del_res.status_code == 200

        # Verify T2 still exists and its prerequisites list is now empty
        t2_res = client.get(f"/api/v1/topics/{t2['id']}", headers=instructor1_auth)
        assert t2_res.status_code == 200
        assert t2_res.json()["prerequisite_topic_ids"] == []


# =============================================================================
# 3. Prerequisite Management Endpoint Tests (FR-08, FR-09)
# =============================================================================


class TestPrerequisiteManagementApi:
    """Integration test suite for prerequisite edge addition, cycles, and deletion."""

    def test_prerequisite_addition_and_cycle_prevention(self, client, instructor1_auth):
        """Add prerequisite, reject self, reject cross-course, reject circular dependency (DFS)."""
        c1 = client.post(
            "/api/v1/courses",
            json={"title": "Prereq C1", "course_code": "PRE-C1"},
            headers=instructor1_auth,
        ).json()
        c2 = client.post(
            "/api/v1/courses",
            json={"title": "Prereq C2", "course_code": "PRE-C2"},
            headers=instructor1_auth,
        ).json()

        t1 = client.post(
            f"/api/v1/courses/{c1['id']}/topics",
            json={"title": "T1", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t2 = client.post(
            f"/api/v1/courses/{c1['id']}/topics",
            json={"title": "T2", "order_index": 1},
            headers=instructor1_auth,
        ).json()
        t3 = client.post(
            f"/api/v1/courses/{c1['id']}/topics",
            json={"title": "T3", "order_index": 2},
            headers=instructor1_auth,
        ).json()
        t_ext = client.post(
            f"/api/v1/courses/{c2['id']}/topics",
            json={"title": "Ext", "order_index": 0},
            headers=instructor1_auth,
        ).json()

        # 1. Self-prerequisite rejected (400)
        self_res = client.post(
            f"/api/v1/topics/{t1['id']}/prerequisites",
            json={"prerequisite_topic_id": t1["id"]},
            headers=instructor1_auth,
        )
        assert self_res.status_code == 400

        # 2. Cross-course prerequisite rejected (400)
        cross_res = client.post(
            f"/api/v1/topics/{t1['id']}/prerequisites",
            json={"prerequisite_topic_id": t_ext["id"]},
            headers=instructor1_auth,
        )
        assert cross_res.status_code == 400

        # 3. Add valid prerequisites: T2 requires T1, T3 requires T2
        p1 = client.post(
            f"/api/v1/topics/{t2['id']}/prerequisites",
            json={"prerequisite_topic_id": t1["id"]},
            headers=instructor1_auth,
        )
        assert p1.status_code == 201
        p2 = client.post(
            f"/api/v1/topics/{t3['id']}/prerequisites",
            json={"prerequisite_topic_id": t2["id"]},
            headers=instructor1_auth,
        )
        assert p2.status_code == 201

        # 4. Circular dependency: T1 requires T3 creates T1 -> T3 -> T2 -> T1 cycle (400)
        cycle_res = client.post(
            f"/api/v1/topics/{t1['id']}/prerequisites",
            json={"prerequisite_topic_id": t3["id"]},
            headers=instructor1_auth,
        )
        assert cycle_res.status_code == 400
        assert "cycle" in cycle_res.json()["error"]["message"].lower()

        # 5. Remove prerequisite relationship
        del_p = client.delete(
            f"/api/v1/topics/{t2['id']}/prerequisites/{t1['id']}", headers=instructor1_auth
        )
        assert del_p.status_code == 200

    def test_duplicate_prerequisite_edge_rejected_409(self, client, instructor1_auth):
        """Adding a duplicate prerequisite edge returns 409 Conflict."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Dup Prereq Course", "course_code": "DUP-PRE"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]
        t1 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Topic 1", "order_index": 0},
            headers=instructor1_auth,
        ).json()
        t2 = client.post(
            f"/api/v1/courses/{cid}/topics",
            json={"title": "Topic 2", "order_index": 1},
            headers=instructor1_auth,
        ).json()

        # Add prerequisite edge: T2 requires T1
        res1 = client.post(
            f"/api/v1/topics/{t2['id']}/prerequisites",
            json={"prerequisite_topic_id": t1["id"]},
            headers=instructor1_auth,
        )
        assert res1.status_code == 201

        # Attempt to add exact same prerequisite edge again -> 409 Conflict
        res2 = client.post(
            f"/api/v1/topics/{t2['id']}/prerequisites",
            json={"prerequisite_topic_id": t1["id"]},
            headers=instructor1_auth,
        )
        assert res2.status_code == 409
        assert "already a prerequisite" in res2.json()["error"]["message"]


# =============================================================================
# 4. Enrollment Endpoint Tests (FR-10, Decisions D3, D6, NFR-06)
# =============================================================================


class TestEnrollmentApi:
    """Integration test suite for student course enrollment and roster inspection."""

    def test_student_enrollment_lifecycle(
        self, client, instructor1_auth, student1_auth, student2_auth
    ):
        """Student enrolls in active course; duplicate is rejected with 409; student views own enrollments."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Enrollment Course", "course_code": "ENR-CRS"},
            headers=instructor1_auth,
        ).json()
        cid = course["id"]

        # Enroll student 1
        res_enroll = client.post(
            f"/api/v1/courses/{cid}/enroll",
            json={"course_code": "ENR-CRS"},
            headers=student1_auth,
        )
        assert res_enroll.status_code == 200
        data = res_enroll.json()
        assert data["student_id"] == 101
        assert data["course_id"] == cid

        # Duplicate enrollment rejected with 409 Conflict
        res_dup = client.post(
            f"/api/v1/courses/{cid}/enroll",
            json={"course_code": "ENR-CRS"},
            headers=student1_auth,
        )
        assert res_dup.status_code == 409

        # Check enrollment status
        res_chk = client.get(f"/api/v1/courses/{cid}/enrollment", headers=student1_auth)
        assert res_chk.status_code == 200
        assert res_chk.json()["student_id"] == 101

        # List enrolled courses for student
        res_list = client.get("/api/v1/courses/enrolled", headers=student1_auth)
        assert res_list.status_code == 200
        assert res_list.json()["total"] == 1

        # Instructor views roster of enrolled students
        res_roster = client.get(f"/api/v1/courses/{cid}/students", headers=instructor1_auth)
        assert res_roster.status_code == 200
        assert 101 in res_roster.json()

    def test_student_enrollment_privacy_nfr06(
        self, client, instructor1_auth, student1_auth, student2_auth
    ):
        """Student A cannot inspect Student B's enrollments (403 Forbidden, NFR-06)."""
        res_privacy = client.get("/api/v1/students/102/enrollments", headers=student1_auth)
        assert res_privacy.status_code == 403

    def test_enrollment_in_archived_course_rejected_400(
        self, client, instructor1_auth, student1_auth
    ):
        """Cannot enroll in an archived course (400 Bad Request, Decision D3)."""
        course = client.post(
            "/api/v1/courses",
            json={"title": "Archived Course", "course_code": "ENR-ARCH"},
            headers=instructor1_auth,
        ).json()
        client.post(f"/api/v1/courses/{course['id']}/archive", headers=instructor1_auth)

        response = client.post(
            f"/api/v1/courses/{course['id']}/enroll",
            json={"course_code": "ENR-ARCH"},
            headers=student1_auth,
        )
        assert response.status_code == 400
        assert "Cannot enroll in an archived course" in response.json()["error"]["message"]
