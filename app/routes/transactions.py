from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models.transaction import Transaction
from app.models.booking import Booking
from app.models.user import User

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None


@router.get("/transactions", response_class=HTMLResponse)
async def list_transactions(
    request: Request,
    search: str = "",
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    query = db.query(Transaction).join(Booking).join(User, Booking.user_id == User.id)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (User.email.ilike(f"%{search}%"))
        )
    transactions = query.order_by(Transaction.created_at.desc()).limit(100).all()
    return templates.TemplateResponse(
        "transactions/list.html",
        {"request": request, "admin": admin, "transactions": transactions, "search": search, "active_page": "transactions"},
    )
