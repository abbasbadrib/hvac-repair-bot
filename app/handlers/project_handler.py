"""
Project management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.services.calculator_service import CalculatorService
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
                    "🛠 <b>لیست پروژه‌ها</b>\n\n"
                    "❌ هیچ پروژه‌ای ثبت نشده است.",
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
            
            if len(projects) > 20:
                text += f"\n... و {len(projects) - 20} پروژه دیگر"
            
            # Create inline keyboard for projects
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
    
    @staticmethod
    async def view_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """View project details."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        
        db = BaseHandler.get_db()
        try:
            project = ProjectService.get_by_id(db, project_id)
            if not project:
                await BaseHandler.answer_callback(update, "❌ پروژه یافت نشد", True)
                return
            
            financials = CalculatorService.calculate_project_financials(db, project_id)
            
            status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅" if project.status == ProjectStatus.COMPLETED else "❌"
            
            text = (
                f"🛠 <b>اطلاعات پروژه</b>\n\n"
                f"👤 <b>مشتری</b>: {project.customer.name}\n"
                f"📞 <b>تلفن</b>: {project.customer.phone}\n"
                f"❄️ <b>نوع</b>: {project.project_type.value}\n"
                f"🛠 <b>نوع سرویس</b>: {project.service_type}\n"
                f"{status_emoji} <b>وضعیت</b>: {project.status.value}\n"
                f"📝 <b>توضیحات</b>: {project.description or 'ثبت نشده'}\n"
                f"💰 <b>اجرت</b>: {project.labor_cost:,.0f} تومان\n"
                f"📅 <b>تاریخ شروع</b>: {project.start_date.strftime('%Y-%m-%d %H:%M')}\n"
                f"📅 <b>تاریخ پایان</b>: {project.end_date.strftime('%Y-%m-%d %H:%M') if project.end_date else 'در حال انجام'}\n\n"
                f"📊 <b>محاسبات مالی</b>:\n"
                f"💰 <b>درآمد کل</b>: {financials['total_income']:,.0f} تومان\n"
                f"🔩 <b>سود قطعات</b>: {financials['total_parts_profit']:,.0f} تومان\n"
                f"💳 <b>هزینه‌ها</b>: {financials['total_expenses']:,.0f} تومان\n"
                f"📈 <b>سود ناخالص</b>: {financials['gross_profit']:,.0f} تومان\n"
                f"🤝 <b>حق معرفی</b>: {financials['referral_amount']:,.0f} تومان ({financials['referral_percentage']}%)\n"
                f"📊 <b>سود خالص</b>: {financials['net_profit']:,.0f} تومان\n"
                f"👤 <b>سهم من</b>: {financials['my_share']:,.0f} تومان\n"
                f"👥 <b>سهم شریک</b>: {financials['partner_share']:,.0f} تومان\n"
                f"💳 <b>طلب من</b>: {financials['my_debt']:,.0f} تومان\n"
                f"💰 <b>بدهی مشتری</b>: {financials['customer_debt']:,.0f} تومان"
            )
            
            await BaseHandler.edit_message(
                update, context,
                text,
                reply_markup=get_project_keyboard(project_id),
                parse_mode='HTML'
            )
            await BaseHandler.answer_callback(update, "✅ اطلاعات پروژه")
        finally:
            db.close()
    
    @staticmethod
    async def add_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new project."""
        if update.callback_query:
            # Check if callback has customer_id
            data = update.callback_query.data
            if '_' in data and data.split('_')[1] == 'project' and len(data.split('_')) > 2:
                customer_id = int(data.split('_')[2])
                context.user_data['project_customer_id'] = customer_id
                await update.callback_query.answer()
            else:
                await update.callback_query.answer()
                # Show customer selection
                db = BaseHandler.get_db()
                try:
                    customers = CustomerService.get_all(db)
                    if not customers:
                        await BaseHandler.send_message(
                            update, context,
                            "❌ ابتدا باید یک مشتری ثبت کنید.\n"
                            "از دکمه '👤 مشتری‌ها' استفاده کنید.",
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
                    return
                finally:
                    db.close()
        
        await BaseHandler.send_message(
            update, context,
            "🛠 <b>ثبت پروژه جدید</b>\n\n"
            "لطفاً <b>نوع پروژه</b> را انتخاب کنید:",
            reply_markup=get_project_type_keyboard(),
            parse_mode='HTML'
        )
        return PROJECT_TYPE
    
    @staticmethod
    async def add_project_customer(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Select customer for project."""
        query = update.callback_query
        customer_id = int(query.data.split('_')[2])
        context.user_data['project_customer_id'] = customer_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "🛠 <b>ثبت پروژه جدید</b>\n\n"
            "لطفاً <b>نوع پروژه</b> را انتخاب کنید:",
            reply_markup=get_project_type_keyboard(),
            parse_mode='HTML'
        )
        return PROJECT_TYPE
    
    @staticmethod
    async def add_project_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get project type."""
        query = update.callback_query
        project_type = query.data.split('_')[2]  # air or package
        
        if project_type == 'air':
            context.user_data['project_type'] = ProjectType.AIR_CONDITIONER
        else:
            context.user_data['project_type'] = ProjectType.PACKAGE
        
        await query.answer()
        
        # Show service type selection
        from app.keyboards.project_keyboards import get_service_type_keyboard
        await BaseHandler.edit_message(
            update, context,
            "🛠 لطفاً <b>نوع سرویس</b> را انتخاب کنید:",
            reply_markup=get_service_type_keyboard(),
            parse_mode='HTML'
        )
        return PROJECT_SERVICE
    
    @staticmethod
    async def add_project_service(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get service type."""
        query = update.callback_query
        service_type = query.data.split('_')[1]  # install, repair, visit
        
        service_map = {
            'install': 'نصب',
            'repair': 'تعمیر',
            'visit': 'بازدید'
        }
        context.user_data['project_service'] = service_map[service_type]
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> پروژه را وارد کنید:\n"
            "(برای رد کردن از این مرحله '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return PROJECT_DESCRIPTION
    
    @staticmethod
    async def add_project_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get project description."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['project_description'] = description
        
        await BaseHandler.send_message(
            update, context,
            "💰 لطفاً مبلغ <b>اجرت</b> را وارد کنید:\n"
            "(مبلغ به تومان - برای رد کردن 0 را وارد کنید)",
            parse_mode='HTML'
        )
        return PROJECT_LABOR
    
    @staticmethod
    async def add_project_labor(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get labor cost and save project."""
        try:
            labor_cost = float(update.message.text.replace(',', '').strip())
            if labor_cost < 0:
                labor_cost = 0.0
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ مبلغ نامعتبر است. لطفاً یک عدد وارد کنید.",
                parse_mode='HTML'
            )
            return PROJECT_LABOR
        
        context.user_data['project_labor'] = labor_cost
        
        # Save project
        db = BaseHandler.get_db()
        try:
            customer_id = context.user_data.get('project_customer_id')
            if not customer_id:
                await BaseHandler.send_message(
                    update, context,
                    "❌ خطا: مشتری انتخاب نشده است.",
                    reply_markup=get_main_keyboard()
                )
                return ConversationHandler.END
            
            project = ProjectService.create(
                db,
                customer_id=customer_id,
                project_type=context.user_data['project_type'],
                service_type=context.user_data['project_service'],
                description=context.user_data.get('project_description'),
                labor_cost=labor_cost
            )
            
            text = (
                "✅ <b>پروژه با موفقیت ثبت شد!</b>\n\n"
                f"🛠 شناسه پروژه: {project.id}\n"
                f"👤 مشتری: {project.customer.name}\n"
                f"❄️ نوع: {project.project_type.value}\n"
                f"🛠 سرویس: {project.service_type}\n"
                f"💰 اجرت: {project.labor_cost:,.0f} تومان\n"
                f"📝 توضیحات: {project.description or 'ثبت نشده'}"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔩 ثبت قطعات", callback_data=f"parts_{project.id}")],
                [InlineKeyboardButton("💰 ثبت پرداخت", callback_data=f"payment_{project.id}")],
                [InlineKeyboardButton("💳 ثبت هزینه", callback_data=f"expense_{project.id}")],
                [InlineKeyboardButton("📊 مشاهده پروژه", callback_data=f"view_project_{project.id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست پروژه‌ها", callback_data="list_projects")]
            ]
            
            await BaseHandler.send_message(
                update, context,
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML'
            )
            
            logger.info(f"New project added: {project.id} - {project.customer.name}")
            
        except Exception as e:
            logger.error(f"Error adding project: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت پروژه: {str(e)}",
                reply_markup=get_main_keyboard()
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
            "❌ عملیات لغو شد.",
            reply_markup=get_main_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
