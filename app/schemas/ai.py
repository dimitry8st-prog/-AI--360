from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class Citation(BaseModel):
    document_id: UUID
    document_title: str
    chunk_id: UUID
    quote: str


class MentorResponse(BaseModel):
    answer: str
    explanation: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    knowledge_gaps: list[str] = Field(default_factory=list)
    next_action: Literal["continue", "repeat", "practice", "escalate"]
    requires_human: bool = False


class RubricCriterion(BaseModel):
    criterion: str
    max_score: int = Field(ge=0)


class TrainingTask(BaseModel):
    learning_objective: str
    question_type: Literal["single_choice", "multiple_choice", "open", "case"]
    question: str
    options: list[str] = Field(default_factory=list)
    correct_answer: str
    rubric: list[RubricCriterion] = Field(default_factory=list)
    difficulty: int = Field(ge=1, le=5)
    source_references: list[UUID] = Field(default_factory=list)
    requires_approval: bool = True

    @field_validator("requires_approval")
    @classmethod
    def generated_tasks_need_approval(cls, value: bool) -> bool:
        if value is not True:
            raise ValueError("Автоматически созданные задания нельзя включать в экзамен без одобрения")
        return value


class CriterionResult(BaseModel):
    criterion: str
    score: float = Field(ge=0)
    evidence_from_answer: str
    comment: str


class GradingResult(BaseModel):
    score: float = Field(ge=0)
    max_score: float = Field(gt=0)
    passed: bool
    criteria_results: list[CriterionResult] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    uncertainties: list[str] = Field(default_factory=list)
    requires_human_review: bool = False


NO_SOURCE_ANSWER = (
    "В утверждённой базе знаний недостаточно информации. Я передам вопрос методисту."
)


def mentor_escalation_fallback(question: str) -> MentorResponse:
    return MentorResponse(
        answer=NO_SOURCE_ANSWER,
        explanation=(
            "Я опираюсь только на утверждённые материалы организации. "
            "По этому вопросу надёжного источника нет, поэтому не дополняю ответ из общей памяти модели."
        ),
        citations=[],
        confidence=0.0,
        knowledge_gaps=[question],
        next_action="escalate",
        requires_human=True,
    )
