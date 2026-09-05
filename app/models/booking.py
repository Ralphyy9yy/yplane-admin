from sqlalchemy import Column, Integer, String, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base
import enum

class BookingStatus(str, enum.Enum):
    pending = "pending"
    reserved = "reserved"
    confirmed = "confirmed"
    cancelled = "cancelled"
    rejected = "rejected"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    seat_id = Column(Integer, ForeignKey("seats.id"), nullable=True)
    status = Column(Enum(BookingStatus), default=BookingStatus.pending, nullable=False)
    requested_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    queue_position = Column(Integer, nullable=True)

    user = relationship("User", back_populates="bookings")
    schedule = relationship("Schedule", back_populates="bookings")
    seat = relationship("Seat", back_populates="bookings")
    transaction = relationship("Transaction", back_populates="booking", uselist=False)
