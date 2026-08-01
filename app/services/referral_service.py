"""
Service for managing referrals.
"""

from sqlalchemy.orm import Session
from app.models.referral import Referral
from typing import Optional

class ReferralService:
    """Referral CRUD operations."""

    @staticmethod
    def create(db: Session, project_id: int, referrer_name: str,
               percentage: float) -> Referral:
        """Create a new referral."""
        referral = Referral(
            project_id=project_id,
            referrer_name=referrer_name,
            percentage=percentage,
            amount=0.0  # Will be calculated later
        )
        db.add(referral)
        db.commit()
        db.refresh(referral)
        return referral

    @staticmethod
    def get_by_id(db: Session, referral_id: int) -> Optional[Referral]:
        """Get referral by ID."""
        return db.query(Referral).filter(Referral.id == referral_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> Optional[Referral]:
        """Get referral for a project."""
        return db.query(Referral).filter(Referral.project_id == project_id).first()

    @staticmethod
    def update(db: Session, referral_id: int, **kwargs) -> Optional[Referral]:
        """Update referral fields."""
        referral = ReferralService.get_by_id(db, referral_id)
        if not referral:
            return None
        for key, value in kwargs.items():
            if hasattr(referral, key) and value is not None:
                setattr(referral, key, value)
        db.commit()
        db.refresh(referral)
        return referral

    @staticmethod
    def delete(db: Session, referral_id: int) -> bool:
        """Delete a referral."""
        referral = ReferralService.get_by_id(db, referral_id)
        if not referral:
            return False
        db.delete(referral)
        db.commit()
        return True

    @staticmethod
    def calculate_amount(db: Session, referral_id: int, net_profit: float) -> float:
        """Calculate referral amount based on net profit."""
        referral = ReferralService.get_by_id(db, referral_id)
        if not referral:
            return 0.0
        amount = (referral.percentage / 100) * net_profit
        referral.amount = amount
        db.commit()
        return amount
