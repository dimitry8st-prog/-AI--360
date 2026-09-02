from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import ForbiddenError
from app.db.models.knowledge import KnowledgeDocument
from app.db.models.user import User, UserRole


def assert_org_scope(actor_org_id: UUID, resource_org_id: UUID) -> None:
    if actor_org_id != resource_org_id:
        raise ForbiddenError("Нет доступа к данным другой организации")


async def get_user_with_roles(session: AsyncSession, user_id: UUID) -> User | None:
    result = await session.execute(
        select(User).options(selectinload(User.user_roles).selectinload(UserRole.role)).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


def approved_documents_query(organization_id: UUID):
    return select(KnowledgeDocument).where(
        KnowledgeDocument.organization_id == organization_id,
        KnowledgeDocument.status == "approved",
    )
