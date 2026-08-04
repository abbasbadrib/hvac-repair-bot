"""
Main keyboard with InlineKeyboardMarkup.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_keyboard() -> InlineKeyboardMarkup:
    """Get the main menu as inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("👤 مشتری‌ها", callback_data="menu_customers"),
            InlineKeyboardButton("🛠 پروژه‌ها", callback_data="menu_projects")
        ],
        [
            InlineKeyboardButton("🔩 قطعات", callback_data="menu_parts"),
            InlineKeyboardButton("💳 هزینه‌ها", callback_data="menu_expenses")
        ],
        [
            InlineKeyboardButton("💰 ثبت درآمد", callback_data="menu_income"),
            InlineKeyboardButton("🤝 حق معرفی", callback_data="menu_referral")
        ],
        [
            InlineKeyboardButton("👥 شریک", callback_data="menu_partner"),
            InlineKeyboardButton("📊 گزارش‌ها", callback_data="menu_reports")
        ],
        [
            InlineKeyboardButton("⏰ یادآوری", callback_data="menu_reminder"),
            InlineKeyboardButton("⚙ تنظیمات", callback_data="menu_settings")
        ],
        [
            InlineKeyboardButton("🏠 خانه", callback_data="menu_home")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_back_keyboard(callback: str = "back_home") -> InlineKeyboardMarkup:
    """Get back button keyboard."""
    keyboard = [
        [InlineKeyboardButton("🔙 بازگشت", callback_data=callback)]
    ]
    return InlineKeyboardMarkup(keyboard)
