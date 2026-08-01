# فقط بخش Report callbacks را اضافه می‌کنیم:

# Report callbacks
application.add_handler(CallbackQueryHandler(ReportHandler.show_report_menu, pattern="^report_menu$"))
application.add_handler(CallbackQueryHandler(ReportHandler.show_dashboard, pattern="^report_dashboard$"))
application.add_handler(CallbackQueryHandler(ReportHandler.generate_daily_report, pattern="^report_daily$"))
application.add_handler(CallbackQueryHandler(ReportHandler.generate_weekly_report, pattern="^report_weekly$"))
application.add_handler(CallbackQueryHandler(ReportHandler.generate_monthly_report, pattern="^report_monthly$"))
application.add_handler(CallbackQueryHandler(ReportHandler.generate_yearly_report, pattern="^report_yearly$"))
application.add_handler(CallbackQueryHandler(ReportHandler.show_statistics, pattern="^statistics$"))
application.add_handler(CallbackQueryHandler(ReportHandler.generate_statistics, pattern="^stats_"))
application.add_handler(CallbackQueryHandler(ReportHandler.income_report, pattern="^report_income$"))
application.add_handler(CallbackQueryHandler(ReportHandler.expense_report, pattern="^report_expense$"))
