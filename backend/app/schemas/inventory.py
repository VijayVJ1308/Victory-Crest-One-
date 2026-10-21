"""Victory Crest One - Supply Chain, ERP & Warehouse Inventory Schemas
Pydantic DTOs for warehouses, stock levels, Purchase Orders, Goods Receipt Notes,
stock movements, replenishment alerts, and inventory valuation KPIs.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Warehouse Schemas
# -------------------------------------------------------------
class WarehouseBase(BaseModel):
    warehouse_code: str
    name: str
    warehouse_type: str = "CENTRAL"  # CENTRAL, FNB_COMMISSARY, COLD_STORAGE, RETAIL_STORE, MAINTENANCE
    location_address: Optional[str] = None
    manager_name: Optional[str] = None
    is_active: bool = True


class WarehouseCreate(WarehouseBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class WarehouseOut(WarehouseBase):
    id: str
    organization_id: str
    property_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Purchase Order Schemas
# -------------------------------------------------------------
class PurchaseOrderLineCreate(BaseModel):
    product_id: Optional[str] = None
    sku: str
    name: str
    unit_of_measure: str = "UNIT"
    quantity_ordered: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(ge=0)


class PurchaseOrderLineOut(BaseModel):
    id: str
    purchase_order_id: str
    product_id: Optional[str] = None
    sku: str
    name: str
    unit_of_measure: str
    quantity_ordered: Decimal
    quantity_received: Decimal
    unit_price: Decimal
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    supplier_name: Optional[str] = None
    warehouse_id: str
    expected_delivery_date: Optional[datetime] = None
    payment_terms_days: int = 30
    tax_rate_percent: Decimal = Field(default=Decimal("18.00"), ge=0)
    lines: List[PurchaseOrderLineCreate] = []
    notes: Optional[str] = None


class PurchaseOrderUpdate(BaseModel):
    status: Optional[str] = None
    expected_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None


class PurchaseOrderReceiveRequest(BaseModel):
    notes: Optional[str] = "Goods delivered and accepted at receiving bay"


class PurchaseOrderOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    status: str
    issue_date: datetime
    expected_delivery_date: Optional[datetime] = None
    payment_terms_days: int
    warehouse_id: str
    warehouse_name: str
    subtotal: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    supplier_bill_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    lines: List[PurchaseOrderLineOut] = []

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Goods Receipt Note (GRN) Schemas
# -------------------------------------------------------------
class GoodsReceiptNoteOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    grn_number: str
    purchase_order_id: str
    supplier_id: str
    supplier_name: str
    warehouse_id: str
    received_date: datetime
    total_items_received: int
    journal_entry_id: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Stock Levels & Replenishment Alert Schemas
# -------------------------------------------------------------
class WarehouseStockOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    warehouse_id: str
    warehouse_name: str
    product_id: Optional[str] = None
    sku: str
    product_name: str
    category: str
    unit_of_measure: str
    quantity_on_hand: Decimal
    quantity_reserved: Decimal
    quantity_available: Decimal
    reorder_point: Decimal
    unit_cost: Decimal
    total_value: Decimal
    stock_status: str
    last_restocked_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StockReplenishmentAlert(BaseModel):
    warehouse_id: str
    warehouse_name: str
    product_id: Optional[str] = None
    sku: str
    product_name: str
    category: str
    quantity_on_hand: Decimal
    reorder_point: Decimal
    shortage_quantity: Decimal
    suggested_order_quantity: Decimal
    recommended_supplier_name: Optional[str] = None


# -------------------------------------------------------------
# Stock Movements & Transfer Schemas
# -------------------------------------------------------------
class StockTransferRequest(BaseModel):
    sku: str
    source_warehouse_id: str
    target_warehouse_id: str
    quantity: Decimal = Field(gt=0)
    notes: Optional[str] = None


class StockMovementCreate(BaseModel):
    movement_type: str  # RECEIPT, TRANSFER, CONSUMPTION, ADJUSTMENT, SCRAP
    sku: str
    product_name: Optional[str] = None
    source_warehouse_id: Optional[str] = None
    target_warehouse_id: Optional[str] = None
    quantity: Decimal = Field(gt=0)
    unit_cost: Optional[Decimal] = None
    reference_doc: Optional[str] = None
    notes: Optional[str] = None


class StockMovementOut(BaseModel):
    id: str
    organization_id: str
    movement_number: str
    movement_type: str
    product_id: Optional[str] = None
    sku: str
    product_name: str
    source_warehouse_id: Optional[str] = None
    target_warehouse_id: Optional[str] = None
    quantity: Decimal
    unit_cost: Decimal
    total_value: Decimal
    reference_doc: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Cycle Count & Stocktaking Schemas
# -------------------------------------------------------------
class CycleCountCreate(BaseModel):
    warehouse_id: str
    notes: Optional[str] = None


class CycleCountItemVariance(BaseModel):
    sku: str
    product_name: str
    book_quantity: Decimal
    counted_quantity: Decimal
    unit_cost: Decimal
    variance_quantity: Decimal
    variance_value: Decimal
    is_discrepant: bool


class CycleCountReconcileRequest(BaseModel):
    counts: List[CycleCountItemVariance]
    notes: Optional[str] = None


class CycleCountOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    warehouse_id: str
    warehouse_name: str
    session_code: str
    status: str
    total_items_counted: int
    total_variance_value: Decimal
    reconciled_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Overall Inventory & ERP Telemetry KPIs
# -------------------------------------------------------------
class InventoryMetricsOut(BaseModel):
    total_warehouses_count: int
    total_active_skus: int
    total_stock_units: Decimal
    total_inventory_valuation: Decimal
    low_stock_items_count: int
    active_purchase_orders_count: int
    total_open_po_value: Decimal
    goods_receipts_completed_count: int
    stock_movements_today_count: int
