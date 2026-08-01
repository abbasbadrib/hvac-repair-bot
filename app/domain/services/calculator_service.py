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
    general_expenses: float  # هزینه‌های عمومی
    project_expenses: float  # هزینه‌های مستقیم پروژه
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
        
        # درآمد کل = مبلغ دریافتی از مشتری
        total_income = total_amount_from_customer
        
        # محاسبه قیمت فروش کل قطعات
        total_parts_selling_price = sum(p.selling_price * p.quantity for p in parts)
        
        # محاسبه سود قطعات
        total_parts_profit = sum((p.selling_price - p.purchase_price) * p.quantity for p in parts)
        
        # اجرت = درآمد کل - قیمت فروش قطعات
        labor_cost = total_income - total_parts_selling_price
        
        # تفکیک هزینه‌ها
        project_expenses = sum(e.amount for e in expenses if not e.is_general)
        general_expenses = sum(e.amount for e in expenses if e.is_general)
        total_expenses = project_expenses + general_expenses
        
        # هزینه‌های پرداخت شده توسط هر نفر
        expenses_paid_by_me = sum(e.amount for e in expenses if e.paid_by == "ME")
        expenses_paid_by_partner = sum(e.amount for e in expenses if e.paid_by == "PARTNER")
        
        # سود ناخالص = سود قطعه + اجرت - هزینه‌های مستقیم پروژه
        gross_profit = total_parts_profit + labor_cost - project_expenses
        
        # حق معرفی = سود ناخالص × درصد
        referral_amount = gross_profit * (referral_percentage / 100)
        
        # سود خالص = سود ناخالص - حق معرفی
        net_profit = gross_profit - referral_amount
        
        # تقسیم سود ۵۰/۵۰
        base_share = net_profit / 2
        
        # تعدیل با هزینه‌های پرداخت شده توسط هر نفر (شامل هزینه‌های عمومی)
        my_share = base_share - expenses_paid_by_me
        partner_share = base_share - expenses_paid_by_partner
        
        # محاسبه بدهی‌ها
        customer_debt = max(0, total_income - total_payments)
        my_debt = my_share + expenses_paid_by_me
        
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
