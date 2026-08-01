"""
Reminder management handlers - برای یادآوری تسویه و پیگیری پروژه‌ها
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.payment_service import PaymentService
from app.services.customer_service import CustomerService
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Conversation states
REMINDER_TYPE, REMINDER_INTERVAL, REMINDER_TIME = range(3)

class ReminderHandler(BaseHandler):
    """Handler for reminder operations."""
    
    REMINDER_TYPE = REMINDER_TYPE
    REMINDER_INTERVAL = REMINDER_INTERVAL
    REMINDER_TIME = REMINDER_TIME
    
    @staticmethod
    async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reminder options."""
        # Check if called from main menu or callback
        if update.callback_query:
            await update.callback_query.answer()
        
        keyboard = [
            [InlineKeyboardButton("💰 یادآوری تسویه", callback_data="reminder_settlement")],
            [InlineKeyboardButton("🛠 یادآوری پیگیری پروژه", callback_data="reminder_followup")],
            [InlineKeyboardButton("📋 لیست پروژه‌های نیازمند پیگیری", callback_data="reminder_list")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "⏰ <b>یادآوری</b>\n\n"
            "• <b>یادآوری تسویه</b>: برای پروژه‌هایی که بدهی دارند\n"
            "• <b>یادآوری پیگیری</b>: برای پروژه‌های ناتمام\n"
            "• <b>لیست پروژه‌ها</b>: مشاهده پروژه‌های نیازمند پیگیری\n\n"
            "لطفاً نوع یادآوری را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def show_settlement_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show projects with debt."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.get_all(db)
            debt_projects = []
            
            for project in projects:
                if project.status == ProjectStatus.COMPLETED:
                    payments = PaymentService.get_by_project(db, project.id)
                    total_payments = sum(p.amount for p in payments)
                    if total_payments < project.labor_cost:
                        debt_projects.append({
                            'project': project,
                            'debt': project.labor_cost - total_payments
                        })
            
            if not debt_projects:
                await BaseHandler.edit_message(
                    update, context,
                    "💰 <b>یادآوری تسویه</b>\n\n"
                    "✅ هیچ پروژه‌ای با بدهی باقی‌مانده وجود ندارد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "💰 <b>پروژه‌های نیازمند تسویه</b>\n\n"
            for item in debt_projects:
                p = item['project']
                text += f"👤 {p.customer.name}\n"
                text += f"   🛠 {p.project_type.value} - {p.service_type}\n"
                text += f"   💰 بدهی: {item['debt']:,.0f} تومان\n"
                text += f"   📅 {p.start_date.strftime('%Y-%m-%d')}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
            ]
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def show_followup_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show incomplete projects."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.get_by_status(db, ProjectStatus.IN_PROGRESS)
            
            if not projects:
                await BaseHandler.edit_message(
                    update, context,
                    "🛠 <b>یادآوری پیگیری پروژه</b>\n\n"
                    "✅ هیچ پروژه ناتمامی وجود ندارد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "🛠 <b>پروژه‌های در حال انجام</b>\n\n"
            for project in projects:
                days = (datetime.utcnow() - project.start_date).days
                text += f"👤 {project.customer.name}\n"
                text += f"   🛠 {project.project_type.value} - {project.service_type}\n"
                text += f"   📅 {days} روز از شروع گذشته\n"
                text += f"   📝 {project.description or 'بدون توضیح'}\n\n"
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
            ]
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def set_reminder_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Set reminder time (for future implementation)."""
        query = update.callback_query
        await query.answer("⏳ این قابلیت به زودی اضافه می‌شود")
        
        await BaseHandler.edit_message(
            update, context,
            "⏰ <b>تنظیم یادآوری</b>\n\n"
            "این قابلیت به شما امکان می‌دهد:\n"
            "• یادآوری روزانه در ساعت مشخص\n"
            "• یادآوری هر چند روز یکبار\n"
            "• یادآوری هفتگی\n\n"
            "🔜 به زودی اضافه می‌شود.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
            ]),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Back to reminder menu."""
        query = update.callback_query
        await query.answer()
        await ReminderHandler.show_reminders(update, context)
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel operation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
