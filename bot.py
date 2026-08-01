"""
Standalone bot that doesn't depend on complex imports.
"""
import os
import sys
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Main menu keyboard
main_keyboard = ReplyKeyboardMarkup([
    ["🏠 خانه", "👤 مشتری‌ها"],
    ["🛠 پروژه‌ها", "💰 ثبت درآمد"],
    ["🔩 قطعات", "💳 هزینه‌ها"],
    ["👥 شریک", "🤝 حق معرفی"],
    ["📊 گزارش", "⏰ یادآوری"],
    ["⚙ تنظیمات"]
], resize_keyboard=True)

async def start(update: Update, context):
    """Start command."""
    await update.message.reply_text(
        "👋 سلام! به ربات مدیریت تعمیرات کولرگازی و پکیج خوش آمدید!\n\n"
        "✅ ربات با موفقیت راه‌اندازی شد!\n"
        "📌 لطفاً از منوی اصلی استفاده کنید.",
        reply_markup=main_keyboard
    )

async def handle_message(update: Update, context):
    """Handle all messages."""
    text = update.message.text
    
    if text == "🏠 خانه":
        await start(update, context)
    else:
        await update.message.reply_text(
            f"📨 <b>{text}</b>\n\n"
            "🔧 این بخش در حال توسعه است.\n"
            "به زودی قابلیت‌های کامل اضافه می‌شوند.",
            parse_mode='HTML'
        )

def main():
    """Main function."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN not set in environment variables!")
        return
    
    logger.info("🚀 Starting HVAC Repair Bot...")
    
    # Create application
    app = Application.builder().token(token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("🤖 Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
