from datetime import time as dt_time
from decimal import Decimal
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models import Route, Airport

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

from app.core.pagination import paginate_query

@router.get("/routes", response_class=HTMLResponse)
async def list_routes(request: Request, page: int = 1, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    query = db.query(Route).order_by(Route.id.asc())
    paginated = paginate_query(query, page=page, page_size=10)
    return templates.TemplateResponse(request=request, name="routes/list.html", context={
        "request": request, "admin": admin, "routes": paginated["items"], "pagination": paginated, "active_page": "routes"
    })

@router.get("/routes/new", response_class=HTMLResponse)
async def new_route_form(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    airports = db.query(Airport).order_by(Airport.code).all()
    return templates.TemplateResponse(request=request, name="routes/form.html", context={
        "request": request, "admin": admin, "route": None, "airports": airports, "errors": {}, "active_page": "routes"
    })

@router.post("/routes/new", response_class=HTMLResponse)
async def create_route(
    request: Request,
    origin_airport_id: int = Form(...),
    destination_airport_id: int = Form(...),
    distance: float = Form(...),
    duration_hours: int = Form(1),
    duration_minutes: int = Form(30),
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    if origin_airport_id == destination_airport_id:
        airports = db.query(Airport).order_by(Airport.code).all()
        return templates.TemplateResponse(request=request, name="routes/form.html", context={
            "request": request, "admin": admin, "route": None, "airports": airports, "errors": {"origin_airport_id": "Origin and destination cannot be the same."}, "active_page": "routes"
        }, status_code=400)
    dur_mins = duration_hours * 60 + duration_minutes
    r = Route(
        origin_airport_id=origin_airport_id,
        destination_airport_id=destination_airport_id,
        distance_km=Decimal(str(distance)),
        estimated_duration_minutes=dur_mins
    )
    db.add(r)
    db.commit()
    return RedirectResponse(url="/admin/routes", status_code=303)

@router.post("/routes/{route_id}/delete")
async def delete_route(request: Request, route_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    r = db.query(Route).filter(Route.id == route_id).first()
    if r:
        db.delete(r)
        db.commit()
    return RedirectResponse(url="/admin/routes", status_code=303)
