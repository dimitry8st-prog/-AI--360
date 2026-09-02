from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import BlockType, CourseStatus, EnrollmentStatus, SessionState

if TYPE_CHECKING:
    from app.db.models.assessment import Exam
    from app.db.models.user import User

JSONType = JSON().with_variant(SQLITE_JSON(), "sqlite")


class Course(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "courses"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=CourseStatus.DRAFT.value, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    owner_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    passing_score: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    require_human_confirmation: Mapped[bool] = mapped_column(default=False, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    modules: Mapped[list["Module"]] = relationship(
        back_populates="course",
        order_by="Module.position",
        cascade="all, delete-orphan",
    )
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="course")
    exams: Mapped[list["Exam"]] = relationship(back_populates="course")


class Module(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "modules"
    __table_args__ = (UniqueConstraint("course_id", "position", name="uq_modules_course_position"),)

    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    learning_objectives: Mapped[str] = mapped_column(Text, default="", nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    course: Mapped[Course] = relationship(back_populates="modules")
    blocks: Mapped[list["LearningBlock"]] = relationship(
        back_populates="module",
        order_by="LearningBlock.position",
        cascade="all, delete-orphan",
    )


class LearningBlock(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_blocks"
    __table_args__ = (UniqueConstraint("module_id", "position", name="uq_learning_blocks_module_position"),)

    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    block_type: Mapped[str] = mapped_column(String(32), default=BlockType.EXPLAIN.value, nullable=False)
    title: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    body: Mapped[str] = mapped_column(Text, default="", nullable=False)
    source_label: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    prompt: Mapped[str] = mapped_column(Text, default="", nullable=False)
    options_json: Mapped[list | None] = mapped_column(JSONType, nullable=True)
    expected_answer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    alt_body: Mapped[str] = mapped_column(Text, default="", nullable=False)

    module: Mapped[Module] = relationship(back_populates="blocks")

    def __repr__(self) -> str:
        return f"<LearningBlock {self.id} type={self.block_type}>"


class ModuleCompletion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "module_completions"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_module_completions_user_module"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    module_id: Mapped[UUID] = mapped_column(ForeignKey("modules.id"), nullable=False, index=True)
    error_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    needs_repeat: Mapped[bool] = mapped_column(default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Enrollment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    assigned_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=EnrollmentStatus.ASSIGNED.value, nullable=False)

    course: Mapped[Course] = relationship(back_populates="enrollments")
    user: Mapped["User"] = relationship(foreign_keys=[user_id])


class LearningSession(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "learning_sessions"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    course_id: Mapped[UUID] = mapped_column(ForeignKey("courses.id"), nullable=False, index=True)
    module_id: Mapped[UUID | None] = mapped_column(ForeignKey("modules.id"), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(32), default=SessionState.STARTED.value, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    current_step: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
