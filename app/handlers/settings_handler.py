"""
Settings and configuration handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.config import Config
from app.keyboards.main_keyboard import get_main_keyboard
import logging
import os
import json

logger = logging.getLogger(__name__)

# Conversation states
EDIT_MY_NAME, EDIT_PARTNER_NAME = range(2)

# File to store names
NAMES_FILE = "names.json"

class SettingsHandler(BaseHandler):
    """Handler for settings operations."""
    
    EDIT_MY_NAME = EDIT_MY_NAME
    EDIT_PARTNER_NAME = EDIT_PARTNER_NAME
    
    @staticmethod
    def load_names():
        """Load names from file."""
        try:
            if os.path.exists(NAMES_FILE):
                with open(NAMES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"my_name": "من", "partner_name": "شریک"}
        except:
            return {"my_name": "من", "partner_name": "شریک"}
    
    @staticmethod
    def save_names(names):
        """Save names to file."""
        try:
            with open(NAMES_FILE, 'w', encoding='utf-8') as f:
                json.dump(names, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    @staticmethod
    async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show settings menu."""
        query = update.callback_query
        if query:
            await query.answer()
        
        names = SettingsHandler.load_names()
        
        text = (
            "⚙️ <b>تنظیمات</b>\n\n"
            f"🔹 <b>نام ربات</b>: {Config.APP_NAME}\n"
            f"🔹 <b>نسخه</b>: 1.0.0\n"
            f"🔹 <b>دیتابیس</b>: {'SQLite' if 'sqlite' in Config.DATABASE_URL else 'PostgreSQL'}\n"
            f"🔹 <b>محدودیت درخواست</b>: {Config.RATE_LIMIT} در دقیقه\n"
            f"🔹 <b>سطح لاگ</b>: {Config.LOG_LEVEL}\n\n"
            f"👤 <b>نام من</b>: {names.get('my_name', 'من')}\n"
            f"👥 <b>نام شریک</b>: {names.get('partner_name', 'شریک')}\n\n"
            "🛠 <b>گزینه‌های تنظیمات</b>:"
        )
        
        keyboard = [
            [InlineKeyboardButton("✏️ ویرایش نام من", callback_data="edit_my_name")],
            [InlineKeyboardButton("✏️ ویرایش نام شریک", callback_data="edit_partner_name")],
            [InlineKeyboardButton("📊 پشتیبان‌گیری از دیتابیس", callback_data="backup_db")],
            [InlineKeyboardButton("🔄 بازنشانی دیتابیس", callback_data="reset_db")],
            [InlineKeyboardButton("📋 گزارش خطاها", callback_data="error_logs")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await BaseHandler.send_message(
            update, context,
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def edit_my_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing my name."""
        query = update.callback_query
        await query.answer()
        
        await BaseHandler.edit_message(
            update, context,
            "✏️ <b>ویرایش نام من</b>\n\n"
            "لطفاً <b>نام جدید</b> خود را وارد کنید:\n"
            "(برای انصراف /cancel را بفرستید)",
            parse_mode='HTML'
        )
        return EDIT_MY_NAME
    
    @staticmethod
    async def save_my_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save my name."""
        new_name = update.message.text.strip()
        if not new_name:
            await BaseHandler.send_message(
                update, context,
                "❌ نام نمی‌تواند خالی باشد.",
                parse_mode='HTML'
            )
            return EDIT_MY_NAME
        
        names = SettingsHandler.load_names()
        names['my_name'] = new_name
        SettingsHandler.save_names(names)
        
        await BaseHandler.send_message(
            update, context,
            f"✅ <b>نام شما با موفقیت ویرایش شد!</b>\n\n"
            f"👤 نام جدید: {new_name}",
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def edit_partner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing partner name."""
        query = update.callback_query
        await query.answer()
        
        await BaseHandler.edit_message(
            update, context,
            "✏️ <b>ویرایش نام شریک</b>\n\n"
            "لطفاً <b>نام جدید</b> شریک را وارد کنید:\n"
            "(برای انصراف /cancel را بفرستید)",
            parse_mode='HTML'
        )
        return EDIT_PARTNER_NAME
    
    @staticmethod
    async def save_partner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save partner name."""
        new_name = update.message.text.strip()
        if not new_name:
            await BaseHandler.send_message(
                update, context,
                "❌ نام نمی‌تواند خالی باشد.",
                parse_mode='HTML'
            )
            return EDIT_PARTNER_NAME
        
        names = SettingsHandler.load_names()
        names['partner_name'] = new_name
        SettingsHandler.save_names(names)
        
        await BaseHandler.send_message(
            update, context,
            f"✅ <b>نام شریک با موفقیت ویرایش شد!</b>\n\n"
            f"👥 نام جدید: {new_name}",
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def backup_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Backup database."""
        query = update.callback_query
        await query.answer("📊 در حال پشتیبان‌گیری...")
        
        try:
            source = "app.db"
            if os.path.exists(source):
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"{backup_dir}/app_backup_{timestamp}.db"
                
                shutil.copy2(source, backup_file)
                
                with open(backup_file, 'rb') as f:
                    await update.callback_query.message.reply_document(
                        document=f,
                        filename=f"backup_{timestamp}.db",
                        caption="✅ پشتیبان‌گیری با موفقیت انجام شد!"
                    )
                
                logger.info(f"Database backed up to {backup_file}")
            else:
                await BaseHandler.send_message(
                    update, context,
                    "❌ فایل دیتابیس یافت نشد."
                )
        except Exception as e:
            logger.error(f"Error backing up database: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در پشتیبان‌گیری: {str(e)}"
            )
    
    @staticmethod
    async def reset_database(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset database (with confirmation)."""
        query = update.callback_query
        await query.answer()
        
        keyboard = [
            [
                InlineKeyboardButton("✅ بله، بازنشانی کن", callback_data="confirm_reset"),
                InlineKeyboardButton("❌ خیر، انصراف", callback_data="cancel_reset")
            ]
        ]
        
        await BaseHandler.edit_message(
            update, context,
            "⚠️ <b>هشدار!</b>\n\n"
            "آیا مطمئن هستید که می‌خواهید دیتابیس را بازنشانی کنید؟\n"
            "این عمل <b>غیرقابل بازگشت</b> است و تمام داده‌ها حذف می‌شوند.\n\n"
            "قبل از انجام این کار حتماً از دیتابیس پشتیبان بگیرید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def confirm_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm database reset."""
        query = update.callback_query
        await query.answer("🔄 در حال بازنشانی...")
        
        try:
            from app.database.base import Base, engine
            
            Base.metadata.drop_all(engine)
            Base.metadata.create_all(engine)
            
            await BaseHandler.edit_message(
                update, context,
                "✅ دیتابیس با موفقیت بازنشانی شد.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings")]
                ]),
                parse_mode='HTML'
            )
            
            logger.info("Database reset successfully")
            
        except Exception as e:
            logger.error(f"Error resetting database: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در بازنشانی دیتابیس: {str(e)}"
            )
    
    @staticmethod
    async def cancel_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel database reset."""
        query = update.callback_query
        await query.answer("❌ عملیات لغو شد")
        await SettingsHandler.show_settings(update, context)
    
    @staticmethod
    async def show_error_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show error logs."""
        query = update.callback_query
        await query.answer()
        
        try:
            log_file = "app.log"
            if not os.path.exists(log_file):
                await BaseHandler.edit_message(
                    update, context,
                    "📋 هیچ لاگ خطایی یافت نشد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                last_lines = lines[-50:] if len(lines) > 50 else lines
                log_text = ''.join(last_lines)
            
            if not log_text.strip():
                log_text = "📋 هیچ لاگ خطایی یافت نشد."
            
            if len(log_text) > 4000:
                with open(log_file, 'rb') as f:
                    await update.callback_query.message.reply_document(
                        document=f,
                        filename="error_logs.log",
                        caption="📋 لاگ‌های خطا"
                    )
            else:
                await BaseHandler.edit_message(
                    update, context,
                    f"📋 <b>لاگ‌های خطا</b>\n\n<code>{log_text}</code>",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔄 بروزرسانی", callback_data="error_logs")],
                        [InlineKeyboardButton("🔙 بازگشت به تنظیمات", callback_data="settings")]
                    ]),
                    parse_mode='HTML'
                )
                
        except Exception as e:
            logger.error(f"Error reading logs: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در خواندن لاگ: {str(e)}"
            )
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
