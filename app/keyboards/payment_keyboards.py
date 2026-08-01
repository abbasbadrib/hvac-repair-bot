"""
Payment-related keyboards.
"""

from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from app.models.payment import PaymentMethod

def get_payment_method_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for payment method selection."""
    keyboard = []
    for method in PaymentMethod:
        keyboard.append([
            InlineKeyboardButton(method.value, callback_data=f"payment_{project_id}_{method.value}")
        ])
    return InlineKeyboardMarkup(keyboard)

def get_expense_type_keyboard(project_id: int) -> InlineKeyboardMarkup:
    """Get keyboard for expense type selection."""
    from app.models.expense import ExpenseType
    keyboard = []
    for exp_type in ExpenseType:
        keyboard.append([
            InlineKeyboardButton(exp_type.value, callback_data=f"expense_{project_id}_{exp_type.value}")
        ])
    return InlineKeyboardMarkup(keyboard)

def get_paid_by_keyboard(project_id: int, expense_type: str) -> InlineKeyboardMarkup:
    """Get keyboard for who paid the expense."""
    from app.models.expense import PaidBy
    keyboard = [
        [
            InlineKeyboardButton("👤 من", callback_data=f"paidby_{project_id}_{expense_type}_me"),
            InlineKeyboardButton("👥 شریک", callback_data=f"paidby_{project_id}_{expense_type}_partner")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
