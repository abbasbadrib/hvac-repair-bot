"""
Service for managing parts.
"""

from sqlalchemy.orm import Session
from app.models.part import Part
from typing import Optional, List

class PartService:
    """Part CRUD operations."""

    @staticmethod
    def create(db: Session, project_id: int, name: str, quantity: int,
               purchase_price: float, selling_price: float) -> Part:
        """Create a new part."""
        profit = (selling_price - purchase_price) * quantity
        part = Part(
            project_id=project_id,
            name=name,
            quantity=quantity,
            purchase_price=purchase_price,
            selling_price=selling_price,
            profit=profit
        )
        db.add(part)
        db.commit()
        db.refresh(part)
        return part

    @staticmethod
    def get_by_id(db: Session, part_id: int) -> Optional[Part]:
        """Get part by ID."""
        return db.query(Part).filter(Part.id == part_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Part]:
        """Get all parts for a project."""
        return db.query(Part).filter(Part.project_id == project_id).all()

    @staticmethod
    def update(db: Session, part_id: int, **kwargs) -> Optional[Part]:
        """Update part fields."""
        part = PartService.get_by_id(db, part_id)
        if not part:
            return None
        for key, value in kwargs.items():
            if hasattr(part, key) and value is not None:
                setattr(part, key, value)
        # Recalculate profit
        part.profit = (part.selling_price - part.purchase_price) * part.quantity
        db.commit()
        db.refresh(part)
        return part

    @staticmethod
    def delete(db: Session, part_id: int) -> bool:
        """Delete a part."""
        part = PartService.get_by_id(db, part_id)
        if not part:
            return False
        db.delete(part)
        db.commit()
        return True

    @staticmethod
    def get_total_profit(db: Session, project_id: int) -> float:
        """Get total parts profit for a project."""
        parts = PartService.get_by_project(db, project_id)
        return sum(p.profit for p in parts)
