from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from app.core.exceptions import AttemptLockedError, ConflictError, ForbiddenError
from app.db.models.enums import AttemptStatus, QuestionPurpose, QuestionStatus
from app.services.exam_rules import (
    assert_attempt_mutable,
    assert_can_start_attempt,
    assert_employee_cannot_see_key,
    assert_snapshot_immutable,
    can_start_attempt,
    hide_correct_answers,
    is_time_expired,
    passed_by_policy,
    question_eligible_for_exam,
    score_closed_question,
)
from pydantic import ValidationError


def test_attempt_limit():
    assert can_start_attempt(used_attempts=0, attempt_limit=2) is True
    assert can_start_attempt(used_attempts=2, attempt_limit=2) is False
    with pytest.raises(ConflictError):
        assert_can_start_attempt(used_attempts=2, attempt_limit=2)


def test_locked_attempt_cannot_be_changed():
    assert_attempt_mutable(AttemptStatus.IN_PROGRESS.value)
    with pytest.raises(AttemptLockedError):
        assert_attempt_mutable(AttemptStatus.SUBMITTED.value)
    with pytest.raises(AttemptLockedError):
        assert_attempt_mutable(AttemptStatus.COMPLETED.value)


def test_snapshot_immutable_after_start():
    with pytest.raises(AttemptLockedError):
        assert_snapshot_immutable(AttemptStatus.IN_PROGRESS.value)


def test_time_limit():
    started = datetime(2026, 1, 1, tzinfo=UTC)
    assert is_time_expired(started, 30, now=started + timedelta(minutes=29)) is False
    assert is_time_expired(started, 30, now=started + timedelta(minutes=31)) is True


def test_only_approved_exam_questions():
    assert (
        question_eligible_for_exam(
            purpose=QuestionPurpose.EXAM.value,
            status=QuestionStatus.APPROVED.value,
            generated_by_ai=False,
            approved=True,
        )
        is True
    )
    assert (
        question_eligible_for_exam(
            purpose=QuestionPurpose.TRAINING.value,
            status=QuestionStatus.APPROVED.value,
            generated_by_ai=False,
            approved=True,
        )
        is False
    )
    assert (
        question_eligible_for_exam(
            purpose=QuestionPurpose.EXAM.value,
            status=QuestionStatus.DRAFT.value,
            generated_by_ai=True,
            approved=False,
        )
        is False
    )


def test_deterministic_closed_score():
    assert score_closed_question(expected="B", given="b") == 1.0
    assert score_closed_question(expected="B", given="A") == 0.0


def test_human_confirmation_blocks_auto_pass():
    assert passed_by_policy(percent=90, passing_score=70, requires_human_confirmation=False, requires_review=False)
    assert not passed_by_policy(percent=90, passing_score=70, requires_human_confirmation=True, requires_review=False)
    assert not passed_by_policy(percent=90, passing_score=70, requires_human_confirmation=False, requires_review=True)


def test_correct_answers_hidden_from_employee():
    hidden = hide_correct_answers({"text": "Q", "correct_answer": "A", "rubric": []})
    assert "correct_answer" not in hidden
    with pytest.raises(ForbiddenError):
        assert_employee_cannot_see_key({"employee"}, reveal=True)


def test_training_task_always_requires_approval():
    from app.schemas.ai import TrainingTask

    with pytest.raises(ValidationError):
        TrainingTask(
            learning_objective="x",
            question_type="open",
            question="?",
            correct_answer="a",
            difficulty=1,
            requires_approval=False,
            source_references=[uuid4()],
        )
