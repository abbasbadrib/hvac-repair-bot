"""
Helper utilities.
"""

from datetime import datetime, timedelta
import re

def format_currency(amount: float) -> str:
    """
    Format amount as currency (with commas).
    
    Args:
        amount: Amount to format
        
    Returns:
        str: Formatted amount with commas
    """
    return f"{amount:,.0f}"

def parse_currency(text: str) -> float:
    """
    Parse currency string to float.
    
    Args:
        text: Currency string (e.g., "1,000,000")
        
    Returns:
        float: Parsed amount
    """
    clean_text = re.sub(r'[^\d.]', '', text)
    try:
        return float(clean_text)
    except ValueError:
        return 0.0

def get_date_range(period: str) -> tuple:
    """
    Get start and end dates for a period.
    
    Args:
        period: 'today', 'week', 'month', 'year'
        
    Returns:
        tuple: (start_date, end_date)
    """
    today = datetime.now().date()
    
    if period == 'today':
        return today, today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        return start, today
    elif period == 'month':
        start = datetime(today.year, today.month, 1).date()
        return start, today
    elif period == 'year':
        start = datetime(today.year, 1, 1).date()
        return start, today
    else:
        return today, today

def generate_project_id() -> str:
    """
    Generate a unique project ID.
    
    Returns:
        str: Project ID
    """
    now = datetime.now()
    return f"PRJ-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}"

def validate_iranian_phone(phone: str) -> bool:
    """
    Validate Iranian phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid
    """
    pattern = r'^(\+98|0|0098)?9\d{9}$'
    return bool(re.match(pattern, phone.replace(' ', '').replace('-', '')))

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        str: Truncated text
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + '...'
