import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, subqueryload, joinedload
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.core.cache import cache_get, cache_set, cache_delete_prefix
from app.models import User, Flight, Booking, BookingSeat, BookingLog

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request, search: str = "", page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse("/auth/login", status_code=302)

    cache_key = f"users_list_{page}_{search}"
    cached = cache_get(cache_key)
    if cached is not None:
        return templates.TemplateResponse(request=request, name="users/list.html", context={
            "request": request, "admin": admin,
            "users": cached["users"], "pagination": cached["paginated"],
            "search": search, "active_page": "users"
        })

    query = (
        db.query(User)
        .options(subqueryload(User.bookings))
    )
    if search:
        query = query.filter((User.name.ilike(f"%{search}%")) | (User.email.ilike(f"%{search}%")))
    query = query.order_by(User.id.desc())
    paginated = paginate_query(query, page=page, page_size=15)
    cache_set(cache_key, {"users": paginated["items"], "paginated": paginated}, ttl=10)
    return templates.TemplateResponse(request=request, name="users/list.html", context={
        "request": request, "admin": admin, "users": paginated["items"], "pagination": paginated, "search": search, "active_page": "users"
    })

@router.get("/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: uuid.UUID, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse("/auth/login", status_code=302)

    user = (
        db.query(User)
        .options(
            joinedload(User.bookings)
            .joinedload(Booking.flight)
            .joinedload(Flight.route),
            joinedload(User.bookings)
            .joinedload(Booking.booking_seats)
            .joinedload(BookingSeat.seat),
            joinedload(User.bookings)
            .joinedload(Booking.payment)
        )
        .filter(User.id == user_id)
        .first()
    )
    if not user:
        raise HTTPException(404, "User not found")

    # Fetch recent booking queue logs for this user
    logs = (
        db.query(BookingLog)
        .filter(BookingLog.user_id == user_id)
        .order_by(BookingLog.id.desc())
        .limit(10)
        .all()
    )

    # Compute passenger overview metrics
    total_bookings = len(user.bookings)
    confirmed_bookings = sum(1 for b in user.bookings if b.status == "CONFIRMED")
    total_spent = sum(float(b.total_amount) for b in user.bookings if b.status == "CONFIRMED" and b.total_amount)
    queue_attempts = len(logs)

    stats = {
        "total_bookings": total_bookings,
        "confirmed_bookings": confirmed_bookings,
        "total_spent": total_spent,
        "queue_attempts": queue_attempts,
    }

    return templates.TemplateResponse(request=request, name="users/detail.html", context={
        "request": request,
        "admin": admin,
        "user": user,
        "logs": logs,
        "stats": stats,
        "active_page": "users"
    })

@router.post("/users/{user_id}/toggle")
async def toggle_user(request: Request, user_id: uuid.UUID, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse("/auth/login", status_code=302)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "User not found")
    if str(user.role).upper() == "ADMIN":
        raise HTTPException(400, "Administrator accounts cannot be disabled")

    try:
        user.is_active = not user.is_active
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"Database error updating user status: {str(e)}")

    cache_delete_prefix("users_list_")   # bust list cache so changes show immediately
    cache_delete_prefix("dashboard_")    # bust dashboard metrics

    referer = request.headers.get("referer")
    if referer and "/admin/users" in referer and not referer.rstrip("/").endswith(f"/{user_id}"):
        return RedirectResponse(referer, status_code=303)
    return RedirectResponse(f"/admin/users/{user_id}", status_code=303)

