"""
Expense management handlers with inline keyboard for edit and delete.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from app.handlers.base_handler import BaseHandler
from app.services.expense_service import ExpenseService
from app.services.project_service import ProjectService
from app.models.expense import ExpenseType, PaidBy
from app.models.project import ProjectStatus
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = logging.getLogger(__name__)

# Conversation states
EXPENSE_TYPE, EXPENSE_AMOUNT, EXPENSE_PAID_BY, EXPENSE_DESCRIPTION = range(4)
EDIT_EXPENSE_AMOUNT, EDIT_EXPENSE_DESCRIPTION = range(10, 12)

class ExpenseHandler(BaseHandler):
    """Handler for expense operations."""
    
    EXPENSE_TYPE = EXPENSE_TYPE
    EXPENSE_AMOUNT = EXPENSE_AMOUNT
    EXPENSE_PAID_BY = EXPENSE_PAID_BY
    EXPENSE_DESCRIPTION = EXPENSE_DESCRIPTION
    EDIT_EXPENSE_AMOUNT = EDIT_EXPENSE_AMOUNT
    EDIT_EXPENSE_DESCRIPTION = EDIT_EXPENSE_DESCRIPTION
    
    @staticmethod
    async def show_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show expenses for a project or general expenses."""
        if update.callback_query:
            query = update.callback_query
            data = query.data
            
            if data == "show_general_expenses":
                context.user_data['show_general'] = True
                await query.answer()
                await ExpenseHandler.show_general_expenses(update, context)
                return
            
            project_id = int(data.split('_')[1])
            context.user_data['current_project_id'] = project_id
            context.user_data['show_general'] = False
            await query.answer()
        else:
            db = BaseHandler.get_db()
            try:
                projects = ProjectService.get_all(db)
                
                text = "💳 <b>مدیریت هزینه‌ها</b>\n\n"
                keyboard = []
                
                if projects:
                    text += "📋 <b>انتخاب پروژه:</b>\n"
                    for project in projects[:10]:
                        status_emoji = "🟢" if project.status == ProjectStatus.IN_PROGRESS else "✅"
                        keyboard.append([
                            InlineKeyboardButton(
                                f"{status_emoji} {project.customer.name} - {project.project_type.value}",
                                callback_data=f"expenses_{project.id}"
                            )
                        ])
                    keyboard.append([])
                
                keyboard.append([InlineKeyboardButton("💳 هزینه‌های عمومی", callback_data="show_general_expenses")])
                keyboard.append([InlineKeyboardButton("➕ هزینه عمومی جدید", callback_data="add_general_expense")])
                keyboard.append([InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="back_home")])
                
                await BaseHandler.send_message(
                    update, context,
                    text,
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='HTML'
                )
                return
            finally:
                db.close()
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data['current_project_id']
            expenses = ExpenseService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)
            
            if not expenses:
                text = f"💳 <b>هزینه‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n❌ هیچ هزینه‌ای ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت هزینه جدید", callback_data=f"add_expense_{project_id}")],
                    [InlineKeyboardButton("💳 هزینه‌های عمومی", callback_data="show_general_expenses")],
                    [InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")]
                ])
                await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = f"💳 <b>هزینه‌های پروژه</b>\n\n👤 مشتری: {project.customer.name}\n\n"
            text += await ExpenseHandler.format_expenses(expenses)
            
            # ساخت کیبورد با دکمه‌های جداگانه برای هر هزینه
            keyboard = []
            for expense in expenses:
                paid_by_emoji = "👤" if expense.paid_by == PaidBy.ME else "👥" if expense.paid_by == PaidBy.PARTNER else "🤝"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{expense.expense_type.value} - {expense.amount:,.0f} تومان {paid_by_emoji}",
                        callback_data=f"expense_detail_{expense.id}"
                    )
                ])
            
            keyboard.append([
                InlineKeyboardButton("➕ ثبت هزینه جدید", callback_data=f"add_expense_{project_id}"),
                InlineKeyboardButton("💳 هزینه‌های عمومی", callback_data="show_general_expenses")
            ])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به پروژه", callback_data=f"view_project_{project_id}")])
            
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def show_general_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show general expenses with inline buttons."""
        db = BaseHandler.get_db()
        try:
            expenses = ExpenseService.get_general_expenses(db)
            
            if not expenses:
                text = "💳 <b>هزینه‌های عمومی</b>\n\n❌ هیچ هزینه عمومی ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ هزینه عمومی جدید", callback_data="add_general_expense")],
                    [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expenses")]
                ])
                
                if update.callback_query:
                    await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                else:
                    await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
                return
            
            text = "💳 <b>هزینه‌های عمومی</b>\n\n"
            text += await ExpenseHandler.format_expenses(expenses)
            
            # ساخت کیبورد با دکمه‌های جداگانه برای هر هزینه
            keyboard = []
            for expense in expenses:
                paid_by_emoji = "👤" if expense.paid_by == PaidBy.ME else "👥" if expense.paid_by == PaidBy.PARTNER else "🤝"
                keyboard.append([
                    InlineKeyboardButton(
                        f"{expense.expense_type.value} - {expense.amount:,.0f} تومان {paid_by_emoji}",
                        callback_data=f"expense_detail_{expense.id}"
                    )
                ])
            
            keyboard.append([InlineKeyboardButton("➕ هزینه عمومی جدید", callback_data="add_general_expense")])
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expenses")])
            
            if update.callback_query:
                await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            else:
                await BaseHandler.send_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        finally:
            db.close()
    
    @staticmethod
    async def format_expenses(expenses):
        """Format expenses list."""
        text = ""
        total_expenses = 0
        general_expenses = 0
        me_expenses = 0
        partner_expenses = 0
        joint_expenses = 0
        
        for expense in expenses:
            paid_by_emoji = "👤" if expense.paid_by == PaidBy.ME else "👥" if expense.paid_by == PaidBy.PARTNER else "🤝"
            general_label = " (عمومی)" if expense.is_general else ""
            text += f"• {expense.expense_type.value}{general_label}\n"
            text += f"   💰 {expense.amount:,.0f} تومان | {paid_by_emoji} {expense.paid_by.value}\n"
            text += f"   📝 {expense.description or 'بدون توضیح'}\n\n"
            total_expenses += expense.amount
            if expense.is_general:
                general_expenses += expense.amount
            if expense.paid_by == PaidBy.ME:
                me_expenses += expense.amount
            elif expense.paid_by == PaidBy.PARTNER:
                partner_expenses += expense.amount
            else:
                joint_expenses += expense.amount
        
        text += f"💰 <b>جمع کل هزینه‌ها</b>: {total_expenses:,.0f} تومان\n"
        if general_expenses > 0:
            text += f"📊 <b>هزینه‌های عمومی</b>: {general_expenses:,.0f} تومان\n"
        text += f"👤 <b>پرداخت شده توسط من</b>: {me_expenses:,.0f} تومان\n"
        text += f"👥 <b>پرداخت شده توسط شریک</b>: {partner_expenses:,.0f} تومان\n"
        if joint_expenses > 0:
            text += f"🤝 <b>پرداخت شده به صورت مشترک</b>: {joint_expenses:,.0f} تومان\n"
        
        return text
    
    @staticmethod
    async def expense_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show expense detail with edit/delete buttons."""
        query = update.callback_query
        expense_id = int(query.data.split('_')[2])
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            expense = ExpenseService.get_by_id(db, expense_id)
            if not expense:
                await BaseHandler.send_message(update, context, "❌ هزینه‌ای با این شناسه یافت نشد")
                return
            
            context.user_data['edit_expense_id'] = expense_id
            
            paid_by_emoji = "👤" if expense.paid_by == PaidBy.ME else "👥" if expense.paid_by == PaidBy.PARTNER else "🤝"
            general_label = " (عمومی)" if expense.is_general else ""
            
            text = (
                f"💳 <b>جزئیات هزینه</b>\n\n"
                f"🆔 شناسه: {expense.id}\n"
                f"💳 نوع: {expense.expense_type.value}{general_label}\n"
                f"💰 مبلغ: {expense.amount:,.0f} تومان\n"
                f"👤 پرداخت کننده: {paid_by_emoji} {expense.paid_by.value}\n"
                f"📝 توضیحات: {expense.description or 'ثبت نشده'}\n"
                f"📅 تاریخ: {expense.created_at.strftime('%Y-%m-%d %H:%M')}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ ویرایش مبلغ", callback_data=f"edit_exp_amount_{expense_id}")],
                [InlineKeyboardButton("✏️ ویرایش توضیحات", callback_data=f"edit_exp_desc_{expense_id}")],
                [InlineKeyboardButton("🗑 حذف هزینه", callback_data=f"delete_exp_confirm_{expense_id}")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expenses")]
            ])
            
            await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
            
        except Exception as e:
            logger.error(f"Error showing expense detail: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
    
    @staticmethod
    async def edit_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit expense amount."""
        query = update.callback_query
        expense_id = int(query.data.split('_')[3])
        context.user_data['edit_expense_id'] = expense_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "💰 <b>ویرایش مبلغ هزینه</b>\n\n"
            "مبلغ جدید را وارد کنید (تومان):\n"
            "(برای انصراف /cancel را بفرستید)",
            parse_mode='HTML'
        )
        return EDIT_EXPENSE_AMOUNT
    
    @staticmethod
    async def edit_expense_amount_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save new expense amount."""
        try:
            new_amount = float(update.message.text.replace(',', '').strip())
            if new_amount <= 0:
                raise ValueError("Amount must be positive")
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
                parse_mode='HTML'
            )
            return EDIT_EXPENSE_AMOUNT
        
        db = BaseHandler.get_db()
        try:
            expense_id = context.user_data['edit_expense_id']
            expense = ExpenseService.update(db, expense_id, amount=new_amount)
            
            if expense:
                await BaseHandler.send_message(
                    update, context,
                    f"✅ <b>مبلغ هزینه با موفقیت ویرایش شد!</b>\n\n"
                    f"🆔 شناسه: {expense.id}\n"
                    f"💳 نوع: {expense.expense_type.value}\n"
                    f"💰 مبلغ جدید: {expense.amount:,.0f} تومان",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expenses")]
                    ]),
                    parse_mode='HTML'
                )
                logger.info(f"Expense {expense_id} amount updated to {new_amount}")
            else:
                await BaseHandler.send_message(update, context, "❌ هزینه‌ای با این شناسه یافت نشد")
        except Exception as e:
            logger.error(f"Error updating expense: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def edit_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit expense description."""
        query = update.callback_query
        expense_id = int(query.data.split('_')[3])
        context.user_data['edit_expense_id'] = expense_id
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📝 <b>ویرایش توضیحات هزینه</b>\n\n"
            "توضیحات جدید را وارد کنید:\n"
            "(برای رد کردن '.' را وارد کنید)\n"
            "(برای انصراف /cancel را بفرستید)",
            parse_mode='HTML'
        )
        return EDIT_EXPENSE_DESCRIPTION
    
    @staticmethod
    async def edit_expense_description_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save new expense description."""
        new_description = update.message.text.strip()
        if new_description == '.':
            new_description = None
        
        db = BaseHandler.get_db()
        try:
            expense_id = context.user_data['edit_expense_id']
            expense = ExpenseService.update(db, expense_id, description=new_description)
            
            if expense:
                await BaseHandler.send_message(
                    update, context,
                    f"✅ <b>توضیحات هزینه با موفقیت ویرایش شد!</b>\n\n"
                    f"🆔 شناسه: {expense.id}\n"
                    f"💳 نوع: {expense.expense_type.value}\n"
                    f"📝 توضیحات جدید: {expense.description or 'ثبت نشده'}",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expenses")]
                    ]),
                    parse_mode='HTML'
                )
                logger.info(f"Expense {expense_id} description updated")
            else:
                await BaseHandler.send_message(update, context, "❌ هزینه‌ای با این شناسه یافت نشد")
        except Exception as e:
            logger.error(f"Error updating expense: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete an expense."""
        query = update.callback_query
        expense_id = int(query.data.split('_')[3])
        
        await query.answer()
        
        # Double confirmation
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"delete_confirm_{expense_id}"),
                InlineKeyboardButton("❌ نه، انصراف", callback_data="back_to_expenses")
            ]
        ])
        
        await BaseHandler.edit_message(
            update, context,
            "⚠️ <b>تأیید حذف</b>\n\n"
            "آیا از حذف این هزینه مطمئن هستید؟\n"
            "این عمل غیرقابل بازگشت است.",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return 15
    
    @staticmethod
    async def delete_expense_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm delete expense."""
        query = update.callback_query
        expense_id = int(query.data.split('_')[2])
        await query.answer()
        
        db = BaseHandler.get_db()
        try:
            expense = ExpenseService.get_by_id(db, expense_id)
            if not expense:
                await BaseHandler.send_message(update, context, "❌ هزینه‌ای با این شناسه یافت نشد")
                return
            
            exp_type = expense.expense_type.value
            exp_amount = expense.amount
            
            if ExpenseService.delete(db, expense_id):
                await BaseHandler.edit_message(
                    update, context,
                    f"✅ <b>هزینه با موفقیت حذف شد!</b>\n\n"
                    f"💳 نوع: {exp_type}\n"
                    f"💰 مبلغ: {exp_amount:,.0f} تومان",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expenses")]
                    ]),
                    parse_mode='HTML'
                )
                logger.info(f"Expense {expense_id} deleted")
            else:
                await BaseHandler.send_message(update, context, "❌ خطا در حذف هزینه")
        except Exception as e:
            logger.error(f"Error deleting expense: {e}")
            await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def back_to_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Back to expense menu."""
        query = update.callback_query
        await query.answer()
        await ExpenseHandler.show_expenses(update, context)
    
    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        await BaseHandler.send_message(
            update, context,
            "❌ عملیات لغو شد."
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    @staticmethod
    async def add_general_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a general expense."""
        query = update.callback_query
        await query.answer()
        
        context.user_data['is_general_expense'] = True
        
        keyboard = []
        for exp_type in ExpenseType:
            keyboard.append([
                InlineKeyboardButton(exp_type.value, callback_data=f"gen_exp_type_{exp_type.value}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_expense")])
        
        await BaseHandler.edit_message(
            update, context,
            "💳 <b>ثبت هزینه عمومی</b>\n\n"
            "هزینه‌های عمومی (ناهار، قهوه، ...) بین همه پروژه‌ها تقسیم می‌شوند.\n\n"
            "لطفاً <b>نوع هزینه</b> را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return EXPENSE_TYPE
    
    @staticmethod
    async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new expense."""
        query = update.callback_query
        project_id = int(query.data.split('_')[2])
        context.user_data['expense_project_id'] = project_id
        context.user_data['is_general_expense'] = False
        
        await query.answer()
        
        keyboard = []
        for exp_type in ExpenseType:
            keyboard.append([
                InlineKeyboardButton(exp_type.value, callback_data=f"exp_type_{project_id}_{exp_type.value}")
            ])
        keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data="cancel_expense")])
        
        await BaseHandler.edit_message(
            update, context,
            "💳 <b>ثبت هزینه جدید</b>\n\nلطفاً <b>نوع هزینه</b> را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML'
        )
        return EXPENSE_TYPE
    
    @staticmethod
    async def add_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense type."""
        query = update.callback_query
        parts = query.data.split('_')
        
        if parts[0] == 'gen':
            expense_type = parts[3]
        else:
            expense_type = parts[3]
            context.user_data['expense_project_id'] = int(parts[2])
        
        context.user_data['expense_type'] = expense_type
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            f"💳 <b>ثبت هزینه {expense_type}</b>\n\n💰 مبلغ هزینه را وارد کنید (تومان):",
            parse_mode='HTML'
        )
        return EXPENSE_AMOUNT
    
    @staticmethod
    async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense amount."""
        try:
            amount = float(update.message.text.replace(',', '').strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            context.user_data['expense_amount'] = amount
        except ValueError:
            await BaseHandler.send_message(
                update, context,
                "❌ مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید.",
                parse_mode='HTML'
            )
            return EXPENSE_AMOUNT
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("👤 من", callback_data="exp_paid_me"),
                InlineKeyboardButton("👥 شریک", callback_data="exp_paid_partner")
            ],
            [
                InlineKeyboardButton("🤝 مشترک", callback_data="exp_paid_joint")
            ],
            [InlineKeyboardButton("🔙 انصراف", callback_data="cancel_expense")]
        ])
        
        await BaseHandler.send_message(
            update, context,
            "💳 چه کسی این هزینه را پرداخت کرده است؟",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return EXPENSE_PAID_BY
    
    @staticmethod
    async def add_expense_paid_by(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get who paid."""
        query = update.callback_query
        paid_by = query.data.split('_')[2]
        if paid_by == 'me':
            context.user_data['expense_paid_by'] = PaidBy.ME
        elif paid_by == 'partner':
            context.user_data['expense_paid_by'] = PaidBy.PARTNER
        else:
            context.user_data['expense_paid_by'] = PaidBy.JOINT
        
        await query.answer()
        await BaseHandler.edit_message(
            update, context,
            "📝 لطفاً <b>توضیحات</b> هزینه را وارد کنید:\n(برای رد کردن '.' را وارد کنید)",
            parse_mode='HTML'
        )
        return EXPENSE_DESCRIPTION
    
    @staticmethod
    async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense description and save."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['expense_description'] = description
        
        db = BaseHandler.get_db()
        try:
            project_id = context.user_data.get('expense_project_id')
            is_general = context.user_data.get('is_general_expense', False)
            
            expense_type_value = context.user_data['expense_type']
            expense_type = None
            for et in ExpenseType:
                if et.value == expense_type_value:
                    expense_type = et
                    break
            
            if not expense_type:
                raise ValueError("Invalid expense type")
            
            expense = ExpenseService.create(
                db,
                project_id=project_id if not is_general else None,
                expense_type=expense_type,
                amount=context.user_data['expense_amount'],
                paid_by=context.user_data['expense_paid_by'],
                description=context.user_data.get('expense_description'),
                is_general=is_general
            )
            
            text = (
                f"✅ <b>هزینه با موفقیت ثبت شد!</b>\n\n"
                f"🆔 شناسه: {expense.id}\n"
                f"💳 نوع: {expense.expense_type.value}\n"
                f"💰 مبلغ: {expense.amount:,.0f} تومان\n"
                f"👤 پرداخت کننده: {expense.paid_by.value}\n"
                f"📊 نوع هزینه: {'عمومی' if expense.is_general else 'پروژه'}\n"
                f"📝 توضیحات: {expense.description or 'ثبت نشده'}"
            )
            
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expenses")]
            ])
            
            await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
            logger.info(f"New expense added: {expense.expense_type.value} for project {project_id or 'general'}")
            
        except Exception as e:
            logger.error(f"Error adding expense: {e}")
            await BaseHandler.send_message(
                update, context,
                f"❌ خطا در ثبت هزینه: {str(e)}"
            )
        finally:
            db.close()
        
        context.user_data.clear()
        return ConversationHandler.END
