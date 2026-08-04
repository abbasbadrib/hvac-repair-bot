"""
Reminder management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.payment_service import PaymentService
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class ReminderHandler(BaseHandler):
    """Handler for reminder operations."""
    
    @staticmethod
    async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reminder options."""
        if update.callback_query:
            await update.callback_query.answer()
        
        keyboard = [
            [InlineKeyboardButton("💰 یادآوری تسویه", callback_data="reminder_settlement")],
            [InlineKeyboardButton("🛠 یادآوری پیگیری پروژه", callback_data="reminder_followup")],
            [InlineKeyboardButton("📋 لیست همه پروژه‌ها", callback_data="reminder_all")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            "⏰ <b>یادآوری</b>\n\n"
            "• <b>یادآوری تسویه</b>: پروژه‌های تکمیل شده با بدهی\n"
            "• <b>یادآوری پیگیری</b>: پروژه‌های در حال انجام\n"
            "• <b>لیست همه پروژه‌ها</b>: مشاهده همه پروژه‌ها\n\n"
            "لطفاً نوع یادآوری را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def show_settlement_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show projects with debt (completed + in progress)."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            all_projects = ProjectService.get_all(db)
            debt_projects = []
            
            for project in all_projects:
                if project.status in [ProjectStatus.COMPLETED, ProjectStatus.IN_PROGRESS]:
                    payments = PaymentService.get_by_project(db, project.id)
                    total_payments = sum(p.amount for p in payments)
                    debt = project.labor_cost - total_payments
                    if debt > 0:
                        debt_projects.append({
                            'project': project,
                            'debt': debt,
                            'status': project.status
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
                status_text = "✅ تکمیل شده" if item['status'] == ProjectStatus.COMPLETED else "🟢 در حال انجام"
                text += f"👤 {p.customer.name}\n"
                text += f"   🛠 {p.project_type.value} - {p.service_type}\n"
                text += f"   📊 وضعیت: {status_text}\n"
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
    async def show_all_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show all projects."""
        query = update.callback_query
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.get_all(db)
            
            if not projects:
                await BaseHandler.edit_message(
                    update, context,
                    "📋 <b>لیست پروژه‌ها</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="reminder_menu")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "📋 <b>لیست همه پروژه‌ها</b>\n\n"
            for project in projects:
                status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
                text += f"{status_emoji} {project.customer.name} - {project.project_type.value}\n"
                text += f"   📅 {project.start_date.strftime('%Y-%m-%d')}\n"
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
        """Set reminder time."""
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
