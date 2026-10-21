"""Victory Crest One - Manufacturing & Production Management Schemas
Pydantic DTOs for Work Centers, Bills of Materials (BOM), Production Orders,
Routing Steps, Material Consumption, Quality Control, and Manufacturing KPIs.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Work Center Schemas
# -------------------------------------------------------------
class WorkCenterBase(BaseModel):
    code: str
    name: str
    work_center_type: str = "ASSEMBLY"
    hourly_labor_rate: Decimal = Field(default=Decimal("450.00"), ge=0)
    hourly_machine_rate: Decimal = Field(default=Decimal("350.00"), ge=0)
    daily_capacity_hours: Decimal = Field(default=Decimal("8.00"), ge=0)
    status: str = "AVAILABLE"
    is_active: bool = True


class WorkCenterCreate(WorkCenterBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class WorkCenterUpdate(BaseModel):
    name: Optional[str] = None
    work_center_type: Optional[str] = None
    hourly_labor_rate: Optional[Decimal] = None
    hourly_machine_rate: Optional[Decimal] = None
    daily_capacity_hours: Optional[Decimal] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None


class WorkCenterOut(WorkCenterBase):
    id: str
    organization_id: str
    property_id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# BOM Component & Operation Line Schemas
# -------------------------------------------------------------
class BomComponentCreate(BaseModel):
    item_code: str
    item_name: str
    quantity: Decimal = Field(gt=0)
    uom: str = "Units"
    unit_cost: Decimal = Field(ge=0)
    scrap_percent: Decimal = Field(default=Decimal("0.00"), ge=0)


class BomComponentOut(BaseModel):
    id: str
    bom_id: str
    item_code: str
    item_name: str
    quantity: Decimal
    uom: str
    unit_cost: Decimal
    scrap_percent: Decimal
    total_cost: Decimal

    model_config = ConfigDict(from_attributes=True)


class BomOperationCreate(BaseModel):
    sequence: int = 10
    work_center_id: str
    work_center_name: str
    operation_name: str
    setup_time_hours: Decimal = Field(default=Decimal("0.00"), ge=0)
    run_time_per_unit_hours: Decimal = Field(default=Decimal("0.10"), ge=0)
    hourly_rate: Decimal = Field(default=Decimal("450.00"), ge=0)


class BomOperationOut(BaseModel):
    id: str
    bom_id: str
    sequence: int
    work_center_id: str
    work_center_name: str
    operation_name: str
    setup_time_hours: Decimal
    run_time_per_unit_hours: Decimal
    hourly_rate: Decimal
    cost: Decimal

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Bill of Materials (BOM) Master Schemas
# -------------------------------------------------------------
class BillOfMaterialsCreate(BaseModel):
    bom_code: str
    product_id: str
    product_name: str
    product_sku: str
    version: str = "v1.0"
    batch_quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    uom: str = "Units"
    notes: Optional[str] = None
    components: List[BomComponentCreate] = []
    operations: List[BomOperationCreate] = []
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class BillOfMaterialsUpdate(BaseModel):
    product_name: Optional[str] = None
    version: Optional[str] = None
    batch_quantity: Optional[Decimal] = None
    uom: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class BillOfMaterialsOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    bom_code: str
    product_id: str
    product_name: str
    product_sku: str
    version: str
    batch_quantity: Decimal
    uom: str
    total_material_cost: Decimal
    total_labor_cost: Decimal
    total_bom_cost: Decimal
    unit_cost: Decimal
    status: str
    notes: Optional[str] = None
    components: List[BomComponentOut] = []
    operations: List[BomOperationOut] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Quality Inspection & Material Usage Schemas
# -------------------------------------------------------------
class MaterialUsageCreate(BaseModel):
    item_code: str
    item_name: str
    planned_quantity: Decimal
    actual_quantity: Decimal
    uom: str = "Units"
    unit_cost: Decimal
    total_cost: Optional[Decimal] = None


class MaterialUsageOut(BaseModel):
    id: str
    production_order_id: str
    item_code: str
    item_name: str
    planned_quantity: Decimal
    actual_quantity: Decimal
    uom: str
    unit_cost: Decimal
    total_cost: Decimal

    model_config = ConfigDict(from_attributes=True)


class QualityInspectionCreate(BaseModel):
    parameter_name: str
    target_specification: str
    measured_value: str
    status: str = "PASSED"  # PENDING, PASSED, FAILED, CONDITIONAL
    inspector_name: str = "Chief QA Inspector"
    remarks: Optional[str] = None


class QualityInspectionOut(BaseModel):
    id: str
    production_order_id: str
    parameter_name: str
    target_specification: str
    measured_value: str
    status: str
    inspector_name: str
    inspected_at: Optional[datetime] = None
    remarks: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Production Order (MO) Schemas
# -------------------------------------------------------------
class ProductionOrderCreate(BaseModel):
    bom_id: str
    target_quantity: Decimal = Field(gt=0)
    planned_start_date: datetime
    planned_end_date: datetime
    priority: str = "NORMAL"
    work_center_id: Optional[str] = None
    supervisor_name: Optional[str] = "Plant Floor Supervisor"
    notes: Optional[str] = None
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class ProductionOrderStartRequest(BaseModel):
    actual_start_date: Optional[datetime] = None
    work_center_id: Optional[str] = None
    supervisor_name: Optional[str] = None


class ProductionOrderCompleteRequest(BaseModel):
    produced_quantity: Decimal = Field(gt=0)
    rejected_quantity: Decimal = Field(default=Decimal("0.00"), ge=0)
    actual_labor_hours: Decimal = Field(gt=0)
    labor_hourly_rate: Optional[Decimal] = None
    overhead_cost: Decimal = Field(default=Decimal("0.00"), ge=0)
    actual_materials: Optional[List[MaterialUsageCreate]] = None
    quality_status: str = "PASSED"
    notes: Optional[str] = None


class ProductionOrderOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    order_number: str
    bom_id: str
    bom_code: str
    product_id: str
    product_name: str
    target_quantity: Decimal
    produced_quantity: Decimal
    rejected_quantity: Decimal
    status: str
    priority: str
    work_center_id: Optional[str] = None
    work_center_name: Optional[str] = None
    supervisor_name: Optional[str] = None
    planned_start_date: datetime
    planned_end_date: datetime
    actual_start_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None
    material_cost: Decimal
    labor_cost: Decimal
    overhead_cost: Decimal
    total_actual_cost: Decimal
    unit_actual_cost: Decimal
    journal_entry_id: Optional[str] = None
    notes: Optional[str] = None
    materials: List[MaterialUsageOut] = []
    inspections: List[QualityInspectionOut] = []
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Manufacturing Executive Telemetry & KPI Schemas
# -------------------------------------------------------------
class ManufacturingMetricsOut(BaseModel):
    total_orders: int
    active_orders: int
    completed_orders: int
    total_produced_units: Decimal
    total_rejected_units: Decimal
    scrap_rate_percent: Decimal
    total_wip_valuation: Decimal
    active_work_centers: int
    total_work_centers: int
    average_unit_cost: Decimal
    capacity_utilization_percent: Decimal

    model_config = ConfigDict(from_attributes=True)
