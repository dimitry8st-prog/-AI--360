from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.permissions import RoleName
from app.db.base import Base, CreatedAtMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import UserStatus

if TYPE_CHECKING:
    from app.db.models.organization import Department, Organization


class Role(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(255), default="", nullable=False)

    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="role")


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("organization_id", "email", name="uq_users_org_email"),)

    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    department_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("departments.id", use_alter=True, name="fk_users_department_id_departments"),
        nullable=True,
        index=True,
    )
    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=UserStatus.ACTIVE.value, nullable=False)

    organization: Mapped["Organization"] = relationship(back_populates="users")
    department: Mapped["Department | None"] = relationship(
        back_populates="users",
        foreign_keys=[department_id],
    )
    user_roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def role_names(self) -> set[str]:
        return {item.role.name if item.role else "" for item in self.user_roles} - {""}

    def has_role(self, role: RoleName | str) -> bool:
        return str(role) in self.role_names


class UserRole(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "user_roles"
    __table_args__ = (
        UniqueConstraint("user_id", "role_id", "organization_id", name="uq_user_roles_user_role_org"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    role_id: Mapped[UUID] = mapped_column(ForeignKey("roles.id"), nullable=False, index=True)
    organization_id: Mapped[UUID] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="user_roles")
    role: Mapped[Role] = relationship(back_populates="user_roles")
