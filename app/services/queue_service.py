import queue
import threading
import logging
import time
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import SessionLocal
from app.models import (
    Booking, BookingSeat, Seat, Flight, User, Payment, BookingLog
)

logger = logging.getLogger("yplane.queue")
logging.basicConfig(level=logging.INFO)

# Global FIFO request queue
booking_queue: queue.Queue = queue.Queue()
_worker_thread: Optional[threading.Thread] = None
_worker_running: bool = False


class BookingRequestItem:
    def __init__(self, user_id: int, flight_id: int, seat_id: int, fare: Optional[Decimal] = None):
        self.user_id = user_id
        self.flight_id = flight_id
        self.seat_id = seat_id
        self.fare = fare
        self.arrival_time = datetime.utcnow()


def generate_booking_reference() -> str:
    return f"YP-{uuid.uuid4().hex[:8].upper()}"


def generate_transaction_reference() -> str:
    return f"TXN-{uuid.uuid4().hex[:10].upper()}"


def process_booking(req: BookingRequestItem) -> Dict[str, Any]:
    """
    Atomic sequential processing with row-level locking.
    Evaluated one-at-a-time by the single dedicated worker thread.
    """
    started_at = datetime.utcnow()
    db: Session = SessionLocal()
    try:
        flight = db.query(Flight).filter(Flight.id == req.flight_id).first()
        seat = db.query(Seat).filter(Seat.id == req.seat_id).first()
        user = db.query(User).filter(User.id == req.user_id).first()

        if not flight or not seat or not user:
            log = BookingLog(
                user_id=req.user_id,
                action="BOOK_SEAT",
                processing_type="SEQUENTIAL",
                status="FAILED",
                message=f"Invalid flight ({req.flight_id}), seat ({req.seat_id}), or user ({req.user_id})",
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            return {"status": "FAILED", "message": log.message}

        fare = req.fare or flight.fare

        # ATOMIC CHECK-AND-RESERVE (Row-level lock on existing bookings for this flight & seat)
        existing = (
            db.query(BookingSeat)
            .join(Booking, BookingSeat.booking_id == Booking.id)
            .filter(
                Booking.flight_id == req.flight_id,
                BookingSeat.seat_id == req.seat_id,
                Booking.status.in_(["PENDING", "CONFIRMED"]),
            )
            .with_for_update()
            .first()
        )

        # Introduce slight observable delta (350ms) so demo viewers see the sequential queue steps
        time.sleep(0.35)
        completed_at = datetime.utcnow()

        if existing:
            # REJECT: Seat already booked on this flight
            log = BookingLog(
                user_id=user.id,
                action="BOOK_SEAT",
                processing_type="SEQUENTIAL",
                status="REJECTED",
                message=f"Seat {seat.seat_number} already reserved on Flight {flight.flight_number}",
                started_at=started_at,
                completed_at=completed_at
            )
            db.add(log)
            db.commit()
            logger.info(f"[REJECTED] User {user.name} for seat {seat.seat_number} on flight {flight.flight_number}")
            return {"status": "REJECTED", "message": log.message, "log_id": log.id}

        # CONFIRM: Seat is available
        ref = generate_booking_reference()
        booking = Booking(
            user_id=user.id,
            flight_id=flight.id,
            booking_reference=ref,
            total_amount=fare,
            status="CONFIRMED",
            booked_at=completed_at
        )
        db.add(booking)
        db.flush()

        booking_seat = BookingSeat(
            booking_id=booking.id,
            seat_id=seat.id,
            price=fare
        )
        db.add(booking_seat)

        # Simulated Payment Record
        payment = Payment(
            booking_id=booking.id,
            amount=fare,
            payment_method="SIMULATED_CARD",
            transaction_reference=generate_transaction_reference(),
            status="PAID",
            paid_at=completed_at
        )
        db.add(payment)

        # Write sequential audit log
        log = BookingLog(
            booking_id=booking.id,
            user_id=user.id,
            action="BOOK_SEAT",
            processing_type="SEQUENTIAL",
            status="SUCCESS",
            message=f"Seat {seat.seat_number} booked successfully. Ref: {ref}",
            started_at=started_at,
            completed_at=completed_at
        )
        db.add(log)
        db.commit()
        logger.info(f"[SUCCESS] User {user.name} booked seat {seat.seat_number} on flight {flight.flight_number} (Ref: {ref})")
        return {"status": "SUCCESS", "booking_id": booking.id, "reference": ref, "log_id": log.id}

    except Exception as e:
        db.rollback()
        logger.error(f"Error processing booking request: {e}")
        try:
            log = BookingLog(
                user_id=req.user_id,
                action="BOOK_SEAT",
                processing_type="SEQUENTIAL",
                status="FAILED",
                message=str(e)[:300],
                started_at=started_at,
                completed_at=datetime.utcnow()
            )
            db.add(log)
            db.commit()
        except Exception:
            pass
        return {"status": "FAILED", "message": str(e)}
    finally:
        db.close()


def cancel_booking(booking_id: int, admin_id: Optional[int] = None) -> Dict[str, Any]:
    """Admin manual override to cancel a booking and release its seat."""
    started_at = datetime.utcnow()
    db: Session = SessionLocal()
    try:
        booking = db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return {"success": False, "error": "Booking not found"}

        if booking.status in ["CANCELLED", "REJECTED"]:
            return {"success": False, "error": f"Booking is already {booking.status}"}

        booking.status = "CANCELLED"

        if booking.payment:
            booking.payment.status = "REFUNDED"

        log = BookingLog(
            booking_id=booking.id,
            user_id=booking.user_id,
            action="CANCEL_SEAT",
            processing_type="SEQUENTIAL",
            status="SUCCESS",
            message=f"Booking {booking.booking_reference} cancelled by Admin override (Seat released)",
            started_at=started_at,
            completed_at=datetime.utcnow()
        )
        db.add(log)
        db.commit()
        return {"success": True, "message": f"Booking {booking.booking_reference} cancelled successfully"}
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}
    finally:
        db.close()


