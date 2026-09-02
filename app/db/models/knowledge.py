from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import AccessScope, DocumentStatus, SourceType

JSONType = JSON().with_variant(SQLITE_JSON(), "sqlite")


class KnowledgeDocument(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "knowledge_documents"

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), default=SourceType.UPLOAD.value, nullable=False)
    source_path: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=DocumentStatus.DRAFT.value, nullable=False)
    access_scope: Mapped[str] = mapped_column(String(32), default=AccessScope.ORGANIZATION.value, nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    approved_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="KnowledgeChunk.position",
    )


class KnowledgeChunk(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_chunks"

    document_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_documents.id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONType, default=dict, nullable=False)
    embedding_reference: Mapped[str | None] = mapped_column(String(255), nullable=True)

    document: Mapped[KnowledgeDocument] = relationship(back_populates="chunks")
