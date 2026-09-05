from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models import Airport

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/airports", response_class=HTMLResponse)
async def list_airports(request: Request, search: str = "", page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    query = db.query(Airport)
    if search:
        query = query.filter((Airport.airport_code.ilike(f"%{search}%")) | (Airport.city.ilike(f"%{search}%")) | (Airport.airport_name.ilike(f"%{search}%")))
    query = query.order_by(Airport.airport_code)
    paginated = paginate_query(query, page=page, page_size=10)
    return templates.TemplateResponse("airports/list.html", {
        "request": request, "admin": admin, "airports": paginated["items"], "pagination": paginated, "search": search, "active_page": "airports"
    })

@router.get("/airports/new", response_class=HTMLResponse)
async def new_airport_form(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse("airports/form.html", {
        "request": request, "admin": admin, "airport": None, "errors": {}, "active_page": "airports"
    })

@router.post("/airports/new", response_class=HTMLResponse)
async def create_airport(
    request: Request,
    airport_code: str = Form(...),
    airport_name: str = Form(...),
    city: str = Form(...),
    country: str = Form("Philippines"),
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    code = airport_code.strip().upper()
    existing = db.query(Airport).filter(Airport.airport_code == code).first()
    if existing:
        return templates.TemplateResponse("airports/form.html", {
            "request": request, "admin": admin, "airport": None, "errors": {"airport_code": f"Airport code '{code}' already exists."}, "active_page": "airports"
        }, status_code=400)
    airport = Airport(airport_code=code, airport_name=airport_name.strip(), city=city.strip(), country=country.strip())
    db.add(airport)
    db.commit()
    return RedirectResponse(url="/admin/airports", status_code=303)

@router.get("/airports/{airport_id}/edit", response_class=HTMLResponse)
async def edit_airport_form(request: Request, airport_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    airport = db.query(Airport).filter(Airport.id == airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    return templates.TemplateResponse("airports/form.html", {
        "request": request, "admin": admin, "airport": airport, "errors": {}, "active_page": "airports"
    })

@router.post("/airports/{airport_id}/edit", response_class=HTMLResponse)
async def update_airport(
    request: Request,
    airport_id: int,
    airport_code: str = Form(...),
    airport_name: str = Form(...),
    city: str = Form(...),
    country: str = Form("Philippines"),
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    airport = db.query(Airport).filter(Airport.id == airport_id).first()
    if not airport:
        raise HTTPException(status_code=404, detail="Airport not found")
    airport.airport_code = airport_code.strip().upper()
    airport.airport_name = airport_name.strip()
    airport.city = city.strip()
    airport.country = country.strip()
    db.commit()
    return RedirectResponse(url="/admin/airports", status_code=303)

@router.post("/airports/{airport_id}/delete")
async def delete_airport(request: Request, airport_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    airport = db.query(Airport).filter(Airport.id == airport_id).first()
    if airport:
        db.delete(airport)
        db.commit()
    return RedirectResponse(url="/admin/airports", status_code=303)
