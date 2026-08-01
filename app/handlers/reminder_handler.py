"""
Reminder management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.reminder_service import ReminderService
from app.services.project_service import ProjectService
from app.models.reminder import ReminderInterval
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Conversation states
(REMINDER_INTERVAL, REMINDER_DATE) = range(2)

class ReminderHandler(BaseHandler):
    """Handler for reminder operations."""
    
    @staticmethod
    async def show_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show reminders for a project."""
        query = update.callback_query
        project_id = int(query.data.split('_')[1])
        context.user_data['reminder_project_id'] = project_id
        
        db = BaseHandler.get_db()
        try:
            reminders = ReminderService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not reminders:
                await query.answer()
                await BaseHandler.edit_message(
                    update, context,
                    f"⏰ <b>یادآوری‌های پروژه</b>\n\n"
                    f"👤 مشتری: {project.customer.name}\n"
                    f"❌ هیچ یادآوری ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت یادآوری جدید", callback_data=f"add_reminder_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = f"⏰ <b>یادآوری‌های پروژه</b>\n\n"
            text += f"👤 مشتری: {project.customer.name}\n\n"
            
            for reminder in reminders:
                status = "✅ ارسال شده" if reminder.is_sent else "⏳ در انتظار"
                text += (
                    f"📅 {reminder.interval.value}\n"
                    f"   تاریخ: {reminder.reminder_date.strftime('%Y-%m-%d %H:%M')}\n"
                    f"   وضعیت: {status}\n\n"
                )
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت یادآوری جدید", callback_data=f"add_reminder_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def add_reminder_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new reminder."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['reminder_project_id'] = project_id
        
        # Show interval selection
        keyboard = []
        for interval in ReminderInterval:
            keyboard.append([
                InlineKeyboardButton(interval.value, callback_data=f"rem_interval_{project_id}_{interval.value}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_reminder")])
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "⏰ <b>ثبت یادآوری جدید</b>\n\n"
            "لطفاً <b>بازه زمانی</b> یادآوری را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return REMINDER_INTERVAL
    
    @staticmethod
    async def add_reminder_interval(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get reminder interval."""
        query = update.callback_query
        parts = query.data.split('_')
        interval_value = parts[3]
        
        # Find the interval enum
        interval = None
        for rem_interval in ReminderInterval:
            if rem_interval.value == interval_value:
                interval = rem_interval
                break
        
        if not interval:
            await query.answer("❌ بازه نامعتبر", True)
            return REMINDER_INTERVAL
        
        context.user_data['reminder_interval'] = interval
        
        # Get project start date or use current date
        db = BaseHandler.get_db()
        try:
            project = ProjectService.get_by_id(db, context.user_data['reminder_project_id'])
            if project and project.start_date:
                start_date = project.start_date
            else:
                start_date = datetime.utcnow()
            
            # Calculate reminder date
            reminder_date = ReminderService.calculate_reminder_date(start_date, interval)
            context.user_data['reminder_date'] = reminder_date
            
            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                f"⏰ <b>یادآوری {interval.value}</b>\n\n"
                f"📅 تاریخ یادآوری: {reminder_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                "آیا از این تاریخ مطمئن هستید؟\n"
                "برای تغییر تاریخ، عدد مورد نظر را وارد کنید (مثلاً 2024-12-31)\n"
                "برای تایید، '.' را وارد کنید.",
                parse_mode='HTML'
            )
            return REMINDER_DATE
        finally:
            db.close()
    
    @staticmethod
    async def add_reminder_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get reminder date and save."""
        text = update.message.text.strip()
        
        if text != '.':
            # Try to parse custom date
            try:
                reminder_date = datetime.strptime(text, '%Y-%m-%d')
                context.user_data['reminder_date'] = reminder_date
            except ValueError:
                await BaseHandler.send_message(
                    update, context,
                    "❌ تاریخ نامعتبر است. فرمت صحیح: YYYY-MM-DD\n"
                    "مثال: 2024-12-31",
                    parse_mode='HTML'
                )
                return REMINDER_DATE
        
        # Save reminder
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['reminder_project_id']
            reminder_date = context.user_data['reminder_date']
            interval = context.user_data['reminder_interval']
            
            reminder = ReminderService.create(
                db,
                project_id=project_id,
                interval=interval,
                reminder_date=reminder_date
            )
            
            text = (
                "✅ <b>یادآوری با موفقیت ثبت شد!</b>\n\n"
                f"⏰ بازه: {reminder.interval.value}\n"
                f"📅 تاریخ: {reminder.reminder_date.strftime('%Y-%m-%d %H:%M')}"
            )
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
            logger.info(f"New reminder added for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error adding reminder: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت یادآوری: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد."
        )
        context.user_data.clear()
        return ConversationHandler.END
