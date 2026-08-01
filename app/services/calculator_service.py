"""
Service for calculating financial metrics.
"""

from sqlalchemy.orm import Session
from app.services.part_service import PartService
from app.services.expense_service import ExpenseService
from app.services.payment_service import PaymentService
from app.services.referral_service import ReferralService
from app.models.expense import PaidBy
from typing import Dict, Any

class CalculatorService:
    """Calculate financial metrics for projects."""

    @staticmethod
    def calculate_project_financials(db: Session, project_id: int) -> Dict[str, Any]:
        """
        Calculate all financial metrics for a project.
        
        Returns:
            Dict containing:
            - total_income: جمع درآمد
            - total_parts_profit: سود قطعات
            - total_expenses: جمع هزینه‌ها
            - gross_profit: سود ناخالص
            - referral_amount: حق معرفی
            - net_profit: سود خالص
            - my_share: سهم من
            - partner_share: سهم شریک
            - my_debt: طلب من
            - customer_debt: بدهکاری مشتری
            - expenses_paid_by_me: هزینه‌های پرداخت شده توسط من
            - expenses_paid_by_partner: هزینه‌های پرداخت شده توسط شریک
        """
        # Get parts profit
        parts_profit = PartService.get_total_profit(db, project_id)
        
        # Get labor cost (اجرت)
        from app.services.project_service import ProjectService
        project = ProjectService.get_by_id(db, project_id)
        labor_cost = project.labor_cost if project else 0.0
        
        # Total income = parts profit + labor cost
        total_income = parts_profit + labor_cost
        
        # Get expenses
        expenses = ExpenseService.get_by_project(db, project_id)
        total_expenses = sum(e.amount for e in expenses)
        expenses_paid_by_me = sum(e.amount for e in expenses if e.paid_by == PaidBy.ME)
        expenses_paid_by_partner = sum(e.amount for e in expenses if e.paid_by == PaidBy.PARTNER)
        
        # Gross profit = total income - total expenses
        gross_profit = total_income - total_expenses
        
        # Get referral
        referral = ReferralService.get_by_project(db, project_id)
        referral_amount = 0.0
        if referral:
            referral_amount = (referral.percentage / 100) * gross_profit
            referral.amount = referral_amount
            db.commit()
        
        # Net profit = gross profit - referral amount
        net_profit = gross_profit - referral_amount
        
        # Split between me and partner (50/50)
        my_share = net_profit / 2
        partner_share = net_profit / 2
        
        # Adjust for expenses paid by each
        # اگر یکی از طرفین هزینه‌ای پرداخت کرده باشد، هنگام تسویه لحاظ شود
        my_share -= expenses_paid_by_me
        partner_share -= expenses_paid_by_partner
        
        # Get total payments from customer
        total_payments = PaymentService.get_total_payments(db, project_id)
        
        # Customer debt = total income - total payments
        customer_debt = total_income - total_payments
        if customer_debt < 0:
            customer_debt = 0.0
        
        # My debt (طلب من) = my_share + expenses_paid_by_me
        my_debt = my_share + expenses_paid_by_me
        
        return {
            "total_income": total_income,
            "total_parts_profit": parts_profit,
            "labor_cost": labor_cost,
            "total_expenses": total_expenses,
            "expenses_paid_by_me": expenses_paid_by_me,
            "expenses_paid_by_partner": expenses_paid_by_partner,
            "gross_profit": gross_profit,
            "referral_amount": referral_amount,
            "referral_percentage": referral.percentage if referral else 0.0,
            "referrer_name": referral.referrer_name if referral else "",
            "net_profit": net_profit,
            "my_share": my_share,
            "partner_share": partner_share,
            "my_debt": my_debt,
            "customer_debt": customer_debt,
            "total_payments": total_payments
        }
