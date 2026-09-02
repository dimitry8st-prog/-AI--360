from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.db.models.audit import AuditEvent

logger = get_logger("audit")


async def record_audit(
    session: AsyncSession,
    *,
    organization_id: UUID,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    before: dict | None = None,
    after: dict | None = None,
    request_id: str | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=uuid4(),
        organization_id=organization_id,
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before,
        after_json=after,
        request_id=request_id,
        created_at=datetime.now(UTC),
    )
    session.add(event)
    logger.info(
        "audit_recorded",
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id else None,
    )
    return event
