"""
Main application entry point.
"""

import asyncio
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from app.config import Config
from app.database.base import Base, engine
from app.utils.logger import setup_logger
from app.handlers.start_handler import StartHandler
from app.handlers.customer_handler import CustomerHandler
from app.handlers.project_handler import ProjectHandler
from app.handlers.part_handler import PartHandler
from app.handlers.expense_handler import ExpenseHandler
from app.handlers.payment_handler import PaymentHandler
from app.handlers.referral_handler import ReferralHandler
from app.handlers.report_handler import ReportHandler
from app.handlers.reminder_handler import ReminderHandler
from app.handlers.dashboard_handler import DashboardHandler
from app.handlers.settings_handler import SettingsHandler
from app.keyboards.main_keyboard import get_main_keyboard
import logging

logger = setup_logger()

def create_tables():
    """Create database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise

def setup_handlers(application: Application):
    """Setup all handlers."""
    
    # Start and help
    application.add_handler(CommandHandler("start", StartHandler.start))
    application.add_handler(CommandHandler("help", StartHandler.help_command))
    
    # Customer
    application.add_handler(MessageHandler(filters.Regex("^👤 مشتری‌ها$"), CustomerHandler.show_customers))
    application.add_handler(CallbackQueryHandler(CustomerHandler.view_customer, pattern="^view_customer_"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.add_customer_start, pattern="^add_customer$"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.show_customers, pattern="^list_customers$"))
    
    # Project
    application.add_handler(MessageHandler(filters.Regex("^🛠 پروژه‌ها$"), ProjectHandler.show_projects))
    application.add_handler(CallbackQueryHandler(ProjectHandler.view_project, pattern="^view_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.add_project_start, pattern="^add_project"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.show_projects, pattern="^list_projects$"))
    
    # Parts
    application.add_handler(CallbackQueryHandler(PartHandler.show_parts, pattern="^parts_"))
    application.add_handler(CallbackQueryHandler(PartHandler.add_part_start, pattern="^add_part_"))
    application.add_handler(CallbackQueryHandler(PartHandler.delete_part, pattern="^delete_part_"))
    
    # Expenses
    application.add_handler(CallbackQueryHandler(ExpenseHandler.show_expenses, pattern="^expenses_"))
    application.add_handler(CallbackQueryHandler(ExpenseHandler.add_expense_start, pattern="^add_expense_"))
    
    # Payments
    application.add_handler(MessageHandler(filters.Regex("^💰 ثبت درآمد$"), PaymentHandler.show_payments))
    application.add_handler(CallbackQueryHandler(PaymentHandler.show_payments, pattern="^payments_"))
    application.add_handler(CallbackQueryHandler(PaymentHandler.add_payment_start, pattern="^add_payment_"))
    
    # Referral
    application.add_handler(MessageHandler(filters.Regex("^🤝 حق معرفی$"), ReferralHandler.show_referral))
    application.add_handler(CallbackQueryHandler(ReferralHandler.show_referral, pattern="^referral_"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.add_referral_start, pattern="^add_referral_"))
    
    # Reminder
    application.add_handler(MessageHandler(filters.Regex("^⏰ یادآوری$"), ReminderHandler.show_reminders))
    application.add_handler(CallbackQueryHandler(ReminderHandler.show_reminders, pattern="^reminder_"))
    application.add_handler(CallbackQueryHandler(ReminderHandler.add_reminder_start, pattern="^add_reminder_"))
    
    # Report
    application.add_handler(MessageHandler(filters.Regex("^📊 گزارش$"), ReportHandler.show_report_menu))
    application.add_handler(CallbackQueryHandler(ReportHandler.show_report_menu, pattern="^report_menu$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.show_dashboard, pattern="^report_dashboard$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_daily_report, pattern="^report_daily$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_weekly_report, pattern="^report_weekly$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_monthly_report, pattern="^report_monthly$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_yearly_report, pattern="^report_yearly$"))
    
    # Settings
    application.add_handler(MessageHandler(filters.Regex("^⚙ تنظیمات$"), SettingsHandler.show_settings))
    application.add_handler(CallbackQueryHandler(SettingsHandler.show_settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.backup_database, pattern="^backup_db$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.reset_database, pattern="^reset_db$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.confirm_reset, pattern="^confirm_reset$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.cancel_reset, pattern="^cancel_reset$"))
    
    # Dashboard and navigation
    application.add_handler(CallbackQueryHandler(DashboardHandler.back_home, pattern="^back_home$"))
    application.add_handler(MessageHandler(filters.Regex("^🏠 خانه$"), DashboardHandler.back_home))
    
    logger.info("All handlers registered successfully")

def main():
    """Main application entry point."""
    try:
        # Create database tables
        create_tables()
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup handlers
        setup_handlers(application)
        
        logger.info("Starting bot...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Application error: {e}")
        raise

if __name__ == "__main__":
    main()
