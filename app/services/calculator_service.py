"""
Financial calculation service - kept for backward compatibility.
This file re-exports from the new location.
"""

from app.domain.services.calculator_service import CalculatorService, FinancialResult

# Re-export for backward compatibility
__all__ = ['CalculatorService', 'FinancialResult']
