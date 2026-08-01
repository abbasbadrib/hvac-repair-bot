"""
Main keyboard with ReplyKeyboardMarkup.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Get the main menu keyboard."""
    keyboard = [
        [KeyboardButton("🏠 خانه"), KeyboardButton("👤 مشتری‌ها")],
        [KeyboardButton("🛠 پروژه‌ها"), KeyboardButton("💰 ثبت درآمد")],
        [KeyboardButton("🔩 قطعات"), KeyboardButton("💳 هزینه‌ها")],
        [KeyboardButton("👥 شریک"), KeyboardButton("🤝 حق معرفی")],
        [KeyboardButton("📊 گزارش"), KeyboardButton("⏰ یادآوری")],
        [KeyboardButton("⚙ تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
