from uuid import uuid4

import pytest
from app.schemas.ai import GradingResult, MentorResponse, TrainingTask, mentor_escalation_fallback
from pydantic import ValidationError


def test_mentor_response_valid():
    payload = MentorResponse(
        answer="Кратко",
        explanation="Почему",
        citations=[],
        confidence=0.4,
        knowledge_gaps=[],
        next_action="continue",
        requires_human=False,
    )
    assert payload.confidence == 0.4


def test_mentor_confidence_bounds():
    with pytest.raises(ValidationError):
        MentorResponse(
            answer="a",
            explanation="b",
            confidence=1.5,
            next_action="continue",
        )


def test_escalation_fallback_text():
    result = mentor_escalation_fallback("Что такое SBI?")
    assert "недостаточно информации" in result.answer
    assert result.next_action == "escalate"
    assert result.requires_human is True
    assert result.confidence == 0.0


def test_training_task_json_roundtrip():
    task = TrainingTask.model_validate(
        {
            "learning_objective": "Дать обратную связь",
            "question_type": "single_choice",
            "question": "Что такое SBI?",
            "options": ["Модель обратной связи", "Метрика KPI"],
            "correct_answer": "Модель обратной связи",
            "rubric": [{"criterion": "Точность", "max_score": 1}],
            "difficulty": 2,
            "source_references": [str(uuid4())],
            "requires_approval": True,
        }
    )
    assert task.requires_approval is True


def test_grading_result_requires_max_score():
    with pytest.raises(ValidationError):
        GradingResult(
            score=1,
            max_score=0,
            passed=False,
            confidence=0.2,
        )
