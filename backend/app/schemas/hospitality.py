"""Victory Crest One - Hospitality & Resort PMS / Restaurant Dining Schemas
Pydantic DTOs for Room Types, Room Rack, Reservations, Guest Folios,
Dining Tables, Kitchen Display System (KDS), and Hospitality Metrics.
"""

from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Room Types & Rooms Rack
# -------------------------------------------------------------
class RoomTypeOut(BaseModel):
    id: str
    code: str
    name: str
    base_occupancy: int
    max_occupancy: int
    base_rate_per_night: Decimal
    description: Optional[str] = None
    amenities: Optional[str] = None
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    room_number: str
    room_type_id: str
    floor: str = "Floor 1"
    building_wing: str = "Main Wing"
    notes: Optional[str] = None


class RoomOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    room_number: str
    room_type_id: str
    room_type_name: str
    floor: str
    building_wing: str
    status: str  # AVAILABLE_CLEAN, DIRTY, INSPECTED, OCCUPIED, MAINTENANCE
    key_card_code: Optional[str] = None
    notes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Reservations Engine
# -------------------------------------------------------------
class ReservationCreate(BaseModel):
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in_date: date
    check_out_date: date
    room_type_id: str
    meal_plan: str = "CP"  # EP, CP, MAP, AP
    advance_deposit_paid: Decimal = Field(default=Decimal("0.00"), ge=0)
    special_requests: Optional[str] = None
    property_id: Optional[str] = None


class ReservationCheckInRequest(BaseModel):
    room_id: str
    key_card_code: Optional[str] = None


class ReservationOut(BaseModel):
    id: str
    confirmation_code: str
    organization_id: str
    property_id: str
    guest_name: str
    guest_email: str
    guest_phone: str
    check_in_date: date
    check_out_date: date
    nights: int
    room_type_id: str
    room_type_name: str
    room_id: Optional[str] = None
    room_number: Optional[str] = None
    meal_plan: str
    status: str  # CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED, NO_SHOW
    room_rate_per_night: Decimal
    meal_plan_rate: Decimal
    subtotal: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    advance_deposit_paid: Decimal
    special_requests: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Guest Folios & Incidentals
# -------------------------------------------------------------
class FolioLineCreate(BaseModel):
    line_type: str = "FOOD_BEVERAGE"  # ROOM_CHARGE, FOOD_BEVERAGE, SPA, LAUNDRY, MISC, PAYMENT
    description: str
    amount: Decimal = Field(gt=0)
    reference: Optional[str] = None


class FolioLineOut(BaseModel):
    id: str
    folio_id: str
    line_type: str
    description: str
    amount: Decimal
    reference: Optional[str] = None
    posted_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuestFolioOut(BaseModel):
    id: str
    folio_number: str
    reservation_id: Optional[str] = None
    organization_id: str
    property_id: str
    guest_name: str
    room_number: str
    status: str  # OPEN, SETTLED, TRANSFERRED
    total_charges: Decimal
    total_payments: Decimal
    balance_due: Decimal
    is_settled: bool
    journal_entry_id: Optional[str] = None
    lines: List[FolioLineOut] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Restaurant Dining Tables & KDS Orders
# -------------------------------------------------------------
class DiningTableOut(BaseModel):
    id: str
    organization_id: str
    property_id: str
    table_number: str
    area_section: str
    seating_capacity: int
    status: str  # VACANT, OCCUPIED, RESERVED, BILLING
    current_order_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DiningOrderItemCreate(BaseModel):
    item_name: str
    quantity: int = Field(default=1, ge=1)
    unit_price: Decimal = Field(ge=0)
    special_notes: Optional[str] = None


class DiningOrderItemOut(BaseModel):
    id: str
    order_id: str
    item_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    special_notes: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class DiningOrderCreate(BaseModel):
    table_id: Optional[str] = None
    table_number: str
    server_name: str = "Staff Server"
    guest_count: int = Field(default=2, ge=1)
    items: List[DiningOrderItemCreate] = []
    property_id: Optional[str] = None


class DiningOrderSettleRequest(BaseModel):
    payment_method: str = "CARD"  # CASH, CARD, UPI, ROOM_FOLIO
    room_folio_id: Optional[str] = None


class DiningOrderOut(BaseModel):
    id: str
    order_number: str
    table_id: Optional[str] = None
    table_number: str
    organization_id: str
    property_id: str
    server_name: str
    guest_count: int
    status: str  # PENDING, PREPARING, READY, SERVED, CANCELLED
    subtotal: Decimal
    service_charge: Decimal
    tax_amount: Decimal
    grand_total: Decimal
    is_paid: bool
    payment_method: Optional[str] = None
    room_folio_id: Optional[str] = None
    journal_entry_id: Optional[str] = None
    items: List[DiningOrderItemOut] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------
# Hospitality Telemetry & Performance Metrics
# -------------------------------------------------------------
class HospitalityMetricsOut(BaseModel):
    total_rooms: int
    occupied_rooms: int
    clean_rooms: int
    dirty_rooms: int
    occupancy_rate: Decimal
    average_daily_rate: Decimal
    revpar: Decimal
    active_reservations: int
    open_folios_count: int
    total_folio_receivables: Decimal
    active_dining_tables: int
    kds_pending_tickets: int
    today_fnb_revenue: Decimal
