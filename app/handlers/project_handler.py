"""
Project management handlers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.project_service import ProjectService
from app.services.customer_service import CustomerService
from app.services.part_service import PartService
from app.services.expense_service import ExpenseService
from app.services.payment_service import PaymentService
from app.services.referral_service import ReferralService
from app.domain.services.calculator_service import CalculatorService
from app.models.project import ProjectType, ProjectStatus
from app.keyboards.project_keyboards import get_project_keyboard, get_project_type_keyboard
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
PROJECT_CUSTOMER, PROJECT_TYPE, PROJECT_SERVICE, PROJECT_DESCRIPTION, PROJECT_LABOR, PROJECT_ASK_PART = range(6)

class ProjectHandler(BaseHandler):
    """Handler for project operations."""
    
    # Expose states for main.py
    PROJECT_CUSTOMER = PROJECT_CUSTOMER
    PROJECT_TYPE = PROJECT_TYPE
    PROJECT_SERVICE = PROJECT_SERVICE
    PROJECT_DESCRIPTION = PROJECT_DESCRIPTION
    PROJECT_LABOR = PROJECT_LABOR
    PROJECT_ASK_PART = PROJECT_ASK_PART
    
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
            
            # Get all parts and calculate profit
            parts = PartService.get_by_project(db, project_id)
            total_parts_profit = sum(p.profit for p in parts)
            
            # Get expenses
            expenses = ExpenseService.get_by_project(db, project_id)
            
            # Get payments
            payments = PaymentService.get_by_project(db, project_id)
            total_payments = sum(p.amount for p in payments)
            
            # Get referral
            referral = ReferralService.get_by_project(db, project_id)
            
            # Calculate financials
            financials = CalculatorService.calculate_project_financials(
                parts_profit=total_parts_profit,
                labor_cost=project.labor_cost,
                expenses=expenses,
                referral_percentage=referral.percentage if referral else 0,
                referral_name=referral.referrer_name if referral else "",
                total_payments=total_payments
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
                f"📅 <b>تاریخ شروع</b>: {project.start_date.strftime('%Y-%m-%d')}\n\n"
                f"📊 <b>محاسبات مالی</b>:\n"
                f"🔩 <b>سود قطعات</b>: {financials.total_parts_profit:,.0f} تومان\n"
                f"💰 <b>اجرت</b>: {financials.labor_cost:,.0f} تومان\n"
                f"📈 <b>درآمد کل</b>: {financials.total_income:,.0f} تومان\n"
                f"💳 <b>هزینه‌ها</b>: {financials.total_expenses:,.0f} تومان\n"
                f"📊 <b>سود ناخالص</b>: {financials.gross_profit:,.0f} تومان\n"
                f"🤝 <b>حق معرفی</b>: {financials.referral_amount:,.0f} تومان ({financials.referral_percentage}%)\n"
                f"💰 <b>سود خالص</b>: {financials.net_profit:,.0f} تومان\n"
                f"👤 <b>سهم من</b>: {financials.my_share:,.0f} تومان\n"
                f"👥 <b>سهم شریک</b>: {financials.partner_share:,.0f} تومان\n"
                f"💳 <b>طلب من</b>: {financials.my_debt:,.0f} تومان\n"
                f"💰 <b>بدهی مشتری</b>: {financials.customer_debt:,.0f} تومان"
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
                    InlineKeyboardButton("✅ پایان پروژه", callback_data=f"complete_project_{project_id}"),
                    InlineKeyboardButton("❌ لغو پروژه", callback_data=f"cancel_project_{project_id}")
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
    async def complete_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Complete a project."""
        query = update.callback_query
        await query.answer()
        
        project_id = int(query.data.split('_')[2])
        db = BaseHandler.get_db()
        try:
            project = ProjectService.update(db, project_id, status=ProjectStatus.COMPLETED)
            if project:
                await BaseHandler.send_message(
                    update, context,
                    f"✅ <b>پروژه با موفقیت پایان یافت!</b>\n\n"
                    f"🛠 شناسه: {project.id}\n"
                    f"👤 مشتری: {project.customer.name}",
                    parse_mode='HTML'
                )
                await ProjectHandler.view_project(update, context)
            else:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
        except Exception as e:
            logger.error(f"Error completing project: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    async def cancel_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel a project."""
        query = update.callback_query
        await query.answer()
        
        project_id = int(query.data.split('_')[2])
        db = BaseHandler.get_db()
        try:
            project = ProjectService.update(db, project_id, status=ProjectStatus.CANCELLED)
            if project:
                await BaseHandler.send_message(
                    update, context,
                    f"❌ <b>پروژه لغو شد!</b>\n\n"
                    f"🛠 شناسه: {project.id}\n"
                    f"👤 مشتری: {project.customer.name}",
                    parse_mode='HTML'
                )
                await ProjectHandler.view_project(update, context)
            else:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
        except Exception as e:
            logger.error(f"Error cancelling project: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    async def add_project_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new project."""
        query = update.callback_query
        if query:
            await query.answer()
        
        db = BaseHandler.get_db()
        try:
            customers = CustomerService.get_all(db)
            if not customers:
                await BaseHandler.send_message(
                    update, context,
                    "❌ ابتدا باید یک مشتری ثبت کنید.",
                    reply_markup=get_main_keyboard()
                )
                return ConversationHandler.END
            
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
    async def add_project_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get project type."""
        query = update.callback_query
        project_type = query.data.split('_')[2]
        
        if project_type == 'air':
            context.user_data['project_type'] = ProjectType.AIR_CONDITIONER
        else:
            context.user_data['project_type'] = ProjectType.PACKAGE
        
        await query.answer()
        
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
        service_type = query.data.split('_')[1]
        
        service_map = {
            'install': 'نصب',
            'repair': 'تعمیر',
            'visit': 'بازدید'
        }
        context.user_data['project_service'] = service_map[service_type]
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> پروژه را وارد کنید:\n(برای رد کردن '.' را وارد کنید)",
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
            "💰 لطفاً <b>کل مبلغی که از مشتری دریافت می‌کنید</b> را وارد کنید:\n"
            "(شامل اجرت و قیمت قطعات)\n"
            "مثال: 2000000",
            parse_mode='HTML'
        )
        return PROJECT_LABOR
    
    @staticmethod
    async def add_project_labor(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get total amount and ask about parts."""
        try:
            total_amount = float(update.message.text.replace(',', '').strip())
            if total_amount < 0:
                total_amount = 0.0
        except ValueError:
            total_amount = 0.0
        
        context.user_data['total_amount'] = total_amount
        context.user_data['labor_cost'] = total_amount  # Store as labor cost for now
        
        # Ask if they want to add parts
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، قطعه دارم", callback_data="part_yes"),
                InlineKeyboardButton("❌ نه، فقط اجرت", callback_data="part_no")
            ]
        ])
        
        await BaseHandler.send_message(
            update, context,
            f"💰 مبلغ کل: {total_amount:,.0f} تومان\n\n"
            "آیا قطعه‌ای هم به مشتری فروخته‌اید؟",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return PROJECT_ASK_PART
    
    @staticmethod
    async def ask_part_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle part response."""
        query = update.callback_query
        await query.answer()
        
        if query.data == "part_yes":
            # Save project first, then go to add part
            await ProjectHandler.save_project(update, context)
            
            # Ask for part details
            await BaseHandler.send_message(
                update, context,
                "🔩 لطفاً <b>نام قطعه</b> را وارد کنید:",
                parse_mode='HTML'
            )
            # We'll handle this in part handler
            return ConversationHandler.END
        else:
            # Save project without parts
            await ProjectHandler.save_project(update, context)
            return ConversationHandler.END
    
    @staticmethod
    async def save_project(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save project to database."""
        db = BaseHandler.get_db()
        try:
            customer_id = context.user_data.get('project_customer_id')
            if not customer_id:
                await BaseHandler.send_message(
                    update, context,
                    "❌ خطا: مشتری انتخاب نشده است.",
                    reply_markup=get_main_keyboard()
                )
                return
            
            project = ProjectService.create(
                db,
                customer_id=customer_id,
                project_type=context.user_data['project_type'],
                service_type=context.user_data['project_service'],
                description=context.user_data.get('project_description'),
                labor_cost=context.user_data.get('labor_cost', 0)
            )
            
            text = (
                f"✅ <b>پروژه با موفقیت ثبت شد!</b>\n\n"
                f"🛠 شناسه: {project.id}\n"
                f"👤 مشتری: {project.customer.name}\n"
                f"❄️ نوع: {project.project_type.value}\n"
                f"🛠 سرویس: {project.service_type}\n"
                f"💰 مبلغ کل: {context.user_data.get('labor_cost', 0):,.0f} تومان"
            )
            
            keyboard = [
                [InlineKeyboardButton("🔩 ثبت قطعات", callback_data=f"parts_{project.id}")],
                [InlineKeyboardButton("💰 ثبت پرداخت", callback_data=f"add_payment_{project.id}")],
                [InlineKeyboardButton("💳 ثبت هزینه", callback_data=f"add_expense_{project.id}")],
                [InlineKeyboardButton("📊 مشاهده پروژه", callback_data=f"view_project_{project.id}")],
                [InlineKeyboardButton("🔙 بازگشت به لیست", callback_data="list_projects")]
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
                f"❌ خطا در ثبت پروژه: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
    
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
