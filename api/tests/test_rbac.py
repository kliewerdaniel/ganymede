# Ganymede API — RBAC Tests

import os
import sys
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.rbac import Role, has_permission, ROLE_PERMISSIONS, ROLE_HIERARCHY


class TestRoles:
    def test_role_enum_values(self):
        assert Role.ADMINISTRATOR.value == "administrator"
        assert Role.ATTORNEY.value == "attorney"
        assert Role.REVIEWER.value == "reviewer"
        assert Role.PARALEGAL.value == "paralegal"
        assert Role.IT_OPERATOR.value == "it_operator"

    def test_all_roles_in_permissions(self):
        for role in Role:
            assert role in ROLE_PERMISSIONS, f"Role {role} missing from ROLE_PERMISSIONS"
            assert role in ROLE_HIERARCHY, f"Role {role} missing from ROLE_HIERARCHY"


class TestPermissions:
    def test_admin_has_all_permissions(self):
        perms = ROLE_PERMISSIONS[Role.ADMINISTRATOR]
        assert "matter.create" in perms
        assert "matter.delete" in perms
        assert "user.create" in perms
        assert "audit.read" in perms

    def test_attorney_cannot_manage_users(self):
        perms = ROLE_PERMISSIONS[Role.ATTORNEY]
        assert "user.create" not in perms
        assert "user.delete" not in perms
        assert "audit.read" not in perms

    def test_attorney_can_query_and_export(self):
        perms = ROLE_PERMISSIONS[Role.ATTORNEY]
        assert "query.submit" in perms
        assert "artifact.export" in perms
        assert "document.upload" in perms

    def test_reviewer_cannot_upload(self):
        perms = ROLE_PERMISSIONS[Role.REVIEWER]
        assert "document.upload" not in perms
        assert "document.read" in perms

    def test_paralegal_cannot_export(self):
        perms = ROLE_PERMISSIONS[Role.PARALEGAL]
        assert "artifact.export" not in perms
        assert "query.submit" in perms

    def test_it_operator_limited_permissions(self):
        perms = ROLE_PERMISSIONS[Role.IT_OPERATOR]
        assert "audit.read" in perms
        assert "query.submit" not in perms
        assert "artifact.export" not in perms


class TestHasPermission:
    def test_valid_role_permission(self):
        assert has_permission("attorney", "query.submit") is True

    def test_valid_role_no_permission(self):
        assert has_permission("attorney", "audit.read") is False

    def test_invalid_role(self):
        assert has_permission("superadmin", "query.submit") is False

    def test_invalid_permission(self):
        assert has_permission("administrator", "fake.permission") is False

    def test_case_sensitive(self):
        assert has_permission("ATTORNEY", "query.submit") is False


class TestRoleHierarchy:
    def test_admin_highest(self):
        assert ROLE_HIERARCHY[Role.ADMINISTRATOR] == 100

    def test_it_operator_lowest(self):
        assert ROLE_HIERARCHY[Role.IT_OPERATOR] == 20

    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY[Role.ADMINISTRATOR] > ROLE_HIERARCHY[Role.ATTORNEY]
        assert ROLE_HIERARCHY[Role.ATTORNEY] > ROLE_HIERARCHY[Role.REVIEWER]
        assert ROLE_HIERARCHY[Role.REVIEWER] > ROLE_HIERARCHY[Role.PARALEGAL]
        assert ROLE_HIERARCHY[Role.PARALEGAL] > ROLE_HIERARCHY[Role.IT_OPERATOR]
