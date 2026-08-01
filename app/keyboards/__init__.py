"""
Keyboards package.
"""
from app.keyboards.main_keyboard import get_main_keyboard
from app.keyboards.project_keyboards import (
    get_project_keyboard,
    get_project_type_keyboard,
    get_service_type_keyboard,
    get_status_keyboard
)
from app.keyboards.payment_keyboards import (
    get_payment_method_keyboard,
    get_expense_type_keyboard,
    get_paid_by_keyboard
)
from app.keyboards.referral_keyboard import get_referral_percentage_keyboard
