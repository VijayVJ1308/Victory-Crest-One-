"""Victory Crest One - Commerce & Point of Sale (POS) Database Models
Terminals, Register Sessions, Orders, Order Lines, and Multi-Tender Payments.
Tightly coupled with Master Data and General Ledger double-entry journals.
"""

from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime
from backend.app.models.base import Base, BaseModelMixin


class PosTerminal(Base, BaseModelMixin):
    """Point of Sale physical or virtual cashier terminal."""
    __tablename__ = "pos_terminals"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    terminal_code = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    counter_location = Column(String(100), nullable=True)  # e.g., "Lobby Cafe Counter 1"
    status = Column(String(20), default="ACTIVE", nullable=False)  # ACTIVE, INACTIVE, MAINTENANCE
    is_active = Column(Boolean, default=True, nullable=False)


class PosSession(Base, BaseModelMixin):
    """Cashier work shift and drawer reconciliation session."""
    __tablename__ = "pos_sessions"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    terminal_id = Column(String(36), nullable=False, index=True)
    terminal_code = Column(String(30), nullable=False)

    cashier_id = Column(String(36), nullable=False, index=True)
    cashier_name = Column(String(100), nullable=False)

    status = Column(String(20), default="OPEN", nullable=False, index=True)  # OPEN, CLOSED, SUSPENDED
    opened_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    opening_float = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_cash_sales = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_card_sales = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_upi_sales = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_room_charge_sales = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_sales = Column(Numeric(12, 2), default=0.00, nullable=False)

    expected_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    counted_cash = Column(Numeric(12, 2), default=0.00, nullable=False)
    cash_variance = Column(Numeric(12, 2), default=0.00, nullable=False)

    notes = Column(Text, nullable=True)


class PosOrder(Base, BaseModelMixin):
    """POS transaction order / retail receipt."""
    __tablename__ = "pos_orders"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(String(36), nullable=True, index=True)
    customer_name = Column(String(150), default="Walk-in Guest", nullable=False)
    table_or_room = Column(String(50), nullable=True)  # e.g., "Table 12" or "Room 402"

    cashier_id = Column(String(36), nullable=False, index=True)
    cashier_name = Column(String(100), nullable=False)

    status = Column(String(20), default="OPEN", nullable=False, index=True)  # OPEN, HELD, COMPLETED, VOIDED, REFUNDED

    subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    discount_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_rate_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    change_returned = Column(Numeric(12, 2), default=0.00, nullable=False)

    # GL Integration: Reference to posted double-entry journal entry
    journal_entry_id = Column(String(36), nullable=True, index=True)

    completed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


class PosOrderLine(Base, BaseModelMixin):
    """Individual line item purchased in a POS order."""
    __tablename__ = "pos_order_lines"

    order_id = Column(String(36), nullable=False, index=True)
    product_id = Column(String(36), nullable=True, index=True)
    sku = Column(String(50), nullable=False)
    barcode = Column(String(50), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    category = Column(String(50), default="General", nullable=False)
    unit_of_measure = Column(String(20), default="UNIT", nullable=False)

    quantity = Column(Numeric(10, 2), default=1.00, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_amount = Column(Numeric(12, 2), nullable=False)


class PosPayment(Base, BaseModelMixin):
    """Payment record linked to a POS transaction."""
    __tablename__ = "pos_payments"

    order_id = Column(String(36), nullable=False, index=True)
    tender_type = Column(String(30), nullable=False)  # CASH, CREDIT_CARD, UPI_QR, ROOM_CHARGE, GIFT_CARD
    amount = Column(Numeric(12, 2), nullable=False)
    reference_number = Column(String(100), nullable=True)  # Auth code, card last 4, UPI UTR
    auth_code = Column(String(50), nullable=True)
