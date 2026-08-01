"""
Financial calculation service.
"""

from dataclasses import dataclass
from typing import List, Optional
from decimal import Decimal, ROUND_HALF_UP

@dataclass
class FinancialResult:
    """Financial calculation result."""
    total_income: float
    total_parts_profit: float
    labor_cost: float
    total_expenses: float
    expenses_paid_by_me: float
    expenses_paid_by_partner: float
    gross_profit: float
    referral_percentage: float
    referral_amount: float
    net_profit: float
    my_share: float
    partner_share: float
    my_debt: float
    customer_debt: float
    referral_name: str = ""

class CalculatorService:
    """Service for financial calculations."""
    
    @staticmethod
    def calculate_project_financials(
        parts_profit: float,
        labor_cost: float,
        expenses: List,
        referral_percentage: float = 0,
        referral_name: str = "",
        total_payments: float = 0
    ) -> FinancialResult:
        """Calculate all financial metrics for a project."""
        
        # Total income
        total_income = parts_profit + labor_cost
        
        # Expenses breakdown
        total_expenses = sum(e.amount for e in expenses)
        expenses_paid_by_me = sum(e.amount for e in expenses if e.paid_by == "ME")
        expenses_paid_by_partner = sum(e.amount for e in expenses if e.paid_by == "PARTNER")
        
        # Gross profit (income - expenses)
        gross_profit = total_income - total_expenses
        
        # Referral amount (calculated from gross profit)
        referral_amount = (referral_percentage / 100) * gross_profit
        
        # Net profit (gross profit - referral)
        net_profit = gross_profit - referral_amount
        
        # Split 50/50
        base_share = net_profit / 2
        
        # Adjust for expenses paid by each partner
        my_share = base_share - expenses_paid_by_me
        partner_share = base_share - expenses_paid_by_partner
        
        # Calculate debts
        customer_debt = max(0, total_income - total_payments)
        my_debt = my_share + expenses_paid_by_me
        
        return FinancialResult(
            total_income=total_income,
            total_parts_profit=parts_profit,
            labor_cost=labor_cost,
            total_expenses=total_expenses,
            expenses_paid_by_me=expenses_paid_by_me,
            expenses_paid_by_partner=expenses_paid_by_partner,
            gross_profit=gross_profit,
            referral_percentage=referral_percentage,
            referral_amount=referral_amount,
            net_profit=net_profit,
            my_share=my_share,
            partner_share=partner_share,
            my_debt=my_debt,
            customer_debt=customer_debt,
            referral_name=referral_name
        )
