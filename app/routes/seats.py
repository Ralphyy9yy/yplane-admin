from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models.seat import Seat, SeatStatus
from app.models.schedule import Schedule

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


def sync_available_seats(db: Session, schedule: Schedule) -> None:
    schedule.available_seats = db.query(Seat).filter(
        Seat.schedule_id == schedule.id, Seat.status == SeatStatus.available
    ).count()


def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None


@router.get("/seats", response_class=HTMLResponse)
async def all_seats(request: Request, schedule_id: int | None = None, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedules = db.query(Schedule).order_by(Schedule.departure_time.desc()).all()
    query = db.query(Seat)
    if schedule_id:
        query = query.filter(Seat.schedule_id == schedule_id)
    seats = query.order_by(Seat.schedule_id, Seat.seat_number).all()
    return templates.TemplateResponse("seats/all.html", {
        "request": request, "admin": admin, "schedules": schedules, "seats": seats,
        "schedule_id": schedule_id, "active_page": "seats",
    })


@router.get("/schedules/{schedule_id}/seats", response_class=HTMLResponse)
async def list_seats(request: Request, schedule_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    seats = db.query(Seat).filter(Seat.schedule_id == schedule_id).order_by(Seat.seat_number).all()
    return templates.TemplateResponse(
        "seats/list.html",
        {"request": request, "admin": admin, "schedule": schedule, "seats": seats, "statuses": SeatStatus, "active_page": "schedules", "error": None},
    )


@router.post("/schedules/{schedule_id}/seats", response_class=HTMLResponse)
async def add_seat(
    request: Request,
    schedule_id: int,
    seat_number: str = Form(...),
    status: str = Form("available"),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    seats = db.query(Seat).filter(Seat.schedule_id == schedule_id).order_by(Seat.seat_number).all()
    try:
        seat = Seat(schedule_id=schedule_id, seat_number=seat_number.strip(), status=SeatStatus(status))
        db.add(seat)
        db.flush()
        sync_available_seats(db, schedule)
        db.commit()
        return RedirectResponse(url=f"/admin/schedules/{schedule_id}/seats", status_code=302)
    except IntegrityError:
        db.rollback()
        seats = db.query(Seat).filter(Seat.schedule_id == schedule_id).order_by(Seat.seat_number).all()
        return templates.TemplateResponse(
            "seats/list.html",
            {"request": request, "admin": admin, "schedule": schedule, "seats": seats, "statuses": SeatStatus, "active_page": "schedules", "error": f"Seat '{seat_number}' already exists for this schedule."},
            status_code=400,
        )


@router.post("/seats/{seat_id}/edit")
async def update_seat(
    request: Request,
    seat_id: int,
    status: str = Form(...),
    seat_number: str = Form(...),
    db: Session = Depends(get_db),
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    seat = db.query(Seat).filter(Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    schedule_id = seat.schedule_id
    seat.seat_number = seat_number.strip()
    seat.status = SeatStatus(status)
    sync_available_seats(db, seat.schedule)
    db.commit()
    return RedirectResponse(url=f"/admin/schedules/{schedule_id}/seats", status_code=302)


@router.post("/seats/{seat_id}/delete")
async def delete_seat(request: Request, seat_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    seat = db.query(Seat).filter(Seat.id == seat_id).first()
    if not seat:
        raise HTTPException(status_code=404, detail="Seat not found")
    schedule_id = seat.schedule_id
    schedule = seat.schedule
    db.delete(seat)
    db.flush()
    sync_available_seats(db, schedule)
    db.commit()
    return RedirectResponse(url=f"/admin/schedules/{schedule_id}/seats", status_code=302)
