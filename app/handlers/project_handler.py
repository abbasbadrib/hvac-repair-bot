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
                        [InlineKeyboardButton("🔍 جستجو", callback_data="search_project")],
                        [InlineKeyboardButton("📊 پروژه‌های در حال انجام", callback_data="open_projects")],
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
            keyboard.append([InlineKeyboardButton("🔍 جستجو", callback_data="search_project")])
            keyboard.append([InlineKeyboardButton("📊 پروژه‌های در حال انجام", callback_data="open_projects")])
            keyboard.append([InlineKeyboardButton("🏠 بازگشت به خانه", callback_data="back_home")])
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
        finally:
            db.close()
