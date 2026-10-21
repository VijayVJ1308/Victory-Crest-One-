"""Victory Crest One - Manufacturing & Production Models
Work Centers, Bills of Materials (BOM), Production Orders (MO),
Component Explosion, Routing Steps, and Quality Inspections.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, Integer
from backend.app.models.base import Base, BaseModelMixin


class WorkCenter(Base, BaseModelMixin):
    """Manufacturing work center, machine bay, or assembly cell."""
    __tablename__ = "mfg_work_centers"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    work_center_type = Column(String(50), default="ASSEMBLY", nullable=False)  # ASSEMBLY, MACHINING, BAKING, PACKAGING, LAB
    hourly_labor_rate = Column(Numeric(12, 2), default=450.00, nullable=False)
    hourly_machine_rate = Column(Numeric(12, 2), default=350.00, nullable=False)
    daily_capacity_hours = Column(Numeric(6, 2), default=8.00, nullable=False)
    status = Column(String(30), default="AVAILABLE", nullable=False, index=True)  # AVAILABLE, BUSY, MAINTENANCE, OFFLINE
    is_active = Column(Boolean, default=True, nullable=False)


class BillOfMaterials(Base, BaseModelMixin):
    """Bill of Materials (BOM) master header recipe for finished good or sub-assembly."""
    __tablename__ = "mfg_bills_of_materials"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    bom_code = Column(String(50), unique=True, nullable=False, index=True)
    product_id = Column(String(36), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)
    product_sku = Column(String(100), nullable=False)
    version = Column(String(20), default="v1.0", nullable=False)
    batch_quantity = Column(Numeric(12, 2), default=1.00, nullable=False)
    uom = Column(String(20), default="Units", nullable=False)

    total_material_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_labor_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_bom_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    unit_cost = Column(Numeric(12, 2), default=0.00, nullable=False)

    status = Column(String(30), default="ACTIVE", nullable=False, index=True)  # DRAFT, ACTIVE, ARCHIVED
    notes = Column(Text, nullable=True)


class BomComponent(Base, BaseModelMixin):
    """Component / Raw Material line item in a Bill of Materials."""
    __tablename__ = "mfg_bom_components"

    bom_id = Column(String(36), nullable=False, index=True)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Numeric(12, 4), nullable=False)
    uom = Column(String(20), default="Units", nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    scrap_percent = Column(Numeric(6, 2), default=0.00, nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)


class BomOperation(Base, BaseModelMixin):
    """Routing step / machine operation in a Bill of Materials."""
    __tablename__ = "mfg_bom_operations"

    bom_id = Column(String(36), nullable=False, index=True)
    sequence = Column(Integer, default=10, nullable=False)
    work_center_id = Column(String(36), nullable=False, index=True)
    work_center_name = Column(String(255), nullable=False)
    operation_name = Column(String(255), nullable=False)
    setup_time_hours = Column(Numeric(6, 2), default=0.00, nullable=False)
    run_time_per_unit_hours = Column(Numeric(6, 4), default=0.1000, nullable=False)
    hourly_rate = Column(Numeric(12, 2), default=450.00, nullable=False)
    cost = Column(Numeric(12, 2), default=0.00, nullable=False)


class ProductionOrder(Base, BaseModelMixin):
    """Manufacturing Work Order / Production Run."""
    __tablename__ = "mfg_production_orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    bom_id = Column(String(36), nullable=False, index=True)
    bom_code = Column(String(50), nullable=False)
    product_id = Column(String(36), nullable=False, index=True)
    product_name = Column(String(255), nullable=False)

    target_quantity = Column(Numeric(12, 2), nullable=False)
    produced_quantity = Column(Numeric(12, 2), default=0.00, nullable=False)
    rejected_quantity = Column(Numeric(12, 2), default=0.00, nullable=False)

    status = Column(String(30), default="PLANNED", nullable=False, index=True)  # DRAFT, PLANNED, IN_PROGRESS, QUALITY_CHECK, COMPLETED, CANCELLED
    priority = Column(String(20), default="NORMAL", nullable=False, index=True) # LOW, NORMAL, HIGH, URGENT

    work_center_id = Column(String(36), nullable=True, index=True)
    work_center_name = Column(String(255), nullable=True)
    supervisor_name = Column(String(255), nullable=True)

    planned_start_date = Column(DateTime, nullable=False)
    planned_end_date = Column(DateTime, nullable=False)
    actual_start_date = Column(DateTime, nullable=True)
    actual_end_date = Column(DateTime, nullable=True)

    material_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    labor_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    overhead_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_actual_cost = Column(Numeric(12, 2), default=0.00, nullable=False)
    unit_actual_cost = Column(Numeric(12, 2), default=0.00, nullable=False)

    journal_entry_id = Column(String(36), nullable=True, index=True)
    notes = Column(Text, nullable=True)


class ProductionMaterialUsage(Base, BaseModelMixin):
    """Actual raw materials consumed against a production work order."""
    __tablename__ = "mfg_material_usages"

    production_order_id = Column(String(36), nullable=False, index=True)
    item_code = Column(String(50), nullable=False)
    item_name = Column(String(255), nullable=False)
    planned_quantity = Column(Numeric(12, 4), nullable=False)
    actual_quantity = Column(Numeric(12, 4), nullable=False)
    uom = Column(String(20), default="Units", nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_cost = Column(Numeric(12, 2), nullable=False)


class QualityInspection(Base, BaseModelMixin):
    """In-process or finished goods quality assurance checkpoint."""
    __tablename__ = "mfg_quality_inspections"

    production_order_id = Column(String(36), nullable=False, index=True)
    parameter_name = Column(String(255), nullable=False)
    target_specification = Column(String(255), nullable=False)
    measured_value = Column(String(255), nullable=False)
    status = Column(String(20), default="PENDING", nullable=False, index=True)  # PENDING, PASSED, FAILED, CONDITIONAL
    inspector_name = Column(String(255), nullable=False)
    inspected_at = Column(DateTime, nullable=True)
    remarks = Column(Text, nullable=True)
