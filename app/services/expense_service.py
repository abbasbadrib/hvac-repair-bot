"""
Service for managing expenses.
"""

from sqlalchemy.orm import Session
from app.models.expense import Expense, ExpenseType, PaidBy
from typing import Optional, List

class ExpenseService:
    """Expense CRUD operations."""

    @staticmethod
    def create(db: Session, project_id: int, expense_type: ExpenseType,
               amount: float, paid_by: PaidBy, description: Optional[str] = None) -> Expense:
        """Create a new expense."""
        expense = Expense(
            project_id=project_id,
            expense_type=expense_type,
            amount=amount,
            paid_by=paid_by,
            description=description
        )
        db.add(expense)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def get_by_id(db: Session, expense_id: int) -> Optional[Expense]:
        """Get expense by ID."""
        return db.query(Expense).filter(Expense.id == expense_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Expense]:
        """Get all expenses for a project."""
        return db.query(Expense).filter(Expense.project_id == project_id).all()

    @staticmethod
    def update(db: Session, expense_id: int, **kwargs) -> Optional[Expense]:
        """Update expense fields."""
        expense = ExpenseService.get_by_id(db, expense_id)
        if not expense:
            return None
        for key, value in kwargs.items():
            if hasattr(expense, key) and value is not None:
                setattr(expense, key, value)
        db.commit()
        db.refresh(expense)
        return expense

    @staticmethod
    def delete(db: Session, expense_id: int) -> bool:
        """Delete an expense."""
        expense = ExpenseService.get_by_id(db, expense_id)
        if not expense:
            return False
        db.delete(expense)
        db.commit()
        return True

    @staticmethod
    def get_total_expenses(db: Session, project_id: int) -> float:
        """Get total expenses for a project."""
        expenses = ExpenseService.get_by_project(db, project_id)
        return sum(e.amount for e in expenses)

    @staticmethod
    def get_expenses_by_payer(db: Session, project_id: int, paid_by: PaidBy) -> float:
        """Get total expenses paid by a specific person."""
        expenses = db.query(Expense).filter(
            Expense.project_id == project_id,
            Expense.paid_by == paid_by
        ).all()
        return sum(e.amount for e in expenses)
