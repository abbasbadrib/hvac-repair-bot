"""
Custom exceptions for the application.
"""

class AppException(Exception):
    """Base exception for the application."""
    pass

class ValidationError(AppException):
    """Raised when validation fails."""
    pass

class NotFoundError(AppException):
    """Raised when an entity is not found."""
    pass

class BusinessLogicError(AppException):
    """Raised when business logic fails."""
    pass

class DatabaseError(AppException):
    """Raised when database operation fails."""
    pass

class AuthorizationError(AppException):
    """Raised when user is not authorized."""
    pass
