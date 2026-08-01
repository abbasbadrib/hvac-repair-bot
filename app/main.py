# ... (قسمت‌های قبلی) ...

def setup_handlers(application: Application):
    """Register all handlers."""
    
    # ... (قسمت‌های قبلی) ...
    
    # Customer Conversation Handler
    customer_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(CustomerHandler.add_customer_start, pattern="^add_customer$"),
            CallbackQueryHandler(CustomerHandler.edit_address_start, pattern="^edit_address_")
        ],
        states={
            CustomerHandler.NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, CustomerHandler.add_customer_name)
            ],
            CustomerHandler.PHONE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, CustomerHandler.add_customer_phone)
            ],
            CustomerHandler.ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, CustomerHandler.add_customer_address)
            ],
            CustomerHandler.EDIT_ADDRESS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, CustomerHandler.edit_address_save)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", CustomerHandler.cancel),
            MessageHandler(filters.Regex("^🏠 خانه$"), CustomerHandler.cancel),
            MessageHandler(filters.Regex("^👤 مشتری‌ها$"), CustomerHandler.cancel)
        ],
        allow_reentry=True
    )
    application.add_handler(customer_conv)
    
    # ... (بقیه کد) ...
