"""
Report generation handlers with statistics.
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
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)

class ReportHandler(BaseHandler):
    """Handler for report and statistics operations."""
    
    @staticmethod
    async def show_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report menu."""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📊 داشبورد", callback_data="report_dashboard")],
            [InlineKeyboardButton("📈 آمار کل", callback_data="statistics")],
            [InlineKeyboardButton("📅 گزارش روزانه", callback_data="report_daily")],
            [InlineKeyboardButton("📅 گزارش هفتگی", callback_data="report_weekly")],
            [InlineKeyboardButton("📅 گزارش ماهانه", callback_data="report_monthly")],
            [InlineKeyboardButton("📅 گزارش سالانه", callback_data="report_yearly")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "📊 <b>گزارش‌گیری</b>\n\n"
            "لطفاً نوع گزارش مورد نظر را انتخاب کنید:\n\n"
            "• <b>داشبورد</b>: نمایش خلاصه آماری کلی\n"
            "• <b>آمار کل</b>: نمایش سهم من، شریک و حق معرفی از کل کارها\n"
            "• <b>گزارش روزانه/هفتگی/ماهانه/سالانه</b>: گزارش بر اساس بازه زمانی",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total statistics with filtering options."""
        query = update.callback_query
        await query.answer()
        
        # Show filter options
        keyboard = [
            [InlineKeyboardButton("📊 کل", callback_data="stats_all")],
            [InlineKeyboardButton("📅 هفتگی", callback_data="stats_weekly")],
            [InlineKeyboardButton("📅 ماهانه", callback_data="stats_monthly")],
            [InlineKeyboardButton("📅 سالانه", callback_data="stats_yearly")],
            [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
        ]
        
        await BaseHandler.edit_message(
            update, context,
            "📈 <b>آمار کل</b>\n\n"
            "لطفاً بازه زمانی مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def generate_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str = "all"):
        """Generate statistics for a specific period."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            # Determine date range
            today = date.today()
            if period == "weekly":
                start_date = today - timedelta(days=today.weekday())
            elif period == "monthly":
                start_date = date(today.year, today.month, 1)
            elif period == "yearly":
                start_date = date(today.year, 1, 1)
            else:  # all
                start_date = datetime(2000, 1, 1).date()
            
            # Get all projects in range
            all_projects = ProjectService.get_all(db)
            filtered_projects = [p for p in all_projects if p.start_date.date() >= start_date]
            
            if not filtered_projects:
                text = f"📊 <b>آمار کل</b>\n\n❌ هیچ پروژه‌ای در این بازه زمانی یافت نشد."
                keyboard = [
                    [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
                    [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
                ]
                await BaseHandler.edit_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            
            # Calculate statistics
            total_projects = len(filtered_projects)
            completed_projects = [p for p in filtered_projects if p.status == ProjectStatus.COMPLETED]
            total_completed = len(completed_projects)
            
            total_my_share = 0
            total_partner_share = 0
            total_referral_amount = 0
            total_income = 0
            total_expenses = 0
            
            for project in filtered_projects:
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
                total_income += financials.total_income
                total_expenses += financials.total_expenses
            
            period_names = {
                "all": "همه",
                "weekly": "هفتگی",
                "monthly": "ماهانه",
                "yearly": "سالانه"
            }
            
            text = (
                f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n"
                f"📋 تعداد کل پروژه‌ها: {total_projects}\n"
                f"✅ پروژه‌های تکمیل شده: {total_completed}\n"
                f"⏳ پروژه‌های در حال انجام: {total_projects - total_completed}\n\n"
                f"💰 مبلغ کل: {total_income:,.0f} تومان\n"
                f"💳 هزینه‌ها: {total_expenses:,.0f} تومان\n"
                f"📊 سود ناخالص: {total_income - total_expenses:,.0f} تومان\n\n"
                f"👤 <b>سهم من</b>: {total_my_share:,.0f} تومان\n"
                f"👥 <b>سهم شریک</b>: {total_partner_share:,.0f} تومان\n"
                f"🤝 <b>کل حق معرفی</b>: {total_referral_amount:,.0f} تومان\n\n"
                f"📊 <b>نهایی</b>:\n"
                f"💵 مبلغ قابل تسویه با شریک: {total_partner_share:,.0f} تومان\n"
                f"💵 مبلغ قابل پرداخت به معرفی‌کننده‌ها: {total_referral_amount:,.0f} تومان"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
                [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
            ]
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در تولید آمار: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show dashboard."""
        # استفاده از dashboard_handler موجود
        from app.handlers.dashboard_handler import DashboardHandler
        await DashboardHandler.show_dashboard_button(update, context)
    
    @staticmethod
    async def generate_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate daily report."""
        query = update.callback_query
        await query.answer()
        await ReportHandler.generate_statistics(update, context, "daily")
    
    @staticmethod
    async def generate_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate weekly report."""
        query = update.callback_query
        await query.answer()
        await ReportHandler.generate_statistics(update, context, "weekly")
    
    @staticmethod
    async def generate_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate monthly report."""
        query = update.callback_query
        await query.answer()
        await ReportHandler.generate_statistics(update, context, "monthly")
    
    @staticmethod
    async def generate_yearly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate yearly report."""
        query = update.callback_query
        await query.answer()
        await ReportHandler.generate_statistics(update, context, "yearly")
