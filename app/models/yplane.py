from datetime import datetime, date, time
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Time as SqlTime,
    Numeric, ForeignKey, UniqueConstraint, Text
)
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    role = Column(String(20), nullable=False, default="CUSTOMER")  # CUSTOMER | ADMIN
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    bookings = relationship("Booking", back_populates="user")
    logs = relationship("BookingLog", back_populates="user")


class Airplane(Base):
    __tablename__ = "airplanes"

    id = Column(Integer, primary_key=True, index=True)
    airplane_code = Column(String(20), unique=True, nullable=False, index=True)  # e.g. RP-C8810
    airplane_name = Column(String(100), nullable=False)
    airplane_type = Column(String(50), nullable=False)  # Airbus A320, ATR 72, etc.
    total_seats = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE")  # ACTIVE | MAINTENANCE | INACTIVE

    seats = relationship("Seat", back_populates="airplane", cascade="all, delete-orphan")
    flights = relationship("Flight", back_populates="airplane")


class Airport(Base):
    __tablename__ = "airports"

    id = Column(Integer, primary_key=True, index=True)
    airport_code = Column(String(10), unique=True, nullable=False, index=True)  # e.g. TAG, MNL
    airport_name = Column(String(150), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False, default="Philippines")

    departing_routes = relationship("Route", foreign_keys="[Route.origin_airport_id]", back_populates="origin_airport")
    arriving_routes = relationship("Route", foreign_keys="[Route.destination_airport_id]", back_populates="destination_airport")


class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    origin_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey("airports.id"), nullable=False)
    distance = Column(Numeric(10, 2), nullable=True)
    estimated_duration = Column(SqlTime, nullable=True)

    origin_airport = relationship("Airport", foreign_keys=[origin_airport_id], back_populates="departing_routes")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], back_populates="arriving_routes")
    flights = relationship("Flight", back_populates="route", cascade="all, delete-orphan")


class Flight(Base):
    __tablename__ = "flights"

    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=False)
    airplane_id = Column(Integer, ForeignKey("airplanes.id"), nullable=False)
    flight_number = Column(String(20), nullable=False, index=True)  # e.g. XP-TAG-101
    departure_date = Column(Date, nullable=False)
    departure_time = Column(SqlTime, nullable=False)
    arrival_time = Column(SqlTime, nullable=False)
    fare = Column(Numeric(10, 2), nullable=False)
    status = Column(String(20), nullable=False, default="SCHEDULED")  # SCHEDULED | BOARDING | COMPLETED | CANCELLED

    route = relationship("Route", back_populates="flights")
    airplane = relationship("Airplane", back_populates="flights")
    bookings = relationship("Booking", back_populates="flight", cascade="all, delete-orphan")


class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("airplane_id", "seat_number", name="uq_airplane_seat"),)

    id = Column(Integer, primary_key=True, index=True)
    airplane_id = Column(Integer, ForeignKey("airplanes.id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String(10), nullable=False)  # e.g. 1A, 2B, 15F
    seat_type = Column(String(20), nullable=False, default="ECONOMY")  # ECONOMY | PREMIUM | BUSINESS
    seat_position = Column(String(10), nullable=True)  # WINDOW | MIDDLE | AISLE

    airplane = relationship("Airplane", back_populates="seats")
    booking_seats = relationship("BookingSeat", back_populates="seat")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    flight_id = Column(Integer, ForeignKey("flights.id"), nullable=False)
    booking_reference = Column(String(30), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0.00)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING | CONFIRMED | CANCELLED | REJECTED
    booked_at = Column(DateTime, nullable=False, default=datetime.utcnow)

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
    payment_method = Column(String(50), nullable=False, default="SIMULATED_CARD")
    transaction_reference = Column(String(50), unique=True, nullable=False, index=True)
    status = Column(String(20), nullable=False, default="PENDING")  # PENDING | PAID | FAILED | REFUNDED
    paid_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="payment")


class BookingLog(Base):
    __tablename__ = "booking_logs"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)  # BOOK_SEAT | CANCEL_SEAT
    processing_type = Column(String(20), nullable=False, default="SEQUENTIAL")
    status = Column(String(20), nullable=False)  # SUCCESS | FAILED | REJECTED | PENDING
    message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    booking = relationship("Booking", back_populates="logs")
    user = relationship("User", back_populates="logs")


class SystemLog(Base):
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
