# در بخش project_conv، PROJECT_ASK_PART را اضافه کنید:

    project_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ProjectHandler.add_project_start, pattern="^add_project")
        ],
        states={
            ProjectHandler.PROJECT_CUSTOMER: [
                CallbackQueryHandler(ProjectHandler.add_project_customer, pattern="^project_customer_")
            ],
            ProjectHandler.PROJECT_TYPE: [
                CallbackQueryHandler(ProjectHandler.add_project_type, pattern="^project_type_")
            ],
            ProjectHandler.PROJECT_SERVICE: [
                CallbackQueryHandler(ProjectHandler.add_project_service, pattern="^service_")
            ],
            ProjectHandler.PROJECT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ProjectHandler.add_project_description)
            ],
            ProjectHandler.PROJECT_LABOR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ProjectHandler.add_project_labor)
            ],
            ProjectHandler.PROJECT_ASK_PART: [
                CallbackQueryHandler(ProjectHandler.ask_part_response, pattern="^part_")
            ],
        },
        fallbacks=[
            CommandHandler("cancel", ProjectHandler.cancel),
            CallbackQueryHandler(ProjectHandler.cancel, pattern="^cancel_project$")
        ],
        allow_reentry=True
    )
