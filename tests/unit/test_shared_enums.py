"""Victory Crest One - Unit Tests for Shared Enums & Constants
"""

from shared.enums import ModuleType, UserRole, PermissionAction, PropertyType
from shared.constants import MODULE_CATALOG, DEMO_ORGANISATIONS, PRODUCT_NAME


def test_product_identity():
    assert PRODUCT_NAME == "Victory Crest One"


def test_module_catalog_completeness():
    assert len(MODULE_CATALOG) >= 15
    module_ids = [m["id"] for m in MODULE_CATALOG]
    assert "dashboard" in module_ids
    assert "sales" in module_ids
    assert "finance" in module_ids
    assert "hotel" in module_ids
    assert "restaurant" in module_ids
    assert "hr" in module_ids
    assert "erp" in module_ids
    assert "pos" in module_ids


def test_demo_organisations():
    assert len(DEMO_ORGANISATIONS) >= 1
    org = DEMO_ORGANISATIONS[0]
    assert org["code"] == "VCG"
    assert org["name"] == "Victory Crest Enterprise Group"
    assert len(org["properties"]) >= 3
    prop_names = [p["name"] for p in org["properties"]]
    assert any("Heritage Hotel" in name for name in prop_names)
    assert any("Mountain Resort" in name for name in prop_names)
    assert any("Business Hotel" in name for name in prop_names)


def test_user_roles():
    assert UserRole.SYSTEM_ADMIN.value == "System Administrator"
    assert UserRole.HOTEL_MANAGER.value == "Hotel Manager"
    assert UserRole.FINANCE_MANAGER.value == "Finance Manager"
