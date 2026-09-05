from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models import Payment, Booking, User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/payments", response_class=HTMLResponse)
async def list_payments(request: Request, search: str = "", page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    query = db.query(Payment).join(Payment.booking).join(Booking.user)
    if search:
        query = query.filter(
            (Payment.transaction_reference.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%")) |
            (Booking.booking_reference.ilike(f"%{search}%"))
        )
    query = query.order_by(Payment.id.desc())
    paginated = paginate_query(query, page=page, page_size=15)
    return templates.TemplateResponse("payments/list.html", {
        "request": request,
        "admin": admin,
        "payments": paginated["items"],
        "pagination": paginated,
        "search": search,
        "active_page": "payments"
    })
