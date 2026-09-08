from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models.schedule import Schedule
from app.models.seat import Seat

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None


@router.get("/schedules", response_class=HTMLResponse)
async def list_schedules(request: Request, search: str = "", db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    query = db.query(Schedule)
    if search:
        query = query.filter(Schedule.route.ilike(f"%{search}%"))
    schedules = query.order_by(Schedule.departure_time.desc()).all()
    return templates.TemplateResponse(request=request, name="schedules/list.html", context={"request": request, "admin": admin, "schedules": schedules, "search": search, "active_page": "schedules"},
    )


@router.get("/schedules/new", response_class=HTMLResponse)
async def new_schedule_form(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse(request=request, name="schedules/form.html", context={"request": request, "admin": admin, "schedule": None, "errors": {}, "active_page": "schedules"},
    )


@router.post("/schedules/new", response_class=HTMLResponse)
async def create_schedule(
    request: Request,
    route: str = Form(...),
    origin: str = Form(""),
    destination: str = Form(""),
    departure_time: str = Form(...),
    arrival_time: str = Form(...),
    price: float = Form(...),
    total_seats: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    errors = {}
    if not route:
        errors["route"] = "Route is required."
    if price < 0:
        errors["price"] = "Price must be >= 0."
    if total_seats <= 0:
        errors["total_seats"] = "Total seats must be > 0."
    try:
        dep_dt = datetime.fromisoformat(departure_time)
        arr_dt = datetime.fromisoformat(arrival_time)
        if arr_dt <= dep_dt:
            errors["arrival_time"] = "Arrival must be after departure."
    except ValueError:
        errors["departure_time"] = "Invalid datetime format."
        dep_dt = arr_dt = datetime.utcnow()

    if errors:
        return templates.TemplateResponse(request=request, name="schedules/form.html", context={"request": request, "admin": admin, "schedule": None, "errors": errors, "active_page": "schedules"},
            status_code=400,
        )

    schedule = Schedule(
        route=route, origin=origin, destination=destination,
        departure_time=dep_dt, arrival_time=arr_dt,
        price=price, total_seats=total_seats, available_seats=total_seats,
        created_by=int(admin["sub"]),
    )
    db.add(schedule)
    db.commit()
    return RedirectResponse(url="/admin/schedules", status_code=302)


@router.get("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def edit_schedule_form(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return templates.TemplateResponse(request=request, name="schedules/form.html", context={"request": request, "admin": admin, "schedule": schedule, "errors": {}, "active_page": "schedules"},
    )


@router.post("/schedules/{schedule_id}/edit", response_class=HTMLResponse)
async def update_schedule(
    request: Request,
    schedule_id: int,
    route: str = Form(...),
    origin: str = Form(""),
    destination: str = Form(""),
    departure_time: str = Form(...),
    arrival_time: str = Form(...),
    price: float = Form(...),
    total_seats: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    errors = {}
    if not route:
        errors["route"] = "Route is required."
    if price < 0:
        errors["price"] = "Price must be >= 0."
    if total_seats <= 0:
        errors["total_seats"] = "Total seats must be > 0."
    try:
        dep_dt = datetime.fromisoformat(departure_time)
        arr_dt = datetime.fromisoformat(arrival_time)
        if arr_dt <= dep_dt:
            errors["arrival_time"] = "Arrival must be after departure."
    except ValueError:
        errors["departure_time"] = "Invalid datetime format."
        dep_dt = arr_dt = schedule.departure_time

    if errors:
        return templates.TemplateResponse(request=request, name="schedules/form.html", context={"request": request, "admin": admin, "schedule": schedule, "errors": errors, "active_page": "schedules"},
            status_code=400,
        )

    diff_seats = total_seats - schedule.total_seats
    schedule.route = route
    schedule.origin = origin
    schedule.destination = destination
    schedule.departure_time = dep_dt
    schedule.arrival_time = arr_dt
    schedule.price = price
    schedule.total_seats = total_seats
    schedule.available_seats = max(0, schedule.available_seats + diff_seats)
    db.commit()
    return RedirectResponse(url="/admin/schedules", status_code=302)


@router.post("/schedules/{schedule_id}/delete")
async def delete_schedule(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if schedule:
        db.delete(schedule)
        db.commit()
    return RedirectResponse(url="/admin/schedules", status_code=302)
