"""
Referral model.
"""

from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database.base import Base

class Referral(Base):
    """Referral commission."""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    referrer_name = Column(String(100), nullable=False)
    percentage = Column(Float, nullable=False)  # 0-100
    amount = Column(Float, default=0.0)  # محاسبه می‌شود
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="referral")
