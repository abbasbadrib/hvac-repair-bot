"""
Report generation handlers with detailed statistics.
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
from app.models.expense import PaidBy, ExpenseType
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
            [InlineKeyboardButton("💰 گزارش درآمد", callback_data="report_income")],
            [InlineKeyboardButton("💳 گزارش هزینه", callback_data="report_expense")],
            [InlineKeyboardButton("📅 گزارش روزانه", callback_data="report_daily")],
            [InlineKeyboardButton("📅 گزارش هفتگی", callback_data="report_weekly")],
            [InlineKeyboardButton("📅 گزارش ماهانه", callback_data="report_monthly")],
            [InlineKeyboardButton("📅 گزارش سالانه", callback_data="report_yearly")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "📊 <b>گزارش‌گیری</b>\n\n"
            "لطفاً نوع گزارش مورد نظر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show total statistics with filtering options."""
        query = update.callback_query
        await query.answer()
        
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
        """Generate detailed statistics for a specific period."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            today = date.today()
            if period == "weekly":
                start_date = today - timedelta(days=today.weekday())
            elif period == "monthly":
                start_date = date(today.year, today.month, 1)
            elif period == "yearly":
                start_date = date(today.year, 1, 1)
            else:
                start_date = datetime(2000, 1, 1).date()
            
            all_projects = ProjectService.get_all(db)
            filtered_projects = [p for p in all_projects if p.start_date.date() >= start_date]
            
            period_names = {"all": "همه", "weekly": "هفتگی", "monthly": "ماهانه", "yearly": "سالانه"}
            
            general_expenses = ExpenseService.get_general_expenses(db)
            total_general_expenses = sum(e.amount for e in general_expenses if e.created_at.date() >= start_date)
            
            general_by_type = {}
            for exp in general_expenses:
                if exp.created_at.date() >= start_date:
                    general_by_type[exp.expense_type.value] = general_by_type.get(exp.expense_type.value, 0) + exp.amount
            
            if not filtered_projects and total_general_expenses == 0:
                text = f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n❌ هیچ داده‌ای در این بازه زمانی یافت نشد."
                keyboard = [
                    [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
                    [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
                ]
                await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
                return
            
            total_projects = len(filtered_projects)
            completed_projects = [p for p in filtered_projects if p.status == ProjectStatus.COMPLETED]
            total_completed = len(completed_projects)
            
            total_my_share = 0
            total_partner_share = 0
            total_referral_amount = 0
            total_income = 0
            total_project_expenses = 0
            total_expenses_by_payer = {"ME": 0, "PARTNER": 0, "JOINT": 0}
            total_expenses_by_type = {}
            total_parts_profit = 0
            total_labor = 0
            
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
                total_project_expenses += financials.project_expenses
                total_parts_profit += financials.total_parts_profit
                total_labor += financials.labor_cost
                
                for exp in expenses:
                    if not exp.is_general:
                        total_expenses_by_payer[exp.paid_by.value] = total_expenses_by_payer.get(exp.paid_by.value, 0) + exp.amount
                        total_expenses_by_type[exp.expense_type.value] = total_expenses_by_type.get(exp.expense_type.value, 0) + exp.amount
            
            text = (
                f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n"
                f"📋 تعداد کل پروژه‌ها: {total_projects}\n"
                f"✅ پروژه‌های تکمیل شده: {total_completed}\n"
                f"⏳ پروژه‌های در حال انجام: {total_projects - total_completed}\n\n"
                f"💰 <b>درآمدها</b>:\n"
                f"   مبلغ کل: {total_income:,.0f} تومان\n"
                f"   سود قطعات: {total_parts_profit:,.0f} تومان\n"
                f"   اجرت: {total_labor:,.0f} تومان\n\n"
                f"💳 <b>هزینه‌ها</b>:\n"
                f"   هزینه‌های مستقیم پروژه‌ها: {total_project_expenses:,.0f} تومان\n"
                f"   هزینه‌های عمومی: {total_general_expenses:,.0f} تومان\n"
                f"   جمع کل هزینه‌ها: {total_project_expenses + total_general_expenses:,.0f} تومان\n\n"
            )
            
            if total_expenses_by_type:
                text += "📋 <b>تفکیک هزینه‌ها بر اساس نوع</b>:\n"
                for exp_type, amount in sorted(total_expenses_by_type.items(), key=lambda x: -x[1]):
                    text += f"   {exp_type}: {amount:,.0f} تومان\n"
                text += "\n"
            
            if any(total_expenses_by_payer.values()):
                text += "👤 <b>تفکیک هزینه‌ها بر اساس پرداخت‌کننده</b>:\n"
                for payer, amount in total_expenses_by_payer.items():
                    if amount > 0:
                        text += f"   {payer}: {amount:,.0f} تومان\n"
                text += "\n"
            
            if general_by_type:
                text += "💳 <b>تفکیک هزینه‌های عمومی</b>:\n"
                for exp_type, amount in sorted(general_by_type.items(), key=lambda x: -x[1]):
                    text += f"   {exp_type}: {amount:,.0f} تومان\n"
                text += "\n"
            
            text += (
                f"👤 <b>سهم نهایی</b>:\n"
                f"   سهم من: {total_my_share:,.0f} تومان\n"
                f"   سهم شریک: {total_partner_share:,.0f} تومان\n"
                f"   🤝 کل حق معرفی: {total_referral_amount:,.0f} تومان\n\n"
                f"📊 <b>نهایی</b>:\n"
                f"💵 مبلغ قابل تسویه با شریک: {total_partner_share:,.0f} تومان\n"
                f"💵 مبلغ قابل پرداخت به معرفی‌کننده‌ها: {total_referral_amount:,.0f} تومان"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
                [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error generating statistics: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا در تولید آمار: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show dashboard."""
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
    
    @staticmethod
    async def income_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate income report."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.get_all(db)
            if not projects:
                await BaseHandler.edit_message(
                    update, context,
                    "💰 <b>گزارش درآمد</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="report_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "💰 <b>گزارش درآمد</b>\n\n"
            total_income = 0
            total_parts_profit = 0
            total_labor = 0
            
            for project in projects:
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
                
                status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
                text += f"{status_emoji} {project.customer.name} - {project.project_type.value}\n"
                text += f"   مبلغ کل: {financials.total_income:,.0f} تومان\n"
                text += f"   سود قطعات: {financials.total_parts_profit:,.0f} تومان\n"
                text += f"   اجرت: {financials.labor_cost:,.0f} تومان\n"
                text += f"   سود خالص: {financials.net_profit:,.0f} تومان\n\n"
                
                total_income += financials.total_income
                total_parts_profit += financials.total_parts_profit
                total_labor += financials.labor_cost
            
            text += f"📊 <b>جمع کل</b>:\n"
            text += f"💰 مبلغ کل: {total_income:,.0f} تومان\n"
            text += f"🔩 سود قطعات: {total_parts_profit:,.0f} تومان\n"
            text += f"🛠 اجرت: {total_labor:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="report_menu")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error generating income report: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    async def expense_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate expense report."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            all_expenses = db.query(ExpenseService.model).all()
            
            if not all_expenses:
                await BaseHandler.edit_message(
                    update, context,
                    "💳 <b>گزارش هزینه</b>\n\n❌ هیچ هزینه‌ای ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="report_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "💳 <b>گزارش هزینه</b>\n\n"
            
            project_expenses = [e for e in all_expenses if not e.is_general]
            general_expenses = [e for e in all_expenses if e.is_general]
            
            if project_expenses:
                text += "📋 <b>هزینه‌های پروژه</b>:\n"
                for exp in project_expenses[:20]:
                    paid_by_emoji = "👤" if exp.paid_by == PaidBy.ME else "👥" if exp.paid_by == PaidBy.PARTNER else "🤝"
                    text += f"   • {exp.expense_type.value}: {exp.amount:,.0f} تومان ({paid_by_emoji} {exp.paid_by.value})\n"
                if len(project_expenses) > 20:
                    text += f"   ... و {len(project_expenses) - 20} مورد دیگر\n"
                text += f"   💰 جمع: {sum(e.amount for e in project_expenses):,.0f} تومان\n\n"
            
            if general_expenses:
                text += "💳 <b>هزینه‌های عمومی</b>:\n"
                for exp in general_expenses[:20]:
                    paid_by_emoji = "👤" if exp.paid_by == PaidBy.ME else "👥" if exp.paid_by == PaidBy.PARTNER else "🤝"
                    text += f"   • {exp.expense_type.value}: {exp.amount:,.0f} تومان ({paid_by_emoji} {exp.paid_by.value})\n"
                if len(general_expenses) > 20:
                    text += f"   ... و {len(general_expenses) - 20} مورد دیگر\n"
                text += f"   💰 جمع: {sum(e.amount for e in general_expenses):,.0f} تومان\n\n"
            
            total_all = sum(e.amount for e in all_expenses)
            text += f"💰 <b>جمع کل هزینه‌ها</b>: {total_all:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="report_menu")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error generating expense report: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
