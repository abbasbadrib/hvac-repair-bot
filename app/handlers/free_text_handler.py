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
    
    # کلمات کلیدی برای تشخیص
    DEVICE_KEYWORDS = {
        'پکیج': ProjectType.PACKAGE,
        'کولر': ProjectType.AIR_CONDITIONER,
        'کولرگازی': ProjectType.AIR_CONDITIONER,
    }
    
    @staticmethod
    async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """پردازش متن آزاد برای ثبت سریع پروژه."""
        text = update.message.text.strip()
        
        # بررسی اینکه آیا کاربر قصد ثبت سریع پروژه را دارد
        if not FreeTextHandler.is_project_request(text):
            return False  # ادامه پردازش عادی
        
        # پردازش متن
        result = await FreeTextHandler.parse_and_create_project(update, context, text)
        
        if result:
            return True  # پروژه ثبت شد، نیازی به پردازش بیشتر نیست
        
        return False  # ادامه پردازش عادی
    
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
            # ۱. تشخیص مشتری
            customer = await FreeTextHandler.find_customer(db, text)
            
            if not customer:
                # مشتری پیدا نشد، از کاربر بخواهید مشتری را ثبت کند
                await update.message.reply_text(
                    f"❌ مشتری با مشخصات '{text}' یافت نشد.\n\n"
                    "لطفاً ابتدا مشتری را با دکمه '👤 مشتری‌ها' ثبت کنید.\n"
                    "یا با فرمت زیر ثبت کنید:\n"
                    "پروژه [نام مشتری] [نوع دستگاه]",
                    reply_markup=get_main_keyboard()
                )
                return False
            
            # ۲. تشخیص نوع دستگاه
            device_type = FreeTextHandler.detect_device_type(text)
            
            # ۳. تشخیص توضیحات
            description = FreeTextHandler.extract_description(text)
            
            # ۴. ثبت پروژه
            project = ProjectService.create(
                db,
                customer_id=customer.id,
                project_type=device_type or ProjectType.PACKAGE,
                service_type="تعمیر",  # مقدار پیش‌فرض
                description=description or f"ثبت سریع برای {customer.name}",
                labor_cost=0  # مقدار پیش‌فرض، قابل ویرایش بعداً
            )
            
            # ۵. پیام موفقیت
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
        # بررسی همه مشتریان
        customers = CustomerService.get_all(db)
        
        # اولویت ۱: جستجوی دقیق بر اساس نام
        for customer in customers:
            if customer.name in text:
                return customer
        
        # اولویت ۲: جستجو بر اساس آدرس
        for customer in customers:
            if customer.address and customer.address in text:
                return customer
        
        # اولویت ۳: جستجوی کلمات کلیدی در نام
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
        # حذف کلمات کلیدی
        remove_words = ['پروژه', 'آدرس', 'پکیج', 'کولر', 'کولرگازی']
        for word in remove_words:
            text = text.replace(word, '')
        
        # حذف نام مشتری (اگر شناسایی شده باشد)
        # این بخش ساده‌سازی شده است
        
        return text.strip() or None
