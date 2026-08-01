# فقط بخش generate_statistics را اصلاح می‌کنیم:

@staticmethod
async def generate_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE, period: str = "all"):
    """Generate statistics for a specific period."""
    query = update.callback_query
    await query.answer()
    
    db = BaseHandler.get_db()
    try:
        today = date.today()
        if period == "weekly":
            start_date = today - timedelta(days=today.weekday())
        elif period == "monthly":
            start_date = date(today.year, today.month, 1)
        elif period == "yearly":
            start_date = date(today.year, 1, 1)
        else:
            start_date = datetime(2000, 1, 1).date()
        
        all_projects = ProjectService.get_all(db)
        filtered_projects = [p for p in all_projects if p.start_date.date() >= start_date]
        
        period_names = {"all": "همه", "weekly": "هفتگی", "monthly": "ماهانه", "yearly": "سالانه"}
        
        if not filtered_projects:
            # Even if no projects, show general expenses
            general_expenses = ExpenseService.get_general_expenses(db)
            total_general = sum(e.amount for e in general_expenses if e.created_at.date() >= start_date)
            
            if total_general > 0:
                text = f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n"
                text += "❌ هیچ پروژه‌ای در این بازه زمانی یافت نشد.\n\n"
                text += f"💳 هزینه‌های عمومی: {total_general:,.0f} تومان"
            else:
                text = f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n❌ هیچ داده‌ای در این بازه زمانی یافت نشد."
            
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
                [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
            ]
            await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
            return
        
        total_projects = len(filtered_projects)
        completed_projects = [p for p in filtered_projects if p.status == ProjectStatus.COMPLETED]
        total_completed = len(completed_projects)
        
        total_my_share = 0
        total_partner_share = 0
        total_referral_amount = 0
        total_income = 0
        total_expenses = 0
        total_general_expenses = 0
        total_project_expenses = 0
        
        for project in filtered_projects:
            parts = PartService.get_by_project(db, project.id)
            expenses = ExpenseService.get_by_project(db, project.id)
            payments = PaymentService.get_by_project(db, project.id)
            referral = ReferralService.get_by_project(db, project.id)
            total_payments = sum(p.amount for p in payments)
            
            financials = CalculatorService.calculate_project_financials(
                total_amount_from_customer=project.labor_cost,
                parts=parts,
                expenses=expenses,
                referral_percentage=referral.percentage if referral else 0,
                referral_name=referral.referrer_name if referral else "",
                total_payments=total_payments
            )
            
            total_my_share += financials.my_share
            total_partner_share += financials.partner_share
            if referral:
                total_referral_amount += referral.amount
            total_income += financials.total_income
            total_expenses += financials.total_expenses
            total_general_expenses += financials.general_expenses
            total_project_expenses += financials.project_expenses
        
        text = (
            f"📊 <b>آمار {period_names.get(period, 'کل')}</b>\n\n"
            f"📋 تعداد کل پروژه‌ها: {total_projects}\n"
            f"✅ پروژه‌های تکمیل شده: {total_completed}\n"
            f"⏳ پروژه‌های در حال انجام: {total_projects - total_completed}\n\n"
            f"💰 مبلغ کل: {total_income:,.0f} تومان\n"
            f"💳 هزینه‌های مستقیم پروژه‌ها: {total_project_expenses:,.0f} تومان\n"
            f"💳 هزینه‌های عمومی: {total_general_expenses:,.0f} تومان\n"
            f"📊 سود ناخالص: {total_income - total_expenses:,.0f} تومان\n\n"
            f"👤 <b>سهم من</b>: {total_my_share:,.0f} تومان\n"
            f"👥 <b>سهم شریک</b>: {total_partner_share:,.0f} تومان\n"
            f"🤝 <b>کل حق معرفی</b>: {total_referral_amount:,.0f} تومان\n\n"
            f"📊 <b>نهایی</b>:\n"
            f"💵 مبلغ قابل تسویه با شریک: {total_partner_share:,.0f} تومان\n"
            f"💵 مبلغ قابل پرداخت به معرفی‌کننده‌ها: {total_referral_amount:,.0f} تومان"
        )
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به آمار", callback_data="statistics")],
            [InlineKeyboardButton("🔙 بازگشت به گزارش‌ها", callback_data="report_menu")]
        ]
        
        await BaseHandler.edit_message(update, context, text, InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        
    except Exception as e:
        logger.error(f"Error generating statistics: {e}")
        await BaseHandler.send_message(update, context, f"❌ خطا در تولید آمار: {str(e)}")
    finally:
        db.close()
