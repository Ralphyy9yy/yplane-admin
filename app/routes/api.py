from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models import Flight, Seat, User, Booking, BookingSeat, BookingLog, Route
from app.services.booking_service import submit_booking_request, get_flight_seat_availability

router = APIRouter()

# --- Schemas ---

class LoginPayload(BaseModel):
    email: str
    password: str

class RegisterPayload(BaseModel):
    name: str
    email: str
    password: str

class BookingRequestPayload(BaseModel):
    user_id: int
    flight_id: int
    seat_id: int

# --- Auth Endpoints for Flutter ---

@router.post("/auth/login")
def mobile_login(body: LoginPayload, db: Session = Depends(get_db)):
    """Authenticate customer in Flutter mobile app."""
    clean_email = body.email.strip().lower()
    user = db.query(User).filter(User.email.ilike(clean_email)).first()

    pwd_valid = False
    if user and user.password_hash:
        if verify_password(body.password, user.password_hash):
            pwd_valid = True

    if not user or not pwd_valid:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account has been deactivated")

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/auth/register", status_code=status.HTTP_201_CREATED)
def mobile_register(body: RegisterPayload, db: Session = Depends(get_db)):
    """Register new customer in Flutter mobile app."""
    clean_email = body.email.strip().lower()
    existing = db.query(User).filter(User.email.ilike(clean_email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(body.password)
    user = User(
        name=body.name.strip(),
        email=clean_email,
        password_hash=hashed,
        role="CUSTOMER",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role
        }
    }

# --- Flight & Seat Endpoints ---

@router.get("/flights")
def get_flights(db: Session = Depends(get_db)):
    """List available flights with airport codes and schedule."""
    flights = (
        db.query(Flight)
        .options(
            joinedload(Flight.route).joinedload(Route.origin_airport),
            joinedload(Flight.route).joinedload(Route.destination_airport)
        )
        .order_by(Flight.departure_time.asc())
        .all()
    )
    return [
        {
            "id": f.id,
            "flight_number": f.flight_number,
            "origin": f.route.origin_airport.code if f.route and f.route.origin_airport else "",
            "origin_city": f.route.origin_airport.city if f.route and f.route.origin_airport else "",
            "destination": f.route.destination_airport.code if f.route and f.route.destination_airport else "",
            "destination_city": f.route.destination_airport.city if f.route and f.route.destination_airport else "",
            "date": str(f.departure_time.date()) if f.departure_time else "",
            "departure": str(f.departure_time),
            "arrival": str(f.arrival_time),
            "fare": float(f.price),
            "status": f.status
        }
        for f in flights
    ]

@router.get("/flights/{flight_id}/seats")
def get_seats(flight_id: int, db: Session = Depends(get_db)):
    """Fetch seat map and real-time availability for flight."""
    return get_flight_seat_availability(db, flight_id)

# --- Booking Endpoints (Sequential Queue) ---

@router.post("/bookings", status_code=status.HTTP_202_ACCEPTED)
def create_booking(body: BookingRequestPayload, db: Session = Depends(get_db)):
    """Submit booking into sequential FIFO processing queue."""
    user = db.query(User).filter(User.id == body.user_id, User.is_active == True).first()
    flight = db.query(Flight).filter(Flight.id == body.flight_id).first()
    seat = db.query(Seat).filter(Seat.id == body.seat_id, Seat.airplane_id == flight.airplane_id if flight else -1).first()

    if not user:
        raise HTTPException(status_code=404, detail="Active passenger account not found")
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    if not seat:
        raise HTTPException(status_code=400, detail="Seat does not belong to this flight's airplane")

    # Enqueue into single-worker sequential pipeline
    submit_booking_request(user.id, flight.id, seat.id, flight.price)
    return {
        "status": "QUEUED",
        "message": "Booking request placed into sequential processing queue",
        "flight_id": flight.id,
        "seat_id": seat.id,
        "user_id": user.id
    }

@router.get("/users/{user_id}/bookings")
def get_user_bookings(user_id: int, db: Session = Depends(get_db)):
    """Get all bookings and tickets for a passenger in Flutter."""
    bookings = (
        db.query(Booking)
        .options(
            joinedload(Booking.flight).joinedload(Flight.route),
            joinedload(Booking.booking_seats).joinedload(BookingSeat.seat)
        )
        .filter(Booking.user_id == user_id)
        .order_by(Booking.created_at.desc())
        .all()
    )
    result = []
    for b in bookings:
        seats = [bs.seat.seat_number for bs in b.booking_seats if bs.seat]
        result.append({
            "id": b.id,
            "booking_reference": b.booking_reference,
            "flight_number": b.flight.flight_number if b.flight else "",
            "origin": b.flight.route.origin_airport.code if b.flight and b.flight.route else "",
            "destination": b.flight.route.destination_airport.code if b.flight and b.flight.route else "",
            "departure_date": str(b.flight.departure_time.date()) if b.flight and b.flight.departure_time else "",
            "seats": seats,
            "total_amount": float(b.total_amount),
            "status": b.status,
            "created_at": str(b.created_at)
        })
    return result

@router.get("/bookings/{booking_id}")
def get_booking_status(booking_id: int, db: Session = Depends(get_db)):
    """Check status of a specific booking (CONFIRMED, REJECTED, PENDING)."""
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return {
        "id": booking.id,
        "booking_reference": booking.booking_reference,
        "status": booking.status,
        "total_amount": float(booking.total_amount)
    }

