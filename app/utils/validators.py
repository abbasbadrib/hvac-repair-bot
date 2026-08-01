"""
Validation utilities.
"""

import re

def validate_phone(phone: str) -> bool:
    """
    Validate Iranian phone number.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Check length (10 digits for mobile, 11 with 0)
    if len(phone) == 10:
        # 9xxxxxxxxx
        if phone[0] == '9':
            return True
    elif len(phone) == 11:
        # 09xxxxxxxxx
        if phone[0] == '0' and phone[1] == '9':
            return True
    
    return False

def validate_amount(amount: str) -> bool:
    """
    Validate amount (positive number).
    
    Args:
        amount: Amount to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        value = float(amount.replace(',', '').strip())
        return value >= 0
    except ValueError:
        return False

def validate_percentage(percentage: float) -> bool:
    """
    Validate percentage (0-100).
    
    Args:
        percentage: Percentage to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    return 0 <= percentage <= 100
