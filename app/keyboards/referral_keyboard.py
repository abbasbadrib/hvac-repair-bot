"""
Referral percentage keyboard.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_referral_percentage_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for referral percentage selection."""
    percentages = [0, 10, 15, 20, 25]
    keyboard = []
    row = []
    for i, pct in enumerate(percentages):
        row.append(InlineKeyboardButton(f"{pct}%", callback_data=f"referral_pct_{project_id}_{pct}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    # Custom percentage option
    keyboard.append([InlineKeyboardButton("✏️ مقدار دلخواه", callback_data=f"referral_custom_{project_id}")])
    keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data=f"cancel_referral")])
    return InlineKeyboardMarkup(keyboard)
