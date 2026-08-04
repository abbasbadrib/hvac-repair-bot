"""
Dashboard and main menu handlers with inline keyboard support.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

class DashboardHandler(BaseHandler):
    """Handler for dashboard and main menu operations."""
    
    @staticmethod
    async def back_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Return to main menu."""
        query = update.callback_query
        if query:
            await query.answer()
            try:
                await query.edit_message_text(
                    "🏠 <b>منوی اصلی</b>\n\n"
                    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    reply_markup=get_main_keyboard(),
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.warning(f"Could not edit message: {e}")
                await query.message.reply_text(
                    "🏠 <b>منوی اصلی</b>\n\n"
                    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                    reply_markup=get_main_keyboard(),
                    parse_mode='HTML'
                )
        else:
            await BaseHandler.send_message(
                update, context,
                "🏠 <b>منوی اصلی</b>\n\n"
                "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
    
    @staticmethod
    async def show_dashboard_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show dashboard from main menu button."""
        db = BaseHandler.get_db()
        try:
            from app.services.report_service import ReportService
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
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_dashboard")],
                [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
            ])
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def refresh_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Refresh dashboard."""
        query = update.callback_query
        await query.answer("🔄 در حال بروزرسانی...")
        await DashboardHandler.show_dashboard_button(update, context)
