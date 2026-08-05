# فقط بخش expense_conv را اصلاح می‌کنیم

expense_conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(ExpenseHandler.add_expense_start, pattern="^add_expense_"),
        CallbackQueryHandler(ExpenseHandler.add_general_expense_start, pattern="^add_general_expense$")
    ],
    states={
        # ثبت هزینه جدید
        ExpenseHandler.EXPENSE_TYPE: [
            CallbackQueryHandler(ExpenseHandler.add_expense_type, pattern="^exp_type_"),
            CallbackQueryHandler(ExpenseHandler.add_expense_type, pattern="^gen_exp_type_")
        ],
        ExpenseHandler.EXPENSE_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.add_expense_description)
        ],
        ExpenseHandler.EXPENSE_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.add_expense_amount)
        ],
        ExpenseHandler.EXPENSE_PAID_BY: [
            CallbackQueryHandler(ExpenseHandler.add_expense_paid_by, pattern="^exp_paid_")
        ],
        # ===== ویرایش مبلغ هزینه =====
        ExpenseHandler.EDIT_EXPENSE_AMOUNT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.edit_expense_amount_save)
        ],
        # ===== ویرایش توضیحات هزینه =====
        ExpenseHandler.EDIT_EXPENSE_DESCRIPTION: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.edit_expense_description_save)
        ],
    },
    fallbacks=[
        CommandHandler("cancel", ExpenseHandler.cancel),
        CallbackQueryHandler(ExpenseHandler.cancel, pattern="^cancel_expense$")
    ],
    allow_reentry=True,
    per_message=True  # <-- این خط را اضافه کنید تا هر پیام را tracking کند
)
application.add_handler(expense_conv)
