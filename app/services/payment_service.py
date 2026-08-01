"""
Service for managing payments.
"""

from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentMethod
from typing import Optional, List

class PaymentService:
    """Payment CRUD operations."""

    @staticmethod
    def create(db: Session, project_id: int, amount: float,
               method: PaymentMethod, description: Optional[str] = None) -> Payment:
        """Create a new payment."""
        payment = Payment(
            project_id=project_id,
            amount=amount,
            method=method,
            description=description
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_by_id(db: Session, payment_id: int) -> Optional[Payment]:
        """Get payment by ID."""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Payment]:
        """Get all payments for a project."""
        return db.query(Payment).filter(Payment.project_id == project_id).all()

    @staticmethod
    def get_total_payments(db: Session, project_id: int) -> float:
        """Get total payments for a project."""
        payments = PaymentService.get_by_project(db, project_id)
        return sum(p.amount for p in payments)

    @staticmethod
    def update(db: Session, payment_id: int, **kwargs) -> Optional[Payment]:
        """Update payment fields."""
        payment = PaymentService.get_by_id(db, payment_id)
        if not payment:
            return None
        for key, value in kwargs.items():
            if hasattr(payment, key) and value is not None:
                setattr(payment, key, value)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def delete(db: Session, payment_id: int) -> bool:
        """Delete a payment."""
        payment = PaymentService.get_by_id(db, payment_id)
        if not payment:
            return False
        db.delete(payment)
        db.commit()
        return True
