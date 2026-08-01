"""
Service for managing customers.
"""

from sqlalchemy.orm import Session
from app.models.customer import Customer
from typing import Optional, List

class CustomerService:
    """Customer CRUD operations."""

    @staticmethod
    def create(db: Session, name: str, phone: str, address: Optional[str] = None,
               latitude: Optional[float] = None, longitude: Optional[float] = None,
               description: Optional[str] = None) -> Customer:
        """Create a new customer."""
        customer = Customer(
            name=name,
            phone=phone,
            address=address,
            latitude=latitude,
            longitude=longitude,
            description=description
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def get_by_id(db: Session, customer_id: int) -> Optional[Customer]:
        """Get customer by ID."""
        return db.query(Customer).filter(Customer.id == customer_id).first()

    @staticmethod
    def get_by_phone(db: Session, phone: str) -> Optional[Customer]:
        """Get customer by phone number."""
        return db.query(Customer).filter(Customer.phone == phone).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Get all customers with pagination."""
        return db.query(Customer).offset(skip).limit(limit).all()

    @staticmethod
    def search(db: Session, query: str) -> List[Customer]:
        """Search customers by name or phone."""
        return db.query(Customer).filter(
            (Customer.name.contains(query)) | (Customer.phone.contains(query))
        ).all()

    @staticmethod
    def update(db: Session, customer_id: int, **kwargs) -> Optional[Customer]:
        """Update customer fields."""
        customer = CustomerService.get_by_id(db, customer_id)
        if not customer:
            return None
        for key, value in kwargs.items():
            if hasattr(customer, key) and value is not None:
                setattr(customer, key, value)
        db.commit()
        db.refresh(customer)
        return customer

    @staticmethod
    def delete(db: Session, customer_id: int) -> bool:
        """Delete a customer."""
        customer = CustomerService.get_by_id(db, customer_id)
        if not customer:
            return False
        db.delete(customer)
        db.commit()
        return True
