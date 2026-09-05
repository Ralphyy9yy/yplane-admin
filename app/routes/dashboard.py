from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.core.cache import cache_get, cache_set
from app.models import Flight, Booking, Payment, BookingLog, Airplane, Route, User
from app.services import queue_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse("/auth/login", status_code=302)

    # --- Cached stats (10s TTL) ---
    stats = cache_get("dashboard_stats")
    if stats is None:
        total_airplanes   = db.query(func.count(Airplane.id)).filter(Airplane.status == "ACTIVE").scalar() or 0
        total_routes      = db.query(func.count(Route.id)).scalar() or 0
        total_flights     = db.query(func.count(Flight.id)).scalar() or 0
        confirmed_bookings= db.query(func.count(Booking.id)).filter(Booking.status == "CONFIRMED").scalar() or 0
        total_passengers  = db.query(func.count(User.id)).filter(User.role == "CUSTOMER").scalar() or 0
        total_revenue     = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "PAID").scalar() or 0
        stats = {
            "airplanes":  total_airplanes,
            "routes":     total_routes,
            "flights":    total_flights,
            "confirmed":  confirmed_bookings,
            "passengers": total_passengers,
            "revenue":    float(total_revenue),
        }
        cache_set("dashboard_stats", stats, ttl=10)

    stats["queue_depth"] = queue_service.get_queue_depth()

    # --- Cached recent bookings (5s TTL) ---
    recent_bookings = cache_get("dashboard_recent_bookings")
    if recent_bookings is None:
        recent_bookings = (
            db.query(Booking)
            .options(joinedload(Booking.user), joinedload(Booking.flight))
            .order_by(Booking.booked_at.desc())
            .limit(8)
            .all()
        )
        cache_set("dashboard_recent_bookings", recent_bookings, ttl=5)

    # --- Cached recent logs (3s TTL) ---
    recent_logs = cache_get("dashboard_recent_logs")
    if recent_logs is None:
        recent_logs = (
            db.query(BookingLog)
            .order_by(BookingLog.id.desc())
            .limit(6)
            .all()
        )
        cache_set("dashboard_recent_logs", recent_logs, ttl=3)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "admin": admin,
        "stats": stats,
        "recent_bookings": recent_bookings,
        "recent_logs": recent_logs,
        "active_page": "dashboard"
    })
