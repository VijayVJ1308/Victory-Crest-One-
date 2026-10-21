"""Victory Crest One - Hospitality & Resort PMS / Restaurant Dining Models
Rooms Rack, Rate Plans, Guest Reservations, Housekeeping, Guest Folios,
Dining Tables, Kitchen Display System (KDS), and Automated Finance GL Billing.
"""

from datetime import datetime, date
from sqlalchemy import Column, String, Boolean, Integer, Numeric, Text, DateTime, Date
from backend.app.models.base import Base, BaseModelMixin


class RoomType(Base, BaseModelMixin):
    """Categorized accommodation tiers with capacity and standard rates."""
    __tablename__ = "hotel_room_types"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. DKG, EXS, PRV
    name = Column(String(100), nullable=False)                         # Deluxe King, Executive Suite, Heritage Villa
    base_occupancy = Column(Integer, default=2, nullable=False)
    max_occupancy = Column(Integer, default=4, nullable=False)
    base_rate_per_night = Column(Numeric(10, 2), default=4500.00, nullable=False)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)                            # WiFi, Minibar, Mountain View, Jacuzzi
    is_active = Column(Boolean, default=True, nullable=False)


class Room(Base, BaseModelMixin):
    """Physical hotel/resort room in the room rack with housekeeping status."""
    __tablename__ = "hotel_rooms"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    room_number = Column(String(20), nullable=False, index=True)
    room_type_id = Column(String(36), nullable=False, index=True)
    room_type_name = Column(String(100), nullable=False)
    floor = Column(String(20), default="Floor 1", nullable=False)
    building_wing = Column(String(100), default="Main Wing", nullable=False)
    status = Column(String(30), default="AVAILABLE_CLEAN", nullable=False, index=True)  # AVAILABLE_CLEAN, DIRTY, INSPECTED, OCCUPIED, MAINTENANCE
    key_card_code = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)


class Reservation(Base, BaseModelMixin):
    """Guest booking record, dates, room night billing, and check-in status."""
    __tablename__ = "hotel_reservations"

    confirmation_code = Column(String(50), unique=True, nullable=False, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    guest_name = Column(String(255), nullable=False, index=True)
    guest_email = Column(String(255), nullable=False)
    guest_phone = Column(String(50), nullable=False)

    check_in_date = Column(Date, nullable=False, index=True)
    check_out_date = Column(Date, nullable=False, index=True)
    nights = Column(Integer, default=1, nullable=False)

    room_type_id = Column(String(36), nullable=False, index=True)
    room_type_name = Column(String(100), nullable=False)
    room_id = Column(String(36), nullable=True, index=True)
    room_number = Column(String(20), nullable=True)

    meal_plan = Column(String(20), default="CP", nullable=False)          # EP, CP, MAP, AP
    status = Column(String(30), default="CONFIRMED", nullable=False, index=True)  # CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED, NO_SHOW

    room_rate_per_night = Column(Numeric(10, 2), default=4500.00, nullable=False)
    meal_plan_rate = Column(Numeric(10, 2), default=0.00, nullable=False)
    subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    grand_total = Column(Numeric(12, 2), default=0.00, nullable=False)
    advance_deposit_paid = Column(Numeric(12, 2), default=0.00, nullable=False)

    special_requests = Column(Text, nullable=True)


class GuestFolio(Base, BaseModelMixin):
    """Guest in-house running account with itemized incidentals and payments."""
    __tablename__ = "hotel_guest_folios"

    folio_number = Column(String(50), unique=True, nullable=False, index=True)
    reservation_id = Column(String(36), nullable=True, index=True)
    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    guest_name = Column(String(255), nullable=False, index=True)
    room_number = Column(String(20), nullable=False, index=True)

    status = Column(String(30), default="OPEN", nullable=False, index=True)  # OPEN, SETTLED, TRANSFERRED
    total_charges = Column(Numeric(12, 2), default=0.00, nullable=False)
    total_payments = Column(Numeric(12, 2), default=0.00, nullable=False)
    balance_due = Column(Numeric(12, 2), default=0.00, nullable=False)
    is_settled = Column(Boolean, default=False, nullable=False)

    journal_entry_id = Column(String(36), nullable=True)


class FolioLine(Base, BaseModelMixin):
    """Individual charge or payment entry posted to a guest folio."""
    __tablename__ = "hotel_folio_lines"

    folio_id = Column(String(36), nullable=False, index=True)
    line_type = Column(String(30), nullable=False)  # ROOM_CHARGE, FOOD_BEVERAGE, SPA, LAUNDRY, MISC, PAYMENT
    description = Column(String(255), nullable=False)
    amount = Column(Numeric(12, 2), default=0.00, nullable=False)
    reference = Column(String(100), nullable=True)
    posted_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DiningTable(Base, BaseModelMixin):
    """Restaurant dining table and section assignment."""
    __tablename__ = "dining_tables"

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    table_number = Column(String(20), nullable=False, index=True)
    area_section = Column(String(100), default="Main Dining Hall", nullable=False)
    seating_capacity = Column(Integer, default=4, nullable=False)
    status = Column(String(30), default="VACANT", nullable=False, index=True)  # VACANT, OCCUPIED, RESERVED, BILLING
    current_order_id = Column(String(36), nullable=True)


class DiningOrder(Base, BaseModelMixin):
    """Restaurant dining order, kitchen ticket, and billing settlement."""
    __tablename__ = "dining_orders"

    order_number = Column(String(50), unique=True, nullable=False, index=True)
    table_id = Column(String(36), nullable=True, index=True)
    table_number = Column(String(20), nullable=False)

    organization_id = Column(String(36), nullable=False, index=True)
    property_id = Column(String(36), nullable=False, index=True)

    server_name = Column(String(100), default="Staff Server", nullable=False)
    guest_count = Column(Integer, default=2, nullable=False)
    status = Column(String(30), default="PENDING", nullable=False, index=True)  # PENDING, PREPARING, READY, SERVED, CANCELLED

    subtotal = Column(Numeric(12, 2), default=0.00, nullable=False)
    service_charge = Column(Numeric(10, 2), default=0.00, nullable=False)
    tax_amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    grand_total = Column(Numeric(12, 2), default=0.00, nullable=False)

    is_paid = Column(Boolean, default=False, nullable=False)
    payment_method = Column(String(50), nullable=True)  # CASH, CARD, UPI, ROOM_FOLIO
    room_folio_id = Column(String(36), nullable=True)
    journal_entry_id = Column(String(36), nullable=True)


class DiningOrderItem(Base, BaseModelMixin):
    """Individual menu item line on a restaurant dining order."""
    __tablename__ = "dining_order_items"

    order_id = Column(String(36), nullable=False, index=True)
    item_name = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1, nullable=False)
    unit_price = Column(Numeric(10, 2), default=0.00, nullable=False)
    total_price = Column(Numeric(12, 2), default=0.00, nullable=False)
    special_notes = Column(String(255), nullable=True)
    status = Column(String(30), default="PENDING", nullable=False)  # PENDING, PREPARING, READY, SERVED
