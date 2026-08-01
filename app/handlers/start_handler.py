"""
Start command handler.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

class StartHandler(BaseHandler):
    """Handler for /start command."""
    
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
        user = update.effective_user
        welcome_text = (
            f"👋 سلام {user.first_name}!\n\n"
            "به ربات مدیریت پروژه‌های تعمیرات کولرگازی و پکیج خوش آمدید.\n\n"
            "✅ این ربات به شما کمک می‌کند تا:\n"
            "• مدیریت مشتریان\n"
            "• ثبت و پیگیری پروژه‌ها\n"
            "• محاسبه سود و هزینه‌ها\n"
            "• مدیریت قطعات و درآمدها\n"
            "• گزارش‌گیری روزانه، هفتگی، ماهانه و سالانه\n"
            "• یادآوری سرویس‌های دوره‌ای\n\n"
            "📌 لطفاً از منوی اصلی استفاده کنید."
        )
        
        await BaseHandler.send_message(
            update, context,
            welcome_text,
            reply_markup=get_main_keyboard()
        )
        logger.info(f"User {user.id} started the bot")
    
    @staticmethod
    async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
        help_text = (
            "📖 <b>راهنمای ربات</b>\n\n"
            "🏠 <b>خانه</b>: بازگشت به منوی اصلی\n"
            "👤 <b>مشتری‌ها</b>: مدیریت مشتریان (ثبت، ویرایش، حذف، جستجو)\n"
            "🛠 <b>پروژه‌ها</b>: مدیریت پروژه‌ها (ثبت، ویرایش، حذف)\n"
            "💰 <b>ثبت درآمد</b>: ثبت درآمدهای نقدی و کارتی\n"
            "🔩 <b>قطعات</b>: ثبت و مدیریت قطعات مصرفی\n"
            "💳 <b>هزینه‌ها</b>: ثبت هزینه‌های مختلف\n"
            "👥 <b>شریک</b>: مدیریت تسویه با شریک\n"
            "🤝 <b>حق معرفی</b>: ثبت حق معرفی برای پروژه‌ها\n"
            "📊 <b>گزارش</b>: دریافت گزارش‌های مختلف\n"
            "⏰ <b>یادآوری</b>: تنظیم یادآوری سرویس\n"
            "⚙ <b>تنظیمات</b>: تنظیمات ربات\n\n"
            "❓ سوالی دارید؟ با پشتیبانی تماس بگیرید."
        )
        await BaseHandler.send_message(
            update, context,
            help_text,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
