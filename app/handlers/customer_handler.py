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
(NAME, PHONE, ADDRESS, LOCATION, DESCRIPTION, SEARCH, DELETE_CONFIRM) = range(7)

class CustomerHandler(BaseHandler):
    """Handler for customer operations."""
    
    @staticmethod
    async def show_customers(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of customers."""
        db = BaseHandler.get_db()
        try:
            customers = CustomerService.get_all(db)
            if not customers:
                await BaseHandler.send_message(
                    update, context,
                    "📋 <b>لیست مشتریان</b>\n\n"
                    "❌ هیچ مشتری ثبت نشده است.\n"
                    "برای ثبت مشتری جدید از دکمه '➕ ثبت مشتری جدید' استفاده کنید.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت مشتری جدید", callback_data="add_customer")],
                        [InlineKeyboardButton("🔍 جستجو", callback_data="search_customer")],
                        [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "📋 <b>لیست مشتریان</b>\n\n"
            for i, customer in enumerate(customers[:20], 1):
                text += f"{i}. {customer.name} - 📞 {customer.phone}\n"
            
            if len(customers) > 20:
                text += f"\n... و {len(customers) - 20} مشتری دیگر"
            
            # Create inline keyboard for customers
            keyboard = []
            for customer in customers[:10]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {customer.name}",
                        callback_data=f"view_customer_{customer.id}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("➕ ثبت مشتری جدید", callback_data="add_customer")])
            keyboard.append([InlineKeyboardButton("🔍 جستجو", callback_data="search_customer")])
            keyboard.append([InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")])
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def view_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View customer details."""
        query = update.callback_query
        customer_id = int(query.data.split('_')[2])
        
        db = BaseHandler.get_db()
        try:
            customer = CustomerService.get_by_id(db, customer_id)
            if not customer:
                await BaseHandler.answer_callback(update, "❌ مشتری یافت نشد", True)
                return
            
            text = (
                f"👤 <b>اطلاعات مشتری</b>\n\n"
                f"📛 <b>نام</b>: {customer.name}\n"
                f"📞 <b>تلفن</b>: {customer.phone}\n"
                f"📍 <b>آدرس</b>: {customer.address or 'ثبت نشده'}\n"
                f"📝 <b>توضیحات</b>: {customer.description or 'ثبت نشده'}\n"
                f"📅 <b>تاریخ ثبت</b>: {customer.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"🔄 <b>آخرین ویرایش</b>: {customer.updated_at.strftime('%Y-%m-%d %H:%M')}\n"
                f"📊 <b>تعداد پروژه‌ها</b>: {len(customer.projects)}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_customer_{customer_id}"),
                    InlineKeyboardButton("🗑 حذف", callback_data=f"delete_customer_{customer_id}")
                ],
                [
                    InlineKeyboardButton("🛠 پروژه‌های این مشتری", callback_data=f"customer_projects_{customer_id}"),
                    InlineKeyboardButton("➕ پروژه جدید", callback_data=f"add_project_{customer_id}")
                ],
                [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="list_customers")]
            ]
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            await BaseHandler.answer_callback(update, "✅ اطلاعات مشتری")
        finally:
            db.close()
    
    @staticmethod
    async def add_customer_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new customer."""
        if update.callback_query:
            await update.callback_query.answer()
        
        await BaseHandler.send_message(
            update, context,
            "➕ <b>ثبت مشتری جدید</b>\n\n"
            "لطفاً <b>نام</b> مشتری را وارد کنید:",
            parse_mode='HTML'
        )
        return NAME
    
    @staticmethod
    async def add_customer_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer name."""
        context.user_data['customer_name'] = update.message.text
        
        await BaseHandler.send_message(
            update, context,
            "📞 لطفاً <b>شماره تلفن</b> مشتری را وارد کنید:\n"
            "مثال: 09121234567",
            parse_mode='HTML'
        )
        return PHONE
    
    @staticmethod
    async def add_customer_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer phone."""
        phone = update.message.text.strip()
        # Simple phone validation
        if len(phone) < 10 or not phone.isdigit():
            await BaseHandler.send_message(
                update, context,
                "❌ شماره تلفن نامعتبر است. لطفاً یک شماره ۱۰ رقمی وارد کنید.",
                parse_mode='HTML'
            )
            return PHONE
        
        # Check if phone already exists
        db = BaseHandler.get_db()
        try:
            existing = CustomerService.get_by_phone(db, phone)
            if existing:
                await BaseHandler.send_message(
                    update, context,
                    f"❌ این شماره تلفن قبلاً برای مشتری '{existing.name}' ثبت شده است.\n"
                    "لطفاً شماره دیگری وارد کنید.",
                    parse_mode='HTML'
                )
                return PHONE
        finally:
            db.close()
        
        context.user_data['customer_phone'] = phone
        
        await BaseHandler.send_message(
            update, context,
            "📍 لطفاً <b>آدرس</b> مشتری را وارد کنید:\n"
            "(برای رد کردن از این مرحله '.' را وارد کنید)",
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
        
        await BaseHandler.send_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> مشتری را وارد کنید:\n"
            "(برای رد کردن از این مرحله '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return DESCRIPTION
    
    @staticmethod
    async def add_customer_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get customer description and save."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['customer_description'] = description
        
        # Save customer
        db = BaseHandler.get_db()
        try:
            customer = CustomerService.create(
                db,
                name=context.user_data['customer_name'],
                phone=context.user_data['customer_phone'],
                address=context.user_data.get('customer_address'),
                description=context.user_data.get('customer_description')
            )
            
            text = (
                "✅ <b>مشتری با موفقیت ثبت شد!</b>\n\n"
                f"👤 نام: {customer.name}\n"
                f"📞 تلفن: {customer.phone}\n"
                f"📍 آدرس: {customer.address or 'ثبت نشده'}\n"
                f"📝 توضیحات: {customer.description or 'ثبت نشده'}"
            )
            
            keyboard = [
                [InlineKeyboardButton("➕ ثبت پروژه جدید", callback_data=f"add_project_{customer.id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست مشتریان", callback_data="list_customers")]
            ]
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            logger.info(f"New customer added: {customer.name} ({customer.phone})")
            
        except Exception as e:
            logger.error(f"Error adding customer: {e}")
            await BaseHandler.send_message(
                update, context,
                "❌ خطا در ثبت مشتری. لطفاً دوباره تلاش کنید.",
                reply_markup=get_main_keyboard()
            )
        finally:
            db.close()
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
