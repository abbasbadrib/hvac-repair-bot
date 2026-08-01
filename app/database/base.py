"""
Database base configuration - kept for backward compatibility.
New code should use app.core.database.
"""

from app.core.database import engine, SessionLocal, Base, get_db

# Re-export for backward compatibility
__all__ = ['engine', 'SessionLocal', 'Base', 'get_db']
