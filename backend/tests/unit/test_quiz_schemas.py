"""Unit tests for Module 2: Quiz & Assessment Engine Pydantic v2 schemas and validators.

Requirements Traceability:
- FR-08: Multiple-choice question validation (2-5 options, 1 correct index, difficulty).
- FR-10: Quiz creation and configuration payload validation.
- FR-11: Student-safe question presentation schema (omission of correct answers).
- FR-13: Quiz attempt submission payload validation.
- FR-14: Graded attempt results and topic score breakdown schemas.
- FR-25: Descriptive server-side validation error messages.
- Decision D3: Single correct index in range 0..len(options)-1.
"""
import pytest
from pydantic import ValidationError

from app.schemas.quiz import (
    AnswerSubmissionItem,
    AttemptResultResponse,
    GradedAnswerResponse,
    PracticeQuizRequest,
    QuestionCreate,
    QuestionResponse,
    QuestionStudentSafe,
    QuestionUpdate,
    QuizAttemptSubmitRequest,
    QuizCreate,
    QuizStudentSafeResponse,
    TopicScoreBreakdown,
)


class TestQuestionSchemas:
    """Test validation and bounds on question schemas (FR-08, FR-25, Decision D3)."""

    def test_valid_question_create(self):
        """A well-formed question payload passes validation."""
        data = {
            "statement": "What is Equivalence Partitioning?",
            "options": ["A black-box testing technique", "A white-box metric", "A compiler optimization"],
            "correct_option_index": 0,
            "difficulty": "Medium",
            "explanation": "EP divides inputs into valid and invalid equivalence classes.",
        }
        schema = QuestionCreate(**data)
        assert schema.statement == "What is Equivalence Partitioning?"
        assert len(schema.options) == 3
        assert schema.correct_option_index == 0
        assert schema.difficulty == "Medium"
        assert schema.explanation == "EP divides inputs into valid and invalid equivalence classes."

    def test_question_statement_cannot_be_empty_or_whitespace(self):
        """Empty or whitespace-only statement raises validation error."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="   ",
                options=["Option 1", "Option 2"],
                correct_option_index=0,
                difficulty="Easy",
            )
        assert "Statement cannot be empty" in str(exc.value)

    def test_options_count_below_minimum_fails_bva(self):
        """Having fewer than 2 options is rejected (BVA: min-1 = 1)."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Only one option"],
                correct_option_index=0,
                difficulty="Easy",
            )
        assert "Options list must contain between 2 and 5 choices" in str(exc.value)

    def test_options_count_above_maximum_fails_bva(self):
        """Having more than 5 options is rejected (BVA: max+1 = 6)."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Opt 1", "Opt 2", "Opt 3", "Opt 4", "Opt 5", "Opt 6"],
                correct_option_index=0,
                difficulty="Easy",
            )
        assert "Options list must contain between 2 and 5 choices" in str(exc.value)

    def test_options_cannot_contain_empty_strings(self):
        """Any option that is empty or pure whitespace is rejected."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Valid Option 1", "   "],
                correct_option_index=0,
                difficulty="Easy",
            )
        assert "Option choices cannot be empty" in str(exc.value)

    def test_negative_correct_option_index_fails_bva(self):
        """Negative index is rejected (BVA: below min 0)."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Option 1", "Option 2"],
                correct_option_index=-1,
                difficulty="Easy",
            )
        assert "Input should be greater than or equal to 0" in str(exc.value) or "correct_option_index" in str(exc.value)

    def test_correct_option_index_equal_to_len_fails_bva(self):
        """Index equal to option count is out of bounds (BVA: len boundary)."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Option 1", "Option 2", "Option 3"],
                correct_option_index=3,  # Valid indices are 0, 1, 2
                difficulty="Easy",
            )
        assert "correct_option_index (3) out of bounds" in str(exc.value)

    def test_invalid_difficulty_level_rejected(self):
        """Difficulties outside ('Easy', 'Medium', 'Hard') are rejected."""
        with pytest.raises(ValidationError) as exc:
            QuestionCreate(
                statement="Valid statement?",
                options=["Option 1", "Option 2"],
                correct_option_index=0,
                difficulty="SuperHard",
            )
        assert "Difficulty must be one of" in str(exc.value)

    def test_difficulty_case_normalization(self):
        """Difficulty input is normalized to title case ('easy' -> 'Easy')."""
        q = QuestionCreate(
            statement="Valid statement?",
            options=["Option 1", "Option 2"],
            correct_option_index=0,
            difficulty="easy",
        )
        assert q.difficulty == "Easy"

    def test_question_student_safe_omits_answers_and_explanations(self):
        """QuestionStudentSafe schema strictly omits correct_option_index and explanation (FR-11)."""
        safe = QuestionStudentSafe(
            id=10,
            statement="Sample question",
            options=["Choice A", "Choice B"],
        )
        dumped = safe.model_dump()
        assert "correct_option_index" not in dumped
        assert "explanation" not in dumped
        assert dumped["id"] == 10
        assert dumped["statement"] == "Sample question"
        assert dumped["options"] == ["Choice A", "Choice B"]


