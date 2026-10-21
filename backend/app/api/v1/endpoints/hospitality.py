"""Victory Crest One - Hospitality & Resort PMS / Restaurant Dining REST Endpoints
Rooms Rack, Reservations, Guest Folios, Housekeeping, Dining Tables,
Kitchen Display System (KDS), and Automated GL Night Audits.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, Path, Body
from backend.app.schemas.hospitality import (
    RoomTypeOut, RoomCreate, RoomOut,
    ReservationCreate, ReservationCheckInRequest, ReservationOut,
    FolioLineCreate, GuestFolioOut,
    DiningTableOut, DiningOrderCreate, DiningOrderSettleRequest, DiningOrderOut,
    HospitalityMetricsOut
)
from backend.app.services.hospitality_service import hospitality_service

router = APIRouter(prefix="/hospitality")


# -------------------------------------------------------------
# Room Types & Rooms Rack
# -------------------------------------------------------------
@router.get("/room-types", response_model=List[RoomTypeOut])
def list_room_types(property_id: Optional[str] = Query(None)):
    """List available room types, base rates, and standard amenities."""
    return hospitality_service.get_room_types(property_id=property_id)


@router.get("/rooms", response_model=List[RoomOut])
def list_rooms(
    property_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="AVAILABLE_CLEAN, DIRTY, INSPECTED, OCCUPIED, MAINTENANCE")
):
    """Retrieve complete room rack inventory with housekeeping and occupancy status."""
    return hospitality_service.get_rooms(property_id=property_id, status_filter=status)


@router.post("/rooms", response_model=RoomOut)
def create_room(room_in: RoomCreate, property_id: Optional[str] = Query(None)):
    """Add a new room to the physical room rack."""
    return hospitality_service.create_room(room_in, property_id=property_id)


@router.put("/rooms/{room_id}/status", response_model=RoomOut)
def update_room_status(
    room_id: str = Path(...),
    status: str = Body(..., embed=True)
):
    """Update housekeeping status of a room (e.g. DIRTY -> AVAILABLE_CLEAN)."""
    return hospitality_service.update_room_status(room_id, status)


# -------------------------------------------------------------
# Reservations Engine
# -------------------------------------------------------------
@router.get("/reservations", response_model=List[ReservationOut])
def list_reservations(
    property_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="CONFIRMED, CHECKED_IN, CHECKED_OUT, CANCELLED"),
    search: Optional[str] = Query(None)
):
    """List guest reservations with room rate breakdowns and booking dates."""
    return hospitality_service.get_reservations(property_id=property_id, status_filter=status, search_query=search)


@router.post("/reservations", response_model=ReservationOut)
def create_reservation(res_in: ReservationCreate):
    """Create a guest reservation with automatic rate and meal plan computation."""
    return hospitality_service.create_reservation(res_in)


@router.post("/reservations/{res_id}/check-in", response_model=ReservationOut)
def check_in_guest(
    res_id: str = Path(...),
    checkin_in: ReservationCheckInRequest = Body(...)
):
    """Check in guest: assigns room, marks room OCCUPIED, and opens guest folio."""
    return hospitality_service.check_in_guest(res_id, checkin_in)


# -------------------------------------------------------------
# Guest Folios & Incidentals
# -------------------------------------------------------------
@router.get("/folios", response_model=List[GuestFolioOut])
def list_guest_folios(
    property_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="OPEN, SETTLED, TRANSFERRED")
):
    """List active and settled guest folios with itemized running incidentals."""
    return hospitality_service.get_guest_folios(property_id=property_id, status_filter=status)


@router.post("/folios/{folio_id}/charges", response_model=GuestFolioOut)
def add_folio_charge(
    folio_id: str = Path(...),
    charge_in: FolioLineCreate = Body(...)
):
    """Post an incidental charge (F&B, Spa, Laundry, Room Service) to an open folio."""
    return hospitality_service.add_folio_charge(folio_id, charge_in)


@router.post("/folios/{folio_id}/settle", response_model=GuestFolioOut)
def check_out_and_settle_folio(
    folio_id: str = Path(...),
    payment_method: str = Body("CREDIT_CARD", embed=True)
):
    """Settle guest folio balance, mark room DIRTY, and post balanced GL journal entry."""
    return hospitality_service.check_out_and_settle_folio(folio_id, payment_method=payment_method)


# -------------------------------------------------------------
# Restaurant Dining Tables & KDS Orders
# -------------------------------------------------------------
@router.get("/dining/tables", response_model=List[DiningTableOut])
def list_dining_tables(property_id: Optional[str] = Query(None)):
    """List restaurant dining floorplan tables, seating capacities, and active status."""
    return hospitality_service.get_dining_tables(property_id=property_id)


@router.get("/dining/orders", response_model=List[DiningOrderOut])
def list_dining_orders(
    property_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="PENDING, PREPARING, READY, SERVED")
):
    """List Kitchen Display System (KDS) order tickets and preparation status."""
    return hospitality_service.get_dining_orders(property_id=property_id, status_filter=status)


@router.post("/dining/orders", response_model=DiningOrderOut)
def create_dining_order(order_in: DiningOrderCreate):
    """Send a new dining order ticket to the Kitchen Display System (KDS)."""
    return hospitality_service.create_dining_order(order_in)


@router.post("/dining/orders/{order_id}/settle", response_model=DiningOrderOut)
def settle_dining_order(
    order_id: str = Path(...),
    settle_in: DiningOrderSettleRequest = Body(...)
):
    """Settle restaurant bill via Cash, Card, UPI, or transfer charge directly to Guest Room Folio."""
    return hospitality_service.settle_dining_order(order_id, settle_in)


# -------------------------------------------------------------
# Night Audit & Hospitality Metrics
# -------------------------------------------------------------
@router.post("/night-audit")
def run_night_audit(property_id: Optional[str] = Query(None)):
    """Run End-of-Day Night Audit: posts daily room charges to folios and posts GL room revenue."""
    return hospitality_service.run_night_audit(property_id=property_id)


@router.get("/metrics", response_model=HospitalityMetricsOut)
def get_hospitality_metrics(property_id: Optional[str] = Query(None)):
    """Retrieve live hospitality KPIs: Occupancy %, ADR, RevPAR, Folio Receivables, and F&B Revenue."""
    return hospitality_service.get_hospitality_metrics(property_id=property_id)
