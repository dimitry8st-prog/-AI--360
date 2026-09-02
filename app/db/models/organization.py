from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import OrgStatus

if TYPE_CHECKING:
    from app.db.models.user import User


class Organization(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=OrgStatus.ACTIVE.value, nullable=False)

    departments: Mapped[list["Department"]] = relationship(back_populates="organization")
    users: Mapped[list["User"]] = relationship(back_populates="organization")


class Department(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_departments_org_name"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", use_alter=True), nullable=True)

    organization: Mapped[Organization] = relationship(back_populates="departments")
    manager: Mapped["User | None"] = relationship(foreign_keys=[manager_id])
    users: Mapped[list["User"]] = relationship(
        back_populates="department",
        foreign_keys="User.department_id",
    )
