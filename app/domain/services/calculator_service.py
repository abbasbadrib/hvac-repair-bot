"""
Financial calculation service.
"""

from dataclasses import dataclass
from typing import List, Optional

@dataclass
class FinancialResult:
    """Financial calculation result."""
    total_income: float
    total_parts_profit: float
    total_parts_selling_price: float
    labor_cost: float
    total_expenses: float
    general_expenses: float
    project_expenses: float
    expenses_paid_by_me: float
    expenses_paid_by_partner: float
    expenses_paid_joint: float
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
        total_amount_from_customer: float,
        parts: List = None,
        expenses: List = None,
        referral_percentage: float = 0,
        referral_name: str = "",
        total_payments: float = 0
    ) -> FinancialResult:
        """
        Calculate all financial metrics for a project.
        """
        if parts is None:
            parts = []
        if expenses is None:
            expenses = []
        
        total_income = total_amount_from_customer
        total_parts_selling_price = sum(p.selling_price * p.quantity for p in parts)
        total_parts_profit = sum((p.selling_price - p.purchase_price) * p.quantity for p in parts)
        labor_cost = total_income - total_parts_selling_price
        
        project_expenses = sum(e.amount for e in expenses if not e.is_general)
        general_expenses = sum(e.amount for e in expenses if e.is_general)
        total_expenses = project_expenses + general_expenses
        
        expenses_paid_by_me = sum(e.amount for e in expenses if e.paid_by == "ME")
        expenses_paid_by_partner = sum(e.amount for e in expenses if e.paid_by == "PARTNER")
        expenses_paid_joint = sum(e.amount for e in expenses if e.paid_by == "JOINT")
        
        gross_profit = total_parts_profit + labor_cost - project_expenses
        referral_amount = gross_profit * (referral_percentage / 100)
        net_profit = gross_profit - referral_amount
        
        base_share = net_profit / 2
        my_adjustment = expenses_paid_by_me + (expenses_paid_joint / 2)
        partner_adjustment = expenses_paid_by_partner + (expenses_paid_joint / 2)
        
        my_share = base_share - my_adjustment
        partner_share = base_share - partner_adjustment
        
        customer_debt = max(0, total_income - total_payments)
        my_debt = my_share + my_adjustment
        
        return FinancialResult(
            total_income=total_income,
            total_parts_profit=total_parts_profit,
            total_parts_selling_price=total_parts_selling_price,
            labor_cost=labor_cost,
            total_expenses=total_expenses,
            general_expenses=general_expenses,
            project_expenses=project_expenses,
            expenses_paid_by_me=expenses_paid_by_me,
            expenses_paid_by_partner=expenses_paid_by_partner,
            expenses_paid_joint=expenses_paid_joint,
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
