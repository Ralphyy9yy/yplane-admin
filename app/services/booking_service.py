from decimal import Decimal
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Flight, Seat, Booking, BookingSeat, Payment, User
from app.services import queue_service


def get_flight_seat_availability(db: Session, flight_id: int) -> List[Dict[str, Any]]:
    """
    Computes seat availability for a specific flight dynamically:
    Seats belong to the airplane assigned to the flight.
    A seat is 'booked' if there is an active booking_seats row joined to bookings
    with status PENDING or CONFIRMED for this flight.
    """
    flight = db.query(Flight).filter(Flight.id == flight_id).first()
    if not flight:
        return []

    # Get all physical seats on this flight's airplane
    airplane_seats = (
        db.query(Seat)
        .filter(Seat.airplane_id == flight.airplane_id)
        .order_by(Seat.id)
        .all()
    )

    # Get all currently booked seat IDs for this flight
    booked_seat_ids = set(
        db.query(BookingSeat.seat_id)
        .join(Booking, BookingSeat.booking_id == Booking.id)
        .filter(
            Booking.flight_id == flight_id,
            Booking.status.in_(["PENDING", "CONFIRMED"])
        )
        .all()
    )
    booked_seat_ids = {s[0] for s in booked_seat_ids}

    result = []
    for seat in airplane_seats:
        is_booked = seat.id in booked_seat_ids
        result.append({
            "seat_id": seat.id,
            "seat_number": seat.seat_number,
            "seat_class": seat.seat_class,
            "seat_position": seat.seat_position,
            "status": "booked" if is_booked else "available",
            "is_available": not is_booked,
        })
    return result


import uuid

def submit_booking_request(user_id: uuid.UUID, flight_id: int, seat_id: int, fare: Optional[Decimal] = None) -> None:
    """Enqueues a booking request into the sequential processing pipeline."""
    queue_service.enqueue_booking(user_id, flight_id, seat_id, fare)


def cancel_booking_request(booking_id: int, admin_id: Optional[str] = None) -> Dict[str, Any]:
    """Cancels a confirmed booking and frees the seat."""
    return queue_service.cancel_booking(booking_id, admin_id)
