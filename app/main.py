# فقط بخش Command handlers را اصلاح می‌کنیم:

def setup_handlers(application: Application):
    """Register all handlers."""
    
    # Command handlers
    application.add_handler(CommandHandler("start", StartHandler.start))
    application.add_handler(CommandHandler("help", StartHandler.help_command))
    application.add_handler(CommandHandler("cancel", StartHandler.cancel))
    application.add_handler(CommandHandler("menu", StartHandler.start))
    application.add_handler(CommandHandler("stats", ReportHandler.show_statistics))
    
    # ... بقیه کد ...
