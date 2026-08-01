"""
Reminder model.
"""

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Enum, String
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.base import Base

class ReminderInterval(str, enum.Enum):
    """Reminder intervals."""
    THREE_MONTHS = "۳ ماه"
    SIX_MONTHS = "۶ ماه"
    TWELVE_MONTHS = "۱۲ ماه"

class Reminder(Base):
    """Service reminders."""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    interval = Column(Enum(ReminderInterval), nullable=False)
    reminder_date = Column(DateTime, nullable=False)
    is_sent = Column(Integer, default=0)  # 0=not sent, 1=sent
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="reminders")
