"""RBAC: roles are assigned separately from the user. All access is organization-scoped."""

from enum import StrEnum

from app.core.exceptions import ForbiddenError


class RoleName(StrEnum):
    EMPLOYEE = "employee"
    MANAGER = "manager"
    METHODIST = "methodist"
    ADMIN = "admin"
    AUDITOR = "auditor"


class Permission(StrEnum):
    COURSE_VIEW_ASSIGNED = "course:view_assigned"
    COURSE_MANAGE = "course:manage"
    MODULE_MANAGE = "module:manage"
    MENTOR_ASK = "mentor:ask"
    PRACTICE_TAKE = "practice:take"
    EXAM_TAKE = "exam:take"
    EXAM_BANK_MANAGE = "exam:bank_manage"
    PROGRESS_VIEW_OWN = "progress:view_own"
    PROGRESS_VIEW_TEAM = "progress:view_team"
    PROGRESS_VIEW_ORG = "progress:view_org"
    ENROLLMENT_ASSIGN_TEAM = "enrollment:assign_team"
    ENROLLMENT_ASSIGN_ORG = "enrollment:assign_org"
    APPEAL_CREATE = "appeal:create"
    APPEAL_REVIEW = "appeal:review"
    KNOWLEDGE_UPLOAD = "knowledge:upload"
    KNOWLEDGE_APPROVE = "knowledge:approve"
    QUESTION_APPROVE = "question:approve"
    RUBRIC_MANAGE = "rubric:manage"
    ATTEMPT_REVIEW = "attempt:review"
    USER_MANAGE = "user:manage"
    DEPARTMENT_MANAGE = "department:manage"
    ORGANIZATION_MANAGE = "organization:manage"
    AI_SETTINGS = "ai:settings"
    AUDIT_READ = "audit:read"
    ANALYTICS_READ = "analytics:read"
    MATERIAL_VERSION_READ = "material:version_read"
    GRADE_OVERRIDE = "grade:override"


# Auditor is read-only. Admin is still bound to one organization.
ROLE_PERMISSIONS: dict[RoleName, frozenset[Permission]] = {
    RoleName.EMPLOYEE: frozenset(
        {
            Permission.COURSE_VIEW_ASSIGNED,
            Permission.MENTOR_ASK,
            Permission.PRACTICE_TAKE,
            Permission.EXAM_TAKE,
            Permission.PROGRESS_VIEW_OWN,
            Permission.APPEAL_CREATE,
        }
    ),
    RoleName.MANAGER: frozenset(
        {
            Permission.COURSE_VIEW_ASSIGNED,
            Permission.PROGRESS_VIEW_OWN,
            Permission.PROGRESS_VIEW_TEAM,
            Permission.ENROLLMENT_ASSIGN_TEAM,
            Permission.ATTEMPT_REVIEW,
            Permission.ANALYTICS_READ,
            Permission.APPEAL_CREATE,
        }
    ),
    RoleName.METHODIST: frozenset(
        {
            Permission.COURSE_MANAGE,
            Permission.MODULE_MANAGE,
            Permission.KNOWLEDGE_UPLOAD,
            Permission.KNOWLEDGE_APPROVE,
            Permission.QUESTION_APPROVE,
            Permission.RUBRIC_MANAGE,
            Permission.EXAM_BANK_MANAGE,
            Permission.APPEAL_REVIEW,
            Permission.ATTEMPT_REVIEW,
            Permission.GRADE_OVERRIDE,
            Permission.ANALYTICS_READ,
            Permission.MATERIAL_VERSION_READ,
            Permission.PROGRESS_VIEW_ORG,
            Permission.PROGRESS_VIEW_OWN,
        }
    ),
    RoleName.ADMIN: frozenset(
        {
            Permission.USER_MANAGE,
            Permission.DEPARTMENT_MANAGE,
            Permission.ORGANIZATION_MANAGE,
            Permission.AI_SETTINGS,
            Permission.AUDIT_READ,
            Permission.ANALYTICS_READ,
            Permission.PROGRESS_VIEW_ORG,
            Permission.PROGRESS_VIEW_OWN,
            Permission.ENROLLMENT_ASSIGN_ORG,
            Permission.MATERIAL_VERSION_READ,
        }
    ),
    RoleName.AUDITOR: frozenset(
        {
            Permission.AUDIT_READ,
            Permission.MATERIAL_VERSION_READ,
            Permission.ANALYTICS_READ,
            Permission.PROGRESS_VIEW_ORG,
        }
    ),
}

AUDITOR_WRITE_PERMISSIONS = frozenset(
    {
        Permission.COURSE_MANAGE,
        Permission.USER_MANAGE,
        Permission.GRADE_OVERRIDE,
        Permission.APPEAL_REVIEW,
        Permission.AI_SETTINGS,
        Permission.QUESTION_APPROVE,
        Permission.KNOWLEDGE_APPROVE,
        Permission.ENROLLMENT_ASSIGN_TEAM,
        Permission.ENROLLMENT_ASSIGN_ORG,
    }
)


def normalize_roles(roles: set[str] | set[RoleName] | list[str]) -> set[RoleName]:
    result: set[RoleName] = set()
    for role in roles:
        result.add(RoleName(str(role)))
    return result


def permissions_for(roles: set[str] | set[RoleName] | list[str]) -> frozenset[Permission]:
    collected: set[Permission] = set()
    for role in normalize_roles(roles):
        collected.update(ROLE_PERMISSIONS[role])
    return frozenset(collected)


def has_permission(roles: set[str] | set[RoleName] | list[str], permission: Permission) -> bool:
    return permission in permissions_for(roles)


def require_permission(roles: set[str] | set[RoleName] | list[str], permission: Permission) -> None:
    if not has_permission(roles, permission):
        raise ForbiddenError(f"Недостаточно прав: {permission.value}")


def assert_same_organization(actor_org_id, resource_org_id) -> None:
    if actor_org_id != resource_org_id:
        raise ForbiddenError("Нет доступа к данным другой организации")


def assert_not_privilege_escalation(
    actor_roles: set[str] | set[RoleName] | list[str],
    target_roles: set[str] | set[RoleName] | list[str],
) -> None:
    """Only admin may assign roles. Auditor and employee cannot grant admin/methodist."""
    actor = normalize_roles(actor_roles)
    target = normalize_roles(target_roles)
    if RoleName.ADMIN not in actor:
        raise ForbiddenError("Назначать роли может только администратор")
    if RoleName.AUDITOR in actor and target - {RoleName.AUDITOR}:
        raise ForbiddenError("Аудитор не может изменять роли")
