import queue
import tempfile
import time
import unittest
from datetime import datetime, date, time as dt_time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    User, Airplane, Airport, Route, Flight, Seat,
    Booking, BookingSeat, Payment, BookingLog
)
from app.services import queue_service, booking_service


class SequentialBookingTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tempdir.name) / "queue-test.db"
        self.engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine, expire_on_commit=False)
        self.original_session = queue_service.SessionLocal
        queue_service.SessionLocal = self.Session
        queue_service.booking_queue = queue.Queue()

    def tearDown(self):
        queue_service.stop_worker()
        queue_service.SessionLocal = self.original_session
        self.engine.dispose()
        self.tempdir.cleanup()

    def test_five_customers_compete_for_one_flight_seat(self):
        db = self.Session()
        admin = User(name="Admin", email="admin@yplane.test", password="x", role="ADMIN")
        users = [User(name=f"Passenger {i}", email=f"p{i}@yplane.test", password="x", role="CUSTOMER") for i in range(1, 6)]
        db.add_all([admin, *users])
        db.flush()

        origin = Airport(airport_code="TAG", airport_name="Panglao Hub", city="Panglao", country="Philippines")
        dest = Airport(airport_code="MNL", airport_name="Manila", city="Manila", country="Philippines")
        db.add_all([origin, dest])
        db.flush()

        route = Route(origin_airport_id=origin.id, destination_airport_id=dest.id, distance=Decimal("630"), estimated_duration=dt_time(1, 25))
        db.add(route)
        db.flush()

        airplane = Airplane(airplane_code="RP-TEST", airplane_name="Test Aircraft", airplane_type="Jet", total_seats=1, status="ACTIVE")
        db.add(airplane)
        db.flush()

        seat = Seat(airplane_id=airplane.id, seat_number="1A", seat_type="BUSINESS", seat_position="WINDOW")
        db.add(seat)
        db.flush()

        flight = Flight(
            flight_number="YP-TEST-01",
            route_id=route.id,
            airplane_id=airplane.id,
            departure_date=date.today() + timedelta(days=1),
            departure_time=dt_time(9, 0),
            arrival_time=dt_time(10, 25),
            fare=Decimal("3500.00"),
            status="SCHEDULED"
        )
        db.add(flight)
        db.commit()

        # Start single dedicated sequential worker
        queue_service.start_worker()

        # Fire 5 booking requests simultaneously for seat 1A on flight YP-TEST-01
        for user in users:
            queue_service.enqueue_booking(user.id, flight.id, seat.id, flight.fare)

        # Wait for FIFO queue to be drained
        queue_service.booking_queue.join()
        time.sleep(0.2)
        db.expire_all()

        # Verification:
        # 1. Booking table has exactly 1 CONFIRMED booking
        confirmed_bookings = db.query(Booking).filter(Booking.flight_id == flight.id, Booking.status == "CONFIRMED").all()
        self.assertEqual(len(confirmed_bookings), 1)

        # 2. Payment table has 1 PAID transaction
        paid_payments = db.query(Payment).filter(Payment.status == "PAID").all()
        self.assertEqual(len(paid_payments), 1)
        self.assertEqual(paid_payments[0].amount, Decimal("3500.00"))

        # 3. Booking logs contain 5 entries: exactly 1 SUCCESS and 4 REJECTED
        logs = db.query(BookingLog).order_by(BookingLog.started_at.asc()).all()
        self.assertEqual(len(logs), 5)
        self.assertEqual(logs[0].status, "SUCCESS")
        self.assertEqual(logs[0].action, "BOOK_SEAT")
        self.assertEqual(logs[0].processing_type, "SEQUENTIAL")

        for log in logs[1:]:
            self.assertEqual(log.status, "REJECTED")
            self.assertIn("already reserved", log.message)

        # 4. Computed seat availability for this flight now shows 0 available
        avail = booking_service.get_flight_seat_availability(db, flight.id)
        self.assertEqual(len(avail), 1)
        self.assertEqual(avail[0]["status"], "booked")
        self.assertFalse(avail[0]["is_available"])

        db.close()


if __name__ == "__main__":
    unittest.main()
