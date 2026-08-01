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
NAME, PHONE, ADDRESS, DESCRIPTION, EDIT_ADDRESS = range(5)

class CustomerHandler(BaseHandler):
    """Handler for customer operations."""
    
    # Expose states for main.py
    NAME = NAME
    PHONE = PHONE
    ADDRESS = ADDRESS
    DESCRIPTION = DESCRIPTION
    EDIT_ADDRESS = EDIT_ADDRESS
    
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
            
            text = (
                f"👤 <b>اطلاعات مشتری</b>\n\n"
                f"📛 نام: {customer.name}\n"
                f"📞 تلفن: {customer.phone}\n"
                f"📍 آدرس: {customer.address or 'ثبت نشده'}\n"
                f"📝 توضیحات: {customer.description or 'ثبت نشده'}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ویرایش آدرس", callback_data=f"edit_address_{customer_id}")],
                [InlineKeyboardButton("✏️ ویرایش نام", callback_data=f"edit_name_{customer_id}")],
                [InlineKeyboardButton("🗑 حذف مشتری", callback_data=f"delete_customer_{customer_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="list_customers")]
            ])
            
            await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def edit_address_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start editing customer address."""
        query = update.callback_query
        customer_id = int(query.data.split('_')[2])
        context.user_data['edit_customer_id'] = customer_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📍 لطفاً <b>آدرس جدید</b> مشتری را وارد کنید:",
            parse_mode='HTML'
        )
        return EDIT_ADDRESS
    
    @staticmethod
    async def edit_address_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save new address."""
        new_address = update.message.text.strip()
        
        db = BaseHandler.get_db()
        try:
            customer_id = context.user_data['edit_customer_id']
            customer = CustomerService.update(db, customer_id, address=new_address)
            
            if customer:
                text = (
                    f"✅ <b>آدرس با موفقیت ویرایش شد!</b>\n\n"
                    f"👤 نام: {customer.name}\n"
                    f"📍 آدرس جدید: {customer.address}"
                )
                await BaseHandler.send_message(update, context, text, parse_mode='HTML')
                logger.info(f"Address updated for customer {customer_id}")
            else:
                await BaseHandler.send_message(update, context, "❌ مشتری یافت نشد")
        except Exception as e:
            logger.error(f"Error updating address: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا در ویرایش آدرس: {str(e)}")
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
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
        context.user_data['customer_name'] = update.message.text.strip()
        await BaseHandler.send_message(
            update, context,
            "📞 لطفاً <b>شماره تلفن</b> مشتری را وارد کنید:\n(مثال: 09123456789)",
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
            "📍 لطفاً <b>آدرس</b> مشتری را وارد کنید:\n(برای رد کردن '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return ADDRESS
    
    @staticmethod
    async def add_customer_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer address and save."""
        address = update.message.text.strip()
        if address == '.':
            address = None
        context.user_data['customer_address'] = address
        
        db = BaseHandler.get_db()
        try:
            customer = CustomerService.create(
                db,
                name=context.user_data['customer_name'],
                phone=context.user_data['customer_phone'],
                address=context.user_data.get('customer_address')
            )
            
            text = (
                f"✅ <b>مشتری با موفقیت ثبت شد!</b>\n\n"
                f"👤 نام: {customer.name}\n"
                f"📞 تلفن: {customer.phone}\n"
                f"📍 آدرس: {customer.address or 'ثبت نشده'}"
            )
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ ثبت پروژه جدید", callback_data=f"add_project_{customer.id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست مشتریان", callback_data="list_customers")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New customer added: {customer.name}")
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت مشتری: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        context.user_data.clear()
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        return ConversationHandler.END
