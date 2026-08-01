"""
Project management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.domain.services.calculator_service import CalculatorService
from app.models.project import ProjectType, ProjectStatus
from app.keyboards.project_keyboards import get_project_keyboard, get_project_type_keyboard
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
(PROJECT_CUSTOMER, PROJECT_TYPE, PROJECT_SERVICE, PROJECT_DESCRIPTION, PROJECT_LABOR) = range(5)

class ProjectHandler(BaseHandler):
    """Handler for project operations."""
    
    @staticmethod
    async def show_projects(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show list of projects."""
        db = BaseHandler.get_db()
        try:
            projects = ProjectService.get_all(db)
            if not projects:
                await BaseHandler.send_message(
                    update, context,
                    "🛠 <b>لیست پروژه‌ها</b>\n\n❌ هیچ پروژه‌ای ثبت نشده است.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ ثبت پروژه جدید", callback_data="add_project")],
                        [InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")]
                    ]),
                    parse_mode='HTML'
                )
                return
            
            text = "🛠 <b>لیست پروژه‌ها</b>\n\n"
            for i, project in enumerate(projects[:20], 1):
                status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
                text += f"{i}. {project.customer.name} - {project.project_type.value} - {status_emoji} {project.status.value}\n"
            
            keyboard = []
            for project in projects[:10]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🛠 {project.customer.name} - {project.project_type.value}",
                        callback_data=f"view_project_{project.id}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("➕ ثبت پروژه جدید", callback_data="add_project")])
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
    async def view_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View project details."""
        query = update.callback_query
        await query.answer()
        
        project_id = int(query.data.split('_')[2])
        db = BaseHandler.get_db()
        try:
            project = ProjectService.get_by_id(db, project_id)
            if not project:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
                return
            
            # Calculate financials
            financials = CalculatorService.calculate_project_financials(
                parts_profit=0,  # TODO: Get from parts
                labor_cost=project.labor_cost,
                expenses=[],  # TODO: Get from expenses
                total_payments=0  # TODO: Get from payments
            )
            
            status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
            
            text = (
                f"🛠 <b>اطلاعات پروژه</b>\n\n"
                f"👤 <b>مشتری</b>: {project.customer.name}\n"
                f"📞 <b>تلفن</b>: {project.customer.phone}\n"
                f"❄️ <b>نوع</b>: {project.project_type.value}\n"
                f"🛠 <b>نوع سرویس</b>: {project.service_type}\n"
                f"{status_emoji} <b>وضعیت</b>: {project.status.value}\n"
                f"💰 <b>اجرت</b>: {project.labor_cost:,.0f} تومان\n"
                f"📅 <b>تاریخ شروع</b>: {project.start_date.strftime('%Y-%m-%d')}"
            )
            
            keyboard = [
                [
                    InlineKeyboardButton("✏️ ویرایش", callback_data=f"edit_project_{project_id}"),
                    InlineKeyboardButton("🗑 حذف", callback_data=f"delete_project_{project_id}")
                ],
                [
                    InlineKeyboardButton("🔩 قطعات", callback_data=f"parts_{project_id}"),
                    InlineKeyboardButton("💰 پرداخت‌ها", callback_data=f"payments_{project_id}")
                ],
                [
                    InlineKeyboardButton("💳 هزینه‌ها", callback_data=f"expenses_{project_id}"),
                    InlineKeyboardButton("🤝 حق معرفی", callback_data=f"referral_{project_id}")
                ],
                [
                    InlineKeyboardButton("✅ پایان پروژه", callback_data=f"complete_{project_id}"),
                    InlineKeyboardButton("❌ لغو پروژه", callback_data=f"cancel_{project_id}")
                ],
                [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="list_projects")]
            ]
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
    
    @staticmethod
    async def add_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new project."""
        query = update.callback_query
        if query:
            await query.answer()
        
        # Show customer selection
        db = BaseHandler.get_db()
        try:
            customers = CustomerService.get_all(db)
            if not customers:
                await BaseHandler.send_message(
                    update, context,
                    "❌ ابتدا باید یک مشتری ثبت کنید.",
                    reply_markup=get_main_keyboard()
                )
                return
            
            keyboard = []
            for customer in customers[:10]:
                keyboard.append([
                    InlineKeyboardButton(
                        f"👤 {customer.name} - {customer.phone}",
                        callback_data=f"project_customer_{customer.id}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_project")])
            
            await BaseHandler.send_message(
                update, context,
                "👤 لطفاً <b>مشتری</b> این پروژه را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            return PROJECT_CUSTOMER
        finally:
            db.close()
    
    @staticmethod
    async def add_project_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select customer for project."""
        query = update.callback_query
        customer_id = int(query.data.split('_')[2])
        context.user_data['project_customer_id'] = customer_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "🛠 <b>ثبت پروژه جدید</b>\n\nلطفاً <b>نوع پروژه</b> را انتخاب کنید:",
            reply_markup=get_project_type_keyboard(),
            parse_mode='HTML'
        )
        return PROJECT_TYPE
    
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
