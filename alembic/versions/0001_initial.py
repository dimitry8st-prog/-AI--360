"""Initial schema and system roles.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.role_ids import SYSTEM_ROLES

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_organizations"),
    )

    op.create_table(
        "roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_roles"),
        sa.UniqueConstraint("name", name="uq_roles_name"),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("department_id", sa.Uuid(), nullable=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_users_organization_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("organization_id", "email", name="uq_users_org_email"),
        sa.UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_index("ix_users_department_id", "users", ["department_id"])
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"])

    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("manager_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_departments_organization_id_organizations"),
        sa.ForeignKeyConstraint(["manager_id"], ["users.id"], name="fk_departments_manager_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("organization_id", "name", name="uq_departments_org_name"),
    )
    op.create_index("ix_departments_organization_id", "departments", ["organization_id"])

    op.create_foreign_key(
        "fk_users_department_id_departments",
        "users",
        "departments",
        ["department_id"],
        ["id"],
    )

    op.create_table(
        "user_roles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role_id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users"),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], name="fk_user_roles_role_id_roles"),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_user_roles_organization_id_organizations"),
        sa.PrimaryKeyConstraint("id", name="pk_user_roles"),
        sa.UniqueConstraint("user_id", "role_id", "organization_id", name="uq_user_roles_user_role_org"),
    )
    op.create_index("ix_user_roles_user_id", "user_roles", ["user_id"])
    op.create_index("ix_user_roles_role_id", "user_roles", ["role_id"])
    op.create_index("ix_user_roles_organization_id", "user_roles", ["organization_id"])

    op.create_table(
        "courses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("passing_score", sa.Integer(), nullable=False),
        sa.Column("require_human_confirmation", sa.Boolean(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_courses_organization_id_organizations"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], name="fk_courses_owner_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_courses"),
    )
    op.create_index("ix_courses_organization_id", "courses", ["organization_id"])

    op.create_table(
        "modules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("learning_objectives", sa.Text(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], name="fk_modules_course_id_courses"),
        sa.PrimaryKeyConstraint("id", name="pk_modules"),
        sa.UniqueConstraint("course_id", "position", name="uq_modules_course_position"),
    )
    op.create_index("ix_modules_course_id", "modules", ["course_id"])

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_path", sa.String(length=1024), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("access_scope", sa.String(length=32), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_knowledge_documents_organization_id_organizations"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_knowledge_documents_approved_by_users"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_documents"),
    )
    op.create_index("ix_knowledge_documents_organization_id", "knowledge_documents", ["organization_id"])

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column("embedding_reference", sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], name="fk_knowledge_chunks_document_id_knowledge_documents"),
        sa.PrimaryKeyConstraint("id", name="pk_knowledge_chunks"),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by", sa.Uuid(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_enrollments_user_id_users"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], name="fk_enrollments_course_id_courses"),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], name="fk_enrollments_assigned_by_users"),
        sa.PrimaryKeyConstraint("id", name="pk_enrollments"),
        sa.UniqueConstraint("user_id", "course_id", name="uq_enrollments_user_course"),
    )
    op.create_index("ix_enrollments_user_id", "enrollments", ["user_id"])
    op.create_index("ix_enrollments_course_id", "enrollments", ["course_id"])

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=True),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_learning_sessions_user_id_users"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], name="fk_learning_sessions_course_id_courses"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_learning_sessions_module_id_modules"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_sessions"),
    )
    op.create_index("ix_learning_sessions_user_id", "learning_sessions", ["user_id"])
    op.create_index("ix_learning_sessions_course_id", "learning_sessions", ["course_id"])
    op.create_index("ix_learning_sessions_module_id", "learning_sessions", ["module_id"])

    op.create_table(
        "questions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=True),
        sa.Column("question_type", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("difficulty", sa.Integer(), nullable=False),
        sa.Column("source_references", sa.JSON(), nullable=False),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generated_by", sa.Uuid(), nullable=True),
        sa.Column("generated_by_ai", sa.Boolean(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], name="fk_questions_course_id_courses"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_questions_module_id_modules"),
        sa.ForeignKeyConstraint(["generated_by"], ["users.id"], name="fk_questions_generated_by_users"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_questions_approved_by_users"),
        sa.PrimaryKeyConstraint("id", name="pk_questions"),
    )
    op.create_index("ix_questions_course_id", "questions", ["course_id"])
    op.create_index("ix_questions_module_id", "questions", ["module_id"])

    op.create_table(
        "rubrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("criteria_json", sa.JSON(), nullable=False),
        sa.Column("max_score", sa.Integer(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_rubrics_question_id_questions"),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"], name="fk_rubrics_approved_by_users"),
        sa.PrimaryKeyConstraint("id", name="pk_rubrics"),
    )
    op.create_index("ix_rubrics_question_id", "rubrics", ["question_id"])

    op.create_table(
        "exams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("course_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("attempt_limit", sa.Integer(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("passing_score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("require_human_confirmation", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], name="fk_exams_course_id_courses"),
        sa.PrimaryKeyConstraint("id", name="pk_exams"),
    )
    op.create_index("ix_exams_course_id", "exams", ["course_id"])

    op.create_table(
        "exam_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("exam_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("score", sa.Numeric(6, 2), nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("requires_review", sa.Boolean(), nullable=False),
        sa.Column("question_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("rubric_snapshot_json", sa.JSON(), nullable=False),
        sa.Column("exam_version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.id"], name="fk_exam_attempts_exam_id_exams"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_exam_attempts_user_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_exam_attempts"),
    )
    op.create_index("ix_exam_attempts_exam_id", "exam_attempts", ["exam_id"])
    op.create_index("ix_exam_attempts_user_id", "exam_attempts", ["user_id"])

    op.create_table(
        "answers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("question_id", sa.Uuid(), nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("score", sa.Numeric(6, 2), nullable=True),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("evidence_json", sa.JSON(), nullable=True),
        sa.Column("grader_type", sa.String(length=32), nullable=False),
        sa.Column("grader_version", sa.String(length=64), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempts.id"], name="fk_answers_attempt_id_exam_attempts"),
        sa.ForeignKeyConstraint(["question_id"], ["questions.id"], name="fk_answers_question_id_questions"),
        sa.PrimaryKeyConstraint("id", name="pk_answers"),
    )
    op.create_index("ix_answers_attempt_id", "answers", ["attempt_id"])

    op.create_table(
        "appeals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("attempt_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("reviewer_id", sa.Uuid(), nullable=True),
        sa.Column("decision", sa.String(length=64), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["attempt_id"], ["exam_attempts.id"], name="fk_appeals_attempt_id_exam_attempts"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_appeals_user_id_users"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.id"], name="fk_appeals_reviewer_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_appeals"),
    )
    op.create_index("ix_appeals_attempt_id", "appeals", ["attempt_id"])
    op.create_index("ix_appeals_user_id", "appeals", ["user_id"])

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=True),
        sa.Column("before_json", sa.JSON(), nullable=True),
        sa.Column("after_json", sa.JSON(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], name="fk_audit_events_organization_id_organizations"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], name="fk_audit_events_actor_id_users"),
        sa.PrimaryKeyConstraint("id", name="pk_audit_events"),
    )
    op.create_index("ix_audit_events_organization_id", "audit_events", ["organization_id"])
    op.create_index("ix_audit_events_actor_id", "audit_events", ["actor_id"])
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_entity_type", "audit_events", ["entity_type"])
    op.create_index("ix_audit_events_entity_id", "audit_events", ["entity_id"])
    op.create_index("ix_audit_events_request_id", "audit_events", ["request_id"])

    roles_table = sa.table(
        "roles",
        sa.column("id", sa.Uuid()),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
    )
    op.bulk_insert(
        roles_table,
        [{"id": role_id, "name": name, "description": description} for role_id, name, description in SYSTEM_ROLES],
    )


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("appeals")
    op.drop_table("answers")
    op.drop_table("exam_attempts")
    op.drop_table("exams")
    op.drop_table("rubrics")
    op.drop_table("questions")
    op.drop_table("learning_sessions")
    op.drop_table("enrollments")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
    op.drop_table("modules")
    op.drop_table("courses")
    op.drop_table("user_roles")
    op.drop_constraint("fk_users_department_id_departments", "users", type_="foreignkey")
    op.drop_table("departments")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("organizations")
