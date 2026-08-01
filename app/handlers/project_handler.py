# فقط بخش مربوط به اجرت را اصلاح می‌کنیم:

    @staticmethod
    async def add_project_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get project description."""
        description = update.message.text.strip()
        if description == '.':
            description = None
        context.user_data['project_description'] = description
        
        await BaseHandler.send_message(
            update, context,
            "💰 لطفاً <b>کل مبلغی که از مشتری دریافت می‌کنید</b> را وارد کنید:\n"
            "(شامل اجرت و قیمت قطعات)\n"
            "مثال: 2000000",
            parse_mode='HTML'
        )
        return PROJECT_LABOR
    
    @staticmethod
    async def add_project_labor(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get total amount and ask about parts."""
        try:
            total_amount = float(update.message.text.replace(',', '').strip())
            if total_amount < 0:
                total_amount = 0.0
        except ValueError:
            total_amount = 0.0
        
        context.user_data['total_amount'] = total_amount
        
        # Ask if they want to add parts
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ بله، قطعه دارم", callback_data=f"part_yes_{context.user_data.get('project_customer_id', 0)}"),
                InlineKeyboardButton("❌ نه، فقط اجرت", callback_data=f"part_no_{context.user_data.get('project_customer_id', 0)}")
            ]
        ])
        
        await BaseHandler.send_message(
            update, context,
            f"💰 مبلغ کل: {total_amount:,.0f} تومان\n\n"
            "آیا قطعه‌ای هم به مشتری فروخته‌اید؟",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        return PROJECT_LABOR + 1  # New state for part question
