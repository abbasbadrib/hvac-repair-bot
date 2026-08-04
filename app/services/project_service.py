"""
Service for managing projects.
"""

from sqlalchemy.orm import Session
from app.models.project import Project, ProjectType, ProjectStatus
from app.models.customer import Customer
from typing import Optional, List
from datetime import datetime, date

class ProjectService:
    """Project CRUD operations."""

    # مدل SQLAlchemy برای دسترسی مستقیم
    model = Project

    @staticmethod
    def create(db: Session, customer_id: int, project_type: ProjectType,
               service_type: str, description: Optional[str] = None,
               labor_cost: float = 0.0) -> Project:
        """Create a new project."""
        project = Project(
            customer_id=customer_id,
            project_type=project_type,
            service_type=service_type,
            description=description,
            labor_cost=labor_cost,
            status=ProjectStatus.IN_PROGRESS
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def get_by_id(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def get_by_customer(db: Session, customer_id: int) -> List[Project]:
        """Get all projects for a customer."""
        return db.query(Project).filter(Project.customer_id == customer_id).all()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination."""
        return db.query(Project).offset(skip).limit(limit).all()

    @staticmethod
    def get_by_status(db: Session, status: ProjectStatus) -> List[Project]:
        """Get projects by status."""
        return db.query(Project).filter(Project.status == status).all()

    @staticmethod
    def search(db: Session, query: str) -> List[Project]:
        """Search projects by customer name or phone or description."""
        return db.query(Project).join(Customer).filter(
            (Customer.name.contains(query)) |
            (Customer.phone.contains(query)) |
            (Project.description.contains(query))
        ).all()

    @staticmethod
    def search_by_date_range(db: Session, start_date: date, end_date: date) -> List[Project]:
        """Search projects by date range."""
        return db.query(Project).filter(
            Project.start_date >= start_date,
            Project.start_date <= end_date
        ).all()

    @staticmethod
    def update(db: Session, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields."""
        project = ProjectService.get_by_id(db, project_id)
        if not project:
            return None
        for key, value in kwargs.items():
            if hasattr(project, key) and value is not None:
                setattr(project, key, value)
        if 'status' in kwargs and kwargs['status'] == ProjectStatus.COMPLETED:
            project.end_date = datetime.utcnow()
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete(db: Session, project_id: int) -> bool:
        """Delete a project."""
        project = ProjectService.get_by_id(db, project_id)
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def get_open_projects(db: Session) -> List[Project]:
        """Get all open projects (in progress)."""
        return db.query(Project).filter(
            Project.status == ProjectStatus.IN_PROGRESS
        ).all()
