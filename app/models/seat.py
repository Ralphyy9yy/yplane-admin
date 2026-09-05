from sqlalchemy import Column, Integer, String, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class SeatStatus(str, enum.Enum):
    available = "available"
    reserved = "reserved"
    booked = "booked"

class Seat(Base):
    __tablename__ = "seats"
    __table_args__ = (UniqueConstraint("schedule_id", "seat_number", name="uq_schedule_seat"),)

    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False)
    seat_number = Column(String(20), nullable=False)
    status = Column(Enum(SeatStatus), default=SeatStatus.available, nullable=False)

    schedule = relationship("Schedule", back_populates="seats")
    bookings = relationship("Booking", back_populates="seat")
