from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload, subqueryload
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.core.cache import cache_get, cache_set, cache_delete
from app.models import Booking, User, Flight, Payment, BookingSeat, Route
from app.services.booking_service import cancel_booking_request

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/bookings", response_class=HTMLResponse)
async def list_bookings(
    request: Request,
    search: str = "",
    status_filter: str = "",
    page: int = 1,
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)

    cache_key = f"bookings_list_{page}_{search}_{status_filter}"
    cached = cache_get(cache_key)
    if cached is not None:
        return templates.TemplateResponse("bookings/list.html", {
            "request": request, "admin": admin,
            "bookings": cached["bookings"],
            "pagination": cached["paginated"],
            "search": search, "status_filter": status_filter,
            "statuses": ["CONFIRMED", "PENDING", "CANCELLED", "REJECTED"],
            "active_page": "bookings"
        })

    query = (
        db.query(Booking)
        .options(
            joinedload(Booking.user),
            joinedload(Booking.flight).joinedload(Flight.route),
            subqueryload(Booking.booking_seats),
        )
        .join(Booking.user)
        .join(Booking.flight)
    )
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%")) |
            (Booking.booking_reference.ilike(f"%{search}%")) |
            (Flight.flight_number.ilike(f"%{search}%"))
        )
    if status_filter:
        query = query.filter(Booking.status == status_filter.upper())

    query = query.order_by(Booking.booked_at.desc())
    paginated = paginate_query(query, page=page, page_size=15)

    statuses = ["CONFIRMED", "PENDING", "CANCELLED", "REJECTED"]
    cache_set(cache_key, {"bookings": paginated["items"], "paginated": paginated}, ttl=5)
    return templates.TemplateResponse("bookings/list.html", {
        "request": request,
        "admin": admin,
        "bookings": paginated["items"],
        "pagination": paginated,
        "search": search,
        "status_filter": status_filter,
        "statuses": statuses,
        "active_page": "bookings"
    })

@router.get("/bookings/{booking_id}", response_class=HTMLResponse)
async def booking_detail(request: Request, booking_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return templates.TemplateResponse("bookings/detail.html", {
        "request": request,
        "admin": admin,
        "booking": booking,
        "active_page": "bookings"
    })

@router.post("/bookings/{booking_id}/cancel")
async def cancel_booking(request: Request, booking_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    res = cancel_booking_request(booking_id, admin_id=int(admin["sub"]))
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return RedirectResponse(url=f"/admin/bookings/{booking_id}", status_code=303)
