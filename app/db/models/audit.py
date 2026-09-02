from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin

JSONType = JSON().with_variant(SQLITE_JSON(), "sqlite")


class AuditEvent(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "audit_events"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    actor_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[UUID | None] = mapped_column(nullable=True, index=True)
    before_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    after_json: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
