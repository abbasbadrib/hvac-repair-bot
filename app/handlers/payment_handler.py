"""
Payment management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.payment_service import PaymentService
from app.services.project_service import ProjectService
from app.models.payment import PaymentMethod
import logging

logger = logging.getLogger(__name__)

# Conversation states
(PAYMENT_AMOUNT, PAYMENT_METHOD, PAYMENT_DESCRIPTION) = range(3)

class PaymentHandler(BaseHandler):
    """Handler for payment operations."""
    
    @staticmethod
    async def show_payments(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show payments for a project."""
        query = update.callback_query
        project_id = int(query.data.split('_')[1])
        context.user_data['current_project_id'] = project_id
        
        db = BaseHandler.get_db()
        try:
            payments = PaymentService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not payments:
                await query.answer()
                await BaseHandler.edit_message(
                    update, context,
                    f"💰 <b>پرداخت‌های پروژه</b>\n\n"
                    f"👤 مشتری: {project.customer.name}\n"
                    f"❌ هیچ پرداختی ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت پرداخت جدید", callback_data=f"add_payment_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = f"💰 <b>پرداخت‌های پروژه</b>\n\n"
            text += f"👤 مشتری: {project.customer.name}\n\n"
            
            total_payments = 0
            for i, payment in enumerate(payments, 1):
                text += (
                    f"{i}. {payment.method.value}\n"
                    f"   💰 {payment.amount:,.0f} تومان\n"
                    f"   📝 {payment.description or 'بدون توضیح'}\n"
                    f"   📅 {payment.created_at.strftime('%Y-%m-%d %H:%M')}\n\n"
                )
                total_payments += payment.amount
            
            text += f"💰 <b>جمع کل پرداخت‌ها</b>: {total_payments:,.0f} تومان"
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت پرداخت جدید", callback_data=f"add_payment_{project_id}")],
                [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
            ]
            
            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
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
            f"💰 <b>ثبت پرداخت جدید</b>\n\n"
            "لطفاً مبلغ پرداخت را وارد کنید (تومان):",
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
        
        await BaseHandler.send_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> پرداخت را وارد کنید:\n"
            "(برای رد کردن از این مرحله '.' را وارد کنید)",
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
                "✅ <b>پرداخت با موفقیت ثبت شد!</b>\n\n"
                f"💰 مبلغ: {payment.amount:,.0f} تومان\n"
                f"💳 روش: {payment.method.value}\n"
                f"📝 توضیحات: {payment.description or 'ثبت نشده'}"
            )
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت پرداخت دیگر", callback_data=f"add_payment_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پرداخت‌ها", callback_data=f"payments_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ]),
                parse_mode='HTML'
            )
            
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
