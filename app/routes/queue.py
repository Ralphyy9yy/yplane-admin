from datetime import datetime, date, time as dt_time, timedelta
from decimal import Decimal
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.core.cache import cache_get, cache_set, cache_delete
from app.models import (
    BookingLog, Flight, Seat, User, Route, Airplane, Booking, BookingSeat
)
from app.services import queue_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/queue", response_class=HTMLResponse)
@router.get("/booking-logs", response_class=HTMLResponse)
async def queue_monitor(request: Request, page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)

    cache_key_page = f"queue_logs_page_{page}"
    paginated = cache_get(cache_key_page)
    if paginated is None:
        query = db.query(BookingLog).order_by(BookingLog.id.desc())
        paginated = paginate_query(query, page=page, page_size=25)
        cache_set(cache_key_page, paginated, ttl=3)

    # Cached GROUP BY stats (3s TTL)
    status_counts = cache_get("queue_status_counts")
    if status_counts is None:
        status_counts = dict(
            db.query(BookingLog.status, func.count(BookingLog.id))
            .group_by(BookingLog.status)
            .all()
        )
        cache_set("queue_status_counts", status_counts, ttl=3)

    total_logs = sum(status_counts.values())
    success_count = status_counts.get("SUCCESS", 0)
    rejected_count = status_counts.get("REJECTED", 0)
    failed_count = status_counts.get("FAILED", 0)
    queue_depth = queue_service.get_queue_depth()

    return templates.TemplateResponse("queue/monitor.html", {
        "request": request,
        "admin": admin,
        "logs": paginated["items"],
        "pagination": paginated,
        "total_logs": total_logs,
        "success_count": success_count,
        "rejected_count": rejected_count,
        "failed_count": failed_count,
        "queue_depth": queue_depth,
        "active_page": "queue"
    })

@router.get("/queue/table", response_class=HTMLResponse)
@router.get("/booking-logs/table", response_class=HTMLResponse)
async def queue_table(request: Request, db: Session = Depends(get_db)):
    """HTMX partial endpoint polled every 300-500ms."""
    admin = require_admin(request)
    if not admin:
        return HTMLResponse("<tr><td colspan='7'>Unauthorized</td></tr>", status_code=401)

    logs = (
        db.query(BookingLog)
        .order_by(BookingLog.id.desc())
        .limit(50)
        .all()
    )
    return templates.TemplateResponse("queue/table_partial.html", {
        "request": request,
        "logs": logs
    })

@router.post("/queue/demo-5-for-1")
async def run_5_customers_1_seat_demo(request: Request, db: Session = Depends(get_db)):
    """
    Official Demo Requirement:
    5 customers simultaneously compete for 1 seat on a Panglao-origin flight.
    Expected outcome: Exactly 1 SUCCESS, 4 REJECTED in strict FIFO arrival order.
    """
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)

    # Find or prepare demo flight
    flight = db.query(Flight).filter(Flight.flight_number == "YP-DEMO").first()
    if not flight:
        flight = db.query(Flight).first()

    # Pick seat 1A on this aircraft
    seat = db.query(Seat).filter(Seat.airplane_id == flight.airplane_id, Seat.seat_number == "1A").first()
    if not seat:
        seat = db.query(Seat).filter(Seat.airplane_id == flight.airplane_id).first()

    # Cancel any existing bookings on this demo seat so it starts clean
    existing_bseats = (
        db.query(BookingSeat)
        .join(Booking, BookingSeat.booking_id == Booking.id)
        .filter(Booking.flight_id == flight.id, BookingSeat.seat_id == seat.id)
        .all()
    )
    for bs in existing_bseats:
        if bs.booking:
            bs.booking.status = "CANCELLED"
    db.commit()

    # Ensure 5 demo customer accounts exist
    customers = []
    for i in range(1, 6):
        c_email = f"customer{i}@yplane.com"
        c = db.query(User).filter(User.email == c_email).first()
        if not c:
            c = User(name=f"Passenger {i}", email=c_email, password="hashed", role="CUSTOMER")
            db.add(c)
            db.flush()
        customers.append(c)
    db.commit()

    # Fire all 5 requests simultaneously into the FIFO queue!
    for customer in customers:
        queue_service.enqueue_booking(customer.id, flight.id, seat.id, flight.fare)

    return RedirectResponse(url="/admin/queue", status_code=303)

@router.post("/queue/demo-2-for-1")
async def run_2_customers_1_seat_demo(request: Request, db: Session = Depends(get_db)):
    """Simpler 2-customers-1-seat warm-up demo."""
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)

    flight = db.query(Flight).filter(Flight.flight_number == "YP-DEMO").first() or db.query(Flight).first()
    seat = db.query(Seat).filter(Seat.airplane_id == flight.airplane_id, Seat.seat_number == "1B").first() or db.query(Seat).first()

    existing_bseats = (
        db.query(BookingSeat)
        .join(Booking, BookingSeat.booking_id == Booking.id)
        .filter(Booking.flight_id == flight.id, BookingSeat.seat_id == seat.id)
        .all()
    )
    for bs in existing_bseats:
        if bs.booking:
            bs.booking.status = "CANCELLED"
    db.commit()

    c1 = db.query(User).filter(User.email == "customer1@yplane.com").first()
    c2 = db.query(User).filter(User.email == "customer2@yplane.com").first()

    queue_service.enqueue_booking(c1.id, flight.id, seat.id, flight.fare)
    queue_service.enqueue_booking(c2.id, flight.id, seat.id, flight.fare)

    return RedirectResponse(url="/admin/queue", status_code=303)
