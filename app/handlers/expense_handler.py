# فقط بخش add_expense_description را اصلاح می‌کنیم

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
            
            # دکمه بازگشت به هزینه‌ها
            if is_general:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 بازگشت به هزینه‌های عمومی", callback_data="show_general_expenses")],
                    [InlineKeyboardButton("🔙 بازگشت به منوی هزینه‌ها", callback_data="back_to_expense_menu")]
                ])
            else:
                keyboard = InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ ثبت هزینه دیگر", callback_data=f"add_expense_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به هزینه‌های پروژه", callback_data=f"expenses_{project_id}")],
                    [InlineKeyboardButton("🔙 بازگشت به منوی هزینه‌ها", callback_data="back_to_expense_menu")]
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
