from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_admin_from_cookie
from app.models import Airplane, Seat

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

def require_admin(request: Request):
    try:
        return get_current_admin_from_cookie(request)
    except HTTPException:
        return None

@router.get("/airplanes", response_class=HTMLResponse)
async def list_airplanes(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    airplanes = db.query(Airplane).order_by(Airplane.id).all()
    return templates.TemplateResponse("airplanes/list.html", {
        "request": request, "admin": admin, "airplanes": airplanes, "active_page": "airplanes"
    })

@router.get("/airplanes/new", response_class=HTMLResponse)
async def new_airplane_form(request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    return templates.TemplateResponse("airplanes/form.html", {
        "request": request, "admin": admin, "airplane": None, "errors": {}, "active_page": "airplanes"
    })

@router.post("/airplanes/new", response_class=HTMLResponse)
async def create_airplane(
    request: Request,
    airplane_code: str = Form(...),
    airplane_name: str = Form(...),
    airplane_type: str = Form(...),
    rows: int = Form(20),
    cols: str = Form("A,B,C,D,E,F"),
    status: str = Form("ACTIVE"),
    db: Session = Depends(get_db)
):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    code = airplane_code.strip().upper()
    existing = db.query(Airplane).filter(Airplane.airplane_code == code).first()
    if existing:
        return templates.TemplateResponse("airplanes/form.html", {
            "request": request, "admin": admin, "airplane": None, "errors": {"airplane_code": f"Aircraft code '{code}' already exists."}, "active_page": "airplanes"
        }, status_code=400)
    col_list = [c.strip().upper() for c in cols.split(",") if c.strip()]
    total_seats = rows * len(col_list)
    ap = Airplane(
        airplane_code=code,
        airplane_name=airplane_name.strip(),
        airplane_type=airplane_type.strip(),
        total_seats=total_seats,
        status=status
    )
    db.add(ap)
    db.flush()

    for r in range(1, rows + 1):
        stype = "BUSINESS" if r <= 2 else ("PREMIUM" if r <= 4 else "ECONOMY")
        for c in col_list:
            pos = "WINDOW" if c in [col_list[0], col_list[-1]] else ("MIDDLE" if len(col_list) >= 5 and c in [col_list[1], col_list[-2]] else "AISLE")
            seat = Seat(
                airplane_id=ap.id,
                seat_number=f"{r}{c}",
                seat_type=stype,
                seat_position=pos
            )
            db.add(seat)
    db.commit()
    return RedirectResponse(url="/admin/airplanes", status_code=303)

@router.get("/airplanes/{airplane_id}/seats", response_class=HTMLResponse)
async def view_airplane_seats(request: Request, airplane_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    ap = db.query(Airplane).filter(Airplane.id == airplane_id).first()
    if not ap:
        raise HTTPException(status_code=404, detail="Aircraft not found")
    seats = db.query(Seat).filter(Seat.airplane_id == airplane_id).order_by(Seat.id).all()
    return templates.TemplateResponse("airplanes/seats.html", {
        "request": request, "admin": admin, "airplane": ap, "seats": seats, "active_page": "airplanes"
    })

@router.post("/airplanes/{airplane_id}/delete")
async def delete_airplane(request: Request, airplane_id: int, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if not admin:
        return RedirectResponse(url="/auth/login", status_code=302)
    ap = db.query(Airplane).filter(Airplane.id == airplane_id).first()
    if ap:
        db.delete(ap)
        db.commit()
    return RedirectResponse(url="/admin/airplanes", status_code=303)
