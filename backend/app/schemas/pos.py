"""Victory Crest One - Point of Sale (POS) & Commerce Schemas
Pydantic DTOs for terminals, cash registers, orders, line items, tenders, receipts, and KPIs.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict



# -------------------------------------------------------------
# Terminal Schemas
# -------------------------------------------------------------
class PosTerminalBase(BaseModel):
    terminal_code: str
    name: str
    counter_location: Optional[str] = None
    status: str = "ACTIVE"
    is_active: bool = True


class PosTerminalCreate(PosTerminalBase):
    organization_id: Optional[str] = None
    property_id: Optional[str] = None


class PosTerminalOut(PosTerminalBase):
    id: str
    organization_id: str
    property_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Session Schemas
# -------------------------------------------------------------
class PosSessionOpenRequest(BaseModel):
    terminal_id: str
    opening_float: Decimal = Field(default=Decimal("5000.00"), ge=0)
    notes: Optional[str] = None


class PosSessionCloseRequest(BaseModel):
    counted_cash: Decimal = Field(ge=0)
    notes: Optional[str] = None


class PosSessionOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    terminal_id: str
    terminal_code: str
    cashier_id: str
    cashier_name: str
    status: str
    opened_at: datetime
    closed_at: Optional[datetime] = None
    opening_float: Decimal
    total_cash_sales: Decimal
    total_card_sales: Decimal
    total_upi_sales: Decimal
    total_room_charge_sales: Decimal
    total_sales: Decimal
    expected_cash: Decimal
    counted_cash: Decimal
    cash_variance: Decimal
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Order & Payment Line Schemas
# -------------------------------------------------------------
class PosOrderLineCreate(BaseModel):
    product_id: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    name: str
    category: str = "General"
    unit_of_measure: str = "UNIT"
    quantity: Decimal = Field(default=Decimal("1.00"), gt=0)
    unit_price: Decimal = Field(ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class PosOrderLineOut(BaseModel):
    id: str
    order_id: str
    product_id: Optional[str] = None
    sku: str
    barcode: Optional[str] = None
    name: str
    category: str
    unit_of_measure: str
    quantity: Decimal
    unit_price: Decimal
    discount_amount: Decimal
    total_amount: Decimal

    model_config = ConfigDict(from_attributes=True)


class PosPaymentCreate(BaseModel):
    tender_type: str  # CASH, CREDIT_CARD, UPI_QR, ROOM_CHARGE, GIFT_CARD
    amount: Decimal = Field(gt=0)
    reference_number: Optional[str] = None


class PosPaymentOut(BaseModel):
    id: str
    order_id: str
    tender_type: str
    amount: Decimal
    reference_number: Optional[str] = None
    auth_code: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Order Management Schemas
# -------------------------------------------------------------
class PosOrderCreate(BaseModel):
    session_id: Optional[str] = None
    customer_id: Optional[str] = None
    customer_name: Optional[str] = "Walk-in Guest"
    table_or_room: Optional[str] = None
    discount_percent: Decimal = Field(default=Decimal("0.00"), ge=0, le=100)
    tax_rate_percent: Decimal = Field(default=Decimal("12.00"), ge=0)
    lines: List[PosOrderLineCreate] = []
    notes: Optional[str] = None


class PosOrderHoldRequest(BaseModel):
    reason: Optional[str] = "Customer request / pending items"


class PosOrderTenderRequest(BaseModel):
    payments: List[PosPaymentCreate]
    notes: Optional[str] = None


class PosOrderOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    session_id: str
    order_number: str
    customer_id: Optional[str] = None
    customer_name: str
    table_or_room: Optional[str] = None
    cashier_id: str
    cashier_name: str
    status: str
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    change_returned: Decimal
    journal_entry_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    lines: List[PosOrderLineOut] = []
    payments: List[PosPaymentOut] = []

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Receipt & Telemetry Schemas
# -------------------------------------------------------------
class PosReceiptItem(BaseModel):
    sku: str
    name: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal


class PosReceiptOut(BaseModel):
    order_number: str
    receipt_title: str = "VICTORY CREST ONE"
    tagline: str = "One Platform. Every Business. Complete Control."
    organization_name: str
    property_name: str
    terminal_code: str
    cashier_name: str
    customer_name: str
    table_or_room: Optional[str] = None
    timestamp: datetime
    lines: List[PosReceiptItem]
    subtotal: Decimal
    discount_percent: Decimal
    discount_amount: Decimal
    taxable_amount: Decimal
    tax_rate_percent: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    paid_amount: Decimal
    change_returned: Decimal
    payments: List[PosPaymentOut]
    journal_entry_id: Optional[str] = None
    footer_message: str = "Thank you for your patronage. Please visit again!"


class PosMetricsOut(BaseModel):
    total_orders_count: int
    total_sales_amount: Decimal
    cash_sales_amount: Decimal
    card_sales_amount: Decimal
    upi_sales_amount: Decimal
    room_charge_sales_amount: Decimal
    average_ticket_size: Decimal
    open_sessions_count: int
    held_orders_count: int
