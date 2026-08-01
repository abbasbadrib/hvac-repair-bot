"""
Simple standalone bot runner for Railway.
This file doesn't depend on the app package structure.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Simple bot starter."""
    try:
        # Get token
        token = os.getenv("BOT_TOKEN")
        if not token:
            logger.error("❌ BOT_TOKEN not set in environment variables!")
            return
        
        logger.info("✅ BOT_TOKEN found")
        logger.info("🚀 Starting bot...")
        
        # Import telegram and start bot
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters
        
        # Simple echo bot for testing
        async def start(update: Update, context):
            await update.message.reply_text(
                "👋 سلام! ربات با موفقیت راه‌اندازی شد!\n"
                "در حال بارگذاری کامل قابلیت‌ها..."
            )
        
        async def echo(update: Update, context):
            await update.message.reply_text(f"📨 پیام شما: {update.message.text}")
        
        # Create application
        app = Application.builder().token(token).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        logger.info("🤖 Bot is running...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise

if __name__ == "__main__":
    main()