def worker_loop():
    """Single dedicated worker pulling requests one-at-a-time (strict FIFO)."""
    global _worker_running
    _worker_running = True
    logger.info("YPlane Sequential Booking Queue Worker started.")
    while _worker_running:
        try:
            req: BookingRequestItem = booking_queue.get(timeout=1.0)
            logger.info(f"Worker dequeued booking request for user {req.user_id}, flight {req.flight_id}, seat {req.seat_id}")
            process_booking(req)
            booking_queue.task_done()
        except queue.Empty:
            continue
        except Exception as e:
            logger.error(f"Worker unexpected error: {e}")
    logger.info("YPlane Sequential Booking Queue Worker stopped.")


def start_worker():
    global _worker_thread, _worker_running
    if _worker_thread and _worker_thread.is_alive():
        return
    _worker_running = True
    _worker_thread = threading.Thread(target=worker_loop, daemon=True, name="YPlaneQueueWorker")
    _worker_thread.start()
    logger.info("YPlane queue worker thread launched.")


def stop_worker():
    global _worker_running, _worker_thread
    _worker_running = False
    if _worker_thread and _worker_thread.is_alive():
        _worker_thread.join(timeout=2.0)
    _worker_thread = None


def enqueue_booking(user_id: int, flight_id: int, seat_id: int, fare: Optional[Decimal] = None) -> None:
    req = BookingRequestItem(user_id, flight_id, seat_id, fare)
    booking_queue.put(req)
    logger.info(f"Enqueued request for user {user_id}, flight {flight_id}, seat {seat_id}. Queue depth: {booking_queue.qsize()}")


def get_queue_depth() -> int:
    return booking_queue.qsize()
