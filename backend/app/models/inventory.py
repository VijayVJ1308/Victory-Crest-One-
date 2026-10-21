"""Victory Crest One - Supply Chain, ERP, Warehouse & Inventory Models
Multi-warehouse inventory, Purchase Orders, Goods Receipt Notes (GRN),
Stock Movements, Reorder Points, and Stocktaking Cycle Counts.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class Warehouse(Base, BaseModelMixin):
    """Storage facility, central commissary, or property stockroom."""
    __tablename__ = "inv_warehouses"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    warehouse_code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False, index=True)
    warehouse_type = Column(String(30), default="CENTRAL", nullable=False)  # CENTRAL, FNB_COMMISSARY, COLD_STORAGE, RETAIL_STORE
    location_address = Column(String(255), nullable=True)
    manager_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


class PurchaseOrder(Base, BaseModelMixin):
    """Procurement purchase order issued to vendors for stock replenishment."""
    __tablename__ = "inv_purchase_orders"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    po_number = Column(String(50), unique=True, nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(150), nullable=False, index=True)

    status = Column(String(30), default="DRAFT", nullable=False, index=True)  # DRAFT, ISSUED, PARTIALLY_RECEIVED, RECEIVED, CLOSED, CANCELLED
    issue_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    expected_delivery_date = Column(DateTime, nullable=True)
    payment_terms_days = Column(Integer, default=30, nullable=False)

    warehouse_id = Column(String(36), nullable=False, index=True)
    warehouse_name = Column(String(150), nullable=False)

    subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=18.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)

    # Cross-module link to AP Supplier Bill in Phase 4 Finance
    supplier_bill_id = Column(String(36), nullable=True, index=True)

    notes = Column(Text, nullable=True)


class PurchaseOrderLine(Base, BaseModelMixin):
    """Line item in a Purchase Order."""
    __tablename__ = "inv_po_lines"

    purchase_order_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=True, index=True)
    sku = Column(String(50), nullable=False)
    name = Column(String(150), nullable=False)
    unit_of_measure = Column(String(20), default="UNIT", nullable=False)

    quantity_ordered = Column(Numeric(10, 2), default=1.00, nullable=False)
    quantity_received = Column(Numeric(10, 2), default=0.00, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)


class GoodsReceiptNote(Base, BaseModelMixin):
    """Formal receiving voucher for goods delivered against a Purchase Order."""
    __tablename__ = "inv_grn_receipts"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    grn_number = Column(String(50), unique=True, nullable=False, index=True)
    purchase_order_id = Column(String(36), nullable=False, index=True)
    supplier_id = Column(String(36), nullable=False, index=True)
    supplier_name = Column(String(150), nullable=False)
    warehouse_id = Column(String(36), nullable=False, index=True)

    received_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_items_received = Column(Integer, default=0, nullable=False)

    # GL Journal posting reference (DR 1200 Inventory Asset, CR 2010 AP)
    journal_entry_id = Column(String(36), nullable=True, index=True)

    notes = Column(Text, nullable=True)


class WarehouseStock(Base, BaseModelMixin):
    """Current stock on hand and reorder threshold for an item at a specific warehouse."""
    __tablename__ = "inv_warehouse_stocks"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    warehouse_id = Column(String(36), nullable=False, index=True)
    warehouse_name = Column(String(150), nullable=False)

    product_id = Column(String(36), nullable=True, index=True)
    sku = Column(String(50), nullable=False, index=True)
    product_name = Column(String(150), nullable=False, index=True)
    category = Column(String(50), default="General", nullable=False, index=True)
    unit_of_measure = Column(String(20), default="UNIT", nullable=False)

    quantity_on_hand = Column(Numeric(12, 2), default=0.00, nullable=False)
    quantity_reserved = Column(Numeric(12, 2), default=0.00, nullable=False)
    quantity_available = Column(Numeric(12, 2), default=0.00, nullable=False)
    reorder_point = Column(Numeric(12, 2), default=10.00, nullable=False)

    unit_cost = Column(Numeric(12, 2), default=0.00, nullable=False)  # Weighted average cost
    total_value = Column(Numeric(12, 2), default=0.00, nullable=False)

    stock_status = Column(String(20), default="IN_STOCK", nullable=False, index=True)  # IN_STOCK, LOW_STOCK, OUT_OF_STOCK
    last_restocked_at = Column(DateTime, nullable=True)


class StockMovement(Base, BaseModelMixin):
    """Immutable audit trail of stock additions, transfers, issues, and adjustments."""
    __tablename__ = "inv_stock_movements"

    organization_id = Column(String(36), nullable=False, index=True)
    movement_number = Column(String(50), unique=True, nullable=False, index=True)
    movement_type = Column(String(30), nullable=False, index=True)  # RECEIPT, TRANSFER, CONSUMPTION, ADJUSTMENT, SCRAP

    product_id = Column(String(36), nullable=True, index=True)
    sku = Column(String(50), nullable=False)
    product_name = Column(String(150), nullable=False)

    source_warehouse_id = Column(String(36), nullable=True)
    target_warehouse_id = Column(String(36), nullable=True)

    quantity = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    total_value = Column(Numeric(12, 2), nullable=False)

    reference_doc = Column(String(100), nullable=True)  # e.g., "PO-2026-00401" or "TRANSFER-0012"
    notes = Column(Text, nullable=True)


class CycleCountSession(Base, BaseModelMixin):
    """Stocktaking cycle count session for physical audit and reconciliation."""
    __tablename__ = "inv_cycle_counts"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    warehouse_id = Column(String(36), nullable=False, index=True)
    warehouse_name = Column(String(150), nullable=False)

    session_code = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), default="OPEN", nullable=False, index=True)  # OPEN, IN_PROGRESS, RECONCILED, CANCELLED

    total_items_counted = Column(Integer, default=0, nullable=False)
    total_variance_value = Column(Numeric(12, 2), default=0.00, nullable=False)

    reconciled_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
