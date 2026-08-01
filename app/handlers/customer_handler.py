"""
Customer management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.customer_service import CustomerService
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
(NAME, PHONE, ADDRESS, DESCRIPTION) = range(4)

class CustomerHandler(BaseHandler):
    """Handler for customer operations."""
    
    @staticmethod
    async def show_customers(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of customers."""
        db = BaseHandler.get_db()
        try:
            customers = CustomerService.get_all(db)
            if not customers:
                text = "📋 <b>لیست مشتریان</b>\n\n❌ هیچ مشتری ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت مشتری جدید", callback_data="add_customer")],
                    [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
                ])
                await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = "📋 <b>لیست مشتریان</b>\n\n"
            for i, customer in enumerate(customers[:20], 1):
                text += f"{i}. {customer.name} - 📞 {customer.phone}\n"
            
            keyboard = []
            for customer in customers[:10]:
                keyboard.append([
                    InlineKeyboardButton(f"👤 {customer.name}", callback_data=f"view_customer_{customer.id}")
                ])
            keyboard.append([InlineKeyboardButton("➕ ثبت مشتری جدید", callback_data="add_customer")])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")])
            
            await BaseHandler.send_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def view_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View customer details."""
        query = update.callback_query
        await query.answer()
        
        customer_id = int(query.data.split('_')[2])
        db = BaseHandler.get_db()
        try:
            customer = CustomerService.get_by_id(db, customer_id)
            if not customer:
                await BaseHandler.send_message(update, context, "❌ مشتری یافت نشد")
                return
            
            text = f"👤 <b>اطلاعات مشتری</b>\n\n📛 نام: {customer.name}\n📞 تلفن: {customer.phone}\n📍 آدرس: {customer.address or 'ثبت نشده'}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑 حذف", callback_data=f"delete_customer_{customer_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="list_customers")]
            ])
            await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def add_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new customer."""
        query = update.callback_query
        if query:
            await query.answer()
        
        await BaseHandler.send_message(
            update, context,
            "➕ <b>ثبت مشتری جدید</b>\n\nلطفاً <b>نام</b> مشتری را وارد کنید:",
            parse_mode='HTML'
        )
        return NAME
    
    @staticmethod
    async def add_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer name."""
        context.user_data['customer_name'] = update.message.text
        await BaseHandler.send_message(
            update, context,
            "📞 لطفاً <b>شماره تلفن</b> مشتری را وارد کنید:",
            parse_mode='HTML'
        )
        return PHONE
    
    @staticmethod
    async def add_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer phone."""
        phone = update.message.text.strip()
        context.user_data['customer_phone'] = phone
        
        await BaseHandler.send_message(
            update, context,
            "📍 لطفاً <b>آدرس</b> مشتری را وارد کنید (برای رد کردن '.' را وارد کنید):",
            parse_mode='HTML'
        )
        return ADDRESS
    
    @staticmethod
    async def add_customer_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer address."""
        address = update.message.text.strip()
        if address == '.':
            address = None
        context.user_data['customer_address'] = address
        
        # Save customer
        db = BaseHandler.get_db()
        try:
            customer = CustomerService.create(
                db,
                name=context.user_data['customer_name'],
                phone=context.user_data['customer_phone'],
                address=context.user_data.get('customer_address')
            )
            
            text = f"✅ <b>مشتری با موفقیت ثبت شد!</b>\n\n👤 نام: {customer.name}\n📞 تلفن: {customer.phone}"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت پروژه جدید", callback_data=f"add_project_{customer.id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست مشتریان", callback_data="list_customers")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New customer added: {customer.name}")
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(update, context, "❌ عملیات لغو شد.", get_main_keyboard())
        context.user_data.clear()
        return ConversationHandler.END
