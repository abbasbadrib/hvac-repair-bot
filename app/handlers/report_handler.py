"""
Report generation handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.report_service import ReportService
from app.services.project_service import ProjectService
from datetime import datetime, timedelta, date
import logging

logger = logging.getLogger(__name__)

# Conversation states
(REPORT_DATE_RANGE, REPORT_TYPE) = range(2)

class ReportHandler(BaseHandler):
    """Handler for report operations."""
    
    @staticmethod
    async def show_report_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show report menu."""
        query = update.callback_query
        if query:
            await query.answer()
        
        keyboard = [
            [InlineKeyboardButton("📊 داشبورد", callback_data="report_dashboard")],
            [InlineKeyboardButton("📅 گزارش روزانه", callback_data="report_daily")],
            [InlineKeyboardButton("📅 گزارش هفتگی", callback_data="report_weekly")],
            [InlineKeyboardButton("📅 گزارش ماهانه", callback_data="report_monthly")],
            [InlineKeyboardButton("📅 گزارش سالانه", callback_data="report_yearly")],
            [InlineKeyboardButton("📊 گزارش دوره دلخواه", callback_data="report_custom")],
            [InlineKeyboardButton("📄 گزارش PDF", callback_data="report_pdf")],
            [InlineKeyboardButton("📊 گزارش Excel", callback_data="report_excel")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "📊 <b>گزارش‌گیری</b>\n\n"
            "لطفاً نوع گزارش مورد نظر را انتخاب کنید:\n\n"
            "• <b>داشبورد</b>: نمایش خلاصه آماری کلی\n"
            "• <b>گزارش روزانه/هفتگی/ماهانه/سالانه</b>: گزارش بر اساس بازه زمانی\n"
            "• <b>گزارش دوره دلخواه</b>: انتخاب تاریخ شروع و پایان\n"
            "• <b>گزارش PDF</b>: خروجی PDF از گزارش\n"
            "• <b>گزارش Excel</b>: خروجی Excel از گزارش",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def show_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show dashboard."""
        query = update.callback_query
        if query:
            await query.answer()
        
        db = BaseHandler.get_db()
        try:
            dashboard_data = ReportService.get_dashboard_data(db)
            
            text = (
                "📊 <b>داشبورد مدیریتی</b>\n\n"
                f"🛠 <b>پروژه‌های باز</b>: {dashboard_data['open_projects_count']}\n"
                f"💰 <b>درآمد امروز</b>: {dashboard_data['today_income']:,.0f} تومان\n"
                f"📈 <b>درآمد این ماه</b>: {dashboard_data['month_income']:,.0f} تومان\n"
                f"📊 <b>سود این ماه</b>: {dashboard_data['month_profit']:,.0f} تومان\n\n"
            )
            
            if dashboard_data['debtors']:
                text += "💰 <b>بدهکاران</b>:\n"
                for debtor in dashboard_data['debtors'][:5]:
                    text += f"• {debtor['customer_name']}: {debtor['amount']:,.0f} تومان\n"
                if len(dashboard_data['debtors']) > 5:
                    text += f"... و {len(dashboard_data['debtors']) - 5} نفر دیگر\n"
            else:
                text += "✅ هیچ بدهکاری وجود ندارد."
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="report_dashboard")],
                [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
            ]
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def generate_daily_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate daily report."""
        query = update.callback_query
        if query:
            await query.answer()
        
        today = date.today()
        await ReportHandler.generate_report_by_date(update, context, today, today)
    
    @staticmethod
    async def generate_weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate weekly report."""
        query = update.callback_query
        if query:
            await query.answer()
        
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        await ReportHandler.generate_report_by_date(update, context, start_of_week, today)
    
    @staticmethod
    async def generate_monthly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate monthly report."""
        query = update.callback_query
        if query:
            await query.answer()
        
        today = date.today()
        start_of_month = date(today.year, today.month, 1)
        
        await ReportHandler.generate_report_by_date(update, context, start_of_month, today)
    
    @staticmethod
    async def generate_yearly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate yearly report."""
        query = update.callback_query
        if query:
            await query.answer()
        
        today = date.today()
        start_of_year = date(today.year, 1, 1)
        
        await ReportHandler.generate_report_by_date(update, context, start_of_year, today)
    
    @staticmethod
    async def generate_report_by_date(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                     start_date: date, end_date: date):
        """Generate report for a date range."""
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.search_by_date_range(db, start_date, end_date)
            
            if not projects:
                text = f"📊 <b>گزارش از {start_date} تا {end_date}</b>\n\n"
                text += "❌ هیچ پروژه‌ای در این بازه زمانی یافت نشد."
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            total_income = 0
            total_profit = 0
            total_expenses = 0
            total_parts_profit = 0
            
            for project in projects:
                from app.services.calculator_service import CalculatorService
                financials = CalculatorService.calculate_project_financials(db, project.id)
                total_income += financials['total_income']
                total_profit += financials['net_profit']
                total_expenses += financials['total_expenses']
                total_parts_profit += financials['total_parts_profit']
            
            text = (
                f"📊 <b>گزارش از {start_date} تا {end_date}</b>\n\n"
                f"📊 <b>تعداد پروژه‌ها</b>: {len(projects)}\n"
                f"💰 <b>درآمد کل</b>: {total_income:,.0f} تومان\n"
                f"🔩 <b>سود قطعات</b>: {total_parts_profit:,.0f} تومان\n"
                f"💳 <b>هزینه‌های کل</b>: {total_expenses:,.0f} تومان\n"
                f"📈 <b>سود خالص</b>: {total_profit:,.0f} تومان\n"
                f"📊 <b>میانگین سود هر پروژه</b>: {total_profit/len(projects):,.0f} تومان"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("📄 PDF", callback_data=f"report_pdf_{start_date}_{end_date}"),
                    InlineKeyboardButton("📊 Excel", callback_data=f"report_excel_{start_date}_{end_date}")
                ],
                [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
            ]
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def generate_pdf_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate PDF report."""
        query = update.callback_query
        if query:
            await query.answer("📄 در حال تولید PDF...")
        
        # Parse date range from callback or use today
        parts = query.data.split('_')
        if len(parts) >= 3:
            start_date = datetime.strptime(parts[2], '%Y-%m-%d').date()
            end_date = datetime.strptime(parts[3], '%Y-%m-%d').date()
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        
        db = BaseHandler.get_db()
        try:
            pdf_bytes = ReportService.generate_pdf_report(db, start_date, end_date)
            
            # Send PDF as document
            await update.callback_query.message.reply_document(
                document=pdf_bytes,
                filename=f"report_{start_date}_{end_date}.pdf",
                caption=f"📄 گزارش از {start_date} تا {end_date}"
            )
            
            logger.info(f"PDF report generated for {start_date} to {end_date}")
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در تولید PDF: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    async def generate_excel_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate Excel report."""
        query = update.callback_query
        if query:
            await query.answer("📊 در حال تولید Excel...")
        
        # Parse date range from callback or use today
        parts = query.data.split('_')
        if len(parts) >= 3:
            start_date = datetime.strptime(parts[2], '%Y-%m-%d').date()
            end_date = datetime.strptime(parts[3], '%Y-%m-%d').date()
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
        
        db = BaseHandler.get_db()
        try:
            excel_bytes = ReportService.generate_excel_report(db, start_date, end_date)
            
            # Send Excel as document
            await update.callback_query.message.reply_document(
                document=excel_bytes,
                filename=f"report_{start_date}_{end_date}.xlsx",
                caption=f"📊 گزارش از {start_date} تا {end_date}"
            )
            
            logger.info(f"Excel report generated for {start_date} to {end_date}")
        except Exception as e:
            logger.error(f"Error generating Excel: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در تولید Excel: {str(e)}"
            )
        finally:
            db.close()
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد."
        )
        context.user_data.clear()
        return ConversationHandler.END
