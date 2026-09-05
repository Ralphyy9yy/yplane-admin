from sqlalchemy import Column, Integer, String, Enum, DateTime, JSON
from datetime import datetime
from app.core.database import Base
import enum

class QueueStatus(str, enum.Enum):
    waiting = "waiting"
    processing = "processing"
    confirmed = "confirmed"
    rejected = "rejected"
    cancelled = "cancelled"
    failed = "failed"

class ProcessingQueue(Base):
    __tablename__ = "processing_queue"

    id = Column(Integer, primary_key=True, index=True)
    request_type = Column(String(50), nullable=False, default="booking")
    booking_id = Column(Integer, nullable=True)
    user_id = Column(Integer, nullable=True)
    user_name = Column(String(255), nullable=True)
    schedule_id = Column(Integer, nullable=True)
    schedule_route = Column(String(255), nullable=True)
    seat_id = Column(Integer, nullable=True)
    seat_number = Column(String(20), nullable=True)
    payload = Column(JSON, nullable=True)
    queue_position = Column(Integer, nullable=True)
    status = Column(Enum(QueueStatus), default=QueueStatus.waiting, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    result = Column(String(255), nullable=True)
    error_message = Column(String(500), nullable=True)
