from sqlalchemy import text
from app.core.database import engine, Base
from app.models import (
    User, Airplane, Airport, Route, Flight, Seat,
    Booking, BookingSeat, Payment, BookingLog, SystemLog
)

with engine.begin() as conn:
    print("Dropping old legacy tables...")
    conn.execute(text("DROP TABLE IF EXISTS booking_logs CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS system_logs CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS payments CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS booking_seats CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS bookings CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS seats CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS flights CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS routes CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS airports CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS airplanes CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS schedules CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS transactions CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS processing_queue CASCADE;"))

print("Creating official YPlane 11-table schema...")
Base.metadata.create_all(bind=engine)
print("All 11 YPlane tables created successfully!")
