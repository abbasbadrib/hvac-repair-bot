"""
Project model and enums.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database.base import Base

class ProjectType(str, enum.Enum):
    """Type of project."""
    AIR_CONDITIONER = "کولرگازی"
    PACKAGE = "پکیج"

class ProjectStatus(str, enum.Enum):
    """Status of project."""
    IN_PROGRESS = "درحال انجام"
    COMPLETED = "پایان یافته"
    CANCELLED = "لغوشده"

class Project(Base):
    """Project information."""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    project_type = Column(Enum(ProjectType), nullable=False)
    service_type = Column(String(50), nullable=False)  # نصب، تعمیر، بازدید
    status = Column(Enum(ProjectStatus), default=ProjectStatus.IN_PROGRESS)
    description = Column(Text, nullable=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=True)
    labor_cost = Column(Float, default=0.0)  # اجرت
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="projects")
    parts = relationship("Part", back_populates="project", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="project", cascade="all, delete-orphan")
    expenses = relationship("Expense", back_populates="project", cascade="all, delete-orphan")
    referral = relationship("Referral", back_populates="project", uselist=False, cascade="all, delete-orphan")
    reminders = relationship("Reminder", back_populates="project", cascade="all, delete-orphan")
