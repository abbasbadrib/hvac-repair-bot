"""
Payment model and enums.
"""

from sqlalchemy import Column, Integer, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.base import Base

class PaymentMethod(str, enum.Enum):
    """Payment methods."""
    CASH = "نقد"
    CARD = "کارت"
    CARD_TO_CARD = "کارت به کارت"
    DEPOSIT = "بیعانه"
    SETTLEMENT = "تسویه"

class Payment(Base):
    """Payment record."""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="payments")
