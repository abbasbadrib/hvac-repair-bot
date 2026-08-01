"""
Project-related keyboards.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.project import ProjectStatus

def get_project_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Get inline keyboard for project operations."""
    keyboard = [
        [
            InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_project_{project_id}"),
            InlineKeyboardButton("🗑 حذف", callback_data=f"delete_project_{project_id}")
        ],
        [
            InlineKeyboardButton("🔩 قطعات", callback_data=f"parts_{project_id}"),
            InlineKeyboardButton("💰 پرداخت‌ها", callback_data=f"payments_{project_id}")
        ],
        [
            InlineKeyboardButton("💳 هزینه‌ها", callback_data=f"expenses_{project_id}"),
            InlineKeyboardButton("🤝 حق معرفی", callback_data=f"referral_{project_id}")
        ],
        [
            InlineKeyboardButton("📊 محاسبات", callback_data=f"calculate_{project_id}"),
            InlineKeyboardButton("⏰ یادآوری", callback_data=f"reminder_{project_id}")
        ],
        [
            InlineKeyboardButton("✅ پایان پروژه", callback_data=f"complete_{project_id}"),
            InlineKeyboardButton("❌ لغو پروژه", callback_data=f"cancel_{project_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_project_type_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for project type selection."""
    keyboard = [
        [
            InlineKeyboardButton("❄️ کولرگازی", callback_data="project_type_air"),
            InlineKeyboardButton("🔥 پکیج", callback_data="project_type_package")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_service_type_keyboard() -> InlineKeyboardMarkup:
    """Get keyboard for service type selection."""
    keyboard = [
        [
            InlineKeyboardButton("🛠 نصب", callback_data="service_install"),
            InlineKeyboardButton("🔧 تعمیر", callback_data="service_repair")
        ],
        [InlineKeyboardButton("👀 بازدید", callback_data="service_visit")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_status_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for status update."""
    keyboard = []
    for status in ProjectStatus:
        keyboard.append([
            InlineKeyboardButton(status.value, callback_data=f"status_{project_id}_{status.value}")
        ])
    return InlineKeyboardMarkup(keyboard)
