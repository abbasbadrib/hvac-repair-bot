# فقط متدهای مربوط به ویرایش را اصلاح می‌کنیم

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
