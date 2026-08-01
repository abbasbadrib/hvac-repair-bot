"""
Expense management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.expense_service import ExpenseService
from app.services.project_service import ProjectService
from app.models.expense import ExpenseType, PaidBy
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
EXPENSE_TYPE, EXPENSE_AMOUNT, EXPENSE_PAID_BY, EXPENSE_DESCRIPTION = range(4)

class ExpenseHandler(BaseHandler):
    """Handler for expense operations."""
    
    # Expose states for main.py
    EXPENSE_TYPE = EXPENSE_TYPE
    EXPENSE_AMOUNT = EXPENSE_AMOUNT
    EXPENSE_PAID_BY = EXPENSE_PAID_BY
    EXPENSE_DESCRIPTION = EXPENSE_DESCRIPTION
    
    @staticmethod
    async def show_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show expenses for a project."""
        # Check if called from main menu or callback
        if update.callback_query:
            query = update.callback_query
            project_id = int(query.data.split('_')[1])
            context.user_data['current_project_id'] = project_id
            await query.answer()
        else:
            # Called from main menu - show list of projects
            db = BaseHandler.get_db()
            try:
                projects = ProjectService.get_all(db)
                if not projects:
                    await BaseHandler.send_message(
                        update, context,
                        "💳 <b>هزینه‌ها</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.\n\n"
                        "لطفاً ابتدا یک پروژه ثبت کنید.",
                        reply_markup=get_main_keyboard(),
                        parse_mode='HTML'
                    )
                    return
                
                text = "💳 <b>انتخاب پروژه برای مدیریت هزینه‌ها</b>\n\n"
                keyboard = []
                for project in projects[:10]:
                    status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                            callback_data=f"expenses_{project.id}"
                        )
                    ])
                keyboard.append([InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")])
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            finally:
                db.close()
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['current_project_id']
            expenses = ExpenseService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not expenses:
                text = f"💳 <b>هزینه‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n❌ هیچ هزینه‌ای ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت هزینه جدید", callback_data=f"add_expense_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ])
                await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = f"💳 <b>هزینه‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n\n"
            total_expenses = 0
            me_expenses = 0
            partner_expenses = 0
            
            for i, expense in enumerate(expenses, 1):
                paid_by_emoji = "👤" if expense.paid_by == PaidBy.ME else "👥"
                text += f"{i}. {expense.expense_type.value}\n   💰 {expense.amount:,.0f} تومان | {paid_by_emoji} {expense.paid_by.value}\n\n"
                total_expenses += expense.amount
                if expense.paid_by == PaidBy.ME:
                    me_expenses += expense.amount
                else:
                    partner_expenses += expense.amount
            
            text += f"💰 <b>جمع کل هزینه‌ها</b>: {total_expenses:,.0f} تومان\n"
            text += f"👤 <b>پرداخت شده توسط من</b>: {me_expenses:,.0f} تومان\n"
            text += f"👥 <b>پرداخت شده توسط شریک</b>: {partner_expenses:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت هزینه جدید", callback_data=f"add_expense_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new expense."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['expense_project_id'] = project_id
        
        await query.answer()
        
        # Show expense type selection
        keyboard = []
        for exp_type in ExpenseType:
            keyboard.append([
                InlineKeyboardButton(exp_type.value, callback_data=f"exp_type_{project_id}_{exp_type.value}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_expense")])
        
        await BaseHandler.edit_message(
            update, context,
            "💳 <b>ثبت هزینه جدید</b>\n\nلطفاً <b>نوع هزینه</b> را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return EXPENSE_TYPE
    
    @staticmethod
    async def add_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense type."""
        query = update.callback_query
        parts = query.data.split('_')
        expense_type = parts[3]
        context.user_data['expense_type'] = expense_type
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            f"💳 <b>ثبت هزینه {expense_type}</b>\n\n💰 مبلغ هزینه را وارد کنید (تومان):",
            parse_mode='HTML'
        )
        return EXPENSE_AMOUNT
    
    @staticmethod
    async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense amount."""
        try:
            amount = float(update.message.text.replace(',', '').strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            context.user_data['expense_amount'] = amount
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
                parse_mode='HTML'
            )
            return EXPENSE_AMOUNT
        
        # Show who paid
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👤 من", callback_data="exp_paid_me"),
                InlineKeyboardButton("👥 شریک", callback_data="exp_paid_partner")
            ],
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_expense")]
        ])
        
        await BaseHandler.send_message(
            update, context,
            "💳 چه کسی این هزینه را پرداخت کرده است؟",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return EXPENSE_PAID_BY
    
    @staticmethod
    async def add_expense_paid_by(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get who paid."""
        query = update.callback_query
        paid_by = query.data.split('_')[2]
        context.user_data['expense_paid_by'] = PaidBy.ME if paid_by == 'me' else PaidBy.PARTNER
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> هزینه را وارد کنید:\n(برای رد کردن '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return EXPENSE_DESCRIPTION
    
    @staticmethod
    async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense description and save."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['expense_description'] = description
        
        # Save expense
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['expense_project_id']
            
            # Get expense type from value
            expense_type_value = context.user_data['expense_type']
            expense_type = None
            for et in ExpenseType:
                if et.value == expense_type_value:
                    expense_type = et
                    break
            
            if not expense_type:
                raise ValueError("Invalid expense type")
            
            expense = ExpenseService.create(
                db,
                project_id=project_id,
                expense_type=expense_type,
                amount=context.user_data['expense_amount'],
                paid_by=context.user_data['expense_paid_by'],
                description=context.user_data.get('expense_description')
            )
            
            text = (
                f"✅ <b>هزینه با موفقیت ثبت شد!</b>\n\n"
                f"💳 نوع: {expense.expense_type.value}\n"
                f"💰 مبلغ: {expense.amount:,.0f} تومان\n"
                f"👤 پرداخت کننده: {expense.paid_by.value}\n"
                f"📝 توضیحات: {expense.description or 'ثبت نشده'}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت هزینه دیگر", callback_data=f"add_expense_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data=f"expenses_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New expense added: {expense.expense_type.value} for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت هزینه: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد."
        )
        context.user_data.clear()
        return ConversationHandler.END
