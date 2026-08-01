"""
Main application entry point for HVAC Repair Bot.
"""

import logging
import threading
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)
from app.core.config import Config
from app.core.database import Base, engine
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
from app.handlers.partner_handler import PartnerHandler
from app.web_server import start_health_server

logger = setup_logger()

def create_tables():
    """Create database tables if they don't exist."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating database tables: {e}")
        raise

def setup_handlers(application: Application):
    """Register all handlers."""
    
    # Start and Help
    application.add_handler(CommandHandler("start", StartHandler.start))
    application.add_handler(CommandHandler("help", StartHandler.help_command))
    
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
    
    # Project Conversation Handler
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
    application.add_handler(project_conv)
    
    # Part Conversation Handler
    part_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(PartHandler.add_part_start, pattern="^add_part_")
        ],
        states={
            PartHandler.PART_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PartHandler.add_part_name)
            ],
            PartHandler.PART_QUANTITY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PartHandler.add_part_quantity)
            ],
            PartHandler.PART_PURCHASE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PartHandler.add_part_purchase)
            ],
            PartHandler.PART_SELLING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PartHandler.add_part_selling)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", PartHandler.cancel),
            MessageHandler(filters.Regex("^🏠 خانه$"), PartHandler.cancel)
        ],
        allow_reentry=True
    )
    application.add_handler(part_conv)
    
    # Expense Conversation Handler
    expense_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ExpenseHandler.add_expense_start, pattern="^add_expense_")
        ],
        states={
            ExpenseHandler.EXPENSE_TYPE: [
                CallbackQueryHandler(ExpenseHandler.add_expense_type, pattern="^exp_type_")
            ],
            ExpenseHandler.EXPENSE_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.add_expense_amount)
            ],
            ExpenseHandler.EXPENSE_PAID_BY: [
                CallbackQueryHandler(ExpenseHandler.add_expense_paid_by, pattern="^exp_paid_")
            ],
            ExpenseHandler.EXPENSE_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ExpenseHandler.add_expense_description)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", ExpenseHandler.cancel),
            CallbackQueryHandler(ExpenseHandler.cancel, pattern="^cancel_expense$")
        ],
        allow_reentry=True
    )
    application.add_handler(expense_conv)
    
    # Payment Conversation Handler
    payment_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(PaymentHandler.add_payment_start, pattern="^add_payment_")
        ],
        states={
            PaymentHandler.PAYMENT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PaymentHandler.add_payment_amount)
            ],
            PaymentHandler.PAYMENT_METHOD: [
                CallbackQueryHandler(PaymentHandler.add_payment_method, pattern="^pay_method_")
            ],
            PaymentHandler.PAYMENT_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, PaymentHandler.add_payment_description)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", PaymentHandler.cancel)
        ],
        allow_reentry=True
    )
    application.add_handler(payment_conv)
    
    # Referral Conversation Handler
    referral_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ReferralHandler.add_referral_start, pattern="^add_referral_")
        ],
        states={
            ReferralHandler.REFERRAL_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, ReferralHandler.add_referral_name)
            ],
            ReferralHandler.REFERRAL_PERCENTAGE: [
                CallbackQueryHandler(ReferralHandler.add_referral_percentage, pattern="^ref_pct_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, ReferralHandler.add_referral_custom_percentage)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", ReferralHandler.cancel),
            CallbackQueryHandler(ReferralHandler.cancel, pattern="^cancel_referral$")
        ],
        allow_reentry=True
    )
    application.add_handler(referral_conv)
    
    # Reminder - بدون ConversationHandler، فقط دکمه‌ها
    application.add_handler(MessageHandler(filters.Regex("^⏰ یادآوری$"), ReminderHandler.show_reminders))
    application.add_handler(CallbackQueryHandler(ReminderHandler.show_reminders, pattern="^reminder_menu$"))
    application.add_handler(CallbackQueryHandler(ReminderHandler.show_settlement_reminders, pattern="^reminder_settlement$"))
    application.add_handler(CallbackQueryHandler(ReminderHandler.show_followup_reminders, pattern="^reminder_followup$"))
    application.add_handler(CallbackQueryHandler(ReminderHandler.set_reminder_time, pattern="^reminder_settime$"))
    application.add_handler(CallbackQueryHandler(ReminderHandler.back_to_menu, pattern="^reminder_back$"))
    
    # Main menu handlers
    application.add_handler(MessageHandler(filters.Regex("^🏠 خانه$"), DashboardHandler.back_home))
    application.add_handler(MessageHandler(filters.Regex("^👤 مشتری‌ها$"), CustomerHandler.show_customers))
    application.add_handler(MessageHandler(filters.Regex("^🛠 پروژه‌ها$"), ProjectHandler.show_projects))
    application.add_handler(MessageHandler(filters.Regex("^💰 ثبت درآمد$"), PaymentHandler.show_payments))
    application.add_handler(MessageHandler(filters.Regex("^💳 هزینه‌ها$"), ExpenseHandler.show_expenses))
    application.add_handler(MessageHandler(filters.Regex("^🔩 قطعات$"), PartHandler.show_parts))
    application.add_handler(MessageHandler(filters.Regex("^👥 شریک$"), PartnerHandler.show_partner_info))
    application.add_handler(MessageHandler(filters.Regex("^🤝 حق معرفی$"), ReferralHandler.show_referral))
    application.add_handler(MessageHandler(filters.Regex("^📊 گزارش$"), ReportHandler.show_report_menu))
    application.add_handler(MessageHandler(filters.Regex("^⚙ تنظیمات$"), SettingsHandler.show_settings))
    
    # Callback handlers
    application.add_handler(CallbackQueryHandler(DashboardHandler.back_home, pattern="^back_home$"))
    
    # Customer callbacks
    application.add_handler(CallbackQueryHandler(CustomerHandler.view_customer, pattern="^view_customer_"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.show_customers, pattern="^list_customers$"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.delete_customer, pattern="^delete_customer_"))
    application.add_handler(CallbackQueryHandler(CustomerHandler.edit_customer, pattern="^edit_customer_"))
    
    # Project callbacks
    application.add_handler(CallbackQueryHandler(ProjectHandler.view_project, pattern="^view_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.show_projects, pattern="^list_projects$"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.complete_project, pattern="^complete_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.cancel_project, pattern="^cancel_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.delete_project, pattern="^delete_project_"))
    application.add_handler(CallbackQueryHandler(ProjectHandler.edit_project, pattern="^edit_project_"))
    
    # Part callbacks
    application.add_handler(CallbackQueryHandler(PartHandler.show_parts, pattern="^parts_"))
    
    # Expense callbacks
    application.add_handler(CallbackQueryHandler(ExpenseHandler.show_expenses, pattern="^expenses_"))
    
    # Payment callbacks
    application.add_handler(CallbackQueryHandler(PaymentHandler.show_payments, pattern="^payments_"))
    
    # Referral callbacks
    application.add_handler(CallbackQueryHandler(ReferralHandler.show_referral, pattern="^referral_"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.quick_add_referral, pattern="^ref_quick_"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.manage_referrers, pattern="^manage_referrers$"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.add_referrer, pattern="^add_referrer$"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.show_referral, pattern="^back_to_referral$"))
    application.add_handler(CallbackQueryHandler(ReferralHandler.delete_referral, pattern="^delete_referral_"))
    
    # Report callbacks
    application.add_handler(CallbackQueryHandler(ReportHandler.show_report_menu, pattern="^report_menu$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.show_dashboard, pattern="^report_dashboard$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_daily_report, pattern="^report_daily$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_weekly_report, pattern="^report_weekly$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_monthly_report, pattern="^report_monthly$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_yearly_report, pattern="^report_yearly$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.show_statistics, pattern="^statistics$"))
    application.add_handler(CallbackQueryHandler(ReportHandler.generate_statistics, pattern="^stats_"))
    
    # Settings callbacks
    application.add_handler(CallbackQueryHandler(SettingsHandler.show_settings, pattern="^settings$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.backup_database, pattern="^backup_db$"))
    application.add_handler(CallbackQueryHandler(SettingsHandler.reset_database, pattern="^reset_db$"))
    
    logger.info("✅ All handlers registered successfully")

def main():
    """Main entry point."""
    try:
        logger.info("🚀 Starting HVAC Repair Bot...")
        
        # Start health check server
        health_thread = threading.Thread(
            target=start_health_server,
            args=(8080,),
            daemon=True
        )
        health_thread.start()
        logger.info("✅ Health check server started")
        
        # Create tables
        create_tables()
        
        # Create application
        application = Application.builder().token(Config.BOT_TOKEN).build()
        
        # Setup handlers
        setup_handlers(application)
        
        # Start bot
        logger.info("🤖 Bot is running...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
        raise

if __name__ == "__main__":
    main()
