"""
Service for managing reminders.
"""

from sqlalchemy.orm import Session
from app.models.reminder import Reminder, ReminderInterval
from app.models.project import Project
from typing import Optional, List
from datetime import datetime, timedelta

class ReminderService:
    """Reminder CRUD operations."""

    @staticmethod
    def create(db: Session, project_id: int, interval: ReminderInterval,
               reminder_date: datetime) -> Reminder:
        """Create a new reminder."""
        reminder = Reminder(
            project_id=project_id,
            interval=interval,
            reminder_date=reminder_date,
            is_sent=0
        )
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return reminder

    @staticmethod
    def get_by_id(db: Session, reminder_id: int) -> Optional[Reminder]:
        """Get reminder by ID."""
        return db.query(Reminder).filter(Reminder.id == reminder_id).first()

    @staticmethod
    def get_by_project(db: Session, project_id: int) -> List[Reminder]:
        """Get all reminders for a project."""
        return db.query(Reminder).filter(Reminder.project_id == project_id).all()

    @staticmethod
    def get_pending_reminders(db: Session) -> List[Reminder]:
        """Get all pending reminders."""
        now = datetime.utcnow()
        return db.query(Reminder).filter(
            Reminder.reminder_date <= now,
            Reminder.is_sent == 0
        ).all()

    @staticmethod
    def mark_as_sent(db: Session, reminder_id: int) -> bool:
        """Mark a reminder as sent."""
        reminder = ReminderService.get_by_id(db, reminder_id)
        if not reminder:
            return False
        reminder.is_sent = 1
        db.commit()
        return True

    @staticmethod
    def calculate_reminder_date(start_date: datetime, interval: ReminderInterval) -> datetime:
        """Calculate the reminder date based on interval."""
        if interval == ReminderInterval.THREE_MONTHS:
            return start_date + timedelta(days=90)
        elif interval == ReminderInterval.SIX_MONTHS:
            return start_date + timedelta(days=180)
        elif interval == ReminderInterval.TWELVE_MONTHS:
            return start_date + timedelta(days=365)
        return start_date

    @staticmethod
    def delete(db: Session, reminder_id: int) -> bool:
        """Delete a reminder."""
        reminder = ReminderService.get_by_id(db, reminder_id)
        if not reminder:
            return False
        db.delete(reminder)
        db.commit()
        return True
