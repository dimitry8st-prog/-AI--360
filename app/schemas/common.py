from uuid import UUID

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SessionUser(BaseModel):
    id: UUID
    organization_id: UUID
    department_id: UUID | None = None
    email: str
    full_name: str
    roles: list[str]


class HealthStatus(BaseModel):
    status: str
    service: str = "mentor360"


class ReadinessStatus(BaseModel):
    status: str
    database: str
    redis: str
    llm: str
