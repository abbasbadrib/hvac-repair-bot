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
            # Check if update has message
            if update.message:
                await update.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            # Check if update has callback_query with message
            elif update.callback_query and update.callback_query.message:
                await update.callback_query.message.reply_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                logger.error("No message or callback_query found in update")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            try:
                if update.callback_query:
                    await update.callback_query.answer("❌ خطا در ارسال پیام", show_alert=True)
            except:
                pass
    
    @staticmethod
    async def edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE,
                          text: str, reply_markup=None, parse_mode='HTML'):
        """Edit an existing message."""
        try:
            if update.callback_query and update.callback_query.message:
                await update.callback_query.edit_message_text(
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode=parse_mode
                )
            else:
                logger.error("No callback_query found for edit_message")
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            try:
                await update.callback_query.answer("❌ خطا در ویرایش پیام", show_alert=True)
            except:
                pass
    
    @staticmethod
    async def answer_callback(update: Update, text: str, show_alert=False):
        """Answer a callback query."""
        try:
            if update.callback_query:
                await update.callback_query.answer(text=text, show_alert=show_alert)
        except Exception as e:
            logger.error(f"Error answering callback: {e}")
