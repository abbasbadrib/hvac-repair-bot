# فقط بخش Callback handlers را اصلاح می‌کنیم:

    # Customer handlers
    application.add_handler(CallbackQueryHandler(CustomerHandler.view_customer, pattern="^view_customer_"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.show_customers, pattern="^list_customers$"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.delete_customer, pattern="^delete_customer_"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.edit_customer, pattern="^edit_customer_"))
    
    # Project handlers
    application.add_handler(CallbackQueryHandler(ProjectHandler.view_project, pattern="^view_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.show_projects, pattern="^list_projects$"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.complete_project, pattern="^complete_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.cancel_project, pattern="^cancel_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.delete_project, pattern="^delete_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.edit_project, pattern="^edit_project_"))
