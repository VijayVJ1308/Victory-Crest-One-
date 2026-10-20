"""Victory Crest One - RBAC & Permissions Unit Tests
Validates role privilege enforcement and separation of duties.
"""

from shared.enums import UserRole, PermissionAction, ModuleType
from backend.app.core.permissions import has_permission


def test_system_admin_full_permissions():
    role = UserRole.SYSTEM_ADMIN.value
    assert has_permission(role, PermissionAction.VIEW, ModuleType.FINANCE.value) is True
    assert has_permission(role, PermissionAction.CREATE, ModuleType.USERS.value if hasattr(ModuleType, "USERS") else "users") is True
    assert has_permission(role, PermissionAction.DELETE, ModuleType.HOTEL.value) is True


def test_accountant_separation_of_duties():
    role = UserRole.ACCOUNTANT.value
    # Accountant CAN create, edit, submit accounting journals
    assert has_permission(role, PermissionAction.CREATE, ModuleType.ACCOUNTING.value) is True
    assert has_permission(role, PermissionAction.EDIT, ModuleType.ACCOUNTING.value) is True
    assert has_permission(role, PermissionAction.SUBMIT, ModuleType.ACCOUNTING.value) is True
    
    # Accountant CANNOT approve their own journals (Separation of duties!)
    assert has_permission(role, PermissionAction.APPROVE, ModuleType.ACCOUNTING.value) is False
    assert has_permission(role, PermissionAction.APPROVE, ModuleType.FINANCE.value) is False


def test_finance_manager_approvals():
    role = UserRole.FINANCE_MANAGER.value
    # Finance Manager CAN approve journals and financial disbursements
    assert has_permission(role, PermissionAction.APPROVE, ModuleType.FINANCE.value) is True
    assert has_permission(role, PermissionAction.APPROVE, ModuleType.ACCOUNTING.value) is True


def test_read_only_user():
    role = UserRole.READ_ONLY.value
    assert has_permission(role, PermissionAction.VIEW, ModuleType.SALES.value) is True
    assert has_permission(role, PermissionAction.EXPORT, ModuleType.SALES.value) is True
    # CANNOT create, edit, or delete
    assert has_permission(role, PermissionAction.CREATE, ModuleType.SALES.value) is False
    assert has_permission(role, PermissionAction.EDIT, ModuleType.SALES.value) is False
    assert has_permission(role, PermissionAction.DELETE, ModuleType.SALES.value) is False


def test_pos_cashier_scoping():
    role = UserRole.POS_CASHIER.value
    assert has_permission(role, PermissionAction.CREATE, ModuleType.POS.value) is True
    # Cannot access General Accounting
    assert has_permission(role, PermissionAction.VIEW, ModuleType.ACCOUNTING.value) is False
    assert has_permission(role, PermissionAction.VIEW, ModuleType.FINANCE.value) is False
