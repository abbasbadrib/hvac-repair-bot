"""
Handler for free text input (quick project creation).
"""

from telegram import Update
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.services.customer_service import CustomerService
from app.services.project_service import ProjectService
from app.models.project import ProjectType
from app.keyboards.main_keyboard import get_main_keyboard
import logging
import re

logger = logging.getLogger(__name__)

class FreeTextHandler(BaseHandler):
    """Handler for free text input."""
    
    DEVICE_KEYWORDS = {
        'پکیج': ProjectType.PACKAGE,
        'کولر': ProjectType.AIR_CONDITIONER,
        'کولرگازی': ProjectType.AIR_CONDITIONER,
    }
    
    EXCLUDED_PATTERNS = [
        r'^🛠', r'^🏠', r'^👤', r'^💰', r'^💳', r'^🔩', r'^👥', r'^🤝', r'^📊', r'^⏰', r'^⚙',
        r'^➕', r'^✅', r'^❌', r'^🔙', r'^📋', r'^✏️', r'^🗑'
    ]
    
    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش متن آزاد برای ثبت سریع پروژه."""
        text = update.message.text.strip()
        
        # بررسی اینکه آیا کاربر در حال پاسخ به Conversation است
        # اگر context.user_data دارای کلیدهای خاص Conversation باشد، نادیده بگیر
        if context.user_data and any(key in context.user_data for key in 
            ['edit_expense_id', 'expense_project_id', 'part_project_id', 'project_customer_id']):
            logger.info(f"🔍 FreeTextHandler - Skipping, user in conversation: {list(context.user_data.keys())}")
            return False
        
        # بررسی الگوهای مستثنی
        for pattern in FreeTextHandler.EXCLUDED_PATTERNS:
            if re.match(pattern, text):
                logger.info(f"🔍 FreeTextHandler - Skipping excluded pattern: {text}")
                return False
        
        # بررسی اینکه آیا متن درخواست ثبت پروژه است
        if not FreeTextHandler.is_project_request(text):
            return False
        
        logger.info(f"🔍 FreeTextHandler - Processing: {text}")
        result = await FreeTextHandler.parse_and_create_project(update, context, text)
        return result if result else False
    
    @staticmethod
    def is_project_request(text: str) -> bool:
        """بررسی اینکه آیا متن درخواست ثبت پروژه است."""
        keywords = ['پروژه', 'آدرس', 'کار', 'تعمیر', 'نصب', 'بازدید']
        return any(kw in text for kw in keywords)
    
    @staticmethod
    async def parse_and_create_project(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
        """تشخیص اطلاعات و ثبت پروژه."""
        db = BaseHandler.get_db()
        try:
            customer = await FreeTextHandler.find_customer(db, text)
            
            if not customer:
                await update.message.reply_text(
                    f"❌ مشتری با مشخصات '{text}' یافت نشد.\n\n"
                    "لطفاً ابتدا مشتری را با دکمه '👤 مشتری‌ها' ثبت کنید.\n"
                    "یا با فرمت زیر ثبت کنید:\n"
                    "پروژه [نام مشتری] [نوع دستگاه]",
                    reply_markup=get_main_keyboard()
                )
                return False
            
            device_type = FreeTextHandler.detect_device_type(text)
            description = FreeTextHandler.extract_description(text)
            
            project = ProjectService.create(
                db,
                customer_id=customer.id,
                project_type=device_type or ProjectType.PACKAGE,
                service_type="تعمیر",
                description=description or f"ثبت سریع برای {customer.name}",
                labor_cost=0
            )
            
            await update.message.reply_text(
                f"✅ <b>پروژه با موفقیت ثبت شد!</b>\n\n"
                f"🛠 شناسه: {project.id}\n"
                f"👤 مشتری: {customer.name}\n"
                f"📍 آدرس: {customer.address or 'ثبت نشده'}\n"
                f"❄️ نوع: {project.project_type.value}\n"
                f"📝 توضیحات: {project.description or 'ثبت نشده'}\n\n"
                f"🔧 برای تکمیل اطلاعات، از دکمه '🛠 پروژه‌ها' استفاده کنید.",
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )
            
            logger.info(f"Quick project created via free text: {project.id} - {customer.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error in free text handler: {e}")
            await update.message.reply_text(
                "❌ خطا در ثبت پروژه. لطفاً از منوی '🛠 پروژه‌ها' استفاده کنید.",
                reply_markup=get_main_keyboard()
            )
            return False
        finally:
            db.close()
    
    @staticmethod
    async def find_customer(db, text: str):
        """پیدا کردن مشتری از متن."""
        customers = CustomerService.get_all(db)
        
        for customer in customers:
            if customer.name in text:
                return customer
            if customer.address and customer.address in text:
                return customer
        
        for customer in customers:
            name_parts = customer.name.split()
            for part in name_parts:
                if part in text:
                    return customer
        
        return None
    
    @staticmethod
    def detect_device_type(text: str):
        """تشخیص نوع دستگاه از متن."""
        for keyword, device_type in FreeTextHandler.DEVICE_KEYWORDS.items():
            if keyword in text:
                return device_type
        return None
    
    @staticmethod
    def extract_description(text: str):
        """استخراج توضیحات از متن."""
        remove_words = ['پروژه', 'آدرس', 'پکیج', 'کولر', 'کولرگازی']
        for word in remove_words:
            text = text.replace(word, '')
        return text.strip() or None
