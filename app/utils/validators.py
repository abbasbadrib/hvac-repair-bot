"""
Input validators.
"""

import re
from typing import Optional
from app.core.exceptions import ValidationError

class Validators:
    """Collection of validation methods."""
    
    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate Iranian phone number."""
        # Remove spaces and dashes
        phone = re.sub(r'[\s\-]', '', phone)
        
        # Check if it's a valid Iranian phone number
        if not re.match(r'^(\+98|0|0098)?9\d{9}$', phone):
            raise ValidationError("شماره تلفن نامعتبر است. فرمت صحیح: 09123456789")
        
        # Normalize to 0XXXXXXXXX format
        if phone.startswith('+98'):
            phone = '0' + phone[3:]
        elif phone.startswith('0098'):
            phone = '0' + phone[4:]
        
        return phone
    
    @staticmethod
    def validate_amount(amount: float) -> float:
        """Validate amount is positive."""
        if amount < 0:
            raise ValidationError("مبلغ نمی‌تواند منفی باشد")
        return amount
    
    @staticmethod
    def validate_percentage(percentage: float) -> float:
        """Validate percentage is between 0 and 100."""
        if not 0 <= percentage <= 100:
            raise ValidationError("درصد باید بین 0 تا 100 باشد")
        return percentage
    
    @staticmethod
    def validate_text(text: str, min_len: int = 1, max_len: int = 200) -> str:
        """Validate text length."""
        if not text or len(text.strip()) < min_len:
            raise ValidationError(f"متن باید حداقل {min_len} کاراکتر باشد")
        if len(text) > max_len:
            raise ValidationError(f"متن نمی‌تواند بیشتر از {max_len} کاراکتر باشد")
        return text.strip()
    
    @staticmethod
    def validate_date(date_str: str) -> str:
        """Validate date format YYYY-MM-DD."""
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
            raise ValidationError("فرمت تاریخ نامعتبر است. فرمت صحیح: YYYY-MM-DD")
        return date_str
