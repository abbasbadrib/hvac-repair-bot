"""
Expense management handlers with debug logging.
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
import traceback

logger = logging.getLogger(__name__)

# Conversation states
EXPENSE_TYPE, EXPENSE_DESCRIPTION, EXPENSE_AMOUNT, EXPENSE_PAID_BY = range(4)
EDIT_EXPENSE_AMOUNT, EDIT_EXPENSE_DESCRIPTION = range(10, 12)


class ExpenseHandler(BaseHandler):
    """Handler for expense operations."""

    EXPENSE_TYPE = EXPENSE_TYPE
    EXPENSE_DESCRIPTION = EXPENSE_DESCRIPTION
    EXPENSE_AMOUNT = EXPENSE_AMOUNT
    EXPENSE_PAID_BY = EXPENSE_PAID_BY
    EDIT_EXPENSE_AMOUNT = EDIT_EXPENSE_AMOUNT
    EDIT_EXPENSE_DESCRIPTION = EDIT_EXPENSE_DESCRIPTION

    @staticmethod
    async def show_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show expenses for a project or general expenses."""
        logger.info("🔍 show_expenses called")
        try:
            if update.callback_query:
                query = update.callback_query
                data = query.data
                logger.info(f"🔍 show_expenses - callback data: {data}")

                if data == "menu_expenses":
                    logger.info("🔍 show_expenses - menu_expenses")
                    await query.answer()
                    db = BaseHandler.get_db()
                    try:
                        projects = ProjectService.get_all(db)
                        logger.info(f"🔍 show_expenses - found {len(projects)} projects")

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

                        await BaseHandler.edit_message(
                            update, context,
                            text,
                            reply_markup=InlineKeyboardMarkup(keyboard),
                            parse_mode='HTML'
                        )
                    finally:
                        db.close()
                    return

                if data == "show_general_expenses":
                    logger.info("🔍 show_expenses - show_general_expenses")
                    context.user_data['show_general'] = True
                    await query.answer()
                    await ExpenseHandler.show_general_expenses(update, context)
                    return

                if data == "back_to_expenses" or data == "back_to_expense_menu":
                    logger.info("🔍 show_expenses - back to expenses")
                    await query.answer()
                    context.user_data.pop('current_project_id', None)
                    await ExpenseHandler.show_expenses(update, context)
                    return

                if data.startswith("expenses_"):
                    try:
                        project_id = int(data.split('_')[1])
                        logger.info(f"🔍 show_expenses - selected project: {project_id}")
                        context.user_data['current_project_id'] = project_id
                        context.user_data['show_general'] = False
                        await query.answer()
                    except (IndexError, ValueError) as e:
                        logger.error(f"Error parsing project_id from {data}: {e}")
                        await query.answer("❌ خطا در شناسایی پروژه", show_alert=True)
                        return
                else:
                    logger.info(f"🔍 show_expenses - unknown data: {data}")
                    await query.answer()
                    return
            else:
                logger.info("🔍 show_expenses - from reply keyboard")
                db = BaseHandler.get_db()
                try:
                    projects = ProjectService.get_all(db)
                    logger.info(f"🔍 show_expenses - found {len(projects)} projects")

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
        except Exception as e:
            logger.error(f"❌ show_expenses error: {e}")
            logger.error(traceback.format_exc())

        db = BaseHandler.get_db()
        try:
            project_id = context.user_data.get('current_project_id')
            if not project_id:
                await BaseHandler.send_message(update, context, "❌ پروژه‌ای انتخاب نشده است")
                return

            expenses = ExpenseService.get_by_project(db, project_id)
            project = ProjectService.get_by_id(db, project_id)

            if not project:
                await BaseHandler.send_message(update, context, "❌ پروژه یافت نشد")
                return

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
        logger.info("🔍 show_general_expenses called")
        db = BaseHandler.get_db()
        try:
            expenses = ExpenseService.get_general_expenses(db)
            logger.info(f"🔍 show_general_expenses - found {len(expenses)} general expenses")

            if not expenses:
                text = "💳 <b>هزینه‌های عمومی</b>\n\n❌ هیچ هزینه عمومی ثبت نشده است."
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ هزینه عمومی جدید", callback_data="add_general_expense")],
                    [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")]
                ])

                if update.callback_query:
                    await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')
                else:
                    await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
                return

            text = "💳 <b>هزینه‌های عمومی</b>\n\n"
            text += await ExpenseHandler.format_expenses(expenses)

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
            keyboard.append([InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")])

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
        logger.info("🔍 expense_detail called")
        try:
            query = update.callback_query
            expense_id = int(query.data.split('_')[2])
            logger.info(f"🔍 expense_detail - expense_id: {expense_id}")

            await query.answer()

            db = BaseHandler.get_db()
            try:
                expense = ExpenseService.get_by_id(db, expense_id)
                if not expense:
                    logger.warning(f"⚠️ expense_detail - expense {expense_id} not found")
                    await BaseHandler.send_message(update, context, "❌ هزینه‌ای با این شناسه یافت نشد")
                    return

                logger.info(f"🔍 expense_detail - found expense: {expense.id}, amount: {expense.amount}")
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
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expense_menu")]
                ])

                await BaseHandler.edit_message(update, context, text, keyboard, parse_mode='HTML')

            except Exception as e:
                logger.error(f"❌ expense_detail - error: {e}")
                logger.error(traceback.format_exc())
                await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
            finally:
                db.close()
        except Exception as e:
            logger.error(f"❌ expense_detail - unexpected error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def edit_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit expense amount."""
        logger.info("=" * 50)
        logger.info("🔍 edit_expense_amount CALLED")
        try:
            query = update.callback_query
            expense_id = int(query.data.split('_')[3])
            logger.info(f"🔍 edit_expense_amount - expense_id: {expense_id}")

            context.user_data['edit_expense_id'] = expense_id
            await query.answer()

            await BaseHandler.send_message(
                update, context,
                "💰 <b>ویرایش مبلغ هزینه</b>\n\n"
                "مبلغ جدید را وارد کنید (تومان):\n"
                "(برای انصراف /cancel را بفرستید)",
                parse_mode='HTML'
            )
            logger.info(f"🔍 edit_expense_amount - returning EDIT_EXPENSE_AMOUNT state: {EDIT_EXPENSE_AMOUNT}")
            return EDIT_EXPENSE_AMOUNT
        except Exception as e:
            logger.error(f"❌ edit_expense_amount error: {e}")
            logger.error(traceback.format_exc())
            return ConversationHandler.END

    @staticmethod
    async def edit_expense_amount_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save new expense amount."""
        logger.info("=" * 50)
        logger.info("🔍 edit_expense_amount_save CALLED")
        try:
            text = update.message.text.strip()
            logger.info(f"🔍 edit_expense_amount_save - text: '{text}'")

            if text.lower() == '/cancel':
                logger.info("🔍 edit_expense_amount_save - user cancelled")
                await BaseHandler.send_message(
                    update, context,
                    "❌ عملیات ویرایش لغو شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")]
                    ]),
                    parse_mode='HTML'
                )
                context.user_data.clear()
                return ConversationHandler.END

            try:
                new_amount = float(text.replace(',', '').strip())
                logger.info(f"🔍 edit_expense_amount_save - parsed amount: {new_amount}")
                if new_amount <= 0:
                    raise ValueError("Amount must be positive")
            except ValueError as e:
                logger.warning(f"⚠️ edit_expense_amount_save - invalid amount: {e}")
                await BaseHandler.send_message(
                    update, context,
                    "❌ مبلغ نامعتبر است. لطفاً یک عدد مثبت وارد کنید.\n"
                    "مثال: 5000 یا 5,000",
                    parse_mode='HTML'
                )
                return EDIT_EXPENSE_AMOUNT

            expense_id = context.user_data.get('edit_expense_id')
            logger.info(f"🔍 edit_expense_amount_save - expense_id from context: {expense_id}")

            if not expense_id:
                logger.error("❌ edit_expense_amount_save - expense_id not found in context")
                await BaseHandler.send_message(
                    update, context,
                    "❌ شناسه هزینه یافت نشد. لطفاً دوباره تلاش کنید.",
                    parse_mode='HTML'
                )
                return ConversationHandler.END

            db = BaseHandler.get_db()
            try:
                logger.info(f"🔍 edit_expense_amount_save - updating expense {expense_id} to {new_amount}")
                expense = ExpenseService.update(db, expense_id, amount=new_amount)

                if expense:
                    logger.info(f"✅ edit_expense_amount_save - expense {expense_id} updated to {new_amount}")
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ ویرایش مجدد", callback_data=f"edit_exp_amount_{expense_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")]
                    ])

                    await BaseHandler.send_message(
                        update, context,
                        f"✅ <b>مبلغ هزینه با موفقیت ویرایش شد!</b>\n\n"
                        f"🆔 شناسه: {expense.id}\n"
                        f"💳 نوع: {expense.expense_type.value}\n"
                        f"💰 مبلغ جدید: {expense.amount:,.0f} تومان",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                    context.user_data.clear()
                    return ConversationHandler.END
                else:
                    logger.error(f"❌ edit_expense_amount_save - expense {expense_id} not found")
                    await BaseHandler.send_message(
                        update, context,
                        "❌ هزینه‌ای با این شناسه یافت نشد.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"❌ edit_expense_amount_save - database error: {e}")
                logger.error(traceback.format_exc())
                await BaseHandler.send_message(
                    update, context,
                    f"❌ خطا در ویرایش هزینه: {str(e)}",
                    parse_mode='HTML'
                )
            finally:
                db.close()

            context.user_data.clear()
            logger.info("🔍 edit_expense_amount_save - clearing context and returning END")
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"❌ edit_expense_amount_save - unexpected error: {e}")
            logger.error(traceback.format_exc())
            return ConversationHandler.END

    @staticmethod
    async def edit_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Edit expense description."""
        logger.info("=" * 50)
        logger.info("🔍 edit_expense_description CALLED")
        try:
            query = update.callback_query
            expense_id = int(query.data.split('_')[3])
            logger.info(f"🔍 edit_expense_description - expense_id: {expense_id}")

            context.user_data['edit_expense_id'] = expense_id
            await query.answer()

            await BaseHandler.send_message(
                update, context,
                "📝 <b>ویرایش توضیحات هزینه</b>\n\n"
                "توضیحات جدید را وارد کنید:\n"
                "(برای رد کردن '.' را وارد کنید)\n"
                "(برای انصراف /cancel را بفرستید)",
                parse_mode='HTML'
            )
            return EDIT_EXPENSE_DESCRIPTION
        except Exception as e:
            logger.error(f"❌ edit_expense_description error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def edit_expense_description_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save new expense description."""
        logger.info("=" * 50)
        logger.info("🔍 edit_expense_description_save CALLED")
        try:
            text = update.message.text.strip()
            logger.info(f"🔍 edit_expense_description_save - text: '{text}'")

            if text.lower() == '/cancel':
                logger.info("🔍 edit_expense_description_save - user cancelled")
                await BaseHandler.send_message(
                    update, context,
                    "❌ عملیات ویرایش لغو شد.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")]
                    ]),
                    parse_mode='HTML'
                )
                context.user_data.clear()
                return ConversationHandler.END

            new_description = None if text == '.' else text
            expense_id = context.user_data.get('edit_expense_id')
            logger.info(f"🔍 edit_expense_description_save - expense_id: {expense_id}")

            if not expense_id:
                await BaseHandler.send_message(
                    update, context,
                    "❌ شناسه هزینه یافت نشد.",
                    parse_mode='HTML'
                )
                return ConversationHandler.END

            db = BaseHandler.get_db()
            try:
                expense = ExpenseService.update(db, expense_id, description=new_description)

                if expense:
                    logger.info(f"✅ edit_expense_description_save - expense {expense_id} description updated")
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ ویرایش مجدد", callback_data=f"edit_exp_desc_{expense_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌ها", callback_data="back_to_expense_menu")]
                    ])

                    await BaseHandler.send_message(
                        update, context,
                        f"✅ <b>توضیحات هزینه با موفقیت ویرایش شد!</b>\n\n"
                        f"🆔 شناسه: {expense.id}\n"
                        f"💳 نوع: {expense.expense_type.value}\n"
                        f"📝 توضیحات جدید: {expense.description or 'ثبت نشده'}",
                        reply_markup=keyboard,
                        parse_mode='HTML'
                    )
                else:
                    await BaseHandler.send_message(
                        update, context,
                        "❌ هزینه‌ای با این شناسه یافت نشد.",
                        parse_mode='HTML'
                    )
            except Exception as e:
                logger.error(f"❌ edit_expense_description_save - error: {e}")
                logger.error(traceback.format_exc())
                await BaseHandler.send_message(
                    update, context,
                    f"❌ خطا در ویرایش هزینه: {str(e)}",
                    parse_mode='HTML'
                )
            finally:
                db.close()

            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"❌ edit_expense_description_save - unexpected error: {e}")
            logger.error(traceback.format_exc())
            return ConversationHandler.END

    @staticmethod
    async def delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Delete an expense."""
        logger.info("🔍 delete_expense called")
        try:
            query = update.callback_query
            expense_id = int(query.data.split('_')[3])
            logger.info(f"🔍 delete_expense - expense_id: {expense_id}")

            await query.answer()

            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("✅ بله، حذف کن", callback_data=f"delete_confirm_{expense_id}"),
                    InlineKeyboardButton("❌ نه، انصراف", callback_data="back_to_expense_menu")
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
        except Exception as e:
            logger.error(f"❌ delete_expense error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def delete_expense_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Confirm delete expense."""
        logger.info("🔍 delete_expense_confirm called")
        try:
            query = update.callback_query
            expense_id = int(query.data.split('_')[2])
            logger.info(f"🔍 delete_expense_confirm - expense_id: {expense_id}")

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
                    logger.info(f"✅ delete_expense_confirm - expense {expense_id} deleted")
                    await BaseHandler.edit_message(
                        update, context,
                        f"✅ <b>هزینه با موفقیت حذف شد!</b>\n\n"
                        f"💳 نوع: {exp_type}\n"
                        f"💰 مبلغ: {exp_amount:,.0f} تومان",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_expense_menu")]
                        ]),
                        parse_mode='HTML'
                    )
                else:
                    await BaseHandler.send_message(update, context, "❌ خطا در حذف هزینه")
            except Exception as e:
                logger.error(f"❌ delete_expense_confirm - error: {e}")
                logger.error(traceback.format_exc())
                await BaseHandler.send_message(update, context, f"❌ خطا: {str(e)}")
            finally:
                db.close()

            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"❌ delete_expense_confirm - unexpected error: {e}")
            logger.error(traceback.format_exc())
            return ConversationHandler.END

    @staticmethod
    async def back_to_expense_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Back to expense menu."""
        logger.info("🔍 back_to_expense_menu called")
        try:
            query = update.callback_query
            await query.answer()
            context.user_data.pop('current_project_id', None)
            await ExpenseHandler.show_expenses(update, context)
        except Exception as e:
            logger.error(f"❌ back_to_expense_menu error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the conversation."""
        logger.info("🔍 cancel called")
        try:
            await BaseHandler.send_message(
                update, context,
                "❌ عملیات لغو شد."
            )
            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"❌ cancel error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def add_general_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a general expense."""
        logger.info("🔍 add_general_expense_start called")
        try:
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
        except Exception as e:
            logger.error(f"❌ add_general_expense_start error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def add_expense_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start adding a new expense."""
        logger.info("🔍 add_expense_start called")
        try:
            query = update.callback_query
            project_id = int(query.data.split('_')[2])
            logger.info(f"🔍 add_expense_start - project_id: {project_id}")

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
        except Exception as e:
            logger.error(f"❌ add_expense_start error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def add_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense type."""
        logger.info("🔍 add_expense_type called")
        try:
            query = update.callback_query
            parts = query.data.split('_')

            if parts[0] == 'gen':
                expense_type = parts[3]
                logger.info(f"🔍 add_expense_type - general expense type: {expense_type}")
            else:
                expense_type = parts[3]
                project_id = int(parts[2])
                context.user_data['expense_project_id'] = project_id
                logger.info(f"🔍 add_expense_type - project expense type: {expense_type}, project_id: {project_id}")

            context.user_data['expense_type'] = expense_type

            await query.answer()
            await BaseHandler.edit_message(
                update, context,
                f"💳 <b>ثبت هزینه {expense_type}</b>\n\n"
                f"📝 لطفاً <b>توضیحات</b> را وارد کنید:\n"
                f"(مثلاً: ناهار امروز، بنزین ماشین، ...)\n"
                f"(برای رد کردن '.' را وارد کنید)",
                parse_mode='HTML'
            )
            return EXPENSE_DESCRIPTION
        except Exception as e:
            logger.error(f"❌ add_expense_type error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def add_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense description."""
        logger.info("🔍 add_expense_description called")
        try:
            description = update.message.text.strip()
            if description == '.':
                description = None
            context.user_data['expense_description'] = description
            logger.info(f"🔍 add_expense_description - description: {description}")

            await BaseHandler.send_message(
                update, context,
                f"💰 <b>ثبت هزینه {context.user_data['expense_type']}</b>\n\n"
                f"مبلغ هزینه را وارد کنید (تومان):",
                parse_mode='HTML'
            )
            return EXPENSE_AMOUNT
        except Exception as e:
            logger.error(f"❌ add_expense_description error: {e}")
            logger.error(traceback.format_exc())

    @staticmethod
    async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get expense amount."""
        logger.info("🔍 add_expense_amount called")
        try:
            text = update.message.text.strip()
            amount = float(text.replace(',', '').strip())
            if amount <= 0:
                raise ValueError("Amount must be positive")
            context.user_data['expense_amount'] = amount
            logger.info(f"🔍 add_expense_amount - amount: {amount}")
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
            f"💳 <b>ثبت هزینه {context.user_data['expense_type']}</b>\n\n"
            f"💰 مبلغ: {amount:,.0f} تومان\n\n"
            "چه کسی این هزینه را پرداخت کرده است؟",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return EXPENSE_PAID_BY

    @staticmethod
    async def add_expense_paid_by(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get who paid and save."""
        logger.info("🔍 add_expense_paid_by called")
        try:
            query = update.callback_query
            paid_by = query.data.split('_')[2]
            if paid_by == 'me':
                context.user_data['expense_paid_by'] = PaidBy.ME
            elif paid_by == 'partner':
                context.user_data['expense_paid_by'] = PaidBy.PARTNER
            else:
                context.user_data['expense_paid_by'] = PaidBy.JOINT
            logger.info(f"🔍 add_expense_paid_by - paid_by: {context.user_data['expense_paid_by']}")

            await query.answer()

            db = BaseHandler.get_db()
            try:
                project_id = context.user_data.get('expense_project_id')
                is_general = context.user_data.get('is_general_expense', False)
                expense_type = context.user_data['expense_type']
                expense_type_enum = None
                for et in ExpenseType:
                    if et.value == expense_type:
                        expense_type_enum = et
                        break

                if not expense_type_enum:
                    raise ValueError("Invalid expense type")

                expense = ExpenseService.create(
                    db,
                    project_id=project_id if not is_general else None,
                    expense_type=expense_type_enum,
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

                if is_general:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"expense_detail_{expense.id}")],
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌های عمومی", callback_data="show_general_expenses")],
                        [InlineKeyboardButton("🔙 بازگشت به منوی هزینه‌ها", callback_data="back_to_expense_menu")]
                    ])
                else:
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("✏️ ویرایش", callback_data=f"expense_detail_{expense.id}")],
                        [InlineKeyboardButton("➕ ثبت هزینه دیگر", callback_data=f"add_expense_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به هزینه‌های پروژه", callback_data=f"expenses_{project_id}")],
                        [InlineKeyboardButton("🔙 بازگشت به منوی هزینه‌ها", callback_data="back_to_expense_menu")]
                    ])

                await BaseHandler.send_message(update, context, text, keyboard, parse_mode='HTML')
                logger.info(f"New expense added: {expense.expense_type.value} for project {project_id or 'general'}")

            except Exception as e:
                logger.error(f"❌ add_expense_paid_by - error: {e}")
                logger.error(traceback.format_exc())
                await BaseHandler.send_message(
                    update, context,
                    f"❌ خطا در ثبت هزینه: {str(e)}"
                )
            finally:
                db.close()

            context.user_data.clear()
            return ConversationHandler.END
        except Exception as e:
            logger.error(f"❌ add_expense_paid_by - unexpected error: {e}")
            logger.error(traceback.format_exc())
            return ConversationHandler.END
