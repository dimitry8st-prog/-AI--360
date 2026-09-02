"""Learning blocks and module completions.

Revision ID: 0002_learning
Revises: 0001_initial
Create Date: 2026-09-01
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_learning"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "learning_blocks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("block_type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("source_label", sa.String(length=255), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=True),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("alt_body", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_learning_blocks_module_id_modules"),
        sa.PrimaryKeyConstraint("id", name="pk_learning_blocks"),
        sa.UniqueConstraint("module_id", "position", name="uq_learning_blocks_module_position"),
    )
    op.create_index("ix_learning_blocks_module_id", "learning_blocks", ["module_id"])

    op.create_table(
        "module_completions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.Uuid(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("needs_repeat", sa.Boolean(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_module_completions_user_id_users"),
        sa.ForeignKeyConstraint(["module_id"], ["modules.id"], name="fk_module_completions_module_id_modules"),
        sa.PrimaryKeyConstraint("id", name="pk_module_completions"),
        sa.UniqueConstraint("user_id", "module_id", name="uq_module_completions_user_module"),
    )
    op.create_index("ix_module_completions_user_id", "module_completions", ["user_id"])
    op.create_index("ix_module_completions_module_id", "module_completions", ["module_id"])


def downgrade() -> None:
    op.drop_table("module_completions")
    op.drop_table("learning_blocks")
