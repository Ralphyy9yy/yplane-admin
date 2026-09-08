from datetime import datetime, date, time as dt_time
from decimal import Decimal
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models import Flight, Route, Airplane, Booking, BookingSeat, Seat
from app.services.booking_service import get_flight_seat_availability

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

from sqlalchemy.orm import joinedload
from app.core.cache import cache_get, cache_set

@router.get("/flights", response_class=HTMLResponse)
async def list_flights(request: Request, search: str = "", page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)

    cache_key = f"flights_list_{page}_{search}"
    cached = cache_get(cache_key)
    if cached is not None:
        return templates.TemplateResponse(request=request, name="flights/list.html", context={
            "request": request, "admin": admin,
            "flights": cached["flight_data"],
            "pagination": cached["paginated"],
            "search": search, "active_page": "flights"
        })

    query = (
        db.query(Flight)
        .options(joinedload(Flight.route), joinedload(Flight.airplane))
        .join(Flight.route)
        .join(Flight.airplane)
    )
    if search:
        query = query.filter((Flight.flight_number.ilike(f"%{search}%")) | (Airplane.model_number.ilike(f"%{search}%")))
    query = query.order_by(Flight.departure_time.desc())
    paginated = paginate_query(query, page=page, page_size=10)

    # Single aggregate query: count booked seats per flight in one round-trip
    flight_ids = [f.id for f in paginated["items"]]
    booked_map = {}
    if flight_ids:
        rows = (
            db.query(Booking.flight_id, func.count(BookingSeat.id))
            .join(BookingSeat, BookingSeat.booking_id == Booking.id)
            .filter(
                Booking.flight_id.in_(flight_ids),
                Booking.status.in_(["PENDING", "CONFIRMED"])
            )
            .group_by(Booking.flight_id)
            .all()
        )
        booked_map = {flight_id: cnt for flight_id, cnt in rows}

    flight_data = []
    for f in paginated["items"]:
        booked_count = booked_map.get(f.id, 0)
        total_seats = f.airplane.total_seats if f.airplane else 0
        avail = max(0, total_seats - booked_count)
        flight_data.append({
            "flight": f,
            "booked_count": booked_count,
            "total_seats": total_seats,
            "available_seats": avail
        })

    cache_set(cache_key, {"flight_data": flight_data, "paginated": paginated}, ttl=5)

    return templates.TemplateResponse(request=request, name="flights/list.html", context={
        "request": request, "admin": admin, "flights": flight_data, "pagination": paginated, "search": search, "active_page": "flights"
    })

@router.get("/flights/new", response_class=HTMLResponse)
async def new_flight_form(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    routes = db.query(Route).all()
    airplanes = db.query(Airplane).all()
    return templates.TemplateResponse(request=request, name="flights/form.html", context={
        "request": request, "admin": admin, "flight": None, "routes": routes, "airplanes": airplanes, "errors": {}, "active_page": "flights"
    })

@router.post("/flights/new", response_class=HTMLResponse)
async def create_flight(
    request: Request,
    flight_number: str = Form(...),
    route_id: int = Form(...),
    airplane_id: int = Form(...),
    departure_date: str = Form(...),
    departure_time: str = Form(...),
    arrival_time: str = Form(...),
    fare: float = Form(...),
    status: str = Form("SCHEDULED"),
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    fn = flight_number.strip().upper()
    dep_d = date.fromisoformat(departure_date)
    dep_t = dt_time.fromisoformat(departure_time)
    arr_t = dt_time.fromisoformat(arrival_time)
    
    # Combine date and time to timezone-aware datetime assuming local timezone for simplicity
    dep_dt = datetime.combine(dep_d, dep_t)
    # Estimate arrival dt based on time (if arr_t < dep_t, it's next day)
    arr_dt = datetime.combine(dep_d, arr_t)
    if arr_t < dep_t:
        arr_dt = datetime.combine(dep_d + timedelta(days=1), arr_t)
        
    # Default available seats based on airplane
    airplane = db.query(Airplane).filter(Airplane.id == airplane_id).first()
    avail_seats = airplane.total_seats if airplane else 0

    flight = Flight(
        flight_number=fn,
        route_id=route_id,
        airplane_id=airplane_id,
        departure_time=dep_dt,
        arrival_time=arr_dt,
        price=Decimal(str(fare)),
        available_seats=avail_seats,
        status=status
    )
    db.add(flight)
    db.commit()
    return RedirectResponse(url="/admin/flights", status_code=303)

@router.get("/flights/{flight_id}", response_class=HTMLResponse)
async def flight_detail(request: Request, flight_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    seat_map = get_flight_seat_availability(db, flight_id)
    booked_count = sum(1 for s in seat_map if not s["is_available"])
    available_count = len(seat_map) - booked_count
    return templates.TemplateResponse(request=request, name="flights/detail.html", context={
        "request": request,
        "admin": admin,
        "flight": flight,
        "seats": seat_map,
        "booked_count": booked_count,
        "available_count": available_count,
        "active_page": "flights"
    })

@router.post("/flights/{flight_id}/delete")
async def delete_flight(request: Request, flight_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if flight:
        db.delete(flight)
        db.commit()
    return RedirectResponse(url="/admin/flights", status_code=303)
