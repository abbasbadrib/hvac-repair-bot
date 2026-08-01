"""
Payment management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.payment_service import PaymentService
from app.services.project_service import ProjectService
from app.models.payment import PaymentMethod
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
PAYMENT_AMOUNT, PAYMENT_METHOD, PAYMENT_DESCRIPTION = range(3)

class PaymentHandler(BaseHandler):
    """Handler for payment operations."""
    
    # Expose states for main.py
    PAYMENT_AMOUNT = PAYMENT_AMOUNT
    PAYMENT_METHOD = PAYMENT_METHOD
    PAYMENT_DESCRIPTION = PAYMENT_DESCRIPTION
    
    @staticmethod
    async def show_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payments for a project."""
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
                        "💰 <b>ثبت درآمد</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.\n\n"
                        "لطفاً ابتدا یک پروژه ثبت کنید.",
                        reply_markup=get_main_keyboard(),
                        parse_mode='HTML'
                    )
                    return
                
                text = "💰 <b>انتخاب پروژه برای ثبت درآمد</b>\n\n"
                keyboard = []
                for project in projects[:10]:
                    status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                    keyboard.append([
                        InlineKeyboardButton(
                            f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                            callback_data=f"payments_{project.id}"
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
            payments = PaymentService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not payments:
                text = f"💰 <b>پرداخت‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n❌ هیچ پرداختی ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت پرداخت جدید", callback_data=f"add_payment_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ])
                await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = f"💰 <b>پرداخت‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n\n"
            total_payments = 0
            
            for i, payment in enumerate(payments, 1):
                text += f"{i}. {payment.method.value}\n   💰 {payment.amount:,.0f} تومان\n   📅 {payment.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                total_payments += payment.amount
            
            text += f"💰 <b>جمع کل پرداخت‌ها</b>: {total_payments:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت پرداخت جدید", callback_data=f"add_payment_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def add_payment_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new payment."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['payment_project_id'] = project_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            f"💰 <b>ثبت پرداخت جدید</b>\n\nلطفاً مبلغ پرداخت را وارد کنید (تومان):",
            parse_mode='HTML'
        )
        return PAYMENT_AMOUNT
    
    @staticmethod
    async def add_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment amount."""
        try:
            amount = float(update.message.text.replace(',', '').strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            context.user_data['payment_amount'] = amount
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
                parse_mode='HTML'
            )
            return PAYMENT_AMOUNT
        
        # Show payment methods
        keyboard = []
        for method in PaymentMethod:
            keyboard.append([
                InlineKeyboardButton(method.value, callback_data=f"pay_method_{method.value}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_payment")])
        
        await BaseHandler.send_message(
            update, context,
            "💳 لطفاً <b>روش پرداخت</b> را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return PAYMENT_METHOD
    
    @staticmethod
    async def add_payment_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment method."""
        query = update.callback_query
        method_value = query.data.split('_')[2]
        
        # Find the payment method enum
        payment_method = None
        for method in PaymentMethod:
            if method.value == method_value:
                payment_method = method
                break
        
        if not payment_method:
            await query.answer("❌ روش پرداخت نامعتبر", True)
            return PAYMENT_METHOD
        
        context.user_data['payment_method'] = payment_method
        await query.answer()
        
        await BaseHandler.edit_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> پرداخت را وارد کنید:\n(برای رد کردن '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return PAYMENT_DESCRIPTION
    
    @staticmethod
    async def add_payment_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get payment description and save."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['payment_description'] = description
        
        # Save payment
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['payment_project_id']
            
            payment = PaymentService.create(
                db,
                project_id=project_id,
                amount=context.user_data['payment_amount'],
                method=context.user_data['payment_method'],
                description=context.user_data.get('payment_description')
            )
            
            text = (
                f"✅ <b>پرداخت با موفقیت ثبت شد!</b>\n\n"
                f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
                f"💳 روش: {payment.method.value}\n"
                f"📝 توضیحات: {payment.description or 'ثبت نشده'}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت پرداخت دیگر", callback_data=f"add_payment_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پرداخت‌ها", callback_data=f"payments_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New payment added: {payment.amount} for project {project_id}")
            
        except Exception as e:
            logger.error(f"Error adding payment: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت پرداخت: {str(e)}"
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
