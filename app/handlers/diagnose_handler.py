"""
Diagnose handler for checking all bot features.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from app.handlers.base_handler import BaseHandler
from app.services.customer_service import CustomerService
from app.services.project_service import ProjectService
from app.services.part_service import PartService
from app.services.expense_service import ExpenseService
from app.services.payment_service import PaymentService
from app.services.referral_service import ReferralService
from app.keyboards.main_keyboard import get_main_keyboard
from app.core.database import engine
import logging
import sys
import importlib

logger = logging.getLogger(__name__)

class DiagnoseHandler(BaseHandler):
    """Handler for system diagnosis."""
    
    @staticmethod
    async def diagnose(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run full system diagnosis."""
        await update.message.reply_text(
            "🔍 <b>شروع تشخیص سیستم...</b>\n\n"
            "لطفاً چند لحظه صبر کنید...",
            parse_mode='HTML'
        )
        
        results = []
        
        # 1. بررسی دیتابیس
        try:
            from sqlalchemy import text
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            results.append("✅ دیتابیس: اتصال برقرار است")
        except Exception as e:
            results.append(f"❌ دیتابیس: خطا - {str(e)}")
        
        # 2. بررسی مدل‌ها
        try:
            from app.models.customer import Customer
            from app.models.project import Project
            from app.models.part import Part
            from app.models.expense import Expense
            from app.models.payment import Payment
            from app.models.referral import Referral
            results.append("✅ مدل‌ها: همه مدل‌ها به درستی بارگذاری شدند")
        except Exception as e:
            results.append(f"❌ مدل‌ها: خطا - {str(e)}")
        
        # 3. بررسی سرویس‌ها
        try:
            db = BaseHandler.get_db()
            try:
                CustomerService.get_all(db)
                results.append("✅ سرویس مشتری: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس مشتری: خطا - {str(e)}")
            
            try:
                ProjectService.get_all(db)
                results.append("✅ سرویس پروژه: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس پروژه: خطا - {str(e)}")
            
            try:
                PartService.get_by_project(db, 0)
                results.append("✅ سرویس قطعه: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس قطعه: خطا - {str(e)}")
            
            try:
                ExpenseService.get_by_project(db, 0)
                results.append("✅ سرویس هزینه: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس هزینه: خطا - {str(e)}")
            
            try:
                PaymentService.get_by_project(db, 0)
                results.append("✅ سرویس پرداخت: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس پرداخت: خطا - {str(e)}")
            
            try:
                ReferralService.get_by_project(db, 0)
                results.append("✅ سرویس حق معرفی: کار می‌کند")
            except Exception as e:
                results.append(f"❌ سرویس حق معرفی: خطا - {str(e)}")
            finally:
                db.close()
        except Exception as e:
            results.append(f"❌ اتصال به دیتابیس: خطا - {str(e)}")
        
        # 4. بررسی Handlerها با نام صحیح
        handlers = [
            ("start_handler", "StartHandler", "start"),
            ("customer_handler", "CustomerHandler", "add_customer_start"),
            ("project_handler", "ProjectHandler", "add_project_start"),
            ("part_handler", "PartHandler", "add_part_start"),
            ("expense_handler", "ExpenseHandler", "add_expense_start"),
            ("payment_handler", "PaymentHandler", "add_payment_start"),
            ("referral_handler", "ReferralHandler", "add_referral_start"),
            ("report_handler", "ReportHandler", "show_report_menu"),
            ("reminder_handler", "ReminderHandler", "show_reminders"),
            ("settings_handler", "SettingsHandler", "show_settings"),
        ]
        
        for module_name, handler_name, method_name in handlers:
            try:
                module = importlib.import_module(f"app.handlers.{module_name}")
                handler_class = getattr(module, handler_name)
                if hasattr(handler_class, method_name):
                    results.append(f"✅ {handler_name}: متد {method_name} موجود است")
                else:
                    results.append(f"⚠️ {handler_name}: متد {method_name} وجود ندارد")
            except ImportError as e:
                results.append(f"❌ {handler_name}: ماژول یافت نشد - {str(e)}")
            except AttributeError as e:
                results.append(f"❌ {handler_name}: کلاس یافت نشد - {str(e)}")
            except Exception as e:
                results.append(f"❌ {handler_name}: خطا - {str(e)}")
        
        # 5. جمع‌بندی
        success_count = sum(1 for r in results if r.startswith("✅"))
        total_count = len(results)
        
        text = "🔍 <b>گزارش تشخیص سیستم</b>\n\n"
        text += "\n".join(results)
        text += f"\n\n📊 <b>جمع‌بندی</b>: {success_count} از {total_count} تست موفق"
        
        if success_count == total_count:
            text += "\n\n✅ <b>سیستم سالم است!</b>"
        else:
            text += f"\n\n⚠️ <b>{total_count - success_count} مشکل شناسایی شده است.</b>"
        
        keyboard = [
            [InlineKeyboardButton("🔄 اجرای مجدد", callback_data="run_diagnose")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")]
        ]
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
    
    @staticmethod
    async def run_diagnose(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Run diagnose from callback."""
        query = update.callback_query
        await query.answer()
        await DiagnoseHandler.diagnose(update, context)
