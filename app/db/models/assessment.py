from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.db.models.course import Course
from app.db.models.enums import (
    AppealStatus,
    AttemptStatus,
    ExamStatus,
    GraderType,
    QuestionPurpose,
    QuestionStatus,
    QuestionType,
)

JSONType = JSON().with_variant(SQLITE_JSON(), "sqlite")


class Question(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "questions"

    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    module_id: Mapped[UUID | None] = mapped_column(ForeignKey("modules.id"), nullable=True, index=True)
    question_type: Mapped[str] = mapped_column(String(32), default=QuestionType.SINGLE_CHOICE.value, nullable=False)
    purpose: Mapped[str] = mapped_column(String(32), default=QuestionPurpose.TRAINING.value, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    options_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    source_references: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=QuestionStatus.DRAFT.value, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    generated_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    generated_by_ai: Mapped[bool] = mapped_column(default=False, nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    rubrics: Mapped[list["Rubric"]] = relationship(back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Question {self.id} type={self.question_type} purpose={self.purpose}>"


class Rubric(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "rubrics"

    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    criteria_json: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    question: Mapped[Question] = relationship(back_populates="rubrics")


class Exam(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "exams"

    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    attempt_limit: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    question_count: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=ExamStatus.DRAFT.value, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    require_human_confirmation: Mapped[bool] = mapped_column(default=False, nullable=False)

    course: Mapped[Course] = relationship(back_populates="exams")
    attempts: Mapped[list["ExamAttempt"]] = relationship(back_populates="exam")


class ExamAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "exam_attempts"

    exam_id: Mapped[UUID] = mapped_column(ForeignKey("exams.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default=AttemptStatus.IN_PROGRESS.value, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    requires_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    question_snapshot_json: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    rubric_snapshot_json: Mapped[list] = mapped_column(JSONType, default=list, nullable=False)
    exam_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    exam: Mapped[Exam] = relationship(back_populates="attempts")
    answers: Mapped[list["Answer"]] = relationship(back_populates="attempt", cascade="all, delete-orphan")
    appeals: Mapped[list["Appeal"]] = relationship(back_populates="attempt")


class Answer(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "answers"

    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("exam_attempts.id"), nullable=False, index=True)
    question_id: Mapped[UUID] = mapped_column(ForeignKey("questions.id"), nullable=False)
    answer_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    grader_type: Mapped[str] = mapped_column(String(32), default=GraderType.DETERMINISTIC.value, nullable=False)
    grader_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    attempt: Mapped[ExamAttempt] = relationship(back_populates="answers")


class Appeal(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "appeals"

    attempt_id: Mapped[UUID] = mapped_column(ForeignKey("exam_attempts.id"), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=AppealStatus.OPEN.value, nullable=False)
    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision: Mapped[str | None] = mapped_column(String(64), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    attempt: Mapped[ExamAttempt] = relationship(back_populates="appeals")
