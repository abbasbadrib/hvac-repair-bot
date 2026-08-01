"""
Partner management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.part_service import PartService
from app.services.expense_service import ExpenseService
from app.services.payment_service import PaymentService
from app.services.referral_service import ReferralService
from app.domain.services.calculator_service import CalculatorService
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

class PartnerHandler(BaseHandler):
    """Handler for partner operations."""
    
    @staticmethod
    async def show_partner_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show partner information and settlement."""
        db = BaseHandler.get_db()
        try:
            # Get all completed projects
            projects = ProjectService.get_all(db)
            completed_projects = [p for p in projects if p.status == ProjectStatus.COMPLETED]
            
            if not completed_projects:
                await BaseHandler.send_message(
                    update, context,
                    "👥 <b>اطلاعات شریک</b>\n\n"
                    "❌ هیچ پروژه تکمیل شده‌ای وجود ندارد.\n\n"
                    "پس از تکمیل پروژه‌ها، اطلاعات تسویه در اینجا نمایش داده می‌شود.",
                    reply_markup=get_main_keyboard(),
                    parse_mode='HTML'
                )
                return
            
            # Calculate total shares
            total_my_share = 0
            total_partner_share = 0
            total_referral_amount = 0
            
            text = "👥 <b>گزارش تسویه با شریک</b>\n\n"
            text += f"📊 تعداد پروژه‌های تکمیل شده: {len(completed_projects)}\n\n"
            
            for project in completed_projects:
                parts = PartService.get_by_project(db, project.id)
                expenses = ExpenseService.get_by_project(db, project.id)
                payments = PaymentService.get_by_project(db, project.id)
                referral = ReferralService.get_by_project(db, project.id)
                total_payments = sum(p.amount for p in payments)
                
                financials = CalculatorService.calculate_project_financials(
                    total_amount_from_customer=project.labor_cost,
                    parts=parts,
                    expenses=expenses,
                    referral_percentage=referral.percentage if referral else 0,
                    referral_name=referral.referrer_name if referral else "",
                    total_payments=total_payments
                )
                
                total_my_share += financials.my_share
                total_partner_share += financials.partner_share
                if referral:
                    total_referral_amount += referral.amount
                
                text += f"🛠 {project.customer.name} - {project.project_type.value}\n"
                text += f"   👤 سهم من: {financials.my_share:,.0f} تومان\n"
                text += f"   👥 سهم شریک: {financials.partner_share:,.0f} تومان\n"
                if referral:
                    text += f"   🤝 حق معرفی: {referral.amount:,.0f} تومان\n"
                text += "\n"
            
            text += f"💰 <b>جمع سهم من</b>: {total_my_share:,.0f} تومان\n"
            text += f"💰 <b>جمع سهم شریک</b>: {total_partner_share:,.0f} تومان\n"
            if total_referral_amount > 0:
                text += f"🤝 <b>جمع حق معرفی</b>: {total_referral_amount:,.0f} تومان\n"
            
            text += f"\n💡 مبلغ قابل تسویه با شریک: {total_partner_share:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("📊 گزارش کامل", callback_data="partner_full_report")],
                [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
            ]
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