class TestQuizSchemas:
    """Test validation on quiz authoring and presentation schemas (FR-10, FR-11)."""

    def test_valid_quiz_create(self):
        """Valid quiz payload passes validation."""
        q = QuizCreate(
            title="Software QA Quiz 1",
            description="Testing fundamentals",
            topic_id=3,
            question_ids=[101, 102, 103],
            is_published=False,
        )
        assert q.title == "Software QA Quiz 1"
        assert len(q.question_ids) == 3
        assert q.is_published is False

    def test_quiz_title_cannot_be_empty(self):
        """Empty quiz title raises validation error."""
        with pytest.raises(ValidationError) as exc:
            QuizCreate(title="   ")
        assert "Title cannot be empty" in str(exc.value)

    def test_quiz_student_safe_response(self):
        """QuizStudentSafeResponse wraps student-safe questions cleanly."""
        res = QuizStudentSafeResponse(
            id=1,
            course_id=10,
            title="Quiz 1",
            description="Instructions",
            topic_id=2,
            questions=[
                QuestionStudentSafe(id=1, statement="Q1", options=["A", "B"]),
                QuestionStudentSafe(id=2, statement="Q2", options=["C", "D"]),
            ],
        )
        data = res.model_dump()
        assert len(data["questions"]) == 2
        for q in data["questions"]:
            assert "correct_option_index" not in q
            assert "explanation" not in q


class TestQuizSubmissionAndResultSchemas:
    """Test schemas for quiz submission and graded result returns (FR-13, FR-14)."""

    def test_valid_submission_request(self):
        """Valid submission answers pass validation."""
        payload = QuizAttemptSubmitRequest(
            answers=[
                AnswerSubmissionItem(question_id=1, selected_option_index=0),
                AnswerSubmissionItem(question_id=2, selected_option_index=3),
            ]
        )
        assert len(payload.answers) == 2
        assert payload.answers[0].question_id == 1
        assert payload.answers[0].selected_option_index == 0

    def test_submission_rejects_empty_answers(self):
        """Submitting an attempt with empty answers list is rejected."""
        with pytest.raises(ValidationError) as exc:
            QuizAttemptSubmitRequest(answers=[])
        assert "Answers list cannot be empty" in str(exc.value)

    def test_submission_rejects_negative_selected_index(self):
        """Selected option index cannot be negative."""
        with pytest.raises(ValidationError):
            AnswerSubmissionItem(question_id=1, selected_option_index=-1)

    def test_attempt_result_response_structure(self):
        """AttemptResultResponse formats all required FR-14 score and answer fields."""
        res = AttemptResultResponse(
            attempt_id=200,
            quiz_id=5,
            quiz_title="Unit Testing Quiz",
            score=0.75,
            total_questions=4,
            correct_answers=3,
            submitted_at="2026-11-21T12:00:00Z",
            topic_scores=[
                TopicScoreBreakdown(topic_id=1, topic_score=1.0, correct_count=2, total_questions=2),
                TopicScoreBreakdown(topic_id=2, topic_score=0.5, correct_count=1, total_questions=2),
            ],
            answers=[
                GradedAnswerResponse(
                    question_id=10,
                    statement="Question 10",
                    options=["A", "B"],
                    selected_option_index=0,
                    correct_option_index=0,
                    is_correct=True,
                    explanation="Correct because A.",
                    topic_id=1,
                    difficulty="Easy",
                )
            ],
        )
        assert res.score == 0.75
        assert res.correct_answers == 3
        assert len(res.topic_scores) == 2
        assert res.answers[0].is_correct is True

    def test_practice_quiz_request_bounds(self):
        """PracticeQuizRequest enforces question_count bounds (1..20)."""
        valid = PracticeQuizRequest(topic_id=5, question_count=10)
        assert valid.question_count == 10

        with pytest.raises(ValidationError):
            PracticeQuizRequest(topic_id=5, question_count=0)

        with pytest.raises(ValidationError):
            PracticeQuizRequest(topic_id=5, question_count=25)
