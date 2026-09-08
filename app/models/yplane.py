from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
import uuid
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time as SqlTime,
    Numeric, ForeignKey, UniqueConstraint, Text, Enum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    role = Column(Enum('CUSTOMER', 'ADMIN', name='user_role', create_type=False), nullable=False, default="CUSTOMER")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    
    # Extra columns not strictly in mobile Supabase schema but useful for local admin login fallback
    password_hash = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    bookings = relationship("Booking", back_populates="user")


class Airplane(Base):
    __tablename__ = "airplanes"

    id = Column(Integer, primary_key=True, index=True)
    model_number = Column(String(50), nullable=False)
    total_seats = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    seats = relationship("Seat", back_populates="airplane", cascade="all, delete-orphan")
    flights = relationship("Flight", back_populates="airplane")


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="Philippines")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    departing_routes = relationship("Route", foreign_keys="[Route.origin_airport_id]", back_populates="origin_airport")
    arriving_routes = relationship("Route", foreign_keys="[Route.destination_airport_id]", back_populates="destination_airport")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=False, default=0.00)
    estimated_duration_minutes = Column(Integer, nullable=False, default=60)
    base_price = Column(Numeric(10, 2), nullable=False, default=100.00)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id], back_populates="departing_routes")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], back_populates="arriving_routes")
    flights = relationship("Flight", back_populates="route", cascade="all, delete-orphan")


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    flight_number = Column(String(20), unique=True, nullable=False, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    airplane_id = Column(Integer, ForeignKey("airplanes.id"), nullable=False)
    departure_time = Column(DateTime(timezone=True), nullable=False)
    arrival_time = Column(DateTime(timezone=True), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    available_seats = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED")  # SCHEDULED | BOARDING | COMPLETED | CANCELLED
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    route = relationship("Route", back_populates="flights")
    airplane = relationship("Airplane", back_populates="flights")
    bookings = relationship("Booking", back_populates="flight", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("airplane_id", "seat_number", name="uq_airplane_seat"),)

    id = Column(Integer, primary_key=True, index=True)
    airplane_id = Column(Integer, ForeignKey("airplanes.id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String(10), nullable=False)
    seat_class = Column(Enum('ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST_CLASS', name='seat_class', create_type=False), nullable=False, default="ECONOMY")
    seat_position = Column(Enum('WINDOW', 'MIDDLE', 'AISLE', name='seat_position', create_type=False), nullable=False, default="AISLE")

    airplane = relationship("Airplane", back_populates="seats")
    booking_seats = relationship("BookingSeat", back_populates="seat")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id", ondelete="CASCADE"), nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    status = Column(Enum('PENDING', 'RESERVED', 'CONFIRMED', 'CANCELLED', 'REJECTED', name='booking_status', create_type=False), nullable=False, default="PENDING")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    requested_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    queue_position = Column(Integer, nullable=True)

    user = relationship("User", back_populates="bookings")
    flight = relationship("Flight", back_populates="bookings")
    booking_seats = relationship("BookingSeat", back_populates="booking", cascade="all, delete-orphan")
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")
    logs = relationship("BookingLog", back_populates="booking")


class BookingSeat(Base):
    __tablename__ = "booking_seats"
    __table_args__ = (UniqueConstraint("booking_id", "seat_id", name="uq_booking_seat"),)

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id", ondelete="CASCADE"), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)

    booking = relationship("Booking", back_populates="booking_seats")
    seat = relationship("Seat", back_populates="booking_seats")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(Enum('WALLET', 'CREDIT_CARD', 'DEBIT_CARD', 'PAYPAL', 'BANK_TRANSFER', name='payment_method', create_type=False), nullable=False, default="WALLET")
    payment_status = Column(Enum('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED', name='payment_status', create_type=False), nullable=False, default="PENDING")
    transaction_reference = Column(String(50), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="payment")


class BookingLog(Base):
    __tablename__ = "booking_logs"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    # The Supabase schema doesn't have a strict user_id foreign key in booking_logs
    processing_type = Column(Enum('SEQUENTIAL', 'CONCURRENT', name='processing_type', create_type=False), nullable=False, default="SEQUENTIAL")
    status = Column(Enum('QUEUED', 'PROCESSING', 'SUCCESS', 'FAILED', name='processing_status', create_type=False), nullable=False)
    message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    booking = relationship("Booking", back_populates="logs")

class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
