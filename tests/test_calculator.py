"""
Unit tests for calculator service.
"""

import pytest
from app.domain.services.calculator_service import CalculatorService

class TestCalculatorService:
    """Test calculator service."""
    
    def test_calculate_project_financials_basic(self):
        """Test basic financial calculation."""
        # Arrange
        parts_profit = 100000
        labor_cost = 50000
        expenses = []
        total_payments = 0
        
        # Act
        result = CalculatorService.calculate_project_financials(
            parts_profit=parts_profit,
            labor_cost=labor_cost,
            expenses=expenses,
            total_payments=total_payments
        )
        
        # Assert
        assert result.total_income == 150000
        assert result.gross_profit == 150000
        assert result.net_profit == 150000
        assert result.my_share == 75000
        assert result.partner_share == 75000
    
    def test_calculate_with_expenses(self):
        """Test calculation with expenses."""
        # Arrange
        parts_profit = 100000
        labor_cost = 50000
        expenses = [
            type('Expense', (), {'amount': 20000, 'paid_by': 'ME'}),
            type('Expense', (), {'amount': 10000, 'paid_by': 'PARTNER'})
        ]
        total_payments = 0
        
        # Act
        result = CalculatorService.calculate_project_financials(
            parts_profit=parts_profit,
            labor_cost=labor_cost,
            expenses=expenses,
            total_payments=total_payments
        )
        
        # Assert
        assert result.total_income == 150000
        assert result.total_expenses == 30000
        assert result.gross_profit == 120000
        assert result.my_share == 60000 - 20000  # 50% - expenses_paid_by_me
        assert result.partner_share == 60000 - 10000  # 50% - expenses_paid_by_partner
    
    def test_calculate_with_referral(self):
        """Test calculation with referral."""
        # Arrange
        parts_profit = 100000
        labor_cost = 50000
        expenses = []
        referral_percentage = 20
        total_payments = 0
        
        # Act
        result = CalculatorService.calculate_project_financials(
            parts_profit=parts_profit,
            labor_cost=labor_cost,
            expenses=expenses,
            referral_percentage=referral_percentage,
            total_payments=total_payments
        )
        
        # Assert
        assert result.total_income == 150000
        assert result.gross_profit == 150000
        assert result.referral_amount == 30000  # 20% of 150000
        assert result.net_profit == 120000
        assert result.my_share == 60000
        assert result.partner_share == 60000
    
    def test_calculate_with_customer_debt(self):
        """Test calculation with customer debt."""
        # Arrange
        parts_profit = 100000
        labor_cost = 50000
        expenses = []
        total_payments = 80000
        
        # Act
        result = CalculatorService.calculate_project_financials(
            parts_profit=parts_profit,
            labor_cost=labor_cost,
            expenses=expenses,
            total_payments=total_payments
        )
        
        # Assert
        assert result.customer_debt == 70000  # 150000 - 80000
        assert result.my_debt == 75000
