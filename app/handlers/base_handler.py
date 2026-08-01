"""
Base handler class with common functionality.
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.database.base import SessionLocal
import logging

logger = logging.getLogger(__name__)

class BaseHandler:
    """Base class for all handlers."""
    
    @staticmethod
    def get_db():
        """Get database session."""
        return SessionLocal()
    
    @staticmethod
    async def send_message(update: Update, context: ContextTypes.DEFAULT_TYPE, 
                          text: str, reply_markup=None, parse_mode='HTML'):
        """Send a message to the user."""
        try:
            await update.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            await update.message.reply_text("❌ خطا در ارسال پیام. لطفاً دوباره تلاش کنید.")
    
    @staticmethod
    async def edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          text: str, reply_markup=None, parse_mode='HTML'):
        """Edit an existing message."""
        try:
            await update.callback_query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            await update.callback_query.answer("❌ خطا در ویرایش پیام.")
    
    @staticmethod
    async def answer_callback(update: Update, text: str, show_alert=False):
        """Answer a callback query."""
        try:
            await update.callback_query.answer(text=text, show_alert=show_alert)
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
