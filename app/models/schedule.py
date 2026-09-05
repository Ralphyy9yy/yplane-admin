from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(Integer, primary_key=True, index=True)
    route = Column(String(255), nullable=False)
    origin = Column(String(255), nullable=True)
    destination = Column(String(255), nullable=True)
    departure_time = Column(DateTime, nullable=False)
    arrival_time = Column(DateTime, nullable=False)
    price = Column(Float, nullable=False, default=0.0)
    total_seats = Column(Integer, nullable=False, default=50)
    available_seats = Column(Integer, nullable=False, default=50)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    seats = relationship("Seat", back_populates="schedule", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="schedule")
    creator = relationship("User", foreign_keys=[created_by])
