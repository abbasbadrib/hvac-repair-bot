"""
Expense model and enums.
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.base import Base

class ExpenseType(str, enum.Enum):
    """Types of expenses."""
    GASOLINE = "بنزین"
    LUNCH = "ناهار"
    COFFEE = "قهوه"
    TOLL = "عوارض"
    PARKING = "پارکینگ"
    TOOLS = "ابزار"
    OTHER = "سایر"

class PaidBy(str, enum.Enum):
    """Who paid the expense."""
    ME = "من"
    PARTNER = "شریک"

class Expense(Base):
    """Expense record."""
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    expense_type = Column(Enum(ExpenseType), nullable=False)
    amount = Column(Float, nullable=False)
    paid_by = Column(Enum(PaidBy), nullable=False)
    description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="expenses")
