from uuid import uuid4

import pytest
from app.core.exceptions import ForbiddenError
from app.core.permissions import (
    Permission,
    RoleName,
    assert_not_privilege_escalation,
    assert_same_organization,
    has_permission,
    permissions_for,
    require_permission,
)


def test_employee_cannot_manage_users():
    assert not has_permission({RoleName.EMPLOYEE}, Permission.USER_MANAGE)
    assert has_permission({RoleName.EMPLOYEE}, Permission.EXAM_TAKE)


def test_auditor_is_read_only():
    perms = permissions_for({RoleName.AUDITOR})
    assert Permission.AUDIT_READ in perms
    assert Permission.GRADE_OVERRIDE not in perms
    assert Permission.USER_MANAGE not in perms
    assert Permission.APPEAL_REVIEW not in perms
    assert Permission.AI_SETTINGS not in perms


def test_methodist_manages_content_not_users():
    assert has_permission({RoleName.METHODIST}, Permission.QUESTION_APPROVE)
    assert has_permission({RoleName.METHODIST}, Permission.APPEAL_REVIEW)
    assert not has_permission({RoleName.METHODIST}, Permission.USER_MANAGE)


def test_admin_cannot_confirm_qualification_via_grade_override():
    assert has_permission({RoleName.ADMIN}, Permission.USER_MANAGE)
    assert not has_permission({RoleName.ADMIN}, Permission.GRADE_OVERRIDE)
    assert not has_permission({RoleName.ADMIN}, Permission.APPEAL_REVIEW)


def test_manager_assigns_team_not_org():
    assert has_permission({RoleName.MANAGER}, Permission.ENROLLMENT_ASSIGN_TEAM)
    assert not has_permission({RoleName.MANAGER}, Permission.ENROLLMENT_ASSIGN_ORG)


def test_require_permission_raises():
    with pytest.raises(ForbiddenError):
        require_permission({RoleName.EMPLOYEE}, Permission.AI_SETTINGS)


def test_org_isolation():
    org_a = uuid4()
    org_b = uuid4()
    assert_same_organization(org_a, org_a)
    with pytest.raises(ForbiddenError, match="другой организации"):
        assert_same_organization(org_a, org_b)


def test_privilege_escalation_blocked():
    with pytest.raises(ForbiddenError):
        assert_not_privilege_escalation({RoleName.EMPLOYEE}, {RoleName.ADMIN})
    with pytest.raises(ForbiddenError):
        assert_not_privilege_escalation({RoleName.AUDITOR}, {RoleName.ADMIN})
    assert_not_privilege_escalation({RoleName.ADMIN}, {RoleName.METHODIST})
